# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The engine's user-facing texts are translatable (owner, 2026-11-12: «для всего фронта сделай i18n переводы на русский
и английский, по дефолту английский и переключением языка»; AGENTS.md §3 rule 13).

Every ``T("...")`` of the engine has a literal English msgid whose placeholders are exactly the arguments passed, and an
entry in the engine's Russian catalogue ``lfphys/locales/ru.json`` with the same placeholders; the catalogue has no
entries the code does not use; no string literal of the engine's code (docstrings aside) is Russian.
"""

import ast
import io
import json
import re
import tokenize
from pathlib import Path

import pytest

from lfphys.i18n import T, render

PKG = Path(__file__).resolve().parents[1] / "lfphys"
CATALOGUE = PKG / "locales" / "ru.json"
PH = re.compile(r"\{(\w+)(?::([^{}]*))?\}")
SPEC = re.compile(r"^(\+?(\.\d+[gfe]|d)|cap|unit)?$")  # the formats the player renders (lfphys.i18n)
CYR = re.compile("[А-Яа-яЁё]")
FILES = sorted(p for p in PKG.rglob("*.py") if p.name != "i18n.py")  # i18n.py: the mechanism itself


def _placeholders(text: str) -> set[tuple[str, str]]:
    return {(m.group(1), m.group(2) or "") for m in PH.finditer(text)}


def _calls():
    """(file, line, msgid or None, keyword names or None) of every call of ``T``."""
    out = []
    for path in FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            if not ((isinstance(f, ast.Name) and f.id == "T") or (isinstance(f, ast.Attribute) and f.attr == "T")):
                continue
            where = f"{path.relative_to(PKG)}:{node.lineno}"
            arg = node.args[0] if node.args else None
            msgid = arg.value if isinstance(arg, ast.Constant) and isinstance(arg.value, str) else None
            kws = None if any(k.arg is None for k in node.keywords) else {k.arg for k in node.keywords}
            out.append((where, msgid, kws, len(node.args)))
    return out


CALLS = _calls()


def _catalogue() -> dict:
    return json.loads(CATALOGUE.read_text(encoding="utf-8"))


def test_every_msgid_is_a_literal_with_matching_arguments():
    bad = []
    for where, msgid, kws, nargs in CALLS:
        if msgid is None and nargs == 1 and kws == set():
            continue  # T(x): a text rebuilt from its JSON form (lfphys.i18n.T)
        if msgid is None or nargs != 1:
            bad.append(f"{where}: the msgid must be one string literal")
            continue
        names = {n for n, _ in _placeholders(msgid)}
        for n, spec in _placeholders(msgid):
            if not SPEC.match(spec):
                bad.append(f"{where}: placeholder {{{n}:{spec}}} has a format the player does not render")
        if kws is not None and names != kws:
            bad.append(f"{where}: placeholders {sorted(names)} but arguments {sorted(kws)}")
    assert not bad, "\n".join(bad)


def test_every_msgid_has_a_russian_entry_with_the_same_placeholders():
    cat = _catalogue()
    missing, wrong = [], []
    for where, msgid, _, _ in CALLS:
        if msgid is None:
            continue
        if msgid not in cat:
            missing.append(f"{where}: {msgid!r}")
            continue
        tr = cat[msgid]
        forms = list(tr.values()) if isinstance(tr, dict) else [tr]
        for form in forms:
            if not isinstance(form, str) or not form.strip():
                wrong.append(f"{msgid!r}: empty or not a text")
            elif _placeholders(form) != _placeholders(msgid):
                wrong.append(f"{msgid!r}: ru placeholders {sorted(_placeholders(form))} != "
                             f"{sorted(_placeholders(msgid))}")
    assert not missing, "no Russian entry:\n" + "\n".join(missing)
    assert not wrong, "\n".join(wrong)


def test_the_catalogue_has_no_unused_entries_and_is_sorted():
    cat = _catalogue()
    used = {m for _, m, _, _ in CALLS if m is not None}
    unused = sorted(set(cat) - used)
    assert not unused, "entries no code uses:\n" + "\n".join(map(repr, unused))
    assert list(cat) == sorted(cat), "the catalogue's keys must be sorted"
    assert not [k for k in cat if CYR.search(k)], "a msgid is the English source text"


def _docstring_ids(tree) -> set[int]:
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                out.add(first.value.lineno)
    return out


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(PKG)))
def test_no_russian_string_literals_in_the_code(path):
    """Russian lives in the catalogue; the code's string literals are English (docstrings may quote the owner)."""
    src = path.read_text(encoding="utf-8")
    docs = _docstring_ids(ast.parse(src))
    bad = [f"{tok.start[0]}: {tok.string[:80]}" for tok in tokenize.generate_tokens(io.StringIO(src).readline)
           if tok.type == tokenize.STRING and CYR.search(tok.string) and tok.start[0] not in docs]
    assert not bad, "\n".join(bad)


def test_render_through_the_catalogue(ru):
    t = T("{a}; {b}", a=T("{a}; {b}", a="x", b=1.5), b=2)
    assert str(t) == "x; 1.5; 2" and render(t) == "x; 1.5; 2"
    assert ru(t) == "x; 1.5; 2"
    from lfphys.core import relativity
    assert ru(relativity.ABOUT["title"]) == "Специальная теория относительности"
    assert str(relativity.ABOUT["title"]) == "Special relativity"


def _shadowing(path: Path) -> list[str]:
    """Functions that make ``T`` a local name (a parameter, an assignment, a loop variable) and also call ``T(...)``:
    the call would then hit the local (UnboundLocalError or a call of an array)."""
    out = []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        a = fn.args
        local = any(x.arg == "T" for x in a.posonlyargs + a.args + a.kwonlyargs + [a.vararg, a.kwarg] if x)
        calls = False
        body = fn.body if isinstance(fn.body, list) else [fn.body]
        stack = list(body)
        while stack:  # this function's own scope, not nested functions
            n = stack.pop()
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                continue
            if isinstance(n, ast.Name) and n.id == "T" and isinstance(n.ctx, ast.Store):
                local = True
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "T":
                calls = True
            stack.extend(ast.iter_child_nodes(n))
        if local and calls:
            out.append(f"{path.relative_to(PKG)}:{fn.lineno}")
    return out


def test_no_function_shadows_T():
    bad = [w for p in FILES for w in _shadowing(p)]
    assert not bad, "a local named T hides lfphys.i18n.T:\n" + "\n".join(bad)
