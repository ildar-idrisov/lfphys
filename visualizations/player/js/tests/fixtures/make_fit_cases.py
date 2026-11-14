# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Write fit_cases.json: the lab's fit (player/js/fit.js) against its Python reference lfphys.tools.stats.linear_fit
(design lfphys/sources/explore_2026-11-14_design.md §2.3; fit.test.mjs compares them to 1e-12). Each case: {x, y, sx,
sy, model, params, sigma, chi2} with fit.js's names (line0: b; line: a, b; quadratic: c0, c1, c2 and the vertex xv;
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
                  "sy": list(map(float, sy)), "params": params, "sigma": sigma, "chi2": r["chi2"], "scaled": r["scaled"]})


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
out = Path(__file__).with_name("fit_cases.json")
out.write_text(json.dumps(cases, indent=1) + "\n", encoding="utf-8")
print(f"{out}: {len(cases)} cases")
