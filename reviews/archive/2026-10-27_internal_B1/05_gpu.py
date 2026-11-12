# Review B1, script 05 (GPU 0 only, ~1 minute): device policy at work.
#  (a) which physical GPU the backend uses; (b) GPU memory a v08 worker holds (nvidia-smi memory.used of GPU 0 around
#  the CUDA context and the worlds; CuPy pool) — the other processes on GPU 0 are the owner's and may change it a little;
#  (c) GPU against CPU, fp64, on v08 worlds; (d) fp32 on the GPU at the edge of v08's range; (e) what happens when GPU
#  memory runs out (simulated by a CuPy pool limit); (f) the calibration: its duration and crossover.
import math
import subprocess
import time

import numpy as np

from harness import Harness
from lfphys.core import backend as B
from lfphys.core.optics import angular_spectrum as AS
from v08_wave_3d.viz import SCHEMA, _aperture


def used_mib():
    out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True).stdout
    return int(out.split()[0])


m0 = used_mib()
print("(a) devices:", B.devices()["gpu"])
cp = B._CP
print("    CUDA device 0 PCI bus id:", cp.cuda.Device(0).pci_bus_id, flush=True)
m1 = used_mib()
print(f"(b) GPU 0 memory.used: before CUDA {m0} MiB; after the backend's probe (context) {m1} MiB (+{m1 - m0})")

pool = cp.get_default_memory_pool()
t = time.time()
B.configure({"kernels": {AS.KERNEL: {"device": "gpu"}}})
hg = Harness("v08_wave_3d", "double")
tg = time.time() - t
m2 = used_mib()
print(f"    after a full-volume world (double, n = 256, pad 4) on the GPU: {m2} MiB (+{m2 - m0} over no CUDA); "
      f"CuPy pool holds {pool.total_bytes() / 2**20:.0f} MiB (in use {pool.used_bytes() / 2**20:.0f}); built in {tg:.1f} s")
t = time.time()
hs = Harness("v08_wave_3d", "square_big")
ts = time.time() - t
m3 = used_mib()
print(f"    after the 512-grid slices world (square_big): {m3} MiB (+{m3 - m0}); pool {pool.total_bytes() / 2**20:.0f} MiB;"
      f" built in {ts:.1f} s", flush=True)
fails = [cid for cid, c in hs.checks().items() if c.get("ok") is False]
print(f"    square_big checks failed on the GPU: {fails}")

print("\n(c) GPU against CPU, fp64, v08 'double' volume and 'circle' volume")
for preset in ("double", "circle"):
    B.configure({"kernels": {AS.KERNEL: {"device": "gpu"}}})
    g = Harness("v08_wave_3d", preset).sim.vol
    B.configure({"kernels": {AS.KERNEL: {"device": "cpu"}}})
    c = Harness("v08_wave_3d", preset).sim.vol
    print(f"    {preset}: max|U_gpu - U_cpu| / max|U| = {np.max(np.abs(g - c)) / np.max(np.abs(c)):.1e}", flush=True)

print("\n(d) fp32 on the GPU: double slit, lam = 0.3 um, z = 80 um, n = 256, pad 4")
p, _ = SCHEMA.resolve("double", {"lam": 0.3, "zmax": 80.0})
x = (np.arange(256) - 128) * 0.075
U0 = _aperture(p, x)
k = 2 * math.pi / 0.3
B.configure({"kernels": {AS.KERNEL: {"device": "gpu", "precision": "fp64"}}})
u64 = AS.propagate_field(U0, 0.075, k, 80.0, pad=4)
B.configure({"kernels": {AS.KERNEL: {"device": "gpu", "precision": "fp32"}}})
u32 = AS.propagate_field(U0, 0.075, k, 80.0, pad=4)
print(f"    fp32 error {np.max(np.abs(u32 - u64)) / np.max(np.abs(u64)):.1e} (declared bound 1e-5); used = {B.used()[AS.KERNEL]}")

print("\n(e) GPU memory exhausted (CuPy pool limited to 64 MiB, as if the owner's other jobs held the rest)")
B.configure(None)
pool.free_all_blocks()
pool.set_limit(size=64 * 2**20)
try:
    Harness("v08_wave_3d", "double")
    print("    the world was built (fallback to the CPU?)", B.used().get(AS.KERNEL))
except Exception as e:  # noqa: BLE001
    print(f"    world construction raised {type(e).__name__}: {str(e)[:120]}  (no fallback to the CPU)")
pool.set_limit(size=0)

print("\n(f) calibration")
t = time.time()
cal = B.calibrate([AS.KERNEL])[AS.KERNEL]
print(f"    took {time.time() - t:.1f} s; crossover {cal['crossover']}; rows:")
for r in cal["rows"]:
    print(f"      {r['size']:>8d}: cpu {r['cpu_s'] * 1e3:8.2f} ms  gpu {r['gpu_s'] * 1e3:8.2f} ms  x{r['cpu_s'] / r['gpu_s']:.1f}")
