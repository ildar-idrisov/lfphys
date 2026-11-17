# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Write fit_cases.json: the lab's fit (player/js/fit.js) against its Python reference lfphys.tools.stats.linear_fit
(design lfphys/sources/explore_2026-11-14_design.md §2.3; fit.test.mjs compares them to 1e-12). Each case: {x, y, sx,
sy, model, params, sigma, chi2, scaled, method} with fit.js's names (line0: b; line: a, b; quadratic: c0, c1, c2 and the
vertex xv;
power: A, p). Run from the repository root in Docker (lfphys on the path):
    docker run --rm --memory=2g -v "$PWD":/lf -w /lf -e PYTHONPATH=/lf/lfphys lfphys-viz \
        python3 visualizations/player/js/tests/fixtures/make_fit_cases.py
"""

import json
from pathlib import Path

import numpy as np

from lfphys.tools.stats import linear_fit

rng = np.random.default_rng(20261114)
cases = []


def add(x, y, sx, sy, model):
    r = linear_fit(x, y, sx, sy, model)
    s = dict(zip(r["names"], r["sigma"]))
    p = dict(zip(r["names"], r["params"]))
    if model == "quadratic":
        params = {"c0": p["a"], "c1": p["b"], "c2": p["c"], "xv": r["vertex"]}
        sigma = {"c0": s["a"], "c1": s["b"], "c2": s["c"], "xv": r["vertex_sigma"]}
    elif model == "power":
        params, sigma = {"A": r["A"], "p": r["n_exp"]}, {"A": r["A_sigma"], "p": r["n_exp_sigma"]}
    else:
        params, sigma = p, s
    cases.append({"model": model, "x": list(map(float, x)), "y": list(map(float, y)), "sx": list(map(float, sx)),
                  "sy": list(map(float, sy)), "params": params, "sigma": sigma, "chi2": r["chi2"], "scaled": r["scaled"],
                  "method": r["method"]})


def refused(x, y, sx, sy, model):
    """A case Python refuses as a singular design (code fit.singular): fit.js must throw why = "singular"."""
    try:
        linear_fit(x, y, sx, sy, model)
    except ValueError as e:
        assert getattr(e, "code", None) == "fit.singular", e
        cases.append({"model": model, "x": list(map(float, x)), "y": list(map(float, y)), "sx": list(map(float, sx)),
                      "sy": list(map(float, sy)), "refused": "singular"})
        return
    raise AssertionError(f"not refused: {model} {x}")


# the S03 lab's shapes: L(√h) through the origin, L(sin 2θ), L(θ) a parabola near its maximum, a power law; readings
# rounded to their divisions, with errors in x and y; a scatter that scales the errors (Birge) and one that does not
h = np.round(np.arange(0.2, 1.01, 0.05), 2)
L = np.round(0.6774 * np.sqrt(h), 3)
add(np.sqrt(h), L, 0.005 / (2 * np.sqrt(h)), np.full(h.size, 0.0005), "line0")
add(np.sqrt(h), L + rng.normal(0, 0.004, h.size), 0.005 / (2 * np.sqrt(h)), np.full(h.size, 0.0005), "line0")
th = np.arange(15.0, 76.0, 5.0)
R = np.round(25 / 9.80665 * np.sin(np.radians(2 * th)), 3)
add(np.sin(np.radians(2 * th)), R, np.abs(2 * np.cos(np.radians(2 * th)) * np.pi / 180 * 0.5), np.full(th.size, 0.0005), "line0")
add(np.sin(np.radians(2 * th)), R + 0.01, np.zeros(th.size), np.full(th.size, 0.0005), "line")
add(th, R, np.full(th.size, 0.5), np.full(th.size, 0.0005), "quadratic")
add(th, R + rng.normal(0, 0.02, th.size), np.full(th.size, 0.5), np.full(th.size, 0.01), "quadratic")
add(h, 3 * h ** 0.5 * (1 + rng.normal(0, 0.002, h.size)), np.full(h.size, 0.005), 0.01 * h, "power")
add([0.0, 1, 2, 3, 4], [1.0, 3.1, 4.9, 7.2, 8.8], [0] * 5, [0] * 5, "line")  # without errors: ordinary least squares
# York (integrator D3; lfphys/sources/verification_2026-11-17_york_fit.md §6): Pearson's data with York's weights (York et al. 2004, Table II, data
# set 3: a = 5.47991, b = -0.480533; the same data as lfphys/tests/test_stats_fit.py)
PY_X = [0.0, 0.9, 1.8, 2.6, 3.3, 4.4, 5.2, 6.1, 6.5, 7.4]
PY_Y = [5.9, 5.4, 4.4, 4.6, 3.5, 3.7, 2.8, 2.8, 2.4, 1.5]
PY_WX = [1000, 1000, 500, 800, 200, 80, 60, 20, 1.8, 1]
PY_WY = [1, 1.8, 4, 8, 20, 20, 70, 70, 100, 500]
add(PY_X, PY_Y, 1 / np.sqrt(PY_WX), 1 / np.sqrt(PY_WY), "line")
# random x errors comparable to the spread of x
xs = np.linspace(0, 1, 8)
add(xs + rng.normal(0, 0.3, 8), 2 * xs + 1 + rng.normal(0, 0.05, 8), np.full(8, 0.3), np.full(8, 0.05), "line")
add([1.0, 2.0], [2.0, 4.2], [0.1, 0.1], [0.1, 0.1], "line0")  # b = (16.64 + sqrt(16.64^2 + 4·10.4^2)) / 20.8
add(h, 3 * h ** 0.5 * (1 + rng.normal(0, 0.01, h.size)), 0.02 * h, 0.01 * 3 * h ** 0.5, "power")  # x errors in log-log
add(np.sqrt(h), L, 0.005 / (2 * np.sqrt(h)), np.zeros(h.size), "line0")  # a point without a y error: York still runs
add([1.0, 2, 3, 4], [2.0, 4.1, 5.9, 8.2], [0, 0, 0, 0], [0.1, 0, 0.1, 0.1], "line")  # a reading without any error: OLS
# the singular designs: refused in Python (fit.singular) and in fit.js (why "singular")
refused([2.0, 2, 2, 2], [1.0, 2, 3, 4], [0.1] * 4, [0.1] * 4, "line")
refused([0.0, 0, 0], [1.0, 2, 3], [0.1] * 3, [0.1] * 3, "line0")
refused([30.0, 30, 30, 40], [1.0, 2, 3, 4], [0.5] * 4, [0.1] * 4, "quadratic")
out = Path(__file__).with_name("fit_cases.json")
out.write_text(json.dumps(cases, indent=1) + "\n", encoding="utf-8")
print(f"{out}: {len(cases)} cases")

# the verdict's bound with σ from the scatter (integrator D4): Student's t with the coverage of the normal ±2σ,
# erf(√2) = 0.9545, two-sided, for n − p degrees of freedom (scipy.stats.t; fit.js tQuantile)
from scipy import stats as sps  # noqa: E402

cover = float(sps.norm.cdf(2.0) - sps.norm.cdf(-2.0))
tq = {"cover": cover, "k": {str(nu): float(sps.t.ppf(0.5 + cover / 2, nu)) for nu in (1, 2, 3, 4, 5, 7, 10, 15, 16, 30, 100)}}
out2 = Path(__file__).with_name("t_quantiles.json")
out2.write_text(json.dumps(tq, indent=1) + "\n", encoding="utf-8")
print(f"{out2}: {len(tq['k'])} quantiles")
