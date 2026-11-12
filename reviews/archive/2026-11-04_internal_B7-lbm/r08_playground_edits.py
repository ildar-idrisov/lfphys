"""R08: live edits in the playground p04 (harness): (a) editing an inlet's dye (or adding a second inlet) restarts the
ramp of every inlet: Flow2D keeps one start time for all inlets and set_sides resets it whenever any inlet is set;
(b) an obstacle's coefficient length set back to 0 ("the diameter") keeps the previous custom length
(update_obstacle reads None as "unchanged").

Run (from engine/): docker run --rm --name lf-b7rl-r08 -v $PWD:/lf:ro -v <this folder>:/out -e PYTHONDONTWRITEBYTECODE=1
-e LFPHYS_NO_GPU=1 -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server:/lf/lfphys:/lf/visualizations/tests
-w /lf/lfphys light-funnel-viz python3 /out/r08_playground_edits.py
"""
from harness import Harness

print("=== (a) karman preset: the inlet's dye changed at t = 1 s ===")
h = Harness("p04_fluids", "karman", {})
fl = h.sim.fl
h.run_to(1.0)
h.runner._frame(0.0)
inlet = [k for k, o in h.sim.objects.items() if o["type"] == "inlet"][0]
print("before the edit: t = %.4f s, inlet scale %.4f, inflow %.5g kg/(s m)" % (fl.t, fl._inlet_scale(fl.t),
                                                                              fl.flow_rates()["left"]))
vals = dict(h.sim.objects[inlet]["values"])
vals["dye"] = 0.5
h.cmd("scene", op="set", id=inlet, values=vals)
print("errors:", h.errors())
for dt in (0.0001443, 0.05, 0.25, 0.5):
    try:
        h.run_to(1.0 + dt)
    except RuntimeError as e:  # the world's blow-up guard
        print("  the world stopped:", str(e)[:330])
        break
    print("  %.4f s after the edit: inlet scale %.4f, inflow %.5g kg/(s m)" % (fl.t - 1.0, fl._inlet_scale(fl.t),
                                                                          fl.flow_rates()["left"]))
print()
print("=== (a') the same preset: a second inlet added on the top side at t = 1.5 s ===")
h = Harness("p04_fluids", "karman", {})
fl = h.sim.fl
h.run_to(1.5)
print("before: inlet scale %.4f, left inflow %.5g" % (fl._inlet_scale(fl.t), fl.flow_rates()["left"]))
h.cmd("scene", op="add", type="inlet", values={"side": "top", "speed": 0.01, "profile": "uniform", "ramp": 0.0})
h.run_to(1.5 + 0.0002)
print("just after: inlet scale %.4f, left inflow %.5g (errors %s)" % (fl._inlet_scale(fl.t), fl.flow_rates()["left"],
                                                                     h.errors()))

print()
print("=== (b) the coefficient length of a disk: 0.2 m, then back to 0 (= its diameter 0.1 m) ===")
h = Harness("p04_fluids", "cylinder_re20", {})
cyl = [k for k, o in h.sim.objects.items() if o["type"] == "disk"][0]
vals = dict(h.sim.objects[cyl]["values"])
for ref in (0.2, 0.0):
    vals["ref"] = ref
    h.cmd("scene", op="set", id=cyl, values=vals)
    oid = h.sim.ref[cyl][1]
    print("ref set to %.2f: the engine's coefficient length = %s m (errors %s)" % (
        ref, h.sim.fl.forces()[oid]["length"], h.errors()))
