"""GPU 0 against the CPU (run through the GPU guard wrapper, < 5 min):
(1) the engine test's scene (box, flux tube, localization region with jumps, an electron; 256^2) for 400 steps on
    both devices: wave difference, jump times, absorbed records, the balance on the GPU;
(2) 3-D sampling on the device (schrodinger_nd.sample with CuPy, > SMALL_GATHER so the einsum runs on the GPU) and
    3-D Bohm points (advance_ensemble, 100 points: device path; 30 points: patches) against the CPU;
(3) the wrapper's double-slit preset with its 60 Bohm points to t = 20 units on GPU 0 and on the CPU: absorbed
    probabilities and the Bohm points' positions."""
import copy, math, os, sys, time
import numpy as np
sys.path.insert(0, "/lf/visualizations/tests")
from lfphys.core import backend
from lfphys.core.quantum import scene as Q, schrodinger_nd as S
from lfphys.theories.interpretations import bohm
print("devices:", backend.devices()["gpu"])


def build(device):
    s = Q.Scene((256, 256), 0.1, dt=0.005, edges=Q.EdgeLayers(3.0, 4.0), device=device, seed=1)
    s.add(Q.Box([1.0, 0.0], [0.6, 2.0], 3.0, 0.4))
    s.add(Q.FluxTube([-1.0, 2.0], 1.0, 0.4))
    s.add(Q.Localization(2.0, 0.5, lo=[0.0, None], hi=[None, None], edge=0.5))
    s.add_particle(Q.Packet(Q.species("electron"), [-1.0, 0.0], [3.0, 0.0], [1.0, 1.0]))
    return s


t0 = time.time()
a, b = build("auto"), build("cpu")
for _ in range(4):
    a.advance(100)
    b.advance(100)
ca, cb = a.checks()[1], b.checks()[1]
print(f"(1) devices {a.device}/{b.device}; max |psi_gpu - psi_cpu| = {np.max(np.abs(a.wave(1) - b.wave(1))):.2e}; "
      f"jumps {[round(t, 4) for t, _ in a.particles[1].jumps]} / {[round(t, 4) for t, _ in b.particles[1].jumps]}; "
      f"absorbed {ca['absorbed']} / {cb['absorbed']}; balance gpu {ca['balance']:.1e} (tol {ca['balance_tol']:.1e}); "
      f"{time.time() - t0:.1f} s")

# (2) 3-D sampling and Bohm on the device
import cupy as cp
g = S.Grid((64, 64, 64), 0.2)
k = np.array([2.0, -1.0, 1.5])
X = g.mesh()
psi = np.broadcast_to(np.exp(1j * (k[0] * X[0] + k[1] * X[1] + k[2] * X[2])), g.shape).copy()
P = np.random.default_rng(2).uniform(-2.0, 2.0, (400, 3))
vh, gh = S.sample(g, psi, P)
vd, gd = S.sample(g, cp.asarray(psi), P, xp=cp)
print(f"(2) sample 3-D: device path used: {400 * 729 > S.SMALL_GATHER}; |v_gpu - v_cpu| {float(np.max(np.abs(cp.asnumpy(vd) - vh))):.1e}, "
      f"|grad| {float(np.max(np.abs(cp.asnumpy(gd) - gh))):.1e}")
g2 = S.Grid((48, 48, 48), 0.25)
c0, k0, sg = (-1.0, 0.5, 0.0), (1.5, -1.0, 0.8), (1.0, 1.2, 0.9)
psi0 = g2.gaussian(c0, k0, sg)
H = S.Hamiltonian(g2)
for N in (30, 100):
    Xs = {}
    for dev in ("cpu", "gpu"):
        op = S.SplitOperator(H, 0.005, force_cpu=(dev == "cpu"))
        p, Xb = op.put(psi0), np.random.default_rng(1).normal(c0, sg, (N, 3))
        for _ in range(10):
            a1 = p
            b1 = op.step(a1, 2)
            c1 = op.step(b1, 2)
            Xb, _ = bohm.advance_ensemble(g2, (a1, b1, c1), Xb, 0.02, H, xp=op.xp)
            p = c1
        Xs[dev] = Xb
    print(f"    3-D Bohm, {N} points (op device {op.device}): max |X_gpu - X_cpu| = {np.max(np.abs(Xs['gpu'] - Xs['cpu'])):.1e}")

# (3) the wrapper on GPU 0 and on the CPU
from harness import Harness
from p02_quantum import viz as PV
res = {}
_Scene = PV.QS.Scene


class CPUScene(_Scene):
    def __init__(self, *a, **kw):
        kw["device"] = "cpu"
        super().__init__(*a, **kw)


for dev in ("gpu", "cpu"):
    t1 = time.time()
    PV.QS.Scene = _Scene if dev == "gpu" else CPUScene
    h = Harness("p02_quantum", "double_slit", seed=3)
    sim, qs = h.sim, h.sim.qs
    t = 0.0
    while qs.t < 20.0 - 0.02:
        t = min(t + sim.max_step(), 20.0 * PV.TU)
        h.run_to(t)
    oid = [o for o, (kk, q) in sim.ref.items() if kk == "particle"][0]
    B = sim.bohm[oid]
    res[dev] = (qs.device, qs.absorbed(1), np.array(B["X"]), [hh[:3] for hh in B["hits"]], qs.wave(1))
    print(f"(3) {dev}: scene on {qs.device}, {time.time() - t1:.1f} s, absorbed {qs.absorbed(1)}, Bohm in flight "
          f"{len(B['X'])}, hits {len(B['hits'])}")
ga, cpu_ = res["gpu"], res["cpu"]
if ga[0] != cpu_[0]:
    print(f"    wave max diff {np.max(np.abs(ga[4] - cpu_[4])):.1e}")
    if len(ga[2]) == len(cpu_[2]):
        print(f"    Bohm points in flight max diff {np.max(np.abs(ga[2] - cpu_[2])) if len(ga[2]) else 0:.1e} nm")
    print(f"    hits gpu {len(ga[3])} cpu {len(cpu_[3])}")
print(f"total {time.time() - t0:.1f} s")
