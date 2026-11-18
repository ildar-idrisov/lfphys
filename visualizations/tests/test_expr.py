# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The formula columns of a lab step (``lfviz.expr``; design ``lfphys/sources/explore_EX2_2026-11-18_design.md`` §5
F5, §7): the shared fixture ``player/js/tests/fixtures/expr_cases.json`` (values and both error terms against mpmath's
own derivatives, to 1e-12; the undefined values with their reasons; the refused formulas with their codes), which
``player/js/tests/expr.test.mjs`` reads too; the parser's safety (no ``eval``: a call of anything that is not a
function, an unknown name such as ``constructor`` or ``__proto__``, attribute access and bad syntax are refused); the
registry's check of a step's formula columns."""

from __future__ import annotations

import json
import math

import pytest

from lfviz import expr as E
from lfviz import registry

FIX = registry.ROOT / "player" / "js" / "tests" / "fixtures" / "expr_cases.json"
CASES = json.loads(FIX.read_text(encoding="utf-8"))


def _close(a, b, tol=1e-12, floor=1e-300):
    return a == b or abs(a - b) <= tol * max(abs(b), floor)


def _values(c):
    return {k: (v, e) for k, (v, e) in c["vars"].items()}


@pytest.mark.parametrize("c", [c for c in CASES["cases"] if not c.get("undefined")], ids=lambda c: c["expr"][:40])
def test_the_shared_fixture_values_and_both_error_terms(c):
    v, s, t1, t2 = E.evaluate(E.parse(c["expr"], columns=list(c["vars"])), _values(c))
    assert _close(v, c["value"]) and _close(t1, c["t1"]) and _close(t2, c["t2"], floor=1e-90) \
        and _close(s, c["error"]), (v, s, t1, t2, c)


@pytest.mark.parametrize("c", [c for c in CASES["cases"] if c.get("undefined")], ids=lambda c: c["expr"][:40])
def test_the_shared_fixture_undefined_values_say_why(c):
    with pytest.raises(E.Undefined) as u:
        E.evaluate(c["expr"], _values(c))
    assert u.value.reason == c["undefined"]


@pytest.mark.parametrize("c", CASES["refused"], ids=lambda c: repr(c["expr"])[:40])
def test_the_shared_fixture_refused_formulas(c):
    with pytest.raises(E.ExprError) as e:
        E.parse(c["expr"], columns=c["columns"], later=c["later"])
    assert e.value.code == c["code"]


def test_the_fixture_covers_every_function_reason_and_code():
    used = " ".join(c["expr"] for c in CASES["cases"])
    assert all(f"{fn}(" in used for fn in E.FUNCTIONS)
    assert {c["undefined"] for c in CASES["cases"] if c.get("undefined")} == set(E.REASONS)
    assert {c["code"] for c in CASES["refused"]} == set(E.CODES)
    assert len([c for c in CASES["cases"] if not c.get("undefined")]) >= 50


def test_names_in_order_and_safety():
    assert E.parse("b * a + sin(b) / pi + a").names == ("b", "a")
    for name in ("constructor", "__proto__", "__class__", "__import__", "toString"):
        ex = E.parse(f"{name} + 1")  # no column list: any name parses, and only the values given bind it
        with pytest.raises(E.Undefined):
            ex.evaluate({})
        assert ex.evaluate({name: (2.0, 0.0)})[0] == 3.0
    for bad in ("__import__('os')", "x.__class__", "().__class__", "[x for x in y]", "lambda: 1", "x if y else z"):
        with pytest.raises(E.ExprError):
            E.parse(bad, columns=["x", "y", "z"])
    src = (registry.SERVER / "lfviz" / "expr.py").read_text(encoding="utf-8")
    code = "\n".join(line.split("#", 1)[0] for line in src.splitlines())
    import re  # noqa: PLC0415
    assert not re.search(r"(?<![.\w])(eval|exec|compile|getattr|__import__)\s*\(", code)  # re.compile is a method


def test_errors_by_hand():
    v, s, t1, t2 = E.evaluate("a * b", {"a": (2.0, 0.1), "b": (3.0, 0.2)})
    assert v == 6.0 and math.isclose(s, math.hypot(0.3, 0.4), rel_tol=1e-15) and t2 == 0.0
    v, s, _t1, t2 = E.evaluate("x^2", {"x": (0.0, 0.1)})  # a stationary point keeps the second-order error
    assert v == 0.0 and math.isclose(s, math.sqrt(0.5) * 2 * 0.01, rel_tol=1e-15) and t2 > 0
    assert E.evaluate("(npp + nmm - npm - nmp) / (npp + nmm + npm + nmp)",
                      {"npp": (500, 500 ** 0.5), "nmm": (500, 500 ** 0.5), "npm": (0, 1), "nmp": (0, 1)})[0] == 1.0
    assert E.evaluate("x", {"x": {"v": 2.0, "e": 0.5}})[:2] == (2.0, 0.5)
    assert E.evaluate("x", {"x": 2.0})[:2] == (2.0, 0.0)


def test_the_check_used_by_the_registry():
    assert E.check("a + b", ["a", "b"]) is None
    assert "later_column" in E.check("a + c", ["a", "b"], ["c"])
    assert "unknown_name" in E.check("a + q", ["a", "b"], ["c"])
    assert "not_callable" in E.check("a(1)", ["a"])
