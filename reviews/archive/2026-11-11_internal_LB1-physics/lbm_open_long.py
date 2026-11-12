# Reviewer's check: the running conservation bound (2 eps per step) on an open channel run long (STATUS V41 (ac)).
import sys
sys.path[:0] = ["/lf/lfphys"]
from lfphys.core import backend  # noqa: E402
from lfphys.core.fluids import lbm  # noqa: E402

backend.configure(None)
fl = lbm.Flow2D(size=(0.6, 0.12), dx=0.005, nu=1e-3, rho=1.0, u_max=0.3, dye=None, device="cpu",
                sides={"left": lbm.Inlet(velocity=0.2, profile="parabolic", ramp=0.2), "right": lbm.Outlet()})
fl.add_obstacle(lbm.Disk((0.15, 0.06), 0.02), interpolated=True, label="disk")
done = 0
for target in (32000, 64000, 96000, 128000):
    fl.advance(target - done)
    done = target
    c = fl.checks()
    print(f"{done:7d} steps (t = {fl.t:.3f} s): momentum |rel.res| {abs(c['momentum']['relative_residual']):.3e} limit "
          f"{c['momentum']['limit']:.3e} ok {c['momentum']['ok']}; mass |rel.res| {abs(c['mass']['relative_residual']):.3e} "
          f"ok {c['mass']['ok']}", flush=True)
