# Review B8-fdtd, script s15: the measured rates behind cost_estimate and the crossover (fdtd.RATES, crossover 128^2):
# seconds per step of the periodic vacuum benchmark world on the CPU (and GPU 0 with --gpu), best of 3, against the
# table; and the cost estimate of a complex (Bloch) world against its measured step.
import argparse
import math
import numpy as np
from lfphys.core.em import fdtd as F
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--gpu", action="store_true")
args = ap.parse_args()
devs = ["cpu"] + (["gpu"] if args.gpu else [])
if args.gpu:
    from lfphys.core import backend
    backend.configure({"kernels": {F.KERNEL: {"device": "gpu"}}})
for dim, sizes in ((2, (64 ** 2, 128 ** 2, 256 ** 2, 1024 ** 2)), (3, (32 ** 3, 64 ** 3, 128 ** 3))):
    for n in sizes:
        row = []
        for dev in devs:
            t = min(F.bench(n, dim, "cpu" if dev == "cpu" else "auto", steps=10) for _ in range(3))
            table = F._interp_rate("2d" if dim == 2 else "3d", dev, n)
            row.append(f"{dev}: {t * 1e3:8.3f} ms (table {table * 1e3:8.3f}, ratio {t / table:4.2f})")
        print(f"  {dim}-D {round(n ** (1 / dim))}^{dim}: " + "  ".join(row))
w = F.FDTD((12.8, 0.05 * 256), 0.05, pol="tm", boundary="periodic", bloch=(0.0, 1.0), device="cpu")
w.advance(2)
import time
t0 = time.perf_counter(); w.advance(10); t = (time.perf_counter() - t0) / 10
c = w.cost_estimate()
print(f"  complex 256^2 world (CPU): measured {t * 1e3:.3f} ms, estimate {c['per_step_s'] * 1e3:.3f} ms, "
      f"'other device' estimate {c['other_device_per_step_s'] * 1e3:.3f} ms (no complex factor)")
