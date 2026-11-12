"""c05: what a series request costs the server's event loop (it serves every viewer and every run).

A p97_osc run plays for PLAY_S seconds with a viewer connected (a WebSocket: otherwise the run is paused after 60 s
without viewers), giving ~20 frames per second. Then:
(a) the request validation: 100 copies of one id (`ids=E,E,...`) are accepted (MAX_IDS counts copies);
(b) the JSON series of 100 ids x all frames, max_points = 50000, while a second task asks /api/health every 20 ms:
    the response size and time, and the longest /api/health latency during it (the event loop blocked);
(c) the same for 1 id (the baseline), and the CSV of 100 ids.
Extrapolation to the cap (50 000 frames) is linear in rows x ids.
"""
import asyncio
import json
import os
import sys
import time

import aiohttp

sys.path.insert(0, "/out")
from lbrf_client import BASE, start  # noqa: E402

PLAY_S = float(os.environ.get("PLAY_S", "200"))


async def main():
    rid = start("p97_osc", "two", seed=5)
    out = {"run": rid}
    async with aiohttp.ClientSession() as s:
        ws = await s.ws_connect(BASE.replace("http", "ws") + f"/ws/runs/{rid}", max_msg_size=0)
        await ws.send_str(json.dumps({"cmd": "play", "args": {}}))

        async def drain():
            async for _ in ws:
                pass
        dr = asyncio.create_task(drain())
        await asyncio.sleep(PLAY_S)
        await ws.send_str(json.dumps({"cmd": "pause", "args": {}}))
        await asyncio.sleep(1.0)

        async def health_probe(stop, lat):
            while not stop.is_set():
                t0 = time.monotonic()
                async with s.get(BASE + "/api/health") as r:
                    await r.read()
                lat.append(time.monotonic() - t0)
                await asyncio.sleep(0.02)

        async def timed(url):
            stop, lat = asyncio.Event(), []
            pr = asyncio.create_task(health_probe(stop, lat))
            await asyncio.sleep(0.3)
            base_lat = max(lat) if lat else None
            t0 = time.monotonic()
            async with s.get(url) as r:
                body = await r.read()
                st = r.status
            dt = time.monotonic() - t0
            stop.set()
            await pr
            return {"status": st, "bytes": len(body), "seconds": round(dt, 3),
                    "health_max_latency_s": round(max(lat), 3), "health_latency_before_s": base_lat,
                    "n": (json.loads(body).get("n") if body[:1] == b"{" else None)}

        one = await timed(BASE + f"/api/runs/{rid}/series?ids=E&max_points=50000")
        print("(c) 1 id:", one)
        many = await timed(BASE + f"/api/runs/{rid}/series?ids={','.join(['E'] * 100)}&max_points=50000")
        print("(a, b) 100 copies of one id:", many)
        csv = await timed(BASE + f"/api/runs/{rid}/series?ids={','.join(['E'] * 100)}&format=csv")
        print("(c) CSV of 100 ids:", csv)
        out.update(one_id=one, hundred_ids=many, csv_hundred=csv)
        await ws.close()
        dr.cancel()
    json.dump(out, open("/out/c05_series_load.json", "w"), indent=1)


asyncio.run(main())
