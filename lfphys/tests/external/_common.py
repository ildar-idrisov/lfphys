# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Shared pieces of the comparison suite (plan item P13): the result row, and a running error bound for float64
evaluations.

Row: one comparison (quantity, inputs, the engine's value, the library's value, |difference|, tolerance and how the
tolerance was derived). The test modules build their rows once; the tests assert ``diff <= tol`` row by row and
``make_results.py`` writes the same rows into RESULTS.md. Where an exact reference exists (a closed form evaluated in
high precision for the same binary64 inputs), ``eng_err`` and ``lib_err`` give each side's distance to it: that is how
a disagreement is attributed to one side.

Fe ("float with error"): first-order running error analysis (Wilkinson; Higham, Accuracy and Stability of Numerical
Algorithms, 2nd ed., section 3.3). A value carries an absolute bound of its accumulated rounding error; each operation
propagates the input bounds with the partial derivatives and adds the bound of its own rounding:
  x +- y: e = ex + ey + u |z|          (real and complex: Higham, Lemma 3.5)
  x * y:  e = |y| ex + |x| ey + c u |z|   (c = 1 real, sqrt 5 complex: Brent, Percival, Zimmermann 2007)
  x / y:  e = ex / |y| + |z| ey / |y| + c u |z|   (c = 1 real, 6 >= sqrt 2 gamma_4 / u complex: Higham, Lemma 3.5)
  sqrt:   e = min(ex / (2 sqrt x), sqrt(ex)) + u |z|  (IEEE 754: correctly rounded; sqrt(ex) bounds the propagated
          error for any size of it, which matters where x -> 0)
  x ** n, exp, log, log1p, sin, cos, sinh, acos (libm): e = |f'(x)| ex + 2 u |z|  (an error of at most one ulp)
  x ** p (p a binary64 approximation of a simple fraction, e.g. 1.0/3.0): the term |z ln x| |p - p_exact| is added, so
     the bound is the distance to the formula with the exact exponent.
u = 2^-53. Plain Python numbers mixed in are exact inputs. The bound is first order in u (terms O(u^2) are dropped);
it is evaluated along the actual sequence of operations of the code under test: the engine's functions are run with
their module's ``math`` replaced by ``FMATH`` below, a library's pure-Python functions are called with Fe arguments,
and the test checks that the Fe value equals the float result bit for bit (the same operations were bounded).
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass, field
from fractions import Fraction
from types import SimpleNamespace

import numpy as np

U = 2.0 ** -53  # unit round-off of binary64


def gamma(n: int) -> float:
    """gamma_n = n u / (1 - n u) (Higham, Lemma 3.1): the bound of n successive relative roundings."""
    return n * U / (1.0 - n * U)


# --- result rows ----------------------------------------------------------------------------------------------------


@dataclass
class Row:
    group: str
    quantity: str
    inputs: str
    engine: object
    library: object
    tol: float
    basis: str  # short key of the tolerance derivation (explained in the module docstring and README)
    eng_err: float | None = None  # |engine - exact| where an exact reference exists
    lib_err: float | None = None  # |library - exact|
    xfail: str | None = None  # reason for a known, measured disagreement (strict xfail)
    diff: float = field(init=False)

    def __post_init__(self):
        self.diff = float(abs(complex(self.engine) - complex(self.library)))

    @property
    def ok(self) -> bool:
        return bool(self.diff <= self.tol)

    @property
    def ident(self) -> str:
        return f"{self.quantity}[{self.inputs}]"

    def message(self) -> str:
        extra = ""
        if self.eng_err is not None:
            extra = f"; |engine - exact| = {self.eng_err:.3e}, |library - exact| = {self.lib_err:.3e}"
        return (f"{self.group}: {self.quantity} at {self.inputs}: engine {fmt(self.engine)}, library "
                f"{fmt(self.library)}, |diff| = {self.diff:.3e} > tol {self.tol:.3e} ({self.basis}){extra}")


def fmt(x) -> str:
    if isinstance(x, (complex, np.complexfloating)):
        x = complex(x)
        if x.imag == 0:
            return f"{x.real:.17g}"
        return f"{x.real:.17g}{x.imag:+.17g}j"
    return f"{float(x):.17g}"


def params(rows):
    """pytest parameters: one per row, xfail(strict=True) where a row records a known disagreement."""
    import pytest
    out = []
    for r in rows:
        marks = [pytest.mark.xfail(strict=True, reason=r.xfail)] if r.xfail else []
        out.append(pytest.param(r, id=r.ident, marks=marks))
    return out


def check(row: Row):
    assert row.ok, row.message()


# --- running error bound --------------------------------------------------------------------------------------------


def _is_c(z) -> bool:
    return isinstance(z, complex) or (isinstance(z, np.complexfloating))


def _v(x):
    return x.v if isinstance(x, Fe) else x


def _e(x) -> float:
    return x.e if isinstance(x, Fe) else 0.0


class Fe:
    """A binary64 value (float or complex) with a first-order bound ``e`` of its accumulated rounding error."""

    __slots__ = ("v", "e")

    def __init__(self, v, e: float = 0.0):
        self.v = v
        self.e = float(e)

    def __repr__(self):
        return f"Fe({self.v!r}, {self.e:.3g})"

    # arithmetic
    def __add__(self, o):
        z = self.v + _v(o)
        return Fe(z, self.e + _e(o) + U * abs(z))

    __radd__ = __add__

    def __sub__(self, o):
        z = self.v - _v(o)
        return Fe(z, self.e + _e(o) + U * abs(z))

    def __rsub__(self, o):
        z = _v(o) - self.v
        return Fe(z, self.e + _e(o) + U * abs(z))

    def __mul__(self, o):
        z = self.v * _v(o)
        return Fe(z, abs(_v(o)) * self.e + abs(self.v) * _e(o) + (math.sqrt(5) if _is_c(z) else 1.0) * U * abs(z))

    __rmul__ = __mul__

    def __truediv__(self, o):
        y = _v(o)
        z = self.v / y
        return Fe(z, self.e / abs(y) + abs(z) * _e(o) / abs(y) + (6.0 if _is_c(z) else 1.0) * U * abs(z))

    def __rtruediv__(self, o):
        x = _v(o)
        z = x / self.v
        return Fe(z, _e(o) / abs(self.v) + abs(z) * self.e / abs(self.v) + (6.0 if _is_c(z) else 1.0) * U * abs(z))

    def __neg__(self):
        return Fe(-self.v, self.e)

    def __pos__(self):
        return self

    def __abs__(self):
        return Fe(abs(self.v), self.e)

    def __pow__(self, p):
        if isinstance(p, Fe):
            raise TypeError("Fe ** Fe is not needed here")
        x = self.v
        z = x ** p
        if float(p) == int(p):  # integer power: pow() with an error of at most one ulp
            n = int(p)
            der = abs(n * x ** (n - 1)) if n != 0 else 0.0
            return Fe(z, der * self.e + 2 * U * abs(z))
        der = abs(p * z / x) if x != 0 else math.inf
        exact = Fraction(float(p)).limit_denominator(64)
        rep = abs(Fraction(float(p)) - exact)  # the exponent itself is a rounded fraction
        log_term = abs(z * math.log(x)) * float(rep) if x > 0 else 0.0
        return Fe(z, der * self.e + 2 * U * abs(z) + log_term)

    # comparisons by value (control flow of the code under test must not depend on the bound)
    def __lt__(self, o):
        return self.v < _v(o)

    def __le__(self, o):
        return self.v <= _v(o)

    def __gt__(self, o):
        return self.v > _v(o)

    def __ge__(self, o):
        return self.v >= _v(o)

    def __eq__(self, o):
        return self.v == _v(o)

    def __ne__(self, o):
        return self.v != _v(o)

    __hash__ = None

    def __float__(self):  # deliberately unsupported: a silent conversion would drop the bound
        raise TypeError("Fe used where a plain float is required: that path is not bounded")

    # numpy object-array ufuncs call these methods
    def sqrt(self):
        return FMATH.sqrt(self)

    @property
    def real(self):
        return Fe(self.v.real, self.e)

    @property
    def imag(self):
        return Fe(self.v.imag, self.e)

    def conjugate(self):
        return Fe(self.v.conjugate(), self.e)


def _lib1(f, d):
    """A one-argument libm function with an error of at most one ulp; d(x, z) = |f'(x)|."""
    def g(x):
        if not isinstance(x, Fe):
            return f(x)
        z = f(x.v)
        return Fe(z, d(x.v, z) * x.e + 2 * U * abs(z))
    return g


def _sqrt(x):
    """sqrt with the propagated part min(e/(2 sqrt x), sqrt(e)): the first-order term, and the bound
    |sqrt(x + d) - sqrt(x)| <= sqrt(|d|) that holds for any d (needed where x -> 0, e.g. r_isco at chi = 0)."""
    if not isinstance(x, Fe):
        return math.sqrt(x)
    z = math.sqrt(x.v)
    prop = 0.0 if x.e == 0 else (min(x.e / (2 * z), math.sqrt(x.e)) if z > 0 else math.sqrt(x.e))
    return Fe(z, prop + U * z)


def _csqrt(x):
    if not isinstance(x, Fe):
        return cmath.sqrt(x)
    z = cmath.sqrt(x.v)
    return Fe(z, (x.e / (2 * abs(z)) if z != 0 else math.inf if x.e else 0.0) + 2 * U * abs(z))


# drop-in replacement for the ``math`` module of an engine module under test (floats pass through unchanged)
FMATH = SimpleNamespace(
    pi=math.pi, e=math.e, inf=math.inf, nan=math.nan, isfinite=math.isfinite, isinf=math.isinf, isnan=math.isnan,
    copysign=math.copysign, floor=math.floor, ceil=math.ceil, radians=math.radians, degrees=math.degrees,
    sqrt=_sqrt,
    exp=_lib1(math.exp, lambda x, z: abs(z)),
    log=_lib1(math.log, lambda x, z: 1.0 / abs(x)),
    log1p=_lib1(math.log1p, lambda x, z: 1.0 / abs(1.0 + x)),
    sin=_lib1(math.sin, lambda x, z: abs(math.cos(x))),
    cos=_lib1(math.cos, lambda x, z: abs(math.sin(x))),
    sinh=_lib1(math.sinh, lambda x, z: math.cosh(x)),
    cosh=_lib1(math.cosh, lambda x, z: abs(math.sinh(x))),
    acos=_lib1(math.acos, lambda x, z: 1.0 / math.sqrt(1.0 - x * x) if abs(x) < 1 else math.inf),
    asin=_lib1(math.asin, lambda x, z: 1.0 / math.sqrt(1.0 - x * x) if abs(x) < 1 else math.inf),
)
CMATH = SimpleNamespace(sqrt=_csqrt, pi=cmath.pi)


def value(x):
    return _v(x)


def bound(x) -> float:
    return _e(x)
