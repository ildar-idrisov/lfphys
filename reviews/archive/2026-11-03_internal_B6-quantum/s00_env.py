"""Environment of the review's runs: versions of the libraries in the image."""
import sys, numpy, scipy, platform
print("python", sys.version.split()[0], "numpy", numpy.__version__, "scipy", scipy.__version__, platform.machine())
import os; print("LFPHYS_NO_GPU", os.environ.get("LFPHYS_NO_GPU"), "uid", os.getuid())
from lfphys.core import backend
print(backend.devices())
