"""Peak memory of a Flow2D per node (dye on/off), CPU: VmHWM after build + 5 steps with an inlet, outlet and a disk."""
import sys, os, resource
sys.path[:0] = ["/lf/lfphys"]
import numpy as np
from lfphys.core.fluids import lbm as L
def hwm():
    for line in open("/proc/self/status"):
        if line.startswith("VmHWM"): return int(line.split()[1]) * 1024
base = hwm()
nx, ny, dye = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3] == "1"
dx = 2.2 / nx
fl = L.Flow2D(size=(nx * dx, ny * dx), dx=dx, nu=1e-3, rho=1.0, u_max=0.45, dye=(1e-3 if dye else None), device="cpu")
fl.set_sides({"left": L.Inlet(velocity=0.1), "right": L.Outlet()})
fl.add_obstacle(L.Disk((0.5, ny * dx / 2), 0.1 * ny * dx))
if dye: fl.add_dye_source(L.Disk((0.2, ny * dx / 2), 0.02))
built = hwm()
fl.advance(5)
f = fl.fields(); fl.vorticity()
peak = hwm()
N = nx * ny
print(f"N={N} dye={dye} build={((built-base)/N):.0f} B/node peak={((peak-base)/N):.0f} B/node footprint={fl._footprint()/N:.0f}", flush=True)
