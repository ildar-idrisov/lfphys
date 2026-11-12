# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Parameter sweeps (plan P16.3; integrator's API of 2026-11-11, §4): the same scene from one moment for a list of values
of a live law or of an object's parameter, a measurable read over world time — in a separate memory-limited process.

The fixture world ``tests/instruments_worlds/p97_osc`` moves harmonic oscillators by the exact rotation of their phase
plane, so each swept value has a closed form from the state the sweep starts from (x0, v0 at t0):

* a law (the spring constant k): x(t0 + T) = x0 cos ωT + v0/ω sin ωT, ω = √(k/m);
* an object's parameter (the mass m; the world keeps x and v): E = m v0²/2 + k x0²/2, constant in time, so its mean over
  any window is that number;
* the maximum of x over one period: the amplitude √(x0² + (v0/ω)²), within the sampling's (ωΔt/2)²/2.

Negative controls: the closed form of the unchanged law does not fit the swept values; a value the world refuses (k >
100) or that does not fit the memory budget is that value's result, in the owner's words, and the others are computed;
the same sweep from the same state gives the same numbers bit for bit, and from another state other numbers."""

import asyncio
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from aiohttp.test_utils import TestClient, TestServer

from lfviz import checkpoint as CK
from lfviz import protocol, registry, sweep
from lfviz.app import MGR, create_app

HERE = Path(__file__).resolve().parent
WORLDS = HERE / "instruments_worlds"


@pytest.fixture(autouse=True)
def _extra(monkeypatch):
    monkeypatch.setenv("LFVIZ_EXTRA", str(WORLDS))
    monkeypatch.setenv("LFVIZ_PLAYGROUND_CKPT", "1")  # checkpoints every second while playing (a suspended run's base)
    monkeypatch.delenv("P97_MEASURE", raising=False)
    monkeypatch.delenv("LFVIZ_SWEEP_BUDGET_S", raising=False)


def xv_exact(t, x0=1.0, v0=0.0, k=4.0, m=1.0):
    w = math.sqrt(k / m)
    c, s = math.cos(w * t), math.sin(w * t)
    return x0 * c + v0 / w * s, -x0 * w * s + v0 * c


def x_after(x0, v0, k, T, m=1.0):
    return xv_exact(T, x0, v0, k, m)[0]


# --- the sweep's computation, without the server --------------------------------------------------------------------
def _base(preset="one", t=0.37, **params):
    from harness import Harness
    h = Harness("p97_osc", preset, params, seed=11)
    h.run_to(t)
    return h, CK.dumps(h.runner.checkpoint_state(), h.sim._emit_real)


CLOCK = sweep.Clock()  # no budget, no folder


def _req(**kw):
    req = {"target": {"kind": "law", "id": "k"}, "values": [], "duration": 0.7, "measure": "o1.x", "stat": "final",
           "window": None, "n_samples": 200}
    req.update(kw)
    return req


def test_run_value_matches_the_closed_form_and_is_deterministic():
    h, data = _base()
    x0, v0 = h.sim.xv["o1"]
    t0 = h.sim.t
    req = _req()
    for k in (1.0, 4.0, 9.0, 16.0):
        r = sweep.run_value(data, req, k, CLOCK)
        assert r["t0"] == t0 and abs(r["t1"] - (t0 + 0.7)) < 1e-12 and r["sampler"] == "frame"
        assert abs(r["measured"] - x_after(x0, v0, k, r["t1"] - t0)) < 1e-12, k
        if k != 4.0:  # negative control: the law as it was does not give the swept value
            assert abs(r["measured"] - x_after(x0, v0, 4.0, r["t1"] - t0)) > 1e-3
        assert r == {**sweep.run_value(data, req, k, CLOCK), "wall_s": r["wall_s"], "restore_s": r["restore_s"],
                     "advance_s": r["advance_s"], "sample_ms": r["sample_ms"]}  # bit for bit, all but the clock
    # the live world was not touched
    assert h.sim.k == 4.0 and h.sim.t == t0
    # a refusal of the world is the value's result
    r = sweep.run_value(data, req, 1000.0, CLOCK)
    assert r["measured"] is None and "жёстче 100 Н/м" in r["error"] and r["error"].startswith("Изменение не применено")


def test_object_parameter_mean_and_max():
    h, data = _base(preset="one", t=0.21)
    x0, v0 = h.sim.xv["o1"]
    # the mass changed, x and v kept: E = m v0²/2 + k x0²/2 at all times, the trapezoid mean over the window too
    req = _req(target={"kind": "object", "obj": "o1", "param": "m"}, measure="o1.E", stat="mean_last", window=0.3,
               duration=0.5, n_samples=50)
    for m in (0.5, 2.0, 7.0):
        r = sweep.run_value(data, req, m, CLOCK)
        assert abs(r["measured"] - (0.5 * m * v0 * v0 + 0.5 * 4.0 * x0 * x0)) < 1e-12
        assert r["readings"] == 51 and abs(r["trace"]["t"][0] - (0.5 - 0.3)) < 1e-12
    # the maximum of x over one period of each k: the amplitude, within the sampling
    for k in (4.0, 9.0):
        w = math.sqrt(k)
        req = _req(stat="max", duration=2 * math.pi / w, n_samples=400)
        r = sweep.run_value(data, req, k, CLOCK)
        amp = math.hypot(x0, v0 / w)
        assert r["measured"] <= amp + 1e-12 and amp - r["measured"] < 0.5 * (w * req["duration"] / 800) ** 2 * amp + 1e-12
        rmin = sweep.run_value(data, {**req, "stat": "min"}, k, CLOCK)
        assert abs(rmin["measured"] + amp) < 0.5 * (w * req["duration"] / 800) ** 2 * amp + 1e-12


def test_random_world_is_deterministic_from_the_same_state_only():
    _, data = _base(preset="two", t=0.5)
    req = _req(measure="o1.x", duration=1.3)
    a = [sweep.run_value(data, req, k, CLOCK)["measured"] for k in (2.0, 5.0)]
    b = [sweep.run_value(data, req, k, CLOCK)["measured"] for k in (2.0, 5.0)]
    assert a == b
    _, data2 = _base(preset="two", t=0.5)  # the same history: the same state, the same numbers
    assert [sweep.run_value(data2, req, k, CLOCK)["measured"] for k in (2.0, 5.0)] == a
    _, data3 = _base(preset="two", t=0.55)  # negative control: another moment, other numbers
    assert [sweep.run_value(data3, req, k, CLOCK)["measured"] for k in (2.0, 5.0)] != a


def test_stats_of_undefined_readings():
    req = {"stat": "mean_last"}
    assert sweep._stat(req, [0, 1, 2], [1.0, None, 1.0])[0] is None
    assert sweep._stat(req, [0, 1, 3], [1.0, 3.0, 3.0]) == ((2.0 + 6.0) / 3, "")
    m, note = sweep._stat({"stat": "max"}, [0, 1, 2], [1.0, None, 5.0])
    assert m == 5.0 and "1 из 3" in note
    assert sweep._stat({"stat": "final"}, [0, 1], [1.0, None])[0] is None


def _env(mem_bytes=None, **extra):
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(registry.SERVER), str(registry.ROOT), str(registry.ENGINE)])
    if mem_bytes:
        env["LFVIZ_WORKER_MEM"] = str(int(mem_bytes))
    env.update(extra)
    return env


def test_the_process_holds_the_memory_budget_and_measures_through_measure(tmp_path):
    """The sweep process itself (``python -m lfviz.sweep``): a value whose world takes more memory than the budget is
    refused in Russian and the others are computed; with ``measure()`` offered, it is read instead of ``frame()``."""
    h, data = _base()
    x0, v0 = h.sim.xv["o1"]
    (tmp_path / "1.base.pkl").write_bytes(data)
    spec = {"n": 1, "run": "test", "viz": "p97_osc", "state": "starting", "budget_s": 600,
            "request": _req(target={"kind": "law", "id": "alloc_mb"}, values=[8, 3000], measure="o1.x"),
            "base": {"path": str(tmp_path / "1.base.pkl"), "t": h.sim.t}, "progress": {"done": 0, "total": 2},
            "results": []}
    (tmp_path / "1.json").write_text(json.dumps(spec))
    p = subprocess.run([sys.executable, "-m", "lfviz.sweep", "--file", str(tmp_path / "1.json")],
                       env=_env(1024 * 2 ** 20, P97_MEASURE="1"), cwd=str(registry.ROOT), capture_output=True,
                       timeout=300)
    assert p.returncode == 0, p.stderr.decode()[-3000:]
    out = json.loads((tmp_path / "1.json").read_text())
    assert out["state"] == "done" and out["progress"]["done"] == 2 and out["sampler"] == "measure"
    ok, big = out["results"]
    assert abs(ok["measured"] - x_after(x0, v0, 4.0, 0.7)) < 1e-12
    assert big["measured"] is None and "не хватает памяти" in big["error"] and "1 ГБ" in big["error"], big
    assert out["measured_cost"]["sample_ms"] >= 0 and out["message"] == "Готово: измерено 1 из 2 значений"


# --- through the server -----------------------------------------------------------------------------------------------
async def wait_for(pred, timeout=60.0, step=0.05):
    t0 = time.monotonic()
    while not pred():
        if time.monotonic() - t0 > timeout:
            raise TimeoutError("condition not reached")
        await asyncio.sleep(step)


async def start_played(cl, app, preset="one", play_s=2.5, **body):
    r = await cl.post("/api/runs", json={"viz": "p97_osc", "preset": preset, "seed": 5, **body})
    rid = (await r.json())["id"]
    run = app[MGR].get(rid)
    await wait_for(lambda: any(e.kind == "header" for e in run.entries))
    await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})
    await asyncio.sleep(play_s)
    await cl.post(f"/api/runs/{rid}/command", json={"cmd": "pause"})
    await asyncio.sleep(0.6)
    return rid, run


async def sweep_done(cl, rid, n, timeout=300.0):
    t0 = time.monotonic()
    while True:
        js = await (await cl.get(f"/api/runs/{rid}/sweeps/{n}")).json()
        if js["state"] not in ("starting", "running") and not js["active"]:
            return js
        if time.monotonic() - t0 > timeout:
            raise TimeoutError(js)
        await asyncio.sleep(0.2)


async def _server(tmp_path, monkeypatch):
    app = create_app(tmp_path / "runs", max_workers=2, idle_pause=600, idle_suspend=3600, worker_mem_gb=1.0)
    async with TestClient(TestServer(app)) as cl:
        rid, run = await start_played(cl, app)
        url = f"/api/runs/{rid}/sweep"
        body = {"target": {"kind": "law", "id": "k"}, "values": [1.0, 4.0, 9.0, 16.0, 1000.0], "duration": 0.7,
                "measure": "o1.x", "stat": "final"}
        # the estimate before the start: from the world's measured cost in the record
        r = await cl.post(url, json={**body, "estimate": True})
        est = await r.json()
        assert r.status == 200, est
        e = est["estimate"]
        assert e["known"] and 0 < e["total_s"] < e["budget_s"] == 600 and e["text"].startswith("≈") and e["n_readings"] == 1
        assert est["target_label"] == "Жёсткость пружины" and est["measure_label"] == "Осциллятор 1: положение"
        assert not (run.dir / "sweeps").exists() or not list((run.dir / "sweeps").glob("*.json"))  # nothing started
        # the sweep
        r = await cl.post(url, json=body)
        st = await r.json()
        assert r.status == 200, st
        n1 = st["n"]
        assert n1 == 1 and st["base"]["source"] in ("now", "latest")
        js = await sweep_done(cl, rid, n1)
        assert js["state"] == "done", js
        t_base = js["base"]["t"]
        x0, v0 = xv_exact(t_base)  # the live world's state at the base: k = 4, m = 1, x0 = 1, v0 = 0
        res = js["results"]
        assert [r_["value"] for r_ in res] == body["values"] and js["progress"]["done"] == 5
        for r_ in res[:4]:
            assert r_["t0"] == t_base
            assert abs(r_["measured"] - x_after(x0, v0, r_["value"], 0.7)) < 1e-10, r_
            if r_["value"] != 4.0:
                assert abs(r_["measured"] - x_after(x0, v0, 4.0, 0.7)) > 1e-3  # negative control
        assert res[4]["measured"] is None and "жёстче 100 Н/м" in res[4]["error"]
        assert not (run.dir / "sweeps" / "1.base.pkl").exists()  # the linked state goes with the sweep's end
        # determinism: the same sweep from the same (paused) world gives the same numbers
        js2 = await sweep_done(cl, rid, (await (await cl.post(url, json=body)).json())["n"])
        assert js2["base"]["t"] == t_base and [r_["measured"] for r_ in js2["results"]] == [r_["measured"] for r_ in res]
        # CSV of the table: its set-up in «#» lines (the base moment, the sampling: review F7), then the header
        r = await cl.get(f"/api/runs/{rid}/sweeps/{n1}", params={"format": "csv"})
        lines = (await r.text()).splitlines()
        meta, lines = [x for x in lines if x.startswith("#")], [x for x in lines if not x.startswith("#")]
        assert lines[0] == "\"Жёсткость пружины, Н/м\",\"Осциллятор 1: положение (в конце (1 замер)), м\",примечание"
        assert lines[1].split(",")[:2] == ["1.0", repr(res[0]["measured"])] and "жёстче" in lines[5]
        assert f"base_t={t_base!r}" in meta[2] and "readings=1;" in meta[2] and "sampler=frame" in meta[2]
        assert "от t = " in meta[1] and "мир в момент запуска свипа" in meta[1]
        # an object's parameter, the mean over a window
        js3 = await sweep_done(cl, rid, (await (await cl.post(url, json={
            "target": {"kind": "object", "obj": "o1", "param": "m"}, "values": [0.5, 2.0], "duration": 0.5,
            "measure": "o1.E", "stat": "mean_last", "window": 0.3, "n_samples": 30})).json())["n"])
        assert js3["state"] == "done" and js3["target_label"] == "Осциллятор 1: масса"
        assert js3["stat_text"] == "среднее за последние 300 мс (31 замер через 10 мс)"  # the sampling (F7)
        x0, v0 = xv_exact(js3["base"]["t"])
        for r_ in js3["results"]:
            assert abs(r_["measured"] - (0.5 * r_["value"] * v0 * v0 + 2.0 * x0 * x0)) < 1e-10
        # the memory budget: one value beyond it is refused, the others computed, the live world goes on
        js4 = await sweep_done(cl, rid, (await (await cl.post(url, json={
            "target": {"kind": "law", "id": "alloc_mb"}, "values": [8, 3000], "duration": 0.2, "measure": "E",
            "stat": "final"})).json())["n"])
        assert js4["state"] == "done" and abs(js4["results"][0]["measured"] - 2.0) < 1e-12
        assert "не хватает памяти" in js4["results"][1]["error"]
        assert run.running and run.meta["state"] == "running"
        # the live world was not touched: it goes on with k = 4 (its frames follow the exact motion)
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})
        await asyncio.sleep(1.0)
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "pause"})
        await asyncio.sleep(0.5)
        ser = await (await cl.get(f"/api/runs/{rid}/series", params={"ids": "o1.x"})).json()
        assert ser["t"][-1] > t_base + 0.5
        assert max(abs(x - xv_exact(t)[0]) for t, x in zip(ser["t"], ser["values"]["o1.x"])) < 1e-10
        # refusals before anything starts
        for b, word in (({**body, "target": {"kind": "law", "id": "nope"}}, "не закон"),
                        ({**body, "target": {"kind": "object", "obj": "o9", "param": "m"}}, "нет объекта"),
                        ({**body, "target": {"kind": "object", "obj": "o1", "param": "zz"}}, "нет параметра"),
                        ({**body, "values": list(range(1, 52))}, "не больше 50"),
                        ({**body, "values": [-1.0]}, "меньше наименьшего"),
                        ({**body, "measure": "nope"}, "нет измеряемой величины"),
                        ({**body, "stat": "mean_last", "window": 5.0}, "длиннее"),
                        ({**body, "duration": 0}, "положительное"),
                        ({**body, "n_samples": 5000}, "n_samples")):
            r = await cl.post(url, json=b)
            assert r.status == 400 and word in (await r.json())["error"], (b, await r.json())
        # above the budget: refused with the estimate
        monkeypatch.setenv("LFVIZ_SWEEP_BUDGET_S", "0.5")
        r = await cl.post(url, json={**body, "duration": 1e5})
        j = await r.json()
        assert r.status == 400 and "больше предела" in j["error"] and j["estimate"]["total_s"] > 0.5 and j["hint"]
        # cancel: a long sweep, a second one refused meanwhile, then cancelled; its computed values are kept
        monkeypatch.setenv("LFVIZ_SWEEP_BUDGET_S", "100000")
        st = await (await cl.post(url, json={**body, "values": [1.0, 2.0, 3.0], "duration": 1e6})).json()
        n_long = st["n"]
        await wait_for(lambda: json.loads((run.dir / "sweeps" / f"{n_long}.json").read_text())["state"] == "running",
                       timeout=60)
        r = await cl.post(url, json=body)
        assert r.status == 409 and "уже идёт свип" in (await r.json())["error"]
        lst = await (await cl.get(f"/api/runs/{rid}/sweeps")).json()
        assert [s["n"] for s in lst] == list(range(1, n_long + 1)) and lst[-1]["active"]
        proc = app[sweep.SWEEPS].active[(rid, n_long)]["proc"]
        r = await cl.delete(f"/api/runs/{rid}/sweeps/{n_long}")  # removing a running sweep is refused (F10)
        assert r.status == 409 and "сначала" in (await r.json())["error"] and proc.returncode is None
        r = await cl.post(f"/api/runs/{rid}/sweeps/{n_long}/cancel")
        assert r.status == 200 and (await r.json())["cancelled"] == n_long
        assert proc.returncode is not None  # the process is gone
        js5 = await (await cl.get(f"/api/runs/{rid}/sweeps/{n_long}")).json()
        assert js5["state"] == "cancelled" and not js5["active"] and js5["message"].startswith("Отменено")
        assert not (run.dir / "sweeps" / f"{n_long}.base.pkl").exists()
        r = await cl.post(f"/api/runs/{rid}/sweeps/{n_long}/cancel")  # a second click: nothing lost (F10)
        assert r.status == 200 and (await r.json())["already"] and (await r.json())["state"] == "cancelled"
        assert (await (await cl.get(f"/api/runs/{rid}/sweeps/{n_long}")).json())["state"] == "cancelled"
        r = await cl.delete(f"/api/runs/{rid}/sweeps/{n_long}")
        assert r.status == 200 and (await r.json())["removed"] == n_long
        assert (await cl.get(f"/api/runs/{rid}/sweeps/{n_long}")).status == 404
        # a suspended run: from its latest saved state, and the result says so
        await cl.post(f"/api/runs/{rid}/stop")
        await wait_for(lambda: not run.running, timeout=60)
        js6 = await sweep_done(cl, rid, (await (await cl.post(url, json={**body, "values": [9.0]})).json())["n"])
        assert js6["state"] == "done" and js6["base"]["source"] == "latest" and "приостановлен" in js6["base"]["note"]
        x0, v0 = xv_exact(js6["base"]["t"])
        assert abs(js6["results"][0]["measured"] - x_after(x0, v0, 9.0, 0.7)) < 1e-10
        assert not run.running  # the sweep did not resume the run


def test_sweeps_through_the_server(tmp_path, monkeypatch):
    asyncio.run(_server(tmp_path, monkeypatch))


async def _two_at_a_time(tmp_path, monkeypatch):
    """At most MAX_SWEEPS on the server at a time; a process killed from outside (the kernel's OOM killer, say) is
    reported as failed with the reason, never left «running»; the server's shutdown ends what still runs."""
    monkeypatch.setenv("LFVIZ_SWEEP_BUDGET_S", "100000")
    app = create_app(tmp_path / "runs", max_workers=3, idle_pause=600, idle_suspend=3600, worker_mem_gb=1.0)
    async with TestClient(TestServer(app)) as cl:
        runs = [await start_played(cl, app, play_s=1.5) for _ in range(3)]
        body = {"target": {"kind": "law", "id": "k"}, "values": [1.0, 2.0], "duration": 1e6, "measure": "o1.x",
                "stat": "final"}
        ns = []
        for rid, _ in runs[:2]:
            r = await cl.post(f"/api/runs/{rid}/sweep", json=body)
            assert r.status == 200, await r.json()
            ns.append((await r.json())["n"])
        r = await cl.post(f"/api/runs/{runs[2][0]}/sweep", json=body)
        assert r.status == 409 and "больше 2 сразу" in (await r.json())["error"]
        rid0, run0 = runs[0]
        await wait_for(lambda: json.loads((run0.dir / "sweeps" / f"{ns[0]}.json").read_text())["state"] == "running",
                       timeout=60)
        a = app[sweep.SWEEPS].active[(rid0, ns[0])]
        a["proc"].kill()
        await asyncio.wait_for(asyncio.shield(a["task"]), 30)
        js = await (await cl.get(f"/api/runs/{rid0}/sweeps/{ns[0]}")).json()
        assert js["state"] == "failed" and "сигнал 9" in js["message"] and not js["active"]
        r = await cl.post(f"/api/runs/{runs[2][0]}/sweep", json=body)  # a place is free again
        assert r.status == 200, await r.json()
        procs = [a["proc"] for a in app[sweep.SWEEPS].active.values()]
        assert len(procs) == 2
    for p in procs:  # the server's shutdown ended them
        assert p.returncode is not None


def test_two_sweeps_at_a_time(tmp_path, monkeypatch):
    asyncio.run(_two_at_a_time(tmp_path, monkeypatch))


# --- processing of the LB1 reviews (LB1-framework F1–F12, LB1-p02-ux Q3, X1) --------------------------------------
def test_an_object_parameter_equal_to_the_stored_one_is_applied_again():
    """F1: every value of an object's parameter is applied, also the one equal to its stored value — the stored value
    of a position or a velocity is where the object was put, not where it is. A handle parameter (the ball's x, vy)
    goes through the scene's ``edit``; any other (the oscillator's x, v) through ``set`` with the stored value applied
    again. Each value's number is the closed form of «set to that value at t0»; negative controls: the closed form of
    «left as it was» does not fit the stored value's row, and without the re-application (``_again`` disabled) that
    row is the unchanged world (the defect)."""
    h, data = _base(preset="ball", t=0.5)
    x0, v0 = h.sim.xv["o1"]
    bx, by, bvx, bvy = h.sim.balls["o2"]
    assert abs(x0 - 1.0) > 0.1 and abs(by - 0.5) > 0.1  # the objects moved away from their stored values
    T = 0.7

    def x_of(X, V):
        return x_after(X, V, 4.0, T)
    cases = [  # (target, values, the stored value, the measure, «set» closed form, «as it was», how)
        ({"kind": "object", "obj": "o1", "param": "x"}, [0.5, 1.0, 1.5], 1.0, "o1.x", lambda X: x_of(X, v0),
         x_of(x0, v0), "set"),
        ({"kind": "object", "obj": "o1", "param": "v"}, [-1.0, 0.0, 1.0], 0.0, "o1.x", lambda V: x_of(x0, V),
         x_of(x0, v0), "set"),
        ({"kind": "object", "obj": "o2", "param": "x"}, [0.5, 1.0, 1.5], 1.0, "o2.x", lambda X: x_of(X, bvx),
         x_of(bx, bvx), "edit"),
        ({"kind": "object", "obj": "o2", "param": "vy"}, [0.0, 0.3, 0.6], 0.3, "o2.y", lambda V: x_of(by, V),
         x_of(by, bvy), "edit"),
    ]
    for tg, values, stored, mid, ref, unchanged, how in cases:
        req = _req(target=tg, measure=mid, duration=T)
        for v in values:
            r = sweep.run_value(data, req, v, CLOCK)
            assert abs(r["measured"] - ref(v)) < 1e-12, (tg, v, r)
            assert r["how"] == (how + "_again" if v == stored and how == "set" else how), r["how"]
            if v == stored:
                assert abs(r["measured"] - unchanged) > 1e-3  # negative control: not the world as it was
    # the flag equal to its stored value cannot be applied again (bool): the row says so
    r = sweep.run_value(data, _req(target={"kind": "object", "obj": "o2", "param": "glow"}, measure="o2.x"), False, CLOCK)
    assert r["how"] == "set_same" and "без изменения" in r["note"]
    # negative control of the test itself: with the re-application disabled, the stored value's row is the old defect
    import unittest.mock as um
    with um.patch.object(sweep, "_again", lambda v: None):
        r = sweep.run_value(data, _req(target=cases[0][0], measure="o1.x", duration=T), 1.0, CLOCK)
    assert abs(r["measured"] - x_of(x0, v0)) < 1e-12 and abs(r["measured"] - x_of(1.0, v0)) > 1e-3


def _spec(tmp_path, data, req, values, budget=600.0, viz="p97_osc", t=None):
    (tmp_path / "1.base.pkl").write_bytes(data)
    spec = {"n": 1, "run": "test", "viz": viz, "state": "starting", "budget_s": budget,
            "request": {**req, "values": values}, "base": {"path": str(tmp_path / "1.base.pkl"), "t": t},
            "progress": {"done": 0, "total": len(values)}, "results": []}
    (tmp_path / "1.json").write_text(json.dumps(spec))
    return tmp_path / "1.json"


def _process(path, **env):
    return subprocess.Popen([sys.executable, "-m", "lfviz.sweep", "--file", str(path)], env=_env(**env),
                            cwd=str(registry.ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def test_the_budget_holds_inside_one_advance(tmp_path):
    """F2: a sweep whose one reading (stat final) asks for a long advance stops by itself once its measured cost
    projects it beyond 1.5 × the budget — after PROBE_S of advancing, not after the advance — and keeps nothing it did
    not finish; a world that has not computed (no measured cost) is covered by the same measurement. Negative control:
    the same sweep with a duration it can finish is done."""
    _, data = _base(t=0.0)
    req = _req(duration=1e7)  # p97: ~0.3 ms per world second -> ~50 min for one value
    p = _process(_spec(tmp_path, data, req, [4.0, 9.0], budget=20.0))
    t0 = time.monotonic()
    out, _ = p.communicate(timeout=120)
    wall = time.monotonic() - t0
    spec = json.loads((tmp_path / "1.json").read_text())
    assert p.returncode == 0, out.decode()[-2000:]
    assert spec["state"] == "over_budget" and spec["results"] == [], spec
    assert wall < sweep.PROBE_S + 15 and "по замеренной цене счёта весь свип занял бы" in spec["message"], (wall, spec)
    # negative control: a duration it can finish
    p = _process(_spec(tmp_path, data, _req(duration=50.0), [4.0, 9.0], budget=20.0))
    p.communicate(timeout=120)
    spec = json.loads((tmp_path / "1.json").read_text())
    assert spec["state"] == "done" and len(spec["results"]) == 2


def test_a_contract_breaking_measure_is_named(tmp_path):
    """LB1-p02-ux Q3: a world whose ``measure()`` does not return a dict breaks the instruments' contract: the sweep
    stops at once and says so (not «AttributeError» at every value). Negative control: the same world with a
    ``measure()`` that keeps the contract is measured."""
    h, data = _base()
    for mode, ok in (("tuple", False), ("1", True)):
        path = _spec(tmp_path, data, _req(), [4.0, 9.0], t=h.sim.t)
        p = subprocess.run([sys.executable, "-m", "lfviz.sweep", "--file", str(path)], env=_env(P97_MEASURE=mode),
                           cwd=str(registry.ROOT), capture_output=True, timeout=120)
        spec = json.loads(path.read_text())
        if ok:
            assert spec["state"] == "done" and spec["sampler"] == "measure", spec
        else:
            assert spec["state"] == "failed" and spec["results"] == [], spec
            assert "нарушает договор приборов" in spec["message"] and "measure() вернул tuple" in spec["message"]
            assert "AttributeError" not in spec["message"]


def test_nothing_measured_is_not_done(tmp_path):
    """LB1-p02-ux X7: a sweep in which no value was measured is not «готово»."""
    h, data = _base()
    path = _spec(tmp_path, data, _req(), [1000.0, 2000.0], t=h.sim.t)  # the world refuses k > 100
    subprocess.run([sys.executable, "-m", "lfviz.sweep", "--file", str(path)], env=_env(), cwd=str(registry.ROOT),
                   capture_output=True, timeout=120)
    spec = json.loads(path.read_text())
    assert spec["state"] == "failed" and spec["message"].startswith("Не измерено ни одно из 2 значений: ")
    assert "жёстче 100 Н/м" in spec["message"]


def test_object_parameters_of_a_real_playground_are_validated_from_its_header():
    """LB1-p02-ux X1: the playgrounds build their palettes per world (``self.PALETTE``), so the class has none; the
    request is checked against the palette of the world's header in the record. Negative control: without it (the
    class's palette alone, the old way) the same request is refused «есть: нет»."""
    from lfviz import instruments as I
    h = Harness_of("p04_fluids", "cylinder_re20")
    viz = registry.load("p04_fluids")
    assert not getattr(viz["simulation"], "PALETTE", {})  # per instance only
    idx = I.Index()
    w = idx.worlds[1] = I.WorldInfo(1)
    for m in h.msgs_meta:
        idx._note(w, m)
    oid = next(k for k, o in w.objects.items() if o["label"] == "Цилиндр")
    mid = next(iter(w.current))
    body = {"target": {"kind": "object", "obj": oid, "param": "radius"}, "values": [0.04, 0.05], "duration": 0.01,
            "measure": mid, "stat": "final"}
    req, info = sweep.validate(viz, idx, body)
    assert req["target"] == {"kind": "object", "obj": oid, "param": "radius"} and req["values"] == [0.04, 0.05]
    assert info["target_handle"] is False and info["target_label"] == "Цилиндр: Радиус, м"
    req, info = sweep.validate(viz, idx, {**body, "target": {"kind": "object", "obj": oid, "param": "x"}})
    assert info["target_handle"] is True  # the disk's position is a handle: a sweep moves it by «edit»
    with pytest.raises(sweep.Refused, match="меньше наименьшего"):  # the parameter's own range
        sweep.validate(viz, idx, {**body, "values": [-1.0]})
    w.palette = {}
    with pytest.raises(sweep.Refused, match="есть: нет"):
        sweep.validate(viz, idx, body)


class Harness_of:
    """A real playground's first messages (its header with the palette, its scene) without the server."""

    def __init__(self, viz_id, preset):
        from harness import Harness
        self.h = Harness(viz_id, preset, seed=1)
        self.msgs_meta = [m for m, _ in self.h.msgs]


def test_malformed_requests_are_400_not_500():
    """F12: ids that are not strings, and a measure declared once but no longer measured, are refused in words."""
    from lfviz import instruments as I
    viz = registry.load("p97_osc")
    idx = I.Index()
    w = idx.worlds[1] = I.WorldInfo(1, palette={"osc": {"type": "osc", "params": [
        {"id": "x", "label": "x", "type": "float", "default": 1.0, "unit": "м"}]}})
    w.objects = {"o1": {"type": "osc", "label": "Осциллятор 1", "values": {"x": 1.0}}}
    w.decl = {"o1.x": {"id": "o1.x", "label": "x", "unit": "м", "of": "o1"},
              "o2.x": {"id": "o2.x", "label": "x", "unit": "м", "of": "o2"}}
    w.current = {"o1.x"}
    good = {"target": {"kind": "object", "obj": "o1", "param": "x"}, "values": [1.0], "duration": 1.0,
            "measure": "o1.x"}
    sweep.validate(viz, idx, good)
    for bad, word in (({**good, "target": {"kind": "law", "id": ["k"]}}, "идентификатор"),
                      ({**good, "target": {"kind": "object", "obj": ["o1"], "param": "x"}}, "идентификатор"),
                      ({**good, "target": {"kind": "object", "obj": "o1", "param": {"a": 1}}}, "идентификатор"),
                      ({**good, "measure": ["o1.x"]}, "нет измеряемой величины"),
                      ({**good, "stat": ["max"]}, "«stat»"),
                      ({**good, "measure": "o2.x"}, "сейчас не измеряет")):
        with pytest.raises(sweep.Refused, match=word):
            sweep.validate(viz, idx, bad)


async def _server_lb1(tmp_path, monkeypatch):
    """Through the server: F3 (a deleted run's sweep ends within seconds and frees its place; a cancel by its key
    still answers), F2 (the server ends a process whose single step outlasts the budget), F6 (checkpoint_now and stop
    refused on the client routes), F9 (the process's budget and OOM priority; a sweep that would not fit is refused),
    F12 (Unicode digits)."""
    monkeypatch.setenv("LFVIZ_SWEEP_BUDGET_S", "100000")
    app = create_app(tmp_path / "runs", max_workers=3, idle_pause=600, idle_suspend=3600, worker_mem_gb=1.0)
    async with TestClient(TestServer(app)) as cl:
        SW = app[sweep.SWEEPS]
        rid, run = await start_played(cl, app, play_s=1.5)
        body = {"target": {"kind": "law", "id": "k"}, "values": [1.0, 2.0], "duration": 1e6, "measure": "o1.x",
                "stat": "final"}
        # F6: a viewer cannot make the world checkpoint itself, nor stop its worker
        n_ck = sum(1 for e in run.entries if e.kind == "checkpoint")
        for c in ("checkpoint_now", "stop"):
            r = await cl.post(f"/api/runs/{rid}/command", json={"cmd": c, "args": {"tag": "x" * 1000}})
            assert r.status == 403 and "только сам сервер" in (await r.json())["error"]
        ws = await cl.ws_connect(f"/ws/runs/{rid}")
        await ws.send_str(json.dumps({"cmd": "checkpoint_now", "args": {"tag": "ws"}}))
        got = None
        for _ in range(200):
            m = await ws.receive(timeout=10)
            if m.type.name == "TEXT":
                got = json.loads(m.data)
                break
        await ws.close()
        assert got and "только сам сервер" in got["error"]
        await asyncio.sleep(0.5)
        assert sum(1 for e in run.entries if e.kind == "checkpoint") == n_ck and run.running
        assert (await cl.post(f"/api/runs/{rid}/command", json=["play"])).status == 400
        # F9: the process's memory budget is half a worker's, and the kernel ends it first
        st = await (await cl.post(f"/api/runs/{rid}/sweep", json=body)).json()
        n = st["n"]
        await wait_for(lambda: json.loads((run.dir / "sweeps" / f"{n}.json").read_text())["state"] == "running", 60)
        proc = SW.active[(rid, n)]["proc"]
        assert open(f"/proc/{proc.pid}/oom_score_adj").read().strip() == "1000"
        lim = [ln for ln in open(f"/proc/{proc.pid}/limits") if ln.startswith("Max data size")][0].split()
        assert int(lim[3]) == 512 * 2 ** 20 == sweep.sweep_mem(app[MGR].worker_mem) < app[MGR].worker_mem
        # F3: the run deleted under its sweep: the process ends within seconds, its place is free again
        r = await cl.delete(f"/api/runs/{rid}")
        assert r.status == 200
        t0 = time.monotonic()
        await wait_for(lambda: proc.returncode is not None and (rid, n) not in SW.active, timeout=10)
        assert time.monotonic() - t0 < 5
        assert (await cl.post(f"/api/runs/{rid}/sweeps/{n}/cancel")).status == 404  # gone with its run
        # F12: Unicode digits are not a sweep's number
        rid2, run2 = await start_played(cl, app, play_s=1.5)
        for path in (f"/api/runs/{rid2}/sweeps/%C2%B2", f"/api/runs/{rid2}/sweeps/%D9%A1"):
            assert (await cl.get(path)).status == 404 and (await cl.delete(path)).status == 404
            assert (await cl.post(path + "/cancel")).status == 404
        # F2: one step of the world longer than the budget — the server ends the process (grace shortened); a world
        # only stepped (its cost unknown), the swept value making each step cost 20 s
        monkeypatch.setenv("LFVIZ_SWEEP_BUDGET_S", "2")
        monkeypatch.setattr(sweep, "WATCH_GRACE_S", 2.0)
        r = await cl.post("/api/runs", json={"viz": "p97_osc", "preset": "one", "seed": 5})
        rid3 = (await r.json())["id"]
        run3 = app[MGR].get(rid3)
        await wait_for(lambda: any(e.kind == "header" for e in run3.entries))
        await cl.post(f"/api/runs/{rid3}/command", json={"cmd": "step", "args": {"dt": 0.1}})
        await asyncio.sleep(1.0)
        st = await (await cl.post(f"/api/runs/{rid3}/sweep", json={**body, "target": {"kind": "law", "id": "cost_ms"},
                                                                   "values": [4e5], "duration": 0.05})).json()
        assert "n" in st and st["estimate"]["known"] is False, st
        t0 = time.monotonic()
        js = await sweep_done(cl, rid3, st["n"], timeout=60)
        assert js["state"] == "over_budget" and js["message"].startswith("Остановлено сервером"), js
        assert time.monotonic() - t0 < 1.5 * 2 + 2.0 + 5  # not the 20 s the step takes
        # F9: a sweep that would not fit its budget is refused before it starts
        monkeypatch.setenv("LFVIZ_SWEEP_BUDGET_S", "100000")
        monkeypatch.setenv("LFVIZ_SWEEP_MEM_GB", "0.1")
        r = await cl.post(f"/api/runs/{rid2}/sweep", json={**body, "duration": 0.1})
        j = await r.json()
        assert r.status == 409 and "свипу отведено 102 МБ" in j["error"] and not SW.active, j
        assert not list((run2.dir / "sweeps").glob("*.base.pkl"))


def test_lb1_server_side(tmp_path, monkeypatch):
    asyncio.run(_server_lb1(tmp_path, monkeypatch))


async def _estimate(tmp_path):
    """F4: the estimate from the record counts only the frames computed while the world played (a paused world's frame
    also counts the runner's wait for the command): within ×3 of the advance the sweep then measures. A world only
    stepped has no measured cost (it measures itself) — the old estimate, every frame's cpu_ms over its world time, was
    more than ×3 too high there (the negative control of the test)."""
    app = create_app(tmp_path / "runs", max_workers=2, idle_pause=600, idle_suspend=3600, worker_mem_gb=1.0)
    async with TestClient(TestServer(app)) as cl:
        r = await cl.post("/api/runs", json={"viz": "p97_osc", "preset": "one", "seed": 5,
                                             "params": {"cost_ms": 40.0}})
        rid = (await r.json())["id"]
        run = app[MGR].get(rid)
        await wait_for(lambda: any(e.kind == "header" for e in run.entries))
        for _ in range(20):  # stepped only
            await cl.post(f"/api/runs/{rid}/command", json={"cmd": "step", "args": {"dt": 0.05}})
            await asyncio.sleep(0.04)
        await asyncio.sleep(1.0)
        body = {"target": {"kind": "law", "id": "k"}, "values": [4.0, 9.0], "duration": 20.0, "measure": "E",
                "stat": "final"}
        e = (await (await cl.post(f"/api/runs/{rid}/sweep", json={**body, "estimate": True})).json())["estimate"]
        assert e["known"] is False and "не измерила" in e["text"]
        fr = [protocol.peek_meta(run._read(x, {})) for x in run.entries if x.is_frame]
        naive = sum(f["cpu_ms"] for f in fr[1:]) / (fr[-1]["t"] - fr[0]["t"])  # the old estimator's numbers
        # played: the estimate against the sweep's own measurement
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})
        await asyncio.sleep(3.0)
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "pause"})
        await asyncio.sleep(0.8)
        e = (await (await cl.post(f"/api/runs/{rid}/sweep", json={**body, "estimate": True})).json())["estimate"]
        assert e["known"] and e["frames_measured"] > 10, e
        js = await sweep_done(cl, rid, (await (await cl.post(f"/api/runs/{rid}/sweep", json=body)).json())["n"])
        adv = sum(r_["advance_s"] for r_ in js["results"]) / len(js["results"])
        est_adv = body["duration"] * e["ms_per_t"] / 1e3
        assert 1 / 3 < est_adv / adv < 3, (est_adv, adv)
        assert naive * body["duration"] / 1e3 / adv > 3, (naive, adv)  # negative control: the old way was off
        await cl.post(f"/api/runs/{rid}/stop")


def test_the_estimate_counts_computation_only(tmp_path):
    asyncio.run(_estimate(tmp_path))
