# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""``lfphys.tools.stats.linear_fit``, the lab work's fit (design explore_2026-11-14 §2.3, §8; review R-E F5, F8): every
model on exact data; the straight lines by York et al. (2004) against the paper's Pearson–York benchmark, the minimum of
S, the closed form of the major axis and Monte Carlo (coverage, also with random x errors comparable to the spread of x,
where the effective variance it replaced failed); the parabola's effective variance against the same iteration written
out with the normal equations; the NIST Statistical Reference Datasets (certified to 15 digits, computed by NIST in
500-digit arithmetic); the Birge scaling; the refusal of a singular design."""

import math

import numpy as np
import pytest
from scipy import optimize

from lfphys.codes import code_of
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


def test_line_through_the_origin_with_equal_errors_is_the_major_axis():
    """line0 through (1, 2) and (2, 4.2) with sx = sy = 0.1: with equal errors in x and y York's line is the major axis
    (the perpendicular distances): b solves Sxy b^2 + (Sxx - Syy) b - Sxy = 0 with Sxx = 5, Sxy = 10.4, Syy = 21.64,
    b = (16.64 + sqrt(16.64^2 + 4 * 10.4^2)) / 20.8 = 2.0806...; every point has W = 1 / (0.01 (1 + b^2)), the adjusted
    x_i = (x_i + b y_i) / (1 + b^2), sigma_b^2 = 1 / sum W x_i^2 and S = sum W (y_i - b x_i)^2. (The effective variance
    it replaced gave the start's 2.08: equal weights, so its re-weighting never moved.)"""
    f = linear_fit([1, 2], [2, 4.2], 0.1, 0.1, "line0")
    b = (16.64 + math.sqrt(16.64 ** 2 + 4 * 10.4 ** 2)) / 20.8
    W = 1.0 / (0.01 * (1 + b * b))
    xa = (np.array([1.0, 2.0]) + b * np.array([2.0, 4.2])) / (1 + b * b)
    assert f["method"] == "york" and f["params"][0] == pytest.approx(b, rel=1e-14)
    assert f["sigma_eff"] == pytest.approx([W ** -0.5] * 2, rel=1e-14)
    assert f["sigma_unscaled"][0] == pytest.approx(1.0 / math.sqrt(W * float(np.sum(xa * xa))), rel=1e-13)
    assert f["chi2"] == pytest.approx(W * ((2 - b) ** 2 + (4.2 - 2 * b) ** 2), rel=1e-12)
    assert not f["scaled"] and f["sigma"] == f["sigma_unscaled"]


def test_line_with_equal_errors_is_the_major_axis_of_the_centred_points():
    """The same for a line with an intercept: the slope solves Sxy b^2 + (Sxx - Syy) b - Sxy = 0 with the centred sums,
    a = ybar - b xbar (the closed form of the major axis: a second method)."""
    x = np.array([0.0, 1.0, 2.0, 3.0, 4.5])
    y = np.array([1.1, 2.9, 5.2, 6.8, 10.3])
    u, v = x - x.mean(), y - y.mean()
    Sxx, Sxy, Syy = float(u @ u), float(u @ v), float(v @ v)
    b = ((Syy - Sxx) + math.sqrt((Syy - Sxx) ** 2 + 4 * Sxy * Sxy)) / (2 * Sxy)
    f = linear_fit(x, y, 0.2, 0.2, "line")
    assert f["params"] == pytest.approx([y.mean() - b * x.mean(), b], rel=1e-13)


def _ev_parabola(x, y, sx, sy, iterations=3):
    """The parabola's effective variance written out with the normal equations (not QR): the start with sigma_y alone,
    then sigma_i^2 = sy^2 + (b + 2 c x)^2 sx^2 three times."""
    x, y, sx, sy = (np.asarray(v, float) for v in (x, y, sx, sy))
    X = np.stack([np.ones_like(x), x, x * x], axis=1)
    w = 1.0 / sy ** 2
    p = np.linalg.solve((X * w[:, None]).T @ X, (X * w[:, None]).T @ y)
    for _ in range(iterations):
        w = 1.0 / (sy ** 2 + ((p[1] + 2 * p[2] * x) * sx) ** 2)
        N = (X * w[:, None]).T @ X
        p = np.linalg.solve(N, (X * w[:, None]).T @ y)
    return p, np.linalg.inv(N), float(np.sum(w * (y - X @ p) ** 2))


def test_parabola_effective_variance_against_the_normal_equations():
    x = [0.0, 1.0, 2.0, 3.0, 4.5, 5.0]
    y = [1.1, 2.9, 4.2, 4.8, 4.3, 3.9]
    sx = [0.05, 0.1, 0.2, 0.1, 0.3, 0.1]
    sy = [0.1, 0.2, 0.1, 0.3, 0.2, 0.1]
    p, C, chi2 = _ev_parabola(x, y, sx, sy)
    f = linear_fit(x, y, sx, sy, "quadratic")
    assert f["method"] == "effective_variance" and f["iterations"] == 3
    assert f["params"] == pytest.approx(p.tolist(), rel=1e-11)
    assert f["sigma_unscaled"] == pytest.approx(np.sqrt(np.diag(C)).tolist(), rel=1e-11)
    assert f["chi2"] == pytest.approx(chi2, rel=1e-11)
    s = math.sqrt(max(1.0, chi2 / 3))
    assert f["sigma"] == pytest.approx((np.sqrt(np.diag(C)) * s).tolist(), rel=1e-11)


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


@pytest.mark.parametrize("x,model", [([2.0, 2.0, 2.0, 2.0], "line"), ([2.0, 2.0, 2.0, 2.0], "power"),
                                     ([0.0, 0.0, 0.0], "line0"), ([30.0, 30.0, 30.0, 40.0], "quadratic"),
                                     ([1.0, 1.0, 1.0 + 1e-15, 1.0], "line")])
def test_a_singular_design_is_refused(x, model):
    """Review R-E F8: all x equal, or fewer distinct x than parameters, is refused with the code "fit.singular" (the
    QR test |R_jj| <= 1e-14 |R_00| on the column-scaled design, as fit.js), instead of numpy's LinAlgError or a
    parabola with parameters ~1e15 and errors ~1e27. With and without errors."""
    y = [1.0, 1.1, 0.9, 1.05][:len(x)]
    for sx, sy in ((0.5, 0.05), (0.0, 0.0)):
        with pytest.raises(ValueError) as e:
            linear_fit(x, y, sx, sy, model)
        assert code_of(e.value) == "fit.singular"


def test_coverage_by_monte_carlo():
    """20 000 data sets of 10 points on y = 1 + 2x with Gaussian errors. With errors in y only, the unscaled 95 %
    interval of the slope covers it in 95 % of the sets (the exact sampling distribution): asserted within 0.6 %
    (4 standard errors of a binomial share at n = 20 000). The Birge scaling enlarges the errors only when chi^2/dof
    > 1, so its intervals cover more often (measured 96.1 %). With errors in x as well (sigma_x b = sigma_y), York's
    unscaled interval: measured 95.0 % (the effective variance's was 94.7 %: its weights are nearly equal here)."""
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


@pytest.mark.parametrize("model,n,sxv", [("line", 10, 0.2), ("line", 8, 0.3), ("line0", 8, 0.3)])
def test_random_x_errors_comparable_to_the_spread(model, n, sxv):
    """Review R-E F5: x in [0, 1], random x errors sigma_x = 0.2–0.3, sigma_y = 0.05, y = (1 +) 2x; 4000 data sets.
    The effective variance it replaced gave the attenuated slope of ordinary least squares (mean 1.55 and 1.24 for the
    two lines) and its 95 % intervals covered 54 % and 36 %. York's slope (the maximum likelihood) is close to the
    truth and its intervals cover near 95 % (the reviewer: mean 2.094 / 93.5 % and 2.318 / 90.9 % for the two lines).
    Measured here: median b 1.994, 2.004, 2.005; coverage 93.4 %, 91.5 %, 94.6 % (the mean, 2.08 and 2.34, is pulled
    by the heavy tail of a slope estimated from x readings that scatter as much as they spread)."""
    rng = np.random.default_rng(1)
    N, z = 4000, 1.959963984540054
    xt = np.linspace(0.0, 1.0, n) + (0.1 if model == "line0" else 0.0)
    a0 = 0.0 if model == "line0" else 1.0
    bs, cover = [], 0
    for _ in range(N):
        xo = xt + rng.normal(0.0, sxv, n)
        yo = a0 + 2.0 * xt + rng.normal(0.0, 0.05, n)
        g = linear_fit(xo, yo, sxv, 0.05, model)
        b = g["params"][-1]
        bs.append(b)
        cover += abs(b - 2.0) < z * g["sigma_unscaled"][-1]
    med = float(np.median(bs))
    print("random x errors", model, n, sxv, "median b", med, "mean b", float(np.mean(bs)), "coverage", cover / N)
    assert abs(med - 2.0) < 0.15 and cover / N > 0.88


def test_line_through_the_origin_by_monte_carlo():
    """The line through the origin (York's equations with the intercept fixed at 0, derived here): its sigma_b
    against the scatter of b over 20 000 data sets drawn around the adjusted points (York 2004, Appendix E), as the
    paper did for the general line (its Table II: within 0.5 % there). Measured: 0.9994; asserted within 3 %."""
    rng = np.random.default_rng(3)
    x = np.array([0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
    sx = np.array([0.05, 0.1, 0.05, 0.2, 0.1, 0.15])
    sy = np.array([0.1, 0.1, 0.2, 0.1, 0.3, 0.2])
    y = 1.7 * x + rng.normal(0.0, 1.0, x.size) * np.hypot(sy, 1.7 * sx)
    f = linear_fit(x, y, sx, sy, "line0")
    b = f["params"][0]
    W = 1.0 / np.array(f["sigma_eff"]) ** 2
    xa = W * (x * sy ** 2 + b * y * sx ** 2)  # the adjusted abscissae (Xbar = 0)
    bs = [linear_fit(xa + rng.normal(0.0, 1.0, x.size) * sx, b * xa + rng.normal(0.0, 1.0, x.size) * sy, sx, sy,
                     "line0")["params"][0] for _ in range(20000)]
    ratio = f["sigma_unscaled"][0] / float(np.std(bs))
    print("line0 sigma_b / Monte Carlo", ratio)
    assert abs(ratio - 1.0) < 0.03


# Pearson's data with York's weights (York, Can. J. Phys. 44, 1079 (1966); as widely reproduced, the table not checked
# against the original; York et al. 2004, Table II, data set 3): x errors comparable to the y errors at the far end
PY_X = [0.0, 0.9, 1.8, 2.6, 3.3, 4.4, 5.2, 6.1, 6.5, 7.4]
PY_Y = [5.9, 5.4, 4.4, 4.6, 3.5, 3.7, 2.8, 2.8, 2.4, 1.5]
PY_WX = [1000, 1000, 500, 800, 200, 80, 60, 20, 1.8, 1]
PY_WY = [1, 1.8, 4, 8, 20, 20, 70, 70, 100, 500]


def test_pearson_york_against_york_2004_table_II():
    """York et al., Am. J. Phys. 72, 367 (2004), Table II, data set 3 (read 2026-11-17): S/(n - 2) = 1.483,
    a = 5.479 91, b = -0.480 533; the Monte Carlo sigma 0.295 713 and 0.058 256 with Delta = -0.251 151 0 % and
    -0.464 447 3 % (Delta = 100 (sigma - sigma_MC) / sigma_MC) give the analytic sigma_a = 0.294 970 and sigma_b =
    0.057 985 of their eq. (13). Reproduced to the printed digits; S/(n - 2) > 1, so the errors as used are
    Birge-scaled (sqrt(1.483))."""
    f = linear_fit(PY_X, PY_Y, 1.0 / np.sqrt(PY_WX), 1.0 / np.sqrt(PY_WY), "line")
    a, b = f["params"]
    assert f["method"] == "york" and f["iterations"] < 50
    assert a == pytest.approx(5.47991, abs=5e-6) and b == pytest.approx(-0.480533, abs=5e-7)
    assert f["chi2_dof"] == pytest.approx(1.483, abs=5e-4)
    assert f["sigma_unscaled"][0] == pytest.approx(0.295713 * (1 - 0.002511510), rel=2e-6)
    assert f["sigma_unscaled"][1] == pytest.approx(0.058256 * (1 - 0.004644473), rel=2e-5)
    assert f["scaled"] and f["sigma"][1] == pytest.approx(f["sigma_unscaled"][1] * math.sqrt(f["chi2_dof"]), rel=1e-14)
    # cov(a, b) = -xbar sigma_b^2 (their section II), xbar the weighted mean of the adjusted x
    W = 1.0 / np.array(f["sigma_eff"]) ** 2
    x, y = np.array(PY_X), np.array(PY_Y)
    sx2, sy2 = 1.0 / np.array(PY_WX), 1.0 / np.array(PY_WY)
    Xb, Yb = float(W @ x / W.sum()), float(W @ y / W.sum())
    xa = Xb + W * ((x - Xb) * sy2 + b * (y - Yb) * sx2)
    xbar = float(W @ xa / W.sum())
    cov = np.array(f["cov"]) / (f["chi2_dof"] if f["scaled"] else 1.0)
    assert cov[0, 1] == pytest.approx(-xbar * cov[1, 1], rel=1e-12)


def test_york_is_the_minimum_of_S_and_the_effective_variance_was_not():
    """York's line minimises S(a, b) = sum (y - a - b x)^2 / (sy^2 + b^2 sx^2) (Nelder-Mead: within 1e-6 sigma_b). The
    effective variance used before (review R-E F5), written out here with the textbook sums of a weighted line and
    iterated to its fixed point, is b = -0.46345, 0.296 sigma_b away: the fixed point of the re-weighting lacks the
    term of the weights' dependence on b."""
    sx = 1.0 / np.sqrt(PY_WX)
    sy = 1.0 / np.sqrt(PY_WY)
    x, y = np.array(PY_X), np.array(PY_Y)
    f = linear_fit(x, y, sx, sy, "line")

    def S(p):
        a, b = p
        return float(np.sum((y - a - b * x) ** 2 / (sy ** 2 + b * b * sx ** 2)))

    m = optimize.minimize(S, [5.0, -0.4], method="Nelder-Mead", options={"xatol": 1e-13, "fatol": 1e-15,
                                                                          "maxiter": 20000})
    sb = f["sigma_unscaled"][1]
    b = 1.0 / sy ** 2
    w = b
    for _ in range(200):  # the effective variance's fixed point by sums
        S0, Sx, Sy, Sxx, Sxy = w.sum(), (w * x).sum(), (w * y).sum(), (w * x * x).sum(), (w * x * y).sum()
        D = S0 * Sxx - Sx * Sx
        b_ev = (S0 * Sxy - Sx * Sy) / D
        w = 1.0 / (sy ** 2 + (b_ev * sx) ** 2)
    print("Pearson-York: York", f["params"], "min S", m.x.tolist(), "EV fixed point b", b_ev)
    assert abs(f["params"][1] - m.x[1]) / sb < 1e-6 and abs(f["params"][0] - m.x[0]) < 1e-6 * f["sigma_unscaled"][0]
    assert S(f["params"]) <= S(m.x) * (1 + 1e-12)
    assert 0.25 < abs(b_ev - f["params"][1]) / sb < 0.35


@pytest.mark.parametrize("model", ["line0", "line"])
def test_line_through_the_origin_and_line_are_the_minimum_of_S_on_random_sets(model):
    """On 50 random data sets with errors in x and y (a few points with sx = 0): the minimum of S found by a bounded
    scalar search over b (a profiled for the line) agrees with York's b to 1e-9 sigma_b."""
    rng = np.random.default_rng(11)
    for _ in range(50):
        n = int(rng.integers(4, 12))
        x = np.sort(rng.uniform(0.2, 5.0, n))
        sx = rng.uniform(0.0, 0.3, n) * (rng.uniform(size=n) > 0.2)
        sy = rng.uniform(0.05, 0.3, n)
        y = (0.0 if model == "line0" else 0.7) + 1.3 * x + rng.normal(0, 1, n) * np.hypot(sy, 1.3 * sx)
        f = linear_fit(x, y, sx, sy, model)

        def S(b):
            W = 1.0 / (sy ** 2 + b * b * sx ** 2)
            a = 0.0 if model == "line0" else float(W @ (y - b * x) / W.sum())
            return float(np.sum(W * (y - a - b * x) ** 2))

        b0, sb = f["params"][-1], f["sigma_unscaled"][-1]
        r = optimize.minimize_scalar(S, bracket=(b0 - 0.5 * sb, b0, b0 + 0.5 * sb), tol=1e-14)
        assert abs(r.x - b0) < 1e-6 * sb and S(b0) <= S(r.x) * (1 + 1e-13)


def test_power_law_is_york_in_log_log():
    """A power law is York's line on (ln x, ln y) with the errors sx/x, sy/y."""
    rng = np.random.default_rng(5)
    x = np.linspace(0.2, 1.0, 9)
    y = 3.0 * x ** 0.5 * (1 + rng.normal(0, 0.01, x.size))
    sx, sy = np.full(x.size, 0.005), 0.01 * y
    f = linear_fit(x, y, sx, sy, "power")
    g = linear_fit(np.log(x), np.log(y), sx / x, sy / y, "line")
    assert f["method"] == "york" and f["params"] == pytest.approx(g["params"], rel=1e-14)
    assert f["sigma"] == pytest.approx(g["sigma"], rel=1e-14)
    assert f["A"] == pytest.approx(math.exp(g["params"][0]), rel=1e-15)
