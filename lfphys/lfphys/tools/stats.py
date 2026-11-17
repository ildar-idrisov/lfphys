# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Statistics of the accumulated screen and independent references.

* ``coherence_ml``: the degree of coherence |gamma_12| of two slits from a histogram (Poisson maximum likelihood)
  or a smooth curve, with the slit envelopes' ratio fixed by the run's own marks (review R2).
* ``coherence_boot`` (and ``coherence_boot_err``): its standard error by a parametric bootstrap from the fitted model
  projected onto |gamma| <= 1, as the refits' central 68 % half-width, or None with the reason (too few hits, a failed
  fit or refits); the Fisher error is only asymptotic (review R-W F2).
* ``chi2``: Pearson chi-square of the histogram against the ensemble prediction (bins with expectation >= 5).
* ``linear_fit``: the lab work's fit (design explore_2026-11-14 §2.3): y = b x, y = a + b x, y = a + b x + c x^2 (with
  its vertex) or y = A x^n (a line in log-log). Straight lines with errors in x and y by York et al. (2004), the
  parabola by the effective variance (an approximation); the parameters' errors scaled by the Birge ratio when
  chi^2/dof > 1 (review R-E F5, F8).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats as sps

from lfphys.codes import coded
from lfphys.i18n import T

ABOUT = {
    "layer": 'tools', "kind": 'statistics',
    "title": T("Statistics of simulated data"),
    "statement": T("The estimate of the degree of coherence from a histogram (Poisson maximum likelihood; its error by "
                   "a parametric bootstrap, given from enough hits), χ², the fringe period; the lab work's "
                   "least-squares fit of a line, a line through the origin, a parabola (with its vertex) or a power "
                   "law, with errors in x and y (York's line for the straight lines and the power law; the effective "
                   "variance, an approximation, for the parabola) and the Birge scaling of the parameters' errors."),
    "validity": T("a tool, not physics"),
    "basis": [T("York, Evensen, Martínez López & De Basabe Delgado, Am. J. Phys. 72, 367 (2004), eqs. (13): the "
                "straight line with errors in x and y"),
              T("Orear, Notes on Statistics for Physicists, Revised (Cornell LNS, 1982), Appendix III, eqs. (36)–(37): "
                "the effective variance; Orear, Am. J. Phys. 50, 912 (1982)"),
              T("Particle Data Group, Review of Particle Physics 2024, Introduction, section 5.2.2: the scale factor "
                "S = [χ²/(N − 1)]^½; Birge, Phys. Rev. 40, 207 (1932)")],
    "conflicts": [],
}


def coherence_ml(h, b11, b22, b12, g11, g22, dark=None, poisson=True, iters=100):
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


#: the bootstrap error of |gamma_12| is given from this many hits (counts in the histogram) on; below it the error is
#: None with the reason (review R-W F2: the calibration study, tests/test_stats_coherence.py)
COH_BOOT_MIN_HITS = 300
#: the share of the bootstrap's refits that must succeed for its error to be given
COH_BOOT_MIN_SHARE = 0.9
_Q16, _Q84 = 100.0 * sps.norm.cdf(-1.0), 100.0 * sps.norm.cdf(1.0)


def _boot_spread(mu, b11, b22, b12, g11, g22, d, rng, n_boot):
    """The standard deviation of ``n_boot`` refits of |gamma| to Poisson draws from mu, and the number of successful
    refits (a refit further than 10 central half-widths from the median, a failed one in effect, is not counted)."""
    vals = []
    for _ in range(int(n_boot)):
        g_b, _ = coherence_ml(rng.poisson(mu).astype(float), b11, b22, b12, g11, g22, dark=d)
        if g_b is not None:
            vals.append(g_b)
    if len(vals) < 2:
        return None, len(vals)
    v = np.asarray(vals)
    med = float(np.median(v))
    q16, q84 = np.percentile(v, [_Q16, _Q84])
    v = v[np.abs(v - med) <= 10.0 * max(0.5 * (q84 - q16), 1e-12 * max(abs(med), 1.0))]
    if v.size < 2:
        return None, int(v.size)
    return float(np.std(v, ddof=1)), int(v.size)


def coherence_boot(h, b11, b22, b12, g11, g22, dark=None, rng=None, n_boot: int = 100) -> dict:
    """The standard error of the histogram's |gamma_12| (``coherence_ml``) by a parametric bootstrap, and why there is
    none. The Fisher error of coherence_ml is only asymptotic: near |gamma| = 1 the expected minima are ~0, the
    information there diverges, and at N = 100 detections the Fisher error was 14x smaller than the real scatter
    (response to the v02 review).

    The counts are drawn from the fitted model projected onto |gamma| <= 1 (c3, c4 scaled down when the fit's |gamma|
    exceeds 1), so that its expectation is >= 0 in every bin (|b12|^2 <= b11 b22 bin by bin) and no bin is clipped;
    ``n_boot`` draws are refitted and the error is the refits' standard deviation. Near full coherence the estimate's
    scatter changes fast with the true |gamma| (at |gamma| = 1 the darkest bins expect almost nothing, and the estimate
    scatters widely above 1 and narrowly below it), so when the estimate lies within two errors of 1 the draws are
    repeated from the same model at |gamma| = 1 and the larger spread is stated (a conservative error: the scatter of
    the plausible true value that scatters most). Review R-W F2: the earlier version drew from the unprojected model with
    its negative bins clipped to 0, whose refits all landed on nearly the same |gamma| (an error of 0.0003 at 662 hits
    where the scatter is 0.02), and one wild refit made it 0.43.

    Returns {"err": float or None, "why": a text (lfphys.i18n.T) or None, "n_ok": successful refits (of the last
    bootstrap), "n_boot", "hits": the histogram's total count, "boundary": True when the |gamma| = 1 model was also
    drawn}. err is None, with why, when the histogram has fewer than COH_BOOT_MIN_HITS hits (where the error is not
    calibrated near full coherence: tests/test_stats_coherence.py), when the fit fails, or when fewer than
    COH_BOOT_MIN_SHARE of the refits succeed."""
    rng = rng or np.random.default_rng(0)
    h = np.asarray(h, float)
    d = np.zeros_like(h) if dark is None else np.asarray(dark, float)
    hits = float(h.sum())
    out = {"err": None, "why": None, "n_ok": 0, "n_boot": int(n_boot), "hits": hits, "boundary": False}
    if hits < COH_BOOT_MIN_HITS:
        out["why"] = T("too few hits for the error of |γ₁₂| ({n:d} < {m:d})", n=int(round(hits)), m=COH_BOOT_MIN_HITS)
        return out
    X = np.stack([g11 * b11 + g22 * b22, b12.real, b12.imag], axis=1)
    beta = _fit_beta(h, X, d)
    if beta is None or not beta[0] > 0 or g11 <= 0 or g22 <= 0:
        out["why"] = T("the fit of |γ₁₂| failed")
        return out
    gam = math.hypot(beta[1], beta[2]) / (2.0 * beta[0] * math.sqrt(g11 * g22))

    def model(g_to):
        sc = g_to / gam if gam > 0 else 0.0
        return np.maximum(X @ np.array([beta[0], beta[1] * sc, beta[2] * sc]) + d, 0.0)  # the clip: round-off only

    def failed(n_ok):
        out["why"] = T("only {k:d} of {n:d} bootstrap refits of |γ₁₂| succeeded", k=n_ok, n=int(n_boot))
        return out

    err, n_ok = _boot_spread(model(min(gam, 1.0)), b11, b22, b12, g11, g22, d, rng, n_boot)
    out["n_ok"] = n_ok
    if err is None or n_ok < COH_BOOT_MIN_SHARE * n_boot:
        return failed(n_ok)
    if gam < 1.0 and gam + 2.0 * err >= 1.0 and gam > 0:
        e1, n1 = _boot_spread(model(1.0), b11, b22, b12, g11, g22, d, rng, n_boot)
        out["n_ok"], out["boundary"] = n1, True
        if e1 is None or n1 < COH_BOOT_MIN_SHARE * n_boot:
            return failed(n1)
        err = max(err, e1)
    out["err"] = err
    return out


def coherence_boot_err(h, b11, b22, b12, g11, g22, dark=None, rng=None, n_boot: int = 100):
    """``coherence_boot``'s (err or None, number of successful refits)."""
    r = coherence_boot(h, b11, b22, b12, g11, g22, dark=dark, rng=rng, n_boot=n_boot)
    return r["err"], r["n_ok"]


def _fit_beta(h, X, d, iters=100):
    """Poisson maximum likelihood of mu = X beta + d for the counts h: L = sum_(h > 0) h ln mu - sum mu, concave in
    beta. Newton's method with the observed information X^T diag(h / mu^2) X and backtracking: every step keeps mu > 0
    in the bins with counts and does not lower L, so it climbs to the one maximum. The start is a weighted least-squares
    fit, or the incoherent pattern (c3 = c4 = 0) when that start leaves a bin with counts at mu <= 0. Review R-W F2: the
    scoring used before weighted each bin by 1 / max(mu, floor); where mu fell below 0 in bins with counts that floor
    made huge weights, and in 0.3 % of the histograms at |gamma| = 1, N = 2000 it settled on a point of no likelihood
    with |gamma| up to 7.5. At a regular maximum (mu > 0 everywhere) both give the same beta. None when the counts do
    not determine the three coefficients."""
    h = np.asarray(h, float)
    pos = h > 0
    if int(pos.sum()) < X.shape[1]:
        return None
    y = h - d
    w = 1.0 / np.sqrt(np.maximum(h, 1.0))
    beta, *_ = np.linalg.lstsq(X * w[:, None], y * w, rcond=None)

    def like(b):
        mu = X @ b + d
        if not np.all(mu[pos] > 0):
            return -math.inf, mu
        return float(np.sum(h[pos] * np.log(mu[pos])) - np.sum(mu)), mu

    L, mu = like(beta)
    if not math.isfinite(L):
        s0 = float(np.sum(X[:, 0]))
        c0 = float(np.sum(y)) / s0 if s0 > 0 else 0.0
        beta = np.array([c0, 0.0, 0.0])
        L, mu = like(beta)
        if not math.isfinite(L):
            return None
    for _ in range(iters):
        r = np.where(pos, h / np.where(pos, mu, 1.0), 0.0)
        grad = X.T @ (r - 1.0)
        info = (X * (np.where(pos, r / np.where(pos, mu, 1.0), 0.0))[:, None]).T @ X
        try:
            step = np.linalg.solve(info, grad)
        except np.linalg.LinAlgError:
            return None
        if not np.all(np.isfinite(step)):
            return None
        t = 1.0
        while True:
            nb = beta + t * step
            Ln, mun = like(nb)
            if Ln >= L - 1e-14 * abs(L):
                break
            t *= 0.5
            if t < 1e-12:
                return beta
        done = np.all(np.abs(nb - beta) <= 1e-12 * np.max(np.abs(nb)))
        beta, L, mu = nb, max(L, Ln), mun
        if done:
            break
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
# Straight lines with errors in x and y ("line", "line0", and "power" as a line in log-log): York, Evensen, Martínez
# López & De Basabe Delgado, "Unified equations for the slope, intercept, and standard errors of the best straight
# line", Am. J. Phys. 72, 367 (2004), read on 2026-11-17 (the AIP PDF): Table I, eqs. (13a)-(13d) and the steps (1)-(10) of
# their section III, with uncorrelated errors (r_i = 0):
#     W_i = 1 / (sy_i^2 + b^2 sx_i^2),  Xbar = sum W X / sum W,  U_i = X_i - Xbar,  V_i = Y_i - Ybar,
#     beta_i = W_i (U_i sy_i^2 + b V_i sx_i^2),  b = sum W beta V / sum W beta U  (iterated),  a = Ybar - b Xbar,
#     the adjusted x_i = Xbar + beta_i,  u_i = x_i - xbar,  sigma_b^2 = 1 / sum W u^2,  sigma_a^2 = 1 / sum W + xbar^2
#     sigma_b^2,  and (their section II) cov(a, b) = -xbar sigma_b^2.
# The solution is the minimum of S = sum W_i (Y_i - a - b X_i)^2 with the weights' dependence on b (the maximum
# likelihood for Gaussian errors), and these errors are the maximum-likelihood ones (the paper's unification). The
# benchmark: Pearson's data with York's weights, the paper's Table II data set 3 (a = 5.47991, b = -0.480533, S/(n - 2)
# = 1.483; sigma_a = 0.294970 and sigma_b = 0.057985 from the table's Monte Carlo sigma and its Delta), reproduced in
# tests/test_stats_fit.py. The iteration stops when successive slopes agree within YORK_TOL of the slope's scale (the
# paper: "for example, one part in 10^15"; "about ten iterations for most data sets, and fewer than 50 for pathological
# data sets"); at most YORK_MAX_ITER, else a refusal ("fit.no_convergence").
# The line through the origin: the same equations with the intercept fixed at 0, i.e. Xbar = Ybar = 0 (U = X, V = Y),
# the adjusted x_i = beta_i and sigma_b^2 = 1 / sum W x_i^2 (no centring). Derived here, not in the paper: the
# stationarity of S(b) = sum W (Y - b X)^2 is sum W^2 (Y - b X)(X sy^2 + b Y sx^2) = 0, which is York's b with U = X,
# V = Y; the error is the inverse Fisher information of b with the true abscissae profiled out, sum W xi^2. Tested
# against the minimum of S and against Monte Carlo.
# Review R-E F5 (the integrator's decision D3): the effective variance used for lines before was the fixed point of a
# re-weighting, not the minimum of S (0.30 sigma_b off on Pearson-York), and, with random x errors comparable to the
# spread of x, the attenuated slope of ordinary least squares (95 % intervals covering 54 % and 36 %).
#
# The parabola keeps the effective variance (Orear, "Notes on Statistics for Physicists, Revised", Cornell LNS 1982,
# Appendix III, read on 2026-11-14 at ned.ipac.caltech.edu/level5/Sept01/Orear/Orear21.html: eq. (36) sigma~_j^2 =
# [df/dx]_j^2 [Delta x_j]^2 + [Delta y_j]^2, eq. (37) S = sum [(y_j - f(x_j)) / sigma~_j]^2; "guess starting values for
# df/dx and then solve for the parameters ... Then new [df/dx]_j can be evaluated and the procedure repeated. Usually
# only two iterations are necessary"; Orear, Am. J. Phys. 50, 912 (1982), Lybanon's comment (52, 276 (1984)) and
# Orear's erratum (52, 278) not read): three re-weightings after a start with sigma_y alone (``ITERATIONS``). It is an
# approximation, not the minimum of S: the fixed point of the re-weighting, sum_j x_j r_j / sigma~_j^2 = 0, lacks the
# term of the weights' dependence on the parameters, and it is biased when random x errors are comparable to the spread
# of x. On S03's lab C (the protractor's 0.5° on throws of 15–75°) the fixed point equals the minimum of S within
# 0.001 sigma (review R-E, i_lab_more.out).
# The Birge scaling: the covariance multiplied by chi^2/dof when that exceeds 1 (the Particle Data Group's scale factor
# S = [chi^2/(N - 1)]^(1/2) of an average, Review of Particle Physics 2024, Introduction, section 5.2.2, applied here to
# a fit with dof = n - p; R. T. Birge, Phys. Rev. 40, 207 (1932), cited for the name only, not read).
# The player's fit.js implements the same algorithm (spec: lfphys/sources/verification_2026-11-17_york_fit.md; fit.test.mjs compares to 1e-12).
FIT_MODELS = ("line0", "line", "quadratic", "power")
ITERATIONS = 3
#: York's iteration: successive slopes agree within YORK_TOL (|b_new - b| <= YORK_TOL (|b_new| + sqrt(sum W V^2 /
#: sum W U^2))), at most YORK_MAX_ITER iterations
YORK_TOL = 1e-14
YORK_MAX_ITER = 200
#: a design whose QR diagonal has |R_jj| <= SINGULAR |R_00| (columns scaled to unit norm) does not determine the fit
SINGULAR = 1e-14


def _singular():
    return coded(ValueError(T("the points do not determine the fit (all x equal, or fewer distinct x than "
                              "parameters)")), "fit.singular")


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
    """Weighted least squares by QR of the column-scaled, row-weighted matrix: the parameters and (X^T W X)^-1. A design
    with |R_jj| <= SINGULAR |R_00| is refused ("fit.singular"), as in fit.js."""
    A = X / sig[:, None]
    norms = np.linalg.norm(A, axis=0)
    norms[norms == 0] = 1.0
    Q, R = np.linalg.qr(A / norms)
    d = np.abs(np.diag(R))
    if not np.all(d > SINGULAR * d[0]):
        raise _singular()
    p = np.linalg.solve(R, Q.T @ (y / sig)) / norms
    Ri = np.linalg.inv(R)
    cov = (Ri @ Ri.T) / np.outer(norms, norms)
    return p, cov


def _york(x, y, sx, sy, b, origin):
    """York et al. (2004), eqs. (13), r_i = 0, from the start slope b (see the comment above); ``origin``: the line
    through the origin. Returns (params, cov, W, iterations), or None when a weight is not finite (a point without any
    error at this slope: the caller fits by ordinary least squares)."""
    vx, vy = sx * sx, sy * sy

    def weights(b):
        with np.errstate(divide="ignore"):
            W = 1.0 / (vy + b * b * vx)
        return W if np.all(np.isfinite(W)) else None

    def centre(W):
        if origin:
            return 0.0, 0.0, x, y
        sw = float(np.sum(W))
        Xb, Yb = float(np.sum(W * x)) / sw, float(np.sum(W * y)) / sw
        return Xb, Yb, x - Xb, y - Yb

    it = 0
    while True:
        it += 1
        W = weights(b)
        if W is None:
            return None
        _, _, U, V = centre(W)
        beta = W * (U * vy + b * V * vx)
        den, num = float(np.sum(W * beta * U)), float(np.sum(W * beta * V))
        if not (den > 0 and math.isfinite(num)):
            raise coded(ValueError(T("the fit with errors in x and y does not converge")), "fit.no_convergence")
        b_new = num / den
        scale = math.sqrt(float(np.sum(W * V * V)) / float(np.sum(W * U * U)))
        done = abs(b_new - b) <= YORK_TOL * (abs(b_new) + scale)
        b = b_new
        if done:
            break
        if it >= YORK_MAX_ITER:
            raise coded(ValueError(T("the fit with errors in x and y does not converge")), "fit.no_convergence")
    W = weights(b)  # steps (7)-(10) at the converged slope
    if W is None:
        return None
    Xb, Yb, U, V = centre(W)
    beta = W * (U * vy + b * V * vx)
    xa = Xb + beta  # the least-squares-adjusted abscissae
    if origin:
        Su = float(np.sum(W * xa * xa))
        if not Su > 0:
            raise _singular()
        return np.array([b]), np.array([[1.0 / Su]]), W, it
    sw = float(np.sum(W))
    xm = float(np.sum(W * xa)) / sw
    u = xa - xm
    Su = float(np.sum(W * u * u))
    if not Su > 0:
        raise _singular()
    vb = 1.0 / Su
    cov = np.array([[1.0 / sw + xm * xm * vb, -xm * vb], [-xm * vb, vb]])
    return np.array([Yb - b * Xb, b]), cov, W, it


def linear_fit(x, y, sx=0.0, sy=0.0, model: str = "line", iterations: int = ITERATIONS) -> dict:
    """Fit ``model`` to points (x, y) with standard errors sx, sy (scalars or arrays, >= 0).

    Models: "line0" y = b x; "line" y = a + b x; "quadratic" y = a + b x + c x^2 (also its vertex x* = -b/(2c) and its
    error from the covariance); "power" y = A x^n, fitted as ln y = ln A + n ln x with the errors sx/x and sy/y (x, y >
    0). The algorithm (the contract with the player's fit.js): the start is a weighted least-squares fit with sigma_y
    alone (unit weights if any sigma_y is 0), by QR, which also refuses a singular design ("fit.singular": all x equal,
    or fewer distinct x than parameters). Then, for the straight lines (line0, line, power in log-log), York's
    iteration from the start's slope to convergence (York et al. 2004: the minimum of S = sum (y_i - f(x_i))^2 /
    (sy_i^2 + b^2 sx_i^2) and the maximum-likelihood errors; the comment above); for the parabola, the effective
    variance: ``iterations`` times sigma_i^2 = sy_i^2 + (f'(x_i) sx_i)^2 with f' from the previous parameters and a
    weighted least-squares fit with weights 1/sigma_i^2 (an approximation, biased when random x errors are comparable
    to the spread of x). sigma_i is the effective error of each point (York: 1/sqrt(W_i)); chi^2 = sum r_i^2 /
    sigma_i^2 (York's S); dof = n - p. When chi^2/dof > 1 the covariance is multiplied by chi^2/dof (the Birge ratio
    squared) and ``scaled`` is True. Readings without errors (every sx and sy 0), or a point whose sigma_i comes out 0,
    are fitted by ordinary least squares (``unit``: unit weights, the errors always from the scatter, s^2 (X^T X)^-1
    with s^2 = RSS / dof; chi2, chi2_dof, birge and sigma_eff are then None). Returns a dict: params, names, sigma (as
    used: scaled or not), sigma_unscaled, cov, chi2, dof, chi2_dof, birge, scaled, unit, sigma_eff (sigma_i), n,
    model, method ("york", "effective_variance" or "ols"), iterations (York's iterations or the re-weightings, 0 for
    ols); quadratic: vertex, vertex_sigma; power: A, A_sigma, n_exp, n_exp_sigma (params are then ln A and n). Unlike
    fit.js it refuses non-finite values and negative errors instead of dropping or taking their absolute value."""
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
    method, its = "ols", 0
    if not unit and model == "quadratic":
        method = "effective_variance"
        for _ in range(int(iterations)):
            sig = np.sqrt(sy * sy + (_slope(model, p, x) * sx) ** 2)
            if np.any(sig <= 0):  # a reading without any error: ordinary least squares, as fit.js
                unit = True
                break
            p, cov = _wls(X, y, sig)
            its += 1
    elif not unit:
        res = _york(x, y, sx, sy, float(p[-1]), model == "line0")
        if res is None:  # a reading without any error at the fitted slope: ordinary least squares, as fit.js
            unit = True
        else:
            p, cov, W, its = res
            sig = 1.0 / np.sqrt(W)
            method = "york"
    if unit:
        sig = np.ones(n)
        p, cov = _wls(X, y, sig)
        method, its = "ols", 0
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
           "sigma_eff": None if unit else sig.tolist(), "n": n, "method": method, "iterations": int(its)}
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
