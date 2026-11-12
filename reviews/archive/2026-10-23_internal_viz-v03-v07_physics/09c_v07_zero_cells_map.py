"""v07: map of the settings with an exactly-zero joint Born probability (photons: a - b = 0 or 90 deg mod 180; spins:
a - b = 0 or 180 deg mod 360) at which the engine's round-off is negative, so that numpy's Generator.choice raises in
qubits.sample_pairs and the run's advance fails. Integer and half-integer degrees in [0, 360), and the run itself for
a few of them (fixed settings, so that the failing cell is the one sampled).
Output: out/09c_v07_zero_cells_map.txt
"""
import sys

import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402
from lfphys.core.quantum import qubits as Q  # noqa: E402
from v07_bell_test.engine.experiment import Law  # noqa: E402

OUT = open("out/09c_v07_zero_cells_map.txt", "w")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.write(s + "\n")
    OUT.flush()


for pair, offs in (("photon", (0.0, 90.0)), ("spin", (0.0, 180.0))):
    law = Law(pair, "quantum")
    for off in offs:
        bad = []
        grid = np.arange(0, 360, 0.5)
        for a in grid:
            b = float(a + off)
            P = Q.joint_probabilities(law.state, law.projectors(float(a)), law.projectors(b))
            if P.min() < 0:
                bad.append(float(a))
        integers = [x for x in bad if x == int(x)]
        say(f"{pair}, b = a + {off:g}: {len(bad)} of {len(grid)} half-degree settings give a negative cell; "
            f"integer a among them: {len(integers)}, e.g. {integers[:15]}")
for pair, a, b in (("photon", 30.0, 30.0), ("photon", 10.0, 100.0), ("spin", 30.0, 30.0), ("spin", 50.0, 230.0)):
    law = Law(pair, "quantum")
    P = Q.joint_probabilities(law.state, law.projectors(a), law.projectors(b))
    h = Harness("v07_bell_test", "scan" if pair == "photon" else "spin_chsh", {"switch": "fixed", "a_deg": a, "b_deg": b})
    try:
        h.run_to(5 * h.sim._flight())
        res = f"ok, detected {h.sim.counts['detected']}"
    except Exception as e:  # noqa: BLE001
        res = f"advance RAISES {type(e).__name__}: {e}"
    say(f"run {pair} fixed a = {a:g}, b = {b:g}: min P = {P.min():.2e} -> {res}")
