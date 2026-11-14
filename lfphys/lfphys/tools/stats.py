# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Statistics of the accumulated screen and independent references.

* ``coherence_ml``: the degree of coherence |gamma_12| of two slits from a histogram (Poisson maximum likelihood)
  or a smooth curve, with the slit envelopes' ratio fixed by the run's own marks (review R2).
* ``coherence_boot_err``: its standard error by a parametric bootstrap (the Fisher error is only asymptotic).
* ``chi2``: Pearson chi-square of the histogram against the ensemble prediction (bins with expectation >= 5).
* ``linear_fit``: the lab work's fit (design explore_2026-11-14 §2.3): y = b x, y = a + b x, y = a + b x + c x^2 (with
  its vertex) or y = A x^n (a line in log-log), weighted least squares with the effective variance for errors in x and
  y, the parameters' errors scaled by the Birge ratio when chi^2/dof > 1.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats as sps

from lfphys.i18n import T

ABOUT = {
    "layer": 'tools', "kind": 'statistics',
    "title": T("Statistics of simulated data"),
    "statement": T("The estimate of the degree of coherence from a histogram (Poisson maximum likelihood, parametric "
                   "bootstrap), χ², the fringe period; the lab work's least-squares fit of a line, a line through the "
                   "origin, a parabola (with its vertex) or a power law, with errors in x and y (the effective "
                   "variance) and the Birge scaling of the parameters' errors."),
    "validity": T("a tool, not physics"),
    "basis": [T("Orear, Notes on Statistics for Physicists, Revised (Cornell LNS, 1982), Appendix III, eqs. (36)–(37): "
                "the effective variance; Orear, Am. J. Phys. 50, 912 (1982)"),
              T("Particle Data Group, Review of Particle Physics 2024, Introduction, section 5.2.2: the scale factor "
                "S = [χ²/(N − 1)]^½; Birge, Phys. Rev. 40, 207 (1932)")],
    "conflicts": [],
}


def coherence_ml(h, b11, b22, b12, g11, g22, dark=None, poisson=True, iters=40):
    """Degree of coherence |gamma_12| of two slits (review R2: the 4-parameter fit was ill-conditioned).

    Model per bin: mu = c0 (g11 b11 + g22 b22) + c3 Re b12 + c4 Im b12 + dark, with the slit basis b_jl = A_j A_l^*
    of the run (integrated over the bins), the slits' relative transmissions g11, g22 known from the marks, and the
    known dark counts. Since P = G11 |A1|^2 + G22 |A2|^2 + 2 Re(G12 A1 A2^*), G12 = (c3 - i c4) / (2 c0) and
    |gamma| = |c3 - i c4| / (2 c0 sqrt(g11 g22)). poisson=True: maximum likelihood for counts (Fisher scoring, error
    from the Fisher matrix); False: least squares weighted by the model (Pearson) for a smooth curve.
    Returns (|gamma|, standard error or None)."""
    h = np.asarray(h, float)
    d = np.zeros_like(h) if dark is None else np.asarray(dark, float)
    X = np.stack([g11 * b11 + g22 * b22, b12.real, b12.imag], axis=1)
    y = h - d
    floor = 1e-9 * max(float(np.max(np.abs(h))), 1e-300)
    beta = _fit_beta(h, X, d, iters)
    if beta is None:
        return None, None
    c0, c3, c4 = beta
    if not (c0 > 0) or g11 <= 0 or g22 <= 0:
        return None, None
    amp = math.hypot(c3, c4)
    gam = amp / (2.0 * c0 * math.sqrt(g11 * g22))
    err = None
    try:
        mu = np.maximum(X @ beta + d, floor)
        cov = np.linalg.inv((X / mu[:, None]).T @ X)
        if not poisson:
            cov = cov * float(np.sum((y - X @ beta) ** 2 / mu)) / max(len(h) - 3, 1)
        grad = np.array([-gam / c0, c3 / (max(amp, 1e-300) * 2 * c0 * math.sqrt(g11 * g22)),
                         c4 / (max(amp, 1e-300) * 2 * c0 * math.sqrt(g11 * g22))])
        err = float(math.sqrt(max(grad @ cov @ grad, 0.0)))
    except np.linalg.LinAlgError:
        pass
    return float(gam), err


def coherence_boot_err(h, b11, b22, b12, g11, g22, dark=None, rng=None, n_boot=60):
    """Standard error of the histogram |gamma_12| by a parametric bootstrap: Poisson counts drawn from the fitted model,
    refitted. The Fisher error of coherence_ml is only asymptotic: near |gamma| = 1 the expected minima are ~0, the
    information there diverges, and at N = 100 detections the Fisher error was 14x smaller than the real scatter
    (response to the v02 review). Returns (std of the refits or None, number of successful refits)."""
    rng = rng or np.random.default_rng(0)
    h = np.asarray(h, float)
    d = np.zeros_like(h) if dark is None else np.asarray(dark, float)
    gam, _ = coherence_ml(h, b11, b22, b12, g11, g22, dark=d)
    if gam is None:
        return None, 0
    X = np.stack([g11 * b11 + g22 * b22, b12.real, b12.imag], axis=1)
    # the fitted model again (coherence_ml returns only |gamma|): weighted least squares then the same scoring
    beta = _fit_beta(h, X, d)
    if beta is None:
        return None, 0
    mu = np.maximum(X @ beta + d, 0.0)
    vals = []
    for _ in range(n_boot):
        g_b, _ = coherence_ml(rng.poisson(mu).astype(float), b11, b22, b12, g11, g22, dark=d)
        if g_b is not None:
            vals.append(g_b)
    if len(vals) < max(10, n_boot // 2):
        return None, len(vals)
    return float(np.std(vals, ddof=1)), len(vals)


def _fit_beta(h, X, d, iters=40):
    y = h - d
    beta, *_ = np.linalg.lstsq(X / np.sqrt(np.maximum(h, 1.0))[:, None], y / np.sqrt(np.maximum(h, 1.0)), rcond=None)
    floor = 1e-9 * max(float(np.max(np.abs(h))), 1e-300)
    for _ in range(iters):
        mu = np.maximum(X @ beta + d, floor)
        W = 1.0 / mu
        try:
            nb = np.linalg.solve((X * W[:, None]).T @ X, (X * W[:, None]).T @ y)
        except np.linalg.LinAlgError:
            return None
        if np.allclose(nb, beta, rtol=1e-12, atol=0.0):
            return nb
        beta = nb
    return beta


def chi2(counts, expected):
    """expected: any non-negative weights per bin; scaled to the total count (shape test only)."""
    e_all = expected * counts.sum() / max(expected.sum(), 1e-300)
    m = e_all >= 5
    if m.sum() < 3:
        return None, None, 0
    c = counts[m]
    e = e_all[m] * c.sum() / e_all[m].sum()
    x2 = float(np.sum((c - e) ** 2 / e))
    dof = int(m.sum() - 1)
    return x2, float(sps.chi2.sf(x2, dof)), dof


def fringe_period_from_curve(x, P, env, guess, window):
    """Period of the fringes: least-squares fit of r(x) = P/env = c0 + c1 cos(2 pi f x) + c2 sin(2 pi f x) in the
    window |x| < window, minimising the residual over f (scan, then golden-section refinement). Dividing by the
    incoherent envelope removes its bias on the frequency."""
    m = (np.abs(x) <= window) & (env > 1e-9 * env.max())
    if m.sum() < 16:
        return None
    xs, r = x[m], P[m] / env[m]

    def resid(f):
        X = np.stack([np.ones_like(xs), np.cos(2 * math.pi * f * xs), np.sin(2 * math.pi * f * xs)], axis=1)
        coef, res, *_ = np.linalg.lstsq(X, r, rcond=None)
        return float(np.sum((X @ coef - r) ** 2))

    fs = np.linspace(0.7 / guess, 1.3 / guess, 601)
    vals = [resid(f) for f in fs]
    i = int(np.argmin(vals))
    lo, hi = fs[max(i - 1, 0)], fs[min(i + 1, len(fs) - 1)]
    g = (math.sqrt(5) - 1) / 2
    c, d = hi - g * (hi - lo), lo + g * (hi - lo)
    fc, fd = resid(c), resid(d)
    for _ in range(80):
        if fc < fd:
            hi, d, fd = d, c, fc
            c = hi - g * (hi - lo)
            fc = resid(c)
        else:
            lo, c, fc = c, d, fd
            d = lo + g * (hi - lo)
            fd = resid(d)
    return float(2.0 / (lo + hi))


# --- the lab work's fit -----------------------------------------------------------------------------------------------
# The effective variance (Orear, "Notes on Statistics for Physicists, Revised", Cornell LNS 1982, Appendix III, read on
# 2026-11-14 at ned.ipac.caltech.edu/level5/Sept01/Orear/Orear21.html: eq. (36) sigma~_j^2 = [df/dx]_j^2 [Delta x_j]^2
# + [Delta y_j]^2, eq. (37) S = sum [(y_j - f(x_j)) / sigma~_j]^2; "guess starting values for df/dx and then solve for
# the parameters ... Then new [df/dx]_j can be evaluated and the procedure repeated. Usually only two iterations are
# necessary"; the same method in Orear, Am. J. Phys. 50, 912 (1982), whose full text, Lybanon's comment (Am. J. Phys.
# 52, 276 (1984)) and Orear's erratum (52, 278) were not read). The iterated solution is the fixed point of the
# re-weighting, sum_j x_j r_j / sigma~_j^2 = 0; the minimum of S with b-dependent sigma~_j has the extra term
# b sigma_x^2 sum r_j^2 / sigma~_j^4, so the two differ when the x errors matter (measured on Pearson's data with York's
# weights, tests/test_stats_fit.py: the fixed point b = -0.4634, the minimum of S b = -0.4805, 0.30 sigma_b apart; three
# re-weightings are within 1e-5 sigma_b of the fixed point). The design fixes three re-weightings after a start with
# sigma_y alone (``ITERATIONS``), so that the player's fit.js reproduces this to 1e-12.
# The Birge scaling: the covariance multiplied by chi^2/dof when that exceeds 1 (the Particle Data Group's scale factor
# S = [chi^2/(N - 1)]^(1/2) of an average, Review of Particle Physics 2024, Introduction, section 5.2.2, applied here to
# a fit with dof = n - p; R. T. Birge, Phys. Rev. 40, 207 (1932), cited for the name only, not read).
FIT_MODELS = ("line0", "line", "quadratic", "power")
ITERATIONS = 3


def _design(model, x):
    if model == "line0":
        return x[:, None]
    if model in ("line", "power"):
        return np.stack([np.ones_like(x), x], axis=1)
    return np.stack([np.ones_like(x), x, x * x], axis=1)


def _slope(model, p, x):
    """df/dx at x for the parameters p (in the fitted coordinates)."""
    if model == "line0":
        return np.full_like(x, p[0])
    if model in ("line", "power"):
        return np.full_like(x, p[1])
    return p[1] + 2.0 * p[2] * x


def _wls(X, y, sig):
    """Weighted least squares by QR of the column-scaled, row-weighted matrix: the parameters and (X^T W X)^-1."""
    A = X / sig[:, None]
    norms = np.linalg.norm(A, axis=0)
    norms[norms == 0] = 1.0
    Q, R = np.linalg.qr(A / norms)
    p = np.linalg.solve(R, Q.T @ (y / sig)) / norms
    Ri = np.linalg.inv(R)
    cov = (Ri @ Ri.T) / np.outer(norms, norms)
    return p, cov


def linear_fit(x, y, sx=0.0, sy=0.0, model: str = "line", iterations: int = ITERATIONS) -> dict:
    """Fit ``model`` to points (x, y) with standard errors sx, sy (scalars or arrays, >= 0).

    Models: "line0" y = b x; "line" y = a + b x; "quadratic" y = a + b x + c x^2 (also its vertex x* = -b/(2c) and its
    error from the covariance); "power" y = A x^n, fitted as ln y = ln A + n ln x with the errors sx/x and sy/y (x, y >
    0). The algorithm (the contract with the player's fit.js): the start is a weighted least-squares fit with sigma_y
    alone (unit weights if any sigma_y is 0); then ``iterations`` times: sigma_i^2 = sy_i^2 + (f'(x_i) sx_i)^2 with f'
    from the previous parameters, and a weighted least-squares fit with weights 1/sigma_i^2. The covariance is
    (X^T W X)^-1 with the last weights; chi^2 = sum r_i^2 / sigma_i^2 with the same sigma_i; dof = n - p. When
    chi^2/dof > 1 the covariance is multiplied by chi^2/dof (the Birge ratio squared) and ``scaled`` is True.
    Readings without errors (every sx and sy 0), or a point whose sigma_i comes out 0, are fitted by ordinary least
    squares (``unit``: unit weights, the errors always from the scatter, s^2 (X^T X)^-1 with s^2 = RSS / dof; chi2,
    chi2_dof, birge and sigma_eff are then None). Returns a dict: params, names, sigma (as used: scaled or not),
    sigma_unscaled, cov, chi2, dof, chi2_dof, birge, scaled, unit, sigma_eff (sigma_i), n, model; quadratic: vertex,
    vertex_sigma; power: A, A_sigma, n_exp, n_exp_sigma (params are then ln A and n). Unlike fit.js it refuses
    non-finite values and negative errors instead of dropping or taking their absolute value."""
    if model not in FIT_MODELS:
        raise ValueError(T("fit model {m}: one of line0, line, quadratic, power", m=str(model)))
    if not (isinstance(iterations, (int, np.integer)) and iterations >= 1):
        raise ValueError(T("the fit needs at least one re-weighting"))
    x = np.asarray(x, float).ravel()
    y = np.asarray(y, float).ravel()
    n = x.size
    sx = np.broadcast_to(np.asarray(sx, float), (n,)).astype(float) if np.ndim(sx) == 0 else np.asarray(sx, float)
    sy = np.broadcast_to(np.asarray(sy, float), (n,)).astype(float) if np.ndim(sy) == 0 else np.asarray(sy, float)
    if y.size != n or sx.size != n or sy.size != n:
        raise ValueError(T("x, y and their errors must have the same length"))
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y)) and np.all(np.isfinite(sx)) and np.all(np.isfinite(sy))):
        raise ValueError(T("the data contain a value that is not a finite number"))
    if np.any(sx < 0) or np.any(sy < 0):
        raise ValueError(T("the errors must be ≥ 0"))
    if model == "power":
        if np.any(x <= 0) or np.any(y <= 0):
            raise ValueError(T("a power law is fitted in log-log: x and y must be > 0"))
        sx, sy, x, y = sx / x, sy / y, np.log(x), np.log(y)
    npar = {"line0": 1, "line": 2, "quadratic": 3, "power": 2}[model]
    if n <= npar:
        raise ValueError(T("the fit needs more points than parameters (points: {n}, parameters: {p})", n=n, p=npar))
    X = _design(model, x)
    unit = not (np.any(sx > 0) or np.any(sy > 0))  # readings without errors: ordinary least squares
    p, cov = _wls(X, y, sy if np.all(sy > 0) else np.ones(n))  # the start: sigma_y alone (unit weights if one is 0)
    sig = np.ones(n)
    if not unit:
        for _ in range(int(iterations)):
            sig = np.sqrt(sy * sy + (_slope(model, p, x) * sx) ** 2)
            if np.any(sig <= 0):  # a reading without any error: ordinary least squares, as fit.js
                unit = True
                break
            p, cov = _wls(X, y, sig)
    if unit:
        sig = np.ones(n)
        p, cov = _wls(X, y, sig)
    r = y - X @ p
    chi2v = float(np.sum((r / sig) ** 2))
    dof = n - npar
    ratio = chi2v / dof
    scaled = True if unit else ratio > 1.0
    cov_s = cov * ratio if scaled else cov
    out = {"model": model, "params": [float(v) for v in p],
           "names": {"line0": ["b"], "line": ["a", "b"], "quadratic": ["a", "b", "c"], "power": ["lnA", "n"]}[model],
           "sigma": [float(v) for v in np.sqrt(np.diag(cov_s))],
           "sigma_unscaled": [float(v) for v in np.sqrt(np.diag(cov))],
           "cov": cov_s.tolist(), "chi2": None if unit else chi2v, "dof": dof, "chi2_dof": None if unit else ratio,
           "birge": None if unit else math.sqrt(ratio), "scaled": bool(scaled), "unit": bool(unit),
           "sigma_eff": None if unit else sig.tolist(), "n": n, "iterations": int(iterations)}
    if model == "quadratic":
        a, b, c = p
        if c != 0:
            xs = -b / (2.0 * c)
            grad = np.array([0.0, -1.0 / (2.0 * c), b / (2.0 * c * c)])
            out["vertex"] = float(xs)
            out["vertex_sigma"] = float(math.sqrt(grad @ cov_s @ grad))
        else:
            out["vertex"], out["vertex_sigma"] = None, None
    if model == "power":
        A = math.exp(p[0])
        out.update({"A": A, "A_sigma": A * out["sigma"][0], "n_exp": float(p[1]), "n_exp_sigma": out["sigma"][1]})
    return out
