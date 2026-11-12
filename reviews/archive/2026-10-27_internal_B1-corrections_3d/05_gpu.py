# Review of the B1 corrections (reviewer's script). GPU 0 (seconds): the spectra evaluated on the device (CuPy
# closed forms, cupyx j1 for the disc) against the host (scipy); propagate_plane and propagate_current GPU vs CPU for
# turned and tilted planes, plain and band-limited; a Spectral fn that cannot take CuPy arrays (host fallback);
# timings of a v08-size slice.
import argparse
import math
import sys
import time

import numpy as np

sys.path.insert(0, "/lf/lfphys")
from common_rev import Tee, rel  # noqa: E402
from lfphys.core import backend  # noqa: E402
from lfphys.core import geometry as G  # noqa: E402
from lfphys.core.optics import angular_spectrum as AS  # noqa: E402
from lfphys.core.optics import aperture_fields as AF  # noqa: E402

argparse.ArgumentParser(description=__doc__).parse_args()
out = Tee("out/05_gpu.txt")
dev = backend.devices()["gpu"]
out(f"GPU: {dev.get('name')} pci {dev.get('pci_bus_id')} available {dev['available']}")
if not dev["available"]:
    sys.exit(0)
import cupy as cp  # noqa: E402

K = 2 * math.pi / 0.5
DX = 0.125
q = 2 * math.pi * np.fft.fftfreq(1024, DX)
QX, QY = np.meshgrid(q, q, indexing="ij", sparse=True)
for name, fn in (("disc a = 3", AF.disc_spectrum(3.0)), ("rect", AF.rect_spectrum([(-2.75, -1.25, -4, 4), (1.25, 2.75, -4, 4)])),
                 ("gauss w = 1.5", AF.gaussian_spectrum(1.5)), ("disc turned 37 deg", AF.rotated(AF.disc_spectrum(3.0), -0.65))):
    h = np.broadcast_to(np.asarray(fn(QX, QY), complex), (1024, 1024))
    d = cp.asnumpy(cp.broadcast_to(cp.asarray(fn(cp.asarray(QX), cp.asarray(QY)), dtype=cp.complex128), (1024, 1024)))
    out(f"spectrum {name:<20}: max|device - host| / max|host| = {np.max(np.abs(d - h)) / np.max(np.abs(h)):.2e}")


def both(f):
    res = {}
    for d in ("cpu", "gpu"):
        backend.configure({"kernels": {"optics.angular_spectrum": {"device": d}}})
        t0 = time.time()
        res[d] = f()
        res[d + "_t"] = time.time() - t0
    backend.configure(None)
    return res


n = 256
for sname, src in (("disc", AS.Spectral((n, n), AF.disc_spectrum(3.0))),
                   ("rect", AS.Spectral((n, n), AF.rect_spectrum([(-2.75, -1.25, -4, 4), (1.25, 2.75, -4, 4)])))):
    for nrm, bl in (((0.4, 0.3, 0.86), False), ((0.4, 0.3, 0.86), True), ((-0.5, 0.866, 0.0), False), ((1.0, 0.0, 0.0), True)):
        pl = G.Plane.horizontal(nrm, (0.3, -0.4, 15.0))
        ts = np.linspace(-20, 20, 256)
        r = both(lambda: AS.propagate_plane(src, DX, K, pl, (-22.0, 22.0), ts, pad=4, band_limit=bl)[1])
        out(f"plane {sname} n={nrm} bl={bl}: max|gpu - cpu|/peak {rel(r['gpu'], r['cpu']):.2e}; cpu {r['cpu_t']:.2f} s, gpu {r['gpu_t']:.2f} s")
    r = both(lambda: AS.propagate_current(src, DX, K, np.linspace(1, 30, 10), pad=4))
    out(f"current {sname}: max|gpu - cpu| j {np.max(np.abs(r['gpu'][0] - r['cpu'][0])):.2e}, P rel {np.max(np.abs(r['gpu'][1] - r['cpu'][1]) / r['cpu'][1]):.2e}; "
        f"cpu {r['cpu_t']:.2f} s, gpu {r['gpu_t']:.2f} s")

# a closed form written for NumPy only: the engine falls back to the host
fn_np = lambda qx, qy: np.vectorize(lambda a, b: complex(math.exp(-(a * a + b * b) * 0.5)))(*np.broadcast_arrays(qx, qy))  # noqa: E731
src = AS.Spectral((64, 64), fn_np)
r = both(lambda: AS.propagate_field(src, DX, K, [2.0], pad=2))
out(f"NumPy-only Spectral fn on the GPU: falls back, max|gpu - cpu| {np.max(np.abs(r['gpu'] - r['cpu'])):.2e}")
out(f"memory after: {cp.get_default_memory_pool().used_bytes() / 1e6:.1f} MB used in the pool")
out("done")
