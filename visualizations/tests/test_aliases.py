# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The old ids of the renamed worlds (2026-11-13: «Префиксы s/u/r/p», «Номер = id в плане»; DESIGN of the start page
§3.2): ``registry.ALIASES`` maps ``v01_light_travel`` … to ``u31_light_travel`` …. The registry, the server's routes
and the run records accept an old id.

The fixture ``tests/fixtures/old_records/20261113-113234-v04-8069`` is a run of ``v04_orbits`` (preset ``default``,
seed 1, played about 4 s, then suspended with a checkpoint) made on 2026-11-13 by the code of commit f3d137d, before the
rename, in a container with a temporary runs folder. Its checkpoint names the old folder's files, so it is stale: the
run resumes by replaying its record (``Runner.restore``; ``RULES.md`` §3)."""

from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path

import pytest
from aiohttp.test_utils import TestClient, TestServer

from lfviz import protocol, registry
from lfviz.app import MGR, create_app
from lfviz.i18n import english

OLD_RUN = "20261113-113234-v04-8069"
FIXTURE = Path(__file__).parent / "fixtures" / "old_records" / OLD_RUN


def test_every_alias_resolves_to_an_existing_folder_and_none_is_a_folder():
    ids = set(registry.viz_ids())
    assert len(registry.ALIASES) == 17 and len(set(registry.ALIASES.values())) == 17
    for old, new in registry.ALIASES.items():
        assert new in ids, (old, new)
        assert old not in ids and not (registry.ROOT / old).exists(), old  # no alias is a folder
        assert registry.resolve(old) == new and registry.resolve(new) == new
        assert registry.folder(old) == registry.folder(new) == registry.ROOT / new
        assert old[:3] != new[:3] and old[3:] == new[3:], (old, new)  # only the prefix and number changed
    with pytest.raises(KeyError):
        registry.folder("v99_nothing")


def test_load_and_describe_accept_an_old_id_and_list_the_aliases():
    viz = registry.load("v02_double_slit")
    assert viz["id"] == "u32_double_slit" and viz is not None
    d = registry.describe("v11_double_slit_2d")
    assert d["id"] == "r12_double_slit_2d" and d["aliases"] == ["v11_double_slit_2d"]
    assert registry.describe(registry.load("u31_light_travel"))["aliases"] == ["v01_light_travel"]
    assert registry.describe(registry.load("p01_gravity"))["aliases"] == []


async def _old_urls(tmp_path):
    app = create_app(tmp_path, max_workers=1, idle_pause=60, idle_suspend=3600)
    async with TestClient(TestServer(app)) as cl:
        for old, new in registry.ALIASES.items():
            r = await cl.get(f"/viz/{old}/view.js", allow_redirects=False)
            assert r.status == 301 and r.headers["Location"] == f"/viz/{new}/view.js", (old, r.status)
            r = await cl.get(f"/viz/{old}/view.js")  # followed: the new module
            assert r.status == 200 and str(r.url).endswith(f"/viz/{new}/view.js")
        r = await cl.get("/viz/v11_double_slit_2d/view.js?x=1", allow_redirects=False)
        assert r.headers["Location"] == "/viz/r12_double_slit_2d/view.js?x=1"
        r = await cl.get("/api/viz/v04_orbits")
        assert r.status == 200
        body = await r.json()
        assert body["id"] == "u34_orbits" and body["aliases"] == ["v04_orbits"]
        assert (await cl.get("/api/viz/v99_nothing")).status == 404
        # a run started by an old id is a run of the renamed world
        r = await cl.post("/api/runs", json={"viz": "v06_qcd", "preset": "standard", "seed": 1})
        assert r.status == 200, await r.text()
        rid = (await r.json())["id"]
        meta = await (await cl.get(f"/api/runs/{rid}")).json()
        assert meta["viz"] == "u36_qcd" and "-u36-" in rid
        await cl.post(f"/api/runs/{rid}/stop", json={})


def test_the_old_urls_answer_301_or_200(tmp_path):
    asyncio.run(_old_urls(tmp_path))


async def _wait(cl, rid, cond, n=600):
    meta = None
    for _ in range(n):
        meta = await (await cl.get(f"/api/runs/{rid}")).json()
        if cond(meta):
            return meta
        await asyncio.sleep(0.1)
    raise AssertionError(meta)


def _texts(path: Path) -> list[str]:
    data = path.read_bytes()
    return [english(m.get("text") or "") for _, msg in protocol.iter_stream(data, len(protocol.MAGIC))
            for m in [protocol.peek_meta(msg)] if m.get("type") == "notice"]


async def _old_record(tmp_path):
    runs = tmp_path / "runs"
    shutil.copytree(FIXTURE, runs / OLD_RUN)
    # the fixture's last action is of 2026-11-13: a removal period of a year keeps it (the default 3 days removed it at
    # load from 2026-11-17 on)
    app = create_app(runs, max_workers=1, idle_pause=60, idle_suspend=3600, keep_days=365)
    async with TestClient(TestServer(app)) as cl:
        mgr = app[MGR]
        listed = {r["id"]: r for r in await (await cl.get("/api/runs")).json()}
        assert listed[OLD_RUN]["viz"] == "u34_orbits"
        meta = await (await cl.get(f"/api/runs/{OLD_RUN}")).json()
        assert meta["viz"] == "u34_orbits" and meta["viz_alias"] == "v04_orbits" and meta["state"] == "suspended"
        run = mgr.get(OLD_RUN)
        n0 = len(run.entries)
        assert n0 > 10
        # it opens and plays: the record streams, the player's passport names the new world and its view loads
        r = await cl.get(f"/api/runs/{OLD_RUN}/stream")
        assert r.status == 200 and (await r.read()).startswith(protocol.MAGIC)
        assert (await cl.get(f"/viz/{meta['viz']}/view.js")).status == 200
        # it resumes: the checkpoint names v04_orbits's files, so the world is rebuilt from its record
        t0 = meta["sim_t"]
        assert (await cl.post(f"/api/runs/{OLD_RUN}/command", json={"cmd": "play"})).status == 200
        meta = await _wait(cl, OLD_RUN, lambda m: m["state"] == "running" and m.get("sim_t", 0) > t0
                           and (m.get("resumes") or [{}])[-1].get("from") == "replay")
        texts = _texts(run.stream_path)
        assert any(x.startswith("Resuming: the world is recomputed from its start") for x in texts), texts
        assert not any("Resuming from the world's saved state" in x for x in texts)
        await _wait(cl, OLD_RUN, lambda m: any("World restored" in x for x in _texts(run.stream_path)))
        assert len(run.entries) > n0
        await cl.post(f"/api/runs/{OLD_RUN}/stop", json={})
        saved = json.loads((runs / OLD_RUN / "meta.json").read_text())
        assert saved["viz"] == "u34_orbits" and saved["viz_alias"] == "v04_orbits"


def test_an_old_record_opens_plays_and_resumes_by_replay(tmp_path):
    asyncio.run(_old_record(tmp_path))
