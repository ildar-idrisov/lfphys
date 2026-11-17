# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The registry as the one source of the start page, the README and the public site (``AGENTS.md`` §3 rules 14–16;
design of the start page §3, §5.4): the completeness check that fails. It needs no recordings.

* every world: its audience agrees with its prefix, its section is known, ``ui`` agrees with the audience, the fields
  its audience needs are there (``registry.check``), and it has a teaser;
* every non-laboratory world has recording specs naming its own presets and only the commands a script may use, within
  ``registry.RECORDING_LIMITS`` and, at the rates measured on 2026-11-12, within the site's size budgets;
* ``related`` links point to a world or a planned item and are mutual between them;
* the aliases resolve and collide with no folder; no two folders share a number; a planned id collides with no folder
  of another item;
* every text of a world (title, teaser, summary, purpose, preset labels, recording labels, courses, the research
  question), of the audiences and sections, and of the planned items is translated into every language of
  ``LANGUAGES.md`` (beyond ``tests/i18n_pending.txt``).

* the generated catalogue sections of the root READMEs (``README.md``, ``README.<code>.md`` of every language) carry
  their markers once and equal ``site/readme.py``'s output (step S);
* the README's links to the public site follow ``site/site.json``: none while it is not published (one line says the
  site is being prepared and the recordings play locally; the recordings are named), every recording linked once it
  is, with ``&lang=<code>`` in a language other than the default (integrator D3; review P17-site F6, F7);
* the audiences' tiles name worlds of their own audience (``registry.check_audiences``; start-page F10);
* every world has its picture ``docs/images/<id>.jpg`` (``site/posters.mjs``): a JPEG 1200 px wide within the poster
  budget's hard limit, listed in ``docs/images/posters.json`` (step S).
"""

from __future__ import annotations

import importlib.util
import json
import sys
import re
import struct
from collections import Counter

import pytest

from lfviz import i18n, registry
from lfviz.i18n import T, is_t, msgids

import i18n_tools as tools

VIZ = registry.ROOT
PLANNED = json.loads((VIZ / "planned.json").read_text(encoding="utf-8"))
OTHER = [code for code in i18n.LANGS if code != i18n.DEFAULT]
IDS = registry.viz_ids()  # the repository's worlds (LFVIZ_EXTRA unset: the test worlds are checked separately)

#: gzip -9 of a recorded frame, kB, measured on 2026-11-12 (scratch size table of the start-page design §4.3: one preset
#: per world, its record without checkpoints divided by its frames, so the world's opening messages are included);
#: "base" is a volume sent once at the start (u38: one 6.3 MB float volume)
RATE_KB = {"u31_light_travel": 0.33, "u32_double_slit": 1.6, "u33_quantum_1d": 9.3, "u34_orbits": 0.25,
           "u35_optics_bench": 0.28, "u36_qcd": 0.2, "u37_bell_test": 0.075, "u38_wave_3d": 5.0,
           "u39_fast_observer": 10.6, "u40_hydrogen_3d": 0.35, "u41_quarkonium_3d": 0.42, "u42_kerr_shadow": 1.6,
           "u43_optical_vortices": 5.4, "u44_mie_scattering": 4.1, "r11_thomas_3d": 1.3, "r12_double_slit_2d": 8.3,
           "r13_arrival_times_2d": 8.8,
           "s03_projectile": 0.07}  # S03: 46.6 kB gzip for 800 frames of "independence" (2026-11-14), with a margin
BASE_KB = {"u38_wave_3d": 6300.0}
#: the hard limits of the design §4.3 (the site's check fails above them; the targets are 3 MB and 12 MB)
FILE_LIMIT_KB, WORLD_LIMIT_KB = 10_000.0, 25_000.0


def _viz(vid):
    return registry.load(vid)


def _planned_ids():
    return {p["id"] for p in PLANNED}


@pytest.mark.parametrize("vid", IDS)
def test_a_world_declares_its_audience_section_ui_and_the_fields_its_audience_needs(vid):
    viz = _viz(vid)  # load() raises on any problem of registry.check
    assert registry.check(viz) == []
    aud = registry.AUDIENCE[viz["audience"]]
    assert vid[0] == aud["prefix"] and viz["kind"] == ("playground" if aud["id"] == "playground" else "demo")
    assert viz["section"] in registry.SECTION and viz["ui"] in registry.UIS
    d = registry.describe(viz)
    for k in ("audience", "section", "ui", "teaser", "related", "recordings", "aliases"):
        assert k in d, k


def test_the_registry_check_refuses_what_the_design_forbids():
    good = _viz("u32_double_slit")
    assert registry.check(good) == []

    def bad(**kw):
        return registry.check({**good, **kw})
    assert any("prefix" in x for x in bad(audience="research", ui="full", question=T("Q"), status="hypothesis",
                                          prior_art=[{"ref": "x"}]))
    assert any("section" in x for x in bad(section="alchemy"))
    assert any("school" in x for x in bad(ui="school"))
    assert any("teaser" in x for x in bad(teaser="a plain string"))
    assert any("courses" in x for x in bad(courses=[]))
    assert any("no recordings" in x for x in bad(recordings=[]))
    rec = dict(good["recordings"][0])
    assert any("preset" in x for x in bad(recordings=[{**rec, "preset": "nope"}]))
    assert any("fps" in x for x in bad(recordings=[{**rec, "fps": 120}]))
    assert any("frames" in x for x in bad(recordings=[{**rec, "seconds": 180, "fps": 30}]))
    assert any("poster" in x for x in bad(recordings=[{**rec, "poster": 1e6}]))
    assert any("script" in x for x in bad(recordings=[{**rec, "script": [{"at": 1, "cmd": "delete", "args": {}}]}]))
    assert any("unique" in x for x in bad(recordings=[rec, rec]))
    assert any("related" in x for x in bad(related=["nowhere"]))
    lab = _viz("p01_gravity")
    assert any("laboratory has no recordings" in x for x in registry.check({**lab, "recordings": [rec]}))
    res = _viz("r12_double_slit_2d")
    assert any("hypothesis" in x for x in registry.check({**res, "status": "confirmed"}))
    assert any("question" in x for x in registry.check({**res, "question": None}))
    assert any("prior art" in x for x in registry.check({**res, "prior_art": []}))
    school = {**good, "id": "s02_free_fall", "audience": "school", "ui": "school", "curriculum": [], "screens": []}
    probs = registry.check(school)
    assert any("FRP" in x for x in probs) and any("AP, IB" in x for x in probs)
    assert any("Explore screen" in x for x in probs) and any("Lab work" in x for x in probs)  # the guide's successors
    assert any("modified physics" in x for x in probs)  # u32's schema has laws: no school world may
    assert any("guide is retired" in x for x in registry.check({**school, "guide": [T("a step")]}))
    assert any("speed takes" in x for x in bad(recordings=[{**rec, "script": [{"at": 1, "cmd": "speed",
                                                                               "args": {"value": 0}}]}]))
    assert not [x for x in bad(recordings=[{**rec, "script": [{"at": 1, "cmd": "speed", "args": {"value": 0.1}}]}])
                if "speed" in x]
    assert any("captions" in x for x in bad(recordings=[{**rec, "captions": "text"}]))
    assert any("caption at 2" in x for x in bad(recordings=[{**rec, "captions": [{"at": 2, "text": "plain"}]}]))
    assert any("order" in x for x in bad(recordings=[{**rec, "captions": [{"at": 2, "text": T("a")},
                                                                          {"at": 1, "text": T("b")}]}]))
    assert any("quantize" in x for x in bad(recordings=[{**rec, "quantize": {"segment.map": "f16"}}]))
    assert any("not declared safe" in x for x in bad(recordings=[{**rec, "quantize": {"segment.nowhere": "u8sqrt"}}]))


@pytest.mark.parametrize("vid", [v for v in IDS if not v.startswith("p")])
def test_a_demonstration_has_recordings_within_the_budgets(vid):
    viz = _viz(vid)
    recs = registry.recordings_of(viz)
    assert 1 <= len(recs) <= 4
    assert vid in RATE_KB, (f"{vid}: no measured rate in RATE_KB (gzip kB per recorded frame): record it "
                            f"(site/record.py --world {vid}) and add bytes_gz / frames_recorded of its largest recording")
    presets = viz["schema"].presets
    total = 0.0
    for r in recs:
        assert r["preset"] in presets
        assert all(c["cmd"] in registry.RECORDING_LIMITS["commands"] for c in r["script"])
        assert is_t(r["label"]), r
        est = BASE_KB.get(vid, 0.0) + r["seconds"] * r["fps"] * RATE_KB[vid]
        assert est <= FILE_LIMIT_KB, (vid, r["id"], est)
        total += est
    assert total <= WORLD_LIMIT_KB, (vid, total)


def test_test_worlds_found_through_lfviz_extra_validate_too(monkeypatch):
    monkeypatch.setenv("LFVIZ_EXTRA", ":".join(str(VIZ / "tests" / d) for d in ("playgrounds", "instruments_worlds")))
    for vid in ("p99_toy", "p97_osc"):
        viz = registry.load(vid)
        assert viz["audience"] == "playground" and registry.check(viz) == []


def _targets():
    return set(IDS) | _planned_ids()


def test_related_links_point_somewhere_and_are_mutual():
    planned = {p["id"]: p for p in PLANNED}
    links = {vid: set(_viz(vid).get("related") or []) for vid in IDS}
    links.update({pid: set(p.get("related") or []) for pid, p in planned.items()})
    bad = [(a, b) for a, bs in links.items() for b in bs if b not in _targets()]
    assert not bad, f"related links that point nowhere: {bad}"
    one_sided = [(a, b) for a, bs in links.items() for b in bs if a not in links.get(b, set())]
    assert not one_sided, f"one-sided related links (both ends exist): {one_sided}"
    assert not [a for a, bs in links.items() if a in bs], "a world related to itself"


def test_aliases_and_numbers_do_not_collide():
    ids = set(IDS)
    for old, new in registry.ALIASES.items():
        assert new in ids and old not in ids
    numbers = Counter(v[:3] for v in ids)
    assert not [n for n, k in numbers.items() if k > 1], numbers
    folder_of = {v[:3]: v for v in ids}
    for p in PLANNED:
        num = p["id"][0].lower() + p["id"][1:]
        if num in folder_of:  # the item has landed: the site's build drops the planned entry; same section only
            assert _viz(folder_of[num])["section"] == p["section"], (p["id"], folder_of[num])


def test_the_planned_items_are_well_formed():
    ids = [p["id"] for p in PLANNED]
    assert len(ids) == len(set(ids))
    counts = Counter(p["audience"] for p in PLANNED)
    assert counts == {"school": 45, "university": 30, "research": 10, "playground": 3}, counts
    assert [p["id"] for p in PLANNED if p["audience"] == "school"] == [f"S{i:02d}" for i in range(1, 46)]
    assert [p["id"] for p in PLANNED if p["audience"] == "university"] == [f"U{i:02d}" for i in range(1, 31)]
    assert [p["id"] for p in PLANNED if p["audience"] == "research"] == [f"R{i:02d}" for i in range(1, 11)]
    for p in PLANNED:
        aud = registry.AUDIENCE[p["audience"]]
        assert p["id"][0].lower() == aud["prefix"] and re.fullmatch(r"[SURp]\d{2}", p["id"]), p
        assert p["section"] in registry.SECTION, p
        assert p["state"] in ("next", "planned") and (p["state"] == "next") == (p.get("batch") == "AB1"), p
        assert isinstance(p["title"], str) and p["title"].strip()
        assert not any(0x400 <= ord(c) <= 0x4FF for c in json.dumps(p, ensure_ascii=False)), p  # English only
        if p["audience"] == "school":
            systems = {c["system"] for c in p["curriculum"]}
            assert any(s.startswith("FRP") for s in systems) and p["grades"], p
        if p["audience"] == "research":
            assert p["status"] == "hypothesis" and isinstance(p["rank"], int)
    assert {p["id"] for p in PLANNED if p["state"] == "next"} == {"S01", "S02", "S03", "S09"}


def _world_texts(vid) -> set[str]:
    viz = _viz(vid)
    d = registry.describe(viz)
    ids = msgids({k: viz.get(k) for k in ("title", "summary", "purpose", "teaser", "question", "lab_absent")})
    ids |= msgids([p.get("label") for p in viz["schema"].presets.values()])
    ids |= msgids([r["label"] for r in d["recordings"]])
    ids |= msgids([r["captions"] for r in d["recordings"]])  # the Watch's captions (design of 2026-11-14 §2.2)
    ids |= msgids(d.get("courses") or [])
    ids |= msgids(d.get("screens") or [])  # tabs, controls, instruments, steps, columns, laws, the worksheet (§2)
    return ids


@pytest.mark.parametrize("lang", OTHER)
def test_every_catalogue_text_is_translated(lang):
    own = i18n._merge(lang)[0]
    pending = tools.read_pending()
    report = []
    for vid in IDS:
        if any((VIZ.parent / p).resolve().is_relative_to(registry.folder(vid).resolve()) for p in pending):
            continue  # being converted (i18n_pending.txt)
        report += [(vid, m) for m in _world_texts(vid) if tools.needs_translation(m) and m not in own]
    framework = msgids([a["label"] for a in registry.AUDIENCES] + [a["text"] for a in registry.AUDIENCES]
                       + [s["label"] for s in registry.SECTIONS])
    report += [("registry", m) for m in framework if m not in own]
    report += [(p["id"], m) for p in PLANNED for m in (p["title"], p.get("text")) if m and m not in own]
    assert not report, f"{len(report)} texts without a {lang} translation: {report[:30]}"


# --- step S: the generated READMEs and the pictures (visualizations/site/) ------------------------------------------
def _site_module(name):
    if f"lfsite_{name}" in sys.modules:
        return sys.modules[f"lfsite_{name}"]
    spec = importlib.util.spec_from_file_location(f"lfsite_{name}", VIZ / "site" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # a dataclass looks its module up there
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("lang", i18n.LANGS)
def test_the_readme_catalogue_is_the_registrys_in_every_language(lang):
    readme = _site_module("readme")
    f = readme.readme_files()[lang]
    assert f.is_file(), f"{f.name} is missing (LANGUAGES.md lists {lang})"
    text = f.read_text(encoding="utf-8")
    assert text.count(readme.BEGIN) == 1 and text.count(readme.END) == 1, f"{f.name}: the markers of the generated section"
    assert readme.apply(text, readme.generate(lang), f.name) == text, \
        f"{f.name}: the generated section differs from the registry: run python3 site/readme.py"
    for vid in IDS:  # every world in exactly one audience
        n = len(re.findall(r"\*\*\[%s · " % re.escape(vid.split("_", 1)[0]), text))
        assert n == 1, (f.name, vid, n)


@pytest.mark.parametrize("published", [False, True])
@pytest.mark.parametrize("lang", i18n.LANGS)
def test_the_readme_links_to_the_site_follow_its_setting(lang, published, monkeypatch):
    """D3: until the owner publishes the site, the README has no link to it (a visitor would get a 404) and says, in
    its language, that the site is being prepared and the recordings play locally; once ``published`` is true, every
    recording of every world is linked, in the README's language (F6: the player does not follow the browser's)."""
    monkeypatch.delenv("LFVIZ_EXTRA", raising=False)
    readme = _site_module("readme")
    url = "https://ildar-idrisov.github.io/lfphys/"
    monkeypatch.setattr(readme, "site_setting", lambda env=True: {"published": published, "url": url})
    g = readme.generate(lang)
    links = re.findall(r"\]\((https://[^)\s]+run\.html\?rec=[^)\s]+)\)", g)  # the recordings' links
    screens = re.findall(r"\]\((https://[^)\s]+run\.html\?demo=[^)\s]+)\)", g)  # the screens' (design 2026-11-14)
    soon = i18n.render_in(readme.SITE_SOON, lang)
    n_recs = sum(len(registry.recordings_of(registry.load(vid))) for vid in IDS)
    n_screens = sum(len(registry.screens_of(registry.load(vid))) for vid in IDS)
    assert len(screens) == (n_screens if published else 0)
    if not published:
        assert links == [] and url not in g, links[:3]
        assert g.count(soon) == 1
        assert g.count(f"▷ {i18n.render_in(readme.RECORDINGS, lang)}:") == \
            sum(1 for vid in IDS if registry.recordings_of(registry.load(vid)))
        return
    assert soon not in g and len(links) == n_recs
    for vid in IDS:
        for r in registry.recordings_of(registry.load(vid)):
            want = f"{url}run.html?rec={vid}/{r['id']}" + ("" if lang == i18n.DEFAULT else f"&lang={lang}")
            assert links.count(want) == 1, want
    if lang == i18n.DEFAULT:
        assert not any("lang=" in x for x in links)


def test_the_committed_readme_matches_the_committed_site_setting():
    """The READMEs in the repository are generated with ``site/site.json`` as committed (``readme.py --check``)."""
    from lfviz.app import site_setting

    readme = _site_module("readme")
    text = readme.readme_files()[i18n.DEFAULT].read_text(encoding="utf-8")
    has_links = "run.html?rec=" in text
    assert has_links == site_setting(env=False)["published"], \
        "the README's links to the site disagree with site/site.json: run python3 site/readme.py"


def test_the_audiences_tiles_name_their_own_worlds():
    assert registry.check_audiences() == []


def _jpeg_size(data: bytes):
    """(width, height) of a JPEG from its first frame header (SOF0..SOF15 but DHT, JPG, DAC)."""
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            return None
        marker, length = data[i + 1], struct.unpack(">H", data[i + 2:i + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + length
    return None


@pytest.mark.parametrize("vid", IDS)
def test_every_world_has_its_picture(vid):
    pic = registry.picture(vid)
    assert pic, f"no docs/images/{vid}.jpg: make it with visualizations/site/posters.mjs"
    data = (VIZ.parent / pic).read_bytes()
    assert data[:2] == b"\xff\xd8", "not a JPEG"
    assert len(data) <= 400_000, (vid, len(data))  # the poster's hard limit (design §4.3; the target is 150 kB)
    size = _jpeg_size(data)
    assert size and size[0] == 1200, (vid, size)
    posters = json.loads((VIZ.parent / "docs" / "images" / "posters.json").read_text(encoding="utf-8"))
    assert vid in posters, f"{vid} is not in docs/images/posters.json"


# --- the screens (design lfphys/sources/explore_2026-11-14_design.md §2, §2.5) --------------------------------------
SITE_WORLDS = VIZ / "tests" / "site_worlds"
TOY = "s98_atlas_toy"


@pytest.fixture
def toy(monkeypatch):
    monkeypatch.setenv("LFVIZ_EXTRA", str(SITE_WORLDS))
    return registry.load(TOY)


def test_the_toy_worlds_screens_validate_and_are_described(toy):
    assert registry.check(toy) == []
    d = registry.describe(toy)
    assert [s["kind"] for s in d["screens"]] == ["watch", "explore", "lab"]
    assert [s["label"]["$t"] for s in d["screens"]] == ["Watch", "Explore", "Lab work"]
    ex = d["screens"][1]
    assert ex["atlas"] == "explore" and [c["kind"] for c in ex["controls"]] == ["slider", "slider"]
    assert ex["controls"][0]["label"]["$t"] == "Height" and ex["controls"][0]["law"] is False
    lab = d["screens"][2]
    assert lab["steps"][0]["atlas"] == "lab.heights" and lab["instruments"]["tape"]["error"] == 0.0005
    assert [a["id"] for a in registry.atlases_of(toy)] == ["explore", "lab.heights"]
    assert registry.view_declarations(toy) == {"quantSafe": {"traj.s": "u16", "header.ticks": "u16"},
                                               "overlays": ["path", "strobe", "v"]}
    assert {"s98_atlas_toy"} <= set(registry.viz_ids())


def _screens_problems(toy, **kw):
    sc = [dict(s) for s in toy["screens"]]
    for i, ch in kw.items():
        sc[int(i[1:])] = {**sc[int(i[1:])], **ch}
    return registry.check({**toy, "screens": sc})


def test_the_registry_refuses_what_the_screens_design_forbids(toy):
    def p(**kw):
        return _screens_problems(toy, **kw)
    assert any("kind" in x for x in p(s0={"kind": "slideshow"}))
    assert any("unique slug" in x for x in p(s1={"id": "watch"}))
    assert any("label is a T" in x for x in p(s1={"label": "plain"}))
    assert any("no captions" in x for x in p(s0={"recording": "field"}))
    assert any("none of the world's recordings" in x for x in p(s0={"recording": "nope"}))
    assert any("preset" in x for x in p(s1={"preset": "nope"}))
    assert any("frame_dt" in x for x in p(s1={"frame_dt": 0}))
    assert any("stop" in x for x in p(s1={"stop": {"seconds": 3}}))
    assert any("stop" in x for x in p(s1={"stop": {"event": "landing"}}))  # max_world_s is required
    assert any("cannot be dropped" in x for x in p(s1={"drop": {"types": ["check"], "frame_blobs": []}}))
    assert any("acts" in x for x in p(s1={"acts": "later"}))
    assert any("time" in x for x in p(s1={"time": "forever"}))
    assert any("traces" in x for x in p(s1={"traces": 6}))
    assert any("not declared by the view" in x for x in p(s1={"overlays": ["path", "rainbow"]}))
    assert any("not declared safe" in x for x in p(s1={"quantize": {"traj.s": "u8sqrt"}}))
    assert any("quantize key" in x for x in p(s1={"quantize": {"traj": "u16"}}))
    assert not [x for x in p(s1={"quantize": {"traj.s": "u16:col"}})]  # u16 declared, the suffix is the packer's
    ctl = toy["screens"][1]["controls"]
    assert any("parameter of the schema" in x for x in p(s1={"controls": [{"param": "nope", "values": [1]}]}))
    assert any("refused by the schema" in x for x in p(s1={"controls": [{"param": "h_m", "values": [0.0, 99.0]}]}))
    assert any("default" in x for x in p(s1={"controls": [{"param": "h_m", "values": [0.0], "default": 1.0}]}))
    assert any("distinct" in x for x in p(s1={"controls": [{"param": "h_m", "values": [1.0, 1.0]}]}))
    assert any("at most 5" in x for x in p(s1={"controls": ctl + [{"param": "v0", "values": [1.0]}] * 4}))
    big = [{"param": "h_m", "values": [round(0.1 * k, 1) for k in range(50)]},
           {"param": "v0", "values": [round(0.1 * k, 1) for k in range(1, 100)]}]
    assert any("grid points, at most 3000" in x for x in p(s1={"controls": big}))
    assert any("both a control and fixed" in x for x in p(s1={"fixed": {"h_m": 1.0}}))
    assert any("unit is a T or a string" in x for x in p(s1={"controls": [{**ctl[0], "unit": 3}]}))
    own = [{**ctl[0], "label": T("λ"), "unit": "nm"}, ctl[1]]
    assert p(s1={"controls": own}) == []
    sc = [dict(x) for x in toy["screens"]]
    sc[1] = {**sc[1], "controls": own}
    c0, c1 = registry.screens_of({**toy, "screens": sc})[1]["controls"]
    assert c0["label"]["$t"] == "λ" and c0["unit"] == "nm"  # the control's own label and unit win
    assert c1["label"]["$t"] == "Angle" and c1["unit"] == "°"  # else the parameter's
    lab = toy["screens"][2]
    st = dict(lab["steps"][0])
    assert any("goal" in x for x in p(s2={"steps": [{**st, "goal": None}]}))
    assert any("instruments" in x for x in p(s2={"steps": [{**st, "instruments": ["tape", "caliper"]}]}))
    assert any("from 'caliper'" in x for x in p(s2={"steps": [{**st, "columns": st["columns"] + [
        {"id": "z", "label": T("z"), "from": "caliper"}]}]}))
    assert any("earlier column" in x for x in p(s2={"steps": [{**st, "columns": [
        {"id": "r", "label": T("r"), "of": "L", "op": "sqrt"}] + st["columns"]}]}))
    assert any("op" in x for x in p(s2={"steps": [{**st, "columns": st["columns"] + [
        {"id": "z", "label": T("z"), "of": "h", "op": "cube"}]}]}))
    assert any("plot" in x for x in p(s2={"steps": [{**st, "plot": {"x": "h", "y": "nope"}}]}))
    assert any("power only above school" in x for x in p(s2={"steps": [{**st, "plot": {**st["plot"],
                                                                                       "fits": ["power"]}}]}))
    assert any("law" in x for x in p(s2={"steps": [{**st, "law": {"quantity": "mood"}}]}))
    assert any("reads" in x for x in p(s2={"instruments": {**lab["instruments"], "ruler": {
        **lab["instruments"]["ruler"], "reads": "control:nope"}}}))
    assert any("event is the kind or name" in x for x in p(s2={"instruments": {**lab["instruments"], "tape": {
        **lab["instruments"]["tape"], "event": 3}}}))
    ok = p(s2={"instruments": {**lab["instruments"], "tape": {**lab["instruments"]["tape"], "event": "landing"}}})
    assert ok == []
    sc = [dict(x) for x in toy["screens"]]
    sc[2] = {**sc[2], "instruments": {**lab["instruments"], "tape": {**lab["instruments"]["tape"], "event": "landing"}}}
    got = registry.screens_of({**toy, "screens": sc})[2]["instruments"]
    assert got["tape"]["event"] == "landing" and got["ruler"]["event"] is None  # passed through to the catalogue
    assert any("only a stopwatch is manual" in x for x in p(s2={"instruments": {**lab["instruments"], "ruler": {
        **lab["instruments"]["ruler"], "manual": True}}}))
    assert any("worksheet" in x for x in p(s2={"worksheet": {**lab["worksheet"], "questions": []}}))
    assert any("worksheet" in x for x in p(s2={"worksheet": {**lab["worksheet"], "frp": [{"name": "plain"}]}}))
    # school: Explore and Lab work required; Lab work may be absent only with lab_absent
    no_lab = [s for s in toy["screens"] if s["kind"] != "lab"]
    assert any("Lab work" in x for x in registry.check({**toy, "screens": no_lab}))
    assert registry.check({**toy, "screens": no_lab, "lab_absent": T("a test")}) == []
    assert any("Explore" in x for x in registry.check({**toy, "screens": [toy["screens"][0], toy["screens"][2]]}))
    lab_viz = _viz("p01_gravity")
    assert any("laboratory has no screens" in x for x in registry.check({**lab_viz, "screens": [toy["screens"][1]]}))


def test_a_steps_laws_name_their_columns_model_and_reference(toy):
    """Integrator D4 (review R-E F9, R-P F3, R-W F5): «Check against the law» judges a fit only when the plotted columns
    and the model are a law's own; a step may declare several laws; the old single ``law`` is refused."""
    lab = toy["screens"][2]
    st = dict(lab["steps"][0])
    law = dict(st["laws"][0])

    def p(**ch):
        return _screens_problems(toy, s2={"steps": [{**st, **ch}]})
    assert p() == []
    assert any("declares laws" in x for x in p(law=law))
    assert any("two columns" in x for x in p(laws=[{**law, "x": "nope"}]))
    assert any("two columns" in x for x in p(laws=[{**law, "y": "sqrt_h"}]))
    assert any("not among the plot's fits" in x for x in p(laws=[{**law, "model": "quadratic"}]))
    assert any("comes from the models" in x for x in p(laws=[{**law, "quantity": "vertex"}]))
    assert any("quantity" in x for x in p(laws=[{**law, "quantity": "mood"}]))
    assert any("unique in the step" in x for x in p(laws=[law, {**law, "model": "line"}]))
    assert any("unknown fields" in x for x in p(laws=[{**law, "tolerance": 2}]))
    assert any("label is a T" in x for x in p(laws=[{**law, "label": "plain"}]))
    assert any("unit is a T or a string" in x for x in p(laws=[{**law, "unit": 1}]))
    assert any("plot's own pair" in x for x in p(laws=[{**law, "x": "h"}]))
    assert p(laws=[{**law, "unit": T("m^½")}]) == []
    assert p(laws=[]) == [] and p(laws=None) == []  # no law: no check
    sim = toy["simulation"]

    class Old(sim):
        @classmethod
        def lab_reference(cls, step_id, fixed, values):  # the form before D4
            return {}
    assert any("lab_reference(step_id, fixed, values, reference)" in x
               for x in registry.check({**toy, "simulation": Old}))
    steps = registry.screens_of(toy)[2]["steps"]
    assert [x["reference"] for x in steps[0]["laws"]] == ["k_horizontal", "zero_intercept"] and "law" not in steps[0]
    assert next(a for a in registry.atlases_of(toy) if a["id"] == "lab.heights")["laws"] == \
        ["k_horizontal", "zero_intercept"]


def test_a_worksheets_programme_and_variants(toy):
    """A worksheet's ``frp`` entries name their programme (a T), and its ``variants`` (a grade's own sheet) name the
    lab's steps, their columns and fits (integrator, 2026-11-17)."""
    lab = toy["screens"][2]
    ws = dict(lab["worksheet"])
    var = dict(ws["variants"][0])

    def p(**ch):
        return _screens_problems(toy, s2={"worksheet": {**ws, **ch}})
    assert p() == []
    assert any("programme" in x for x in p(frp=[{k: v for k, v in ws["frp"][0].items() if k != "programme"}]))
    assert any("steps" in x for x in p(variants=[{**var, "steps": ["nope"]}]))
    assert any("not a step of the variant" in x for x in p(variants=[{**var, "plot": {"angles": {"x": "h", "y": "L"}}}]))
    assert any("two columns" in x for x in p(variants=[{**var, "plot": {"heights": {"x": "h", "y": "z", "fit": None}}}]))
    assert any("fit 'quadratic'" in x for x in p(variants=[{**var, "plot": {"heights": {"x": "h", "y": "L",
                                                                                        "fit": "quadratic"}}}]))
    assert p(variants=[{**var, "plot": {"heights": {"x": "h", "y": "L", "fit": "line"}}}]) == []
    assert any("grade" in x for x in p(variants=[{**var, "grade": "7"}]))
    assert any("label is a T" in x for x in p(variants=[{**var, "label": "plain"}]))
    assert any("unique slug" in x for x in p(variants=[var, var]))
    assert any("questions" in x for x in p(variants=[{**var, "questions": [{"q": "plain", "answer": T("a")}]}]))
    assert any("unknown fields" in x for x in p(variants=[{**var, "notes": []}]))
    assert p(variants=None) == []
    assert p(variants=[{**var, "goals": {"heights": T("a test")}}]) == []  # a step's goal for the variant's sheet
    assert any("not a step of the variant" in x for x in p(variants=[{**var, "goals": {"angles": T("a test")}}]))
    assert any("goal of heights is a T" in x for x in p(variants=[{**var, "goals": {"heights": "plain"}}]))
    assert any("goals is a map" in x for x in p(variants=[{**var, "goals": ["x"]}]))


def test_a_law_parameter_is_no_control_at_school_but_may_be_at_university():
    viz = _viz("u32_double_slit")
    law = next(p for p in viz["schema"].params if p.standard is not None)
    sc = {"id": "explore", "kind": "explore", "preset": next(iter(viz["schema"].presets)), "frame_dt": 0.25,
          "stop": {"world_s": 1.0}, "controls": [{"param": law.id, "values": [law.standard]}]}
    assert not [x for x in registry.check({**viz, "screens": [sc]}) if "law parameter" in x]
    probs = registry.check({**viz, "id": "s02_x", "audience": "school", "ui": "school", "screens": [sc]})
    assert any("law parameter" in x for x in probs)
    assert registry.screens_of({**viz, "screens": [sc]})[0]["controls"][0]["law"] is True


def test_every_screens_atlas_is_planned_and_every_screens_text_is_translated(toy):
    import importlib.util as _u  # noqa: PLC0415
    spec = _u.spec_from_file_location("lfsite_sitelib_reg", VIZ / "site" / "sitelib.py")
    L = _u.module_from_spec(spec)
    spec.loader.exec_module(L)
    plan = L.planned_world(TOY)
    assert [a["id"] for a in plan["atlases"]] == [a["id"] for a in registry.atlases_of(toy)]
    for lang in OTHER:
        own = i18n._merge(lang)[0]
        miss = sorted(m for m in _world_texts(TOY) if tools.needs_translation(m) and m not in own)
        assert not miss, f"{lang}: {miss}"
    for vid in IDS:  # a related world's screens: every repository world with screens names atlases that exist
        assert [a["id"] for a in registry.atlases_of(_viz(vid))] == \
            [a["id"] for a in L.planned_world(vid)["atlases"]]


@pytest.mark.parametrize("published", [False, True])
def test_the_readme_catalogue_lists_the_screens(toy, monkeypatch, published):
    readme = _site_module("readme")
    url = "https://ildar-idrisov.github.io/lfphys/"
    monkeypatch.setattr(readme, "site_setting", lambda env=True: {"published": published, "url": url})
    for lang in i18n.LANGS:
        row = readme.Gen(lang).row(TOY)
        labels = [i18n.render_in(T(x), lang) for x in ("Watch", "Explore", "Lab work")]
        assert all(lab in row for lab in labels), row
        q = "" if lang == i18n.DEFAULT else f"&lang={lang}"
        assert (f"({url}run.html?demo={TOY}&screen=explore{q})" in row) == published
