# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Write expr_cases.json: the formula columns of a lab step (player/js/expr.js and server/lfviz/expr.py; design
lfphys/sources/explore_EX2_2026-11-18_design.md §5 F5) against references computed here independently of both: each
formula is written a second time as an mpmath function (50 digits), its value is that function's, and its two error
terms t1 = Σ(∂f/∂xᵢ·σᵢ)² and t2 = ½ΣᵢΣⱼ(∂²f/∂xᵢ∂xⱼ·σᵢσⱼ)² (the diagonal and, since review R2-F F2, the mixed second
derivatives) come from mpmath's own derivatives (``mpmath.diff`` at 50 digits, partial ones for the mixed terms), not
from the hyper-dual numbers under test. expr.test.mjs and tests/test_expr.py hold both evaluators to 1e-12. The
refused formulas (``refused``: the code each parser must give) and the undefined values (``undefined``: the reason) are
listed too. Run from the repository root in Docker:
    docker run --rm --memory=1g -v "$PWD":/lf -w /lf lfphys-viz \
        python3 visualizations/player/js/tests/fixtures/make_expr_cases.py
"""

import json
from pathlib import Path

import mpmath as mp

mp.mp.dps = 50
D = mp.pi / 180


def sind(x):
    return mp.sin(x * D)


def cosd(x):
    return mp.cos(x * D)


def tand(x):
    return mp.tan(x * D)


def asind(x):
    return mp.asin(x) / D


def acosd(x):
    return mp.acos(x) / D


def atand(x):
    return mp.atan(x) / D


cases = []


def add(text, f, inputs, note=""):
    """A defined case: ``inputs`` {name: (v, σ)} in the order of the formula's first appearance."""
    names = list(inputs)
    at = {k: mp.mpf(v) for k, (v, _s) in inputs.items()}
    value = f(**at)
    t1 = t2 = mp.mpf(0)
    live = []
    for k in names:
        s = mp.mpf(inputs[k][1])
        if s == 0:
            continue
        live.append(k)

        def g(x, k=k):
            return f(**{**at, k: x})
        d1 = mp.diff(g, at[k], 1)
        d2 = mp.diff(g, at[k], 2)
        t1 += (d1 * s) ** 2
        t2 += (d2 * s * s) ** 2 / 2
    for i, ki in enumerate(live):  # the mixed terms: Σ_{i<j} (∂²f/∂xᵢ∂xⱼ·σᵢσⱼ)²
        for kj in live[i + 1:]:
            def h(xi, xj, ki=ki, kj=kj):
                return f(**{**at, ki: xi, kj: xj})
            dij = mp.diff(h, (at[ki], at[kj]), (1, 1))
            t2 += (dij * mp.mpf(inputs[ki][1]) * mp.mpf(inputs[kj][1])) ** 2
    cases.append({"expr": text, "vars": {k: list(v) for k, v in inputs.items()}, "value": float(value),
                  "t1": float(t1), "t2": float(t2), "error": float(mp.sqrt(t1 + t2)), "note": note})


def undefined(text, inputs, reason):
    cases.append({"expr": text, "vars": {k: list(v) for k, v in inputs.items()}, "undefined": reason})


refused = []


def refuse(text, code, columns=("x", "y", "a", "b"), later=("z",)):
    refused.append({"expr": text, "columns": list(columns), "later": list(later), "code": code})


# the arithmetic and its precedence
add("a + b", lambda a, b: a + b, {"a": (1.25, 0.01), "b": (-3.5, 0.02)})
add("a - b", lambda a, b: a - b, {"a": (1.25, 0.01), "b": (-3.5, 0.02)})
add("a * b", lambda a, b: a * b, {"a": (1.25, 0.01), "b": (-3.5, 0.02)})
add("a / b", lambda a, b: a / b, {"a": (1.25, 0.01), "b": (-3.5, 0.02)})
add("a ^ 2", lambda a: a ** 2, {"a": (1.25, 0.01)})
add("a ^ 3", lambda a: a ** 3, {"a": (-1.25, 0.01)}, "a whole power of a negative number")
add("a ^ 0.5", lambda a: a ** mp.mpf("0.5"), {"a": (2.5, 0.1)})
add("a ^ -1.5", lambda a: a ** mp.mpf("-1.5"), {"a": (2.5, 0.1)})
add("a ^ b", lambda a, b: a ** b, {"a": (2.5, 0.1), "b": (1.7, 0.05)}, "a variable exponent: exp(b·ln a)")
add("2 ^ -a", lambda a: mp.mpf(2) ** (-a), {"a": (1.5, 0.2)})
add("-a ^ 2", lambda a: -(a ** 2), {"a": (1.5, 0.2)}, "-a^2 is -(a^2)")
add("a ^ 2 ^ 0.5", lambda a: a ** (mp.mpf(2) ** mp.mpf("0.5")), {"a": (1.5, 0.2)}, "right-associative")
add("(a + b) * (a - b) / 2", lambda a, b: (a + b) * (a - b) / 2, {"a": (3.0, 0.3), "b": (2.0, 0.1)})
add("x * x + x", lambda x: x * x + x, {"x": (0.7, 0.05)}, "one input used three times")
add("-(-x)", lambda x: x, {"x": (0.7, 0.05)})
add("+x - -x", lambda x: 2 * x, {"x": (0.7, 0.05)})
add("pi / 4", lambda: mp.pi / 4, {}, "a constant formula")
add("1.5e-3 * x + .25", lambda x: mp.mpf("1.5e-3") * x + mp.mpf("0.25"), {"x": (2.0, 0.5)})
add("x * 1e10", lambda x: x * mp.mpf("1e10"), {"x": (3.3, 0.1)})
add("1 / x", lambda x: 1 / x, {"x": (1e-8, 1e-10)})
add("x / y", lambda x, y: x / y, {"x": (5.0, 0.0), "y": (2.0, 0.1)}, "an exact input adds nothing")
# every function
for fn, f, v, s in [("sqrt", mp.sqrt, 2.0, 0.1), ("ln", mp.log, 2.0, 0.1), ("exp", mp.exp, 0.7, 0.05),
                    ("abs", abs, -0.7, 0.05), ("abs", abs, 0.7, 0.05), ("sin", mp.sin, 0.7, 0.05),
                    ("cos", mp.cos, 0.7, 0.05), ("tan", mp.tan, 0.7, 0.05), ("asin", mp.asin, 0.3, 0.02),
                    ("acos", mp.acos, -0.3, 0.02), ("atan", mp.atan, 2.0, 0.1), ("sind", sind, 30.0, 0.5),
                    ("cosd", cosd, 45.0, 0.5), ("tand", tand, 60.0, 0.5), ("asind", asind, 0.5, 0.01),
                    ("acosd", acosd, 0.5, 0.01), ("atand", atand, 1.0, 0.01)]:
    add(f"{fn}(x)", lambda x, f=f: f(x), {"x": (v, s)})
# the labs of EX2: E from four counts, R from two, the Fresnel linearisations, S from four E, Δφ, M/p, the CHSH x
add("(npp + nmm - npm - nmp) / (npp + nmm + npm + nmp)",
    lambda npp, nmm, npm, nmp: (npp + nmm - npm - nmp) / (npp + nmm + npm + nmp),
    {"npp": (431.0, 431 ** 0.5), "nmm": (418.0, 418 ** 0.5), "npm": (74.0, 74 ** 0.5), "nmp": (77.0, 77 ** 0.5)},
    "u37: E from four coincidence counts, Poisson errors")
add("(npp + nmm - npm - nmp) / (npp + nmm + npm + nmp)",
    lambda npp, nmm, npm, nmp: (npp + nmm - npm - nmp) / (npp + nmm + npm + nmp),
    {"npp": (503.0, 503 ** 0.5), "nmm": (497.0, 497 ** 0.5), "npm": (0.0, 1.0), "nmp": (0.0, 1.0)},
    "u37: a count of 0 carries the error of one count")
add("nR / (nR + nT)", lambda nR, nT: nR / (nR + nT), {"nR": (838.0, 838 ** 0.5), "nT": (19162.0, 19162 ** 0.5)},
    "u35: R from two counts")
add("(cosd(th) * (1 + sqrt(R)) / (1 - sqrt(R))) ^ 2",
    lambda th, R: (cosd(th) * (1 + mp.sqrt(R)) / (1 - mp.sqrt(R))) ** 2, {"th": (40.0, 0.0), "R": (0.0526, 0.0016)},
    "u35: the linearisation of R_s")
add("(cosd(th) * (1 - sqrt(R)) / (1 + sqrt(R))) ^ 2",
    lambda th, R: (cosd(th) * (1 - mp.sqrt(R)) / (1 + mp.sqrt(R))) ** 2, {"th": (40.0, 0.0), "R": (0.0181, 0.00094)},
    "u35: the linearisation of R_p")
add("sind(th) ^ 2", lambda th: sind(th) ** 2, {"th": (40.0, 0.5)})
add("E1 - E2 + E3 + E4", lambda E1, E2, E3, E4: E1 - E2 + E3 + E4,
    {"E1": (0.7071, 0.011), "E2": (-0.7071, 0.011), "E3": (0.7071, 0.011), "E4": (0.7071, 0.011)}, "u37: S")
add("shift * pi / 180 / N", lambda shift, N: shift * mp.pi / 180 / N, {"shift": (3.0, 0.05), "N": (1.0, 0.0)},
    "u34: Δφ from a shift")
add("(rp + ra) / (2 * rp * ra)", lambda rp, ra: (rp + ra) / (2 * rp * ra), {"rp": (300.0, 0.5), "ra": (460.0, 0.5)},
    "u34: M/p from two radii")
add("3 * cosd(2 * D) - cosd(6 * D)", lambda D: 3 * cosd(2 * D) - cosd(6 * D), {"D": (22.5, 0.0)},
    "u37: the CHSH abscissa")
add("dphi / x", lambda dphi, x: dphi / x, {"dphi": (0.0523, 0.0005), "x": (0.00275, 0.00001)})
# the mixed second derivatives (review R2-F F2): a saddle, where they are the whole error, and ordinary points
add("x * y", lambda x, y: x * y, {"x": (0.0, 1.0), "y": (0.0, 1.0)}, "a saddle: only the mixed term (σ_xσ_y)")
add("x * y", lambda x, y: x * y, {"x": (0.1, 1.0), "y": (0.1, 1.0)}, "near the saddle")
add("x * y", lambda x, y: x * y, {"x": (0.5, 0.2), "y": (0.3, 0.4)}, "a product: the exact variance")
add("x * y * z", lambda x, y, z: x * y * z, {"x": (1.0, 0.1), "y": (-2.0, 0.2), "z": (0.5, 0.05)}, "three pairs")
add("x / y + sin(x * y)", lambda x, y: x / y + mp.sin(x * y), {"x": (1.0, 0.1), "y": (2.0, 0.1)})
add("x ^ y", lambda x, y: x ** y, {"x": (1.5, 0.05), "y": (0.0, 0.3)}, "a variable exponent at 0")
add("abs(x)", lambda x: abs(x), {"x": (0.0, 0.0)}, "|0| of an exact input: 0 ± 0")
# a constant part with an infinite derivative does not spoil the input's own error
add("sqrt(c) + a", lambda c, a: mp.sqrt(c) + a, {"c": (0.0, 0.0), "a": (2.0, 0.1)})
add("sqrt(x)", lambda x: mp.sqrt(x), {"x": (0.0, 0.0)}, "√0 of an exact input: 0 ± 0")
# undefined values: the reason
undefined("sqrt(x)", {"x": (-1.0, 0.1)}, "sqrt_negative")
undefined("1 / x", {"x": (0.0, 0.1)}, "division_by_zero")
undefined("x / (y - y)", {"x": (1.0, 0.1), "y": (2.0, 0.1)}, "division_by_zero")
undefined("ln(x)", {"x": (0.0, 0.1)}, "log_nonpositive")
undefined("ln(x)", {"x": (-2.0, 0.1)}, "log_nonpositive")
undefined("asin(x)", {"x": (1.5, 0.1)}, "asin_domain")
undefined("acosd(x)", {"x": (-2.0, 0.1)}, "acos_domain")
undefined("x ^ 0.5", {"x": (-4.0, 0.1)}, "power")
undefined("x ^ -1", {"x": (0.0, 0.1)}, "division_by_zero")
undefined("x ^ y", {"x": (-2.0, 0.1), "y": (2.0, 0.1)}, "power")
undefined("exp(x)", {"x": (1000.0, 0.1)}, "not_finite")
undefined("x * 1e300 * 1e300", {"x": (1.0, 0.1)}, "not_finite")
undefined("x + y", {"x": (1.0, 0.1), "y": (None, 0.1)}, "missing")
undefined("sqrt(x)", {"x": (0.0, 0.1)}, "error_undefined")
undefined("asin(x)", {"x": (1.0, 0.1)}, "error_undefined")
undefined("abs(x)", {"x": (0.0, 0.1)}, "error_undefined")  # the kink: no derivative (review R2-F F9)
undefined("abs(x - y) * 2", {"x": (1.0, 0.1), "y": (1.0, 0.0)}, "error_undefined")
# refused formulas: the code
for text, code in [("constructor", "unknown_name"), ("__proto__", "unknown_name"), ("prototype", "unknown_name"),
                   ("toString", "unknown_name"), ("x.y", "syntax"), ("x.constructor", "syntax"), ("x(1)", "not_callable"),
                   ("pi(2)", "not_callable"), ("eval(1)", "not_callable"), ("Function(1)", "not_callable"),
                   ("constructor(1)", "not_callable"), ("alert(x)", "not_callable"), ("sin", "no_argument"),
                   ("sin x", "no_argument"), ("1 +", "syntax"), ("(1", "syntax"), ("1)", "syntax"), ("[1]", "syntax"),
                   ("x ** 2", "syntax"), ("'a'", "syntax"), ('"a"', "syntax"), ("`a`", "syntax"), ("x;y", "syntax"),
                   ("x = 1", "syntax"), ("a, b", "syntax"), ("x % 2", "syntax"), ("x ? a : b", "syntax"),
                   ("\\u0078", "syntax"), ("1e400", "number"), ("", "empty"), ("   ", "empty"), ("z + 1", "later_column"),
                   ("w + 1", "unknown_name"), ("1 2", "syntax"), ("x y", "syntax"), ("()", "syntax"),
                   ("(" * 60 + "x" + ")" * 60, "too_deep"), ("-" * 60 + "x", "too_deep"),
                   ("x + " * 120 + "x", "too_long"), ("2x", "syntax"), ("x..y", "syntax"), ("1.2.3", "syntax"),
                   # ASCII digits and spaces only, in both parsers (review R2-F F8)
                   ("\u0663 * x", "syntax"), ("x * \uff13", "syntax"), ("x\u00a0+ 1", "syntax"), ("x\u2028+ 1", "syntax"),
                   ("x\u3000+ 1", "syntax"), ("x\ufeff+ 1", "syntax"), ("x\x1c+ 1", "syntax"), ("x\x85+ 1", "syntax")]:
    refuse(text, code)

out = Path(__file__).with_name("expr_cases.json")
out.write_text(json.dumps({"cases": cases, "refused": refused}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"{len(cases)} cases, {len(refused)} refused -> {out}")
