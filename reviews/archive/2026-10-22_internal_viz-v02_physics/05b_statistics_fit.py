"""Review check 05b (follow-up of 05): the histogram coherence fit, dark counts, ensemble scatter, grid cap.

(c) The histogram |gamma_12| fit of the run (stats.coherence_fit with Neyman weights 1/max(h,1), 4 free parameters
    c1 b11 + c2 b22 + c3 Re b12 + c4 Im b12) on multinomial samples of the run's exact expectation; how often it fails
    (returns None), its bias, scatter and reported error. Cause: in the far field b11 and b22 are almost the same
    function (two single-slit envelopes shifted by d << lambda L / a), so c1 and c2 separately are ill-determined and
    sqrt(c1 c2) in the denominator scatters. Alternative shown for comparison (a possible fix): fix the ratio
    c1 : c2 = G11 : G22 from the run's marks (the slit transmissions, known without interference) and fit three
    parameters c0 (G11 b11 + G22 b22) + c3 Re b12 + c4 Im b12 by Poisson maximum likelihood.
(d) Dark counts: they enter the histogram, not the expectation.
(e) Seed scatter of the run's expected |gamma| for the microscope with p = 0.5.
(f) Grids capped at 16384 points in a geometry that is paraxial (electrons, many slits / wide spacing).
"""
import math
import sys

import numpy as np
from scipy import optimize

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402

from v02_double_slit.engine import fresnel  # noqa: E402
from v02_double_slit.viz import _rebin  # noqa: E402

V = "v02_double_slit"


def basis(sim):
    g = sim.geom
    A0 = sim.exp.base_A()
    e = np.linspace(g.x[0], g.x[-1], sim._nbins() + 1)
    b11 = _rebin(g.x, np.abs(A0[0]) ** 2, e)
    b22 = _rebin(g.x, np.abs(A0[1]) ** 2, e)
    b12 = _rebin(g.x, (A0[0] * A0[1].conj()).real, e) + 1j * _rebin(g.x, (A0[0] * A0[1].conj()).imag, e)
    return b11, b22, b12


def constrained_ml(h, b11, b22, b12, G11, G22):
    """Poisson ML of h_b ~ mu_b = c0 (G11 b11 + G22 b22) + c3 Re b12 + c4 Im b12; gamma = |c3 - i c4|/(2 c0 sqrt(G11 G22))."""
    X = np.stack([G11 * b11 + G22 * b22, b12.real, b12.imag], axis=1)
    c_ls, *_ = np.linalg.lstsq(X, h, rcond=None)

    def nll(c):
        mu = np.maximum(X @ c, 1e-12)
        return float(np.sum(mu - h * np.log(mu)))

    r = optimize.minimize(nll, c_ls, method="Nelder-Mead", options={"xatol": 1e-10, "fatol": 1e-10, "maxiter": 4000})
    c0, c3, c4 = r.x
    return math.hypot(c3, c4) / (2 * c0 * math.sqrt(G11 * G22))


SKIP_C = "--skip-c" in sys.argv  # part (c) output: out/05b_statistics_fit.txt; parts (d)-(f): out/05b_statistics_fit_part2.txt
print("== (c) histogram coherence fit: run's estimator vs a constrained Poisson-ML alternative ==")
rng = np.random.default_rng(7)
for preset in (() if SKIP_C else ("electron_weak", "electron_qubit", "photon_young")):
    h = Harness(V, preset, seed=1)
    sim = h.sim
    g = sim.geom
    e = np.linspace(g.x[0], g.x[-1], sim._nbins() + 1)
    q = _rebin(g.x, sim.theory["Pens"].sum(axis=0), e)
    q = q / q.sum()
    true = sim.gamma_expected
    b11, b22, b12 = basis(sim)
    corr = float(np.dot(b11, b22) / math.sqrt(np.dot(b11, b11) * np.dot(b22, b22)))
    ops, rho = sim.exp.ensemble_marks()
    G11 = float(np.trace(ops[0] @ rho @ ops[0].conj().T).real)
    G22 = float(np.trace(ops[1] @ rho @ ops[1].conj().T).real)
    print(f"  {preset}: true |gamma| = {true:.4f}; correlation of the basis functions b11, b22 = {corr:.6f}")
    for N in (100, 300, 1000, 5000, 20000, 100000):
        est, errs, none, ml = [], [], 0, []
        for i in range(200):
            hh = rng.multinomial(N, q).astype(float)
            gg, ee = sim._coherence(hh, weights=1.0 / np.maximum(hh, 1.0), bins=True)
            if gg is None:
                none += 1
            else:
                est.append(gg)
                errs.append(ee if ee is not None else np.nan)
            if i < 60:
                ml.append(constrained_ml(hh, b11, b22, b12, G11, G22))
        est, errs, ml = np.array(est), np.array(errs), np.array(ml)
        print(f"    N = {N:6d}: run's fit: None in {none}/200, mean {est.mean():.3f} (bias {est.mean() - true:+.3f}), "
              f"median {np.median(est):.3f}, scatter {est.std(ddof=1):.3f}, median reported err {np.nanmedian(errs):.3f}, "
              f"fraction > 1: {np.mean(est > 1):.2f} | constrained ML (60 samples): mean {ml.mean():.3f} "
              f"(bias {ml.mean() - true:+.3f}), scatter {ml.std(ddof=1):.3f}")

print("\n== (d) dark counts: histogram includes them, expectation does not ==")
for dr in (0.0, 50.0, 500.0):
    h = Harness(V, "photon_young", {"dark_rate": dr}, seed=4)
    h.run_to(30.0)
    fr, _ = h.sim.frame()
    print(f"  photon_young, rate 1000/s, dark {dr:5.0f}/s, 30 s: detections {h.sim.hist['n']}, dark {h.sim.counts['dark']}; "
          f"chi2 = {fr['chi2']['x2']:.1f} / {fr['chi2']['dof']} dof, p = {fr['chi2']['p']:.2e}; |gamma| hist "
          f"{fr['coh']['hist']} +- {fr['coh']['err']} (None = the fit failed: c1 or c2 <= 0) vs expected {fr['coh']['expected']:.3f}")

print("\n== (e) seed scatter of the run's expected |gamma|, electron microscope p = 0.5 (near-exact 0.432, see 05) ==")
vals = []
for sd in range(1, 13):
    hh = Harness(V, "electron_microscope", {"mic_prob": 0.5}, seed=sd)
    vals.append(hh.sim.gamma_expected)
print("  " + ", ".join(f"{v:.3f}" for v in vals) + f"; mean {np.mean(vals):.4f}, std {np.std(vals, ddof=1):.4f}")

print("\n== (f) grid cap in paraxial geometries (electrons 50 keV, L2 = 1 m) ==")
for n, a_um, d_um in [(12, 0.1, 10.0), (2, 0.1, 50.0), (2, 0.1, 150.0)]:
    h = Harness(V, "electron", {"n_slits": n, "a_um": a_um, "d_um": d_um, "n_bohm": 0}, seed=1)
    sim = h.sim
    g, pt = sim.geom, sim.particle
    span = (g.n - 1) * g.d + g.a
    fine = pt.lam * g.L2 / span
    G = np.ones((g.n, g.n))
    nb = sim._nbins()
    e = np.linspace(g.x[0], g.x[-1], nb + 1)
    b_run = _rebin(g.x, fresnel.intensity(sim.exp.base_A(), G), e)
    xf = np.linspace(g.x[0], g.x[-1], 16 * (len(g.x) - 1) + 1)
    b_f = _rebin(xf, fresnel.intensity(fresnel.slit_amplitudes(xf, g.L2, pt.k, g.slits, g.a, g.L1), G), e)
    b_run, b_f = b_run / b_run.sum(), b_f / b_f.sum()
    m = b_f > 0.05 * b_f.max()
    # visibility of the binned pattern near the centre: exact vs run grid
    c = slice(nb // 2 - nb // 20, nb // 2 + nb // 20)
    vis = lambda b: (b[c].max() - b[c].min()) / (b[c].max() + b[c].min())  # noqa: E731
    rsv = [cc["value"] for cc in h.checks().values() if cc["id"] == "rs0"][0]
    print(f"  n={n:2d} a={a_um} um d={d_um:5.1f} um: Nx = {len(g.x)}, points per finest fringe {fine / g.dx:.2f}, "
          f"bins {nb} (bin width / finest fringe {(e[1] - e[0]) / fine:.2f}); max rel. error of bin probabilities "
          f"{np.max(np.abs(b_run[m] / b_f[m] - 1)):.3f}; central bin contrast run {vis(b_run):.3f} vs exact {vis(b_f):.3f}; "
          f"rs check {rsv:.1e} ({'passes' if rsv < 0.01 else 'fails'}); notices {[m_['text'][:30] for m_ in h.of('notice')]}")
