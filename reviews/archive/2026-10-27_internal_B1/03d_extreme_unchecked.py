# Review B1, script 03d: an allowed v08 world with wide-angle light (narrow double slit, long wavelength, coarse grid,
# deep volume): what it draws at z = z_max against a x16 window, and which of its checks fail.
import numpy as np

from harness import Harness
from lfphys.core.optics import angular_spectrum as AS

params = {"source": "double", "a": 0.2, "d": 2.0, "L": 8.0, "lam": 1.5, "n": 128, "zmax": 80.0}
h = Harness("v08_wave_3d", None, params)
s = h.sim
print("params:", params, "| pad used:", s.pad, "| half-window:", s.half, "um")
img = np.abs(s.vol[-1]) ** 2
ref = np.abs(AS.propagate_field(s.U0, s.dx, s.k, float(s.zs[-1]), pad=16, check=True)) ** 2
print(f"z = z_max plane: max|I - I_ref| / max I_ref = {np.max(np.abs(img - ref)) / ref.max():.2e};"
      f" peak drawn / true = {img.max() / ref.max():.3f}")
yz = np.abs(s.vol[:, :, s.n // 2]) ** 2
yref = np.abs(AS.propagate_slice(s.U0, s.dx, s.k, s.zs, axis=1, at=0.0, pad=16, check=True)) ** 2
print(f"y = 0 slice: max|I - I_ref| / max I_ref = {np.max(np.abs(yz - yref)) / yref.max():.2e}")
for cid, c in h.checks().items():
    print(f"check {cid}: ok={c.get('ok')} info={c.get('info', False)} value={c['value']}")
