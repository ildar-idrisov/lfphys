import math, copy, dataclasses, numpy as np
from harness import Harness
from lfphys.core.quantum import scene as QS
V = "p02_quantum"
h = Harness(V, "double_slit")
t0 = h.sim.t
for k in range(15):
    h.run_to(t0 + 4.5 * h.sim.default_speed * (k + 1) / 15); h.runner._frame(0.0)
qs = h.sim.qs; p = qs.particles[1]
o = qs.observables(1); print("r", o["r"], "k", o["k"])
psi = qs.wave(1); F = np.fft.fftn(psi); w = np.abs(F) ** 2
print("spec model", qs._spec_model(psi), "k_spread", qs.k_spread(1))
for a in (0.0, 0.5, 1.0):
    kt = np.array([5.38 * a, 0.0]); dk = kt - np.array(o["k"])
    al = qs._alias(w, dk)
    X = qs.grid.mesh(); b = psi * np.exp(1j * (dk[0] * X[0] + dk[1] * X[1]))
    sh = copy.copy(p); sh.psi, sh.kspec, sh.sk_extra2 = b, qs._spec_model(b), 0.0
    sh.packet = dataclasses.replace(p.packet, k=list(kt))
    print(a, "alias", al, "res", qs._resolution_info(qs._arr, [sh]))
print("current resolution", qs._resolution_info(qs._arr, [p]))
K = qs.grid.kmesh(); kn = math.pi / qs.grid.d[0]
for thr in (5, 7, 9, 9.9):
    m = (np.abs(np.broadcast_to(K[0], w.shape)) > thr) | (np.abs(np.broadcast_to(K[1], w.shape)) > thr)
    print("spectrum beyond |k|>", thr, w[m].sum() / w.sum())
