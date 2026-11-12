"""v03: rapid successive live changes (each 'set' rebuilds the world synchronously: _build + _evolve), refused
changes, reading changes; wall time of each change (the world and the player wait for it), errors, failed checks.
Output: out/13_v03_rapid_sets.txt
"""
import sys
import time

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402

OUT = open("out/13_v03_rapid_sets.txt", "w")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.write(s + "\n")
    OUT.flush()


def bad(h, seg):
    out = []
    for c in h.checks().values():
        if not c["id"].endswith(str(seg)):
            continue
        if c.get("ok") is False or (c.get("ok") is None and c.get("rel") is not None and c.get("ref") is not None
                                    and abs(c["rel"]) > max(c.get("tol") or 1e-9, 1e-12)):
            out.append((c["id"], c["value"], c["ref"]))
    return out


h = Harness("v03_quantum_1d", "tunnel")
SEQ = [{"interp": "bohm"}, {"n_bohm": 0}, {"n_bohm": 200}, {"scenario": "oscillator"}, {"interp": "everett"},
       {"x0": 0.0}, {"hw": 0.001}, {"scenario": "double", "gap": 20.0, "width": 10.0},
       {"scenario": "free", "energy": 20.0}, {"energy": 0.05, "sigma": 15.0}, {"scenario": "step", "V0": 10.0},
       {"V0": 11.0}, {"scenario": "well", "V0": -5.0, "edge": 0.02, "energy": 20.0},
       {"scenario": "barrier", "V0": 10.0, "width": 10.0, "edge": 2.0, "energy": 0.05, "sigma": 1.0}]
for vals in SEQ:
    t0 = time.time()
    n_err = len(h.errors())
    try:
        h.set(**vals)
        res = "applied" if len(h.errors()) == n_err else "refused: " + h.errors()[-1][:100]
    except Exception as e:  # noqa: BLE001
        res = f"UNCAUGHT {type(e).__name__}: {e}"
    seg = h.sim.seg
    h.run_to(h.sim.t + 2 * h.sim.cycle * 1e-15)
    say(f"set {vals}: {res}; {time.time() - t0:.1f} s; n_grid {h.sim.n_grid}; failed checks of segment {seg}: "
        f"{bad(h, seg)}")
