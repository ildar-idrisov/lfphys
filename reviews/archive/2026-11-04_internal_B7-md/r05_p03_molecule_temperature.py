"""p03 preset "molecules" (60 dimers, 'Температура' 200 K): MD.add_molecule(T=...) draws Maxwell velocities and removes
each molecule's own momentum, so every molecule starts with zero translation and (d n - d) of its d n kinetic
degrees of freedom: the measured temperature at the start is ~(d n - d)/(d n) T = 100 K, and the energy then spreads
over 7 quadratic terms per dimer (3 translation, 2 rotation, 1 + 1 vibration). The energy split by mode is measured
here (the preset claims rotation and vibration share the energy). Also: hbar omega / k of the preset's bond."""
import common  # noqa: F401
import math

import numpy as np
from harness import Harness
from scipy import constants as sc

from p03_molecules.viz import KELVIN, PS

h = Harness("p03_molecules", "molecules")
md = h.sim.md


def modes():
    """Per dimer (averages, in K = 2 <E_mode> / (number of quadratic terms)): translation (3), rotation (2),
    vibration kinetic (1) and potential (1)."""
    x = md.positions(True)
    v = md.velocities()
    m = 1.0
    tr, rot, vk, vp = [], [], [], []
    for mk, keys in md.molecules().items():
        r = md._rows(keys)
        vc = v[r].mean(0)
        tr.append(0.5 * 2 * m * vc @ vc)
        d = x[r[1]] - x[r[0]]
        d -= md.L * np.rint(d / md.L)
        L = np.linalg.norm(d)
        u = d / L
        dv = v[r[1]] - v[r[0]]
        mu = m / 2
        vr = dv @ u
        vk.append(0.5 * mu * vr * vr)
        rot.append(0.5 * mu * (dv @ dv - vr * vr))
        vp.append(0.5 * 400.0 * (L - 1.1) ** 2)
    f = 2 * KELVIN
    return {"T_measured": md.temperature()["T"] * KELVIN, "trans": f * np.mean(tr) / 3, "rot": f * np.mean(rot) / 2,
            "vib_kin": f * np.mean(vk), "vib_pot": f * np.mean(vp)}


print("t = 0:", {k: round(v, 1) for k, v in modes().items()})
t_ps = 0.0
for chunk in (5, 20, 75, 200, 400):
    md.advance(md.t + chunk / PS)
    t_ps += chunk
    print(f"t = {t_ps:.0f} ps:", {k: round(v, 1) for k, v in modes().items()})
w = math.sqrt(400.0 / 0.5) / (PS * 1e-12)
print(f"bond: omega = sqrt(k/mu) = {w:.4g} 1/s, hbar omega / k_B = {sc.hbar * w / sc.k:.1f} K")
