"""Review check 04: kinematics precision, the Aharonov-Bohm phase for |q| != e, probe polarisation validity.

References: mpmath at 50 digits for the relativistic kinematics; q Phi / hbar for the AB phase.
"""
import math
import sys

import mpmath as mp
import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402

from v02_double_slit.engine.particles import EV, H, C, U, make  # noqa: E402

V = "v02_double_slit"
mp.mp.dps = 50

print("== 1. lambda from the kinetic energy: engine vs 50-digit reference ==")
cases = [("neutron", 2.045e-4), ("neutron", 0.025), ("c60", 2.4e-20 / EV), ("he4", 0.02), ("electron", 50e3),
         ("electron", 1.0)]
for sp, ek in cases:
    p = make(sp, "ekin", ek)
    m = mp.mpf(p.mass)
    E = mp.mpf(ek) * mp.mpf(EV)
    pc = mp.sqrt(E * E + 2 * E * m * mp.mpf(C) ** 2)
    lam_ref = mp.mpf(H) * mp.mpf(C) / pc
    print(f"  {sp:8s} E_k = {ek:.4g} eV: lambda = {p.lam:.6e} m, rel. error vs 50 digits = "
          f"{float((mp.mpf(p.lam) - lam_ref) / lam_ref):+.2e}")

print("\n== 2. the run's own wavelength check for a slow neutron given by kinetic energy ==")
h = Harness(V, None, {"species": "neutron", "energy_by": "ekin", "ekin_ev": 2.045e-4, "a_um": 5.0, "d_um": 25.0,
                      "L2_m": 5.0, "rate": 100.0})
c = h.checks()["lam"]
print(f"  check 'lam': value {c['value']:.9g} nm, ref {c['ref']:.9g} nm, rel {c['rel']:+.2e}, tol {c['tol']}"
      f"  -> {'FAILS (|rel| > tol)' if abs(c['rel']) > c['tol'] else 'passes'}")
h = Harness(V, None, {"species": "c60", "energy_by": "ekin", "ekin_ev": 2.4e-20 / EV, "n_slits": 10, "a_um": 0.05,
                      "d_um": 0.1, "L2_m": 1.25, "rate": 100.0})
c = h.checks()["lam"]
print(f"  C60 by E_k: rel {c['rel']:+.2e} vs tol {c['tol']}")

print("\n== 3. Aharonov-Bohm phase: engine vs q Phi / hbar ==")
for qe, flux in ((-1, 0.5), (-1, 0.25), (2, 0.25), (-3, 1 / 6), (0.5, 1.0)):
    h = Harness(V, None, {"species": "custom", "mass_u": 4.0, "charge_e": qe, "energy_by": "speed", "speed_ms": 1e4,
                          "a_um": 0.1, "d_um": 0.5, "L2_m": 1.0, "ab_flux": flux})
    ph = h.sim.exp.ab_phases()
    ref = qe * flux * 2 * math.pi  # q * (flux h/e) / hbar = 2 pi (q/e) flux
    ref_mod = (ref + math.pi) % (2 * math.pi) - math.pi
    eng_mod = (ph[1] + math.pi) % (2 * math.pi) - math.pi
    print(f"  q = {qe:+g} e, Phi = {flux:.4g} h/e: engine phase {eng_mod:+.4f} rad, q Phi/hbar = {ref_mod:+.4f} rad"
          f"  {'OK' if abs(math.remainder(ph[1] - ref, 2 * math.pi)) < 1e-12 else 'MISMATCH'}")

print("\n== 4. probe photon polarised along its own propagation direction is accepted ==")
for d_, p_ in (("z", "z"), ("y", "y"), ("x", "x")):
    try:
        h = Harness(V, "electron_microscope", {"mic_dir": d_, "mic_pol": p_})
        print(f"  mic_dir={d_}, mic_pol={p_}: accepted (no error); scattered fraction "
              f"{h.sim.app.mic_prob}; header errors: {h.errors()}")
    except Exception as e:  # noqa: BLE001
        print(f"  mic_dir={d_}, mic_pol={p_}: rejected: {e}")

print("\n== 5. GRW nucleon count of light custom particles and of electrons ==")
for mu in (0.3, 0.6, 1.0):
    p = make("custom", "speed", 1e3, mass_u=mu)
    print(f"  custom mass {mu} u -> nucleons used for the GRW rate: {p.nucleons}")
print(f"  electron -> {make('electron', 'ekin', 1e3).nucleons} (mass-proportional CSL/GRW would give m_e/m_N = "
      f"{9.109e-31 / 1.6605e-27:.2e} nucleon equivalents)")

print("\n== 6. spectral width: per-particle wavelength but common time of flight ==")
h = Harness(V, None, {"species": "neutron", "lam_nm": 2.0, "a_um": 5.0, "d_um": 25.0, "L2_m": 5.0, "rate": 100.0,
                      "dlam_rel": 0.2})
pt = h.sim.particle
print(f"  neutron 2 nm, sigma_lambda/lambda = 0.2: velocity spread of the particles 20 % ({pt.v:.1f} m/s +- "
      f"{0.2 * pt.v:.1f}); time of flight used for every particle {h.sim.t_flight * 1e3:.3f} ms (one value)")
