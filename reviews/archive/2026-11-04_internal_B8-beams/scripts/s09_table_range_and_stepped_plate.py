"""s09: (a) where v16's detectors sample the beam relative to the radial table's range (apparatus.py: DovePrism samples a
square of half-width 2.2 w(z_d) sqrt(max(|l|,1)/2 + p + 1); SpinningDisc a disc of 2.6 w(z_d) sqrt(...); the table
reaches r_far = 1.45 max(half, am_half)); beyond r_far RadialTable evaluates its splines outside their data. The table's
field there is compared with the direct route.
(b) the stepped spiral plate of tests/test_beams.py (l = 3, 8 steps): OAM per photon of the propagated field on two grids,
against the thin-mask value derived here: the plate's harmonics are n = l + jN with |c_n| = |sinc(n/N)|, and the
symmetric sum gives <L> = (N/2pi) sin(2 pi l / N) = 0.900 for N = 8, l = 3.
"""
import math
import sys

import numpy as np

for p in ("/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys"):
    sys.path.insert(0, p)
from lfphys.core.optics import beams as B  # noqa: E402
from lfphys.core.optics import beams_generation as GEN  # noqa: E402
from v16_optical_vortices.engine import apparatus as A  # noqa: E402

print("(a) detector sampling radius against the table's range")
for l, p in [(3, 0), (6, 3), (6, 0)]:
    bm = A.Beam("mode", "exact", l, p, 1.5, 1.0, "+1", 1.5)
    L = bm.z1 - bm.z0
    z_d = bm.z1 - 0.10 * L
    w = bm.width(z_d)
    fac = math.sqrt(max(abs(l), 1) / 2 + p + 1)
    r_dove = math.sqrt(2) * 2.2 * w * fac
    r_disc = 2.6 * w * fac
    r_far = float(bm.r[-1])
    rr = np.array([0.9 * r_far, 1.0 * r_far, min(r_dove, 1.3 * r_far)])
    Et = bm.fields(rr, 0 * rr, np.full(3, z_d))[0]
    Ed = bm.direct(rr, 0 * rr, np.full(3, z_d))
    pk = math.sqrt(bm.peak)
    print(f"  l = {l}, p = {p}: r_far = {r_far:.2f}, Dove square corner = {r_dove:.2f}, disc = {r_disc:.2f};"
          f" |E_table - E_direct| / peak at r = {np.round(rr, 2)}: {np.round(np.max(np.abs(Et - Ed), axis=0) / pk, 12)}"
          f"; |E_direct|/peak there {np.round(np.max(np.abs(Ed), axis=0) / pk, 12)}")

print("(b) stepped spiral plate, l = 3, 8 steps, Gaussian w = 2, z = 6 (as in the engine's test)")
l, N, w, z = 3, 8, 2.0, 6.0
print(f"  thin-mask symmetric sum (N/2pi) sin(2 pi l/N) = {N / (2 * math.pi) * math.sin(2 * math.pi * l / N):.4f};"
      f" power in n = l: sinc^2(l/N) = {(math.sin(math.pi * l / N) / (math.pi * l / N)) ** 2:.4f}")
K = 2 * math.pi
for n, dx in ((512, 0.125), (1024, 0.0625)):
    x = (np.arange(n) - n // 2) * dx
    X, Y = np.meshgrid(x, x, indexing="ij")
    U0 = np.exp(-(X * X + Y * Y) / w ** 2) * GEN.spiral_phase_plate(X, Y, l, N)
    Uz = GEN.propagate(U0, dx, K, z)
    print(f"  grid {n} x {dx}: OAM per photon of the propagated field = {B.scalar_oam_per_photon(Uz, x, x):.4f};"
          f" of the sampled mask itself = {B.scalar_oam_per_photon(U0, x, x):.4f}")
