# Review B8-mie, script s06b: separate two effects that s06 mixed: (1) the bias of cutting the gamma distribution at
# +-3 sigma, on ONE node grid (the 6-sigma grid, weights outside 3 sigma set to zero and renormalised); (2) the spread
# of the fine "reference" itself between node spacings (narrow resonances sampled, not resolved), near the glory.
import sys

import numpy as np

sys.path.insert(0, "/lf/lfphys")
from lfphys.core import data as D  # noqa: E402
from lfphys.core.optics import mie_poly as MP  # noqa: E402

TH = np.radians(np.linspace(125.0, 180.0, 551))
deg = np.degrees(TH)
glo = deg > 170
for label, r, w, lam, dx in [("rainbow 150 um +-2 %", 150.0, 0.02, 0.55, 0.05), ("glory 8 um +-10 %", 8.0, 0.10, 0.55, 0.005),
                             ("fogbow 15 um +-15 %", 15.0, 0.15, 0.45, 0.005)]:
    m = complex(float(D.water_index(lam * 1e3, 10.0)))
    nd6 = MP.size_nodes(r, w, lam, dx_max=dx, n_sigma=6.0, max_nodes=10 ** 6)
    full = MP.average(m, lam, nd6, TH)
    nd3 = dict(nd6)
    keep = np.abs(nd6["r"] - r) <= 3 * w * r
    w3 = np.where(keep, nd6["w"], 0.0)
    nd3["w"] = w3 / w3.sum()
    cut = MP.average(m, lam, nd3, TH)
    top = full["dsdo"].max()
    d = np.abs(cut["dsdo"] - full["dsdo"]) / top
    print(f"{label}: the 3-sigma cut on the same grid: max |diff|/max {d.max():.2e} (glory {d[glo].max():.2e}); "
          f"weight dropped {1 - w3.sum():.2e}")
    outs = []
    for dxx in (dx, dx * 0.61803, dx * 0.37):
        nd = MP.size_nodes(r, w, lam, dx_max=dxx, max_nodes=10 ** 6)
        outs.append(MP.average(m, lam, nd, TH)["dsdo"])
    sp = max(np.abs(outs[i] - outs[j]).max() for i in range(3) for j in range(i)) / top
    spg = max(np.abs(outs[i] - outs[j])[glo].max() for i in range(3) for j in range(i)) / top
    print(f"   fine sums at dx = {dx:g}, {dx * 0.61803:.4g}, {dx * 0.37:.4g}: largest mutual difference / max {sp:.2e} "
          f"(glory {spg:.2e})")
