"""p03 preset "liquid_vapour" ("Жидкость и пар в поле: капля оседает, над ней пар"): 2-D LJ (force-shifted at 2.5
sigma), CSVR at 90 K = 0.751 eps/k, field 0.02. The 2-D LJ critical temperature is ~0.50 (Jiang & Gubbins 0.498,
Smit & Frenkel 0.515; arXiv:2606.08178 Table II), lower still for the force-shifted potential: at 0.751 there is no
liquid-vapour coexistence. The run: the density profile along the field (y), time-averaged. Control: the same scene
with the thermostat at 45 K (0.376): a liquid layer with a sharp interface under a dilute vapour."""
import common  # noqa: F401
import copy

import numpy as np
from harness import Harness

from p03_molecules.viz import KELVIN, NM, PS, SCHEMA


def profile(T_K, t_eq=200.0, t_avg=200.0):
    p = copy.deepcopy(SCHEMA.presets["liquid_vapour"]["params"])
    for o in p["scene"]["objects"]:
        if o["type"] == "thermostat":
            o["values"]["T"] = T_K
    h = Harness("p03_molecules", None, p)
    md = h.sim.md
    Ly = md.L[1]
    edges = np.arange(0.0, Ly + 1e-9, 1.0)
    md.step(int(t_eq / md.dt))
    hist = np.zeros(len(edges) - 1)
    ns = 0
    Ts = []
    for _ in range(int(t_avg / 0.5)):
        md.step(int(0.5 / md.dt))
        y = md.positions()[:, 1]
        hist += np.histogram(y, edges)[0]
        ns += 1
        Ts.append(md.temperature()["T"])
    rho = hist / ns / (md.L[0] * 1.0)
    print(f"thermostat {T_K} K = {T_K / KELVIN:.3f} eps/k; N = {md.n}; box {md.L[0]:.1f} x {Ly:.1f} sigma "
          f"({md.L[0] * NM:.1f} x {Ly * NM:.1f} nm); run {t_eq * PS:.0f} + {t_avg * PS:.0f} ps; "
          f"mean T = {np.mean(Ts) * KELVIN:.1f} K")
    print("   rho(y) per 1 sigma slab, bottom to top:")
    print("   " + " ".join(f"{r:.3f}" for r in rho))
    big = np.max(np.abs(np.diff(rho)))
    print(f"   largest jump between neighbouring slabs {big:.3f}; max rho {rho.max():.3f}, min rho {rho.min():.3f}; "
          f"rho(top 5 sigma) {rho[-5:].mean():.4f}")
    return rho


profile(90.0)
profile(45.0)
