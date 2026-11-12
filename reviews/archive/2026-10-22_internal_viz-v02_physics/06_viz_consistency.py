"""Review check 06: does what is drawn come from the run's computation, and is it causal?

(a) The near-field map and flow lines use the averaged marks Gavg only; the run's decoherence from the microscope,
    GRW, source width and spectral width is not in them. Compare |gamma| of Gavg (what the map/flow lines show) with
    |gamma| of the run's expectation Pens, and the fringe contrast of the map's last column (z = L2) itself.
(b) The expected curve in the browser is rebinned by view.js rebin() (grid point -> bin, P_i dx); compare with the
    server's _rebin (trapezoid integral) used for chi-square.
(c) The view's filter "без рассеянного фотона" draws the full ensemble expectation for that subset.
(d) Apparatus change while particles are in flight: the analyzer (in front of the screen) is applied at slit passage.
(e) Born exponent != 2 with the detector read: sampling signals, the no-signalling check does not see it.
(f) Flow-line velocity formula vs the phase gradient; no crossing for a pure state.
"""
import math
import sys

import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402

from v02_double_slit.engine import fresnel  # noqa: E402
from v02_double_slit.engine.experiment import FLAG_SCAT  # noqa: E402
from v02_double_slit.viz import _rebin  # noqa: E402

V = "v02_double_slit"


def seg_blobs(h):
    return [b for m, b in h.msgs if m.get("type") == "segment"]


def gram_gamma(G):
    return abs(G[0, 1]) / math.sqrt(G[0, 0].real * G[1, 1].real)


print("== (a) map / flow lines vs the run's own expectation ==")
for preset, extra in [("photon_young", {}), ("electron_microscope", {}), ("c60_grw", {}), ("photon_partial", {}),
                      ("photon_young", {"dlam_rel": 0.3}), ("electron_qubit", {})]:
    h = Harness(V, preset, extra, seed=1)
    sim = h.sim
    ops, rho = sim.exp.ensemble_marks()
    n = sim.geom.n
    Gavg = np.array([[np.trace(ops[j] @ rho @ ops[l].conj().T) for l in range(n)] for j in range(n)])
    b = seg_blobs(h)[-1]
    nz = len(b["map_z"])
    mp = np.asarray(b["map"]).reshape(nz, -1)
    last = mp[-1]
    nxi = len(last)
    c = last[nxi // 2 - nxi // 8: nxi // 2 + nxi // 8]
    contrast = (c.max() - c.min()) / (c.max() + c.min())
    print(f"  {preset}{extra}: |gamma| shown by map/flow lines (Gavg) = {gram_gamma(Gavg):.3f}; "
          f"run's expectation |gamma| = {sim.gamma_expected:.3f}; map contrast near axis at z = L2: {contrast:.3f}")

print("\n== (b) browser rebin (view.js) vs server rebin ==")
for preset in ("photon_young", "electron", "c60"):
    h = Harness(V, preset, seed=1)
    sim = h.sim
    g = sim.geom
    P = sim.theory["Pens"].sum(axis=0)
    nb = sim._nbins()
    half = float(g.x[-1])
    X = g.x
    dx = X[1] - X[0]
    js = np.zeros(nb)
    b = np.minimum(nb - 1, np.maximum(0, np.floor((X + half) / (2 * half) * nb).astype(int)))
    np.add.at(js, b, P * dx)
    e = np.linspace(g.x[0], g.x[-1], nb + 1)
    sv = _rebin(g.x, P, e)
    js /= js.sum()
    sv /= sv.sum()
    pts = np.bincount(b, minlength=nb)
    m = sv > 0.2 * sv.max()
    print(f"  {preset}: {len(X)} grid points into {nb} bins (points per bin {pts.min()}..{pts.max()}); "
          f"browser/server expected per bin: min {np.min(js[m] / sv[m]):.3f}, max {np.max(js[m] / sv[m]):.3f} "
          f"(bins above 20 % of max)")

print("\n== (c) filter 'no scattered photon' (electron microscope, p = 0.5) ==")
h = Harness(V, "electron_microscope", {"mic_prob": 0.5}, seed=2)
h.run_to(30000 / 1000.0)
X, F = [], []
for m, b in h.msgs:
    if m.get("type") == "detections":
        X.append(b["x"])
        F.append(b["f"])
X, F = np.concatenate(X), np.concatenate(F)
sim = h.sim
nb = sim._nbins()
g = sim.geom
e = np.linspace(g.x[0], g.x[-1], nb + 1)
sel = (F & FLAG_SCAT) == 0
hn, _ = np.histogram(np.clip(X[sel], g.x[0], g.x[-1]), bins=e)
ga, ea = sim._coherence(hn.astype(float), weights=1 / np.maximum(hn, 1), bins=True)
print(f"  subset without scattered photon: {sel.sum()} detections, histogram |gamma| = {ga:.3f} +- {ea:.3f}; "
      f"curve the view draws for it (whole ensemble) has |gamma| = {sim.gamma_expected:.3f}; "
      f"correct subset expectation: 1.000")

print("\n== (d) apparatus change while particles are in flight (neutron, analyzer inserted) ==")
h = Harness(V, "neutron", {"rate": 20000.0, "spin_state": "up_z"}, seed=3)
tf = h.sim.t_flight
t0 = 0.1
h.run_to(t0)
h.action("apparatus", analyzer="on", analyzer_angle=90.0)  # spin filter along x: transmits 1/2 of up_z
h.run_to(t0 + 3 * tf)
T, S = [], []
for m, b in h.msgs:
    if m.get("type") == "detections":
        T.append(b["t"])
        S.append(b["s"])
T, S = np.concatenate(T), np.concatenate(S)
win = (T > t0) & (T <= t0 + tf)
print(f"  time of flight {tf * 1e3:.2f} ms; detections in (t0, t0 + flight]: {win.sum()}, of them tagged with the old "
      f"segment (analyzer absent although they reach it after t0): {np.sum(win & (S == 0))}")
late = (T > t0 + tf) & (T <= t0 + 3 * tf)
rate = 20000.0
print(f"  detection rate in (t0, t0+flight]: {win.sum() / tf:.0f}/s (no analyzer acting); in (t0+flight, t0+3 flight]: "
      f"{late.sum() / (2 * tf):.0f}/s (analyzer acting, expected 0.5 x {rate:.0f})")

print("\n== (e) Born exponent 2.4 with the which-path detector read in the 45 deg basis ==")
h = Harness(V, "electron_eraser", {"born_p": 2.4}, seed=1)
sim = h.sim
R = sim.exp.realize(1, np.random.default_rng(0))
I = R["I"][0]  # (nR, x) |psi|^2 per reading
joint = sim.exp.born(I)
marg_read = joint.sum(axis=0) / joint.sum()
unread = sim.exp.born(I.sum(axis=0))
unread = unread / unread.sum()
print(f"  screen marginal of the sampled joint distribution (read) vs not read: max |diff| / max = "
      f"{np.max(np.abs(marg_read - unread)) / unread.max():.3f}")
c = [c for c in h.checks().values() if c["id"] == "nosig0"][0]
print(f"  the run's no-signalling check: value {c['value']:.1e}, ok = {c.get('ok')}")

print("\n== (f) flow-line velocity vs phase gradient; ordering ==")
lam, a, d, L = 632.8e-9, 20e-6, 100e-6, 1.0
k = 2 * math.pi / lam
x = np.linspace(-3e-3, 3e-3, 2001)
zz = 0.2
A, dA = fresnel.slit_amplitudes(x[:, None], zz, k, [-d / 2, d / 2], a, deriv=True)
num, den = fresnel.current(A, dA, np.ones((2, 2)))
v_eng = (num / den)[:, 0] / k
psi = A.sum(axis=1)[:, 0]
ph = np.unwrap(np.angle(psi))
v_fd = np.gradient(ph, x) / k
mm = np.abs(psi) ** 2 > 0.05 * np.max(np.abs(psi) ** 2)
print(f"  max |v_engine - (1/k) dphase/dx| / max|v| (|psi|^2 > 5% max) = {np.max(np.abs(v_eng[mm] - v_fd[mm])) / np.max(np.abs(v_fd[mm])):.2e}")
bt = fresnel.bohm_trajectories(k, [-d / 2, d / 2], a, math.inf, np.ones((2, 2)), [1, 1], L, n=60,
                               rng=np.random.default_rng(1), n_steps=900)
xs = bt["x"]
print(f"  pure state, 60 lines: order preserved at every step: {bool(np.all(np.diff(xs, axis=1) >= -1e-15))}")
