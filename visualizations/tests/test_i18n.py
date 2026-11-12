# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The interface's languages (owner, 2026-11-12: «для всего фронта сделай i18n переводы на русский и английский, по
дефолту английский и переключением языка»; AGENTS.md §3 rule 13, LANGUAGES.md, RULES.md «Languages and i18n»).

* the catalogues: valid, merged without conflicts, every translation with the msgid's placeholders;
* completeness, static: every msgid the code uses (``T("...")`` in Python, ``t("...")`` in JavaScript, ``data-t`` in
  the HTML pages) is translated into every language other than English;
* completeness, dynamic: what every world sends — its schema and presets (the catalogue's form), a playground's
  palette, and the messages of a short run (header, events, checks, notices, the engine's ABOUT texts) — is translated;
* the Cyrillic guard: no Cyrillic in code lines outside comments and docstrings, except the files listed in
  ``tests/i18n_pending.txt`` (being converted; each agent removes its own; empty at the end);
* the texts themselves: ``T`` survives JSON, ``dataclasses.asdict`` and pickling; the server's rendering (nested texts,
  plural forms, the placeholder formats); the endpoint ``GET /api/i18n/<lang>``.

A file listed in ``i18n_pending.txt`` is skipped by the completeness tests too (it is not converted yet)."""

from __future__ import annotations

import asyncio
import dataclasses
import json
import pickle
import queue
import re
import warnings
from pathlib import Path

import pytest

from lfviz import i18n, registry
from lfviz.i18n import T, english, is_t, join, msgids, render, text_of
from lfviz.params import Param, Schema
from lfviz.sim import Runner

import i18n_tools as tools

VIZ = registry.ROOT
REPO = VIZ.parent
OTHER = [code for code in i18n.LANGS if code != i18n.DEFAULT]
EXTRA = [VIZ / "tests" / "playgrounds", VIZ / "tests" / "instruments_worlds"]
PLURAL_FORMS = {"zero", "one", "two", "few", "many", "other"}


@pytest.fixture(autouse=True)
def _extra(monkeypatch):
    monkeypatch.setenv("LFVIZ_EXTRA", ":".join(str(p) for p in EXTRA))


def _pending() -> set[str]:
    return tools.read_pending()


def _rel(p: Path) -> str:
    return Path(p).resolve().relative_to(REPO).as_posix()


# --- the catalogues --------------------------------------------------------------------------------------------------
def _catalogue_files():
    out = []
    for root in (REPO / "lfphys" / "lfphys", VIZ):
        out += [f for f in root.rglob("locales/*.json") if "node_modules" not in f.parts]
    return sorted(out)


@pytest.mark.parametrize("path", _catalogue_files(), ids=lambda p: _rel(p))
def test_a_catalogue_is_a_flat_object_of_translations(path):
    d = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(d, dict), path
    assert path.stem in i18n.LANGS, f"{_rel(path)}: a catalogue of a language not in LANGUAGES.md"
    bad = []
    for k, v in d.items():
        if isinstance(v, dict):
            if not v or set(v) - PLURAL_FORMS or "other" not in v or not all(isinstance(x, str) for x in v.values()):
                bad.append((k, "plural forms: an object of CLDR categories with 'other'"))
            elif not all(tools.placeholders(x) <= tools.placeholders(k) for x in v.values()):
                bad.append((k, "a plural form has a placeholder the msgid has not"))
        elif not isinstance(v, str) or not v:
            bad.append((k, "not a text"))
        elif tools.placeholders(v) != tools.placeholders(k):
            bad.append((k, f"placeholders {sorted(tools.placeholders(v))} ≠ {sorted(tools.placeholders(k))}"))
    assert not bad, bad[:20]
    assert list(d) == sorted(d), f"{_rel(path)}: keys not sorted"


@pytest.mark.parametrize("lang", OTHER)
def test_no_msgid_is_translated_differently_in_two_catalogues(lang):
    clashes = i18n.conflicts(lang)
    assert not clashes, [(c["msgid"], c["values"], [Path(f).relative_to(REPO).as_posix() for f in c["files"]])
                         for c in clashes[:20]]


def test_the_languages_are_those_of_languages_md_and_of_the_player():
    rows = re.findall(r"^\|\s*`(\w+)`\s*\|", (REPO / "LANGUAGES.md").read_text(encoding="utf-8"), re.M)
    assert tuple(rows) == i18n.LANGS
    js = (VIZ / "player" / "js" / "i18n.js").read_text(encoding="utf-8")
    assert re.findall(r'\["(\w+)", "[A-Z]+", ', js) == list(i18n.LANGS)


# --- completeness ----------------------------------------------------------------------------------------------------
def _missing(ids, lang) -> list[str]:
    own = i18n._merge(lang)[0]  # the language's own entries (English's fill-ins are not a translation)
    return sorted({m for m in ids if tools.needs_translation(m) and m not in own})


def _static_msgids():
    """{file: [(msgid, line)]} of every code file not pending."""
    pending = _pending()
    out = {}
    for f in tools.code_files():
        rel = _rel(f)
        if rel in pending or Path(rel).name.startswith(("test_", "conftest")) or rel.endswith(".mjs"):
            continue  # the tests' own fixtures are no texts of the product
        if f.suffix == ".py":
            try:
                ids = tools.msgids_py(f)
            except SyntaxError:
                continue
        elif f.suffix in (".js", ".mjs"):
            ids = tools.msgids_js(f)
        else:
            ids = tools.msgids_html(f)
        if ids:
            out[rel] = ids
    return out


@pytest.mark.parametrize("lang", OTHER)
def test_every_msgid_of_the_code_is_translated(lang):
    """Static: T("...") in Python, t("...") in JavaScript, data-t / data-t-title in HTML — of the converted files."""
    report = []
    for rel, ids in _static_msgids().items():
        miss = _missing([m for m, _ in ids], lang)
        if miss:
            lines = {m: ln for m, ln in ids}
            report += [f"{rel}:{lines[m]}: {m!r}" for m in miss]
    assert not report, f"{len(report)} msgids without a {lang} translation:\n" + "\n".join(report[:60])


# worlds that are heavy at their defaults: small geometries (as test_restore's)
SMALL = {
    "v08_wave_3d": {"n": 128, "zmax": 10.0},
    "v09_thomas_3d": {"ngrid": 48},
    "v11_double_slit_2d": {"a": 1.5, "d": 4.0, "w": 1.0, "L": 12.0, "sigma_x": 3.0, "sigma_z": 2.0, "grid": "coarse",
                           "n_bohm": 100, "n_tracks": 10},
    "v12_arrival_times_2d": {"grid": "coarse", "n_bohm": 100, "n_tracks": 10, "L": 12.0, "sigma_z": 2.0, "sigma_x": 2.0},
    "v17_mie_scattering": {"radius_um": 1.0, "width": 0.05, "n_lam": 8},
}


def _world_files_pending(viz_id: str) -> list[str]:
    try:
        folder = registry.folder(viz_id)
    except KeyError:
        return []
    pending = _pending()
    return [p for p in pending if (REPO / p).resolve().is_relative_to(folder.resolve())]


def _all_viz():
    import os  # noqa: PLC0415 - the parametrisation runs before the fixture sets LFVIZ_EXTRA
    old = os.environ.get("LFVIZ_EXTRA")
    os.environ["LFVIZ_EXTRA"] = ":".join(str(p) for p in EXTRA)
    try:
        return registry.viz_ids()
    finally:
        if old is None:
            os.environ.pop("LFVIZ_EXTRA", None)
        else:
            os.environ["LFVIZ_EXTRA"] = old


def _texts_of_a_short_run(viz_id: str) -> set[str]:
    """The msgids a world sends: its catalogue entry (schema, presets), its palette, and a short run (the header with
    the engine's modules, what it emits building itself, a few steps)."""
    viz = registry.load(viz_id)
    ids = msgids(registry.describe(viz))
    ids |= msgids({k: viz.get(k) for k in ("title", "summary", "purpose")})
    sim_cls = viz["simulation"]
    for ot in (getattr(sim_cls, "PALETTE", None) or {}).values():
        ids |= msgids(ot.to_json())
    presets = list(viz["schema"].presets) or [None]
    for preset in presets[:2]:  # the first scenarios: a playground's first is its richest scene
        params, errors = viz["schema"].resolve(preset, SMALL.get(viz_id, {}))
        if errors:
            continue
        msgs = []

        def emit(meta, blobs=None):
            msgs.append(meta)
        sim = sim_cls(params, 3, emit)
        run = Runner(sim, emit, queue.Queue())
        run._start_world()
        for _ in range(3):
            run.handle({"cmd": "step", "args": {}})
        for m in msgs:
            ids |= msgids(m)
        for ot in (getattr(sim, "PALETTE", None) or {}).values():
            ids |= msgids(ot.to_json())
    return ids


@pytest.mark.parametrize("viz_id", _all_viz())
def test_every_text_a_world_sends_is_translated(viz_id):
    """Dynamic: the schema, the presets, the palette and the messages of a short run of each world (its own texts, the
    framework's and the engine's)."""
    pend = _world_files_pending(viz_id)
    if pend:
        pytest.skip(f"{viz_id}: being converted ({len(pend)} files in i18n_pending.txt)")
    ids = _texts_of_a_short_run(viz_id)
    for lang in OTHER:
        miss = _missing(ids, lang)
        assert not miss, f"{viz_id}: {len(miss)} texts without a {lang} translation: {miss[:40]}"


def test_unused_catalogue_entries_are_reported():
    """The framework catalogue's entries no code uses statically (reported, not failed: a world's texts and the
    dynamic ones are found by the other tests)."""
    used = {m for ids in _static_msgids().values() for m, _ in ids}
    for lang in OTHER:
        f = VIZ / "locales" / f"{lang}.json"
        if not f.is_file():
            continue
        unused = sorted(set(json.loads(f.read_text(encoding="utf-8"))) - used)
        if unused:
            warnings.warn(f"{_rel(f)}: {len(unused)} entries not used statically, e.g. {unused[:8]}", stacklevel=1)


# --- the Cyrillic guard ------------------------------------------------------------------------------------------------
def test_no_cyrillic_in_code_lines_outside_the_pending_files():
    pending = _pending()
    report = []
    for f in tools.code_files():
        rel = _rel(f)
        if rel in pending:
            continue
        lines = tools.cyrillic_lines(f)
        if lines:
            src = f.read_text(encoding="utf-8").splitlines()
            report += [f"{rel}:{n}: {src[n - 1].strip()[:100]}" for n in lines[:5]]
    assert not report, ("Cyrillic in code lines (a user-facing text is an English msgid with its translation in the "
                        "catalogues; RULES.md «Languages and i18n»):\n" + "\n".join(report[:80]))


def test_the_pending_list_names_only_files_still_to_convert():
    """Every file in i18n_pending.txt exists and still has Cyrillic in its code lines: a converted file is taken off."""
    stale = []
    for rel in sorted(_pending()):
        f = REPO / rel
        if not f.is_file():
            stale.append(f"{rel}: no such file")
        elif not tools.cyrillic_lines(f):
            stale.append(f"{rel}: converted — remove it from tests/i18n_pending.txt")
    assert not stale, stale


# --- the texts ---------------------------------------------------------------------------------------------------------
def test_a_text_is_json_and_survives_copies_and_pickling():
    x = T("Slit width {w:.3g} µm, {what}", w=0.5, what=T("open"))
    assert json.loads(json.dumps(x)) == {"$t": "Slit width {w:.3g} µm, {what}", "a": {"w": 0.5, "what": {"$t": "open"}}}
    p = Param("w", T("Width"), "float", 1.0, unit=T("µm"), help=T("Help"), group=T("Group"),
              options=[(1, T("one"))])
    d = p.to_json()
    assert d["label"] == {"$t": "Width"} and d["options"][0]["label"] == {"$t": "one"}
    assert isinstance(dataclasses.asdict(p)["label"], T)
    y = pickle.loads(pickle.dumps(x))
    assert isinstance(y, T) and y == x and str(y) == "Slit width 0.5 µm, open"
    assert T(json.loads(json.dumps(x))) == x


def test_the_server_renders_english_and_a_catalogue():
    cat = {"open": "открыта", "Slit {what}": "Щель {what}"}  # i18n-ok: a catalogue under test
    cat["{n:d} slits"] = {"one": "{n:d} щель", "few": "{n:d} щели", "many": "{n:d} щелей", "other": "{n:d} щели"}  # i18n-ok
    assert render(T("Slit {what}", what=T("open")), cat) == "Щель открыта"  # i18n-ok: nested texts in the catalogue's
    ru = [render(T("{n:d} slits", n=n), cat, "ru") for n in (1, 3, 5, 21)]
    assert ru == ["1 щель", "3 щели", "5 щелей", "21 щель"]  # i18n-ok: the Russian plural rules
    assert str(T("{x:+.2f} and {y:.2e}", x=1.5, y=12345.0)) == "+1.50 and 1.23e+04"
    assert str(T("{text}. What to change: {hint}", text=T("Too wide."), hint="x")) == "Too wide. What to change: x"
    assert str(T("{b:cap}", b=T("out of memory"))) == "Out of memory"
    assert str(T("{label:unit}", label=T("Mass, M☉"))) == "M☉"
    assert str(join([T("a"), "b", T("c")], "; ")) == "a; b; c"
    assert english({"x": [T("a {n}", n=2)]}) == {"x": ["a 2"]}
    assert text_of(ValueError(T("no"))) == {"$t": "no"} and text_of(ValueError("plain")) == "plain"
    assert msgids({"k": [T("a {b}", b=T("c"))]}) == {"a {b}", "c"}


def test_a_refusal_carries_its_text_and_hint_as_one_text():
    from lfviz.errors import Refusal, owner_text  # noqa: PLC0415
    e = Refusal(T("The slit is wider than the plate."), hint=T("narrow it"))
    assert is_t(e.owner) and e.owner["$t"] == "{text}. What to change: {hint}"
    assert str(e) == "The slit is wider than the plate. What to change: narrow it"
    text, _ = owner_text(e, "set")
    assert text["$t"] == "{head}: {body}" and text["a"]["head"] == {"$t": "Change not applied"}
    text, detail = owner_text(ZeroDivisionError("float division by zero"), "action", label=T("Flash"))
    assert "internal error of the world" in str(text) and detail.startswith("ZeroDivisionError")
    assert text["a"]["head"]["a"]["label"] == {"$t": "Flash"}


def test_parameter_refusals_are_texts_with_their_field():
    sch = Schema([Param("w", T("Width"), "float", 1.0, unit=T("µm"), min=0.1, max=5.0)])
    _, errors = sch.resolve(None, {"w": 9})
    (e,) = errors
    assert e.pid == "w" and is_t(e) and e["$t"].startswith("{name}: {x:.10g} is above the maximum")
    assert str(e) == "“Width, µm”: 9 is above the maximum 5; allowed: from 0.1 to 5"
    # a label that names its unit already, as a text and the unit a plain string, or the reverse: the unit once
    for lab, unit in ((T("Width, µm"), "µm"), ("Width, µm", T("µm")), (T("Width, µm"), T("µm"))):
        (e,) = Schema([Param("w", lab, "float", 1.0, unit=unit, max=5.0)]).resolve(None, {"w": 9})[1]
        assert str(e).startswith("“Width, µm”: 9"), (lab, unit, str(e))


# --- the endpoint ------------------------------------------------------------------------------------------------------
def test_the_catalogue_is_served_per_language_with_an_etag(tmp_path):
    from aiohttp.test_utils import TestClient, TestServer  # noqa: PLC0415
    from lfviz.app import create_app  # noqa: PLC0415

    async def go():
        app = create_app(tmp_path / "runs", max_workers=1)
        async with TestClient(TestServer(app)) as c:
            r = await c.get("/api/i18n/ru")
            assert r.status == 200
            j = await r.json()
            assert j["lang"] == "ru" and j["messages"]["Run"] == "Запуск"  # i18n-ok: a translation under test
            et = r.headers["ETag"]
            r2 = await c.get("/api/i18n/ru", headers={"If-None-Match": et})
            assert r2.status == 304
            r3 = await c.get("/api/i18n/en")
            assert r3.status == 200 and "messages" in await r3.json()
            r4 = await c.get("/api/i18n/xx")
            j4 = await r4.json()
            assert r4.status == 404 and j4["error"]["$t"].startswith("No interface language") and "xx" in j4["text"]
            r5 = await c.get("/api/runs/nope")
            j5 = await r5.json()
            assert r5.status == 404 and j5 == {"error": {"$t": "there is no such run"}, "text": "there is no such run"}
    asyncio.run(go())


def test_no_local_hides_the_translator():
    """A JavaScript module that imports ``t`` from i18n.js names no parameter or local ``t`` (inside such a scope a call
    t("…") would call a number: found in orbitview.js's drawPhase(meta, t), 2026-11-12). Pending files are skipped."""
    pending = _pending()
    bad = []
    for f in tools.code_files():
        if f.suffix in (".js", ".mjs") and _rel(f) not in pending:
            bad += [f"{_rel(f)}:{ln}" for ln in tools.shadowed_t(f)]
    assert not bad, "rename these parameters or locals (e.g. tt, tNow):\n" + "\n".join(bad)
