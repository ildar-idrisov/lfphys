import math, numpy as np
from harness import Harness
V = "p02_quantum"
def run(h, t_end, n=10):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + (t_end - t0) * k / n); h.runner._frame(0.0)
ev = lambda h, n=2: [m.get("text") for m in h.of("event")][-n:]
print("== AB preset drag after the wall (Q1)")
h = Harness(V, "aharonov_bohm"); run(h, h.sim.t + 5.0 * h.sim.default_speed, 20)
oid = "o4"; pid = h.sim.ref[oid][1]; r = h.sim.qs.observables(pid)["r"]; w0 = h.sim.qs.wave(pid).copy()
h.cmd("scene", op="edit", id=oid, values={"x": r[0], "y": r[1] + 4.0})
print(" errors:", h.errors()[-1:]); print(" unchanged:", np.array_equal(w0, h.sim.qs.wave(pid)))
h.cmd("scene", op="edit", id=oid, values={"x": r[0] - 6.0, "y": r[1]})
ne = len(h.errors()); h.cmd("scene", op="edit", id=oid, values={"x": 15.0, "y": 0.0})
print(" move across the wall:", h.errors()[ne:], ev(h, 1))
print("== measure() is a dict (Q3):", type(h.sim.measure()).__name__)
print("== throw clamp (Q5) double slit after the wall")
h = Harness(V, "double_slit"); run(h, h.sim.t + 4.5 * h.sim.default_speed, 15)
r = h.sim.qs.observables(1)["r"]; vm = h.sim.objects["o4"]["values"]["v_max"]; print(" v_max", vm)
h.cmd("scene", op="edit", id="o4", values={"x": r[0], "y": r[1], "vx": 0.999 * vm, "vy": 0.0})
print(" clamp-at-vmax:", h.errors()[-1:], ev(h, 1))
h.cmd("scene", op="edit", id="o4", values={"x": r[0], "y": r[1], "vx": 5e14, "vy": 1e14})
print(" big throw:", h.errors()[-1:], ev(h, 1))
h.cmd("scene", op="set", id="o4", values={"vx": 3e15})
print(" typed:", h.errors()[-1:])
print("== carry 2d->3d")
pr = {"dim": "2d", "n2": "128", "size": 40.0, "edges": "open", "scene": {"format": "lfscene", "version": 1, "objects": [
    {"type": "slit_wall", "label": "Стенка", "values": {"position": 0.0, "thickness": 3.0, "V": 3.0, "n_slits": 2, "width": 2.0, "spacing": 8.0}},
    {"type": "flux", "label": "Трубка", "values": {"x": 0.0, "y": 0.0, "flux": 0.5, "radius": 1.0}},
    {"type": "plane", "label": "Поток", "values": {"position": 8.0}},
    {"type": "detector", "label": "Экран", "values": {"x": 15.0, "sx": 3.0, "edge": 3.0}},
    {"type": "packet", "label": "Электрон", "values": {"x": -5.0, "wavelength": 4.0, "sx": 1.5, "sy": 1.5}}]}}
h = Harness(V, None, pr); run(h, h.sim.t + 1.0 * h.sim.default_speed, 3)
h.cmd("new_world", params={"dim": "3d", "n3": "96", "size": 40.0}, carry=True)
print(" errors:", h.errors()[-2:]); print(" objects:", [o["type"] for o in h.sim.objects.values()])
print(" notices:", [n["text"] for n in h.of("notice")][-2:])
print("== carry 2d->2d keeps the wave")
h = Harness(V, "tunnel"); run(h, h.sim.t + 2.0 * h.sim.default_speed, 6)
w = h.sim.qs.wave(1).copy(); A = h.sim.qs.absorbed(1)
h.cmd("new_world", params={"dim": "2d", "n2": "384", "size": 80.0}, carry=True)
print(" errors:", h.errors()[-2:]); s2 = h.sim
pid = [q for k, q in s2.ref.values() if k == "particle"][0]
print(" norm", s2.qs.norm(pid), "absorbed", s2.qs.absorbed(pid), "old absorbed", A)
print(" notices:", [n["text"] for n in h.of("notice")][-1:])
run(h, h.sim.t + 1.0 * h.sim.default_speed, 4); print(" failed checks", [c["id"] for c in h.checks().values() if c.get("ok") is False])

print("== prepare where now; coarsen")
h = Harness(V, "double_slit"); run(h, h.sim.t + 1.0 * h.sim.default_speed, 4)
h.action("prepare", particle="o4", where="now"); print(" ", [m.get("text") for m in h.of("event")][-1:], h.errors()[-1:])
ne = len(h.errors()); h.set(n2="192"); print(" n2 192:", h.errors()[ne:])
h.action("coarsen", n="192"); print(" coarsen:", h.errors()[ne+1:], [m.get("text") for m in h.of("event")][-1:], h.of("live")[-1]["values"])
run(h, h.sim.t + 1.0 * h.sim.default_speed, 4); print(" failed checks", [c["id"] for c in h.checks().values() if c.get("ok") is False])
