# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Discovery of visualization folders.

A visualization is a folder ``visualizations/vNN_<slug>/`` (a prepared demonstration) or ``visualizations/pNN_<slug>/``
(a playground section, plan P15: a research sandbox; ``VIZ["kind"] == "playground"``) that is a Python package with
``viz.py`` defining ``VIZ`` (a dict: id, title, summary, purpose, schema, simulation, version[, kind, section]) and a
browser module ``web/view.js``. The folder name is the id. Contract and rules: ``visualizations/RULES.md``.
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
_NAME = re.compile(r"^[vp]\d{2}_[a-z0-9_]+$")


def roots() -> list[Path]:
    """Where visualization folders are found: ``visualizations/`` and, for tests only, the folders named in the
    environment variable ``LFVIZ_EXTRA`` (e.g. the toy playground of ``tests/playgrounds``)."""
    extra = [Path(p) for p in os.environ.get("LFVIZ_EXTRA", "").split(os.pathsep) if p.strip()]
    return [ROOT] + [p for p in extra if p.is_dir()]


def folder(viz_id: str) -> Path:
    """The folder of a visualization (KeyError when there is none)."""
    if _NAME.match(viz_id):
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
    folder(viz_id)  # KeyError when there is none
    ensure_path()
    mod = importlib.import_module(f"{viz_id}.viz")
    viz = dict(mod.VIZ)
    if viz.get("id") != viz_id:
        raise ValueError(f"{viz_id}/viz.py declares id {viz.get('id')!r}")
    viz.setdefault("kind", "playground" if viz_id.startswith("p") else "demo")
    if (viz["kind"] == "playground") != viz_id.startswith("p"):
        raise ValueError(f"{viz_id}: a playground's folder starts with p, a demonstration's with v")
    return viz


def code_hash(viz_id: str) -> str:
    """Hash of the code a run executes: the visualization folder, the lfviz package and the engine (no git needed)."""
    h = hashlib.sha256()
    vf = folder(viz_id)
    files = sorted(list(vf.rglob("*.py")) + list(vf.rglob("*.js"))
                   + list((SERVER / "lfviz").rglob("*.py")) + list((ENGINE / "lfphys").rglob("*.py")))
    for f in files:
        if "__pycache__" in f.parts:
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


def describe(viz: dict) -> dict:
    return {
        "id": viz["id"],
        "title": viz["title"],
        "summary": viz.get("summary", ""),
        "purpose": viz.get("purpose", ""),
        "version": viz.get("version", ""),
        "kind": viz.get("kind", "demo"),
        "section": viz.get("section"),
        "schema": viz["schema"].to_json(),
    }
