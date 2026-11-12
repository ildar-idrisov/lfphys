"""R06 (GPU 0): the GPU kernel against the CPU step bit for bit in set-ups the shipped test does not cover: periodic
sides in both axes with a body force (the kernel's wrap-around), a driven lid with a periodic pair, a turning disk and
an interpolated disk, the dye with a drop; then the shipped GPU test itself.

Run (from engine/), through the host's GPU wrapper:
gpu_run.sh lf-b7rl-r06 --rm --gpus '"device=0"' -v $PWD:/lf:ro -v <this folder>:/out -e PYTHONDONTWRITEBYTECODE=1
  -e PYTHONPATH=/lf/lfphys -w /lf/lfphys light-funnel-viz sh -c "python3 /out/r06_gpu_equals_cpu.py &&
  python3 -m pytest -q -p no:cacheprovider tests/test_lbm.py -k gpu"
"""
import numpy as np

from lfphys.core import backend
from lfphys.core.fluids import lbm

backend.configure({"kernels": {"fluids.lbm": {"device": "gpu", "precision": "fp64"}}})
print("GPU available:", backend.devices()["gpu"]["available"])


def periodic_box(device):
    fl = lbm.Flow2D((96.0, 64.0), 1.0, nu=0.05, rho=1.0, dt=1.0, sides={s: "periodic" for s in lbm.SIDES},
                    gravity=(3e-6, -1e-6), dye=0.02, device=device)
    fl.add_obstacle(lbm.Disk((30.0, 31.0), 7.3), interpolated=True)
    fl.add_obstacle(lbm.Disk((70.0, 20.0), 5.0), omega=0.003)
    fl.add_dye(lbm.Disk((50.0, 50.0), 6.0), 1.0)
    return fl


def lid_channel(device):
    fl = lbm.Flow2D((80.0, 48.0), 1.0, nu=0.04, rho=1.0, dt=1.0,
                    sides={"left": "periodic", "right": "periodic", "top": lbm.Wall(0.06)}, dye=0.03, device=device)
    fl.add_obstacle(lbm.Rect((40.0, 18.0), (12.0, 5.0), 0.5), velocity=(0.01, 0.0))
    fl.add_dye_source(lbm.Disk((10.0, 30.0), 3.0), 1.0)
    return fl


for make in (periodic_box, lid_channel):
    c, g = make("cpu"), make("auto")
    print(make.__name__, "devices:", c.device, g.device)
    for k in range(2):
        c.advance(400)
        g.advance(400)
        same_f = np.array_equal(c.populations(), g.populations())
        same_d = np.array_equal(c.dye(), g.dye(), equal_nan=True)
        same_acc = all(np.array_equal(v, g._link_acc()[q]) for q, v in c._link_acc().items())
        print("  after %d steps: populations equal %s, dye equal %s, link records equal %s, forces equal %s" % (
            c.steps, same_f, same_d, same_acc, c.forces() == g.forces()))
        if k == 0:
            for fl in (c, g):
                fl.add_obstacle(lbm.Disk((60.0, 40.0), 3.0))
    print("  balance residuals cpu / gpu:", c.balance()["mass"]["relative_residual"], g.balance()["mass"]["relative_residual"])
