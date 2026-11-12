"""Q: the B6 fix of the einsum letters covers schrodinger_nd.sample (tested in 3-D) and bohm._Patches.sample (no 3-D
test: _Patches is used whenever <= PATCH_MAX = 64 particles are left, i.e. always for the playground's ensembles of
30-60 points). A free 3-D Gaussian packet; 30 Bohm points advanced with patches (default) and without
(PATCH_MAX = -1), against the exact trajectories; plus a spinor (two components) through the patches."""
import math
import numpy as np
from lfphys.core.quantum import schrodinger_nd as S
from lfphys.theories.interpretations import bohm

g = S.Grid((48, 48, 48), 0.25)
c, k, sg = (-1.0, 0.5, 0.0), (1.5, -1.0, 0.8), (1.0, 1.2, 0.9)
psi0 = g.gaussian(c, k, sg)
H = S.Hamiltonian(g)
op = S.SplitOperator(H, 0.005, force_cpu=True)
X0 = np.random.default_rng(1).normal(c, sg, (30, 3))
res = {}
for mode in ("patches", "device"):
    keep = bohm.PATCH_MAX
    if mode == "device":
        bohm.PATCH_MAX = -1
    try:
        psi, X = psi0.copy(), X0.copy()
        for _ in range(20):
            a = psi
            b = op.step(a, 2)
            cc = op.step(b, 2)
            X, _ = bohm.advance_ensemble(g, (a, b, cc), X, 0.02, H)
            psi = cc
    finally:
        bohm.PATCH_MAX = keep
    res[mode] = X
ref = bohm.gaussian_trajectory(X0, 0.4, c, k, sg)
for mode, X in res.items():
    print(f"{mode:8s}: max |X - exact| = {np.max(np.linalg.norm(X - ref, axis=1)):.2e}")
print(f"patches vs device: {np.max(np.abs(res['patches'] - res['device'])):.2e}")
# a spinor (both components the same Gaussian, weights 0.6, 0.8): the guidance is the same field
sp0 = np.stack([0.6 * psi0, 0.8 * psi0])
Hs = S.Hamiltonian(g, b=np.zeros((3,) + g.shape))
ops = S.SplitOperator(Hs, 0.005, force_cpu=True)
X = X0.copy()
psi = sp0
for _ in range(20):
    a = psi
    b = ops.step(a, 2)
    cc = ops.step(b, 2)
    X, _ = bohm.advance_ensemble(g, (a, b, cc), X, 0.02, Hs)
    psi = cc
print(f"spinor through patches: max |X - exact| = {np.max(np.linalg.norm(X - ref, axis=1)):.2e}")
