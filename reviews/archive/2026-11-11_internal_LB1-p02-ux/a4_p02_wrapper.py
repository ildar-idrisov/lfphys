# Review LB1-p02-ux, Part A, script a4: p02's wrapper — what the owner reads after a live change, a drag, a throw,
# «Приготовить пакет заново» and a new world with the scene carried over. Driven through the test harness (no server).
# Run (from engine/): docker run --rm --name lf-lbrx-a4 --memory=8g -v $PWD:/lf:ro -v <this folder>:/out
#   -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1
#   -e PYTHONPATH=/lf/lfphys:/lf/visualizations/server:/lf/visualizations:/lf/visualizations/tests
#   -w /lf/visualizations light-funnel-viz python3 /out/a4_p02_wrapper.py
import math
import numpy as np
from harness import Harness
from p02_quantum import viz as P

V = "p02_quantum"


def run(h, t_end, n=10):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + (t_end - t0) * k / n)
        h.runner._frame(0.0)


def last_events(h, n=1):
    return [m.get("text") for m in h.of("event")][-n:]


def outer(psi):
    F = np.abs(np.fft.fftn(psi)) ** 2
    n = psi.shape[0]
    m = np.abs(np.rint(np.fft.fftfreq(n) * n))
    M = np.maximum(m[:, None], m[None, :])
    return float(F[M > n / 3].sum() / F.sum())


print("== 1. an empty plane with one free electron (lambda 2 nm, sigma 3): coarsen the grid step by step")
h = Harness(V, None, {"dim": "2d", "n2": "256", "size": 80.0, "edges": "open", "scene": {"format": "lfscene", "version": 1,
            "objects": [{"type": "packet", "label": "Электрон", "values": {"x": -10.0, "wavelength": 2.0, "sx": 3.0, "sy": 3.0}}]}})
run(h, h.sim.t + 1.0 * h.sim.default_speed, 4)
for n2 in ("192", "128"):
    ne = len(h.errors())
    h.set(n2=n2)
    print(f"  n2 -> {n2}: " + (("REFUSED: " + h.errors()[-1]) if len(h.errors()) > ne else "taken: " + last_events(h)[0]))

print("\n== 2. tunnel preset (open edges): shrink the window 80 -> 56 nm while the wave is mid-window")
h = Harness(V, "tunnel")
run(h, h.sim.t + 1.0 * h.sim.default_speed, 4)
qs = h.sim.qs
rho = qs.density()
new_w = 0.10 * 56.0
g = qs.grid
X = g.mesh()
inner = np.ones(g.shape, bool)
for a in range(2):
    inner &= (np.abs(X[a]) < 28.0 - new_w) * np.ones(g.shape, bool)
in_new_layers = float(rho[~inner & (np.abs(X[0]) < 28.0) & (np.abs(X[1]) < 28.0)].sum() / rho.sum())
ne = len(h.errors())
h.set(size=56.0)
print(f"  probability that would sit inside the NEW absorbing layers (5.6 nm per side): {in_new_layers:.3e}")
print("  " + (("REFUSED: " + h.errors()[-1]) if len(h.errors()) > ne else "taken: " + last_events(h)[0]))

print("\n== 3. Aharonov-Bohm preset: the electron dragged sideways by 4 nm after it has passed the wall")
h = Harness(V, "aharonov_bohm")
run(h, h.sim.t + 5.0 * h.sim.default_speed, 20)
qs = h.sim.qs
oid = [o for o, (k, q) in h.sim.ref.items() if k == "particle"][0]
pid = h.sim.ref[oid][1]
o = qs.observables(pid)
w0 = qs.wave(pid)
s0 = outer(w0)
r = o["r"]
h.cmd("scene", op="edit", id=oid, values={"x": r[0], "y": r[1] + 4.0})
w1 = qs.wave(pid)
o1 = qs.observables(pid)
print(f"  <r> {np.round(r, 3)} -> {np.round(o1['r'], 3)}; <k - qA> {np.round(o['k'], 5)} -> {np.round(o1['k'], 5)}; "
      f"spectrum in the outer third {s0:.2e} -> {outer(w1):.2e}")
print("  event: " + str(last_events(h, 2)))
print("  errors: " + str(h.errors()[-1:]))

print("\n== 4. the cyclotron preset: a throw; units the owner reads (throw velocity, v_max, the measured |<v>|)")
h = Harness(V, "cyclotron")
run(h, h.sim.t + 1.0 * h.sim.default_speed, 4)
oid = [o for o, (k, q) in h.sim.ref.items() if k == "particle"][0]
vals = h.sim.objects[oid]["values"]
print(f"  packet values: vx = {vals['vx']:.4g} нм/с, vy = {vals['vy']:.4g} нм/с, v_max = {vals['v_max']:.4g} нм/с")
fr = h.of("frame")[-1]
print(f"  frame 'now': скорость |⟨v⟩| = {fr['now'][oid]['скорость |⟨v⟩|, км/с']:.6g} км/с; meas v = {fr['meas'][oid + '.v']:.6g}")
r = h.sim.qs.observables(h.sim.ref[oid][1])["r"]
h.cmd("scene", op="edit", id=oid, values={"x": r[0], "y": r[1], "vx": 1.0e14, "vy": 2.0e14})
print("  throw (1e14, 2e14) nm/s: " + str(last_events(h, 2)))
run(h, h.sim.t + 0.2 * h.sim.default_speed, 2)
fr = h.of("frame")[-1]
print(f"  afterwards |⟨v⟩| = {fr['meas'][oid + '.v']:.6g} km/s (expected |(1e14, 2e14)| nm/s = {math.hypot(1e14, 2e14) * 1e-12:.6g} km/s)")

print("\n== 5. «Приготовить пакет заново» after a drag and a throw (tunnel preset)")
h = Harness(V, "tunnel")
run(h, h.sim.t + 2.0 * h.sim.default_speed, 6)
oid = [o for o, (k, q) in h.sim.ref.items() if k == "particle"][0]
pid = h.sim.ref[oid][1]
r = h.sim.qs.observables(pid)["r"]
h.cmd("scene", op="edit", id=oid, values={"x": r[0] - 15.0, "y": r[1] + 5.0, "vx": 3.0e14, "vy": 0.0})
run(h, h.sim.t + 1.0 * h.sim.default_speed, 4)
before = h.sim.qs.observables(pid)
h.action("prepare", particle=oid)
after = h.sim.qs.observables(pid)
print(f"  values now: x = {h.sim.objects[oid]['values']['x']:.4g}, y = {h.sim.objects[oid]['values']['y']:.4g}, "
      f"lambda = {h.sim.objects[oid]['values']['wavelength']:.4g}")
print(f"  <r> before {np.round(before['r'], 3)} -> after {np.round(after['r'], 3)}; <k> {np.round(before['k'], 4)} -> {np.round(after['k'], 4)}")
print("  result: " + str([m.get("text") for m in h.of("action_result")][-1:] or last_events(h, 2)))

print("\n== 6. a new world of the other dimension with the scene carried (double slit, after the electron passed the wall)")
h = Harness(V, "double_slit")
run(h, h.sim.t + 4.0 * h.sim.default_speed, 10)
oid = [o for o, (k, q) in h.sim.ref.items() if k == "particle"][0]
pre = h.sim.qs.observables(h.sim.ref[oid][1])
A = h.sim.qs.absorbed(h.sim.ref[oid][1])
print(f"  2-D before: norm {pre['norm']:.4f}, absorbed {A}, <r> {np.round(pre['r'], 2)}")
h.cmd("new_world", params={"dim": "3d"}, carry=True)
s3 = h.sim
print(f"  3-D world: n3 = {s3.params['n3']}, size = {s3.params['size']}, objects = {[o['type'] for o in s3.objects.values()]}")
print("  errors: " + str(h.errors()[-2:]))
print("  notices: " + str([n["text"] for n in h.of("notice")][-2:]))
pid3 = [q for o, (k, q) in s3.ref.items() if k == "particle"]
if pid3:
    o3 = s3.qs.observables(pid3[0])
    print(f"  3-D particle: norm {o3['norm']:.4f}, <r> {np.round(o3['r'], 2)} (a fresh packet at its values' centre)")
