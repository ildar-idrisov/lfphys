# Review B1, script 06: the CPU fallback. Run in a container without a GPU, with LFPHYS_NO_GPU=1, and (GPU 0 given)
# as a user with no home directory. Prints what the backend reports, the notes for a GPU asked for, and whether a v08
# world builds with all its checks passing.
import os

from harness import Harness
from lfphys.core import backend as B
from lfphys.core.optics import angular_spectrum as AS

print("env: LFPHYS_NO_GPU =", os.environ.get("LFPHYS_NO_GPU"), "| HOME =", os.environ.get("HOME"),
      "| CUDA_VISIBLE_DEVICES =", os.environ.get("CUDA_VISIBLE_DEVICES"))
print("gpu:", B.devices()["gpu"])
notes = B.configure({"kernels": {AS.KERNEL: {"device": "gpu", "precision": "fp64"}}})
print("configure(device = gpu) notes:", notes)
h = Harness("v08_wave_3d", "gauss")
hdr = h.of("header")[0]
print("header backend.notes:", hdr["backend"]["notes"])
print("header backend.used:", hdr["backend"]["used"].get(AS.KERNEL))
bad = [cid for cid, c in h.checks().items() if c.get("ok") is False]
print("failed checks:", bad, "| errors:", h.errors())
