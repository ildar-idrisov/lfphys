"""Review check 05: statistics of the expected curve, chi-square and the coherence fit.

(a) Monte-Carlo noise of the run's expectation Pens (M = 600/1500 realisations) against a near-exact ensemble from
    the engine's own code path with M = 100000. Non-centrality per detection
        delta = sum_b (p_b - q_b)^2 / q_b       (p: run's expectation, q: near-exact; both binned like the run)
    gives the number of detections N* = dof / delta at which the chi-square of a perfect detector against the run's
    expectation exceeds its dof by a factor ~2 (false rejection grows quickly beyond that).
    Also: |gamma| of the near-exact ensemble vs the closed-form references and the check tolerances.
(b) The detector sampler (grid point + uniform jitter dx) vs the trapezoid rebinning used for the expectation.
(c) Bias and error coverage of the histogram coherence fit (Neyman weights 1/max(h,1)) on multinomial samples of
    the exact expectation.
(d) Dark counts: they enter the histogram but not the expectation.
"""
import math
import sys
import time

import numpy as np
from scipy import stats as sps

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402

from v02_double_slit.engine import stats  # noqa: E402
from v02_double_slit.viz import _rebin  # noqa: E402

V = "v02_double_slit"


def binned(sim, P):
    g = sim.geom
    e = np.linspace(g.x[0], g.x[-1], sim._nbins() + 1)
    b = _rebin(g.x, P.sum(axis=0), e)
    return b / b.sum()


print("== (a) MC noise of the run's expectation ==")
cases = [("photon_partial", {}), ("electron_microscope", {}), ("c60_grw", {}),
         ("photon_pol_marks", {"pol_state": "unpol"}), ("electron_microscope", {"mic_prob": 0.5})]
for preset, extra in cases:
    t0 = time.time()
    h = Harness(V, preset, extra, seed=1)
    sim = h.sim
    ex = sim.exp
    M = sim.M_last
    p = binned(sim, sim.theory["Pens"])
    g = sim.geom
    Pref, _ = ex.ensemble(100000, np.random.default_rng(12345), chunk=max(4, int(3e6 // (g.n * len(g.x)))))
    q = binned(sim, Pref)
    m = q * 1e6 >= 5
    delta = float(np.sum((p[m] - q[m]) ** 2 / q[m]))
    dof = int(m.sum() - 1)
    gam_run = sim.gamma_expected if g.n == 2 else None
    gam_ref = sim._coherence(Pref.sum(axis=0))[0] if g.n == 2 else None
    cc = [c for c in h.checks().values() if c["id"] == "coh0"]
    line = f"  {preset}{extra}: M = {M}, bins = {len(p)}, dof = {dof}, delta = {delta:.3e} -> N* = dof/delta = {dof / delta:.3g}"
    print(line)
    if cc:
        c = cc[0]
        print(f"      |gamma|: run {gam_run:.4f}, near-exact (M=1e5) {gam_ref:.4f}, closed-form ref "
              f"{c['ref'] if c['ref'] is None else round(c['ref'], 4)}; check tolerance "
              f"{4 / math.sqrt(M) + (0.02 if 'microscope' in preset else 0.01 if 'partial' in preset else 0):.4f}"
              f"  [{time.time() - t0:.0f} s]")

print("\n   seed-to-seed scatter of the run's |gamma| (M as in the run), 12 seeds:")
for preset, extra in [("photon_partial", {}), ("electron_microscope", {}), ("c60_grw", {})]:
    vals = []
    for sd in range(12):
        h = Harness(V, preset, extra, seed=100 + sd)
        vals.append(h.sim.gamma_expected)
    print(f"  {preset}: mean {np.mean(vals):.4f}, std {np.std(vals, ddof=1):.4f}; tolerance used 4/sqrt(M)+c = "
          f"{4 / math.sqrt(h.sim.M_last) + (0.02 if 'microscope' in preset else 0.01 if 'partial' in preset else 0):.4f}")

print("\n== (b) sampler cells vs trapezoid rebinning (photon_young, c60 grating) ==")
for preset in ("photon_young", "c60", "electron"):
    h = Harness(V, preset, seed=1)
    sim = h.sim
    g = sim.geom
    P = sim.theory["Pens"].sum(axis=0)
    nb = sim._nbins()
    e = np.linspace(g.x[0], g.x[-1], nb + 1)
    # exact bin probabilities of the sampler: mass P_i dx spread uniformly on [x_i - dx/2, x_i + dx/2],
    # positions beyond the ends clipped into the end bins (as in _reveal)
    dx = g.dx
    lo, hi = g.x - dx / 2, g.x + dx / 2
    w = P / P.sum()
    cell = np.zeros(nb)
    for j in range(nb):
        a0 = e[j] if j > 0 else -np.inf
        a1 = e[j + 1] if j < nb - 1 else np.inf
        ov = np.clip(np.minimum(hi, a1) - np.maximum(lo, a0), 0, None) / dx
        cell[j] = np.sum(w * ov)
    q = _rebin(g.x, P, e)
    q /= q.sum()
    m = q * 1e6 >= 5
    delta = float(np.sum((cell[m] - q[m]) ** 2 / q[m]))
    print(f"  {preset}: grid points {len(g.x)}, bins {nb}, points per finest fringe "
          f"{(pt := sim.particle).lam * g.L2 / ((g.n - 1) * g.d + g.a) / dx:.1f}; delta = {delta:.2e} -> N* = {(m.sum() - 1) / delta:.3g}")

print("\n== (c) coherence fit of histograms: bias and error coverage (multinomial samples of the exact expectation) ==")
rng = np.random.default_rng(7)
for preset in ("electron_weak", "electron_qubit"):
    h = Harness(V, preset, seed=1)
    sim = h.sim
    q = binned(sim, sim.theory["Pens"])
    true = sim.gamma_expected
    for N in (100, 300, 1000, 5000, 20000):
        est, errs = [], []
        for _ in range(300):
            hh = rng.multinomial(N, q).astype(float)
            gg, ee = sim._coherence(hh, weights=1.0 / np.maximum(hh, 1.0), bins=True)
            if gg is not None and ee is not None:
                est.append(gg)
                errs.append(ee)
        est, errs = np.array(est), np.array(errs)
        cov = np.mean(np.abs(est - true) <= errs)
        print(f"  {preset} (true {true:.4f}) N = {N:6d}: mean fit {est.mean():.4f} (bias {est.mean() - true:+.4f}), "
              f"scatter {est.std(ddof=1):.4f}, mean reported err {errs.mean():.4f}, |fit-true| <= err in {100 * cov:.0f} %")
    # Poisson-likelihood (unbiased) alternative for comparison at N=300
    N = 300
    est = []
    for _ in range(300):
        hh = rng.multinomial(N, q).astype(float)
        gg, _ = sim._coherence(hh, weights=None, bins=True)  # unweighted least squares
        est.append(gg)
    print(f"    unweighted LSQ at N = {N}: mean {np.mean(est):.4f} (bias {np.mean(est) - true:+.4f})")

print("\n== (d) dark counts: histogram includes them, expectation does not ==")
h = Harness(V, "photon_young", {"dark_rate": 500.0}, seed=4)
h.run_to(30.0)
fr, _ = h.sim.frame()
print(f"  photon_young + dark 500/s (rate 1000/s), 30 s: detections in segment {h.sim.hist['n']}, dark {h.sim.counts['dark']}")
print(f"  chi2 = {fr['chi2']['x2']:.1f} on {fr['chi2']['dof']} dof, p = {fr['chi2']['p']:.2e}; |gamma| hist "
      f"{fr['coh']['hist']:.4f} +- {fr['coh']['err']:.4f} vs expected {fr['coh']['expected']:.4f}")
h = Harness(V, "photon_young", {}, seed=4)
h.run_to(30.0)
fr, _ = h.sim.frame()
print(f"  same without dark counts: chi2 p = {fr['chi2']['p']:.3f}; |gamma| hist {fr['coh']['hist']:.4f} +- {fr['coh']['err']:.4f}")
