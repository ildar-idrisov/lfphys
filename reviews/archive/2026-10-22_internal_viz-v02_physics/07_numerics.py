"""Review check 07: numerical robustness.

1. Screen grid: points per finest fringe (lambda L2 / span) for every preset and for stress geometries; when the cap of
   16384 points binds, the bin probabilities computed on the run's grid vs an 8x finer grid.
2. The Rayleigh-Sommerfeld check's quadrature size (same formula as rs.slit_fields) for user-settable geometries.
3. The near-field map starts at z = 2a with the paraxial formula; its accuracy there vs the exact RS integral.
4. Segment cost for many slits with a Monte-Carlo ensemble (time and peak memory).
5. The run's own paraxial check value for the presets with picometre wavelengths.
"""
import math
import resource
import sys
import time

import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402

from v02_double_slit.engine import fresnel, rs  # noqa: E402
from v02_double_slit.viz import SCHEMA, _rebin  # noqa: E402

V = "v02_double_slit"


def rs_nodes(x, z, k, c, a, L1=math.inf, src=0.0, kappa=0.0):
    xm = float(np.max(np.abs(x - c)))
    R_near = math.hypot(xm, z)
    ph = k * a * xm / R_near + k * a * a / (8 * z) + (k * a * abs(src) / L1 if not math.isinf(L1) else 0.0) \
        + abs(kappa) * a + (k * a * a / (8 * L1) if not math.isinf(L1) else 0.0)
    return int(min(max(32, 12 * ph / math.pi + 32), 20000)), ph


print("== 1. screen grid resolution ==")
for pid in SCHEMA.presets:
    h = Harness(V, pid, seed=1)
    g, pt = h.sim.geom, h.sim.particle
    span = (g.n - 1) * g.d + g.a
    fine = pt.lam * g.L2 / span
    print(f"  {pid:22s} Nx = {len(g.x):5d}, points per finest fringe {fine / g.dx:6.1f}, bins {h.sim._nbins():4d}, "
          f"rs check {[c['value'] for c in h.checks().values() if c['id'] == 'rs0'][0]:.2e}")

print("\n  stress geometries (photon 632.8 nm, L2 = 1 m):")
for n, a_um, d_um in [(12, 10.0, 200.0), (12, 5.0, 500.0), (12, 2.0, 1000.0), (2, 1.0, 2000.0)]:
    p = {"n_slits": n, "a_um": a_um, "d_um": d_um, "n_bohm": 0}
    h = Harness(V, None, p, seed=1)
    sim = h.sim
    g, pt = sim.geom, sim.particle
    span = (g.n - 1) * g.d + g.a
    fine = pt.lam * g.L2 / span
    # bin probabilities on the run grid vs an 8x finer grid (fully coherent marks)
    G = np.ones((g.n, g.n))
    nb = sim._nbins()
    e = np.linspace(g.x[0], g.x[-1], nb + 1)
    P_run = fresnel.intensity(sim.exp.base_A(), G)
    xf = np.linspace(g.x[0], g.x[-1], 8 * (len(g.x) - 1) + 1)
    P_f = fresnel.intensity(fresnel.slit_amplitudes(xf, g.L2, pt.k, g.slits, g.a, g.L1), G)
    b_run = _rebin(g.x, P_run, e)
    b_f = _rebin(xf, P_f, e)
    b_run, b_f = b_run / b_run.sum(), b_f / b_f.sum()
    m = b_f > 0.05 * b_f.max()
    print(f"  n={n:2d} a={a_um:5.1f} um d={d_um:6.1f} um: Nx = {len(g.x)} (cap 16384), points per finest fringe "
          f"{fine / g.dx:5.2f}, bins {nb}, max rel. error of bin probabilities {np.max(np.abs(b_run[m] / b_f[m] - 1)):.3f}; "
          f"rs check {[c['value'] for c in h.checks().values() if c['id'] == 'rs0'][0]:.2e}")

print("\n== 2. RS-check quadrature size (rs.slit_fields formula), numpy leggauss is O(n^3) time, O(n^2) memory ==")
for lab, lam, a, d, L2, screen in [("photon a=20um L=1m (default)", 632.8e-9, 20e-6, 100e-6, 1.0, 0.0),
                                   ("photon a=1mm d=3mm, screen 0.1 m", 632.8e-9, 1e-3, 3e-3, 1.0, 0.1),
                                   ("photon a=1mm d=3mm, screen 1 m", 632.8e-9, 1e-3, 3e-3, 1.0, 1.0),
                                   ("photon a=1mm d=3mm, L2=1mm (near field)", 632.8e-9, 1e-3, 3e-3, 1e-3, 0.0),
                                   ("electron a=0.1um d=0.5um, screen 1 cm", 5.355e-12, 0.1e-6, 0.5e-6, 1.0, 0.01)]:
    k = 2 * math.pi / lam
    span = d + a
    half = screen or (0.5 * span + 3.0 * lam * L2 / a)
    x = np.linspace(-half, half, 400)
    nn, ph = rs_nodes(x, L2, k, d / 2, a)
    est = 4.69 * (nn / 4000) ** 3
    print(f"  {lab:42s}: phase {ph:9.0f} rad -> {nn:5d} nodes per slit; leggauss ~{est:7.1f} s, matrix "
          f"{nn * nn * 8 / 1e9:.2f} GB")

print("\n== 3. near-field map: paraxial vs exact RS at the first columns (z = 2a ... ) ==")
for lab, lam, a, d in [("photon a=20um", 632.8e-9, 20e-6, 100e-6), ("photon a=3um", 632.8e-9, 3e-6, 15e-6),
                       ("photon a=1um", 632.8e-9, 1e-6, 5e-6)]:
    k = 2 * math.pi / lam
    for zf in (2, 5, 20, 100):
        z = zf * a
        x = np.linspace(-(d + 2 * a), d + 2 * a, 301)
        A = fresnel.slit_amplitudes(x, z, k, [-d / 2, d / 2], a)
        dev, _ = rs.paraxial_deviation(x, z, k, [-d / 2, d / 2], a, math.inf, np.ones((2, 2), complex), A)
        print(f"  {lab}: z = {zf:3d} a: max|P_RS - P_F|/max P_F = {dev:.3f}")

print("\n== 4. segment cost, many slits with a Monte-Carlo ensemble ==")
for lab, p in [("electron microscope n=12 a=0.1um d=1um", {"species": "electron", "energy_by": "ekin", "ekin_ev": 5e4,
                                                           "n_slits": 12, "a_um": 0.1, "d_um": 1.0, "L2_m": 1.0,
                                                           "wp_mode": "microscope", "n_bohm": 40}),
               ("photon partial coherence n=12 a=10um d=200um", {"n_slits": 12, "a_um": 10.0, "d_um": 200.0, "L1_m": 0.5,
                                                                 "src_width_um": 500.0, "n_bohm": 40})]:
    t0 = time.time()
    h = Harness(V, None, p, seed=1)
    t1 = time.time() - t0
    t0 = time.time()
    h.run_to(500 / h.sim.app.rate)
    t2 = time.time() - t0
    print(f"  {lab}: Nx = {len(h.sim.geom.x)}, first segment {t1:.1f} s, 500 particles {t2:.1f} s, "
          f"peak RSS so far {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024:.0f} MB")
