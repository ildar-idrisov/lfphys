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

Since review i18n-code (2026-11-13): a translation keeps each placeholder's format and every format is one the player
renders (F6); a msgid built at run time names its msgids in a marker (F6); the dynamic run covers every preset, each
action with its defaults and each palette type placed, and also reads plain strings under the user-facing keys (F6); no
JavaScript local hides ``t`` and no Python local hides ``T``, in any form (F8); the Cyrillic guard decodes escapes and
takes its marker from comments only (F8); no server code turns a text into a string by ``str()`` (F2); texts are
compared by msgid and arguments (F1, F2); the renderers agree at the edges (F10, F11); English plural forms reach the
API (F12); the catalogue is served compressed, by a weak ETag and from ``/static/locales`` (F9, F13).

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
            elif not all(tools.placeholder_specs(x) <= tools.placeholder_specs(k) for x in v.values()):
                bad.append((k, "a plural form formats a placeholder otherwise than the msgid"))
        elif not isinstance(v, str) or not v:
            bad.append((k, "not a text"))
        elif tools.placeholders(v) != tools.placeholders(k):
            bad.append((k, f"placeholders {sorted(tools.placeholders(v))} ≠ {sorted(tools.placeholders(k))}"))
        elif tools.placeholder_specs(v) != tools.placeholder_specs(k):  # {x:.2f} for {x:.3g}: another precision (F6)
            bad.append((k, f"formats {sorted(tools.placeholder_specs(v))} ≠ {sorted(tools.placeholder_specs(k))}"))
        for x in [k] + (list(v.values()) if isinstance(v, dict) else [v]):
            if isinstance(x, str) and tools.bad_specs(x):
                bad.append((k, f"formats the player does not render: {tools.bad_specs(x)}"))
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


def test_a_msgid_built_at_run_time_names_its_msgids():
    """``T("a" + b)``, ``t(`…${x}…`)``: the static test cannot see such msgids, so the line names them in a comment
    ``i18n-msgids: "…"`` (review i18n-code F6). A choice between literals (``t(c ? "a" : "b")``, ``T(MSG)``) is read."""
    pending = _pending()
    bad = []
    for f in tools.code_files():
        rel = _rel(f)
        if rel in pending or Path(rel).name.startswith(("test_", "conftest")):
            continue
        if f.suffix == ".py":
            try:
                bad += [f"{rel}:{ln}" for ln in tools.composed_py(f)]
            except SyntaxError:
                continue
        elif f.suffix in (".js", ".mjs") and not rel.endswith(".mjs"):
            bad += [f"{rel}:{ln}" for ln in tools.composed_js(f)]
    assert not bad, "msgids built at run time without a marker i18n-msgids: \"…\" (RULES.md «Languages and i18n»):\n" \
        + "\n".join(bad)


def test_every_msgid_has_formats_the_player_renders():
    """Every placeholder format of the code's msgids is one the player renders: nothing, .Ng, .Nf, .Ne, d (each with
    "+"), cap, unit (review i18n-code F6, F10: a width, "," or "%" is dropped or rendered otherwise in the browser)."""
    bad = [f"{rel}:{ln}: {m!r} {tools.bad_specs(m)}" for rel, ids in _static_msgids().items() for m, ln in ids
           if tools.bad_specs(m)]
    assert not bad, "\n".join(bad[:40])


# worlds that are heavy at their defaults: small geometries (as test_restore's)
SMALL = {
    "u38_wave_3d": {"n": 128, "zmax": 10.0},
    "r11_thomas_3d": {"ngrid": 48},
    "r12_double_slit_2d": {"a": 1.5, "d": 4.0, "w": 1.0, "L": 12.0, "sigma_x": 3.0, "sigma_z": 2.0, "grid": "coarse",
                           "n_bohm": 100, "n_tracks": 10},
    "r13_arrival_times_2d": {"grid": "coarse", "n_bohm": 100, "n_tracks": 10, "L": 12.0, "sigma_z": 2.0, "sigma_x": 2.0},
    "u44_mie_scattering": {"radius_um": 1.0, "width": 0.05, "n_lam": 8},
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


#: the keys under which a world or the framework sends a text the viewer reads (a plain string there is looked up by the
#: player's t() as a msgid, so it must be translated too: review i18n-code F6)
USER_KEYS = {"label", "unit", "help", "group", "title", "summary", "purpose", "note", "text", "hint", "statement",
             "validity", "kind_text", "reason", "button", "mode_label"}
NAME_KEYS = {"label", "title", "group", "help", "summary", "purpose", "button"}
PROSE = re.compile(r"[a-z]{3,}")  # a word of prose (not a symbol such as "x", "E_k", "LIGO", "Rb-87")


def _prose(key: str, x: str) -> bool:
    """A plain string the viewer reads as words: two words or more with one of prose, or one capitalised word as a label
    ("Width"); not an id ("strip", "step", "lam_nm"), a symbol or a name with its designation ("Sgr A* (EHT 2022)")."""
    x = x.strip()
    if "_" in x and " " not in x:
        return False
    words = re.sub(r"\S*_\S*", " ", x)  # symbols with an index (f_acd, C_A) are no words
    return (" " in x and bool(re.search(r"(?<!\w)[a-z]{3,}(?!\w)", words))) \
        or (key in NAME_KEYS and bool(re.fullmatch(r"[A-Z][a-z]{2,}", x)))  # "Width"; not "Sgr A* (EHT 2022)"


def plain_texts(x, out: set | None = None, key: str | None = None) -> set[str]:
    """Plain strings under the user-facing keys of a structure (outside texts: a T's arguments are its own)."""
    out = set() if out is None else out
    if is_t(x):
        return out
    if isinstance(x, dict):
        for k, v in x.items():
            plain_texts(v, out, k if isinstance(k, str) else None)
    elif isinstance(x, (list, tuple)):
        for v in x:
            plain_texts(v, out, key)
    elif isinstance(x, str) and key in USER_KEYS and _prose(key, x) and not re.match(r"^[\w./-]+\.\w+$", x):
        out.add(x)
    return out


def _texts_of_a_run(viz_id: str) -> set[str]:
    """The msgids a world sends (and the plain strings it sends under user-facing keys): its catalogue entry (schema,
    presets), its palette, and for every preset a world built and stepped; for the first preset also each action with
    its default arguments and each palette type placed (review i18n-code F6: the texts that appear only after an
    action or a scene operation)."""
    viz = registry.load(viz_id)
    desc = registry.describe(viz)
    ids = msgids(desc) | plain_texts(desc)
    ids |= msgids({k: viz.get(k) for k in ("title", "summary", "purpose")})
    sim_cls = viz["simulation"]
    for ot in (getattr(sim_cls, "PALETTE", None) or {}).values():
        ids |= msgids(ot.to_json()) | plain_texts(ot.to_json())
    presets = list(viz["schema"].presets) or [None]
    for i, preset in enumerate(presets):
        params, errors = viz["schema"].resolve(preset, SMALL.get(viz_id, {}))
        if errors:
            continue
        msgs = []

        def emit(meta, blobs=None):
            msgs.append(meta)
        sim = sim_cls(params, 3, emit)
        run = Runner(sim, emit, queue.Queue())
        run._start_world()
        for _ in range(3 if i < 2 else 1):
            run.handle({"cmd": "step", "args": {}})
        if i == 0:
            actions = [a for m in msgs if isinstance(m, dict) for a in (m.get("actions") or []) if isinstance(a, dict)]
            for a in {a.get("name"): a for a in actions if a.get("name")}.values():
                args = {x["id"]: x.get("default") for x in a.get("args") or [] if isinstance(x, dict) and "id" in x}
                run.handle({"cmd": "action", "args": {"name": a["name"], "args": args}})
            for typ in (getattr(sim, "PALETTE", None) or {}):
                run.handle({"cmd": "scene", "args": {"op": "add", "type": typ, "values": {}}})
            run.handle({"cmd": "step", "args": {}})
        for m in msgs:
            ids |= msgids(m) | plain_texts(m)
        for ot in (getattr(sim, "PALETTE", None) or {}).values():
            ids |= msgids(ot.to_json()) | plain_texts(ot.to_json())
    return ids


@pytest.mark.parametrize("viz_id", _all_viz())
def test_every_text_a_world_sends_is_translated(viz_id):
    """Dynamic: the schema, the presets, the palette and the messages of a short run of each world (its own texts, the
    framework's and the engine's)."""
    pend = _world_files_pending(viz_id)
    if pend:
        pytest.skip(f"{viz_id}: being converted ({len(pend)} files in i18n_pending.txt)")
    ids = _texts_of_a_run(viz_id)
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


# --- review i18n-code (2026-11-13): the guards themselves ---------------------------------------------------------------
def test_the_guards_catch_shadowing_escapes_and_markers_in_strings(tmp_path):
    """The forms the review built (evidence/c05_fixtures): a later name in a list, defaults with calls, a method, a
    function named t, a destructured loop variable; escaped Cyrillic; the marker inside a string (F8)."""
    js = tmp_path / "shadow.js"
    js.write_text('import { t, fmt } from "/static/js/i18n.js";\n'
                  'export function a1(meta) { let x, t; t = meta.t; return t("Run"); }\n'
                  'export function a2(meta, cb = make(), t) { return t("Run"); }\n'
                  'export function t2() {}\n'
                  'function t() { return 0; }\n'
                  'export const a4 = { draw(meta, opts = f(1), t) { return t("Run"); } };\n'
                  'export function a5(rows) { for (const { t } of rows) return t("Run"); }\n'
                  'export function ok(meta, tt = t("Run")) { const tNow = 1; return tNow; }\n', encoding="utf-8")
    assert tools.shadowed_t(js) == [2, 3, 5, 6, 7]
    cyr = tmp_path / "cyr.js"
    cyr.write_text('export const A = "\\u0428\\u0438";\nexport const B = "Ш i18n-ok";\n'  # i18n-ok: fixtures of the guard
                   'export const C = "Ш";  // i18n-ok: a marker in a comment\n', encoding="utf-8")  # i18n-ok
    assert tools.cyrillic_lines(cyr) == [1, 2]
    py = tmp_path / "cyr.py"
    py.write_text('A = "\\u0428"\nB = "\\N{CYRILLIC CAPITAL LETTER SHA}"\nC = "Ш i18n-ok"\nD = "Ш"  # i18n-ok\n',  # i18n-ok
                  encoding="utf-8")
    assert tools.cyrillic_lines(py) == [1, 2, 3]
    ids = tmp_path / "ids.py"
    ids.write_text('from lfphys.i18n import T\nMSG = "A constant"\na = T(MSG)\nb = T("x " + y)\n'
                   'c = T("Open" if k else "Closed")\nd = T("{n} " + u)  # i18n-msgids: "{n} B" "{n} KB"\n',
                   encoding="utf-8")
    assert sorted(m for m, _ in tools.msgids_py(ids)) == ["A constant", "Closed", "Open", "{n} B", "{n} KB"]
    assert tools.composed_py(ids) == [4]
    tj = tmp_path / "ids.js"
    tj.write_text('import { t } from "./i18n.js";\nconst a = t(c ? "One" : "Two");\nconst b = t(`x ${y}`);\n'
                  'const d = t(`x ${y}`);  // i18n-msgids: "x a"\nconst e = t(v.label);\n', encoding="utf-8")
    assert sorted(m for m, _ in tools.msgids_js(tj)) == ["One", "Two", "x a"] and tools.composed_js(tj) == [3]
    sh = tmp_path / "sh.py"
    sh.write_text("from lfphys.i18n import T\n"
                  "def a(T):\n    return 1\n"
                  "def b():\n    try:\n        pass\n    except ValueError as T:\n        pass\n"
                  "def c():\n    def T():\n        pass\n"
                  "def d():\n    import numpy as T\n"
                  "def e():\n    return T('ok')\n", encoding="utf-8")
    assert tools.shadowed_T(sh) == [2, 4, 9, 12]


def test_no_function_of_the_visualizations_makes_T_a_local():
    """A function in a module that imports ``T`` never binds ``T`` itself (a parameter, an assignment, ``except … as
    T``, ``def T``, ``import … as T``): a later ``T("…")`` there would fail (review i18n-code F8; the engine's own test
    covers lfphys)."""
    bad = []
    for f in tools.code_files():
        rel = _rel(f)
        if f.suffix != ".py" or rel.startswith("lfphys/") or Path(rel).name.startswith(("test_", "conftest")):
            continue
        try:
            bad += [f"{rel}:{ln}" for ln in tools.shadowed_T(f)]
        except SyntaxError:
            continue
    assert not bad, "rename these locals (e.g. T_K, temp):\n" + "\n".join(bad)


def test_the_server_never_turns_a_text_into_a_string_by_str():
    """``str()`` of a text read back from JSON is a dict's repr, and of a live one its English rendering: the server
    compares texts by msgid and arguments (``mentions``, ``names_unit``) and renders them by ``render_in`` (review
    i18n-code F2). A ``str()`` of a name holding a label, a unit, a text, a note, a title or a hint is allowed only on a
    line that checks ``is_t`` first, or with the marker ``i18n-str-ok``."""
    import ast  # noqa: PLC0415
    rx = re.compile(r"label|unit|text|note|title|help|hint", re.I)
    bad = []
    for f in sorted((VIZ / "server" / "lfviz").glob("*.py")):
        src = f.read_text(encoding="utf-8")
        lines = src.splitlines()
        for n in ast.walk(ast.parse(src)):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "str" and len(n.args) == 1:
                seg = ast.get_source_segment(src, n.args[0]) or ""
                line = lines[n.lineno - 1]
                if rx.search(seg) and "is_t(" not in line and "i18n-str-ok" not in line:
                    bad.append(f"{_rel(f)}:{n.lineno}: str({seg})")
    assert not bad, "\n".join(bad)


def test_texts_are_compared_by_msgid_and_arguments_also_after_json():
    """Review i18n-code F1, F2: a probe's quantity that names its object gets no second prefix, and a label that names
    its unit gets no second unit — for live texts and for texts read back from JSON (a record, a sweep's spec)."""
    import types  # noqa: PLC0415
    from lfviz.i18n import json_hook, mentions, names_unit, revive, same_text  # noqa: PLC0415
    from lfviz.instruments import column_title, display_label  # noqa: PLC0415
    from lfviz.sweep import with_unit  # noqa: PLC0415
    probe = T("Probe {n:d}", n=1)
    lab = T("“{label}”: to the nearest particle", label=probe)
    rt = lambda x: json.loads(json.dumps(x))  # noqa: E731 - plain dicts, as json.loads without a hook gives
    for ol, d in ((probe, {"id": "near.o1", "label": lab, "unit": T("m"), "of": "o1"}),
                  (rt(probe), rt({"id": "near.o1", "label": lab, "unit": T("m"), "of": "o1"}))):
        w = types.SimpleNamespace(objects={"o1": {"label": ol}})
        assert same_text(display_label(w, d), lab), display_label(w, d)
        head = i18n.render_in(column_title(w, d), "en")
        assert head == "“Probe 1”: to the nearest particle, m [near.o1]" and head.count("Probe 1") == 1
    w = types.SimpleNamespace(objects={"o1": {"label": probe}})
    assert str(display_label(w, {"id": "x", "label": T("distance"), "of": "o1"})) == "Probe 1: distance"
    for label, unit in ((T("Hold memory, MB"), T("MB")), (rt(T("Hold memory, MB")), rt(T("MB"))),
                        (T("{label} ({stat})", label=T("Hold memory, MB"), stat=T("at the end")), T("MB")),
                        ("Window size, nm", "nm"), (T("Length, {u}", u=T("nm")), T("nm"))):
        assert names_unit(label, unit) and same_text(with_unit(label, unit), label), (label, unit)
    assert str(with_unit(T("Hold memory"), T("MB"))) == "Hold memory, MB"
    assert not names_unit(T("Mass of the star"), T("s"))  # a one-letter unit is a word, not a letter of a word (F14)
    x = json.loads(json.dumps({"a": [T("Slit {w:.3g}", w=0.5)]}), object_hook=json_hook)
    assert isinstance(x["a"][0], T) and str(x["a"][0]) == "Slit 0.5"
    assert isinstance(revive(rt(lab))["a"]["label"], T) and mentions(rt(lab), probe)


def test_the_renderers_agree_at_the_edges():
    """Review i18n-code F10, F11 (the player's side: player/js/tests/i18n.test.mjs): a bool, a float with {n:d}, a plural
    without n or with n not finite, the plural form of the number as shown, a server file's Russian numbers."""
    cat = {"{n:d} days": {"one": "{n:d} день", "few": "{n:d} дня", "many": "{n:d} дней", "other": "{n:d} дня"}}  # i18n-ok
    assert str(T("{b} {x:d}", b=True, x=2.6)) == "true 3"
    assert [render(T("{n:d} days", n=n), cat, "ru") for n in (4.6, 21.4, 1)] == ["5 дней", "21 день", "1 день"]  # i18n-ok
    assert render(T("{n:d} days", n=float("nan")), cat, "ru").endswith("дня")  # i18n-ok: no crash on NaN
    assert render(T("{n:d} days", n=float("inf")), cat, "ru").endswith("дня")  # i18n-ok
    assert render(T("{n:d} days"), cat, "ru") == "{n:d} дня"  # i18n-ok: no n: "other", as the player
    en = {"{n:.3g} years": {"one": "{n:.3g} year", "other": "{n:.3g} years"}}
    assert render(T("{n:.3g} years", n=1.0004), en, "en") == "1 year"
    assert render(T("{n:.2f} years", n=1.0), en, "en") == "1.00 years"
    assert render(T("{x:.3g} and {n}", x=-1.5e4, n=12345678), {}, "ru", numbers=True) == "−15\u202f000 and 12\u202f345\u202f678"
    assert render(T("{x:.2e}", x=1.2345e-5), {}, "ru", numbers=True) == "1,23·10⁻⁵"
    assert render(T("{x:.2f}", x=0.5), {}, "ru", numbers=True) == "0,50"


def test_errors_for_api_clients_use_the_english_plural_forms():
    """``error_body``'s English ``text`` goes through ``en.json`` (review i18n-code F12)."""
    b = i18n.error_body(T("At most {n:d} plots at once", n=1))
    assert b["text"] == "At most 1 plot at once"


def test_a_plain_english_refusal_is_not_shown_in_english():
    """A plain (untranslated) English ValueError that no world put into the owner's terms: a translated head, the
    sentence under "details" (review i18n-code F4, framework side); a known library sentence keeps its own text."""
    from lfviz.errors import owner_text  # noqa: PLC0415
    text, detail = owner_text(ValueError("total reflection at the second interface"), "set")
    assert "in English" in str(text) and "total reflection" not in str(text) and "total reflection" in detail
    text, _ = owner_text(ValueError("Probabilities contain NaN"), "set")
    assert "not-a-number" in str(text)
    old = "ширина щели больше пластины"  # i18n-ok: a record's text from before the translation
    assert str(owner_text(ValueError(old), "set")[0]).endswith(old)


def test_a_unit_taken_from_a_label_survives_the_translation():
    """``{label:unit}`` takes what follows a label's last comma, in the viewer's language (lfviz.playground.unit_of):
    for every palette parameter it reaches (no explicit unit, a comma in the msgid), the translation keeps a unit after
    its last comma too (review i18n-code F15)."""
    from lfphys.i18n import _UNIT  # noqa: PLC0415
    bad = []
    for viz_id in _all_viz():
        viz = registry.load(viz_id)
        if viz.get("kind") != "playground":
            continue
        sim_cls = viz["simulation"]
        types_ = dict(getattr(sim_cls, "PALETTE", None) or {})
        if not types_:
            params, errors = viz["schema"].resolve(None, SMALL.get(viz_id, {}))
            if errors:
                continue
            sim = sim_cls(params, 3, lambda m, b=None: None)
            types_ = dict(getattr(sim, "PALETTE", None) or {})
        for ot in types_.values():
            for p in ot.schema.params:
                lab = p.label
                if getattr(p, "unit", "") or not is_t(lab) or not _UNIT.search(lab["$t"]):
                    continue
                for lang in OTHER:
                    tr = i18n.catalogue(lang).get(lab["$t"])
                    if isinstance(tr, str) and not _UNIT.search(tr):
                        bad.append(f"{viz_id}: {lab['$t']!r} → {lang} {tr!r}")
    assert not bad, "a translation that drops the comma before the unit (unit_of reads it):\n" + "\n".join(bad)


def test_the_catalogue_is_compressed_cached_and_served_where_a_static_copy_has_it(tmp_path):
    """Review i18n-code F9, F13: gzip; a weak or listed If-None-Match; "RU" and "ru-RU"; the same body at
    /static/locales/<lang>.json, where the player loads it (a static copy has the exported file there)."""
    from aiohttp.test_utils import TestClient, TestServer  # noqa: PLC0415
    from lfviz.app import create_app  # noqa: PLC0415

    async def go():
        app = create_app(tmp_path / "runs", max_workers=1)
        async with TestClient(TestServer(app)) as c:
            r = await c.get("/api/i18n/ru", headers={"Accept-Encoding": "gzip"})
            assert r.status == 200 and r.headers.get("Content-Encoding") == "gzip"
            j = await r.json()
            et = r.headers["ETag"]
            for inm in (et, "W/" + et, f'"x", {et}', "*"):
                r2 = await c.get("/api/i18n/ru", headers={"If-None-Match": inm, "Accept-Encoding": "gzip"})
                assert r2.status == 304, inm
            r3 = await c.get("/api/i18n/ru", headers={"Accept-Encoding": "identity"})
            assert r3.status == 200 and "Content-Encoding" not in r3.headers and (await r3.json()) == j
            for code in ("RU", "ru-RU"):
                r4 = await c.get(f"/api/i18n/{code}")
                assert r4.status == 200 and (await r4.json())["lang"] == "ru"
            r5 = await c.get("/static/locales/ru.json")
            assert r5.status == 200 and (await r5.json()) == j
            r6 = await c.get("/static/js/i18n.js")
            assert r6.status == 200  # the static files are still served
    asyncio.run(go())
    files = i18n.export(tmp_path / "locales")
    assert sorted(f.name for f in files) == ["en.json", "en.json.gz", "ru.json", "ru.json.gz"]
    import gzip  # noqa: PLC0415
    body, _ = i18n.payload("ru")
    assert (tmp_path / "locales" / "ru.json").read_bytes() == body
    assert gzip.decompress((tmp_path / "locales" / "ru.json.gz").read_bytes()) == body


def test_the_engines_english_catalogue_is_merged_and_exported(tmp_path):
    """The engine's ``en.json`` (its English plural forms, PR-B 2026-11-13) is part of the English catalogue the server
    serves and exports, and fills English in the other languages' catalogues where they have no entry."""
    f = REPO / "lfphys" / "lfphys" / "locales" / "en.json"
    if not f.is_file():
        pytest.skip("the engine has no en.json")
    own = json.loads(f.read_text(encoding="utf-8"))
    assert f in i18n.catalogue_files("en")
    en = i18n.catalogue("en")
    assert all(en.get(k) == v for k, v in own.items() if k not in i18n._merge("en")[0] or i18n._merge("en")[0][k] == v)
    i18n.export(tmp_path)
    exported = json.loads((tmp_path / "en.json").read_text(encoding="utf-8"))["messages"]
    assert all(k in exported for k in own)


def test_the_map_of_old_records_is_there_and_frozen():
    """Records made before the translation are read through ``player/legacy/ru-2026-11-12.json`` (Russian string of
    that time → msgid; review i18n-browser F3): it holds the labels such records carry."""
    m = json.loads((VIZ / "player" / "legacy" / "ru-2026-11-12.json").read_text(encoding="utf-8"))["messages"]
    assert m["Плейграунд: частицы и молекулы"] == "Playground: particles and molecules"  # i18n-ok: an old record's scene
    assert m["Запуски"] == "Runs"  # i18n-ok
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in m.items())


def test_an_engine_refusal_is_recognised_by_its_code():
    """The framework's own wording of an engine refusal is chosen by the engine's machine code, not by its English text
    (lfphys.codes; the "worldline is not timelike" sentence became a coded text)."""
    from lfphys.codes import coded  # noqa: PLC0415
    from lfviz.errors import owner_text  # noqa: PLC0415
    e = coded(RuntimeError("some other wording"), "gr.not_timelike")
    text, _ = owner_text(e, "advance", t=1.0)
    assert "worldline is not timelike" in str(text)
    text, _ = owner_text(coded(ValueError("reworded"), "gr.not_timelike"), "set")
    assert "worldline is not timelike" in str(text)
