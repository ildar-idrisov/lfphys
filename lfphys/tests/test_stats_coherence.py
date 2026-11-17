# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The degree of coherence |gamma_12| of a histogram and its bootstrap error (``lfphys.tools.stats``; review R-W F2,
the integrator's decision D9), against a Monte Carlo reference: the scatter of the estimate over many histograms of the
same pattern, at several hit counts, near and far from full coherence.

The pattern is a synthetic two-slit one: A_j(x) = sinc(1.4 x) exp(+-i 5 pi x / 2) on x in [-1, 1] (about ten fringes
under the envelope), averaged over 200 bins; G11 = 1 and G22 = 1 (equal slits: at |gamma| = 1 the minima are dark, the
hardest case) or 0.8; the true |gamma| and the phase 0.3 set G12. The scatter is the standard deviation of the
estimates over 400 histograms (the Poisson fit has no wild outliers any more: test_no_wild_estimates_at_full_coherence).

The calibration study behind COH_BOOT_MIN_HITS (QE, 2026-11-17; RESPONSE_engine.md of the review EX1-worlds): four
geometries (200 bins with G22 = 1 and 0.8, 60 coarse bins with equal slits, 400 bins with 5 % dark counts), |gamma| =
1, 0.99, 0.97, 0.95, 0.9, 0.7, 0.3, hits 100–3000, 40 histograms each against 600 for the scatter. From 300 hits on the
stated error was within a factor 2 of the scatter in >= 95 % of the histograms of every row (median ratio 0.75–1.6:
conservative just below |gamma| = 1); at 200 hits down to 87.5 % (|gamma| = 0.9: overestimated up to 2.3x), at 100
down to 55 %."""

import math

import numpy as np
import pytest

from lfphys.tools import stats as S

G11 = 1.0


def _basis(nb=200, fringes=10.0, env=0.35, sub=16):
    xe = np.linspace(-1.0, 1.0, nb + 1)
    xs = (xe[:-1, None] + (np.arange(sub)[None, :] + 0.5) / sub * (xe[1] - xe[0])).ravel()
    E = np.sinc(env * 4 * xs)
    A1 = E * np.exp(1j * math.pi * fringes * xs / 2)
    A2 = E * np.exp(-1j * math.pi * fringes * xs / 2)

    def rb(f):
        return f.reshape(nb, sub).mean(axis=1)
    b12 = A1 * A2.conj()
    return rb(np.abs(A1) ** 2), rb(np.abs(A2) ** 2), rb(b12.real) + 1j * rb(b12.imag)


B = _basis()


def _expected(gam, n, g22, phi=0.3):
    b11, b22, b12 = B
    G12 = gam * math.sqrt(G11 * g22) * np.exp(1j * phi)
    P = np.maximum(G11 * b11 + g22 * b22 + 2.0 * (G12 * b12).real, 0.0)
    return P / P.sum() * n


def _draw(rng, mu):
    """A histogram of exactly round(sum mu) hits (multinomial): the hit count a world reads."""
    n = int(round(float(mu.sum())))
    return rng.multinomial(n, mu / mu.sum()).astype(float)


def _scatter(gam, n, g22, rng, m=400):
    mu = _expected(gam, n, g22)
    vals = [S.coherence_ml(_draw(rng, mu), *B, G11, g22)[0] for _ in range(m)]
    vals = np.array([v for v in vals if v is not None])
    assert vals.size == m
    return vals, float(np.std(vals, ddof=1))


@pytest.mark.parametrize("gam,n,g22", [(1.0, S.COH_BOOT_MIN_HITS, 1.0), (1.0, 1000, 1.0), (1.0, 3000, 1.0),
                                       (0.97, S.COH_BOOT_MIN_HITS, 1.0), (0.97, 1000, 1.0),
                                       (0.9, S.COH_BOOT_MIN_HITS, 1.0), (0.9, 1000, 1.0),
                                       (0.5, S.COH_BOOT_MIN_HITS, 1.0), (0.5, 1000, 1.0),
                                       (1.0, S.COH_BOOT_MIN_HITS, 0.8)])
def test_the_bootstrap_error_against_the_monte_carlo_scatter(gam, n, g22):
    """From COH_BOOT_MIN_HITS hits on, the stated error is within a factor 2 of the true scatter for at least 18 of 20
    histograms, and its median ratio is between 0.7 and 1.7 (above 1 just below full coherence, where the error is
    the larger of the fitted model's and the |gamma| = 1 model's: conservative)."""
    rng = np.random.default_rng(int(1000 * gam) + n + int(10 * g22))
    vals, sd = _scatter(gam, n, g22, rng)
    mu = _expected(gam, n, g22)
    ratios = []
    for k in range(20):
        r = S.coherence_boot(_draw(rng, mu), *B, G11, g22, rng=np.random.default_rng(k))
        assert r["err"] is not None, r["why"]
        assert r["n_ok"] >= S.COH_BOOT_MIN_SHARE * r["n_boot"]
        ratios.append(r["err"] / sd)
    ratios = np.array(ratios)
    print("gamma", gam, "hits", n, "G22", g22, "scatter", sd, "median est", float(np.median(vals)), "ratios",
          float(ratios.min()), float(np.median(ratios)), float(ratios.max()))
    assert np.sum((ratios > 0.5) & (ratios < 2.0)) >= 18
    assert 0.7 < float(np.median(ratios)) < 1.7


def test_the_review_case_an_estimate_above_one_gets_an_error_of_its_scatter():
    """Review R-W F2: at |gamma| = 1 a histogram whose estimate is above 1 got an error of 0.0003 (the old bootstrap
    drew from the fitted model with its negative bins clipped to 0, and every refit landed on nearly the same value),
    while the estimates scatter by several 0.01 at ~650 hits. Now the model is projected onto |gamma| <= 1 before the
    draws."""
    rng = np.random.default_rng(5)
    _, sd = _scatter(1.0, 650, 1.0, rng)
    mu = _expected(1.0, 650, 1.0)
    found = 0
    for _ in range(200):
        h = _draw(rng, mu)
        g, _ = S.coherence_ml(h, *B, G11, 1.0)
        if g is not None and g > 1.02:
            err, n_ok = S.coherence_boot_err(h, *B, G11, 1.0, rng=np.random.default_rng(1))
            assert 0.5 * sd < err < 2.0 * sd and n_ok >= 90
            found += 1
            if found == 5:
                break
    assert found == 5


def test_no_wild_estimates_at_full_coherence():
    """The Poisson fit climbs to the one maximum of the concave likelihood. The scoring used before (weights
    1 / max(mu, floor)) settled in 8 of 3000 histograms at |gamma| = 1 and 2000 hits (G22 = 0.8) on points where the
    model was negative in bins with counts, with |gamma| up to 7.5 (or no estimate). Now: none of 1500."""
    rng = np.random.default_rng(7)
    mu = _expected(1.0, 2000, 0.8)
    vals = [S.coherence_ml(_draw(rng, mu), *B, G11, 0.8)[0] for _ in range(1500)]
    assert all(v is not None for v in vals)
    assert max(vals) < 1.2 and min(vals) > 0.8


def _irls(h, X, d, iters=200):
    """The scoring of the earlier version, for regular data (the model > 0 in every bin): weighted least squares with
    the weights 1 / mu, iterated."""
    beta, *_ = np.linalg.lstsq(X / np.sqrt(np.maximum(h, 1.0))[:, None], (h - d) / np.sqrt(np.maximum(h, 1.0)),
                               rcond=None)
    for _ in range(iters):
        W = 1.0 / (X @ beta + d)
        beta = np.linalg.solve((X * W[:, None]).T @ X, (X * W[:, None]).T @ (h - d))
    return beta


@pytest.mark.parametrize("gam", [0.3, 0.8])
def test_the_fit_is_the_maximum_of_the_earlier_scoring_on_regular_data(gam):
    """Where the fitted model is > 0 in every bin, Newton's method with backtracking and the earlier scoring reach the
    same maximum (1e-9 relative), with dark counts as well."""
    rng = np.random.default_rng(3)
    h = rng.poisson(_expected(gam, 5000, 0.8) + 2.0).astype(float)
    d = np.full(h.size, 2.0)
    X = np.stack([G11 * B[0] + 0.8 * B[1], B[2].real, B[2].imag], axis=1)
    ref = _irls(h, X, d)
    assert np.all(X @ ref + d > 0)
    assert S._fit_beta(h, X, d) == pytest.approx(ref, rel=1e-9)


def test_too_few_hits_or_a_failed_fit_give_no_error_with_the_reason():
    rng = np.random.default_rng(2)
    h = _draw(rng, _expected(0.5, 100, 0.8))
    r = S.coherence_boot(h, *B, G11, 0.8)
    assert r["err"] is None and r["why"] is not None and r["hits"] == h.sum() < S.COH_BOOT_MIN_HITS
    assert S.coherence_boot_err(h, *B, G11, 0.8) == (None, 0)
    z = np.zeros(B[0].size)
    z[:2] = 300.0  # counts in two bins: the three coefficients are not determined
    r = S.coherence_boot(z, *B, G11, 0.8)
    assert r["err"] is None and r["why"] is not None


def test_the_bootstrap_model_is_not_negative():
    """The fitted model projected onto |gamma| <= 1 has an expectation >= 0 in every bin: |b12|^2 <= b11 b22 bin by bin
    (Cauchy-Schwarz on the bin's integrals), so no bin is clipped."""
    b11, b22, b12 = B
    assert np.all(np.abs(b12) ** 2 <= b11 * b22 * (1 + 1e-12))
    for g22 in (1.0, 0.8):
        X = np.stack([G11 * b11 + g22 * b22, b12.real, b12.imag], axis=1)
        for ph in np.linspace(0.0, 2 * math.pi, 13):
            beta = np.array([1.0, 2.0 * math.sqrt(G11 * g22) * math.cos(ph), 2.0 * math.sqrt(G11 * g22) * math.sin(ph)])
            assert np.min(X @ beta) >= -1e-12 * np.max(X @ beta)
