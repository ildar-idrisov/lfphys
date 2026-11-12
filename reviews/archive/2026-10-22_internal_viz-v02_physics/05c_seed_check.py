"""Review check 05c: are the run's ensembles for different seeds independent? (seeds 1, 2 gave the same |gamma| to 3 digits)."""
import sys
import numpy as np
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402
V = "v02_double_slit"
for extra in ({"mic_prob": 0.5}, {}):
    for sd in (1, 2, 3):
        h = Harness(V, "electron_microscope", extra, seed=sd)
        P = h.sim.theory["Pens"].sum(axis=0)
        print(f"  {extra} seed {sd}: |gamma| = {h.sim.gamma_expected:.10f}, sum Pens*dx = {P.sum() * h.sim.geom.dx:.10f}, "
              f"Pens[1000] = {P[1000]:.10e}")
