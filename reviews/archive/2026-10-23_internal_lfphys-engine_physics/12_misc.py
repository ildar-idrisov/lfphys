"""12: edge cases: orbits.periapsis_advance / elements for nearly circular orbits (np.roots splits the double root),
hydrogen.dirac_level for a non-existent (n, j), and the start distribution of theories.interpretations.bohm
slit_trajectories (uniform across the slit) against |Psi(x, z0)|^2 at its start plane z0 = 2a.
Usage: python3 12_misc.py
"""
import argparse
import math

argparse.ArgumentParser(description=__doc__).parse_args()

import numpy as np

from lfphys.core.gravity import orbits
from lfphys.core.quantum import hydrogen
from lfphys.theories.approx import paraxial

print("=== periapsis_advance(e, l) near a circular orbit (r_peri = 10 M (1 - eps), r_apo = 10 M (1 + eps)) ===")
for eps in (1e-2, 1e-4, 1e-6, 1e-8):
    u1, u2 = 1 / (10 * (1 + eps)), 1 / (10 * (1 - eps))
    u3 = 0.5 - u1 - u2
    l = 1 / math.sqrt(u1 * u2 + u1 * u3 + u2 * u3)
    e = math.sqrt(1 - 2 * u1 * u2 * u3 * l * l)
    ref = 2 * math.pi / math.sqrt(1 - 6 / 10) - 2 * math.pi  # epicyclic limit, eps -> 0
    try:
        adv = orbits.periapsis_advance(e, l)
        msg = f"{adv:.10f} (circular limit {ref:.10f})"
    except Exception as ex:  # noqa: BLE001
        msg = f"RAISES {type(ex).__name__}: {ex}"
    try:
        orbits.elements(e, l)
        m2 = "elements ok"
    except Exception as ex:  # noqa: BLE001
        m2 = f"elements RAISES {type(ex).__name__}"
    print(f"eps = {eps:g}: periapsis_advance {msg}; {m2}; advance_from_turning {orbits.advance_from_turning(u1, u2):.10f}")

print("\n=== dirac_level for states that do not exist ===")
for n, j in ((1, 1.5), (2, 2.5)):
    try:
        print(f"n={n}, j={j}: returns {hydrogen.dirac_level(n, j):.6e} J (no error; j must be <= n - 1/2)")
    except Exception as ex:  # noqa: BLE001
        print(f"n={n}, j={j}: raises {type(ex).__name__}")

print("\n=== Bohm slit trajectories: start distribution vs |Psi(x, 2a)|^2 inside one slit ===")
lam = 633e-9
k = 2 * math.pi / lam
for a in (5e-6, 20e-6, 100e-6):
    z0 = 2 * a
    x = np.linspace(-a, a, 4001)
    A = paraxial.slit_amplitudes(x, z0, k, [0.0], a)[0, :]
    I = np.abs(A) ** 2
    inside = np.abs(x) <= 0.48 * a  # where the engine starts trajectories (uniform on +-0.48 a)
    cdf = np.cumsum(I * inside)
    cdf /= cdf[-1]
    uni = np.clip((x + 0.48 * a) / (0.96 * a), 0, 1)
    ks = np.max(np.abs(cdf - uni))
    frac = I[~inside].sum() / I.sum()
    print(f"a = {a * 1e6:g} um (Fresnel number a^2/(lam z0) = {a / (2 * lam):.1f}): KS distance uniform vs |Psi|^2 "
          f"= {ks:.3f}; |Psi|^2 outside +-0.48a: {frac:.1%}; max/min of |Psi|^2 inside = {I[inside].max() / I[inside].min():.2f}")
