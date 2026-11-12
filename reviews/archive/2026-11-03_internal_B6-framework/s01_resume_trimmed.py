# Review B6-framework, script s01: resuming a playground's buffered record after trimming.
# Runs the real server (aiohttp test client) and real workers on the toy section p99_toy (LFVIZ_EXTRA).
#   A: recording on at the start (the header's segment protected), off later, a scene change in an unprotected
#      segment that is then trimmed; no usable checkpoint (code hash changed, as in tests/test_playground.py) ->
#      the server accepts the resume (complete=True) and the worker replays a script with a hole.
#   B: recording never on, the header trimmed (complete=False); the latest checkpoint passes the server's checks but
#      fails to load in the worker (here: corrupt bytes; in life e.g. a GPU array that cannot be put back) -> the worker
#      falls back to "rebuild from the start" with the kept tail only.
#   C: world 1 protected (recording on), world 2 started later and its header trimmed -> _latest_world() takes t_end over
#      the entries of world 1 too, and the resumed world 2 is advanced to world 1's time.
# Usage (from engine/):
#   docker run --rm --name lf-b6rf-s01 -v $PWD:/lf:ro -v <review>:/out -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 \
#     -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server:/lf/lfphys \
#     -e LFVIZ_EXTRA=/lf/visualizations/tests/playgrounds -e P99_CKPT=0.4 -w /lf/visualizations light-funnel-viz \
#     python3 /out/s01_resume_trimmed.py
import asyncio
import sys
import tempfile
from pathlib import Path

import numpy as np
from aiohttp.test_utils import TestClient, TestServer

from lfviz import checkpoint as CK, protocol
from lfviz.app import MGR, create_app


async def wait(cond, n=600, dt=0.05):
    for _ in range(n):
        if cond():
            return True
        await asyncio.sleep(dt)
    raise AssertionError("timeout")


def frames(run, after=None):
    """(t, ids, pos) of the frames in the record, optionally only those after entry index `after`."""
    out, cache = [], {}
    for i, e in enumerate(run.entries):
        if not e.is_frame or (after is not None and i <= after):
            continue
        m, b = protocol.decode(run._read(e, cache))
        out.append((m["t"], m["ids"], np.asarray(b["pos"]).reshape(-1, 2)))
    return out


def find(run, typ, pred=lambda m: True):
    cache, out = {}, []
    for i, e in enumerate(run.entries):
        m = protocol.peek_meta(run._read(e, cache))
        if m.get("type") == typ and pred(m):
            out.append((i, e.seg, m))
    return out


def age_and_trim(run):
    for sg in run.meta["buffer"]["segs"][:-1]:
        sg["wall0"] -= 10_000
    run._trim()


async def cmd(cl, rid, c, args=None):
    r = await cl.post(f"/api/runs/{rid}/command", json={"cmd": c, "args": args or {}})
    assert r.status == 200, (c, r.status, await r.text())


async def scenario_a(cl, mgr):
    print("=== A: recording on/off leaves a hole between the header and the tail; no usable checkpoint ===")
    rid = (await (await cl.post("/api/runs", json={"viz": "p99_toy", "preset": "two", "seed": 3})).json())["id"]
    run = mgr.get(rid)
    await cmd(cl, rid, "play")
    st = await (await cl.post(f"/api/runs/{rid}/record", json={"on": True})).json()
    print("recording on:", st["recording"], "protected", st["protected"])
    await wait(lambda: len(run.meta["buffer"]["segs"]) >= 3)
    st = await (await cl.post(f"/api/runs/{rid}/record", json={"on": False})).json()
    print("recording off: protected", st["protected"])
    n = len(run.meta["buffer"]["segs"])
    await wait(lambda: len(run.meta["buffer"]["segs"]) >= n + 2)
    await cmd(cl, rid, "scene", {"op": "set", "id": "o1", "values": {"vx": 5.0}})
    await asyncio.sleep(0.3)
    sets = find(run, "command", lambda m: m.get("cmd") == "scene")
    print("the scene change is recorded in segment", [s for _, s, _ in sets], "at t =", [round(m["t"], 3) for *_, m in sets])
    n = len(run.meta["buffer"]["segs"])
    await wait(lambda: len(run.meta["buffer"]["segs"]) >= n + 4)
    age_and_trim(run)
    print("segments kept:", [sg["k"] for sg in run.meta["buffer"]["segs"]], "trimmed:", run.meta["buffer"]["trimmed"])
    print("scene change still in the record:", bool(find(run, "command", lambda m: m.get("cmd") == "scene")))
    print("header in the record:", bool(find(run, "header")))
    await cl.post(f"/api/runs/{rid}/stop", json={})
    last = frames(run)[-1]
    print(f"before suspension: t = {last[0]:.4f}, o1 x = {last[2][0][0]:.4f} (vx = 5 since the change)")
    real = CK.files_hash
    CK.files_hash = lambda root, files: "another-code"  # as tests/test_playground.py: no usable checkpoint
    try:
        w = run._latest_world()
        print("_latest_world: complete =", w["complete"], " checkpoint =", w["checkpoint"],
              " script commands =", [c.get("cmd") for c in w["script"] if "cmd" in c])
        n_before = len(run.entries)
        r = await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})  # as the player's button: resume, then play
        print("POST command play (resumes) ->", r.status, (await r.json()))
    finally:
        CK.files_hash = real
    await wait(lambda: len(frames(run, n_before)) >= 3)
    print("resumed how:", run.meta["resumes"][-1].get("from"))
    t1, ids, pos = frames(run, n_before)[0]
    print(f"after resume: t = {t1:.4f}, o1 x = {pos[0][0]:.4f};"
          f" expected about {last[2][0][0] + 5.0 * (t1 - last[0]):.4f} (continuation with vx = 5)")
    await cl.post(f"/api/runs/{rid}/stop", json={})


async def scenario_b(cl, mgr):
    print("=== B: header trimmed; the checkpoint passes the server's checks but does not load in the worker ===")
    rid = (await (await cl.post("/api/runs", json={"viz": "p99_toy", "preset": "two", "seed": 3})).json())["id"]
    run = mgr.get(rid)
    await cmd(cl, rid, "play")
    await wait(lambda: len(run.meta["buffer"]["segs"]) >= 2)
    await cmd(cl, rid, "scene", {"op": "set", "id": "o1", "values": {"vx": 5.0}})
    n = len(run.meta["buffer"]["segs"])
    await wait(lambda: len(run.meta["buffer"]["segs"]) >= n + 4)
    age_and_trim(run)
    print("segments kept:", [sg["k"] for sg in run.meta["buffer"]["segs"]], "header in the record:",
          bool(find(run, "header")), "scene change in the record:",
          bool(find(run, "command", lambda m: m.get("cmd") == "scene")))
    await cl.post(f"/api/runs/{rid}/stop", json={})
    last = frames(run)[-1]
    w = run._latest_world()
    print("_latest_world: complete =", w["complete"], " checkpoint file =", Path(w["checkpoint"]["file"]).name)
    Path(w["checkpoint"]["file"]).write_bytes(b"\x00" * 64)  # a file that exists and has the right name, unloadable
    n_before = len(run.entries)
    r = await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})
    print("POST command play (resumes) ->", r.status, (await r.json()))
    await wait(lambda: len(frames(run, n_before)) >= 3)
    for _, _, m in find(run, "notice")[-3:]:
        print("notice:", m["text"][:160])
    print("resumed how:", run.meta["resumes"][-1].get("from"), "| errors:", run.meta.get("errors", [])[-1:] or "none")
    t1, ids, pos = frames(run, n_before)[0]
    print(f"before suspension: t = {last[0]:.4f}, o1 x = {last[2][0][0]:.4f}; after resume: t = {t1:.4f}, "
          f"o1 x = {pos[0][0]:.4f}; expected about {last[2][0][0] + 5.0 * (t1 - last[0]):.4f}")
    await cl.post(f"/api/runs/{rid}/stop", json={})


async def scenario_c(cl, mgr):
    print("=== C: world 1 kept (recording on), world 2's header trimmed: t_end of the resume ===")
    rid = (await (await cl.post("/api/runs", json={"viz": "p99_toy", "preset": "two", "seed": 3})).json())["id"]
    run = mgr.get(rid)
    await cmd(cl, rid, "speed", {"value": 50.0})
    await cmd(cl, rid, "play")
    await cl.post(f"/api/runs/{rid}/record", json={"on": True})
    await asyncio.sleep(2.0)
    await cl.post(f"/api/runs/{rid}/record", json={"on": False})
    print("world 1 reached t =", round(run.meta["sim_t"], 3))
    n = len(run.meta["buffer"]["segs"])
    await wait(lambda: len(run.meta["buffer"]["segs"]) >= n + 2)
    await cmd(cl, rid, "new_world", {"preset": "two", "seed": 4})
    await cmd(cl, rid, "play")
    n = len(run.meta["buffer"]["segs"])
    await wait(lambda: len(run.meta["buffer"]["segs"]) >= n + 5)
    age_and_trim(run)
    heads = [m.get("world") for _, _, m in find(run, "header")]
    print("headers in the record:", heads, " headers kept apart:", sorted(run.headers))
    await cl.post(f"/api/runs/{rid}/stop", json={})
    last = frames(run)[-1]
    w = run._latest_world()
    print(f"world 2 last frame t = {last[0]:.4f};  _latest_world: world {w['header'].get('world')}, "
          f"t_end = {w['t_end']:.4f}, checkpoint t = {w['checkpoint']['t']:.4f}")
    n_before = len(run.entries)
    r = await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})
    print("POST command play (resumes) ->", r.status)
    await wait(lambda: len(frames(run, n_before)) >= 2)
    t1, ids, pos = frames(run, n_before)[0]
    print(f"first frame after the resume: t = {t1:.4f} (world 2 was at {last[0]:.4f})")
    await cl.post(f"/api/runs/{rid}/stop", json={})


async def main():
    with tempfile.TemporaryDirectory() as td:
        app = create_app(Path(td), max_workers=2, idle_pause=600, idle_suspend=3600)
        async with TestClient(TestServer(app)) as cl:
            mgr = app[MGR]
            for f in (scenario_a, scenario_b, scenario_c):
                try:
                    await f(cl, mgr)
                except Exception as e:  # noqa: BLE001
                    import traceback
                    traceback.print_exc(file=sys.stdout)
                    print("scenario failed:", e)


asyncio.run(main())
