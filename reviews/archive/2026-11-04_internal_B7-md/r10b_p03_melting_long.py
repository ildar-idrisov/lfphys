"""r10 continued: the "melting" preset at 80 K for 1000 ps (the player's default speed is 2 ps per second: 8 minutes of
watching): orientational order and the mean-square displacement in each 200 ps window. Control: the same atoms with
the bath at 120 K (1.0 eps/k)."""
import common  # noqa: F401
import copy

from harness import Harness

from p03_molecules.viz import KELVIN, PS, SCHEMA
import numpy as np

from lfphys.core.md import cells


def psi6(md):
    """As in r10: global |<psi6>|, mean local |psi6| (neighbours within 1.45 sigma), mean neighbour count."""
    x = md.positions()
    i, j = cells.pair_list(x, md.L, md.periodic, 1.45)
    dx = x[j] - x[i]
    dx -= md.L * np.rint(dx / md.L)
    z = np.exp(6j * np.arctan2(dx[:, 1], dx[:, 0]))
    s = np.bincount(i, weights=z.real, minlength=md.n) + 1j * np.bincount(i, weights=z.imag, minlength=md.n)
    s += np.bincount(j, weights=z.real, minlength=md.n) + 1j * np.bincount(j, weights=z.imag, minlength=md.n)
    c = np.bincount(i, minlength=md.n) + np.bincount(j, minlength=md.n)
    loc = np.where(c > 0, s / np.maximum(c, 1), 0)
    return abs(loc.mean()), float(np.mean(np.abs(loc))), float(np.mean(c))


def world(T_K):
    p = copy.deepcopy(SCHEMA.presets["melting"]["params"])
    for o in p["scene"]["objects"]:
        if o["type"] == "thermostat":
            o["values"]["T"] = T_K
    return Harness("p03_molecules", None, p)


for T_K, t_end in ((80.0, 1000), (120.0, 400)):
    md = world(T_K).sim.md
    print(f"bath {T_K} K ({T_K / KELVIN:.3f} eps/k):")
    for t0 in range(0, t_end, 200):
        md.msd_origin()
        md.advance((t0 + 200) / PS)
        g, l, c = psi6(md)
        print(f"   {t0:4d}-{t0 + 200:4d} ps: T = {md.temperature()['T'] * KELVIN:5.1f} K, |<psi6>| = {g:.3f}, "
              f"<|psi6|> = {l:.3f}, MSD in the window = {md.msd()['msd']:.3f} sigma^2")
