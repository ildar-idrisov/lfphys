# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The formula columns of a lab step (design ``lfphys/sources/explore_EX2_2026-11-18_design.md`` §5 F5): a column
``{id, label, expr}`` is a formula of the step's earlier columns, evaluated on each row with its error propagated.
``player/js/expr.js`` is the same grammar and the same arithmetic, operation for operation; the shared fixture
``player/js/tests/fixtures/expr_cases.json`` (made by ``make_expr_cases.py`` with mpmath's derivatives) holds both to
1e-12. The registry parses every formula of the registry (``registry._check_lab``: it names earlier columns only); this
module evaluates for the tests and for the worksheets' answers. There is no ``eval``: a small parser of this grammar
only, and the formulas come from the registry, never from a viewer.

Grammar (whitespace between tokens is free)::

    expr    := term (("+" | "-") term)*
    term    := unary (("*" | "/") unary)*
    unary   := ("-" | "+") unary | power
    power   := primary ("^" unary)?             # right-associative; -2^2 = -(2^2); 2^-1 = 0.5
    primary := number | "pi" | column | function "(" expr ")" | "(" expr ")"
    number  := digits ["." digits] [("e" | "E") ["+" | "-"] digits]  |  "." digits [exponent]

``function`` is one of ``FUNCTIONS``: ``sqrt ln exp abs``, ``sin cos tan asin acos atan`` (radians) and ``sind cosd
tand asind acosd atand`` (degrees). A name is a column of the step (an earlier one: the registry refuses a later one),
``pi``, or a function before its parenthesis; anything else is refused (``ExprError`` with a ``code``): an unknown name
(``constructor`` and ``__proto__`` too), a call of anything that is not a function, a function without its argument,
a number too large, a character outside the grammar, a formula longer than ``MAX_CHARS`` or nested deeper than
``MAX_DEPTH``.

The error (EX1's rule for one variable, extended to independent inputs): σ_f² = Σᵢ (∂f/∂xᵢ · σᵢ)² + ½ Σᵢ (∂²f/∂xᵢ²)²
σᵢ⁴, over the formula's distinct columns in the order of their first appearance, each derivative exact (to rounding) by
hyper-dual numbers ``a + b·ε₁ + c·ε₂ + d·ε₁ε₂`` with ε₁² = ε₂² = 0: the input xᵢ is ``(xᵢ, 1, 1, 0)`` and the others
are constants, so the result's ``b`` is ∂f/∂xᵢ and its ``d`` is ∂²f/∂xᵢ². Never finite differences. An input with σ = 0
(an exact set-up) adds nothing. ``evaluate`` returns ``(value, sigma, t1, t2)``: t1 = Σ(∂f/∂xᵢ·σᵢ)² and t2 =
½Σ(∂²f/∂xᵢ²)²σᵢ⁴ (the fixture's «both error terms»).

An undefined value raises ``Undefined`` with its reason (``REASONS``): √ of a negative number, a division by zero, the
logarithm of a number ≤ 0, asin or acos outside [−1, 1], a power of a negative number with a non-whole exponent (or of 0
with a negative one, or a variable exponent of a number ≤ 0), a value that is not finite, an input that is empty, or an
error that is not finite (an infinite derivative, e.g. √R at R = 0 with σ_R > 0). The lab leaves such a cell empty with
the reason.
"""

from __future__ import annotations

import math
import re
from typing import Iterable, Mapping

#: the functions of the grammar: (value, first derivative, second derivative) are computed in ``_apply``
FUNCTIONS = ("sqrt", "ln", "exp", "abs", "sin", "cos", "tan", "asin", "acos", "atan",
             "sind", "cosd", "tand", "asind", "acosd", "atand")
CONSTANTS = {"pi": math.pi}
#: names a column may not take (they are the grammar's own)
RESERVED = frozenset(FUNCTIONS) | frozenset(CONSTANTS)
MAX_CHARS = 400
MAX_DEPTH = 48
#: why a formula is refused (``ExprError.code``)
CODES = ("syntax", "number", "unknown_name", "later_column", "not_callable", "no_argument", "too_long", "too_deep",
         "empty")
#: why a value is undefined (``Undefined.reason``)
REASONS = ("sqrt_negative", "division_by_zero", "log_nonpositive", "asin_domain", "acos_domain", "power",
           "not_finite", "missing", "error_undefined")

_TOKEN = re.compile(r"\s*(?:(?P<num>(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)|(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
                    r"|(?P<op>[-+*/^()]))")
_DEG = math.pi / 180.0
_RAD = 180.0 / math.pi
_NAN = float("nan")


class ExprError(ValueError):
    """A formula the grammar refuses: ``code`` (``CODES``), ``pos`` (the character), ``name`` (the name concerned)."""

    def __init__(self, code: str, pos: int = 0, name: str | None = None, text: str = ""):
        self.code, self.pos, self.name = code, pos, name
        super().__init__(f"{code} at {pos}" + (f" ({name})" if name else "") + (f": {text}" if text else ""))


class Undefined(ArithmeticError):
    """A value the formula does not define at these inputs: ``reason`` (``REASONS``)."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


# --- the parser ------------------------------------------------------------------------------------------------------
def _tokens(text: str) -> list[tuple[str, object, int]]:
    out, i, n = [], 0, len(text)
    while i < n:
        if text[i].isspace():
            i += 1
            continue
        m = _TOKEN.match(text, i)
        if not m or m.end() == i:
            raise ExprError("syntax", i, text=f"unexpected character {text[i]!r}")
        pos = m.start(m.lastgroup)
        if m.lastgroup == "num":
            v = float(m.group("num"))
            if not math.isfinite(v):
                raise ExprError("number", pos, text="a number too large")
            out.append(("num", v, pos))
        elif m.lastgroup == "name":
            out.append(("name", m.group("name"), pos))
        else:
            out.append(("op", m.group("op"), pos))
        i = m.end()
    out.append(("end", None, n))
    return out


class _Parser:
    def __init__(self, text: str, columns, later):
        self.toks = _tokens(text)
        self.k = 0
        self.columns = None if columns is None else set(columns)
        self.later = set(later or ())
        self.names: list[str] = []

    def peek(self):
        return self.toks[self.k]

    def take(self):
        t = self.toks[self.k]
        self.k += 1
        return t

    def is_op(self, ch):
        t = self.peek()
        return t[0] == "op" and t[1] == ch

    def expect(self, ch):
        t = self.take()
        if t[0] != "op" or t[1] != ch:
            raise ExprError("syntax", t[2], text=f"{ch!r} expected")

    def expr(self, depth):
        if depth > MAX_DEPTH:
            raise ExprError("too_deep", self.peek()[2])
        node = self.term(depth)
        while self.is_op("+") or self.is_op("-"):
            op = self.take()[1]
            node = ("bin", op, node, self.term(depth))
        return node

    def term(self, depth):
        node = self.unary(depth)
        while self.is_op("*") or self.is_op("/"):
            op = self.take()[1]
            node = ("bin", op, node, self.unary(depth))
        return node

    def unary(self, depth):
        if depth > MAX_DEPTH:
            raise ExprError("too_deep", self.peek()[2])
        if self.is_op("-"):
            self.take()
            return ("neg", self.unary(depth + 1))
        if self.is_op("+"):
            self.take()
            return self.unary(depth + 1)
        return self.power(depth)

    def power(self, depth):
        base = self.primary(depth)
        if self.is_op("^"):
            self.take()
            return ("bin", "^", base, self.unary(depth + 1))
        return base

    def primary(self, depth):
        kind, val, pos = self.take()
        if kind == "num":
            return ("num", val)
        if kind == "op" and val == "(":
            node = self.expr(depth + 1)
            self.expect(")")
            return node
        if kind == "name":
            call = self.is_op("(")
            if val in FUNCTIONS:
                if not call:
                    raise ExprError("no_argument", pos, val, "a function needs its argument in parentheses")
                self.take()
                arg = self.expr(depth + 1)
                self.expect(")")
                return ("call", val, arg)
            if call:
                raise ExprError("not_callable", pos, val, "only the grammar's functions can be called")
            if val in CONSTANTS:
                return ("num", CONSTANTS[val])
            if val in self.later:
                raise ExprError("later_column", pos, val, "a formula names earlier columns only")
            if self.columns is not None and val not in self.columns:
                raise ExprError("unknown_name", pos, val)
            if val not in self.names:
                self.names.append(val)
            return ("var", val)
        if kind == "end":
            raise ExprError("syntax", pos, text="the formula ends too early")
        raise ExprError("syntax", pos, text=f"{val!r} unexpected")


class Expr:
    """A parsed formula: ``text``, ``node`` (the tree) and ``names`` (its distinct columns, in the order of their first
    appearance)."""

    def __init__(self, text: str, node, names):
        self.text, self.node, self.names = text, node, tuple(names)

    def evaluate(self, values: Mapping[str, object]) -> tuple[float, float, float, float]:
        return evaluate(self, values)

    def __repr__(self):
        return f"Expr({self.text!r})"


def parse(text: str, columns: Iterable[str] | None = None, later: Iterable[str] = ()) -> Expr:
    """A formula parsed (``ExprError`` when the grammar refuses it). ``columns``: the names it may use (the step's
    earlier columns; None: any name but the grammar's own); ``later``: the step's later columns (named in the refusal)."""
    if not isinstance(text, str):
        raise ExprError("syntax", 0, text="a formula is a string")
    if len(text) > MAX_CHARS:
        raise ExprError("too_long", MAX_CHARS)
    if not text.strip():
        raise ExprError("empty", 0)
    p = _Parser(text, columns, later)
    node = p.expr(0)
    t = p.peek()
    if t[0] != "end":
        raise ExprError("syntax", t[2], text=f"{t[1]!r} unexpected")
    return Expr(text, node, p.names)


# --- hyper-dual arithmetic (a, b, c, d) = a + b·ε₁ + c·ε₂ + d·ε₁ε₂ -----------------------------------------------------
def _chain(x, f0, f1, f2):
    """g(x) for a function g with g(a) = f0, g′(a) = f1, g″(a) = f2; a constant x stays a constant (an infinite or
    undefined derivative of a part that does not depend on the input does not spoil the input's own derivative)."""
    if x[1] == 0.0 and x[2] == 0.0 and x[3] == 0.0:
        return (f0, 0.0, 0.0, 0.0)
    return (f0, f1 * x[1], f1 * x[2], f1 * x[3] + f2 * x[1] * x[2])


def _const(x) -> bool:
    return x[1] == 0.0 and x[2] == 0.0 and x[3] == 0.0


def _div(x, y):
    if y[0] == 0.0:
        raise Undefined("division_by_zero")
    q = x[0] / y[0]
    qb = (x[1] - q * y[1]) / y[0]
    qc = (x[2] - q * y[2]) / y[0]
    qd = (x[3] - q * y[3] - qb * y[2] - qc * y[1]) / y[0]
    return (q, qb, qc, qd)


def _q(n: float, d: float) -> float:
    """n / d as IEEE gives it (Python raises on a zero divisor; JavaScript does not): ±inf, or NaN for 0 / 0."""
    if d == 0.0:
        return _NAN if n == 0.0 or n != n else math.copysign(math.inf, n) * math.copysign(1.0, d)
    return n / d


def _pw(a: float, e: float) -> float:
    """a ** e as IEEE gives it (an overflow is inf, 0 ** negative is inf), for a ≥ 0 or a whole e."""
    if a == 0.0 and e < 0:
        return math.inf
    try:
        return a ** e
    except OverflowError:
        return math.inf


def _whole(e: float) -> bool:
    return math.isfinite(e) and e == math.floor(e)


def _pow(x, y):
    if _const(y):
        p = y[0]
        if x[0] < 0.0 and not _whole(p):
            raise Undefined("power")
        if x[0] == 0.0 and p < 0.0:
            raise Undefined("division_by_zero")
        if _const(x):
            return (_pw(x[0], p), 0.0, 0.0, 0.0)
        if p == 0.0:
            return (1.0, 0.0, 0.0, 0.0)
        if p == 1.0:
            return x
        f0 = _pw(x[0], p)
        f1 = p * _pw(x[0], p - 1.0) if x[0] != 0.0 or p >= 1.0 else _NAN
        f2 = p * (p - 1.0) * _pw(x[0], p - 2.0) if x[0] != 0.0 or p >= 2.0 else _NAN
        return _chain(x, f0, f1, f2)
    if x[0] <= 0.0:
        raise Undefined("power")
    return _apply("exp", _mul(y, _apply("ln", x)))


def _mul(x, y):
    return (x[0] * y[0], x[0] * y[1] + x[1] * y[0], x[0] * y[2] + x[2] * y[0],
            x[0] * y[3] + x[1] * y[2] + x[2] * y[1] + x[3] * y[0])


def _scale(x, k):
    return (x[0] * k, x[1] * k, x[2] * k, x[3] * k)


def _exp(a: float) -> float:
    try:
        return math.exp(a)
    except OverflowError:
        return math.inf


def _apply(fn: str, x):
    a = x[0]
    if fn == "sqrt":
        if a < 0.0:
            raise Undefined("sqrt_negative")
        r = math.sqrt(a)
        if a == 0.0:
            return _chain(x, 0.0, _NAN, _NAN)
        return _chain(x, r, _q(0.5, r), _q(-0.25, a * r))
    if fn == "ln":
        if a <= 0.0:
            raise Undefined("log_nonpositive")
        return _chain(x, math.log(a), _q(1.0, a), _q(-1.0, a * a))
    if fn == "exp":
        e = _exp(a)
        return _chain(x, e, e, e)
    if fn == "abs":
        return (-x[0], -x[1], -x[2], -x[3]) if a < 0.0 else x
    if fn == "sin":
        s, c = math.sin(a), math.cos(a)
        return _chain(x, s, c, -s)
    if fn == "cos":
        s, c = math.sin(a), math.cos(a)
        return _chain(x, c, -s, -c)
    if fn == "tan":
        tn = math.tan(a)
        sec2 = 1.0 + tn * tn
        return _chain(x, tn, sec2, 2.0 * tn * sec2)
    if fn in ("asin", "acos"):
        if not -1.0 <= a <= 1.0:
            raise Undefined(f"{fn}_domain")
        v = math.asin(a) if fn == "asin" else math.acos(a)
        if a in (-1.0, 1.0):
            return _chain(x, v, _NAN, _NAN)
        s = 1.0 - a * a
        r = math.sqrt(s)
        k = 1.0 if fn == "asin" else -1.0
        return _chain(x, v, _q(k, r), _q(k * a, s * r))
    if fn == "atan":
        s = 1.0 + a * a
        return _chain(x, math.atan(a), _q(1.0, s), _q(-2.0 * a, s * s))
    if fn in ("sind", "cosd", "tand"):
        return _apply(fn[:-1], _scale(x, _DEG))
    if fn in ("asind", "acosd", "atand"):
        return _scale(_apply(fn[:-1], x), _RAD)
    raise Undefined("not_finite")  # unreachable: the parser admits the grammar's functions only


def _eval(node, env):
    kind = node[0]
    if kind == "num":
        return (node[1], 0.0, 0.0, 0.0)
    if kind == "var":
        return env[node[1]]
    if kind == "neg":
        x = _eval(node[1], env)
        return (-x[0], -x[1], -x[2], -x[3])
    if kind == "call":
        return _apply(node[1], _eval(node[2], env))
    op, a, b = node[1], _eval(node[2], env), _eval(node[3], env)
    if op == "+":
        return (a[0] + b[0], a[1] + b[1], a[2] + b[2], a[3] + b[3])
    if op == "-":
        return (a[0] - b[0], a[1] - b[1], a[2] - b[2], a[3] - b[3])
    if op == "*":
        return _mul(a, b)
    if op == "/":
        return _div(a, b)
    return _pow(a, b)


def _pair(x) -> tuple[float | None, float]:
    """An input as ``(value, sigma)``: a pair, a ``{v, e}`` map, or a plain number (σ 0); None: empty."""
    if x is None:
        return None, 0.0
    if isinstance(x, Mapping):
        v, e = x.get("v"), x.get("e", 0.0)
    elif isinstance(x, (tuple, list)):
        v, e = (x[0], x[1] if len(x) > 1 else 0.0)
    else:
        v, e = x, 0.0
    return (None if v is None else float(v)), float(e if e is not None else _NAN)


def evaluate(expr: Expr | str, values: Mapping[str, object]) -> tuple[float, float, float, float]:
    """The formula's value and error at ``values`` (``{column: (v, σ) | {v, e} | v}``): ``(value, sigma, t1, t2)``
    (the module's docstring). Raises ``Undefined`` (its reason) or ``ExprError`` (a string that does not parse)."""
    if isinstance(expr, str):
        expr = parse(expr)
    env, sig = {}, {}
    for name in expr.names:
        v, e = _pair(values.get(name))
        if v is None or not math.isfinite(v):
            raise Undefined("missing")
        env[name] = (v, 0.0, 0.0, 0.0)
        sig[name] = e
    value = _eval(expr.node, env)[0]
    if not math.isfinite(value):
        raise Undefined("not_finite")
    t1 = t2 = 0.0
    for name in expr.names:
        s = sig[name]
        if s == 0.0:
            continue  # an exact input adds nothing (and an infinite derivative times 0 is no error)
        if not math.isfinite(s) or s < 0.0:
            raise Undefined("error_undefined")
        v = env[name][0]
        env[name] = (v, 1.0, 1.0, 0.0)
        r = _eval(expr.node, env)
        env[name] = (v, 0.0, 0.0, 0.0)
        a = r[1] * s
        b = r[3] * s * s
        t1 += a * a
        t2 += 0.5 * b * b
    err = math.sqrt(t1 + t2) if math.isfinite(t1 + t2) else _NAN
    if not math.isfinite(err):
        raise Undefined("error_undefined")
    return value, err, t1, t2


def check(text: str, earlier: Iterable[str], later: Iterable[str] = ()) -> str | None:
    """Why the registry refuses a formula column (English, for its problems list), or None."""
    try:
        parse(text, columns=list(earlier), later=later)
    except ExprError as e:
        return str(e)
    return None
