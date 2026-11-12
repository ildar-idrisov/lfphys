# Review B1, script 03: what v08 draws against the same propagation in a much wider padded window (CPU, fp64).
# v08 pads x2 or x4 "so that the periodic copies of the field do not reach the region shown" (README). The reference
# here is the same grid, same aperture, same z planes, padded x16 (y = 0 slice, x = 0 slice and the plane z = z_max).
# Reported: max |I - I_ref| / max I_ref (linear view), and on the six-decade log view the share of pixels with
# I_ref > 1e-6 max where |log10(I/I_ref)| > 0.1 (a visible change of colour on that scale).
import math
import sys

import numpy as np

from harness import Harness
from lfphys.core.optics import angular_spectrum as AS

PAD_REF = 16


def compare(img, ref):
    pk = ref.max()
    lin = float(np.max(np.abs(img - ref)) / pk)
    m = ref > 1e-6 * pk
    with np.errstate(divide="ignore", invalid="ignore"):
        dl = np.abs(np.log10(np.maximum(img[m], 1e-300) / ref[m]))
    return lin, float(np.mean(dl > 0.1)), float(np.max(dl))


presets = sys.argv[1:] or ["double", "circle", "gauss", "double_slices", "square_big"]
for preset in presets:
    h = Harness("v08_wave_3d", preset)
    s = h.sim
    print(f"preset {preset}: n={s.n} dx={s.dx:.4g} half={s.half:.3g} zmax={s.zs[-1]:g} pad used={s.pad}", flush=True)
    j = s.n // 2
    if s.vol is not None:
        drawn = {"y=0": np.abs(s.vol[:, :, j]) ** 2, "x=0": np.abs(s.vol[:, j, :]) ** 2, "z=zmax": np.abs(s.vol[-1]) ** 2}
    else:
        drawn = {}
        for (pl, c), img in s.planes.items():
            if pl == "xz" and s.modelling.approximation:
                continue  # the reduced model is compared by the run itself
            drawn[{"xz": "y=0", "yz": "x=0", "xy": "z=zmax"}[pl]] = img
    for key, img in drawn.items():
        if key == "z=zmax":
            ref = np.abs(AS.propagate_field(s.U0, s.dx, s.k, float(s.zs[-1]), pad=PAD_REF, check=True)) ** 2
        else:
            axis = 1 if key == "y=0" else 0
            ref = np.abs(AS.propagate_slice(s.U0, s.dx, s.k, s.zs, axis=axis, at=0.0, pad=PAD_REF, check=True)) ** 2
        lin, share, worst = compare(img, ref)
        print(f"   {key:7s}: linear max|dI|/max I = {lin:.2e};  log view: {share * 100:5.1f}% of pixels off by > 0.1 decade"
              f" (worst {worst:.2f} decades)", flush=True)
