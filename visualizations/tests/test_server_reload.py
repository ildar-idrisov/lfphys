# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The code the server process holds (2026-11-18: the owner's server, started before S03 existed, showed «Not loaded:
s03_projectile — … AttributeError: module 'lfphys.core.data' has no attribute 'P_ATM'»: the world's new ``viz.py`` was
imported against the engine the process had imported at its start).

* A world's own files edited, the engine and the framework unchanged: ``RunManager.viz`` drops the world's package
  from ``sys.modules`` and imports it anew, so the catalogue follows without a restart; so does a world that imports an
  edited world (r13 imports r12).
* Nothing changed: the world is not imported again.
* The engine or the framework edited on disk after the start: ``/api/health`` says ``restart_needed`` and names the
  files, and a world that fails to load gets the translated advice to restart the server, with the exception's line as
  its detail (``/api/viz``, ``/api/viz/<id>``).

The checks run on a small tree in a temporary folder (``registry.ROOT``, ``SERVER``, ``ENGINE`` patched, as in
``test_code_hash.py``), with ``registry.check`` stubbed so that a two-line ``VIZ`` loads; the toy worlds' modules are
removed from ``sys.modules`` afterwards.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import pytest

from lfviz import i18n, registry, runs
from lfviz.app import MGR
from lfviz.runs import RESTART_TEXT, RunManager

WORLD, DEP = "u96_reload_toy", "u95_reload_dep"
REAL = Path(__file__).resolve().parents[1]  # the real visualizations/ (its catalogues)


def _write(path, text):
    """Write a file and move its time on, so that the edit is seen whatever the file system's time resolution."""
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.stat().st_mtime_ns if path.exists() else 0
    path.write_text(text, encoding="utf-8")
    st = path.stat()
    if st.st_mtime_ns <= old:
        os.utime(path, ns=(st.st_atime_ns, old + 2_000_000_000))


def _world(title_expr: str, head: str = "") -> str:
    return f"{head}VIZ = {{'id': {WORLD!r}, 'title': {title_expr}}}\n"


@pytest.fixture
def tree(tmp_path, monkeypatch):
    """The engine ``lfphys/lfphys``, the framework ``visualizations/server/lfviz`` and two toy worlds, the first
    importing the second; the registry pointed at them; ``sys.path`` and the toy modules restored afterwards."""
    viz = tmp_path / "visualizations"
    files = {
        viz / "server" / "lfviz" / "sim.py": "STEP = 1\n",
        viz / "server" / "lfviz" / "app.py": "ROUTES = 1\n",
        viz / "server" / "serve.py": "MAIN = 1\n",
        tmp_path / "lfphys" / "lfphys" / "core.py": "G = 1\n",
        viz / DEP / "__init__.py": "",
        viz / DEP / "viz.py": f"VIZ = {{'id': {DEP!r}, 'title': 'dependency'}}\n",
        viz / DEP / "data.py": "NAME = 'first'\n",
        viz / WORLD / "__init__.py": "",
        viz / WORLD / "viz.py": _world("'one'"),
        viz / WORLD / "web" / "view.js": "export const v = 1;\n",
    }
    for f, text in files.items():
        _write(f, text)
    monkeypatch.setattr(registry, "ROOT", viz)
    monkeypatch.setattr(registry, "SERVER", viz / "server")
    monkeypatch.setattr(registry, "ENGINE", tmp_path / "lfphys")
    monkeypatch.setattr(registry, "check", lambda v: [])  # a two-line VIZ is enough here
    monkeypatch.setattr(registry, "_CODE_HASHES", {})
    monkeypatch.setenv("LFVIZ_EXTRA", "")
    monkeypatch.setattr(sys, "path", list(sys.path))  # registry.ensure_path adds the temporary folders
    monkeypatch.setattr(runs, "_PKG_SIG", {})
    yield {"viz": viz, "engine": tmp_path / "lfphys" / "lfphys", "runs": tmp_path / "runs"}
    for name in [n for n in sys.modules if n.split(".")[0] in (WORLD, DEP)]:
        del sys.modules[name]


def test_an_edit_of_a_world_is_imported_anew_without_a_restart(tree):
    mgr = RunManager(tree["runs"])
    assert mgr.viz(WORLD)["title"] == "one"
    first = sys.modules[f"{WORLD}.viz"]
    _write(tree["viz"] / WORLD / "viz.py", _world("'three'"))
    assert mgr.viz(WORLD)["title"] == "three"
    assert sys.modules[f"{WORLD}.viz"] is not first
    assert mgr.code_changed() == []  # a world's own edit needs no restart
    _write(tree["viz"] / WORLD / "helper.py", "X = 1\n")  # a new file of the world: imported anew too
    _write(tree["viz"] / WORLD / "viz.py", _world("H.X", "from . import helper as H\n"))
    assert mgr.viz(WORLD)["title"] == 1


def test_a_world_that_imports_an_edited_world_is_imported_anew(tree):
    """r13 imports r12's modules: an edit of r12 makes r13's entry stale too."""
    _write(tree["viz"] / WORLD / "viz.py", _world("D.NAME", f"from {DEP} import data as D\n"))
    mgr = RunManager(tree["runs"])
    assert mgr.viz(WORLD)["title"] == "first"
    _write(tree["viz"] / DEP / "data.py", "NAME = 'second'\n")
    assert mgr.viz(WORLD)["title"] == "second"
    assert mgr.viz(DEP)["title"] == "dependency"
    assert sys.modules[f"{DEP}.data"].NAME == "second"


def test_a_dependency_imported_before_its_edit_is_imported_anew(tree):
    """The dependency loaded first (its own entry), then edited, then the dependent world asked for the first time:
    it is not built on the dependency's old modules."""
    _write(tree["viz"] / WORLD / "viz.py", _world("D.NAME", f"from {DEP} import data as D\n"))
    mgr = RunManager(tree["runs"])
    assert mgr.viz(DEP)["title"] == "dependency"
    import importlib
    assert importlib.import_module(f"{DEP}.data").NAME == "first"
    _write(tree["viz"] / DEP / "data.py", "NAME = 'second'\n")
    assert mgr.viz(WORLD)["title"] == "second"


def test_a_world_that_failed_is_tried_again_and_loads_once_mended(tree):
    _write(tree["viz"] / WORLD / "viz.py", "raise RuntimeError('broken on purpose')\n")
    mgr = RunManager(tree["runs"])
    with pytest.raises(RuntimeError, match="broken on purpose"):
        mgr.viz(WORLD)
    assert WORLD not in sys.modules  # nothing half imported is kept
    _write(tree["viz"] / WORLD / "viz.py", _world("'mended'"))
    assert mgr.viz(WORLD)["title"] == "mended"


def test_nothing_changed_nothing_is_imported_again(tree, monkeypatch):
    mgr = RunManager(tree["runs"])
    calls = []
    real = registry.load
    monkeypatch.setattr(registry, "load", lambda v: calls.append(v) or real(v))
    one = mgr.viz(WORLD)
    mod = sys.modules[f"{WORLD}.viz"]
    for _ in range(3):
        assert mgr.viz(WORLD) is one
    assert calls == [WORLD] and sys.modules[f"{WORLD}.viz"] is mod
    _write(tree["viz"] / WORLD / "web" / "view.js", "export const v = 2;\n")  # not Python: nothing to import
    assert mgr.viz(WORLD) is one and calls == [WORLD]
    assert mgr.code_changed() == []


def _api(tree, steps):
    """Run ``steps(client)`` against the app on the temporary tree."""
    from aiohttp.test_utils import TestClient, TestServer

    from lfviz.app import create_app

    async def go():
        app = create_app(tree["runs"], max_workers=1, idle_pause=60, idle_suspend=3600)
        async with TestClient(TestServer(app)) as cl:
            return await steps(cl)

    return asyncio.run(go())


@pytest.mark.parametrize("edited", ["lfphys/lfphys/core.py", "visualizations/server/lfviz/sim.py"])
def test_an_edit_of_the_engine_or_the_framework_asks_for_a_restart(tree, edited):
    root = tree["viz"].parent

    async def steps(cl):
        h = await (await cl.get("/api/health")).json()
        assert h["restart_needed"] is False and h["changed"] == []
        # the owner's case: the engine gains a constant and a world uses it; the server holds the old engine
        _write(root / edited, "G = 1\nP_ATM = 101325.0\n")
        _write(tree["viz"] / WORLD / "viz.py", _world("I.P_ATM", "from lfphys import i18n as I\n"))
        h = await (await cl.get("/api/health")).json()
        assert h["restart_needed"] is True and h["changed"] == [edited]
        cat = await (await cl.get("/api/viz")).json()
        entry = next(v for v in cat if v["id"] == WORLD)
        assert entry["error"] == {"$t": "the visualization does not load: {error}", "a": {"error": RESTART_TEXT}}
        assert entry["detail"] == "AttributeError: module 'lfphys.i18n' has no attribute 'P_ATM'"
        assert entry["title"] == WORLD and entry["kind"] == "demo"
        r = await cl.get(f"/api/viz/{WORLD}")
        body = await r.json()
        assert r.status == 503 and body["error"] == entry["error"] and body["detail"] == entry["detail"]
        assert body["text"] == ("the visualization does not load: the server's code changed on disk after it started: "
                                "restart the server")
        return body["error"]

    error = _api(tree, steps)
    # in Russian too (the real catalogues: the temporary tree has none)
    ru = json.loads((REAL / "locales" / "ru.json").read_text(encoding="utf-8"))
    rendered = i18n.render(error, ru, "ru")
    assert rendered.endswith(ru[RESTART_TEXT.msgid]) and "P_ATM" not in rendered


def test_a_world_that_fails_while_the_code_is_unchanged_keeps_its_own_error(tree):
    async def steps(cl):
        _write(tree["viz"] / WORLD / "viz.py", _world("I.NOT_THERE", "from lfphys import i18n as I\n"))
        h = await (await cl.get("/api/health")).json()
        assert h["restart_needed"] is False
        entry = next(v for v in await (await cl.get("/api/viz")).json() if v["id"] == WORLD)
        detail = "AttributeError: module 'lfphys.i18n' has no attribute 'NOT_THERE'"
        assert entry["error"] == {"$t": "the visualization does not load: {error}", "a": {"error": detail}}
        assert entry["detail"] == detail
        r = await cl.get(f"/api/viz/{WORLD}")
        assert r.status == 500 and (await r.json())["detail"] == detail
        _write(tree["viz"] / WORLD / "viz.py", _world("'mended'"))  # mended: loads at the next request
        assert cl.server.app[MGR].viz(WORLD)["title"] == "mended"
        r = await cl.get("/api/viz/u94_no_such_world")
        assert r.status == 404
        return True

    assert _api(tree, steps)
