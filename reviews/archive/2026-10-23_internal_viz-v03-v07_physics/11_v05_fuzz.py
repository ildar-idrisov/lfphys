"""v05: random live changes over the allowed ranges (incl. the range ends), several per world-step, with the photon
stream running. After every change: uncaught exceptions, non-finite numbers in the segment blobs, failed checks (the
player's rule), and the photon bookkeeping  emitted = R + T + A + lost + in flight  (all-time totals).
Output: out/11_v05_fuzz.txt
"""
import math
import sys
import traceback
from collections import Counter

import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402
from v05_optics_bench.viz import SCHEMA  # noqa: E402

OUT = open("out/11_v05_fuzz.txt", "w")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.write(s + "\n")
    OUT.flush()


def failed_ids(h, seg):
    out = []
    for c in h.checks().values():
        if not c["id"].endswith(str(seg)) or not c["id"][:-len(str(seg))].isalpha():
            continue
        if c.get("ok") is False:
            out.append(c["id"][:-len(str(seg))])
        elif c.get("ok") is None and c.get("rel") is not None and c.get("ref") is not None \
                and abs(c["rel"]) > max(c.get("tol") or 1e-9, 1e-12):
            out.append(c["id"][:-len(str(seg))])
    return out


rng = np.random.default_rng(7)
live = [p for p in SCHEMA.params if p.live]


def random_value(p):
    if p.type == "select":
        return p.options[int(rng.integers(len(p.options)))][0]
    lo, hi = p.min, p.max
    u = rng.random()
    if u < 0.15:
        return lo
    if u < 0.3:
        return hi
    if p.type == "int":
        return int(rng.integers(int(lo), int(hi) + 1))
    if p.log and lo > 0:
        return float(math.exp(rng.uniform(math.log(lo), math.log(hi))))
    return float(rng.uniform(lo, hi))


fail_count = Counter()
examples = {}
n_changes = 0
exceptions = []
book_bad = []
nonfinite = []
for world in range(12):
    h = Harness("v05_optics_bench", list(SCHEMA.presets)[world % len(SCHEMA.presets)], seed=world)
    h.cmd("speed", value=h.sim.times["t_in"] / 4)
    for step in range(25):
        vals = {}
        for p in rng.choice(live, size=int(rng.integers(1, 4)), replace=False):
            if p.id == "rate":
                vals[p.id] = float(10 ** rng.uniform(6, 10))  # keep the run cheap
            else:
                vals[p.id] = random_value(p)
        n_seg = len(h.of("segment"))
        try:
            h.set(**vals)
        except Exception as e:  # noqa: BLE001
            exceptions.append((vals, f"{type(e).__name__}: {e}"))
            break
        n_changes += 1
        if len(h.of("segment")) > n_seg:
            seg_msgs = [(m, b) for m, b in h.msgs if m.get("type") == "segment"]
            m, b = seg_msgs[-1]
            for k, v in b.items():
                if not np.all(np.isfinite(v)):
                    nonfinite.append((dict(h.sim.params), k))
            for fid in failed_ids(h, m["seg"]):
                fail_count[fid] += 1
                examples.setdefault(fid, {k: h.sim.params[k] for k in SCHEMA.live_ids()})
        try:
            h.run_to(h.sim.t + float(rng.uniform(0.2, 3.0)) * h.sim.times["t_in"])
        except Exception as e:  # noqa: BLE001
            exceptions.append(("advance after " + str(vals), f"{type(e).__name__}: {e}"))
            break
        tt = h.sim.tot
        if tt["emitted"] != tt["R"] + tt["T"] + tt["A"] + tt["lost"] + len(h.sim.flight):
            book_bad.append((dict(tt), len(h.sim.flight)))

say(f"live changes applied: {n_changes}")
say(f"uncaught exceptions: {len(exceptions)}")
for v, e in exceptions[:10]:
    say(f"   {v} -> {e}")
say(f"bookkeeping violations: {len(book_bad)} {book_bad[:3]}")
say(f"non-finite blobs: {len(nonfinite)} {nonfinite[:3]}")
say("failed checks by kind (count over all new segments) and one example set-up:")
for k, n in fail_count.most_common():
    say(f"   {k}: {n}   e.g. {examples[k]}")
