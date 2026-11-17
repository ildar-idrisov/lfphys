# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""``registry.code_hash``: what a run executes, and nothing else (the key of the site's recordings and of a run's
checkpoints). The server's own modules (``registry.SERVER_ONLY``: ``app.py``, ``runs.py``, ``atlas_live.py``: the HTTP
routes, the runs' bookkeeping and the live points' endpoint, which no worker imports; review R-F F11) are left out, so an
edit there re-records nothing; an edit of the framework a run executes (``sim.py``), of the engine, or of the world's
own files (``viz.py``, ``web/view.js``) changes it.

The checks run on a small copy of the tree in a temporary folder (``registry.ROOT``, ``SERVER``, ``ENGINE`` patched), so
nothing of the real tree is touched. ``code_hash_current`` (the catalogue's ``code_hash``, the live points' key) is cached
by the files' sizes and times: an edit, a new file or a removed one is seen at the next call (review R-F F1).
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
        viz / "server" / "lfviz" / "atlas_live.py": "LIVE = 1\n",
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


def test_the_server_only_modules_are_app_runs_and_the_live_points():
    assert registry.SERVER_ONLY == {"app.py", "runs.py", "atlas_live.py"}


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


def test_the_current_hash_sees_an_edit_a_new_file_and_a_removed_one(tree, monkeypatch):
    monkeypatch.setattr(registry, "_CODE_HASHES", {})
    first = registry.code_hash_current(WORLD)
    assert first == registry.code_hash(WORLD) and registry.code_hash_cached is registry.code_hash_current
    calls = []
    real = registry.code_hash
    monkeypatch.setattr(registry, "code_hash", lambda v: calls.append(v) or real(v))
    assert registry.code_hash_current(WORLD) == first and calls == []  # nothing changed: not read again
    _edit(tree["viz"] / "server" / "lfviz" / "sim.py")
    second = registry.code_hash_current(WORLD)
    assert second != first and second == real(WORLD)  # review R-F F1: the code on disk, not the process's first view
    extra = tree["viz"] / "server" / "lfviz" / "new.py"
    extra.write_text("NEW = 1\n", encoding="utf-8")
    third = registry.code_hash_current(WORLD)
    assert third not in (first, second)
    extra.unlink()
    assert registry.code_hash_current(WORLD) == second


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
    assert [a["picture"] for a in body["audiences"]] == [a.get("picture") for a in registry.AUDIENCES]  # start-page F10
    assert [s["id"] for s in body["sections"]] == [s["id"] for s in registry.SECTIONS]
    assert body["sections"][0]["label"] == {"$t": "Mechanics"}


# --- the recorder's part of a recording's key (review P17-site F3) ---------------------------------------------------

def _sitelib():
    import importlib.util
    import sys

    if "lfsite_sitelib" in sys.modules:
        return sys.modules["lfsite_sitelib"]
    spec = importlib.util.spec_from_file_location("lfsite_sitelib", registry.ROOT / "site" / "sitelib.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_the_key_covers_the_recorder_its_budgets_and_the_images_dependencies(tmp_path, monkeypatch):
    """A recording's key changes with the recorder's code, the image's locked dependencies and Dockerfile, and the
    budgets that decide the thinning, not only with the world's code (F3): a change of any of them makes every
    recording stale, so the CI cache never serves a recording made by another recorder or other libraries."""
    L = _sitelib()
    names = [f.name for f in L.RECORDER_FILES]
    # the recorder, the atlas maker and the shared headless runner they both use (explore design §1.4)
    assert names == ["record.py", "atlas.py", "headless.py", "requirements.lock", "Dockerfile"] \
        and all(f.is_file() for f in L.RECORDER_FILES)
    copies = []
    for f in L.RECORDER_FILES:
        c = tmp_path / f.name
        c.write_bytes(f.read_bytes())
        copies.append(c)
    base = L.recorder_hash(copies)
    assert base == L.recorder_hash()  # the same bytes: the same hash
    spec = {"id": "a", "preset": "p", "seconds": 1, "fps": 10}
    key = L.spec_key(spec, "code")
    for c in copies:
        old = c.read_bytes()
        c.write_bytes(old + b"\n# an edit\n")
        assert L.recorder_hash(copies) != base, c.name
        c.write_bytes(old)
    assert L.recorder_hash(copies) == base
    monkeypatch.setitem(L.BUDGET, "file", (L.BUDGET["file"][0] + 1, L.BUDGET["file"][1]))
    assert L.recorder_hash() != base and L.spec_key(spec, "code") != key
    monkeypatch.undo()
    monkeypatch.setattr(L, "MIN_KEPT_FPS", L.MIN_KEPT_FPS + 1)
    assert L.spec_key(spec, "code") != key
    monkeypatch.undo()
    monkeypatch.setattr(L, "RECORDER_VERSION", "x")
    assert L.spec_key(spec, "code") != key
