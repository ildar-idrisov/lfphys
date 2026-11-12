"""Review check 03: GRW collapse hits.

(a) Per-hit average of the engine's sampler (Experiment._grw_weights): E[c_j c_l^*] after n hits must equal
    exp(-n d^2/(4 r_C^2)) for point-like slits (Gaussian GRW, jump operator exp(-(x-X)^2/(2 r_C^2))).
(b) Where the hits happen. The engine draws Poisson(lambda N L2/v) hits over the flight slits -> screen but applies
    all of them AT THE SLIT PLANE. Exact identity used for an independent reference: the averaged GRW map
    rho(x,x') -> exp(-(x-x')^2/(4 r_C^2)) rho(x,x') equals the average of random momentum kicks exp(iqx) with
    q ~ N(0, 1/(2 r_C^2)). In the paraxial free flight a kick at distance z behind the slits shifts the screen
    pattern rigidly by q (L2 - z)/k (completing the square in the Fresnel kernel; verified numerically below).
    So the exact expected pattern is P0(x - sum_i q_i (L2 - z_i)/k) averaged over Poisson hits with z_i uniform
    on [0, L2] -- valid for any slit width (no narrow-slit approximation).
(c) The engine's own expected pattern and its |gamma_12| for the c60_grw preset, against both formulas.
"""
import math
import sys

import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402

from v02_double_slit.engine import fresnel, stats  # noqa: E402

V = "v02_double_slit"

print("== (a) per-hit average of the engine's GRW sampler ==")
h = Harness(V, "c60_grw", seed=1)
ex = h.sim.exp
d, rc = h.sim.geom.d, h.sim.laws.grw_rc
rng = np.random.default_rng(11)
for nh in (1, 2, 4):
    N = 40000
    acc = 0j
    for _ in range(N):
        c = ex._grw_weights(np.ones(1, complex), nh, rng)
        acc += c[0] * np.conj(c[1])
    print(f"  {nh} hit(s): E[c1 c2*] = {acc.real / N:.4f}{acc.imag / N:+.4f}i   exp(-n d^2/4rC^2) = "
          f"{math.exp(-nh * d * d / (4 * rc * rc)):.4f}   (MC sigma ~ {1 / math.sqrt(N):.4f})")

print("\n== (b1) kick at distance z = rigid shift q(L2 - z)/k on the screen (two-step Fresnel, numerical) ==")
lam, a, dd, L2 = 632.8e-9, 20e-6, 100e-6, 1.0
k = 2 * math.pi / lam
zk, q = 0.4, 2.0e4
# field at zk with the true prefactor, then a numerical Fresnel integral over a fine grid to L2
xz = np.linspace(-0.03, 0.03, 120001)
Uz = fresnel.slit_amplitudes(xz, zk, k, [-dd / 2, dd / 2], a).sum(axis=0) * np.sqrt(k / (2j * math.pi * zk))
Uz = Uz * np.exp(1j * q * xz)
s = L2 - zk
xs = np.linspace(-0.01, 0.01, 401)
dxz = xz[1] - xz[0]
U2 = np.array([np.sum(Uz * np.exp(1j * k * (x - xz) ** 2 / (2 * s))) * dxz for x in xs]) * np.sqrt(k / (2j * math.pi * s))
P_two = np.abs(U2) ** 2
P_shift = np.abs(fresnel.slit_amplitudes(xs - q * s / k, L2, k, [-dd / 2, dd / 2], a).sum(axis=0)) ** 2 * k / (2 * math.pi * L2)
print(f"  max|P_two-step - P0(x - q s/k)| / max P = {np.max(np.abs(P_two - P_shift)) / np.max(P_shift):.2e}")

print("\n== (b2/c) c60_grw preset: engine vs exact free-flight GRW ==")
g, pt, laws = h.sim.geom, h.sim.particle, h.sim.laws
Lam = laws.grw_lambda * pt.nucleons * g.L2 / pt.v
f_slit = math.exp(-d * d / (4 * rc * rc))
mu = np.linspace(0, 1, 200001)
f_flight = float(np.trapezoid(np.exp(-d * d * (1 - mu) ** 2 / (4 * rc * rc)), mu))
print(f"  lambda N T = {Lam:.4f}; per-hit coherence factor: at slit plane {f_slit:.5f}, averaged over the flight {f_flight:.5f}")
print(f"  engine formula exp(-LNT(1-e^(-d^2/4rC^2)))         = {math.exp(-Lam * (1 - f_slit)):.4f}")
print(f"  free flight   exp(-LNT(1-<e^(-d^2(1-z/L)^2/4rC^2)>)) = {math.exp(-Lam * (1 - f_flight)):.4f}")
chk = h.checks()
coh = [c for c in chk.values() if c["id"] == "coh0"][0]
print(f"  engine run: |gamma| of the expected pattern = {coh['value']:.4f}, its reference {coh['ref']:.4f}")
# exact (paraxial) free-flight ensemble by Monte-Carlo of hits on the base pattern, fitted by the engine's own fit
x = g.x
A0 = ex.base_A()
P0 = fresnel.intensity(A0, np.ones((2, 2)))
rng = np.random.default_rng(5)
M = 200000
nh = rng.poisson(Lam, size=M)
shift = np.zeros(M)
sq = 1 / (math.sqrt(2) * rc)
for i in np.nonzero(nh)[0]:
    zi = rng.random(nh[i]) * g.L2
    qi = rng.normal(size=nh[i]) * sq
    shift[i] = np.sum(qi * (g.L2 - zi)) / pt.k
# histogram the shifts and convolve (exact average up to the shift binning)
dx = x[1] - x[0]
rmax = 1.01 * max(np.max(np.abs(shift)), 1e-30)
edges = np.linspace(-rmax, rmax, 2 * int(rmax / (0.25 * dx)) + 2)
hs, _ = np.histogram(np.clip(shift, edges[0], edges[-1] - 1e-30), bins=edges)
cent = 0.5 * (edges[1:] + edges[:-1])
Pex = np.zeros_like(P0)
for w, c in zip(hs, cent):
    if w:
        Pex += w * np.interp(x - c, x, P0)
Pex /= M
gam_exact = h.sim._coherence(Pex)[0]
print(f"  exact paraxial free-flight ensemble (MC of {M} particles), fitted |gamma| = {gam_exact:.4f}")
# same with all hits at the slit plane (the engine's model, but via kicks): should reproduce the engine
shift0 = np.zeros(M)
for i in np.nonzero(nh)[0]:
    shift0[i] = np.sum(rng.normal(size=nh[i]) * sq) * g.L2 / pt.k
rmax0 = 1.01 * max(np.max(np.abs(shift0)), 1e-30)
edges0 = np.linspace(-rmax0, rmax0, 2 * int(rmax0 / (0.25 * dx)) + 2)
cent0 = 0.5 * (edges0[1:] + edges0[:-1])
hs0, _ = np.histogram(shift0, bins=edges0)
P0k = np.zeros_like(P0)
for w, c in zip(hs0, cent0):
    if w:
        P0k += w * np.interp(x - c, x, P0)
P0k /= M
print(f"  same kicks all at the slit plane (engine's assumption), fitted |gamma| = {h.sim._coherence(P0k)[0]:.4f}")
print(f"  fraction of shifts beyond the binning range: {np.mean(np.abs(shift) > edges[-1]):.2e}")
