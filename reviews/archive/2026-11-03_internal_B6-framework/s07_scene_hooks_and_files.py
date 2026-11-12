# Review B6-framework, script s07: the scene command's hooks and scene files (p02_quantum on a 128-point grid, the toy).
#  (a) a p02 scene file with the time it was saved at: the new world's clock starts at t, the engine's at 0, and the
#      first advance silently integrates the whole span (counted in scene steps; the original computed them in real time)
#  (b) a barrier of V = 1e308 eV: a finite value of the schema (no max), inf in the engine's units: accepted, and the
#      potential on the grid holds NaN (inf * 0 in the smooth profile)
#  (c) p02 on_set of a particle's Bohm count only: the particle's wave is replaced by its starting packet
#  (d) scene files that are not what start_scene expects: what reaches the caller
# Usage: see s01 (+ LFVIZ_EXTRA for the toy); python3 /out/s07_scene_hooks_and_files.py
import queue
import time

import numpy as np

from lfviz import registry
from lfviz.sim import Runner


def p02(msgs, values, preset="tunnel", seed=3):
    viz = registry.load("p02_quantum")
    p, errs = viz["schema"].resolve(preset, values)
    assert not errs, errs
    sim = viz["simulation"](p, seed, lambda m, b=None: msgs.append((m, b)))
    return sim, Runner(sim, lambda m, b=None: msgs.append((m, b)), queue.Queue())


def last(msgs, typ):
    return [m for m, _ in msgs if m.get("type") == typ][-1]


def play(run, n):
    for _ in range(n):
        run._advance(run.sim.t + run.speed / 20)
        run._frame(0.0)


print("=== (a) a p02 scene saved at time t, loaded as a new world ===")
msgs = []
sim, run = p02(msgs, {"n2": "128"})
run._start_world()
t0 = time.monotonic()
play(run, 300)
wall = time.monotonic() - t0
print(f"original: world t = {sim.t:.4g} s, {sim.qs.steps} scene steps computed over 300 frames ({wall:.1f} s)")
run.handle({"cmd": "scene", "args": {"op": "export"}})
sc = last(msgs, "scene_export")["scene"]
print("scene file: t =", sc["t"], " objects:", [o["type"] for o in sc["objects"]],
      " states:", [("state" in o) for o in sc["objects"]])
m2 = []
t0 = time.monotonic()
sim2, run2 = p02(m2, {**sc["laws"], "scene": sc}, preset=None)
run2._start_world()
print(f"loaded world right after its header: t = {sim2.t:.4g} s, engine steps already computed: {sim2.qs.steps} "
      f"({time.monotonic() - t0:.1f} s blocking in the header's advance)")

print("=== (b) a barrier of V = 1e308 eV (a finite value the schema accepts) ===")
msgs = []
sim, run = p02(msgs, {"n2": "128"})
run._start_world()
play(run, 5)
n_err = sum(1 for m, _ in msgs if m.get("type") == "error")
run.handle({"cmd": "scene", "args": {"op": "add", "type": "box", "values": {"V": 1e308}}})
ev = last(msgs, "event")
print("accepted:", ev.get("kind") == "scene" and "добавлен" in ev["text"], "|", ev["text"][:80],
      "| errors:", sum(1 for m, _ in msgs if m.get("type") == "error") - n_err)
pid = [q for q in sim.qs.particles][0]
V = sim.qs.potential(sim.qs.particles[pid].species)
print("potential on the grid: NaN points", int(np.isnan(V).sum()), "of", V.size, "; inf points", int(np.isinf(V).sum()))
try:
    play(run, 20)
    fr = last(msgs, "frame")
    po = [o for o in sim.objects.values() if o["type"] == "packet"][0]["id"]
    print("20 frames later: the packet's norm in the window:", fr["now"][po].get("в окне (вероятность)"))
    bal = [m for m, _ in msgs if m.get("type") == "check" and str(m.get("id", "")).startswith("balance_")]
    print("its balance check:", {k: bal[-1].get(k) for k in ("value", "ok")} if bal else "not emitted")
except Exception as e:  # noqa: BLE001
    print("the world fails:", type(e).__name__, str(e)[:200])

print("=== (c) p02: only the Bohm count of a particle changed ===")
msgs = []
sim, run = p02(msgs, {"n2": "128"})
run._start_world()
play(run, 60)
pid = [o for o in sim.objects.values() if o["type"] == "packet"][0]["id"]
x_before = last(msgs, "frame")["now"][pid]["⟨x⟩, нм"]
run.handle({"cmd": "scene", "args": {"op": "set", "id": pid, "values": {"bohm": 10}}})
run._frame(0.0)
x_after = last(msgs, "frame")["now"][pid]["⟨x⟩, нм"]
print(f"⟨x⟩ of the packet before the change {x_before:.4f} nm, right after it {x_after:.4f} nm "
      f"(the preset's packet starts at x = -20 nm)")

print("=== (d) scene files start_scene does not expect (toy section) ===")
toy = registry.load("p99_toy")
for label, scene in [("a list instead of an object", [1, 2]),
                     ("objects not objects", {"format": "lfscene", "objects": ["a"]}),
                     ("t = 'inf'", {"format": "lfscene", "t": "inf", "objects": []}),
                     ("t = 'nan'", {"format": "lfscene", "t": "nan", "objects": []}),
                     ("t = -1e300", {"format": "lfscene", "t": -1e300, "objects": []})]:
    p, errs = toy["schema"].resolve(None, {"scene": scene})
    try:
        s = toy["simulation"](p, 1, lambda m, b=None: None)
        print(f"{label}: schema errors {errs}; world built, t = {s.t}")
    except Exception as e:  # noqa: BLE001
        print(f"{label}: schema errors {errs}; world construction raises {type(e).__name__}: {e}")
