"""Review B8 (v02 vector mode) through visualizations/tests/harness.py, no server.

1. The preset vector_narrow: T_TE, T_TM, T_Kirchhoff, the checks; 30 000 emitted photons for five seeds: chi^2 p of
   the histogram against the vector curve ('all') and the scalar Kirchhoff curve ('kir'); the transmitted fraction.
2. Detector efficiency with dark counts in vector mode: is the expected curve right? (eff = 0.2, dark counts comparable
   to the signal): chi^2 of the histogram against the run's 'all' curve and against the same curve with eff applied.
3. The vector curve when the hits stay scalar (marks): its normalisation against the scalar 'all' curve.
4. The default geometry switched to the conductor: the refusal text; the cost of a set-up at k a = 130 (the cap) and of
   a live change of the detector efficiency in vector mode.
"""
import math
import sys
import time

import numpy as np

for p in ("/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys", "/lf/visualizations/tests"):
    sys.path.insert(0, p)
from harness import Harness  # noqa: E402
from lfphys.tools import stats  # noqa: E402

V = "v02_double_slit"

print("== 1. vector_narrow ==")
for seed in (1, 2, 3, 4, 5):
    t0 = time.time()
    h = Harness(V, "vector_narrow", seed=seed)
    tb = time.time() - t0
    seg = h.of("segment")[-1]
    v = seg["vector"]
    rate = h.of("header")[0]["rate"]
    h.run_to(30000 / rate)
    sim = h.sim
    hist = sim.hist["bins"].sum(axis=0).astype(float)
    cur = sim.theory["curves"]
    x2v, pv, dof = stats.chi2(hist, cur["all"])
    x2s, ps, _ = stats.chi2(hist, cur["kir"])
    c = sim.counts
    n_tr = c["detected"] + c["missed"]
    if seed == 1:
        print(f"build {tb:.1f} s; T_TE = {v['T_TE']:.5f}, T_TM = {v['T_TM']:.5f}, T_K = {v['T_K']:.5f}; weights H/V "
              f"{v['wH']:.3f}/{v['wV']:.3f}; modes {v['modes']} ({v['method']}); conv TE {v['conv_TE']:+.2e} TM "
              f"{v['conv_TM']:+.2e}; balance TE {v['rel_TE']:.1e} TM {v['rel_TM']:.1e}; p_trans {v['p_trans']:.4f}; "
              f"screen_frac {v['screen_frac']:.4f}")
        ch = h.checks()
        for k in sorted(ch):
            if k.startswith("v"):
                print(f"   check {k}: value {ch[k]['value']}, ok {ch[k].get('ok')}")
        print("   curves:", sorted(cur), "; approx lines mentioning the vector screen:",
              sum("проводник" in a or "вектор" in a for a in seg["approx"]))
    print(f"seed {seed}: emitted {c['emitted']}, detected {c['detected']}, reflected {c['reflected']}, missed "
          f"{c['missed']}; transmitted fraction {n_tr / c['emitted']:.4f} vs P_t/W {v['p_trans']:.4f}; chi2 vector p = "
          f"{pv:.3f} (dof {dof}); chi2 Kirchhoff p = {ps:.1e}")

print("\n== 2. efficiency + dark counts in vector mode ==")
for eff, dark in ((0.2, 0.0), (0.2, 300.0), (1.0, 300.0)):
    h = Harness(V, "vector_narrow", {"eff": eff, "dark_rate": dark}, seed=7)
    rate = h.of("header")[0]["rate"]
    h.run_to(60000 / rate)
    sim = h.sim
    hist = sim.hist["bins"].sum(axis=0).astype(float)
    cur = sim.theory["curves"]
    nb = len(hist)
    dark_bin = dark / rate / nb
    sig = cur["all"] - dark_bin  # the vector part per emitted photon (no efficiency)
    fixed = eff * sig + dark_bin
    _, p_run, _ = stats.chi2(hist, cur["all"])
    _, p_fix, _ = stats.chi2(hist, fixed)
    print(f"eff = {eff}, dark = {dark}/s: detected {sim.counts['detected']}, dark {sim.counts['dark']}; chi2 p against "
          f"the run's curve {p_run:.1e}; against eff*vector + dark {p_fix:.3f}")

print("\n== 3. the vector curve when the hits stay scalar (photon_eraser + conductor) ==")
h = Harness(V, "photon_eraser", {"screen_model": "pec", "a_um": 2.0, "d_um": 10.0, "L2_m": 0.1}, seed=2)
seg = h.of("segment")[0]
cur = h.sim.theory["curves"]
print(f"hits: {seg['vector']['hits']} ({seg['vector']['why']}); sum(all) = {cur['all'].sum():.4f}, sum(vec) = "
      f"{cur['vec'].sum():.4f}, sum(cl) = {cur['cl'].sum():.4f}; T_TE {seg['vector']['T_TE']:.4f} T_TM "
      f"{seg['vector']['T_TM']:.4f}")
h2 = Harness(V, "photon_young", {"screen_model": "kirchhoff", "a_um": 2.0, "d_um": 10.0, "L2_m": 0.1,
                                 "pol_state": "D"}, seed=2)
print(f"   same slits, scalar mode, no marks: sum(all) = {h2.sim.theory['curves']['all'].sum():.4f}")
h3 = Harness(V, "photon_young", {"screen_model": "pec", "a_um": 2.0, "d_um": 10.0, "L2_m": 0.1, "pol_state": "D",
                                 "eff": 0.5}, seed=2)
h4 = Harness(V, "photon_young", {"screen_model": "pec", "a_um": 2.0, "d_um": 10.0, "L2_m": 0.1, "pol_state": "D",
                                 "eff": 0.5, "el1": "phase", "el1_angle": 0.0}, seed=2)
c4 = h4.sim.theory["curves"]
print(f"   a zero phase element (no physical change), eff = 0.5: hits {h4.of('segment')[0]['vector']['hits']}; "
      f"sum(all) = {c4['all'].sum():.4f} (scalar, with eff), sum(vec) = {c4['vec'].sum():.4f}; max|diff|/max(all) = "
      f"{np.max(np.abs(c4['diff'])) / np.max(c4['all']):.3f}")

print("\n== 4. refusals and costs ==")
for params in ({"screen_model": "pec"}, {"screen_model": "pec", "a_um": 13.0, "d_um": 60.0}):
    t0 = time.time()
    try:
        h = Harness(V, "photon_young", params, seed=1)
        print(f"{params}: built in {time.time() - t0:.1f} s; T_TE {h.of('segment')[0]['vector']['T_TE']:.5f}")
    except Exception as exc:  # noqa: BLE001
        print(f"{params}: refused ({type(exc).__name__}): {exc}")
h = Harness(V, "photon_young", {}, seed=1)
h.run_to(0.02)
t0 = time.time()
h.set(screen_model="pec")
print(f"live switch of the default world to the conductor: {time.time() - t0:.2f} s; errors/notices: "
      f"{h.errors()[-1:] if h.errors() else None}; segments {len(h.of('segment'))}")
h = Harness(V, "photon_young", {"screen_model": "pec", "a_um": 13.0, "d_um": 60.0}, seed=1)
for change in ({"eff": 0.5}, {"dark_rate": 10.0}, {"pol_state": "V"}):
    t0 = time.time()
    h.set(**change)
    print(f"live change {change} in a vector world at k a = 129: {time.time() - t0:.1f} s")
