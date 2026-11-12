# Review B1, script 07: PUT /api/settings and POST /api/settings/calibrate, in-process (aiohttp TestClient), with
# lfviz.devices.SETTINGS_FILE patched to a temporary file: the owner's settings file and the shared server are never
# touched. Part 1 uses the real engine subprocess; part 2 replaces the subprocess by a stub with controlled delays to
# show what concurrent writes do (the real subprocess takes ~0.3-1 s, varying).
import asyncio
import json
import tempfile
from pathlib import Path

from aiohttp.test_utils import TestClient, TestServer

from lfviz import devices
from lfviz.app import create_app

TMP = Path(tempfile.mkdtemp())
devices.SETTINGS_FILE = TMP / "settings.local.json"
AS = "optics.angular_spectrum"


async def part1(cl):
    cases = [
        ("not JSON", "{oops", None),
        ("a list", None, []),
        ("kernels is a list", None, {"kernels": []}),
        ("kernel value is a string", None, {"kernels": {AS: "gpu"}}),
        ("precision is a list", None, {"kernels": {AS: {"device": "cpu", "precision": ["fp32"]}}}),
        ("crossover true", None, {"crossover": {AS: True}}),
        ("crossover -5 / 'big'", None, {"crossover": {AS: -5, "gravity.geodesics": "big"}}),
        ("150 kB of unknown kernel names", None, {"kernels": {f"k{i:06d}" + "x" * 40: {"device": "cpu"} for i in range(3000)}}),
    ]
    for label, raw, body in cases:
        devices.SETTINGS_FILE.write_text(json.dumps({"kernels": {AS: {"device": "cpu", "precision": "fp64"}}}))
        if raw is not None:
            r = await cl.put("/api/settings", data=raw, headers={"Content-Type": "application/json"})
        else:
            r = await cl.put("/api/settings", json=body)
        txt = (await r.text())[:150].replace("\n", " ")
        saved = json.loads(devices.SETTINGS_FILE.read_text())
        print(f"  {label:32s}: HTTP {r.status}; {txt}\n  {'':32s}  file now: kernels={saved.get('kernels')}, "
              f"crossover={saved.get('crossover')}", flush=True)


async def part2(cl):
    real = devices._backend
    delays = []

    async def stub(*args, timeout=60.0):
        if "--configure" in args:
            await asyncio.sleep(delays.pop(0))
            s = json.loads(args[args.index("--configure") + 1])
            return {"notes": [], "settings": {"kernels": s["kernels"], "crossover": s["crossover"]}}
        if "--calibrate" in args:
            await asyncio.sleep(0.3)
            return {"calibration": {AS: {"rows": [], "crossover": 4096, "measured": "now", "gpu": "stub"}}}
        return await real(*args, timeout=timeout)

    devices._backend = stub
    try:
        print("  (a) two quick changes from the settings page: PUT gpu (engine answers in 0.6 s), then PUT cpu (0.1 s)")
        devices.SETTINGS_FILE.write_text("{}")
        delays[:] = [0.6, 0.1]
        t1 = asyncio.create_task(cl.put("/api/settings", json={"kernels": {AS: {"device": "gpu"}}}))
        await asyncio.sleep(0.05)
        t2 = asyncio.create_task(cl.put("/api/settings", json={"kernels": {AS: {"device": "cpu"}}}))
        await asyncio.gather(t1, t2)
        print("      last choice sent: cpu; file now:", json.loads(devices.SETTINGS_FILE.read_text())["kernels"])
        print("  (b) 'Measure again' while a change is being validated (PUT 0.6 s, calibration 0.3 s)")
        devices.SETTINGS_FILE.write_text("{}")
        delays[:] = [0.6]
        t1 = asyncio.create_task(cl.put("/api/settings", json={"kernels": {AS: {"device": "auto"}}}))
        await asyncio.sleep(0.05)
        t2 = asyncio.create_task(cl.post("/api/settings/calibrate", json={}))
        r2 = await t2
        print("      calibrate answered", r2.status, "with crossover", (await r2.json()).get("crossover"))
        await t1
        s = json.loads(devices.SETTINGS_FILE.read_text())
        print("      file now: crossover =", s.get("crossover"), "| calibration kept:", "calibration" in s)
    finally:
        devices._backend = real


async def main():
    app = create_app(TMP / "runs", max_workers=1, idle_pause=60, idle_stop=3600)
    async with TestClient(TestServer(app)) as cl:
        print("Part 1: validation of PUT /api/settings (real engine subprocess)")
        await part1(cl)
        print("\nPart 2: concurrent writes (stubbed engine with controlled delays)")
        await part2(cl)


asyncio.run(main())
