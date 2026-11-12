"""Review check 05d: stability of the run's 'expected |gamma_12|' (4-parameter slit-basis fit of the smooth expectation
Pens) for the microscope preset over seeds; the run's coh check outcome; the same with the ratio c1:c2 fixed by the
marks (constrained 3-parameter least squares)."""
import math
import sys
import numpy as np
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402
V = "v02_double_slit"
fails = 0
gs, gcs = [], []
for sd in range(1, 21):
    h = Harness(V, "electron_microscope", {}, seed=sd)
    sim = h.sim
    A0 = sim.exp.base_A()
    b11, b22, b12 = np.abs(A0[0]) ** 2, np.abs(A0[1]) ** 2, A0[0] * A0[1].conj()
    P = sim.theory["Pens"].sum(axis=0)
    X = np.stack([b11, b22, b12.real, b12.imag], axis=1)
    c, *_ = np.linalg.lstsq(X, P, rcond=None)
    Xc = np.stack([b11 + b22, b12.real, b12.imag], axis=1)  # G11 = G22 here (no elements)
    cc, *_ = np.linalg.lstsq(Xc, P, rcond=None)
    gcon = math.hypot(cc[1], cc[2]) / (2 * cc[0])
    chk = [x for x in h.checks().values() if x["id"] == "coh0"][0]
    fails += chk.get("ok") is False
    gs.append(sim.gamma_expected)
    gcs.append(gcon)
    print(f"  seed {sd:2d}: run |gamma| {sim.gamma_expected:.4f} (c1 {c[0]:.4g}, c2 {c[1]:.4g}); check ok = {chk.get('ok')} "
          f"(ref {chk['ref']:.4f}); constrained fit {gcon:.4f}")
print(f"  run fit: mean {np.mean(gs):.4f}, std {np.std(gs, ddof=1):.4f}; constrained: mean {np.mean(gcs):.4f}, "
      f"std {np.std(gcs, ddof=1):.4f}; failed checks {fails}/20")
