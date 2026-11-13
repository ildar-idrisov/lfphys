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
           "r13_arrival_times_2d": 8.8}
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
    school = {**good, "id": "s02_free_fall", "audience": "school", "ui": "school", "curriculum": [], "guide": None}
    probs = registry.check(school)
    assert any("FRP" in x for x in probs) and any("AP, IB" in x for x in probs) and any("guide" in x for x in probs)
    assert any("modified physics" in x for x in probs)  # u32's schema has laws: no school world may


@pytest.mark.parametrize("vid", [v for v in IDS if not v.startswith("p")])
def test_a_demonstration_has_recordings_within_the_budgets(vid):
    viz = _viz(vid)
    recs = registry.recordings_of(viz)
    assert 1 <= len(recs) <= 4
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
    ids = msgids({k: viz.get(k) for k in ("title", "summary", "purpose", "teaser", "question")})
    ids |= msgids([p.get("label") for p in viz["schema"].presets.values()])
    ids |= msgids([r["label"] for r in d["recordings"]])
    ids |= msgids(d.get("courses") or [])
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
