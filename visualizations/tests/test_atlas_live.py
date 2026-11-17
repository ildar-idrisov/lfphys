# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""«Compute live»: ``POST /api/atlas/<world>/<atlas>/point`` (``lfviz.atlas_live``; design
``lfphys/sources/explore_2026-11-14_design.md`` §3.7, §8), on the toy worlds of ``tests/site_worlds``:

* an off-grid value is computed in a separate process and is a whole point (its header a delta against the screen's
  base header that names it, ``$base``; the world's messages, ``end {reason: "atlas"}``); ``full_header`` gives the
  same point with the header merged; the headers name the point's key, code and time (integrator D13, review R-F F2);
* an on-grid value computed live is the same bytes a site build makes; with the local atlas current it is served
  from it; a second request is served from the cache; another seed is another point;
* the cache follows the code on disk: a point is never served or stored under another code's key (review R-F F1); a
  point computed while the code changed is not kept;
* a value the world refuses (``check_params`` or its constructor) is ``400 {error, hint}`` with its texts; a point whose
  checks end ✗ is ``409`` naming them (integrator D14, review R-F F4); a value the schema refuses or outside the
  control's span, a parameter that is not a control, a bad seed or body (an integer of 5000 digits too: review R-F F12)
  are ``400``; an unknown world or atlas ``404``;
* the memory limit and the time limit end the point's process, not the server (``503``), which then computes the next
  point; more than one computed and ``QUEUE`` waiting is ``429``;
* the cache's housekeeping: leftovers of killed processes go, the log keeps the last point, the cache keeps under its
  cap (review R-F F13);
* the nested route ``/recordings/<world>/atlas/<atlas>/<file>`` serves an atlas's files and nothing outside.
"""

from __future__ import annotations

import asyncio
import datetime as _dt
import gzip
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import time

import pytest
from aiohttp.test_utils import TestClient, TestServer

from lfviz import atlas_live, headless, protocol, registry
from lfviz.app import create_app

VIZ = registry.ROOT
SITE_WORLDS = VIZ / "tests" / "site_worlds"
URL = "/api/atlas/s98_atlas_toy/explore/point"


def _site(name):
    if f"lfsite_{name}" in sys.modules:
        return sys.modules[f"lfsite_{name}"]
    spec = importlib.util.spec_from_file_location(f"lfsite_{name}", VIZ / "site" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path):
    monkeypatch.setenv("LFVIZ_EXTRA", str(SITE_WORLDS))
    monkeypatch.setenv("LFVIZ_RECORDINGS", str(tmp_path / "no-recordings"))
    monkeypatch.setenv("LFVIZ_POINT_TIMEOUT_S", "20")


def _api(tmp_path, fn):
    async def go():
        app = create_app(tmp_path / "runs", max_workers=1, idle_pause=60, idle_suspend=3600, worker_mem_gb=2)
        async with TestClient(TestServer(app)) as cl:
            return await fn(cl)
    return asyncio.run(go())


async def _post(cl, body, url=URL):
    r = await cl.post(url, json=body)
    data = await r.read()
    return r.status, data, dict(r.headers)


def test_an_off_grid_point_is_computed_whole(tmp_path):
    async def fn(cl):
        return await _post(cl, {"values": {"h_m": 0.7, "angle_deg": 12.5}})
    st, data, hd = _api(tmp_path, fn)
    assert st == 200 and hd["Content-Type"] == "application/gzip" and hd["X-LF-Source"] == "computed"
    msgs = headless.read_stream(data)
    head = msgs[0][0]
    assert head["type"] == "header" and head["$delta"] is True and head["params"]["h_m"] == 0.7
    assert head["params"]["angle_deg"] == 12.5 and msgs[-1][0] == {**msgs[-1][0], "type": "end", "reason": "atlas"}
    assert any(m["type"] == "event" and m["kind"] == "landing" for m, _b in msgs)
    assert not any(m["type"] == "story" for m, _b in msgs)  # the screen's dropped type
    assert all("ghost" not in b for m, b in msgs if m["type"] == "frame")  # the screen's dropped frame blob
    cached = list((tmp_path / "runs" / "atlas-live" / "s98_atlas_toy" / "explore").glob("*.lfpt.gz"))
    assert len(cached) == 2 and any(f.name.startswith("base-") for f in cached)  # the point and the base header


def test_an_on_grid_point_is_the_bytes_of_a_build_then_the_atlas_and_the_cache(tmp_path, monkeypatch):
    atlas = _site("atlas")
    built = tmp_path / "built"
    entries, problems, _w = atlas.build_world("s98_atlas_toy", built, ["explore"])
    assert problems == []
    atlas.write_atlases(built, "s98_atlas_toy", entries)
    man = json.loads((built / "s98_atlas_toy" / entries[0]["file"]).read_text(encoding="utf-8"))
    p4 = man["points"][4]  # h 1, angle 30
    want = (built / "s98_atlas_toy" / "atlas" / "explore" / p4[0]).read_bytes()

    async def fn(cl):
        a = await _post(cl, {"values": {"h_m": 1.0, "angle_deg": 30.0}})
        b = await _post(cl, {"values": {"h_m": 1, "angle_deg": 30}})  # the same values, as the schema coerces them
        c = await _post(cl, {"values": {"h_m": 1.0, "angle_deg": 30.0}, "seed": 2})
        return a, b, c
    (st, data, hd), (st2, data2, hd2), (st3, _d3, hd3) = _api(tmp_path, fn)
    assert st == 200 and hd["X-LF-Source"] == "computed" and data == want
    assert st2 == 200 and hd2["X-LF-Source"] == "cache" and data2 == want and hd2["X-LF-Key"] == hd["X-LF-Key"]
    assert st3 == 200 and hd3["X-LF-Key"] != hd["X-LF-Key"]  # another seed: another point
    monkeypatch.setenv("LFVIZ_RECORDINGS", str(built))  # the local atlas, current: served from it

    async def fn2(cl):
        return await _post(cl, {"values": {"h_m": 1.0, "angle_deg": 30.0}})
    st, data, hd = _api(tmp_path / "other", fn2)
    assert st == 200 and hd["X-LF-Source"] == "atlas" and data == want


def test_refusals_are_400_with_their_texts(tmp_path):
    async def fn(cl):
        out = [await _post(cl, {"values": {"h_m": 0.0, "angle_deg": 0.0}}),
               await _post(cl, {"values": {"h_m": 99.0}}),
               await _post(cl, {"values": {"v0": 3.0}}),
               await _post(cl, {"values": {}, "seed": -1}),
               await _post(cl, {"nonsense": 1}),
               await _post(cl, {"values": {}}, "/api/atlas/s98_atlas_toy/nowhere/point"),
               await _post(cl, {"values": {}}, "/api/atlas/s00_nothing/explore/point")]
        r = await cl.post(URL, data="not json")
        out.append((r.status, await r.read(), {}))
        return out
    res = _api(tmp_path, fn)
    st, data, _h = res[0]
    body = json.loads(data)
    assert st == 400 and body["error"]["$t"] == "The ball starts on the ground moving along it or into it: no flight"
    assert body["hint"]["$t"] == "raise the height or the angle" and body["text"]
    assert [r[0] for r in res[1:]] == [400, 400, 400, 400, 404, 404, 400]
    assert "v0" in json.loads(res[2][1])["text"]


def test_the_memory_limit_and_the_timeout_end_the_process_not_the_server(tmp_path, monkeypatch):
    monkeypatch.setenv("LFVIZ_POINT_MEM_GB", "0.6")
    monkeypatch.setenv("LFVIZ_POINT_TIMEOUT_S", "3")
    url = "/api/atlas/u97_atlas_hog/explore/point"

    async def fn(cl):
        mem = await _post(cl, {"values": {"mode": "mem"}}, url)
        cpu = await _post(cl, {"values": {"mode": "cpu"}}, url)
        ok = await _post(cl, {"values": {"mode": "none", "h_m": 0.5}}, url)
        return mem, cpu, ok
    mem, cpu, ok = _api(tmp_path, fn)
    assert mem[0] == 503 and "memory" in json.loads(mem[1])["text"], mem
    assert cpu[0] == 503 and "longer than" in json.loads(cpu[1])["text"], cpu
    assert ok[0] == 200 and ok[2]["X-LF-Source"] == "computed"


def test_beyond_the_queue_a_request_is_429(tmp_path, monkeypatch):
    gate = {"n": 0}

    async def slow(self, world, atlas, values, seed, folder, want):
        gate["n"] += 1
        await asyncio.sleep(0.5)
        return b"x", {"key": f"k{seed}", "base_key": "b", "code_hash": "c", "stable": True}
    monkeypatch.setattr(atlas_live.LivePoints, "_spawn", slow)

    async def fn(cl):
        reqs = [_post(cl, {"values": {"h_m": 1.0}, "seed": 10 + k}) for k in range(atlas_live.QUEUE + 2)]
        return await asyncio.gather(*reqs)
    res = _api(tmp_path, fn)
    codes = sorted(r[0] for r in res)
    assert codes == [200] * (atlas_live.QUEUE + 1) + [429], codes
    assert gate["n"] == atlas_live.QUEUE + 1


def test_the_nested_route_serves_an_atlas_and_nothing_outside(tmp_path, monkeypatch):
    monkeypatch.setenv("LFVIZ_RECORDINGS", str(SITE_WORLDS / "recordings"))
    idx = json.loads((SITE_WORLDS / "recordings" / "s98_atlas_toy" / "index.json").read_text(encoding="utf-8"))
    man_rel = next(a for a in idx["atlases"] if a["id"] == "explore")["file"]
    man = json.loads((SITE_WORLDS / "recordings" / "s98_atlas_toy" / man_rel).read_text(encoding="utf-8"))

    async def fn(cl):
        out = []
        for rel in (man_rel, f"atlas/explore/{man['base']['file']}", "atlas/explore/../index.json", "a/b/c/d",
                    "atlas/explore/nothing.gz"):
            r = await cl.get(f"/recordings/s98_atlas_toy/{rel}")
            out.append((r.status, r.headers.get("Content-Type"), await r.read()))
        return out
    res = _api(tmp_path, fn)
    assert res[0][0] == 200 and json.loads(res[0][2])["atlas"] == "explore"
    assert res[1][0] == 200 and res[1][1] == "application/gzip" and gzip.decompress(res[1][2]).startswith(b"LFVREC1")
    assert [r[0] for r in res[2:]] == [404, 404, 404]


# --- integrator D13, D14; review R-F F1, F2, F4, F12, F13 -----------------------------------------------------------
def _stream_items(data):
    raw = gzip.decompress(data)
    return [m for _o, m in protocol.iter_stream(raw, len(protocol.MAGIC))]


def test_a_live_point_names_its_base_its_key_code_and_time_and_comes_whole_on_request(tmp_path):
    body = {"values": {"h_m": 0.7, "angle_deg": 12.5}}

    async def fn(cl):
        a = await _post(cl, body)
        b = await _post(cl, {**body, "full_header": True})
        c = await _post(cl, {**body, "full_header": "yes"})
        return a, b, c
    (st, data, hd), (st2, full, hd2), (st3, _d, _h) = _api(tmp_path, fn)
    assert st == 200 and st2 == 200 and st3 == 400
    assert hd["X-LF-Code"] == registry.code_hash("s98_atlas_toy") and hd2["X-LF-Source"] == "cache"
    assert hd2["X-LF-Key"] == hd["X-LF-Key"] and hd2["X-LF-Made"] == hd["X-LF-Made"]
    made = _dt.datetime.fromisoformat(hd["X-LF-Made"])
    assert made.tzinfo is not None and abs((_dt.datetime.now(_dt.timezone.utc) - made).total_seconds()) < 600
    folder = tmp_path / "runs" / "atlas-live" / "s98_atlas_toy" / "explore"
    base_f = next(folder.glob("base-*.lfpt.gz"))
    head = headless.read_stream(data)[0][0]
    assert head["$delta"] is True and head["$base"] == hashlib.sha256(base_f.read_bytes()).hexdigest()
    fhead = headless.read_stream(full)[0][0]
    assert not [k for k in fhead if k.startswith("$")]
    merged, _blobs = headless.merge_header(headless.read_stream(base_f.read_bytes())[0], headless.read_stream(data)[0])
    assert {k: v for k, v in fhead.items() if k != "blobs"} == {k: v for k, v in merged.items() if k != "blobs"}
    assert _stream_items(full)[1:] == _stream_items(data)[1:]  # only the header differs


def _toy_copy(tmp_path, monkeypatch):
    extra = tmp_path / "extra"
    shutil.copytree(SITE_WORLDS / "s98_atlas_toy", extra / "s98_atlas_toy",
                    ignore=shutil.ignore_patterns("__pycache__"))
    monkeypatch.setenv("LFVIZ_EXTRA", str(extra))
    return extra / "s98_atlas_toy" / "viz.py"


def test_the_cache_follows_the_code_on_disk(tmp_path, monkeypatch):
    """Review R-F F1: a world file edited while the server runs. The point is computed by the edited code under the
    edited code's key; after the edit is reverted, the first code's point is served again, never the edited one."""
    f = _toy_copy(tmp_path, monkeypatch)
    orig = f.read_text(encoding="utf-8")
    old = 'meta = {"x": x, "y": y, "landed": self.landed, "meas": meas}'
    assert orig.count(old) == 1
    body = {"values": {"h_m": 0.7, "angle_deg": 12.5}}

    def probed(data):
        return any(m.get("probe") for m, _b in headless.read_stream(data) if m["type"] == "frame")

    async def fn(cl):
        a = await _post(cl, body)
        time.sleep(0.01)
        f.write_text(orig.replace(old, old[:-1] + ', "probe": 1}'), encoding="utf-8")
        b = await _post(cl, body)
        time.sleep(0.01)
        f.write_text(orig, encoding="utf-8")
        c = await _post(cl, body)
        return a, b, c
    (st, da, ha), (st2, db, hb), (st3, dc, hc) = _api(tmp_path, fn)
    assert st == st2 == st3 == 200
    assert ha["X-LF-Source"] == "computed" and not probed(da)
    assert hb["X-LF-Source"] == "computed" and probed(db)  # not the first code's cached point
    assert hb["X-LF-Code"] != ha["X-LF-Code"] and hb["X-LF-Key"] != ha["X-LF-Key"]
    assert hc["X-LF-Source"] == "cache" and hc["X-LF-Key"] == ha["X-LF-Key"] and not probed(dc)  # not poisoned


def test_a_point_computed_while_the_code_changed_is_not_kept(tmp_path, monkeypatch):
    sigs = iter([("c1", "r", "l"), ("c2", "r", "l")])
    monkeypatch.setattr(atlas_live, "_code_signature", lambda world, L: next(sigs))
    folder = tmp_path / "cache"
    folder.mkdir()
    data, rep = atlas_live.compute("s98_atlas_toy", "explore", {"h_m": 0.7, "angle_deg": 12.5}, 1, folder)
    assert data[:2] == b"\x1f\x8b" and rep["stable"] is False and rep["code_hash"] == "c1"
    assert not list(folder.glob("base-*"))  # its base is not kept either


def test_refusals_of_the_constructor_failed_checks_spans_and_huge_numbers(tmp_path):
    url = "/api/atlas/u97_atlas_hog/explore/point"

    async def fn(cl):
        out = [await _post(cl, {"values": {"mode": "refuse"}}, url),
               await _post(cl, {"values": {"mode": "fail"}}, url),
               await _post(cl, {"values": {"h_m": 2.0}}),
               await _post(cl, {"values": {"mode": "mem"}}, "/api/atlas/u97_atlas_hog/faults/point")]
        r = await cl.post(URL, data='{"values": {"h_m": 1' + "1" * 5000 + "}}",
                          headers={"Content-Type": "application/json"})
        out.append((r.status, await r.read(), {}))
        return out
    ref, fail, span, sel, huge = _api(tmp_path, fn)
    body = json.loads(ref[1])
    assert ref[0] == 400 and body["error"]["$t"] == "This test world refuses the mode “refuse” while it is built"
    assert body["hint"]["$t"] == "choose another mode"  # D14: a constructor's refusal is a refusal, not a 500
    body = json.loads(fail[1])
    assert fail[0] == 409 and body["error"]["$t"] == "the world's checks fail at these values: {checks}"
    assert "a check that fails on purpose" in body["text"]
    body = json.loads(span[1])
    assert span[0] == 400 and body["error"]["$t"].startswith("“{label}” = {value:.6g} is outside")
    assert sel[0] == 400 and json.loads(sel[1])["error"]["$t"] == "“{label}”: this screen offers only its own values"
    assert huge[0] == 400 and json.loads(huge[1])["error"]["$t"] == "the request body is not JSON"


def test_the_cache_housekeeping(tmp_path, monkeypatch):
    folder = tmp_path / "runs" / "atlas-live" / "s98_atlas_toy" / "explore"
    folder.mkdir(parents=True)
    old_t = time.time() - 2 * atlas_live.LEFTOVER_S
    for name in ("dead.part", "dead.part.json", "base-x.lfpt.gz.tmp"):
        (folder / name).write_bytes(b"x")
        os.utime(folder / name, (old_t, old_t))
    (folder / "fresh.part").write_bytes(b"x")
    monkeypatch.setenv(atlas_live.ENV_CACHE, "0.001")  # 1000 bytes: only the newest point is kept

    async def fn(cl):
        a = await _post(cl, {"values": {"h_m": 0.7, "angle_deg": 12.5}})
        b = await _post(cl, {"values": {"h_m": 0.8, "angle_deg": 12.5}})
        return a, b
    a, b = _api(tmp_path, fn)
    assert a[0] == b[0] == 200
    names = {f.name for f in folder.iterdir()}
    assert not names & {"dead.part", "dead.part.json", "base-x.lfpt.gz.tmp"} and "fresh.part" in names
    assert f"{b[2]['X-LF-Key']}.lfpt.gz" in names and f"{a[2]['X-LF-Key']}.lfpt.gz" not in names
    log = (folder / "point.log").read_bytes()
    assert len(log) < 20000  # the last point's log only
