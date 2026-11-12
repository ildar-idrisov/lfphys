# P1 reproduction: the running momentum check on the 4 x 16 body-force channel and on the open channel.
import argparse
import math
import sys
import time

import numpy as np

sys.path[:0] = ["/lf/lfphys"]
from lfphys.core import backend  # noqa: E402
from lfphys.core.fluids import lbm  # noqa: E402

PER_X = {"left": "periodic", "right": "periodic"}


def channel(ny=16, tau=0.8, g=1e-5):
    nu = (tau - 0.5) / 3
    fl = lbm.Flow2D((4.0, float(ny)), 1.0, nu=nu, rho=1.0, dt=1.0, sides=PER_X, gravity=(g, 0.0), device="cpu")
    H = float(ny)
    fl.set_flow(velocity=lambda X, Y: (g / (2 * nu) * Y * (H - Y), 0 * X))
    return fl


def row(fl, tag):
    c = fl.checks()
    b = fl.balance()
    print(f"  {tag:>8s} steps {fl.steps:7d}: momentum {abs(c['momentum']['relative_residual']):.3e} / "
          f"{c['momentum']['limit']:.3e} ok={c['momentum']['ok']}; mass {abs(c['mass']['relative_residual']):.3e} "
          f"ok={c['mass']['ok']}" + (f"; dye {abs(c['dye']['relative_residual']):.3e} ok={c['dye']['ok']}" if 'dye' in c else ""),
          flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="P1 reproduction")
    ap.add_argument("--steps", type=int, nargs="*", default=[9537, 16000, 32000, 64000])
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--open-steps", type=int, nargs="*", default=[32000, 64000, 128000])
    a = ap.parse_args()
    backend.configure(None)
    t0 = time.time()
    fl = channel()
    done = 0
    print("== 4 x 16 channel, tau 0.8, g 1e-5 (fresh start, books from t = 0)")
    for s in a.steps:
        fl.advance(s - done)
        done = s
        row(fl, "chan")
    print(f"  ({time.time() - t0:.1f} s)")
    if a.open:
        t0 = time.time()
        fl = lbm.Flow2D(size=(0.6, 0.12), dx=0.005, nu=1e-3, rho=1.0, u_max=0.3, dye=1e-3, device="cpu",
                        sides={"left": lbm.Inlet(velocity=0.2, profile="parabolic", ramp=0.2), "right": lbm.Outlet()})
        fl.add_obstacle(lbm.Disk((0.15, 0.06), 0.02), interpolated=True, label="disk")
        fl.add_dye_source(lbm.Disk((0.05, 0.06), 0.01), 1.0)
        done = 0
        print("== open channel 120 x 24 (inlet, outlet, interpolated disk, dye source)")
        for s in a.open_steps:
            fl.advance(s - done)
            done = s
            row(fl, "open")
        print(f"  ({time.time() - t0:.1f} s)")
