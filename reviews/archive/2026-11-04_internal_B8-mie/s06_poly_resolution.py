# Review B8-mie, script s06: the size average (lfphys.core.optics.mie_poly) as v17 uses it (dx_max = 0.25,
# n_sigma = 3, at most 1200 nodes): its actual error against a much finer sum, against its own half-sum estimate
# "err"; and the bias of the +-3 sigma cut of the gamma distribution (not part of "err").
import math
import sys
import time

import numpy as np

sys.path.insert(0, "/lf/lfphys")
from lfphys.core import data as D  # noqa: E402
from lfphys.core.optics import mie_poly as MP  # noqa: E402

TH = np.radians(np.linspace(125.0, 180.0, 551))


def run(r, w, lam_um, dx, n_sigma=3.0, max_nodes=200000):
    m = complex(float(D.water_index(lam_um * 1e3, 10.0)))
    nodes = MP.size_nodes(r, w, lam_um, dx_max=dx, n_sigma=n_sigma, max_nodes=max_nodes)
    return MP.average(m, lam_um, nodes, TH), nodes


cases = [("supernumerary 100 um +-0.5 %, 550 nm", 100.0, 0.005, 0.55, 0.01),
         ("rainbow 150 um +-2 %, 550 nm", 150.0, 0.02, 0.55, 0.05),
         ("glory 8 um +-10 %, 550 nm", 8.0, 0.10, 0.55, 0.005),
         ("fogbow 15 um +-15 %, 450 nm", 15.0, 0.15, 0.45, 0.005)]
for label, r, w, lam, dx_ref in cases:
    t0 = time.time()
    v17, nd = run(r, w, lam, 0.25, max_nodes=1200)
    ref, ndr = run(r, w, lam, dx_ref)
    err_true = np.abs(v17["dsdo"] - ref["dsdo"])
    top = ref["dsdo"].max()
    ratio = err_true / np.maximum(v17["err"], 1e-300)
    bow = (np.degrees(TH) > 136) & (np.degrees(TH) < 146)
    glo = np.degrees(TH) > 170
    print(f"{label}: v17 nodes {len(nd['r'])} (dx {nd['dx']:.3f}, coarse {nd['coarse']}), reference nodes "
          f"{len(ndr['r'])} (dx {ndr['dx']:.4f}); max |error|/max = {err_true.max() / top:.2e} (bow {err_true[bow].max() / top:.2e}, "
          f"glory {err_true[glo].max() / top:.2e}); max 'err'/max = {v17['err'].max() / top:.2e}; error > err at "
          f"{np.mean(err_true > v17['err']) * 100:.0f} % of angles (largest error/err {ratio.max():.1f}); "
          f"C_sca rel err {abs(v17['C_sca'] / ref['C_sca'] - 1):.1e} vs err_C_sca rel {v17['err_C_sca'] / ref['C_sca']:.1e}  "
          f"({time.time() - t0:.0f} s)")
    cut6, _ = run(r, w, lam, dx_ref, n_sigma=6.0)
    d = np.abs(ref["dsdo"] - cut6["dsdo"])
    print(f"   cut at 3 sigma against 6 sigma (same fine dx): max |diff|/max = {d.max() / top:.2e}, at the glory "
          f"(theta > 170) {d[glo].max() / top:.2e}; C_sca rel {abs(ref['C_sca'] / cut6['C_sca'] - 1):.1e}")

print("\nbig_drops (300 um +-10 %) at 550 nm: the 1200-node cap (coarse) against dx = 0.25")
t0 = time.time()
v17, nd = run(300.0, 0.10, 0.55, 0.25, max_nodes=1200)
ref, ndr = run(300.0, 0.10, 0.55, 0.25)
e = np.abs(v17["dsdo"] - ref["dsdo"])
print(f"  v17 nodes {len(nd['r'])} dx {nd['dx']:.2f} (coarse {nd['coarse']}); reference nodes {len(ndr['r'])}; max |error|/max "
      f"{e.max() / ref['dsdo'].max():.2e}; max 'err'/max {v17['err'].max() / ref['dsdo'].max():.2e}; error > err at "
      f"{np.mean(e > v17['err']) * 100:.0f} % of angles  ({time.time() - t0:.0f} s)")
