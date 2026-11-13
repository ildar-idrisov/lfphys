# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The static site's build and check (``site/build.py``, ``site/check.py``, ``site/readme.py``; design of the start page
§4.5, §5.1, §5.3, §5.4; CONTRACT of steps S and P), with the two tiny test worlds of ``tests/site_worlds`` recorded:

* the pages ``index.html``, ``run.html``, ``legal.html``, ``404.html`` with ``lf-mode=static``, ``lf-base`` and one import
  map whose targets are relative and exist; no absolute ``/static``, ``/api`` or ``/viz`` outside the import map;
* the catalogue files as the server returns them (``api/viz.json``, ``api/viz/<id>.json`` also under the old ids,
  ``api/planned.json``, ``api/recordings.json``, ``aliases.json``), the i18n JSON of every language, the recordings
  with their indexes, the manifest with every file's size and sha256;
* the check passes on it, and fails on a changed file, a missing recording and a budget exceeded;
* ``readme.py`` is idempotent in English and Russian and the READMEs are up to date.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys

import pytest

from lfviz import app as A
from lfviz import i18n, registry

VIZ = registry.ROOT
SITE_WORLDS = VIZ / "tests" / "site_worlds"
BASE = "/lfphys/"
TEST_WORLDS = ("u98_site_toy", "r98_site_probe")


def _site(name):
    if f"lfsite_{name}" in sys.modules:
        return sys.modules[f"lfsite_{name}"]
    spec = importlib.util.spec_from_file_location(f"lfsite_{name}", VIZ / "site" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    """A site built for /lfphys/ with the test worlds recorded (the repository's worlds have no recordings here)."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("LFVIZ_EXTRA", str(SITE_WORLDS))
        rec, build = _site("record"), _site("build")
        recs = tmp_path_factory.mktemp("rec")
        for vid in TEST_WORLDS:
            _index, problems = rec.record_world(vid, recs)
            assert problems == []
        out = tmp_path_factory.mktemp("site")
        manifest = build.build(recs, out, BASE)
        yield {"out": out, "recs": recs, "manifest": manifest, "mp": mp}


@pytest.fixture
def extra(monkeypatch):
    monkeypatch.setenv("LFVIZ_EXTRA", str(SITE_WORLDS))


def _read(site, rel):
    return (site["out"] / rel).read_text(encoding="utf-8")


def _json(site, rel):
    return json.loads(_read(site, rel))


@pytest.mark.parametrize("name", ["index.html", "run.html", "legal.html", "404.html"])
def test_a_page_has_the_static_metas_and_one_relative_import_map(site, name):
    check = _site("check")
    html = _read(site, name)
    assert '<meta name="lf-mode" content="static">' in html
    assert f'<meta name="lf-base" content="{BASE}">' in html
    maps = check.IMPORTMAP.findall(html)
    if name == "404.html":  # a page of its own: links with the base, no player
        assert not maps and f'href="{BASE}"' in html
        return
    assert len(maps) == 1
    imports = json.loads(maps[0])["imports"]
    assert imports["/static/"] == "./static/" and imports["/viz/"] == "./viz/"
    assert imports["three"].startswith("./static/vendor/") and (site["out"] / imports["three"][2:]).is_file()


@pytest.mark.parametrize("name", ["index.html", "run.html", "legal.html", "404.html"])
def test_no_page_has_an_absolute_server_path_outside_its_import_map(site, name):
    check = _site("check")
    html = _read(site, name)
    assert check.absolute_paths(html) == [], f"{name}: absolute /static, /api or /viz outside the import map"
    assert check.absolute_paths('<a href="/static/x.js">') == ["/static/"]  # the guard itself
    assert check.absolute_paths('<script type="importmap">{"imports": {"/viz/": "./viz/"}}</script>') == []


def test_the_catalogue_files_are_what_the_server_returns(site, extra):
    ids = registry.viz_ids()
    cat = _json(site, "api/viz.json")
    assert [d["id"] for d in cat] == ids
    for vid in ids:
        assert _json(site, f"api/viz/{vid}.json") == json.loads(json.dumps(registry.describe(vid), ensure_ascii=False))
    old, new = next(iter(registry.ALIASES.items()))
    assert _json(site, f"api/viz/{old}.json")["id"] == new
    assert _json(site, "aliases.json") == registry.ALIASES
    assert _json(site, "api/planned.json") == A.planned_list()
    assert _json(site, "api/audiences.json") == json.loads(json.dumps(A.audiences_list(), ensure_ascii=False))
    recs = _json(site, "api/recordings.json")
    assert set(recs["worlds"]) == set(TEST_WORLDS) and recs["site"].startswith("https://")
    assert recs == json.loads(json.dumps(A.recordings_list(site["out"] / "recordings"), ensure_ascii=False))
    health = _json(site, "api/health.json")
    assert health["cite"]["code"] == registry.citation()["code"]
    for name in A.LEGAL:  # the licence page's full texts
        assert (site["out"] / "legal" / name).is_file()
    for vid in ids:  # each world's browser module
        assert (site["out"] / "viz" / vid / "view.js").is_file()
    assert (site["out"] / "static" / "js" / "player.js").is_file()
    assert not (site["out"] / "static" / "js" / "tests").exists() and not (site["out"] / "static" / "index.html").exists()


def test_the_i18n_files_of_every_language_are_there(site):
    for lang in i18n.LANGS:
        body = _json(site, f"static/locales/{lang}.json")
        assert body["lang"] == lang and isinstance(body["messages"], dict)
    ru = _json(site, "static/locales/ru.json")["messages"]
    assert ru["Watch on the site"] and ru["Go to the start page"]
    html = _read(site, "404.html")
    assert i18n.render_in(_site("build").TO_START, "ru") in html  # the page's other language is translated


def test_the_recordings_and_the_manifest(site, extra):
    man = _json(site, "site-manifest.json")
    assert man["base"] == BASE
    for vid in TEST_WORLDS:
        w = man["worlds"][vid]
        assert w["code_hash"] == registry.code_hash(vid)
        assert {r["state"] for r in w["recordings"].values()} == {"present"}
        idx = _json(site, f"recordings/{vid}/index.json")
        for e in idx["recordings"]:
            rel = f"recordings/{vid}/{e['file']}"
            assert man["files"][rel]["bytes"] == e["bytes_gz"] and man["files"][rel]["sha256"] == e["sha256"]
    for rel, info in man["files"].items():
        assert (site["out"] / rel).stat().st_size == info["bytes"]


def test_the_check_passes_and_fails_where_it_must(site, extra, tmp_path, monkeypatch):
    check = _site("check")
    rep = check.check(site["out"], BASE, allow_missing=True)  # the repository's worlds are not recorded here
    assert [f for f in rep.fails if "absolute addresses" not in f] == []
    assert not [w for w in rep.warns if any(v in w for v in TEST_WORLDS)]
    copy = tmp_path / "site"
    shutil.copytree(site["out"], copy)
    idx = json.loads((copy / "recordings" / "u98_site_toy" / "index.json").read_text(encoding="utf-8"))
    f = copy / "recordings" / "u98_site_toy" / idx["recordings"][0]["file"]
    data = bytearray(f.read_bytes())
    data[len(data) // 2] ^= 0xFF
    f.write_bytes(bytes(data))
    fails = check.check(copy, BASE, allow_missing=True).fails
    assert any("differs" in x and "u98_site_toy" in x for x in fails)
    f.unlink()
    fails = check.check(copy, BASE, allow_missing=False).fails
    assert any("u98_site_toy/slow" in x for x in fails)
    assert any("r12_double_slit_2d" in x and "missing" in x for x in fails)  # not recorded: fails without the flag
    monkeypatch.setitem(check.L.BUDGET, "file", (10, 20))
    fails = check.check(site["out"], BASE, allow_missing=True).fails
    assert any("over the hard limit" in x and "r98_site_probe/only" in x for x in fails)
    assert any("lf-base" in x for x in check.check(site["out"], "/other/", allow_missing=True).fails)


def test_the_build_refuses_a_folder_that_is_not_its_own(tmp_path):
    (tmp_path / "keep.txt").write_text("not a site", encoding="utf-8")
    with pytest.raises(SystemExit):
        _site("build").build(None, tmp_path, BASE)
    assert (tmp_path / "keep.txt").is_file()


@pytest.mark.parametrize("lang", ["en", "ru"])
def test_readme_generation_is_idempotent_and_up_to_date(lang, monkeypatch):
    monkeypatch.delenv("LFVIZ_EXTRA", raising=False)  # the README lists the repository's worlds only
    readme = _site("readme")
    g1, g2 = readme.generate(lang), readme.generate(lang)
    assert g1 == g2 and g1.startswith(readme.BEGIN) and g1.endswith(readme.END)
    text = readme.readme_files()[lang].read_text(encoding="utf-8")
    once = readme.apply(text, g1)
    assert readme.apply(once, g1) == once == text
    assert readme.main(["--check"]) == 0
    with pytest.raises(ValueError):
        readme.apply("no markers here", g1)
    if lang != "en":
        assert not any(w in g1 for w in ("Watch on the site", "Same topic at other levels", "Planned benches"))
