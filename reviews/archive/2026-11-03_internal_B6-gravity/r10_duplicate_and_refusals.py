# Reviewer script (B6 gravity): a refused change must leave the scene AND the engine as they were
# (lfviz.playground: "raise ValueError to refuse: the scene is then left as it was").
# (1) Newton: duplicate a massive body (the copy is placed at the source's current state, i.e. the same point);
# (2) Newton: add a star exactly on another one; (3) Kerr: set a body's colour only (does it restart the orbit?).
import sys

import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402

from p01_gravity.viz import YR  # noqa: E402


def run(h, t_end, n=50):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + (t_end - t0) * k / n)
        h.runner._frame(0.0)


def state(h):
    nb = h.sim.mode.nb
    return (f"scene objects {[o['id'] for o in h.sim.objects.values()]}; engine keys {nb.keys}; "
            f"engine rows x {nb._x.shape[0]}, a {nb._a.shape[0]}")


for label, cmd in (("duplicate the Earth (o2)", dict(op="duplicate", id="o2")),
                   ("add a star on the Sun's position", dict(op="add", type="star",
                                                              values={"mass": 1.0, "x": 0.0, "y": 0.0, "z": 0.0}))):
    h = Harness("p01_gravity", "sun_earth")
    run(h, 0.1 * YR, 10)
    print(f"({label}) before: {state(h)}")
    h.cmd("scene", **cmd)
    errs = [m for m in h.of("log") + h.of("error") + h.of("refused") if m]
    print(f"   after the command: {state(h)}")
    print("   messages:", [(m.get("type"), str(m.get("text", m))[:110]) for m in h.msgs[-6:] if m[0].get("type") not in
                            ("frame", "check", "trail")] if False else
          [(m.get("type"), str(m.get("text", ""))[:110]) for m, _ in h.msgs[-6:]
           if m.get("type") not in ("frame", "check", "trail")])
    try:
        run(h, h.sim.t + 0.1 * YR, 10)
        print("   the world runs on:", state(h))
    except Exception as exc:  # noqa: BLE001
        print(f"   the world FAILS on the next frame: {type(exc).__name__}: {str(exc)[:120]}")

print()
h = Harness("p01_gravity", "kerr_orbits")
run(h, 50 * h.sim.mode.T, 20)
g = h.sim.mode.geo
i = g.keys.index("o2")
before = g.bl()[i].copy(), float(g.proper_time()[i])
h.cmd("scene", op="set", id="o2", values={"color": "#ff6b6b"})
i = g.keys.index("o2")
after = g.bl()[i].copy(), float(g.proper_time()[i])
print(f"(3) Kerr body o2 before a colour change: r, theta, phi = {np.round(before[0], 6).tolist()}, tau = {before[1]:.6g}; "
      f"after: {np.round(after[0], 6).tolist()}, tau = {after[1]:.6g}")
