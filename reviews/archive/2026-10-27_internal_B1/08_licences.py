# Review B1, script 08: spot-checks of lfphys/sources/dependencies.md against the installed wheels in the image.
import glob
import hashlib
import importlib.metadata as md
import os
import re

for pkg in ("numpy", "scipy", "python-flint", "cupy-cuda12x", "mpmath", "cuda-toolkit"):
    m = md.metadata(pkg)
    lic = m.get("License-Expression") or (m.get("License") or "")[:120].replace("\n", " ")
    print(f"{pkg:14s} {m['Version']:10s} License-Expression/License: {lic}")
    print(f"{'':25s} License-File: {m.get_all('License-File')[:8] if m.get_all('License-File') else None}")

sp = os.path.dirname(os.path.dirname(md.distribution("numpy").locate_file("numpy/__init__.py")))
print("\nsite-packages:", sp)
print("python_flint.libs:", sorted(os.listdir(os.path.join(sp, "python_flint.libs"))))
print("numpy.libs:", sorted(os.listdir(os.path.join(sp, "numpy.libs"))))
print("cupy .so not CuPy's own (outside cupy/ cupyx/ cupy_backends/):",
      [p for p in glob.glob(os.path.join(sp, "cupy*", "**", "*.so*"), recursive=True)
       if not re.search(r"/(cupy|cupyx|cupy_backends)/", p)][:5])
nv = sorted(glob.glob(os.path.join(sp, "nvidia_*", "License.txt")) + glob.glob(os.path.join(sp, "nvidia*", "**", "License.txt"), recursive=True))
nv = sorted(set(nv))
hashes = {p: hashlib.md5(open(p, "rb").read()).hexdigest() for p in nv}
print(f"\nNVIDIA License.txt files: {len(nv)}; distinct MD5: {set(hashes.values())}")
t = open(nv[0], encoding="utf-8", errors="replace").read()
norm = re.sub(r"\s+", " ", t)
for q in ["Install and use the SDK", "material additional functionality, beyond the included portions of the SDK",
          "you may not distribute or sublicense the SDK as a stand-alone product",
          "You may not use the SDK in any manner that would cause it to become subject to an open source software license",
          "Release Date: July 26, 2018", "Release date: August 16, 2018",
          "only for use in systems with NVIDIA GPUs", "provided that the object code files are not modified in any way",
          "commercially viable", "Open Source Initiative", "libnvJitLink", "libcufft.so", "libcusolverMg", "libnvrtc"]:
    print(f"  {'FOUND  ' if q in norm else 'absent '} {q!r}")
inst = sorted({os.path.basename(p) for p in glob.glob(os.path.join(sp, "nvidia", "*", "lib", "*.so*"))})
print("\ninstalled NVIDIA libraries:", inst)
