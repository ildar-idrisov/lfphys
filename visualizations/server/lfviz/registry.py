# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Discovery of visualization folders, their audiences and the old ids.

A visualization is a folder ``visualizations/<a>NN_<slug>/`` whose prefix names its audience (``AGENTS.md`` §3 rule
14; owner, 2026-11-12: «Префиксы s/u/r/p»): ``s`` school, ``u`` university, ``r`` research, ``p`` laboratories (the
free benches of plan P15; internally "playground", ``VIZ["kind"] == "playground"``). The number is the item's id in
the plan of the audiences (owner, 2026-11-13: «Номер = id в плане»; ``lfphys/sources/audiences_2026-11-12_plan.md``):
``u32_double_slit`` is U32. The folder is a Python package with ``viz.py`` defining ``VIZ`` and a browser module
``web/view.js``; the folder name is the id. Contract and rules: ``visualizations/RULES.md``.

``VIZ`` (a dict; texts are ``T``):

* always: ``id``, ``title``, ``summary``, ``purpose``, ``version``, ``schema``, ``simulation``;
* ``audience`` (``AUDIENCES``; it must agree with the prefix), ``section`` (``SECTIONS``, the teaching order of plan
  §5.1), ``ui`` (``school`` | ``standard`` | ``full``; default by the audience, ``school`` if and only if the audience is
  school), ``teaser`` (one line: what you will see), ``related`` (the same topic at other levels: world ids or the ids
  of planned items, ``planned.json``);
* per audience: school ``curriculum`` (a ФРП anchor and an AP/IB/AQA anchor) and ``guide``; university ``courses``
  (``[{"text": T, "chapters": str}]``); research ``question`` (T), ``prior_art`` (``[{"ref", "url"}]``) and ``status``
  (``"hypothesis"`` until reproduced: ``AGENTS.md`` rule 11);
* ``recordings`` (not for the laboratories, at least one): what the public site plays, ``[{"id", "preset", "seconds",
  "fps"[, "speed", "seed", "script", "poster"]}]`` (``RECORDING_LIMITS``; the recorder of the site follows them);
* ``kind`` is derived from the audience (``playground`` for the laboratories, else ``demo``).

``load`` checks all of this (``check``); ``describe`` gives the catalogue's entry. The old ids (``v01_light_travel`` …,
before 2026-11-13) are aliases (``ALIASES``): ``folder``, ``load`` and ``describe`` accept them, and so do the server's
routes and the run records (``lfviz.runs``).
"""

from __future__ import annotations

import hashlib
import importlib
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # .../visualizations
SERVER = ROOT / "server"
ENGINE = ROOT.parent / "lfphys"  # the physics engine library (package lfphys), engine/lfphys
_NAME = re.compile(r"^[surp]\d{2}_[a-z0-9_]+$")

if str(ENGINE) not in sys.path:  # the texts below are the engine's T
    sys.path.insert(0, str(ENGINE))
from lfphys.i18n import T, is_t  # noqa: E402

#: the old ids (folders renamed on 2026-11-13; the archived reviews and old run records keep them) -> the new ones
ALIASES = {
    "v01_light_travel": "u31_light_travel", "v02_double_slit": "u32_double_slit", "v03_quantum_1d": "u33_quantum_1d",
    "v04_orbits": "u34_orbits", "v05_optics_bench": "u35_optics_bench", "v06_qcd": "u36_qcd",
    "v07_bell_test": "u37_bell_test", "v08_wave_3d": "u38_wave_3d", "v10_fast_observer": "u39_fast_observer",
    "v13_hydrogen_3d": "u40_hydrogen_3d", "v14_quarkonium_3d": "u41_quarkonium_3d",
    "v15_kerr_shadow": "u42_kerr_shadow", "v16_optical_vortices": "u43_optical_vortices",
    "v17_mie_scattering": "u44_mie_scattering",
    "v09_thomas_3d": "r11_thomas_3d", "v11_double_slit_2d": "r12_double_slit_2d",
    "v12_arrival_times_2d": "r13_arrival_times_2d",
}

#: the four audiences in the catalogue's order (plan §5.1): prefix, label, one line, the ``ui`` by default
AUDIENCES = [
    {"id": "school", "prefix": "s", "label": T("School"), "ui": "school",
     "text": T("Grades 7–11: the ordinary lab experiment, computed and guided step by step")},
    {"id": "university", "prefix": "u", "label": T("University"), "ui": "standard", "picture": "u32_double_slit",
     "text": T("The experiments of the university courses, computed from the laws")},
    {"id": "research", "prefix": "r", "label": T("Research"), "ui": "full", "picture": "r12_double_slit_2d",
     "text": T("Set-ups not computed before, to study the harder laws; every novelty is a hypothesis")},
    {"id": "playground", "prefix": "p", "label": T("Laboratories"), "ui": "full", "picture": "p04_fluids",
     "text": T("Free benches: build a scene, and the engine computes it live")},
]
AUDIENCE = {a["id"]: a for a in AUDIENCES}
# ``picture`` (optional): the world whose picture the start page's tile shows (review P17-start-page F10: the first world
# with a picture gave a nearly blank tile); without one, or while that world has no picture, the first world that has one


def check_audiences() -> list[str]:
    """What is wrong with ``AUDIENCES`` (empty when nothing): a tile's ``picture`` names a world of that audience."""
    out, ids = [], set(viz_ids())
    for a in AUDIENCES:
        w = a.get("picture")
        if w is None:
            continue
        if w not in ids:
            out.append(f"audience {a['id']}: picture {w!r} is no world")
        elif not w.startswith(a["prefix"]):
            out.append(f"audience {a['id']}: picture {w!r} is not a world of this audience (prefix {a['prefix']})")
    return out

#: the physics sections in teaching order (plan §5.1; curriculum research §2)
SECTIONS = [
    {"id": "mechanics", "label": T("Mechanics")},
    {"id": "fluids", "label": T("Liquids and gases")},
    {"id": "waves", "label": T("Oscillations and waves")},
    {"id": "heat", "label": T("Heat and molecular physics")},
    {"id": "electromagnetism", "label": T("Electricity and magnetism")},
    {"id": "optics", "label": T("Optics")},
    {"id": "relativity", "label": T("The theory of relativity")},
    {"id": "quantum", "label": T("Quantum physics")},
    {"id": "atom", "label": T("Atomic physics")},
    {"id": "condensed_matter", "label": T("Condensed matter")},
    {"id": "nucleus", "label": T("Nuclear physics")},
    {"id": "particles", "label": T("Particle physics")},
    {"id": "astrophysics", "label": T("Astrophysics and cosmology")},
]
SECTION = {s["id"]: s for s in SECTIONS}

UIS = ("school", "standard", "full")
#: what a recording spec may ask of the site's recorder (DESIGN §4.1, §4.3): the played seconds, the frames per played
#: second, their product, and the commands of a script (the ones a viewer of a live run may send that change the world)
RECORDING_LIMITS = {"seconds": (1.0, 180.0), "fps": (1, 30), "frames": 3600,
                    "commands": ("set", "action", "view", "new_world")}
_REC_ID = re.compile(r"^[a-z0-9_]{1,40}$")
_PLANNED_ID = re.compile(r"^[SUR]\d{2}$|^p\d{2}$")


def roots() -> list[Path]:
    """Where visualization folders are found: ``visualizations/`` and, for tests only, the folders named in the
    environment variable ``LFVIZ_EXTRA`` (e.g. the toy playground of ``tests/playgrounds``)."""
    extra = [Path(p) for p in os.environ.get("LFVIZ_EXTRA", "").split(os.pathsep) if p.strip()]
    return [ROOT] + [p for p in extra if p.is_dir()]


def resolve(viz_id: str) -> str:
    """The current id of a visualization: an old id (``ALIASES``) gives its new one, any other id itself."""
    return ALIASES.get(viz_id, viz_id) if isinstance(viz_id, str) else viz_id


def aliases_of(viz_id: str) -> list[str]:
    """The old ids that name this visualization."""
    return sorted(old for old, new in ALIASES.items() if new == viz_id)


def folder(viz_id: str) -> Path:
    """The folder of a visualization, also by an old id (KeyError when there is none)."""
    viz_id = resolve(viz_id)
    if isinstance(viz_id, str) and _NAME.match(viz_id):
        for r in roots():
            if (r / viz_id / "viz.py").is_file():
                return r / viz_id
    raise KeyError(viz_id)


def ensure_path():
    for p in [str(ENGINE), *map(str, reversed(roots())), str(SERVER)]:
        if p not in sys.path:
            sys.path.insert(0, p)


def viz_ids() -> list[str]:
    return sorted({p.name for r in roots() for p in r.iterdir()
                   if p.is_dir() and _NAME.match(p.name) and (p / "viz.py").is_file()})


def load(viz_id: str) -> dict:
    """``VIZ`` of a visualization (an old id gives the new one), with ``kind`` and ``ui`` filled in and checked
    (``check``: ValueError naming every problem)."""
    viz_id = resolve(viz_id)
    folder(viz_id)  # KeyError when there is none
    ensure_path()
    mod = importlib.import_module(f"{viz_id}.viz")
    viz = dict(mod.VIZ)
    if viz.get("id") != viz_id:
        raise ValueError(f"{viz_id}/viz.py declares id {viz.get('id')!r}")
    aud = AUDIENCE.get(viz.get("audience"))
    if aud is not None:
        viz.setdefault("ui", aud["ui"])
        viz.setdefault("kind", "playground" if aud["id"] == "playground" else "demo")
    problems = check(viz)
    if problems:
        raise ValueError(f"{viz_id}/viz.py: " + "; ".join(problems))
    return viz


def _is_text(x) -> bool:
    """A translatable text with words (a ``T``, not a plain string)."""
    return is_t(x) and bool(x["$t"].strip())


def check(viz: dict) -> list[str]:
    """What is wrong with a ``VIZ`` (empty when nothing): the audience against the prefix, the section, ``ui``, the fields
    the audience needs, the recording specs (DESIGN §3.1). ``related`` is checked against the other worlds and the
    planned items by ``tests/test_site_registry.py``, which sees them all."""
    out = []
    vid = viz.get("id") or ""
    aud = AUDIENCE.get(viz.get("audience"))
    if aud is None:
        return [f"audience {viz.get('audience')!r} is none of {sorted(AUDIENCE)}"]
    if not vid.startswith(aud["prefix"]):
        out.append(f"the audience {aud['id']} takes the prefix {aud['prefix']}, the id is {vid!r}")
    if (viz.get("kind") == "playground") != (aud["id"] == "playground"):
        out.append(f"kind {viz.get('kind')!r} disagrees with the audience {aud['id']}")
    if viz.get("section") not in SECTION:
        out.append(f"section {viz.get('section')!r} is none of {[s['id'] for s in SECTIONS]}")
    ui = viz.get("ui")
    if ui not in UIS:
        out.append(f"ui {ui!r} is none of {UIS}")
    elif (ui == "school") != (aud["id"] == "school"):
        out.append(f"ui 'school' is for the school audience only (ui {ui!r}, audience {aud['id']})")
    if not _is_text(viz.get("teaser")):
        out.append("no teaser (a T: one line, what you will see)")
    rel = viz.get("related", [])
    if not isinstance(rel, list) or not all(isinstance(r, str) and (_NAME.match(r) or _PLANNED_ID.match(r))
                                            for r in rel):
        out.append(f"related {rel!r}: a list of world ids or planned ids (S01, U01, R01, p05)")
    if aud["id"] == "school":
        cur = viz.get("curriculum") or []
        systems = {str(c.get("system", "")) for c in cur if isinstance(c, dict)}
        if not any(s.startswith("FRP") for s in systems):
            out.append("a school world needs an FRP anchor (the Russian federal programme) in curriculum")
        if not any(s.startswith(("AP", "IB", "AQA")) for s in systems):
            out.append("a school world needs an AP, IB or AQA anchor in curriculum")
        if not viz.get("guide"):
            out.append("a school world needs its guide")
        schema = viz.get("schema")
        laws = [p.id for p in getattr(schema, "params", []) if getattr(p, "standard", None) is not None]
        if laws:
            out.append(f"a school world has no modified physics, yet declares laws {laws}")
    elif aud["id"] == "university":
        courses = viz.get("courses") or []
        if not courses or not all(isinstance(c, dict) and _is_text(c.get("text")) for c in courses):
            out.append("a university world needs courses: [{'text': T(...), 'chapters': ...}]")
    elif aud["id"] == "research":
        if not _is_text(viz.get("question")):
            out.append("a research world needs its question (a T)")
        pa = viz.get("prior_art") or []
        if not pa or not all(isinstance(r, dict) and r.get("ref") for r in pa):
            out.append("a research world needs its prior art: [{'ref': ..., 'url': ...}]")
        if viz.get("status") != "hypothesis":
            out.append("a research world's status is 'hypothesis' until reproduced (AGENTS.md rule 11)")
    out += _check_recordings(viz, aud["id"])
    return out


def _check_recordings(viz: dict, audience: str) -> list[str]:
    recs = viz.get("recordings")
    if audience == "playground":
        return [] if not recs else ["a laboratory has no recordings: it computes what its user builds"]
    if not isinstance(recs, list) or not recs:
        return ["no recordings: the public site plays at least one (DESIGN §4.1)"]
    out, seen = [], set()
    presets = getattr(viz.get("schema"), "presets", {}) or {}
    lim = RECORDING_LIMITS
    for r in recs:
        if not isinstance(r, dict):
            out.append(f"recording {r!r} is not a dict")
            continue
        rid = r.get("id")
        if not isinstance(rid, str) or not _REC_ID.match(rid) or rid in seen:
            out.append(f"recording id {rid!r}: a unique slug")
        seen.add(rid)
        if r.get("preset") not in presets:
            out.append(f"recording {rid}: preset {r.get('preset')!r} is not one of the world's")
        sec, fps = r.get("seconds"), r.get("fps")
        if not isinstance(sec, (int, float)) or not lim["seconds"][0] <= sec <= lim["seconds"][1]:
            out.append(f"recording {rid}: seconds {sec!r} outside {lim['seconds']}")
        if not isinstance(fps, int) or not lim["fps"][0] <= fps <= lim["fps"][1]:
            out.append(f"recording {rid}: fps {fps!r} outside {lim['fps']}")
        if isinstance(sec, (int, float)) and isinstance(fps, int) and sec * fps > lim["frames"]:
            out.append(f"recording {rid}: {sec} s × {fps} fps exceeds {lim['frames']} frames")
        speed = r.get("speed")
        if speed is not None and not (isinstance(speed, (int, float)) and speed > 0):
            out.append(f"recording {rid}: speed {speed!r} is a positive number or None (the world's default)")
        if not isinstance(r.get("seed", 1), int):
            out.append(f"recording {rid}: seed is an integer")
        poster = r.get("poster", 0)
        if not isinstance(poster, (int, float)) or (isinstance(sec, (int, float)) and not 0 <= poster <= sec):
            out.append(f"recording {rid}: poster {poster!r} is a time within the recording")
        for c in r.get("script") or []:
            if not isinstance(c, dict) or c.get("cmd") not in lim["commands"] \
                    or not isinstance(c.get("at"), (int, float)) or (isinstance(sec, (int, float)) and not 0 <= c["at"] <= sec):
                out.append(f"recording {rid}: script entry {c!r}: {{'at': seconds, 'cmd': one of {lim['commands']}, "
                           f"'args': {{...}}}}")
    return out


# modules of the server process only (HTTP routes, the runs' bookkeeping): no worker imports them, so they never change
# what a run computes; leaving them out keeps checkpoints and the site's recordings valid across server-only edits
SERVER_ONLY = frozenset({"app.py", "runs.py"})


def code_hash(viz_id: str) -> str:
    """Hash of the code a run executes: the visualization folder, the lfviz package and the engine (no git needed)."""
    h = hashlib.sha256()
    vf = folder(viz_id)
    files = sorted(list(vf.rglob("*.py")) + list(vf.rglob("*.js"))
                   + list((SERVER / "lfviz").rglob("*.py")) + list((ENGINE / "lfphys").rglob("*.py")))
    for f in files:
        if "__pycache__" in f.parts or f.parent == SERVER / "lfviz" and f.name in SERVER_ONLY:
            continue
        own = f.is_relative_to(vf)
        if ("tests" in f.relative_to(vf).parts) if own else ("tests" in f.relative_to(ROOT.parent).parts):
            continue  # a folder's own tests are not the code a run executes (a section found through LFVIZ_EXTRA,
            # e.g. in tests/playgrounds, is: review B6-F24)
        rel = (f.relative_to(ROOT.parent) if f.is_relative_to(ROOT.parent)
               else Path("extra") / vf.name / f.relative_to(vf))  # a section outside engine/
        h.update(str(rel).encode())
        h.update(f.read_bytes())
    return h.hexdigest()[:12]


_CODE_HASHES: dict[str, str] = {}


def code_hash_cached(viz_id: str) -> str:
    """``code_hash`` of a visualization, computed once per process (the catalogue's entries carry it, and it reads the
    whole engine): what a recording's ``code_hash`` is compared with («recorded with code X; this server runs Y»,
    design of the start page §4.6). A file edited while the process runs is not seen; ``code_hash`` itself always
    reads the files."""
    viz_id = resolve(viz_id)
    if viz_id not in _CODE_HASHES:
        _CODE_HASHES[viz_id] = code_hash(viz_id)
    return _CODE_HASHES[viz_id]


def citation() -> dict:
    """What a publication cites (lfphys Research Licence §5): the version in CITATION.cff and the code identifier of this
    copy (a hash of the server and the engine, as in ``code_hash``), for a copy that is not a release."""
    version = None
    try:
        for line in (ROOT.parent / "CITATION.cff").read_text(encoding="utf-8").splitlines():
            if line.startswith("version:"):
                version = line.split(":", 1)[1].strip().strip('"')
    except OSError:
        pass
    h = hashlib.sha256()
    for f in sorted(list((SERVER / "lfviz").rglob("*.py")) + list((ENGINE / "lfphys").rglob("*.py"))):
        if "__pycache__" in f.parts:
            continue
        h.update(str(f.relative_to(ROOT.parent)).encode())
        h.update(f.read_bytes())
    return {"version": version, "code": h.hexdigest()[:12],
            "text": f"I. Idrisov, lfphys: a physics engine and interactive visualizations of physical hypotheses, "
                    f"version {version} (code {h.hexdigest()[:12]})"}


def recordings_of(viz: dict) -> list[dict]:
    """The recording specs of a world with their defaults filled in and the preset's label (the catalogue's form)."""
    presets = getattr(viz.get("schema"), "presets", {}) or {}
    out = []
    for r in viz.get("recordings") or []:
        pre = presets.get(r.get("preset"), {})
        out.append({"id": r["id"], "preset": r.get("preset"), "label": r.get("label") or pre.get("label", r.get("preset")),
                    "seconds": r.get("seconds"), "fps": r.get("fps"), "speed": r.get("speed"),
                    "seed": r.get("seed", 1), "poster": r.get("poster", 0), "script": list(r.get("script") or [])})
    return out


def picture(viz_id: str) -> str | None:
    """The world's picture for the catalogue and the README (``docs/images/<id>.jpg``, made by the site's posters
    script), relative to the repository; None while there is none."""
    rel = f"docs/images/{viz_id}.jpg"
    return rel if (ROOT.parent / rel).is_file() else None


def describe(viz: dict | str) -> dict:
    """The catalogue's entry of a visualization (``GET /api/viz``; the start page, the README and the site are made from
    it). ``viz`` is a loaded ``VIZ`` or an id (an old id too)."""
    if isinstance(viz, str):
        viz = load(viz)
    aud = viz.get("audience")
    out = {
        "id": viz["id"],
        "title": viz["title"],
        "summary": viz.get("summary", ""),
        "purpose": viz.get("purpose", ""),
        "version": viz.get("version", ""),
        "code_hash": code_hash_cached(viz["id"]),
        "kind": viz.get("kind", "demo"),
        "audience": aud,
        "section": viz.get("section"),
        "ui": viz.get("ui"),
        "teaser": viz.get("teaser"),
        "related": list(viz.get("related") or []),
        "recordings": recordings_of(viz),
        "aliases": aliases_of(viz["id"]),
        "picture": picture(viz["id"]),
        "schema": viz["schema"].to_json(),
    }
    if aud == "school":
        out["curriculum"] = list(viz.get("curriculum") or [])
    elif aud == "university":
        out["courses"] = list(viz.get("courses") or [])
    elif aud == "research":
        out.update(question=viz.get("question"), prior_art=list(viz.get("prior_art") or []), status=viz.get("status"))
    return out
