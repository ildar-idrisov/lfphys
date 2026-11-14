# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""``lfphys.tools.stats.linear_fit``, the lab work's fit (design explore_2026-11-14 §2.3, §8): every model on exact
data; the effective variance against a hand-computed case and against the same iteration written out with sums; the
NIST Statistical Reference Datasets (certified to 15 digits, computed by NIST in 500-digit arithmetic); the Birge
scaling; the coverage of the errors by Monte Carlo; the iterated solution against the true minimum of S."""

import math

import numpy as np
import pytest
from scipy import optimize

from lfphys.tools.stats import linear_fit

# --- NIST/ITL StRD, linear least squares (https://www.itl.nist.gov/div898/strd/lls/, data files Norris.dat, NoInt1.dat,
# Pontius.dat, fetched 2026-11-14; public domain). The certified standard deviations are sqrt(diag(s^2 (X^T X)^-1)),
# s^2 = RSS / (n - p) (the certification page): the Birge-scaled errors of an unweighted fit whose chi^2/dof > 1.
NORRIS_X = [0.2, 337.4, 118.2, 884.6, 10.1, 226.5, 666.3, 996.3, 448.6, 777.0, 558.2, 0.4, 0.6, 775.5, 666.9, 338.0,
            447.5, 11.6, 556.0, 228.1, 995.8, 887.6, 120.2, 0.3, 0.3, 556.8, 339.1, 887.2, 999.0, 779.0, 11.1, 118.3,
            229.2, 669.1, 448.9, 0.5]
NORRIS_Y = [0.1, 338.8, 118.1, 888.0, 9.2, 228.1, 668.5, 998.5, 449.1, 778.9, 559.2, 0.3, 0.1, 778.1, 668.8, 339.3,
            448.9, 10.8, 557.7, 228.3, 998.0, 888.8, 119.6, 0.3, 0.6, 557.6, 339.3, 888.0, 998.5, 778.9, 10.2, 117.6,
            228.9, 668.4, 449.2, 0.2]
NORRIS = {"params": [-0.262323073774029, 1.00211681802045], "sigma": [0.232818234301152, 0.429796848199937E-03],
          "resid_sd": 0.884796396144373}
NOINT1_X = list(range(60, 71))
NOINT1_Y = list(range(130, 141))
NOINT1 = {"params": [2.07438016528926], "sigma": [0.165289256198347E-01], "resid_sd": 3.56753034006338}
PONTIUS_X = [150000 * (i % 20 + 1) for i in range(40)]
PONTIUS_Y = [.11019, .21956, .32949, .43899, .54803, .65694, .76562, .87487, .98292, 1.09146, 1.20001, 1.30822, 1.41599,
             1.52399, 1.63194, 1.73947, 1.84646, 1.95392, 2.06128, 2.16844, .11052, .22018, .32939, .43886, .54798,
             .65739, .76596, .87474, .98300, 1.09150, 1.20004, 1.30818, 1.41613, 1.52408, 1.63159, 1.73965, 1.84696,
             1.95445, 2.06177, 2.16829]
PONTIUS = {"params": [0.673565789473684E-03, 0.732059160401003E-06, -0.316081871345029E-14],
           "sigma": [0.107938612033077E-03, 0.157817399981659E-09, 0.486652849992036E-16],
           "resid_sd": 0.205177424076185E-03}


@pytest.mark.parametrize("name,x,y,model,cert,rtol", [
    ("Norris", NORRIS_X, NORRIS_Y, "line", NORRIS, 1e-12),
    ("NoInt1", NOINT1_X, NOINT1_Y, "line0", NOINT1, 1e-12),
    ("Pontius", PONTIUS_X, PONTIUS_Y, "quadratic", PONTIUS, 2e-11),
])
def test_nist_strd_certified_values(name, x, y, model, cert, rtol):
    """sy far below the scatter makes chi^2/dof > 1, so the Birge-scaled errors are NIST's s * sqrt(diag((X^T X)^-1)).
    Measured (largest relative deviation, parameters / errors): Norris 1.3e-13 / 1.4e-14 (B0 = -0.26 is small against
    data up to 1000); NoInt1 1.7e-15 / 2e-16; Pontius 1.9e-12 / 5e-14 (x up to 3e6 and x^2 up to 9e12)."""
    sy = cert["resid_sd"] * 1e-3
    f = linear_fit(x, y, 0.0, sy, model)
    assert f["scaled"] and f["dof"] == len(x) - len(cert["params"])
    assert np.allclose(f["params"], cert["params"], rtol=rtol, atol=0)
    assert np.allclose(f["sigma"], cert["sigma"], rtol=rtol, atol=0)
    assert math.sqrt(f["chi2"] / f["dof"]) * sy == pytest.approx(cert["resid_sd"], rel=rtol)


@pytest.mark.parametrize("name,x,y,model,cert,rtol", [
    ("Norris", NORRIS_X, NORRIS_Y, "line", NORRIS, 1e-12),
    ("NoInt1", NOINT1_X, NOINT1_Y, "line0", NOINT1, 1e-12),
    ("Pontius", PONTIUS_X, PONTIUS_Y, "quadratic", PONTIUS, 2e-11),
])
def test_nist_strd_readings_without_errors(name, x, y, model, cert, rtol):
    """Readings without errors (as fit.js): ordinary least squares with the errors from the scatter, NIST's
    definition exactly."""
    f = linear_fit(x, y, 0.0, 0.0, model)
    assert f["unit"] and f["scaled"] and f["chi2"] is None
    assert np.allclose(f["params"], cert["params"], rtol=rtol, atol=0)
    assert np.allclose(f["sigma"], cert["sigma"], rtol=rtol, atol=0)


def test_a_point_without_any_error_falls_back_to_ordinary_least_squares():
    a = linear_fit([0, 1, 2, 3], [0.1, 0.9, 2.2, 2.9], [0, 0.1, 0.1, 0.1], [0, 0.1, 0.1, 0.1], "line")
    b = linear_fit([0, 1, 2, 3], [0.1, 0.9, 2.2, 2.9], 0, 0, "line")
    assert a["unit"] and a["params"] == b["params"] and a["sigma"] == b["sigma"]


def test_hand_computed_effective_variance():
    """line0 through (1, 2) and (2, 4.2), sx = sy = 0.1 at both. By hand: the start (weights 1/sy^2, equal here)
    b0 = sum xy / sum x^2 =
    10.4 / 5 = 2.08; sigma^2 = 0.1^2 + (2.08 * 0.1)^2 = 0.053264 at both points, so the weights are equal and b stays
    2.08 in every re-weighting; sigma_b^2 = sigma^2 / sum x^2 = 0.0106528; chi^2 = ((2 - 2.08)^2 + (4.2 - 4.16)^2) /
    0.053264 = 0.008 / 0.053264 = 0.150195...; dof 1, chi^2/dof < 1: not scaled."""
    f = linear_fit([1, 2], [2, 4.2], 0.1, 0.1, "line0")
    assert f["params"][0] == pytest.approx(2.08, rel=1e-15)
    assert f["sigma_eff"] == pytest.approx([math.sqrt(0.053264)] * 2, rel=1e-15)
    assert f["sigma"][0] == pytest.approx(math.sqrt(0.0106528), rel=1e-14)
    assert f["chi2"] == pytest.approx(0.008 / 0.053264, rel=1e-13)
    assert not f["scaled"] and f["sigma"] == f["sigma_unscaled"]


def _by_sums(x, y, sx, sy, iterations=3):
    """The same algorithm written with the textbook sums of a weighted straight line (no matrices)."""
    x, y, sx, sy = (np.asarray(v, float) for v in (x, y, sx, sy))
    w = 1.0 / sy ** 2  # the start: sigma_y alone
    S, Sx, Sy, Sxx, Sxy = w.sum(), (w * x).sum(), (w * y).sum(), (w * x * x).sum(), (w * x * y).sum()
    b = (S * Sxy - Sx * Sy) / (S * Sxx - Sx * Sx)
    for _ in range(iterations):
        w = 1.0 / (sy ** 2 + (b * sx) ** 2)
        S, Sx, Sy, Sxx, Sxy = w.sum(), (w * x).sum(), (w * y).sum(), (w * x * x).sum(), (w * x * y).sum()
        D = S * Sxx - Sx * Sx
        a, b = (Sxx * Sy - Sx * Sxy) / D, (S * Sxy - Sx * Sy) / D
    return a, b, math.sqrt(Sxx / D), math.sqrt(S / D), float(np.sum(w * (y - a - b * x) ** 2))


def test_effective_variance_against_the_sums():
    x = [0.0, 1.0, 2.0, 3.0, 4.5]
    y = [1.1, 2.9, 5.2, 6.8, 10.3]
    sx = [0.05, 0.1, 0.2, 0.1, 0.3]
    sy = [0.1, 0.2, 0.1, 0.3, 0.2]
    a, b, sa, sb, chi2 = _by_sums(x, y, sx, sy)
    f = linear_fit(x, y, sx, sy, "line")
    assert f["params"] == pytest.approx([a, b], rel=1e-13)
    assert f["sigma_unscaled"] == pytest.approx([sa, sb], rel=1e-13)
    assert f["chi2"] == pytest.approx(chi2, rel=1e-12)
    s = math.sqrt(max(1.0, chi2 / 3))
    assert f["sigma"] == pytest.approx([sa * s, sb * s], rel=1e-13)


@pytest.mark.parametrize("model", ["line0", "line", "quadratic", "power"])
def test_every_model_on_exact_data(model):
    x = np.array([0.5, 1.0, 1.5, 2.0, 3.0, 4.0])
    y = {"line0": 1.7 * x, "line": 0.3 + 1.7 * x, "quadratic": 0.3 + 1.7 * x - 0.4 * x * x,
         "power": 2.5 * x ** 0.5}[model]
    f = linear_fit(x, y, 0.01, 0.02, model)
    want = {"line0": [1.7], "line": [0.3, 1.7], "quadratic": [0.3, 1.7, -0.4], "power": [math.log(2.5), 0.5]}[model]
    assert np.allclose(f["params"], want, rtol=1e-13, atol=1e-14)
    assert f["chi2"] < 1e-20 and not f["scaled"]
    if model == "quadratic":
        assert f["vertex"] == pytest.approx(1.7 / 0.8, rel=1e-13) and f["vertex_sigma"] > 0
    if model == "power":
        assert f["A"] == pytest.approx(2.5, rel=1e-13) and f["n_exp"] == pytest.approx(0.5, rel=1e-13)


def test_vertex_error_by_propagation():
    """The vertex's error from the covariance equals the numerical gradient's propagation."""
    rng = np.random.default_rng(7)
    th = np.arange(20.0, 71.0, 5.0)
    L = 40.0 - 0.02 * (th - 43.0) ** 2 + rng.normal(0, 0.1, th.size)
    f = linear_fit(th, L, 0.5, 0.1, "quadratic")
    p = np.array(f["params"])
    C = np.array(f["cov"])

    def vertex(q):
        return -q[1] / (2.0 * q[2])

    grad = []
    for i in range(3):
        e = np.zeros(3)
        e[i] = 1e-6 * max(abs(p[i]), 1e-12)
        grad.append((vertex(p + e) - vertex(p - e)) / (2 * e[i]))
    grad = np.array(grad)
    assert f["vertex_sigma"] == pytest.approx(math.sqrt(grad @ C @ grad), rel=1e-6)
    assert abs(f["vertex"] - 43.0) < 4 * f["vertex_sigma"]


def test_refusals():
    with pytest.raises(ValueError):
        linear_fit([1, 2], [1, 2], 0, 0.1, "cubic")
    with pytest.raises(ValueError):
        linear_fit([1, 2], [1, 2], 0, 0.1, "line")  # n = p
    with pytest.raises(ValueError):
        linear_fit([1, 2, 3], [1, -2, 3], 0, 0.1, "power")
    with pytest.raises(ValueError):
        linear_fit([1, 2, float("nan")], [1, 2, 3], 0, 0.1, "line")
    with pytest.raises(ValueError):
        linear_fit([1, 2, 3], [1, 2, 3], -0.1, 0.1, "line")


def test_coverage_by_monte_carlo():
    """20 000 data sets of 10 points on y = 1 + 2x with Gaussian errors. With errors in y only, the unscaled 95 %
    interval of the slope covers it in 95 % of the sets (the exact sampling distribution): asserted within 0.6 %
    (4 standard errors of a binomial share at n = 20 000). The Birge scaling enlarges the errors only when chi^2/dof
    > 1, so its intervals cover more often (measured 96.1 %). With errors in x as well (sigma_x b = sigma_y), the
    effective variance's unscaled interval: measured 94.7 %."""
    rng = np.random.default_rng(20261114)
    N, z = 20000, 1.959963984540054
    x = np.linspace(0.0, 4.5, 10)
    cover = {"y": 0, "y_birge": 0, "xy": 0}
    for _ in range(N):
        y = 1.0 + 2.0 * x + rng.normal(0.0, 0.2, x.size)
        f = linear_fit(x, y, 0.0, 0.2, "line")
        cover["y"] += abs(f["params"][1] - 2.0) < z * f["sigma_unscaled"][1]
        cover["y_birge"] += abs(f["params"][1] - 2.0) < z * f["sigma"][1]
        xt = x + rng.normal(0.0, 0.1, x.size)
        y2 = 1.0 + 2.0 * x + rng.normal(0.0, 0.2, x.size)
        g = linear_fit(xt, y2, 0.1, 0.2, "line")
        cover["xy"] += abs(g["params"][1] - 2.0) < z * g["sigma_unscaled"][1]
    share = {k: v / N for k, v in cover.items()}
    print("coverage", share)
    assert abs(share["y"] - 0.95) < 0.006
    assert 0.95 < share["y_birge"] < 0.985
    assert abs(share["xy"] - 0.95) < 0.01


# Pearson's data with York's weights (York, Can. J. Phys. 44, 1079 (1966); as widely reproduced, the table not checked
# against the original): x errors comparable to the y errors at the far end, a hard case for the effective variance
PY_X = [0.0, 0.9, 1.8, 2.6, 3.3, 4.4, 5.2, 6.1, 6.5, 7.4]
PY_Y = [5.9, 5.4, 4.4, 4.6, 3.5, 3.7, 2.8, 2.8, 2.4, 1.5]
PY_WX = [1000, 1000, 500, 800, 200, 80, 60, 20, 1.8, 1]
PY_WY = [1, 1.8, 4, 8, 20, 20, 70, 70, 100, 500]


def test_iterated_effective_variance_against_the_minimum_of_S():
    """The fixed point of the re-weighting is not the minimum of S(a, b) = sum (y - a - b x)^2 / (sy^2 + b^2 sx^2)
    (the minimum has an extra term from the weights' dependence on b). Measured here: the fixed point b = -0.46345,
    a = 5.39605; the true minimum (Nelder–Mead) b = -0.480533, a = 5.479910 — 0.296 sigma_b apart; three
    re-weightings are within 1e-5 sigma_b of the fixed point. The test keeps the statement in tools.stats true."""
    sx = 1.0 / np.sqrt(PY_WX)
    sy = 1.0 / np.sqrt(PY_WY)
    x, y = np.array(PY_X), np.array(PY_Y)
    f3 = linear_fit(x, y, sx, sy, "line")
    fc = linear_fit(x, y, sx, sy, "line", iterations=200)

    def S(p):
        a, b = p
        return float(np.sum((y - a - b * x) ** 2 / (sy ** 2 + b * b * sx ** 2)))

    m = optimize.minimize(S, fc["params"], method="Nelder-Mead", options={"xatol": 1e-13, "fatol": 1e-15,
                                                                          "maxiter": 20000})
    sb = fc["sigma_unscaled"][1]
    gap_fixed = abs(fc["params"][1] - m.x[1]) / sb
    gap_3 = abs(f3["params"][1] - fc["params"][1]) / sb
    print("Pearson-York: b3", f3["params"], "b_fixed", fc["params"], "min S", m.x.tolist(), "gaps/sigma_b",
          gap_fixed, gap_3)
    assert 0.25 < gap_fixed < 0.35 and gap_3 < 1e-5
    assert S(m.x) <= S(fc["params"])
