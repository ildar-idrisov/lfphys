"""p03 preset "melting" ("Кристалл аргона нагревают термостатом: плавление"): a 2-D LJ crystal object (density 0.85
in a 10 x 10 nm periodic box) and a CSVR bath at 80 K = 0.668 eps/k. (1) What the crystal object builds:
MD.fill(density) gives n = 0.85 A atoms on the first n sites of a lattice whose spacing is set by the box and the cell
counts, not by the density. (2) Does it melt: the bond-orientational order (global |<psi6>| and the mean local
|psi6|) and the mean-square displacement after equilibration. Control: the same crystal held at 20 K."""
import common  # noqa: F401
import copy
import math

import numpy as np
from harness import Harness

from lfphys.core.md import cells
from p03_molecules.viz import KELVIN, PS, SCHEMA


def psi6(md):
    x = md.positions()
    i, j = cells.pair_list(x, md.L, md.periodic, 1.45)
    dx = x[j] - x[i]
    dx -= md.L * np.rint(dx / md.L)
    th = np.arctan2(dx[:, 1], dx[:, 0])
    z = np.exp(6j * th)
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


h = world(80.0)
md = h.sim.md
x = md.positions()
i, j = cells.pair_list(x, md.L, md.periodic, 1.5)
dx = x[j] - x[i]
dx -= md.L * np.rint(dx / md.L)
r = np.sqrt((dx * dx).sum(1))
A = float(np.prod(md.L))
print(f"(1) box {md.L[0]:.3f} sigma; atoms {md.n} = round(0.85 x {A:.1f}); nearest-neighbour distance "
      f"{r.min():.4f}..{np.percentile(r, 50):.4f} sigma -> lattice density 2/(sqrt(3) a^2) = "
      f"{2 / (math.sqrt(3) * np.percentile(r, 50) ** 2):.3f}; sites of that lattice in the box "
      f"{A * 2 / (math.sqrt(3) * np.percentile(r, 50) ** 2):.0f}")
xs = np.sort(x[:, 0])
gaps = np.diff(np.r_[xs, xs[0] + md.L[0]])
print(f"    the widest empty strip across x: {gaps.max():.3f} sigma (a row spacing is ~{np.median(gaps[gaps > 0.05]):.3f})")
for T_K, hh in ((80.0, h), (20.0, world(20.0))):
    md = hh.sim.md
    rows = []
    for t in (0, 25, 50, 100):
        target = t / PS
        if target > md.t:
            md.advance(target)
        g, l, c = psi6(md)
        rows.append(f"t = {t:3d} ps: T = {md.temperature()['T'] * KELVIN:5.1f} K, |<psi6>| = {g:.3f}, <|psi6|> = {l:.3f}")
    md.msd_origin()
    md.advance(md.t + 100 / PS)
    g, l, c = psi6(md)
    m = md.msd()
    rows.append(f"t = 200 ps: T = {md.temperature()['T'] * KELVIN:5.1f} K, |<psi6>| = {g:.3f}, <|psi6|> = {l:.3f}; "
                f"MSD over the last 100 ps = {m['msd']:.3f} sigma^2")
    print(f"(2) bath {T_K} K ({T_K / KELVIN:.3f} eps/k):")
    for s in rows:
        print("    " + s)
