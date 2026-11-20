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
* ``readme.py`` is idempotent in English and Russian and the READMEs are up to date;
* the atlases of the screens (design ``lfphys/sources/explore_2026-11-14_design.md`` §1.3, §3.8, §8): copied with
  their manifests, bases and points, listed in ``site-manifest.json`` with their keys and states; the check fails on a
  missing or changed point, a manifest that disagrees, a stale key and an atlas over its hard limit; the lab's
  worksheet page is built when the player has it.
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
TEST_WORLDS = ("u98_site_toy", "r98_site_probe", "s98_atlas_toy")


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
    assert all("picture" in a for a in _json(site, "api/audiences.json")["audiences"])  # start-page F10
    recs = _json(site, "api/recordings.json")
    assert set(recs["worlds"]) == set(TEST_WORLDS) and recs["site"].startswith("https://")
    assert recs["published"] is A.site_setting()["published"]  # D3, D4: the player falls back to the site only then
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


# --- review P17-site F4, F5, F13; integrator D3, D4 ------------------------------------------------------------------

def _copy(site, tmp_path):
    copy = tmp_path / "site"
    shutil.copytree(site["out"], copy)
    return copy


def _fails(check, copy):
    return check.check(copy, BASE, allow_missing=True).fails


def test_the_check_catches_a_missing_view_picture_or_absolute_address_in_a_script(site, extra, tmp_path):
    """F5: the module graph of the site: every catalogue world's view module, every named picture, and no absolute
    server address in a script (the import map serves /static/ and /viz/; nothing else is absolute on the site)."""
    check = _site("check")
    assert check.js_absolute('const a = "/api/runs"; b = `/run?id=${x}`; c = \'/recordings/x\';') == \
        ["/api/", "/recordings/", "/run?"]
    assert check.js_absolute('import { t } from "/static/js/i18n.js"; await import(`/viz/${id}/view.js`);') == []
    assert check.js_absolute('// a comment: "/run?rec=…"\n/* "/api/x" */ const u = url("api/x");') == []
    assert check.js_absolute('const s = "https://example.org/api/x";') == []
    base = _fails(check, site["out"])
    copy = _copy(site, tmp_path)
    (copy / "viz" / "u98_site_toy" / "view.js").unlink()
    assert any("viz/u98_site_toy/view.js is missing" in f for f in _fails(check, copy))
    copy = _copy(site, tmp_path / "b")
    js = copy / "static" / "js" / "start.js"
    js.write_text(js.read_text(encoding="utf-8") + '\nconst bad = fetch("/api/runs");\n', encoding="utf-8")
    assert any("static/js/start.js: absolute server addresses ['/api/']" in f for f in _fails(check, copy))
    cat = [d for d in _json(site, "api/viz.json") if d.get("picture")]
    if cat:  # a world with a picture: its file is required
        copy = _copy(site, tmp_path / "c")
        (copy / "images" / f"{cat[0]['id']}.jpg").unlink()
        assert any(f"images/{cat[0]['id']}.jpg is missing" in f for f in _fails(check, copy))
    assert not [f for f in base if "is missing (the world's view module)" in f or "absolute server" in f]


def test_the_check_fails_a_recording_with_a_failed_check_and_warns_on_extras(site, extra, tmp_path):
    """D5 (F4): an index entry that counts a check ending failed fails the site; F13: an entry or a file the registry
    does not ask for is warned, and the build leaves such an entry out."""
    check = _site("check")
    copy = _copy(site, tmp_path)
    f = copy / "recordings" / "u98_site_toy" / "index.json"
    idx = json.loads(f.read_text(encoding="utf-8"))
    assert all(e["checks"]["failed"] == 0 for e in idx["recordings"])
    idx["recordings"][0]["checks"]["failed"] = 2
    extra_e = {**idx["recordings"][1], "id": "gone", "file": "gone.00000000.lfrec.gz"}
    (copy / "recordings" / "u98_site_toy" / extra_e["file"]).write_bytes(b"x")
    (copy / "recordings" / "u98_site_toy" / "stray.lfrec.gz").write_bytes(b"x")
    idx["recordings"].append(extra_e)
    f.write_text(json.dumps(idx), encoding="utf-8")
    rep = check.check(copy, BASE, allow_missing=True)
    assert any("u98_site_toy/slow: 2 check(s) end failed" in x for x in rep.fails)
    assert any("u98_site_toy/gone: in the site's index, not asked for" in w for w in rep.warns)
    assert any("recordings/u98_site_toy/stray.lfrec.gz: a file its index does not name" in w for w in rep.warns)
    # the build copies only what the registry asks for
    recs = tmp_path / "recs"
    shutil.copytree(site["recs"], recs)
    ri = recs / "u98_site_toy" / "index.json"
    idx = json.loads(ri.read_text(encoding="utf-8"))
    idx["recordings"].append({**idx["recordings"][1], "id": "gone"})
    ri.write_text(json.dumps(idx), encoding="utf-8")
    out = tmp_path / "out"
    _site("build").build(recs, out, BASE)
    built = json.loads((out / "recordings" / "u98_site_toy" / "index.json").read_text(encoding="utf-8"))
    assert [e["id"] for e in built["recordings"]] == ["slow", "fast"]


def test_the_site_setting_reaches_the_player_and_the_check(site, extra, tmp_path, monkeypatch):
    """D3, D4: site/site.json says where the public site is and whether it is published; /api/recordings and the site's
    api/recordings.json carry both (LFVIZ_SITE_URL overrides the address on a server); the check fails when the built
    file disagrees with the setting."""
    setting = json.loads(A.SITE_JSON.read_text(encoding="utf-8"))
    assert set(setting) == {"published", "url"} and isinstance(setting["published"], bool)
    assert setting["url"] == "https://ildar-idrisov.github.io/lfphys/"
    f = tmp_path / "site.json"
    f.write_text(json.dumps({"published": True, "url": "https://example.org/x"}), encoding="utf-8")
    monkeypatch.setattr(A, "SITE_JSON", f)
    monkeypatch.delenv("LFVIZ_SITE_URL", raising=False)
    assert A.site_setting() == {"published": True, "url": "https://example.org/x/"}
    got = A.recordings_list(tmp_path / "none")
    assert {k: v for k, v in got.items() if k != "expected"} == {"worlds": {}, "site": "https://example.org/x/",
                                                                 "published": True}
    monkeypatch.setenv("LFVIZ_SITE_URL", "http://127.0.0.1:9/")
    assert A.site_setting()["url"] == "http://127.0.0.1:9/" and A.site_setting(env=False)["url"] == "https://example.org/x/"
    monkeypatch.delenv("LFVIZ_SITE_URL")
    f.write_text("{not json", encoding="utf-8")  # an unreadable setting: not published
    assert A.site_setting()["published"] is False
    f.write_text(json.dumps({"published": True, "url": "https://example.org/x/"}), encoding="utf-8")
    # the site was built with the repository's setting: now it differs
    check = _site("check")
    monkeypatch.setattr(check, "site_setting", A.site_setting)
    if setting["published"] is not True:
        assert any("api/recordings.json: published" in x for x in _fails(check, site["out"]))


# --- the atlases of the screens (design of 2026-11-14 §1.3, §3.8, §8) ---------------------------------------------

def test_the_atlases_are_copied_and_in_the_manifest(site, extra):
    man = _json(site, "site-manifest.json")
    w = man["worlds"]["s98_atlas_toy"]
    assert set(w["atlases"]) == {"explore", "throws", "lab.heights", "lab.ticks"}  # the toy's EX2 screen and step
    assert {a["state"] for a in w["atlases"].values()} == {"present"}
    idx = _json(site, "recordings/s98_atlas_toy/index.json")
    assert [a["id"] for a in idx["atlases"]] == ["explore", "throws", "lab.heights", "lab.ticks"]
    for a in idx["atlases"]:
        assert w["atlases"][a["id"]]["key"] == a["key"] and w["atlases"][a["id"]]["file"] == a["file"]
        m = _json(site, f"recordings/s98_atlas_toy/{a['file']}")
        folder = f"recordings/s98_atlas_toy/{a['file'].rsplit('/', 1)[0]}"
        assert man["files"][f"{folder}/{m['base']['file']}"]["sha256"] == m["base"]["sha256"]
        for name, size, state in m["points"]:
            if not state:
                assert man["files"][f"{folder}/{name}"]["bytes"] == size
        if m.get("pool"):  # the blobs the points share (EX2 §5 F10): copied and named like the base
            assert man["files"][f"{folder}/{m['pool']['file']}"]["sha256"] == m["pool"]["sha256"]
    assert _json(site, f"recordings/s98_atlas_toy/{idx['atlases'][0]['file']}").get("pool"), "the toy's explore has a pool"
    recs = _json(site, "api/recordings.json")
    assert recs["worlds"]["s98_atlas_toy"]["atlases"] == idx["atlases"]  # the player finds the manifests there
    d = _json(site, "api/viz/s98_atlas_toy.json")
    assert [s["kind"] for s in d["screens"]] == ["watch", "explore", "explore", "lab"]  # «Throws»: the toy's EX2 screen


def test_the_check_fails_on_a_broken_atlas(site, extra, tmp_path, monkeypatch):
    check = _site("check")
    assert not [f for f in _fails(check, site["out"]) if "s98_atlas_toy" in f]
    idx = _json(site, "recordings/s98_atlas_toy/index.json")
    e = idx["atlases"][0]
    m = _json(site, f"recordings/s98_atlas_toy/{e['file']}")
    name = m["points"][4][0]
    # a missing point
    copy = _copy(site, tmp_path / "a")
    (copy / "recordings" / "s98_atlas_toy" / "atlas" / "explore" / name).unlink()
    assert any("point p4" in f and "missing" in f for f in _fails(check, copy))
    # a changed point
    copy = _copy(site, tmp_path / "b")
    f = copy / "recordings" / "s98_atlas_toy" / "atlas" / "explore" / name
    data = bytearray(f.read_bytes())
    data[len(data) // 2] ^= 0xFF
    f.write_bytes(bytes(data))
    assert any("point p4" in x and "differs" in x for x in _fails(check, copy))
    # a manifest that disagrees with its index
    copy = _copy(site, tmp_path / "c")
    mf = copy / "recordings" / "s98_atlas_toy" / e["file"]
    mm = json.loads(mf.read_text(encoding="utf-8"))
    mm["key"] = "0" * 16
    mm["points"] = mm["points"][:-1]
    mf.write_text(json.dumps(mm), encoding="utf-8")
    fails = _fails(check, copy)
    assert any("manifest disagrees" in x for x in fails) and any("its grid has 6" in x for x in fails)
    # a stale key (in the index and the site's manifest)
    copy = _copy(site, tmp_path / "d")
    ix = copy / "recordings" / "s98_atlas_toy" / "index.json"
    j = json.loads(ix.read_text(encoding="utf-8"))
    j["atlases"][0]["key"] = "1" * 16
    ix.write_text(json.dumps(j), encoding="utf-8")
    assert any("atlas explore: stale" in x for x in check.check(copy, BASE, allow_missing=False).fails)
    # the pool (EX2 §5 F10): missing, or of another size
    copy = _copy(site, tmp_path / "p")
    pf = copy / "recordings" / "s98_atlas_toy" / "atlas" / "explore" / m["pool"]["file"]
    pf.unlink()
    assert any("atlas explore" in x and "its pool" in x and "missing or differs" in x for x in _fails(check, copy))
    copy = _copy(site, tmp_path / "q")
    pf = copy / "recordings" / "s98_atlas_toy" / "atlas" / "explore" / m["pool"]["file"]
    pf.write_bytes(pf.read_bytes() + b"x")
    assert any("atlas explore" in x and "its pool" in x for x in _fails(check, copy))
    # missing altogether
    copy = _copy(site, tmp_path / "e")
    shutil.rmtree(copy / "recordings" / "s98_atlas_toy" / "atlas" / "lab.heights")
    assert any("atlas lab.heights" in x and "missing" in x for x in _fails(check, copy))
    # over the atlas's and the point's hard limits
    monkeypatch.setitem(check.L.BUDGET, "atlas", (100, 1000))
    monkeypatch.setitem(check.L.BUDGET, "point", (100, 1000))
    fails = _fails(check, site["out"])
    assert any("atlas explore" in x and "atlas's hard limit" in x for x in fails)
    assert any("atlas explore: point p" in x and "hard limit" in x for x in fails)


def test_the_expected_keys_reach_the_player_and_the_check(site, extra, tmp_path):
    """Integrator D11: ``GET /api/recordings`` and the site's ``api/recordings.json`` carry, per world with recordings,
    the version, the code hash and the keys of its recordings and atlases as the code gives them; a server's player
    takes the public site's atlas only when its key is the expected one. The check fails when they differ."""
    check, L = _site("check"), _site("check").L
    recs = _json(site, "api/recordings.json")
    exp = recs["expected"]
    assert set(exp) == set(L.demo_worlds())
    toy = exp["s98_atlas_toy"]
    plan = L.planned_world("s98_atlas_toy")
    assert toy == {"version": plan["version"], "code_hash": registry.code_hash("s98_atlas_toy"),
                   "recordings": {r["id"]: r["key"] for r in plan["recordings"]},
                   "atlases": {a["id"]: a["key"] for a in plan["atlases"]}}
    idx = _json(site, "recordings/s98_atlas_toy/index.json")
    assert {a["id"]: a["key"] for a in idx["atlases"]} == toy["atlases"]  # what the player compares
    assert A.recordings_list(tmp_path / "none")["expected"] == exp  # a server gives the same
    assert not [f for f in _fails(check, site["out"]) if "expected" in f]
    copy = _copy(site, tmp_path / "x")
    f = copy / "api" / "recordings.json"
    j = json.loads(f.read_text(encoding="utf-8"))
    j["expected"]["s98_atlas_toy"]["atlases"]["explore"] = "0" * 16
    f.write_text(json.dumps(j), encoding="utf-8")
    assert any("expected[s98_atlas_toy]" in x for x in _fails(check, copy))
    del j["expected"]
    f.write_text(json.dumps(j), encoding="utf-8")
    assert any("no expected keys" in x for x in _fails(check, copy))


def test_the_expected_keys_are_kept_while_the_code_is(extra, monkeypatch):
    """Review R2-F F9: ``GET /api/recordings`` read every world's VIZ and planned its keys on every request (0.23 s on
    the event loop). They are kept per world while its code hash, the recorder's hash and its folder are the same; a
    world whose code changed is computed again, alone."""
    monkeypatch.setattr(A, "_EXPECTED", {})
    loads = []

    def load(vid):
        loads.append(vid)
        return registry.load(vid)
    first = A.expected_keys(load)
    assert "s98_atlas_toy" in first and loads
    loads.clear()
    assert A.expected_keys(load) == first and loads == []  # nothing read again
    first["s98_atlas_toy"]["atlases"]["explore"] = "x"  # the caller's copy: the cache is not changed through it
    assert A.expected_keys(load)["s98_atlas_toy"]["atlases"]["explore"] != "x"
    real = registry.code_hash_current
    monkeypatch.setattr(registry, "code_hash_current", lambda v: "0" * 12 if v == "s98_atlas_toy" else real(v))
    again = A.expected_keys(load)
    assert loads == ["s98_atlas_toy"] and again["s98_atlas_toy"]["code_hash"] == "0" * 12
    plan = _site("check").L.planned_world("s98_atlas_toy", "0" * 12)
    assert again["s98_atlas_toy"]["atlases"] == {a["id"]: a["key"] for a in plan["atlases"]}


def test_the_worksheet_page_is_built_when_the_player_has_it(site, tmp_path, monkeypatch):
    build, check = _site("build"), _site("check")
    has = (A.PLAYER / "worksheet.html").is_file()
    assert ("worksheet.html" in build.pages()) == has
    assert (site["out"] / "worksheet.html").is_file() == has
    if has:
        html = _read(site, "worksheet.html")
        assert '<meta name="lf-mode" content="static">' in html and check.IMPORTMAP.findall(html)
