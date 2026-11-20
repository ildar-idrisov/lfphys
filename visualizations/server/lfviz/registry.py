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
* per audience: school ``curriculum`` (a ФРП anchor and an AP/IB/AQA anchor); university ``courses``
  (``[{"text": T, "chapters": str}]``); research ``question`` (T), ``prior_art`` (``[{"ref", "url"}]``) and ``status``
  (``"hypothesis"`` until reproduced: ``AGENTS.md`` rule 11); the former school ``guide`` is retired (design of
  2026-11-14 §2.5: the lab's steps replace it);
* ``recordings`` (not for the laboratories, at least one): what the public site plays, ``[{"id", "preset", "seconds",
  "fps"[, "speed", "seed", "script", "poster", "captions", "quantize"]}]`` (``RECORDING_LIMITS``; the recorder of the
  site follows them; a script may also change the playback ``speed``; ``captions`` ``[{"at", "text": T, "hold"?}]``);
* ``screens`` (design ``lfphys/sources/explore_2026-11-14_design.md`` §2): the demonstration's Watch, Explore and Lab work,
  in tab order (``check_screens``; normalised for the catalogue by ``screens_of``, their atlases listed by
  ``atlases_of``); a school world needs Explore and Lab work (or ``lab_absent``: a T, why the programme has no lab);
* ``kind`` is derived from the audience (``playground`` for the laboratories, else ``demo``).

``load`` checks all of this (``check``); ``describe`` gives the catalogue's entry. The old ids (``v01_light_travel`` …,
before 2026-11-13) are aliases (``ALIASES``): ``folder``, ``load`` and ``describe`` accept them, and so do the server's
routes and the run records (``lfviz.runs``).
"""

from __future__ import annotations

import hashlib
import importlib
import json
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

from . import expr as _expr  # noqa: E402

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
                    "commands": ("set", "action", "view", "new_world", "speed")}
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
    if "guide" in viz:
        out.append("guide is retired (design of 2026-11-14 §2.5): the lab's steps replace it")
    out += _check_recordings(viz, aud["id"])
    out += check_screens(viz)
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
            elif c["cmd"] == "speed":
                v = (c.get("args") or {}).get("value")
                if isinstance(v, bool) or not isinstance(v, (int, float)) or not v > 0:
                    out.append(f"recording {rid}: script entry {c!r}: speed takes {{'value': world seconds per played "
                               f"second > 0}}")
        out += [f"recording {rid}: {x}" for x in _check_captions(r.get("captions"), sec)]
        out += [f"recording {rid}: {x}" for x in _check_quantize(r.get("quantize"))]
        if r.get("quantize"):
            out += _check_quant_declared(r["quantize"], view_declarations(viz), f"recording {rid}")
    return out


def _check_captions(caps, seconds) -> list[str]:
    """``captions``: ``[{"at": played seconds, "text": T, "hold": seconds?}]``, in order of ``at`` (design §2.2)."""
    if caps is None:
        return []
    if not isinstance(caps, list):
        return [f"captions {caps!r}: a list of {{'at', 'text': T, 'hold'?}}"]
    out, last = [], -1.0
    for c in caps:
        at = c.get("at") if isinstance(c, dict) else None
        if not isinstance(c, dict) or isinstance(at, bool) or not isinstance(at, (int, float)) \
                or (isinstance(seconds, (int, float)) and not 0 <= at <= seconds):
            out.append(f"caption {c!r}: 'at' is a time within the recording")
            continue
        if at < last:
            out.append(f"caption at {at}: the captions are in the order of their times")
        last = at
        if not _is_text(c.get("text")):
            out.append(f"caption at {at}: its text is a T")
        hold = c.get("hold")
        if hold is not None and (isinstance(hold, bool) or not isinstance(hold, (int, float)) or not hold > 0):
            out.append(f"caption at {at}: hold {hold!r} is a positive number of seconds")
    return out


_QKEY = re.compile(r"^[a-z_][a-z0-9_]*\.[A-Za-z0-9_]+(\|[A-Za-z0-9_]+)*$")


def quantize_items(qmap) -> list[tuple[str, str, str]]:
    """A ``quantize`` map expanded: ``{"detections.t|x": "u16"}`` -> ``[("detections", "t", "u16"), ("detections", "x",
    "u16")]``."""
    out = []
    for key, enc in (qmap or {}).items():
        typ, _, names = key.partition(".")
        out += [(typ, b, enc) for b in names.split("|")]
    return out


#: the message types whose blobs may be quantised: what is drawn. The other types that make a point a world or say it is
#: right (``UNDROPPABLE``: checks, events, errors, captions …) are never quantised (RULES.md §10; review R-F F9)
QUANT_TYPES_REFUSED = frozenset({"end", "check", "event", "error", "notice", "caption", "state", "live"})


def _check_quantize(qmap) -> list[str]:
    """A ``quantize`` map: keys ``<message type>.<blob>[|<blob>…]``, values an encoding of
    ``protocol.QUANT_ENCODINGS`` (design §1.3, §2.5); never the blobs of a check, an event or another type that says
    the run is right (``QUANT_TYPES_REFUSED``)."""
    from .protocol import QUANT_ENCODINGS, quant_encoding_ok  # noqa: PLC0415
    if qmap is None:
        return []
    if not isinstance(qmap, dict):
        return [f"quantize {qmap!r}: a map {{'<type>.<blob>': encoding}}"]
    out = []
    for key, enc in qmap.items():
        if not isinstance(key, str) or not _QKEY.match(key):
            out.append(f"quantize key {key!r}: '<message type>.<blob>[|<blob>…]'")
        elif key.partition(".")[0] in QUANT_TYPES_REFUSED:
            out.append(f"quantize key {key!r}: a {key.partition('.')[0]} message is never quantised (only what is "
                       f"drawn: never measurables, events or checks)")
        if not quant_encoding_ok(enc):
            out.append(f"quantize {key!r}: {enc!r} is none of {sorted(QUANT_ENCODINGS)} (optionally ':col' or ':all')")
    return out


# --- screens: Watch, Explore, Lab work (design lfphys/sources/explore_2026-11-14_design.md §2) ----------------------
SCREEN_KINDS = ("watch", "explore", "lab")
#: the default tab labels (the glossary of the design §10, question 1)
SCREEN_LABELS = {"watch": T("Watch"), "explore": T("Explore"), "lab": T("Lab work")}
ACTS = ("next", "now")
TIMES = ("flight", "buildup", "none")
INSTRUMENT_KINDS = ("ruler", "protractor", "stopwatch", "readout", "counter")
#: the instruments drawn over the view at the world's places (the view's ``anchors()`` and ``worldToPx``; EX2 §5 F8)
PLACED_KINDS = ("ruler", "protractor")
COLUMN_OPS = ("sqrt", "square", "sin2", "inverse", "log")
FITS = ("line0", "line", "quadratic", "power")
LAW_QUANTITIES = ("slope", "intercept", "vertex", "exponent")
#: the fit models that give a law's quantity (integrator D4): the slope of a line (through the origin or not), the
#: intercept of a line, the vertex of a parabola, the exponent of a power law
LAW_MODELS = {"slope": ("line0", "line"), "intercept": ("line",), "vertex": ("quadratic",), "exponent": ("power",)}
#: the limits of an atlas (design §1.8): controls per atlas by ``ui``; points (the product of the value counts): the
#: target (over it the registry warns through ``tests/test_site_registry.py``) and the hard limit; earlier points kept
ATLAS_LIMITS = {"controls": {"school": 5, "standard": 6, "full": 6}, "points": (1500, 3000), "traces": (0, 5)}
#: what an atlas may never drop: what makes a point a world (rules 2, 3) and what says it is right
UNDROPPABLE = frozenset({"header", "frame", "end", "check", "event", "error", "notice", "caption", "state", "live"})
_SLUG = re.compile(r"^[a-z][a-z0-9_]{0,39}$")
_COL = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,39}$")  # a lab table's column (L, sqrt_h)


def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _check_stop(stop, where: str) -> list[str]:
    """An atlas point's stop rule (design §1.2; EX2 §5 F2): ``{"world_s": t}``, ``{"event": kind, "after_s": s,
    "max_world_s": t}`` or ``{"events": {kind: n, …}, "after_s": s, "max_world_s": t}`` (the point stops ``after_s``
    after the first kind, or name, that has occurred n times; ``{"event": k}`` is the shorthand of ``{"events": {k:
    1}}``). ``max_world_s`` is required with an event: a run whose events do not come by then fails."""
    if isinstance(stop, dict) and set(stop) == {"world_s"} and _num(stop["world_s"]) and stop["world_s"] > 0:
        return []
    tail = isinstance(stop, dict) and _num(stop.get("after_s", 0)) and stop.get("after_s", 0) >= 0 \
        and _num(stop.get("max_world_s")) and stop["max_world_s"] > 0
    if tail and set(stop) <= {"event", "after_s", "max_world_s"} and isinstance(stop.get("event"), str) \
            and stop["event"]:
        return []
    ev = stop.get("events") if isinstance(stop, dict) else None
    if tail and set(stop) <= {"events", "after_s", "max_world_s"} and isinstance(ev, dict) and ev \
            and all(isinstance(k, str) and k and isinstance(n, int) and not isinstance(n, bool) and n >= 1
                    for k, n in ev.items()):
        return []
    return [f"{where}: stop {stop!r} is {{'world_s': t}}, {{'event': kind, 'after_s': s, 'max_world_s': t}} or "
            f"{{'events': {{kind: n ≥ 1, …}}, 'after_s': s, 'max_world_s': t}}"]


def stop_events(stop: dict) -> dict:
    """The counted events of a stop rule (EX2 §5 F2): ``{kind or name: n}``; ``{"event": k}`` is ``{k: 1}``; empty for
    ``world_s`` or ``seconds``."""
    if not isinstance(stop, dict):
        return {}
    if isinstance(stop.get("events"), dict):
        return {str(k): int(n) for k, n in stop["events"].items()}
    if stop.get("event"):
        return {str(stop["event"]): 1}
    return {}


def _view_js(viz: dict) -> str | None:
    try:
        f = folder(viz.get("id") or "") / "web" / "view.js"
    except KeyError:
        return None
    try:
        return f.read_text(encoding="utf-8")
    except OSError:
        return None


def _bracketed(text: str, start: int, open_: str, close: str) -> str:
    """The text from ``start`` (an opening bracket) to its matching close, strings skipped."""
    depth, i, quote = 0, start, None
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 1
            elif ch == quote:
                quote = None
        elif ch in "\"'`":
            quote = ch
        elif ch == open_:
            depth += 1
        elif ch == close:
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    return text[start:]


def view_declarations(viz: dict) -> dict:
    """What a world's view declares for the screens (design §2.4), read from its ``web/view.js``: ``quantSafe`` (the
    blobs it accepts quantised: an object literal of string pairs, ``quantSafe: {"traj.s": "u16"}`` or
    ``const QUANT_SAFE = {…}``) and the ids of its ``overlays`` (an array literal of ``{id: "…", …}``, ``overlays: […]`` or
    ``const OVERLAYS = […]``). None for a key the view does not declare. ``anchors`` and ``worldToPx``: whether the view
    defines them (a method or a property, ``anchors() {…}`` or ``anchors: …``; EX2 §5 F8: a lab step with a ruler or a
    protractor needs both, so that its instruments are drawn where the world is)."""
    js = _view_js(viz)
    out = {"quantSafe": None, "overlays": None, "anchors": False, "worldToPx": False}
    if js is None:
        return out
    js = re.sub(r"/\*.*?\*/|(?:^|(?<=\s))//.*?$", "", js, flags=re.S | re.M)  # comments (a URL's // stays)
    for name in ("anchors", "worldToPx"):
        out[name] = bool(re.search(rf"(?<![\w.]){name}\s*(?:\([^)]*\)\s*\{{|:|=)", js))
    m = re.search(r"\b(?:quantSafe|QUANT_SAFE)\s*[:=]\s*\{", js)
    if m:
        body = _bracketed(js, m.end() - 1, "{", "}")
        out["quantSafe"] = dict(re.findall(r"[\"']([^\"']+)[\"']\s*:\s*[\"']([^\"']+)[\"']", body))
    m = re.search(r"\b(?:overlays|OVERLAYS)\s*[:=]\s*\[", js)
    if m:
        body = _bracketed(js, m.end() - 1, "[", "]")
        out["overlays"] = re.findall(r"\bid\s*:\s*[\"']([\w.-]+)[\"']", body)
    return out


#: how fine a range suffix is: ``:all`` (one range) is the coarsest, no suffix (one range per column of a table of at
#: most ``protocol.COL_MAX`` columns, else one range) is in between, ``:col`` (a range per column) the finest
_SUFFIX_RANK = {"all": 0, "": 1, "col": 2}


def _quant_safe(enc: str, declared: str | None) -> bool:
    """A quantisation the view declared safe: the same encoding, or a finer one of the same transform (u16 where u8 is
    safe, u16sqrt where u8sqrt is), with ranges at least as fine as declared (``:all`` is refused where the view
    declared the default or ``:col``: one range over a table's columns widens the step of its narrow columns; review
    R-F F9)."""
    if not declared:
        return False
    want, _, wsuf = enc.partition(":")
    have, _, hsuf = declared.partition(":")
    same = want == have or (want, have) in {("u16", "u8"), ("u16sqrt", "u8sqrt")}
    return same and _SUFFIX_RANK.get(wsuf, -1) >= _SUFFIX_RANK.get(hsuf, 3)


def _check_quant_declared(qmap, decl: dict, where: str) -> list[str]:
    safe = decl.get("quantSafe") or {}
    return [f"{where}: quantize {typ}.{blob}: {enc} is not declared safe by the view (its quantSafe: "
            f"{safe.get(f'{typ}.{blob}')!r})" for typ, blob, enc in quantize_items(qmap)
            if _enc_ok(enc) and not _quant_safe(enc, safe.get(f"{typ}.{blob}"))]


def _enc_ok(enc) -> bool:
    from .protocol import quant_encoding_ok  # noqa: PLC0415
    return quant_encoding_ok(enc)


_DROP_BLOB = re.compile(r"^[a-z_][a-z0-9_]*\.[A-Za-z0-9_]+\*?$")


def _check_drop(drop, where: str) -> list[str]:
    """What an atlas does not keep (design §1.3; EX2 §5 F8): ``{types: [message types], frame_blobs: [blob names],
    blobs: ["<type>.<blob>", …]}``; a blob name may end with ``*`` (every blob whose name starts so); ``frame_blobs:
    [b]`` is the shorthand of ``blobs: ["frame.b"]``. Never what makes a point a world or says it is right: the types
    ``UNDROPPABLE``, and the blobs of the types ``QUANT_TYPES_REFUSED`` (checks, events, errors, …)."""
    if drop is None:
        return []
    keys = ("types", "frame_blobs", "blobs")
    if not isinstance(drop, dict) or set(drop) - set(keys) \
            or not all(isinstance(drop.get(k, []), list) and all(isinstance(x, str) for x in drop.get(k, []))
                       for k in keys):
        return [f"{where}: drop {drop!r} is {{'types': [message types], 'frame_blobs': [blob names], 'blobs': "
                f"['<type>.<blob>', …]}}"]
    out = []
    bad = sorted(set(drop.get("types", [])) & UNDROPPABLE)
    if bad:
        out.append(f"{where}: drop: {bad} cannot be dropped (they make a point a world and say it is right)")
    for b in drop.get("blobs", []):
        if not _DROP_BLOB.match(b):
            out.append(f"{where}: drop blob {b!r} is '<message type>.<blob>' (a '*' at the end of the blob's name "
                       f"allowed)")
        elif b.partition(".")[0] in QUANT_TYPES_REFUSED:
            out.append(f"{where}: drop blob {b!r}: the blobs of a {b.partition('.')[0]} message are never dropped "
                       f"(they say the run is right)")
    return out


def drop_blob_rules(drop: dict | None) -> list[tuple[str, str, bool]]:
    """An atlas's dropped blobs as ``(type, name, prefix)``: ``frame_blobs`` as ``frame.<name>``, ``blobs`` as given,
    a name ending with ``*`` a prefix (EX2 §5 F8)."""
    out = []
    for b in (drop or {}).get("frame_blobs") or []:
        out.append(("frame", b, False))
    for b in (drop or {}).get("blobs") or []:
        typ, _, name = b.partition(".")
        out.append((typ, name[:-1], True) if name.endswith("*") else (typ, name, False))
    return out


#: names a compound control's id cannot take: the keys a control's values share in the player's objects (EX2 §5 F3)
_JS_OWN = frozenset({"constructor", "prototype", "toString", "valueOf", "hasOwnProperty", "isPrototypeOf",
                     "propertyIsEnumerable", "toLocaleString", "__proto__", "__defineGetter__", "__defineSetter__",
                     "__lookupGetter__", "__lookupSetter__"})


def control_key(c: dict) -> str | None:
    """The key of a control's value in a point's values (the manifest's and the player's ``param``): its parameter, or
    a compound control's ``id`` (EX2 §5 F3)."""
    return c.get("id") if "sets" in c else c.get("param")


def expand_values(controls: list[dict], values: dict) -> dict:
    """The world's parameter values of a point: a compound control's grid value replaced by the parameters it sets
    (``sets[param][k]`` for the value's index k among its ``values``); a plain control's value as it is. ValueError
    for a compound value off its grid (a compound control takes grid values only, EX2 §5 F3)."""
    out = dict(values)
    for c in controls:
        if "sets" not in c:
            continue
        key = control_key(c)
        if key not in out:
            continue
        v = out.pop(key)
        k = next((j for j, x in enumerate(c["values"]) if type(x) is type(v) and x == v), None)
        if k is None:
            k = next((j for j, x in enumerate(c["values"]) if x == v), None)
        if k is None:
            raise ValueError(f"{key} = {v!r} is not one of the compound control's values {c['values']}")
        for p, vals in c["sets"].items():
            out[p] = vals[k]
    return out


def _check_compound(viz, c: dict, preset, fixed, where: str) -> tuple[list[str], set, int]:
    """A compound control (EX2 §5 F3): ``{id, label, unit?, values, labels?, sets: {param: [one value per grid value]},
    default?}``; returns (problems, the parameters it sets, its number of values)."""
    schema = viz.get("schema")
    by_id = getattr(schema, "by_id", {}) or {}
    out = []
    cid = c.get("id")
    w = f"{where}: compound control {cid!r}"
    extra = sorted(set(c) - {"id", "label", "unit", "values", "labels", "sets", "default"})
    if "param" in c:
        out.append(f"{w}: a compound control has an id and sets, no param")
    elif extra:
        out.append(f"{w}: unknown fields {extra}")
    if not isinstance(cid, str) or not _SLUG.match(cid) or cid in by_id or cid in _JS_OWN:
        out.append(f"{w}: id is a slug that is no parameter of the schema")
    if not _is_text(c.get("label")):
        out.append(f"{w}: label is a T (a compound control has no parameter to take it from)")
    if c.get("unit") is not None and not (_is_text(c["unit"]) or isinstance(c["unit"], str)):
        out.append(f"{w}: unit is a T or a string (a symbol such as \"°\")")
    vals = c.get("values")
    if not isinstance(vals, list) or not vals or len({json.dumps(v) for v in vals}) != len(vals) \
            or not all(isinstance(v, (str, int, float)) for v in vals):
        return out + [f"{w}: values is a list of distinct numbers or strings"], set(), 1
    if "default" in c and c["default"] not in vals:
        out.append(f"{w}: default {c['default']!r} is not one of its values")
    labels = c.get("labels")
    if labels is not None and (not isinstance(labels, list) or len(labels) != len(vals)
                               or not all(_is_text(x) for x in labels)):
        out.append(f"{w}: labels is a list of T, one per value")
    sets = c.get("sets")
    if not isinstance(sets, dict) or not sets:
        return out + [f"{w}: sets is a map {{param: [one value per grid value]}}"], set(), len(vals)
    for pid, lst in sets.items():
        if pid not in by_id:
            out.append(f"{w}: sets {pid!r}, no parameter of the schema")
        elif pid in (fixed or {}):
            out.append(f"{w}: {pid} is both set by the control and fixed")
        if not isinstance(lst, list) or len(lst) != len(vals):
            out.append(f"{w}: sets {pid}: one value per grid value ({len(vals)})")
        elif pid in by_id and by_id[pid].standard is not None and viz.get("ui") == "school":
            out.append(f"{w}: sets {pid}, a law parameter: no modified physics at school (rule 4)")
    if not out and schema is not None:
        for k, v in enumerate(vals):
            _p, errs = schema.resolve(preset, {**(fixed or {}), **{pid: lst[k] for pid, lst in sets.items()}})
            if errs:
                out.append(f"{w}: value {v!r} sets values the schema refuses: {[str(e) for e in errs]}")
    return out, set(sets) if isinstance(sets, dict) else set(), len(vals)


def _check_controls(viz, controls, preset, fixed, where: str, limit: int) -> list[str]:
    schema = viz.get("schema")
    by_id = getattr(schema, "by_id", {}) or {}
    out = []
    if not isinstance(controls, list) or not controls:
        return [f"{where}: controls: a list of {{'param', 'values', 'default'?}} or compound "
                f"{{'id', 'label', 'values', 'sets'}}"]
    if len(controls) > limit:
        out.append(f"{where}: {len(controls)} controls, at most {limit} at ui {viz.get('ui')!r}")
    seen, n = set(), 1
    compound_sets: dict = {}  # param -> the compound control that sets it
    for c in controls:
        if isinstance(c, dict) and "sets" in c:
            probs, params, nv = _check_compound(viz, c, preset, fixed, where)
            out += probs
            n *= nv
            key = c.get("id")
            if key in seen:
                out.append(f"{where}: control {key} twice")
            seen.add(key)
            for pid in params:
                if pid in compound_sets:
                    out.append(f"{where}: {pid} is set by two compound controls")
                compound_sets[pid] = key
            continue
        if not isinstance(c, dict) or c.get("param") not in by_id:
            out.append(f"{where}: control {c!r}: 'param' is a parameter of the schema")
            continue
        pid = c["param"]
        if pid in seen:
            out.append(f"{where}: control {pid} twice")
        seen.add(pid)
        if pid in (fixed or {}):
            out.append(f"{where}: {pid} is both a control and fixed")
        p = by_id[pid]
        if p.standard is not None and viz.get("ui") == "school":
            out.append(f"{where}: {pid} is a law parameter: no modified physics at school (rule 4)")
        vals = c.get("values")
        if not isinstance(vals, list) or not vals or len({json.dumps(v) for v in vals}) != len(vals):
            out.append(f"{where}: control {pid}: values is a list of distinct values")
            continue
        n *= len(vals)
        for v in vals:
            _p, errs = schema.resolve(preset, {**(fixed or {}), pid: v})
            if errs:
                out.append(f"{where}: control {pid}: value {v!r} refused by the schema: {[str(e) for e in errs]}")
        if "default" in c and c["default"] not in vals:
            out.append(f"{where}: control {pid}: default {c['default']!r} is not one of its values")
        if c.get("label") is not None and not _is_text(c["label"]):
            out.append(f"{where}: control {pid}: label is a T")
        if c.get("unit") is not None and not (_is_text(c["unit"]) or isinstance(c["unit"], str)):
            out.append(f"{where}: control {pid}: unit is a T or a string (a symbol such as \"nm\")")
    for pid, key in compound_sets.items():
        if pid in seen:
            out.append(f"{where}: {pid} is both a control and set by the compound control {key}")
    pmin, pmax = ATLAS_LIMITS["points"]
    if n > pmax:
        out.append(f"{where}: {n} grid points, at most {pmax}")
    elif compound_sets and not out and schema is not None:  # every combination resolves (EX2 §5 F3)
        import itertools  # noqa: PLC0415
        for combo in itertools.product(*[c["values"] for c in controls]):
            vals = expand_values(controls, {control_key(c): v for c, v in zip(controls, combo)})
            _p, errs = schema.resolve(preset, {**(fixed or {}), **vals})
            if errs:
                out.append(f"{where}: the combination {dict(zip([control_key(c) for c in controls], combo))} is "
                           f"refused by the schema: {[str(e) for e in errs]}")
                break
    return out


#: the speed of a screen or a step (EX2 §5 F1): world seconds per played second, or "world" (the point's own default)
SPEED_WORLD = "world"
#: frames per played second an atlas may take (EX2 §5 F1: ``fps`` instead of ``frame_dt``)
ATLAS_FPS = (0.1, 120.0)


def _check_clock(sc, where: str) -> list[str]:
    """An atlas's clock and a screen's speed (EX2 §5 F1): exactly one of ``frame_dt`` (world seconds between frames)
    and ``fps`` (frames per played second at the world's default speed, ``headless.run_spec``'s recording clock);
    ``speed`` optional: world seconds per played second > 0, or ``"world"`` (the point's own default speed, from its
    ``state`` message)."""
    out = []
    fdt, fps = sc.get("frame_dt"), sc.get("fps")
    if (fdt is None) == (fps is None):
        out.append(f"{where}: one of frame_dt (world seconds between frames) and fps (frames per played second at the "
                   f"world's default speed), not {'both' if fdt is not None else 'neither'}")
    elif fdt is not None and (not _num(fdt) or not fdt > 0):
        out.append(f"{where}: frame_dt {fdt!r} is a positive number of world seconds")
    elif fps is not None and (not _num(fps) or not ATLAS_FPS[0] <= fps <= ATLAS_FPS[1]):
        out.append(f"{where}: fps {fps!r} is a number of frames per played second in {ATLAS_FPS}")
    speed = sc.get("speed")
    if speed is not None and speed != SPEED_WORLD and (not _num(speed) or not speed > 0):
        out.append(f"{where}: speed {speed!r} is world seconds per played second (> 0) or \"world\" (the point's own "
                   f"default speed)")
    return out


def _check_atlas_common(viz, sc, where: str, decl: dict) -> list[str]:
    out = []
    presets = getattr(viz.get("schema"), "presets", {}) or {}
    if sc.get("preset") not in presets:
        out.append(f"{where}: preset {sc.get('preset')!r} is not one of the world's")
    fixed = sc.get("fixed") or {}
    if not isinstance(fixed, dict):
        out.append(f"{where}: fixed is a map of parameter values")
        fixed = {}
    elif sc.get("preset") in presets:
        params, errs = viz["schema"].resolve(sc["preset"], fixed)
        if errs:
            out.append(f"{where}: fixed {fixed!r} refused by the schema: {[str(e) for e in errs]}")
        elif viz.get("ui") == "school":  # rule 4 (EX2 §5 F6): no modified physics at school, by a preset or fixed
            mods = [m.get("id") for m in viz["schema"].modifications(params)]
            if mods:
                out.append(f"{where}: its preset and fixed values set the law parameters {mods}: no modified physics "
                           f"at school (rule 4)")
    out += _check_clock(sc, where)
    if not isinstance(sc.get("seed", 1), int) or isinstance(sc.get("seed", 1), bool):
        out.append(f"{where}: seed is an integer")
    out += _check_stop(sc.get("stop"), where)
    out += _check_drop(sc.get("drop"), where)
    out += [f"{where}: {x}" for x in _check_quantize(sc.get("quantize"))]
    out += _check_quant_declared(sc.get("quantize"), decl, where)
    limit = ATLAS_LIMITS["controls"].get(viz.get("ui"), 6)
    out += _check_controls(viz, sc.get("controls"), sc.get("preset") if sc.get("preset") in presets else None,
                           fixed, where, limit)
    return out


def _lab_reference_takes_reference(sim) -> bool:
    """Whether ``Simulation.lab_reference`` takes the law's ``reference`` id (``lab_reference(step_id, fixed, values,
    reference)``)."""
    import inspect  # noqa: PLC0415
    fn = getattr(sim, "lab_reference", None)
    if not callable(fn):
        return False
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return False
    return "reference" in params or any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values())


def _check_laws(viz, st: dict, w: str, cids: list, fits: list) -> list[str]:
    """A lab step's laws: data, optional (EX2 §5 F6 (d); integrator D4 of 2026-11-17 for their form): the world's
    computed values for the bench, listed in Lab work's drawer under «Computed for this bench» with the quantity and the
    columns they belong to, never set beside the student's fit (the app judges nothing: the owner, 2026-11-18).
    ``laws``: ``[{x, y, model, quantity, label, unit, reference}]``: ``x`` and ``y`` two columns of the step; ``model``
    one of the step's plot ``fits``; ``quantity`` what the model gives (``LAW_MODELS``); ``label`` a T; ``unit`` a T or
    a plain symbol; ``reference`` an id unique in the step, answered by ``Simulation.lab_reference(step_id, fixed,
    values, reference)`` when the atlas is built. **[error in earlier]** The step's plot no longer has to be one of its
    laws (that served «Check against the law», which is withdrawn)."""
    out = []
    if "law" in st:
        out.append(f"{w}: law: a step declares laws: [{{x, y, model, quantity, label, unit, reference}}, …] "
                   f"(integrator D4)")
    laws = st.get("laws")
    if laws is None:
        return out
    if not isinstance(laws, list):
        return out + [f"{w}: laws {laws!r}: a list of {{x, y, model, quantity, label, unit, reference}}"]
    refs = set()
    for law in laws:
        if not isinstance(law, dict):
            out.append(f"{w}: law {law!r}: a map {{x, y, model, quantity, label, unit, reference}}")
            continue
        ref = law.get("reference")
        lw = f"{w}: law {ref!r}"
        extra = sorted(set(law) - {"x", "y", "model", "quantity", "label", "unit", "reference"})
        if extra:
            out.append(f"{lw}: unknown fields {extra}")
        if not isinstance(ref, str) or not _SLUG.match(ref) or ref in refs:
            out.append(f"{lw}: reference is an id (a slug), unique in the step")
        refs.add(ref)
        if law.get("x") not in cids or law.get("y") not in cids or law.get("x") == law.get("y"):
            out.append(f"{lw}: x {law.get('x')!r} and y {law.get('y')!r} are two columns of the step ({cids})")
        model, qty = law.get("model"), law.get("quantity")
        if model not in fits:
            out.append(f"{lw}: model {model!r} is not among the plot's fits {fits}")
        if qty not in LAW_QUANTITIES:
            out.append(f"{lw}: quantity {qty!r} is none of {LAW_QUANTITIES}")
        elif model not in LAW_MODELS[qty]:
            out.append(f"{lw}: the quantity {qty!r} comes from the models {LAW_MODELS[qty]}, not {model!r}")
        if not _is_text(law.get("label")):
            out.append(f"{lw}: label is a T")
        if not (_is_text(law.get("unit")) or isinstance(law.get("unit"), str)):
            out.append(f"{lw}: unit is a T or a string (a plain symbol)")
    if laws and not _lab_reference_takes_reference(viz.get("simulation")):
        out.append(f"{w}: laws: the world's Simulation has no lab_reference(step_id, fixed, values, reference)")
    return out


#: what a step on an Explore screen's atlas takes from the screen (EX2 §5 F9) and so may not declare itself
SHARED_FIELDS = ("preset", "fixed", "controls", "frame_dt", "fps", "stop", "seed", "quantize", "drop")
#: the task sheet's fields (EX2 §5 F8): ``frp`` at school, ``basis`` at university
WORKSHEET_FIELDS = ("frp", "basis", "goal", "bench", "procedure", "record", "record_rows", "variants")


def shared_screen(viz: dict, st: dict) -> dict | None:
    """The Explore screen whose atlas a lab step uses (``atlas: <screen id>``; EX2 §5 F9), or None."""
    sid = st.get("atlas") if isinstance(st, dict) else None
    if not isinstance(sid, str):
        return None
    return next((x for x in viz.get("screens") or [] if isinstance(x, dict) and x.get("id") == sid
                 and x.get("kind") == "explore"), None)


def _check_step_view(viz, st: dict, w: str, decl: dict) -> list[str]:
    """A lab step's ``overlays`` and ``readouts`` (EX2 §5 F6 (b)), as an Explore screen's."""
    out = []
    ov = st.get("overlays") or []
    have = decl.get("overlays")
    if not isinstance(ov, list) or not all(isinstance(o, str) for o in ov):
        out.append(f"{w}: overlays: a list of the ids the view declares")
    elif ov and not set(ov) <= set(have or []):
        out.append(f"{w}: overlays {sorted(set(ov) - set(have or []))} are not declared by the view (its overlays: "
                   f"{have})")
    rd = st.get("readouts") or []
    if not isinstance(rd, list) or not all(isinstance(x, str) and x for x in rd):
        out.append(f"{w}: readouts: a list of the world's measurables (ids in its header)")
    return out


def _check_lab(viz, sc, where: str, decl: dict) -> list[str]:
    out = []
    by_id = getattr(viz.get("schema"), "by_id", {}) or {}
    compound_ids = {c.get("id") for st in sc.get("steps") or [] if isinstance(st, dict)
                    for c in st.get("controls") or [] if isinstance(c, dict) and "sets" in c}
    instr = sc.get("instruments")
    if not isinstance(instr, dict) or not instr:
        out.append(f"{where}: instruments: a map {{id: {{kind, label, unit, division, error?, reads | manual, event?}}}}")
        instr = {}
    for iid, d in instr.items():
        w = f"{where}: instrument {iid}"
        if not isinstance(d, dict) or not _SLUG.match(str(iid)):
            out.append(f"{w}: an id (slug) and a map")
            continue
        if d.get("kind") not in INSTRUMENT_KINDS:
            out.append(f"{w}: kind {d.get('kind')!r} is none of {INSTRUMENT_KINDS}")
        if not _is_text(d.get("label")):
            out.append(f"{w}: label is a T")
        if not isinstance(d.get("unit"), str):
            out.append(f"{w}: unit is a string")
        counter = d.get("kind") == "counter"
        if counter:  # a count (EX2 §5 F4): its division is one count; its error √N ("poisson") or a number
            if d.get("division", 1) != 1:
                out.append(f"{w}: a counter's division is one count (1)")
            if d.get("error") != "poisson" and (not _num(d.get("error")) or d["error"] < 0):
                out.append(f"{w}: a counter's error is \"poisson\" (√N, one count for N = 0) or a number ≥ 0 (0: an "
                           f"exact count)")
        else:
            if not _num(d.get("division")) or not d["division"] > 0:
                out.append(f"{w}: division is a positive number")
            if d.get("error") is not None and (not _num(d["error"]) or d["error"] < 0):
                out.append(f"{w}: error is a number ≥ 0 (default: half a division)")
        if d.get("sigma") is not None:  # the run's own standard error at the cursor (EX2 §5 F4)
            if d.get("kind") != "readout":
                out.append(f"{w}: only a readout takes the run's own error (sigma)")
            elif not isinstance(d["sigma"], str) or not d["sigma"] or d["sigma"].startswith("control:"):
                out.append(f"{w}: sigma names a measurable of the world (the run's standard error of what it reads)")
            elif d.get("error") is not None:
                out.append(f"{w}: an error and a sigma: the run's own error replaces the declared one")
        if d.get("error_note") is not None and not _is_text(d["error_note"]):
            out.append(f"{w}: error_note is a T")
        if d.get("event") is not None and (not isinstance(d["event"], str) or not d["event"]):
            out.append(f"{w}: event is the kind or name of the event at which its reading stops (a string)")
        reads, manual = d.get("reads"), bool(d.get("manual"))
        if manual:
            if d.get("kind") != "stopwatch":
                out.append(f"{w}: only a stopwatch is manual")
        elif not isinstance(reads, str) or not reads:
            out.append(f"{w}: reads a measurable of the world ('range') or a set-up value ('control:<param>')")
        elif reads.startswith("control:") and (counter or d.get("sigma") is not None):
            out.append(f"{w}: a counter or a readout with the run's error reads a measurable, not a set-up value")
        elif reads.startswith("control:") and reads[8:] not in by_id and reads[8:] not in compound_ids:
            out.append(f"{w}: reads {reads!r}: no such parameter or compound control")
    steps = sc.get("steps")
    if not isinstance(steps, list) or not steps:
        out.append(f"{where}: steps: a list of the lab's parts")
        steps = []
    sids = set()
    shapes: dict = {}  # step id -> (its column ids, its plot's fits, its controls): what a sheet's variant may name
    for st in steps:
        if not isinstance(st, dict):
            out.append(f"{where}: step {st!r} is a map")
            continue
        sid = st.get("id")
        w = f"{where}: step {sid}"
        if not isinstance(sid, str) or not _SLUG.match(sid) or sid in sids:
            out.append(f"{where}: step id {sid!r}: a unique slug")
        sids.add(sid)
        for k in ("title", "goal"):
            if not _is_text(st.get(k)):
                out.append(f"{w}: {k} is a T")
        if st.get("hint") is not None and not _is_text(st["hint"]):
            out.append(f"{w}: hint is a T")
        if "atlas" in st:  # the points of an Explore screen of this world (EX2 §5 F9)
            screen = shared_screen(viz, st)
            if screen is None:
                out.append(f"{w}: atlas {st.get('atlas')!r} is no Explore screen of this world")
            own = sorted(k for k in SHARED_FIELDS if k in st)
            if own:
                out.append(f"{w}: its points are the Explore screen's: it does not declare {own}")
            if st.get("speed") is not None and st["speed"] != SPEED_WORLD \
                    and (not _num(st["speed"]) or not st["speed"] > 0):
                out.append(f"{w}: speed {st['speed']!r} is world seconds per played second (> 0) or \"world\"")
            controls = list((screen or {}).get("controls") or [])
        else:
            out += _check_atlas_common(viz, st, w, decl)
            controls = list(st.get("controls") or []) if isinstance(st.get("controls"), list) else []
        out += _check_step_view(viz, st, w, decl)
        used = st.get("instruments")
        if not isinstance(used, list) or not used or not all(u in instr for u in used):
            out.append(f"{w}: instruments {used!r}: a list of the lab's instruments")
            used = [u for u in used or [] if u in instr] if isinstance(used, list) else []
        speed = st.get("speed") if st.get("speed") is not None or "atlas" not in st \
            else (shared_screen(viz, st) or {}).get("speed")
        if any(isinstance(instr.get(u), dict) and instr[u].get("manual") for u in used) and speed is not None:
            # RULES §10: «its step declares no speed» (review R2-F F5 (b): speed 1 was let through)
            out.append(f"{w}: a manual stopwatch times the flight on the wall clock: its step plays in real time and "
                       f"declares no speed (EX2 §5 F1)")
        cols, cids = st.get("columns"), []
        if not isinstance(cols, list) or not cols:
            out.append(f"{w}: columns: a list of {{id, label, from | of + op | expr}}")
            cols = []
        all_ids = [c.get("id") for c in cols if isinstance(c, dict)]
        for c in cols:
            cid = c.get("id") if isinstance(c, dict) else None
            if not isinstance(cid, str) or not _COL.match(cid) or cid in cids:
                out.append(f"{w}: column {c!r}: a unique slug id")
                continue
            if cid in _expr.RESERVED or cid in _JS_OWN:
                out.append(f"{w}: column {cid}: the name is the formulas' own ({sorted(_expr.RESERVED)}) or a "
                           f"property every object has: choose another")
            if not _is_text(c.get("label")):
                out.append(f"{w}: column {cid}: label is a T")
            kinds = [k for k in ("from", "of", "expr") if k in c]
            if len(kinds) != 1:
                out.append(f"{w}: column {cid}: one of 'from' an instrument, 'of' an earlier column with 'op', or "
                           f"'expr' a formula of earlier columns")
            elif "from" in c:
                if c["from"] not in used:
                    out.append(f"{w}: column {cid}: from {c['from']!r} is not an instrument of the step")
            elif "expr" in c:  # a formula of earlier columns (EX2 §5 F5): parsed by the grammar of lfviz.expr
                why = _expr.check(c["expr"], cids, [x for x in all_ids if x not in cids]) \
                    if isinstance(c["expr"], str) else "a formula is a string"
                if why:
                    out.append(f"{w}: column {cid}: expr {c['expr']!r} refused: {why}")
            elif c.get("of") not in cids or c.get("op") not in COLUMN_OPS:
                out.append(f"{w}: column {cid}: 'from' an instrument, or 'of' an earlier column with 'op' one of "
                           f"{COLUMN_OPS}")
            cids.append(cid)
        plot = st.get("plot")
        fits = []
        if not isinstance(plot, dict) or plot.get("x") not in cids or plot.get("y") not in cids:
            out.append(f"{w}: plot {plot!r}: {{x, y}} name columns of the step")
        else:
            fits = plot.get("fits") or ([plot["fit"]] if plot.get("fit") else [])
            allowed = [f for f in FITS if f != "power" or viz.get("ui") != "school"]
            if plot.get("fit") is not None and plot["fit"] not in fits:
                out.append(f"{w}: plot: fit {plot['fit']!r} is not among its fits {fits}")
            for f in fits:
                if f not in allowed:
                    out.append(f"{w}: plot: fit {f!r} is none of {allowed} (power only above school)")
        out += _check_laws(viz, st, w, cids, fits)
        shapes[sid] = (list(cids), list(fits), controls)
    placed = sorted({iid for st in steps if isinstance(st, dict) for iid in st.get("instruments") or []
                     if isinstance(instr.get(iid), dict) and instr[iid].get("kind") in PLACED_KINDS})
    if placed and not (decl.get("anchors") and decl.get("worldToPx")):  # EX2 §5 F8 (STATUS V52 (l))
        out.append(f"{where}: the instruments {placed} are drawn over the view: its web/view.js defines anchors() and "
                   f"worldToPx (where the tape, the ruler and the protractor sit)")
    ws = sc.get("worksheet")
    return out + _check_task_sheet(viz, ws, shapes, where)


def _check_task_sheet(viz, ws, shapes: dict, where: str) -> list[str]:
    """Lab work's task sheet (EX2 §5 F8 (a), (b)): ``frp`` (school: the programme's lab, as EX1) or ``basis``
    (university: the course or the manual, quoted verbatim), ``goal: T``, ``bench: [T]`` (what the bench is and what can
    be set on it), ``procedure: [T]`` (one suggested procedure, not the only one), ``record: [T]`` (what to record and
    hand in), ``record_rows`` (blank rows per step, default 10), ``variants`` (the teacher's tasks computed in the
    atlases). **[error in earlier]** EX1's ``questions`` with their answers, the ``teacher``'s notes and the first EX2
    form's ``grading`` are refused: Lab work is a bench, not a test (the owner, 2026-11-18)."""
    out = []
    w = f"{where}: worksheet"
    school = viz.get("ui") == "school"
    if not isinstance(ws, dict):
        return [f"{w}: the task sheet {{frp | basis, goal, bench, procedure, record, record_rows?, variants?}}"]
    gone = sorted(k for k in ("questions", "teacher", "grading", "equipment") if k in ws)
    if gone:
        out.append(f"{w}: {gone} are gone: the task sheet has no questions, answers, teacher's pages or grading (the "
                   f"bench is open and the teacher judges; EX2 §5 F8); the equipment is the sheet's «bench»")
    extra = sorted(set(ws) - set(WORKSHEET_FIELDS) - {"questions", "teacher", "grading", "equipment"})
    if extra:
        out.append(f"{w}: unknown fields {extra} (a task sheet has {list(WORKSHEET_FIELDS)})")
    frp = ws.get("frp")
    if school and (not isinstance(frp, list) or not frp
                   or not all(isinstance(x, dict) and _is_text(x.get("name")) and _is_text(x.get("programme"))
                              for x in frp)):
        out.append(f"{w}: frp is a list of {{name: T (the programme's words), programme: T (the programme's name to "
                   f"show), …}}")
    if not school and frp is not None:
        out.append(f"{w}: a university task sheet names its basis (worksheet.basis: the course or the manual it "
                   f"follows), not a school programme (frp)")
    out += _check_basis(ws.get("basis"), not school, w)
    if not _is_text(ws.get("goal")):
        out.append(f"{w}: goal is a T (the bench's goal; each part's own goal is its step's)")
    for k in ("bench", "procedure", "record"):
        v = ws.get(k)
        if not isinstance(v, list) or not v or not all(_is_text(x) for x in v):
            out.append(f"{w}: {k} is a list of T (paragraphs)")
    rr = ws.get("record_rows", 10)
    if isinstance(rr, bool) or not isinstance(rr, int) or not 1 <= rr <= 40:
        out.append(f"{w}: record_rows {rr!r} is a whole number of blank rows, 1–40")
    out += _check_task_variants(ws.get("variants"), shapes, w, school)
    return out


def _check_task_variants(variants, shapes: dict, where: str, school: bool) -> list[str]:
    """The teacher's tasks (EX2 §5 F8 (b)): ``[{id, label: T, grade?, steps?: [step ids], values?: {<step>: {<control
    id>: value}}, text?: {goal?: T, procedure?: [T], record?: [T]}}]``: computed in the atlases (each value one of its
    control's grid values), preselected by ``&variant=<id>`` on run.html and worksheet.html (nothing locked). ``grade``
    is required at school only."""
    if variants is None:
        return []
    if not isinstance(variants, list):
        return [f"{where}: variants is a list of {{id, label, grade?, steps?, values?, text?}}"]
    out, ids = [], set()
    for v in variants:
        if not isinstance(v, dict):
            out.append(f"{where}: variant {v!r} is a map")
            continue
        vid = v.get("id")
        w = f"{where}: variant {vid!r}"
        if not isinstance(vid, str) or not _SLUG.match(vid) or vid in ids:
            out.append(f"{w}: id is a unique slug")
        ids.add(vid)
        extra = sorted(set(v) - {"id", "label", "grade", "steps", "values", "text"})
        if extra:
            out.append(f"{w}: unknown fields {extra} (a variant has id, label, grade?, steps?, values?, text?)")
        g = v.get("grade")
        if (school or g is not None) and (isinstance(g, bool) or not isinstance(g, int) or not 1 <= g <= 12):
            out.append(f"{w}: grade {g!r} is a school grade (a whole number 1–12; optional at university)")
        if not _is_text(v.get("label")):
            out.append(f"{w}: label is a T")
        steps = v.get("steps", list(shapes))
        if not isinstance(steps, list) or not steps or not all(isinstance(x, str) and x in shapes for x in steps) \
                or len(set(steps)) != len(steps):
            out.append(f"{w}: steps {steps!r}: distinct step ids of the lab ({sorted(shapes)})")
            steps = [x for x in steps if x in shapes] if isinstance(steps, list) else []
        values = v.get("values", {})
        if not isinstance(values, dict):
            out.append(f"{w}: values is a map {{step id: {{control id: value}}}}")
            values = {}
        for sid, vals in values.items():
            if sid not in steps:
                out.append(f"{w}: values name {sid!r}, not a step of the variant")
                continue
            ctl = {control_key(c): c for c in shapes[sid][2] if isinstance(c, dict)}
            if not isinstance(vals, dict):
                out.append(f"{w}: values of {sid}: a map {{control id: value}}")
                continue
            for k, x in vals.items():
                c = ctl.get(k)
                if c is None:
                    out.append(f"{w}: values of {sid}: {k!r} is no control of the step ({sorted(ctl)})")
                elif not any(type(y) is type(x) and y == x for y in c.get("values") or []) \
                        and not any(y == x and not isinstance(y, bool) and not isinstance(x, bool)
                                    for y in c.get("values") or []):
                    out.append(f"{w}: values of {sid}: {k} = {x!r} is not on its grid (a variant is computed in the "
                               f"atlas)")
        text = v.get("text", {})
        if not isinstance(text, dict) or set(text) - {"goal", "procedure", "record"}:
            out.append(f"{w}: text is a map {{goal?: T, procedure?: [T], record?: [T]}}")
        else:
            if "goal" in text and not _is_text(text["goal"]):
                out.append(f"{w}: text.goal is a T")
            for k in ("procedure", "record"):
                if k in text and (not isinstance(text[k], list) or not all(_is_text(x) for x in text[k])):
                    out.append(f"{w}: text.{k} is a list of T")
    return out


def _check_basis(basis, required: bool, where: str) -> list[str]:
    """A university worksheet's sources (EX2 §1.4, §5 F8; replaces ``frp`` at ``standard``): ``[{text: T (what the lab
    takes from it), source: the citation (a string or a T), quote?: the source's words verbatim (a string, printed in
    its language and marked as a quotation), quote_lang?: that language's code (default "en")}]``."""
    if basis is None:
        return [f"{where}: basis: [{{text: T, source, quote?}}]: the course or the manual the lab follows"] \
            if required else []
    if not isinstance(basis, list) or not basis:
        return [f"{where}: basis is a list of {{text: T, source, quote?, quote_lang?}}"]
    out = []
    for b in basis:
        if not isinstance(b, dict) or set(b) - {"text", "source", "quote", "quote_lang"}:
            out.append(f"{where}: basis {b!r}: {{text: T, source, quote?, quote_lang?}}")
            continue
        if not _is_text(b.get("text")):
            out.append(f"{where}: basis: text is a T (what the lab takes from the source)")
        src = b.get("source")
        if not (_is_text(src) or (isinstance(src, str) and src.strip())):
            out.append(f"{where}: basis: source is the citation (a string or a T)")
        q = b.get("quote")
        if q is not None and (not isinstance(q, str) or not q.strip()):
            out.append(f"{where}: basis: quote is the source's words verbatim (a string, not translated)")
        ql = b.get("quote_lang")
        if ql is not None and (not isinstance(ql, str) or not re.match(r"^[a-z]{2}$", ql)):
            out.append(f"{where}: basis: quote_lang is a language code such as \"en\"")
    return out


def check_screens(viz: dict) -> list[str]:
    """What is wrong with ``VIZ["screens"]`` (design §2.1, §2.3, §2.5). What needs the world built (the readouts and
    the instruments' measurables in its header, ``lab_reference``, a refused default point) is checked when the atlas
    is built (``site/atlas.py``)."""
    aud = viz.get("audience")
    screens = viz.get("screens")
    out = []
    if screens is None:
        screens = []
    if not isinstance(screens, list):
        return ["screens: a list of {id, kind, label?, …} in tab order"]
    if screens and aud == "playground":
        return ["a laboratory has no screens: it computes what its user builds"]
    if viz.get("lab_absent") is not None and not _is_text(viz["lab_absent"]):
        out.append("lab_absent is a T: why the programme has no lab for the topic")
    kinds = [s.get("kind") for s in screens if isinstance(s, dict)]
    if aud == "school":
        if "explore" not in kinds:
            out.append("a school world needs an Explore screen (design §2.5)")
        if "lab" not in kinds and not _is_text(viz.get("lab_absent")):
            out.append("a school world needs a Lab work screen, or lab_absent: T(why the programme has none)")
    decl = view_declarations(viz) if screens else {}
    recs = {r.get("id"): r for r in viz.get("recordings") or [] if isinstance(r, dict)}
    ids = set()
    for sc in screens:
        if not isinstance(sc, dict):
            out.append(f"screen {sc!r} is a map")
            continue
        sid, kind = sc.get("id"), sc.get("kind")
        w = f"screen {sid}"
        if not isinstance(sid, str) or not _SLUG.match(sid) or sid in ids:
            out.append(f"screen id {sid!r}: a unique slug")
        ids.add(sid)
        if kind not in SCREEN_KINDS:
            out.append(f"{w}: kind {kind!r} is none of {SCREEN_KINDS}")
            continue
        if sc.get("label") is not None and not _is_text(sc["label"]):
            out.append(f"{w}: label is a T")
        if kind == "watch":
            r = recs.get(sc.get("recording"))
            if r is None:
                out.append(f"{w}: recording {sc.get('recording')!r} is none of the world's recordings")
            elif not r.get("captions"):
                out.append(f"{w}: its recording {r.get('id')} has no captions (a Watch needs them, design §2.1)")
            more = sc.get("more") or []
            if not isinstance(more, list) or not all(m in recs for m in more):
                out.append(f"{w}: more {more!r}: ids of the world's recordings")
        elif kind == "explore":
            out += _check_atlas_common(viz, sc, w, decl)
            if sc.get("acts", "next") not in ACTS:
                out.append(f"{w}: acts {sc.get('acts')!r} is none of {ACTS}")
            if sc.get("time", "flight") not in TIMES:
                out.append(f"{w}: time {sc.get('time')!r} is none of {TIMES}")
            tr = sc.get("traces", 0)
            lo, hi = ATLAS_LIMITS["traces"]
            if not isinstance(tr, int) or isinstance(tr, bool) or not lo <= tr <= hi:
                out.append(f"{w}: traces {tr!r}: {lo}–{hi} earlier points kept")
            ov = sc.get("overlays") or []
            have = decl.get("overlays")
            if not isinstance(ov, list) or not all(isinstance(o, str) for o in ov):
                out.append(f"{w}: overlays: a list of the ids the view declares")
            elif ov and not set(ov) <= set(have or []):
                out.append(f"{w}: overlays {sorted(set(ov) - set(have or []))} are not declared by the view "
                           f"(its overlays: {have})")
            rd = sc.get("readouts") or []
            if not isinstance(rd, list) or not all(isinstance(x, str) and x for x in rd):
                out.append(f"{w}: readouts: a list of the world's measurables (ids in its header)")
        else:
            out += _check_lab(viz, sc, w, decl)
    return out


def _control(viz, c: dict) -> dict:
    if "sets" in c:  # a compound control (EX2 §5 F3): its id is the key of its value, its sets the parameters it sets
        vals = list(c["values"])
        by_id = viz["schema"].by_id
        return {"param": c["id"], "id": c["id"], "compound": True, "values": vals, "default": c.get("default", vals[0]),
                "label": c["label"], "unit": c.get("unit"), "labels": list(c["labels"]) if c.get("labels") else None,
                "sets": {k: list(v) for k, v in c["sets"].items()},
                "kind": "slider" if all(_num(v) for v in vals) else "select",
                "law": any(by_id[k].standard is not None for k in c["sets"])}
    p = viz["schema"].by_id[c["param"]]
    vals = list(c["values"])
    kind = c.get("kind") or ("toggle" if len(vals) == 2 and all(isinstance(v, bool) for v in vals)
                             else "slider" if all(_num(v) for v in vals) else "select")
    # a control's own label and unit (a T or a symbol) win over the parameter's: a schema whose label carries its unit
    # («Wavelength, nm», unit None) declares them here so the player can write «λ 600 nm»
    return {"param": p.id, "values": vals, "default": c.get("default", vals[0]), "label": c.get("label") or p.label,
            "unit": c.get("unit") or p.unit, "kind": kind, "law": p.standard is not None}


def _atlas_part(viz, sc: dict) -> dict:
    """What an Explore screen and a lab step share: the atlas's spec (``sitelib.atlas_spec_of`` keys it) and the
    screen's playback ``speed`` (EX2 §5 F1: world seconds per played second, ``"world"`` or None for 1). The clock is
    ``frame_dt`` or ``fps`` (the other None); ``drop.blobs`` only when declared, so that an atlas without it keeps its
    spec's form."""
    drop = sc.get("drop") or {}
    d = {"types": list(drop.get("types", [])), "frame_blobs": list(drop.get("frame_blobs", []))}
    if drop.get("blobs"):
        d["blobs"] = list(drop["blobs"])
    return {"preset": sc["preset"], "fixed": dict(sc.get("fixed") or {}),
            "controls": [_control(viz, c) for c in sc["controls"]], "seed": int(sc.get("seed", 1)),
            "frame_dt": float(sc["frame_dt"]) if sc.get("frame_dt") is not None else None,
            "fps": float(sc["fps"]) if sc.get("fps") is not None else None,
            "speed": sc.get("speed") if sc.get("speed") in (None, SPEED_WORLD) else float(sc["speed"]),
            "stop": dict(sc["stop"]), "drop": d, "quantize": dict(sc.get("quantize") or {})}


def screens_of(viz: dict) -> list[dict]:
    """The screens in the catalogue's form (``describe``; the player's contract, design §2, §3): every default filled
    in, every control with its label, unit, kind (slider | toggle | select) and whether it is a law parameter, each
    Explore screen and each lab step with the id of its atlas (``atlases_of``; a step on an Explore screen's atlas has
    ``shared: true``, the screen's atlas id and its spec, EX2 §5 F9); a lab step's ``laws`` (the world's computed values
    for the bench: «Computed for this bench», EX2 §5 F6 (d)), ``overlays`` and ``readouts`` are always lists; the
    worksheet is the task sheet (``record_rows`` filled in)."""
    out = []
    for sc in viz.get("screens") or []:
        kind = sc["kind"]
        d = {"id": sc["id"], "kind": kind, "label": sc.get("label") or SCREEN_LABELS[kind]}
        if kind == "watch":
            d.update(recording=sc["recording"], more=list(sc.get("more") or []))
        elif kind == "explore":
            d.update(atlas=sc["id"], **_atlas_part(viz, sc), acts=sc.get("acts", "next"),
                     time=sc.get("time", "flight"), traces=int(sc.get("traces", 0)),
                     overlays=list(sc.get("overlays") or []), readouts=list(sc.get("readouts") or []))
        else:
            instr = {}
            for iid, i in sc["instruments"].items():
                div = i.get("division", 1)
                # a counter's error is "poisson" (√N) or a number; a readout with the run's own error (sigma) has
                # error None: the run gives it at the cursor (EX2 §5 F4)
                err = i["error"] if i.get("error") is not None else (None if i.get("sigma") else div / 2)
                instr[iid] = {"kind": i["kind"], "label": i["label"], "unit": i["unit"], "division": div,
                              "error": err, "sigma": i.get("sigma"), "reads": i.get("reads"),
                              "manual": bool(i.get("manual")), "error_note": i.get("error_note"),
                              "event": i.get("event")}
            steps = []
            for st in sc["steps"]:
                screen = shared_screen(viz, st)
                if screen is not None:  # the points of an Explore screen (EX2 §5 F9): its atlas, its spec
                    part = _atlas_part(viz, screen)
                    if st.get("speed") is not None:
                        part["speed"] = st["speed"] if st["speed"] == SPEED_WORLD else float(st["speed"])
                    head = {"atlas": screen["id"], "shared": True}
                else:
                    part = _atlas_part(viz, st)
                    head = {"atlas": f"{sc['id']}.{st['id']}", "shared": False}
                s2 = {"id": st["id"], **head, "title": st["title"], "goal": st["goal"],
                      "hint": st.get("hint"), **part, "instruments": list(st["instruments"]),
                      "columns": [dict(c) for c in st["columns"]], "plot": dict(st["plot"]),
                      "laws": [dict(x) for x in st.get("laws") or []],
                      "overlays": list(st.get("overlays") or []), "readouts": list(st.get("readouts") or [])}
                s2["plot"].setdefault("fits", [s2["plot"]["fit"]] if s2["plot"].get("fit") else [])
                steps.append(s2)
            ws = dict(sc["worksheet"])
            ws.setdefault("record_rows", 10)
            d.update(instruments=instr, steps=steps, worksheet=ws)
        out.append(d)
    return out


def atlases_of(viz: dict) -> list[dict]:
    """Every atlas of a world (design §1.1, §1.4): one per Explore screen (``id`` = the screen's id) and one per lab
    step (``<screen id>.<step id>``), each ``{id, screen, step, preset, fixed, controls, seed, frame_dt, fps, speed,
    stop, drop, quantize, laws}``: what ``site/atlas.py`` computes and what its key covers (``laws``: the ids of the
    step's laws' references, in order; the manifest's ``references`` holds one per id). A lab step on an Explore
    screen's atlas (``atlas: <screen>``, EX2 §5 F9) has none of its own: the screen's atlas carries its laws as
    ``<step>/<law>`` (so the screen's key covers them)."""
    out = []
    shared: dict = {}  # an Explore screen's id -> the laws of the lab steps on its atlas, as "<step>/<law>" (EX2 §5 F9)
    for sc in viz.get("screens") or []:
        if sc["kind"] == "lab":
            for st in sc["steps"]:
                if shared_screen(viz, st) is not None:
                    shared.setdefault(st["atlas"], []).extend(f"{st['id']}/{x.get('reference')}"
                                                              for x in st.get("laws") or [])
    for sc in viz.get("screens") or []:
        if sc["kind"] == "explore":
            out.append({"id": sc["id"], "screen": sc["id"], "step": None, **_atlas_part(viz, sc),
                        "laws": list(shared.get(sc["id"], []))})
        elif sc["kind"] == "lab":
            for st in sc["steps"]:
                if shared_screen(viz, st) is not None:
                    continue  # no atlas of its own: the screen's (EX2 §5 F9)
                out.append({"id": f"{sc['id']}.{st['id']}", "screen": sc["id"], "step": st["id"],
                            **_atlas_part(viz, st), "laws": [x.get("reference") for x in st.get("laws") or []]})
    return out


# modules of the server process only (HTTP routes, the runs' bookkeeping, the live points' endpoint): no worker imports
# them, so they never change what a run computes; leaving them out keeps checkpoints and the site's recordings valid
# across server-only edits. ``atlas_live.py`` runs a point through ``site/atlas.py`` and ``headless.py`` (both in the
# recorder's hash): its own hash is in the live points' key instead (``atlas_live.point_key``; review R-F F11)
SERVER_ONLY = frozenset({"app.py", "runs.py", "atlas_live.py"})


def _shared_raw() -> list[Path]:
    """The lfviz package's and the engine's ``*.py`` (unfiltered, as listed): what every world's code hash reads."""
    return list((SERVER / "lfviz").rglob("*.py")) + list((ENGINE / "lfphys").rglob("*.py"))


def _keep(f: Path, vf: Path | None) -> bool:
    """Whether ``code_hash`` reads a listed file: not ``__pycache__``, not a server-only module, not a test (of the
    world's folder ``vf``, or of the repository; ``vf`` None: a shared file, no world's own)."""
    if "__pycache__" in f.parts or f.parent == SERVER / "lfviz" and f.name in SERVER_ONLY:
        return False
    own = vf is not None and f.is_relative_to(vf)
    # a folder's own tests are not the code a run executes (a section found through LFVIZ_EXTRA, e.g. in
    # tests/playgrounds, is: review B6-F24)
    return not (("tests" in f.relative_to(vf).parts) if own else ("tests" in f.relative_to(ROOT.parent).parts))


def _code_files(viz_id: str, shared: list[Path] | None = None) -> tuple[Path, list[Path]]:
    """The files ``code_hash`` reads, sorted: the visualization folder's ``*.py`` and ``*.js``, the lfviz package and the
    engine, without ``__pycache__``, the server-only modules and the tests (``_keep``). ``shared``: the lfviz package's
    and the engine's files already kept (``_shared_cached``), when the caller has them."""
    vf = folder(viz_id)
    if shared is None:
        files = sorted(list(vf.rglob("*.py")) + list(vf.rglob("*.js")) + _shared_raw())
        return vf, [f for f in files if _keep(f, vf)]
    own = [f for f in list(vf.rglob("*.py")) + list(vf.rglob("*.js")) if _keep(f, vf)]
    return vf, sorted(own + shared)


def _rel(f: Path, vf: Path) -> Path:
    return f.relative_to(ROOT.parent) if f.is_relative_to(ROOT.parent) else Path("extra") / vf.name / f.relative_to(vf)


def code_files(viz_id: str) -> list[Path]:
    """The files ``code_hash`` reads (``_code_files``): what a batch builder checks for a change during its build
    (``site/sitelib.check_unchanged``, review R2-F F1)."""
    return _code_files(resolve(viz_id))[1]


def code_hash(viz_id: str) -> str:
    """Hash of the code a run executes: the visualization folder, the lfviz package and the engine (no git needed)."""
    vf, files = _code_files(viz_id)
    h = hashlib.sha256()
    for f in files:
        rel = _rel(f, vf)  # a section outside engine/
        h.update(str(rel).encode())
        h.update(f.read_bytes())
    return h.hexdigest()[:12]


_CODE_HASHES: dict[str, tuple[tuple, str]] = {}
#: the shared files' listing per (lfviz, engine) roots: (its directories' mtimes, the files); trusted only while no
#: directory changed (a file added or removed changes its directory's time) and only when the directories had settled
#: before the listing (a change within one tick of the file system's clock is not hidden): STATUS V52 (af)
_SHARED_LIST: dict[tuple, tuple[dict, list]] = {}
#: the hash of the engine's files, which come first in every world's sorted list: (their signature, the sha256 state
#: after them), so that a world's hash does not read the engine again (STATUS V52 (af); the keys are the same bytes)
_ENGINE_PREFIX: dict[tuple, tuple[tuple, object]] = {}
_SETTLED_S = 2.0


def _shared_cached() -> list[Path]:
    """``_shared_raw`` without what ``code_hash`` does not read (``_keep``), listed again only when a directory of the
    lfviz package or the engine changed (or the listing could not be trusted: ``_SHARED_LIST``)."""
    import time  # noqa: PLC0415
    key = (str(SERVER), str(ENGINE))
    hit = _SHARED_LIST.get(key)
    if hit is not None:
        try:
            if all(os.stat(d).st_mtime_ns == m for d, m in hit[0].items()):
                return hit[1]
        except OSError:
            pass
    now = time.time()
    dirs: dict = {}
    for root in (SERVER / "lfviz", ENGINE / "lfphys"):
        try:
            dirs[str(root)] = os.stat(root).st_mtime_ns
            for d in root.rglob("*"):
                if d.is_dir() and "__pycache__" not in d.parts:
                    dirs[str(d)] = d.stat().st_mtime_ns
        except OSError:
            _SHARED_LIST.pop(key, None)
            return [f for f in _shared_raw() if _keep(f, None)]
    files = [f for f in _shared_raw() if _keep(f, None)]
    if all(m < (now - _SETTLED_S) * 1e9 for m in dirs.values()):
        _SHARED_LIST[key] = (dirs, files)
    else:
        _SHARED_LIST.pop(key, None)
    return files


def code_hash_current(viz_id: str) -> str:
    """``code_hash`` of a visualization as the files are now, cached by their paths, sizes and modification times: a
    file edited, added or removed while the process runs is seen at the next call (the files are listed and stat'ed,
    not read, when nothing changed). What a recording's or an atlas's key is compared with on a server, and what the
    catalogue's ``code_hash`` is («recorded with code X; this server runs Y», design of the start page §4.6); the live
    points' key (review R-F F1: a hash computed once per process named code the point's process did not run).

    STATUS V52 (af): ``/api/viz`` asked this for every world, and each listed the lfviz package and the engine again
    (about 3 ms a world) and, after an edit, read the engine again. The shared files' listing is kept while their
    directories are unchanged (``_shared_cached``), and the engine's part of the hash (its files come first in every
    world's sorted list) is kept with its files' signature (``_ENGINE_PREFIX``): the same bytes are hashed in the same
    order, so the keys are ``code_hash``'s."""
    viz_id = resolve(viz_id)
    vf, files = _code_files(viz_id, _shared_cached())
    try:
        stats = [(str(f), st.st_size, st.st_mtime_ns) for f in files for st in (f.stat(),)]
    except OSError:  # a file removed between the listing and the stat: no cache
        return code_hash(viz_id)
    sig = tuple(stats)
    hit = _CODE_HASHES.get(viz_id)
    if hit is not None and hit[0] == sig:
        return hit[1]
    eng = ENGINE / "lfphys"
    n = 0
    while n < len(files) and files[n].is_relative_to(eng):
        n += 1
    if any(f.is_relative_to(eng) for f in files[n:]) or not eng.is_relative_to(ROOT.parent):
        # the engine's files are not one run at the start, or their names depend on the world: no prefix
        h = code_hash(viz_id)
        _CODE_HASHES[viz_id] = (sig, h)
        return h
    pkey = (str(ENGINE), str(ROOT.parent))
    pre = _ENGINE_PREFIX.get(pkey)
    try:
        if pre is not None and pre[0] == sig[:n]:
            hh = pre[1].copy()
        else:
            hh = hashlib.sha256()
            for f in files[:n]:
                hh.update(str(_rel(f, vf)).encode())
                hh.update(f.read_bytes())
            _ENGINE_PREFIX[pkey] = (sig[:n], hh.copy())
        for f in files[n:]:
            hh.update(str(_rel(f, vf)).encode())
            hh.update(f.read_bytes())
    except OSError:
        return code_hash(viz_id)
    h = hh.hexdigest()[:12]
    _CODE_HASHES[viz_id] = (sig, h)
    return h


#: the former name (once per process until 2026-11-17)
code_hash_cached = code_hash_current


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
                    "seed": r.get("seed", 1), "poster": r.get("poster", 0), "script": list(r.get("script") or []),
                    "captions": list(r.get("captions") or []), "quantize": dict(r.get("quantize") or {})})
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
        "code_hash": code_hash_current(viz["id"]),
        "kind": viz.get("kind", "demo"),
        "audience": aud,
        "section": viz.get("section"),
        "ui": viz.get("ui"),
        "teaser": viz.get("teaser"),
        "related": list(viz.get("related") or []),
        "recordings": recordings_of(viz),
        "screens": screens_of(viz),
        "aliases": aliases_of(viz["id"]),
        "picture": picture(viz["id"]),
        "schema": viz["schema"].to_json(),
    }
    if viz.get("lab_absent") is not None:
        out["lab_absent"] = viz["lab_absent"]
    if aud == "school":
        out["curriculum"] = list(viz.get("curriculum") or [])
    elif aud == "university":
        out["courses"] = list(viz.get("courses") or [])
    elif aud == "research":
        out.update(question=viz.get("question"), prior_art=list(viz.get("prior_art") or []), status=viz.get("status"))
    return out
