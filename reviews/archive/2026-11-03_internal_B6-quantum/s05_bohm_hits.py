"""Q: are the Bohm points the wrapper registers in an absorber consistent with the probability the absorber takes
(equivariance: the fraction of points registered by detector k should estimate A_k)? The double-slit preset with
300 Bohm points (the maximum), run until the wave has left (t = 40 units); counts per absorber against the engine's
absorbed probabilities (binomial z-scores). Then the y distribution of the screen's hits against the screen's
absorbed record per y (Kolmogorov-Smirnov)."""
import copy, math, sys
import numpy as np
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness
from lfphys.core import backend
from p02_quantum import viz as P

pr = copy.deepcopy(P.SCHEMA.presets["double_slit"]["params"])
for o in pr["scene"]["objects"]:
    if o["type"] == "packet":
        o["values"]["bohm"] = 300
h = Harness("p02_quantum", None, pr, seed=3)
sim, qs = h.sim, h.sim.qs
T_END = 40.0
t = 0.0
while qs.t < T_END - 0.02:
    t = min(t + sim.max_step(), T_END * P.TU)
    h.run_to(t)
oid = [o for o, (k, q) in sim.ref.items() if k == "particle"][0]
B = sim.bohm[oid]
ab = qs.absorbed(1)
N = B["n"]
cnt = {}
for hit in B["hits"]:
    cnt[hit[3]] = cnt.get(hit[3], 0) + 1
print(f"t = {qs.t:.2f}, dt = {qs.dt}, norm in flight {qs.norm(1):.2e}, Bohm points in flight {len(B['X'])} of {N}")
for k, A in sorted(ab.items()):
    n = cnt.get(k, 0)
    z = (n / N - A) / math.sqrt(max(A * (1 - A), 1e-12) / N)
    print(f"  {k:12s}: absorbed probability {A:.4f}, Bohm hits {n}/{N} = {n / N:.4f}, z = {z:+.2f}")
det = [k for k in ab if k.startswith("detector")][0]
ys = np.array([hit[1] for hit in B["hits"] if hit[3] == det])
p = qs.particles[1]
u = qs._arr["u"][det]
prof = np.sum(backend.to_numpy(p.acc) * u, axis=0)
y = qs.grid.axes[1]
cdf = np.cumsum(prof) / prof.sum()
F = np.interp(np.sort(ys), y, cdf)
M = len(ys)
D = float(max(np.max(np.arange(1, M + 1) / M - F), np.max(F - np.arange(M) / M))) if M else float("nan")
print(f"screen hits: {M}; KS distance of their y against the screen's absorbed profile: {D:.3f} "
      f"(DKW bound at alpha = 1e-3: {math.sqrt(math.log(2 / 1e-3) / (2 * max(M, 1))):.3f})")
