"""Q: the preset "tunnel" ("Туннелирование: пакет на тонкий барьер выше своей энергии") — how much of what passes
the barrier is tunnelling (components with E_x below the barrier's top) and how much goes over the top?

The barrier is uniform along y (sy = 0), so the x motion separates exactly: the transmitted probability is
int |phi(kx)|^2 T(kx) dkx with phi the packet's x spectrum (N(k0, sigma_k^2), sigma_k = 1/(2 sigma_x)) and T by
transfer matrices of the profile the wrapper builds (Box with the default edge 1.05 edge_min(d)). Cross-checked by the
wrapper's own run (probability beyond the barrier + absorbed beyond it, when the packet has gone)."""
import math, sys
import numpy as np
sys.path.insert(0, "/lf/visualizations/tests")
from lfphys.core.quantum import scene as QS, transfer
from p02_quantum import viz as P

pr = P.SCHEMA.presets["tunnel"]["params"]
size, n = pr["size"], int(pr["n2"])
d = size / n
box = [o for o in pr["scene"]["objects"] if o["type"] == "box"][0]["values"]
pk = [o for o in pr["scene"]["objects"] if o["type"] == "packet"][0]["values"]
w = 1.05 * QS.edge_min(d)
V0 = box["V"] / P.EV
a = box["sx"]
k0 = 2 * math.pi / pk["wavelength"]
sk = 1 / (2 * pk["sx"])
E0 = k0 * k0 / 2
Vf = lambda x: V0 * QS.smooth_interval(np.asarray(x), -a / 2, a / 2, w)
top = float(Vf(0.0))
print(f"grid step {d} nm, edge (10-90 %) {w:.4f} nm, barrier {box['V']} eV = {V0:.4f} units, its top {top * P.EV:.4f} eV")
print(f"packet: k0 = {k0:.4f}/nm, sigma_k = {sk:.4f}, E(k0) = {E0 * P.EV:.4f} eV; k at the top: {math.sqrt(2 * top):.4f}")
x, wq = np.polynomial.hermite.hermgauss(200)
ks = k0 + math.sqrt(2) * sk * x
wq = wq / wq.sum()
T = transfer.transmission_profile(ks**2 / 2, Vf, -a / 2 - 8 * w, a / 2 + 8 * w, 6000)
T2 = transfer.transmission_profile(ks**2 / 2, Vf, -a / 2 - 8 * w, a / 2 + 8 * w, 12000)
print(f"Richardson residual of T: {np.max(np.abs(T2 - T)):.2e}")
T = T2
below = ks**2 / 2 < top
Ptot = float(np.sum(wq * T))
Pbelow = float(np.sum(wq * T * below))
Pabove = float(np.sum(wq * T * ~below))
frac_above = float(np.sum(wq * ~below))
print(f"transmitted probability {Ptot:.5f}: from E_x below the top {Pbelow:.5f} ({100 * Pbelow / Ptot:.1f} %), "
      f"over the top {Pabove:.5f} ({100 * Pabove / Ptot:.1f} %); share of the packet above the top {100 * frac_above:.2f} %")
print(f"T at k0 itself: {float(transfer.transmission_profile(np.array([E0]), Vf, -a/2 - 8*w, a/2 + 8*w, 12000)[0]):.3e}")

# the wrapper's run (Harness): probability beyond the barrier once the packet has gone
from harness import Harness
h = Harness("p02_quantum", "tunnel")
sim = h.sim
t_end = (abs(pk["x"]) + 25.0) / (k0) * P.TU   # the centre 25 nm past the barrier
step = sim.max_step()
t = 0.0
while t < t_end:
    t = min(t + step, t_end)
    h.run_to(t)
qs = sim.qs
pid = 1
g = qs.grid
X = g.axes[0]
rho = qs.density(pid)
acc = qs.particles[pid].acc
from lfphys.core import backend
acc = backend.to_numpy(acc) if acc is not None else 0 * rho
beyond = float(np.sum((rho + acc)[X > a / 2 + 2 * w, :])) * g.dV
banked = qs.particles[pid].banked
print(f"wrapper run: t = {qs.t:.3f} units, dt = {qs.dt}, beyond the barrier (density + absorbed record since the last "
      f"bank) {beyond:.5f}; banked {banked}; absorbed {qs.absorbed(pid)}")
