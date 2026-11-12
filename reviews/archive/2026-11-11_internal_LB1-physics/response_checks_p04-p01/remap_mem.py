# remap_memory_estimate against the measured peak of a remap (tracemalloc: NumPy reports its buffers)
import sys, tracemalloc
sys.path[:0] = ["/lf/lfphys"]
from lfphys.core import backend
from lfphys.core.fluids import lbm
backend.configure(None)
for dye in (1e-3, None):
    for (n0, n1) in (((200, 40), (400, 80)), ((400, 80), (200, 40)), ((200, 40), (200, 40))):
        fl = lbm.Flow2D(size=(1.0, 0.2), dx=1.0 / n0[0], nu=1e-3, rho=1.0, u_max=0.2, dye=dye, device="cpu",
                        sides={"left": lbm.Inlet(0.1, "parabolic"), "right": lbm.Outlet()})
        fl.add_obstacle(lbm.Disk((0.3, 0.1), 0.03), interpolated=True)
        if dye:
            fl.add_dye_source(lbm.Disk((0.1, 0.1), 0.01), 1.0)
        fl.advance(20)
        est = fl.remap_memory_estimate(*n1)
        tracemalloc.start(); tracemalloc.reset_peak()
        base = tracemalloc.get_traced_memory()[0]
        fl.remap(dx=1.0 / n1[0], u_max=0.25 if n1 == n0 else None)
        peak = tracemalloc.get_traced_memory()[1] - base
        tracemalloc.stop()
        print(f"dye={dye} {n0}->{n1}: peak {peak/1e6:.2f} MB, estimate {est/1e6:.2f} MB, ratio {peak/est:.3f}")
