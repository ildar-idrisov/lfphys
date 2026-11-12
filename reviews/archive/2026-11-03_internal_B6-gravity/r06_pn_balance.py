# Reviewer script (B6 gravity): the playground's PN energy-balance check (p01 PNMode.checks): the ratio (orbital
# energy lost) / (time integral of the 1PN circular flux in x = (m Omega)^(2/3)) against 1 with tolerance 100 x^2,
# x = 1/r (r harmonic). Measured for several binaries: (ratio - 1) / x^2 along the run, and every failed message.
import sys

import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402


def run(h, t_end, n=200):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + (t_end - t0) * k / n)
        h.runner._frame(0.0)


for q, r0, span in ((1.0, 20.0, 2.0e4), (1.0, 12.0, 2.0e3), (1.0, 60.0, 2.0e5), (0.1, 20.0, 2.0e4),
                    (1.0, 300.0, 2.0e5), (0.05, 8.5, 3.0e3)):
    params = {"laws": "pn", "m_total": 20.0, "scene": {"format": "lfscene", "version": 1, "objects": [
        {"type": "binary", "values": {"q": q, "r0": r0, "r_stop": 6.0}},
        {"type": "detector", "values": {"distance": 400.0, "iota": 30.0}}]}}
    h = Harness("p01_gravity", None, params)
    T = h.sim.mode.T
    run(h, span * T, 2000)
    rows = []
    for m in h.of("check"):
        if m["id"] != "balance":
            continue
        x = m["tol"] / 100.0  # tol = 100 x^2
        x = x ** 0.5
        rows.append((m["t"] / T, x, m["value"], m.get("ok")))
    if not rows:
        print(f"q = {q}, r0 = {r0}: no balance check emitted")
        continue
    rows = np.array([(t, x, v, 1.0 if ok else 0.0) for t, x, v, ok in rows])
    dev = (rows[:, 2] - 1.0) / rows[:, 1] ** 2
    nbad = int(np.sum(rows[:, 3] == 0.0))
    st = h.sim.mode.bin["status"]
    print(f"q = {q}, r0 = {r0}: {len(rows)} messages over t = {rows[0, 0]:.0f}..{rows[-1, 0]:.0f} m "
          f"(x = {rows[0, 1]:.4f}..{rows[-1, 1]:.4f}; status {st}); failed: {nbad}")
    idx = np.unique(np.linspace(0, len(rows) - 1, 8).astype(int))
    for i in idx:
        print(f"    t = {rows[i, 0]:9.1f}  x = {rows[i, 1]:.4f}  ratio = {rows[i, 2]:.6f}  (ratio - 1)/x^2 = {dev[i]:8.2f}"
              f"  ok = {bool(rows[i, 3])}")
    if nbad:
        i = int(np.flatnonzero(rows[:, 3] == 0.0)[0])
        print(f"    first failure: t = {rows[i, 0]:.1f}, x = {rows[i, 1]:.4f}, ratio = {rows[i, 2]:.6f}, "
              f"(ratio - 1)/x^2 = {dev[i]:.1f}")
