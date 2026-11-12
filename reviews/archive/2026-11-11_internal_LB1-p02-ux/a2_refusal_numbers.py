# Review LB1-p02-ux, Part A, script a2: refinement, coarsening and window changes — which rule refuses, with what
# number, against the closed form of a free Gaussian (|phi(k)|^2 and |psi(x, t)|^2 are Gaussians).
# Run as a1 (PYTHONPATH=/lf/lfphys).
import math
import numpy as np
from scipy import constants as sc, special
from lfphys.core.quantum import scene as Q
from lfphys.core.quantum import schrodinger_nd as S

UNIT = Q.species("atom", Q.Units(), mass_u=sc.m_e / sc.atomic_mass)  # mass 1
C0, K0, SIG = (-4.0, 2.0), (1.5, -0.5), (3.0, 3.0)


def scene(t=2.0, dt=0.25, edges=None):
    s = Q.Scene((192, 192), 0.5, dt=dt, edges=edges, device="cpu")
    pid = s.add_particle(Q.Packet(UNIT, list(C0), list(K0), list(SIG)))
    s.advance(int(round(t / dt)))
    return s, pid


def tail_k(d2, k0, sk):
    """closed form: the fraction of a Gaussian spectrum (mean k0, sd sk) outside [-pi/d2, pi/d2)"""
    kn = math.pi / d2
    return 0.5 * special.erfc((kn - k0) / (sk * math.sqrt(2))) + 0.5 * special.erfc((kn + k0) / (sk * math.sqrt(2)))


print("== coarsening on the same window (96 nm): free packet, k0 = (1.5, -0.5), sigma 3 (sigma_k = 1/6)")
print("   rule of the regrid: spectrum beyond the new band <= 1e-6; rule of _resolution_reason: |k| + 6 sigma_k <= pi/d2")
for n2 in (128, 96, 84, 80, 78, 77, 76, 75, 74, 72, 70, 68, 66, 64):
    d2 = 96.0 / n2
    s, pid = scene()
    sk = 1 / 6
    cf = tail_k(d2, K0[0], sk) + tail_k(d2, K0[1], sk)
    loss = S.regrid_losses(s.wave(pid), s.grid, S.Grid((n2, n2), d2))
    try:
        s.regrid((n2, n2), d2)
        res = "taken"
    except ValueError as e:
        res = "REFUSED [" + ("spectrum rule" if getattr(e, "what", None) == "spectrum" else
                             "resolution rule" if "сетка не передаёт" in str(e) else str(e)[:40]) + "]: " + str(e)[:260]
    print(f"  {n2} pts, d2 = {d2:.4f}, pi/d2 = {math.pi / d2:.4f}, |k|+6sk = {K0[0] + 1.0:.4f}: spectrum beyond "
          f"(measured) {loss['spectrum']:.2e}, closed form {cf:.2e} -> {res}")

print("\n== shrinking the window at the same step: probability outside the new window, measured vs closed form")
for n2 in (60, 50, 44, 40, 38, 36, 34, 32):
    s, pid = scene()
    t = s.t
    st = math.sqrt(SIG[0] ** 2 + (t / (2 * SIG[0])) ** 2)  # sigma of |psi|^2 at t (m = hbar = 1)
    c = np.array(C0) + np.array(K0) * t
    g2 = S.Grid((n2, n2), 0.5)
    inside = 1.0
    for a in range(2):
        lo, hi = S.window(g2, a)
        inside *= 0.5 * (special.erf((hi - c[a]) / (st * math.sqrt(2))) - special.erf((lo - c[a]) / (st * math.sqrt(2))))
    loss = S.regrid_losses(s.wave(pid), s.grid, g2)
    try:
        rep = s.regrid((n2, n2), 0.5)
        res = f"taken, dropped {rep['particles'][pid]['dropped']:.2e}"
    except ValueError as e:
        res = "REFUSED: " + str(e)[:200]
    print(f"  {n2} pts (window {n2 * 0.5}): outside measured {loss['outside']:.3e}, closed form {1 - inside:.3e} -> {res}")

print("\n== accepted with a raised tolerance: the banked 'regrid' equals the measured fraction x norm")
s, pid = scene()
rep = s.regrid((34, 34), 0.5, tol=1e-1)
r = rep["particles"][pid]
print(f"  outside {r['outside']:.6e}, norm before {r['norm_before']:.15f}, after {r['norm_after']:.15f}, "
      f"dropped {r['dropped']:.6e}, banked {s.absorbed(pid)['regrid']:.6e}; norm + absorbed - 1 = "
      f"{s.norm(pid) + sum(s.absorbed(pid).values()) - 1:.2e}")
s, pid = scene()
rep = s.regrid((116, 116), 96 / 116, tol=1e-2)
r = rep["particles"][pid]
print(f"  coarsening 116: spectrum {r['spectrum']:.6e}, dropped {r['dropped']:.6e} (dropped/norm = {r['dropped'] / r['norm_before']:.6e})")

print("\n== enlarging the window while the wave is at the faces (closed window, packet drifting towards +x)")
for t in (10.0, 14.0, 18.0, 22.0):
    s = Q.Scene((128, 128), 0.5, dt=0.25, device="cpu")
    pid = s.add_particle(Q.Packet(UNIT, [0.0, 0.0], [1.5, 0.0], [3.0, 3.0]))
    s.advance(int(round(t / 0.25)))
    g2 = S.Grid((160, 160), 0.5)
    loss = S.regrid_losses(s.wave(pid), s.grid, g2)
    # what the face test bounds: the wave beyond the old face continues on the other side; the zero padding cuts it.
    # The true error: the closed-form packet on the larger window against the resampled one
    try:
        s.regrid((160, 160), 0.5, tol=1.0)
        ref = S.Grid((160, 160), 0.5, m=1.0).free_gaussian(s.t, (0.0, 0.0), (1.5, 0.0), (3.0, 3.0))
        err = float(np.sum(np.abs(s.wave(pid) - ref) ** 2) * 0.25)
        res = f"taken with tol=1; ||psi - free closed form||^2 on the new window = {err:.2e}"
    except ValueError as e:
        res = "REFUSED: " + str(e)[:120]
    print(f"  t = {t}: face (4 outer cells) {loss['face']:.2e} -> {res}")
