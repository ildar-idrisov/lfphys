# Review B6-framework, script s12: a scene file between the WebSocket's message limit (1 MB, app.ws_run) and the json
# parameter's limit (params.JSON_MAX = 2 000 000 characters): loading it in the player sends new_world over the socket.
# Against the PRIVATE server of b01_browser.mjs (port 8531). Usage:
#   docker run --rm --network host --name lf-b6rf-s12 -v <engine>:/lf:ro -v <review>:/out -e PYTHONPATH=... light-funnel-viz \
#     python3 /out/s12_ws_size.py 8531
import asyncio
import json
import sys

import aiohttp

base = f"http://127.0.0.1:{sys.argv[1] if len(sys.argv) > 1 else 8531}"
objs = [{"type": "test", "label": f"тело {i}", "values": {"x": 2.0 + i * 1e-3, "y": 0.0, "z": 0.0, "vmode": "manual",
                                                          "vx": 0.0, "vy": 1.0, "vz": 0.0},
         "state": {"x": [2.0 + i * 1e-3, 0.0, 0.0], "v": [0.0, 6.28, 0.0]}, "note": "x" * 4500} for i in range(299)]
objs.insert(0, {"type": "star", "values": {"mass": 1.0}})
scene = {"format": "lfscene", "version": 1, "viz": "p01_gravity", "laws": {"laws": "newton", "collisions": "merge"},
         "t": 0.0, "objects": objs}
text = json.dumps({"cmd": "new_world", "args": {"params": {**scene["laws"], "scene": scene}, "seed": None}})
print(f"scene as JSON: {len(json.dumps(scene)) / 1e6:.2f} M characters (limit of the json parameter: 2.0 M); "
      f"the WebSocket message: {len(text) / 2**20:.2f} MiB (limit 1 MiB)")


async def main():
    async with aiohttp.ClientSession() as s:
        r = await s.post(base + "/api/runs", json={"viz": "p01_gravity", "params": {**scene["laws"], "scene": scene}})
        print("POST /api/runs with this scene (the catalogue's way):", r.status, (await r.text())[:80])
        rid = (await r.json())["id"]
        ws = await s.ws_connect(f"{base}/ws/runs/{rid}", max_msg_size=0)
        while True:  # the history
            m = await ws.receive()
            if m.type == aiohttp.WSMsgType.BINARY and b"history_end" in m.data[:200]:
                break
        await ws.send_str(text)  # the player's «📂 Загрузить сцену…»
        try:
            while True:
                m = await asyncio.wait_for(ws.receive(), 10)
                if m.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    print("the socket after the load:", m.type.name, "code", ws.close_code, m.extra)
                    break
                if m.type == aiohttp.WSMsgType.BINARY and b'"header"' in m.data[:400] and b'"world":2' in m.data[:4000]:
                    print("a new world started")
                    break
        except asyncio.TimeoutError:
            print("nothing within 10 s")
        await s.post(f"{base}/api/runs/{rid}/stop", json={})

asyncio.run(main())
