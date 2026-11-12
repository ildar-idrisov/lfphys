# Review B6-framework, script s06: POST /api/runs/{id}/record — what it does with bodies a client may send.
# Real server (aiohttp test client) and a real worker on the toy section.
# Usage: see s01 (with LFVIZ_EXTRA); python3 /out/s06_record_api.py
import asyncio
import tempfile
from pathlib import Path

from aiohttp.test_utils import TestClient, TestServer

from lfviz.app import MGR, create_app


async def main():
    with tempfile.TemporaryDirectory() as td:
        app = create_app(Path(td), max_workers=2, idle_pause=600, idle_suspend=3600)
        async with TestClient(TestServer(app)) as cl:
            mgr = app[MGR]
            rid = (await (await cl.post("/api/runs", json={"viz": "p99_toy", "preset": "two"})).json())["id"]

            async def rec(body, raw=None):
                r = await cl.post(f"/api/runs/{rid}/record", **({"data": raw, "headers": {"Content-Type":
                                                                                          "application/json"}}
                                                                 if raw is not None else {"json": body}))
                txt = await r.text()
                return r.status, txt[:120], mgr.get(rid).meta["buffer"].get("recording")

            print("on: true                ->", await rec({"on": True}))
            print("only window_s: 300      ->", await rec({"window_s": 300}), " (recording switched off)")
            print("on: 'false' (a string)  ->", await rec({"on": "false"}), " (recording switched on)")
            print("a JSON list             ->", await rec(None, raw="[1, 2]"))
            print("window_s: [60]          ->", await rec({"on": True, "window_s": [60]}))
            print("window_s: 'NaN'         ->", await rec({"on": True, "window_s": "NaN"}))
            print("window_mb: 1e9          ->", await rec({"on": True, "window_mb": 1e9}))
            await cl.post(f"/api/runs/{rid}/stop", json={})


asyncio.run(main())
