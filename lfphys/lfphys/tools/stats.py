# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Statistics of the accumulated screen and independent references.

* ``coherence_ml``: the degree of coherence |gamma_12| of two slits from a histogram (Poisson maximum likelihood)
  or a smooth curve, with the slit envelopes' ratio fixed by the run's own marks (review R2).
* ``coherence_boot_err``: its standard error by a parametric bootstrap (the Fisher error is only asymptotic).
* ``chi2``: Pearson chi-square of the histogram against the ensemble prediction (bins with expectation >= 5).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats as sps

ABOUT = {
    "layer": 'tools', "kind": 'statistics',
    "title": 'Статистика смоделированных данных',
    "statement": 'Оценка степени когерентности по гистограмме (пуассоновское МП, параметрический бутстрэп), χ², период полос.',
    "validity": 'инструмент, не физика',
    "basis": [],
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
