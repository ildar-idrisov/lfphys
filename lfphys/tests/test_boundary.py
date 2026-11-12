# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The boundary between engine/ and the research projects around it (owner, 2026-10-24; ../AGENTS.md §4): no file of
engine/ refers to research folders, knowledge-base items or research records, and no relative path in engine/ leads
outside engine/. Every source file carries its SPDX lines (../AGENTS.md §3 rule 8)."""

import re
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[2]  # engine/
SKIP_DIRS = {"runs", "__pycache__", ".pytest_cache", "node_modules"}
TEXT = {".py", ".js", ".mjs", ".css", ".html", ".md", ".txt", ".toml", ".yml", ".yaml", ".cff", ".lock", ""}
CODE = {".py", ".js", ".mjs", ".css", ".html"}
# markers of the research project's records (folder names, knowledge-base item IDs, research registers)
FORBIDDEN = re.compile(r"thomas_isoholonomy|relativistic_light_boundary|observer_projections|knowledge_base|"
                       r"ai_practice|PAPERS\.md|ANOMALIES\.md|LIBRARY_REQUESTS\.md|\bKB-[A-Z]+-\d+")
REL_PATH = re.compile(r"(?:\(|`|\"|')((?:\.\./)+[A-Za-z0-9_.\-/]*)")


def _files():
    me = Path(__file__).resolve()
    for p in ENGINE.rglob("*"):
        if p.is_file() and p != me and not (set(p.relative_to(ENGINE).parts) & SKIP_DIRS) and p.suffix in TEXT:
            yield p


def test_no_research_records_are_referenced():
    bad = []
    for p in _files():
        try:
            s = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for m in FORBIDDEN.finditer(s):
            bad.append(f"{p.relative_to(ENGINE)}: {m.group(0)}")
    assert not bad, bad


def _ours(p):
    """Not third-party code kept as published (visualizations/player/vendor/, checked by test_licences.py)."""
    return "vendor" not in p.relative_to(ENGINE).parts


def test_relative_paths_stay_inside_engine():
    bad = []
    for p in filter(_ours, _files()):
        try:
            s = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for m in REL_PATH.finditer(s):
            target = (p.parent / m.group(1)).resolve()
            if ENGINE not in target.parents and target != ENGINE:
                bad.append(f"{p.relative_to(ENGINE)}: {m.group(1)}")
    assert not bad, bad


def test_every_source_file_carries_its_licence_lines():
    # review folders are kept as delivered (reviews/README.md): their scripts are not edited
    spdx = "SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0"
    missing = [str(p.relative_to(ENGINE)) for p in filter(_ours, _files())
               if p.suffix in CODE and p.relative_to(ENGINE).parts[0] != "reviews"
               and spdx not in p.read_text(encoding="utf-8")[:400]]
    assert not missing, missing
    for name in ("LICENSE.md", "LICENSE-DOCS.txt", "NOTICE", "COMMERCIAL.md", "CITATION.cff", "CONTRIBUTING.md",
                 "CLA.md", "PUBLICATIONS.md"):
        assert (ENGINE / name).is_file(), name
