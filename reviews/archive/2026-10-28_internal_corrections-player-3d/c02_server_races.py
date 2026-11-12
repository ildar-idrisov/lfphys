"""C1 review, check 02: the server's suspend / resume under concurrency (own server on 127.0.0.1:8502, temporary runs
directory; never the shared server).

T1  two viewers press ⏺ on a suspended run at the same moment (two concurrent commands): how many workers are spawned
    for the run, and is its record still a valid stream?
T2  a suspension arriving while a resume is still rebuilding the world, and a `set` sent during a rebuild.
T3  ⏺ on a suspended run when every worker is busy with viewed runs: what the viewer receives.

Run:
  docker run --rm --name lf-c1rev-c02 --network host -v <engine>:/lf:ro -v <this folder>:/rev -v <runs dir>:/runs:ro \
      -w /lf/visualizations light-funnel-viz python3 /rev/c02_server_races.py
Output: /rev/out/c02_server_races.txt
"""
import asyncio
import json
import struct
import sys
import time

import aiohttp

sys.path[:0] = ["/lf/visualizations/server"]
from lfviz import protocol  # noqa: E402

BASE = "http://127.0.0.1:8502"
OUT = []


def log(s):
    OUT.append(s)
    print(s, flush=True)


async def post(s, path, body=None):
    async with s.post(BASE + path, json=body or {}) as r:
        return r.status, await r.json()


async def get(s, path):
    async with s.get(BASE + path) as r:
        return r.status, await r.json()


def stream_check(rid):
    """Parse the record as the server does on start; count messages, workers' 'start' states, notices."""
    data = open(f"/runs/{rid}/stream.lfrec", "rb").read()
    n, types, tail = 0, {}, len(data)
    pos = len(protocol.MAGIC)
    bad = None
    for off, msg in protocol.iter_stream(data, pos):
        try:
            m = protocol.peek_meta(msg)
        except Exception as e:  # noqa: BLE001
            bad = f"undecodable message at {off}: {e!r}"
            break
        n += 1
        k = m.get("type")
        if k == "state" and m.get("reason") == "start":
            k = "state:start"
        if k == "notice" and "восстановлен" in (m.get("text") or ""):
            k = "notice:restored"
        types[k] = types.get(k, 0) + 1
        tail = off + 4 + len(msg)
    return n, types, len(data) - tail, bad


async def wait_state(s, rid, want, timeout=60):
    t0 = time.time()
    while time.time() - t0 < timeout:
        _, m = await get(s, f"/api/runs/{rid}")
        if m.get("state") in want:
            return m
        await asyncio.sleep(0.2)
    return m


async def t1(s):
    log("\n[T1] two concurrent ⏺ (play) on a suspended run")
    st, r = await post(s, "/api/runs", {"viz": "v01_light_travel"})
    rid = r["id"]
    await post(s, f"/api/runs/{rid}/command", {"cmd": "play"})
    await asyncio.sleep(4)
    await post(s, f"/api/runs/{rid}/stop")
    m = await wait_state(s, rid, ("suspended",))
    log(f"  run {rid}: state {m['state']}, sim_t {m['sim_t']:.4g}")
    res = await asyncio.gather(post(s, f"/api/runs/{rid}/command", {"cmd": "play"}),
                               post(s, f"/api/runs/{rid}/command", {"cmd": "play"}))
    log(f"  answers: {res}")
    await asyncio.sleep(5)
    _, m = await get(s, f"/api/runs/{rid}")
    log(f"  meta: state {m['state']}, resumed {m.get('resumed')}, pid {m.get('pid')}")
    _, h = await get(s, "/api/health")
    log(f"  health: running {h.get('running')} (max {h.get('max_workers')})")
    await post(s, f"/api/runs/{rid}/stop")
    await asyncio.sleep(3)
    n, types, garbage, bad = stream_check(rid)
    log(f"  record: {n} messages, trailing bytes not parsed {garbage}, {bad or 'all decodable'}; "
        f"state:start×{types.get('state:start', 0)}, notice:restored×{types.get('notice:restored', 0)}, "
        f"header×{types.get('header', 0)}")
    return rid


async def t2(s):
    log("\n[T2] a suspension during a rebuild; a `set` during a rebuild (v04: a long record rebuilds in seconds)")
    st, r = await post(s, "/api/runs", {"viz": "v04_orbits"})
    rid = r["id"]
    await post(s, f"/api/runs/{rid}/command", {"cmd": "speed", "args": {"value": 1e9}})
    await post(s, f"/api/runs/{rid}/command", {"cmd": "play"})
    await asyncio.sleep(12)
    await post(s, f"/api/runs/{rid}/stop")
    m = await wait_state(s, rid, ("suspended",))
    log(f"  run {rid}: state {m['state']}, sim_t {m['sim_t']:.6g}")
    t0 = time.time()
    st, a = await post(s, f"/api/runs/{rid}/resume")
    log(f"  resume answered in {time.time() - t0:.2f} s: {st} {a}")
    st, a = await post(s, f"/api/runs/{rid}/command", {"cmd": "set", "args": {"values": {"speed": 1.05}}})
    log(f"  set during the rebuild: {st} {a}")
    await asyncio.sleep(0.3)
    st, a = await post(s, f"/api/runs/{rid}/stop")
    log(f"  stop during the rebuild: {st} {a}")
    m = await wait_state(s, rid, ("suspended", "failed", "stopped", "finished"))
    log(f"  after: state {m['state']}, stop_reason {m.get('stop_reason')}, returncode {m.get('returncode')}")
    st, a = await post(s, f"/api/runs/{rid}/resume")
    log(f"  resume again: {st} {a}")
    await asyncio.sleep(8)
    _, m = await get(s, f"/api/runs/{rid}")
    log(f"  then: state {m['state']}, resumed {m.get('resumed')}, sim_t {m['sim_t']:.6g}, errors {m.get('errors')}")
    await post(s, f"/api/runs/{rid}/stop")
    await asyncio.sleep(2)
    n, types, garbage, bad = stream_check(rid)
    # was the `set` sent during the first rebuild applied (a 'live' after it)?
    data = open(f"/runs/{rid}/stream.lfrec", "rb").read()
    sets = [protocol.peek_meta(msg) for _, msg in protocol.iter_stream(data, len(protocol.MAGIC))]
    cmds = [(m.get("t"), m.get("args")) for m in sets if m.get("type") == "command"]
    log(f"  record: {n} messages; commands recorded {cmds}; {bad or 'all decodable'}")
    return rid


async def t3(s):
    log("\n[T3] ⏺ on a suspended run while both workers serve viewed runs (max_workers = 2 on this server)")
    _, r = await post(s, "/api/runs", {"viz": "v01_light_travel"})
    rid = r["id"]
    await asyncio.sleep(1)
    await post(s, f"/api/runs/{rid}/stop")
    await wait_state(s, rid, ("suspended",))
    others, wss = [], []
    for _ in range(2):
        _, o = await post(s, "/api/runs", {"viz": "v01_light_travel"})
        others.append(o["id"])
        ws = await s.ws_connect(f"ws://127.0.0.1:8502/ws/runs/{o['id']}")
        wss.append(ws)
    ws = await s.ws_connect(f"ws://127.0.0.1:8502/ws/runs/{rid}")
    got = []
    await ws.send_str(json.dumps({"cmd": "play", "args": {}}))
    t0 = time.time()
    while time.time() - t0 < 4:
        try:
            msg = await ws.receive(timeout=0.5)
        except asyncio.TimeoutError:
            continue
        if msg.type == aiohttp.WSMsgType.TEXT:
            got.append(("text", msg.data))
        elif msg.type == aiohttp.WSMsgType.BINARY:
            m = protocol.peek_meta(msg.data)
            if m.get("type") in ("history_end", "error", "notice", "state", "closed"):
                got.append((m.get("type"), {k: m.get(k) for k in ("live", "state", "resumable", "text", "playing")}))
    log(f"  the viewer of the suspended run received: {got}")
    for w in wss + [ws]:
        await w.close()
    await asyncio.sleep(1)
    for o in others:
        await post(s, f"/api/runs/{o}/stop")


async def main():
    async with aiohttp.ClientSession() as s:
        for t in (t1, t2, t3):
            try:
                await t(s)
            except Exception as e:  # noqa: BLE001
                import traceback
                log(f"  ERROR {e!r}\n{traceback.format_exc(limit=3)}")
    with open("/rev/out/c02_server_races.txt", "w") as f:
        f.write("\n".join(OUT) + "\n")


asyncio.run(main())
