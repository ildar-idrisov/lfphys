# Review B1, script 04: the fp32 policy (CPU; the same arithmetic as on the GPU, cuFFT vs pocketfft aside).
#  (a) the declared fp32 bound (max|U32 - U64| / max|U64| <= 1e-5) against the propagation distance, inside v08's own
#      parameter range (lam 0.3..1.5 um, z up to 80 um);
#  (b) a v08 world built with the owner's choice "fp32" for the angular spectrum: what its checks and its header say.
import math

import numpy as np

from harness import Harness
from lfphys.core import backend as B
from lfphys.core.optics import angular_spectrum as AS
from v08_wave_3d.viz import SCHEMA, _aperture

print("(a) fp32 error against fp64 (CPU), v08 geometry n = 256, dx = lam/4, pad 4")
for preset, extra in (("gauss", {"lam": 0.3, "zmax": 80.0}), ("double", {"lam": 0.3, "zmax": 80.0}),
                      ("double", {})):
    p, _ = SCHEMA.resolve(preset, extra)
    lam, n = p["lam"], int(p["n"])
    dx = lam / 4
    x = (np.arange(n) - n // 2) * dx
    U0 = _aperture(p, x)
    k = 2 * math.pi / lam
    zs = [1.0, 10.0, 30.0, 80.0]
    zs = [z for z in zs if z <= p["zmax"]]
    B.configure({"kernels": {AS.KERNEL: {"device": "cpu", "precision": "fp64"}}})
    u64 = AS.propagate_field(U0, dx, k, zs, pad=4)
    B.configure({"kernels": {AS.KERNEL: {"device": "cpu", "precision": "fp32"}}})
    u32 = AS.propagate_field(U0, dx, k, zs, pad=4)
    for i, z in enumerate(zs):
        e = np.max(np.abs(u32[i] - u64[i])) / np.max(np.abs(u64[i]))
        print(f"  {preset:6s} lam={lam:3.1f} z={z:5.1f} um (k z = {k * z:7.0f} rad): fp32 error {e:.1e}"
              f"{'  > declared bound 1e-5' if e > 1e-5 else ''}", flush=True)

print("\n(b) v08 worlds with the angular spectrum set to fp32 (device cpu)")
for preset in ("double", "gauss"):
    B.configure({"kernels": {AS.KERNEL: {"device": "cpu", "precision": "fp32"}}})
    h = Harness("v08_wave_3d", preset)
    hdr = h.of("header")[0]
    c = h.checks()
    print(f"  preset {preset}: header backend.settings = {hdr['backend']['settings']['kernels']}")
    print(f"     header backend.used[{AS.KERNEL}] = {hdr['backend']['used'].get(AS.KERNEL)}")
    print(f"     check 'device' label: {c['device']['label']}")
    print(f"     drawn volume dtype: {h.sim.vol.dtype}")
    sr = c.get("slice_route")
    if sr:
        print(f"     check slice_route: value {sr['value']:.2e}, tol {sr['tol']:.0e}, ok = {sr.get('ok')}")
    B.configure(None)
