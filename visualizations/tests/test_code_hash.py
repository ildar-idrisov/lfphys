# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""``registry.code_hash``: what a run executes, and nothing else (the key of the site's recordings and of a run's
checkpoints). The server's own modules (``registry.SERVER_ONLY``: ``app.py``, ``runs.py``: the HTTP routes and the runs'
bookkeeping, which no worker imports) are left out, so an edit there re-records nothing; an edit of the framework a run
executes (``sim.py``), of the engine, or of the world's own files (``viz.py``, ``web/view.js``) changes it.

The checks run on a small copy of the tree in a temporary folder (``registry.ROOT``, ``SERVER``, ``ENGINE`` patched), so
nothing of the real tree is touched. ``code_hash_cached`` (the catalogue's ``code_hash``) is computed once per process.
"""

from __future__ import annotations

import pytest

from lfviz import registry

WORLD = "u97_hash_toy"


@pytest.fixture
def tree(tmp_path, monkeypatch):
    """A minimal tree: ``visualizations/server/lfviz`` (app.py, runs.py, sim.py), the engine ``lfphys/lfphys`` and one
    world folder, with the registry pointed at it."""
    viz = tmp_path / "visualizations"
    files = {
        viz / "server" / "lfviz" / "app.py": "ROUTES = 1\n",
        viz / "server" / "lfviz" / "runs.py": "KEEP = 1\n",
        viz / "server" / "lfviz" / "sim.py": "STEP = 1\n",
        viz / "server" / "lfviz" / "tests" / "test_x.py": "X = 1\n",
        tmp_path / "lfphys" / "lfphys" / "core.py": "G = 1\n",
        viz / WORLD / "viz.py": "VIZ = {}\n",
        viz / WORLD / "web" / "view.js": "export const v = 1;\n",
    }
    for f, text in files.items():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
    monkeypatch.setattr(registry, "ROOT", viz)
    monkeypatch.setattr(registry, "SERVER", viz / "server")
    monkeypatch.setattr(registry, "ENGINE", tmp_path / "lfphys")
    monkeypatch.setenv("LFVIZ_EXTRA", "")
    return {"viz": viz, "engine": tmp_path / "lfphys" / "lfphys"}


def _edit(path):
    path.write_text(path.read_text(encoding="utf-8") + "# an edit\n", encoding="utf-8")


def test_the_server_only_modules_are_app_and_runs():
    assert registry.SERVER_ONLY == {"app.py", "runs.py"}


@pytest.mark.parametrize("name", sorted(registry.SERVER_ONLY))
def test_an_edit_of_a_server_only_module_keeps_the_code_hash(tree, name):
    before = registry.code_hash(WORLD)
    _edit(tree["viz"] / "server" / "lfviz" / name)
    assert registry.code_hash(WORLD) == before


@pytest.mark.parametrize("rel", ["server/lfviz/sim.py", f"{WORLD}/viz.py", f"{WORLD}/web/view.js"])
def test_an_edit_of_what_a_run_executes_changes_the_code_hash(tree, rel):
    before = registry.code_hash(WORLD)
    _edit(tree["viz"] / rel)
    assert registry.code_hash(WORLD) != before


def test_an_edit_of_the_engine_changes_the_code_hash(tree):
    before = registry.code_hash(WORLD)
    _edit(tree["engine"] / "core.py")
    assert registry.code_hash(WORLD) != before


def test_the_framework_tests_are_not_hashed(tree):
    before = registry.code_hash(WORLD)
    _edit(tree["viz"] / "server" / "lfviz" / "tests" / "test_x.py")
    assert registry.code_hash(WORLD) == before


def test_the_catalogue_hash_is_computed_once_per_process(tree, monkeypatch):
    monkeypatch.setattr(registry, "_CODE_HASHES", {})
    first = registry.code_hash_cached(WORLD)
    assert first == registry.code_hash(WORLD)
    _edit(tree["viz"] / "server" / "lfviz" / "sim.py")
    assert registry.code_hash_cached(WORLD) == first  # cached: the running server's code
    assert registry.code_hash(WORLD) != first


# --- the catalogue: the code a recording is compared with, and the audiences' API ---------------------------------------
def test_the_catalogue_entry_carries_the_code_hash():
    vid = registry.viz_ids()[0]
    assert registry.describe(vid)["code_hash"] == registry.code_hash(vid)


def test_the_audiences_api_is_the_registrys(tmp_path):
    import asyncio
    import json

    from aiohttp.test_utils import TestClient, TestServer

    from lfviz.app import audiences_list, create_app

    async def go():
        app = create_app(tmp_path, max_workers=1, idle_pause=60, idle_suspend=3600)
        async with TestClient(TestServer(app)) as cl:
            r = await cl.get("/api/audiences")
            assert r.status == 200
            return await r.json()

    body = asyncio.run(go())
    assert body == json.loads(json.dumps(audiences_list(), ensure_ascii=False))
    assert [a["id"] for a in body["audiences"]] == [a["id"] for a in registry.AUDIENCES]
    assert [a["prefix"] for a in body["audiences"]] == ["s", "u", "r", "p"]
    assert all(a["label"]["$t"] and a["description"]["$t"] and a["ui"] for a in body["audiences"])
    assert [s["id"] for s in body["sections"]] == [s["id"] for s in registry.SECTIONS]
    assert body["sections"][0]["label"] == {"$t": "Mechanics"}
