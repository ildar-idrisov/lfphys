"""Q: a live change of a magnetic field while a charged packet flies (the playground's normal use: the inspector
changes Bz at the current moment). The scene keeps psi, so the kinetic momentum jumps by -q Delta A(r) of the scene's
Landau gauge — which depends on the gauge's reference (the region's lo edge, or the centre (0, 0) for a field over the
whole window), not on anything physical in the scene. Two physically identical set-ups inside the window: the
cyclotron preset (Bz = 100 T over the whole window: A_y = B x) and the same field as a region box of 76 x 76 nm
centred at 0 (A_y = B (x + 38) inside), both electrons on the same orbit; at t ~ T/4 the inspector sets Bz = 50 T.
Before the change the two runs agree (gauge invariance); after it they differ by the kick q Delta B * 38 nm."""
import copy, math, sys
import numpy as np
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness
from p02_quantum import viz as P

runs = {}
for name, vals in (("whole window", {"Bz": 100.0, "region": "all"}),
                   ("region box 76 nm", {"Bz": 100.0, "region": "box", "x": 0.0, "y": 0.0, "sx": 76.0, "sy": 76.0,
                                         "edge": 1.0})):
    pr = copy.deepcopy(P.SCHEMA.presets["cyclotron"]["params"])
    for o in pr["scene"]["objects"]:
        if o["type"] == "bfield":
            o["values"] = {**o["values"], **vals}
        if o["type"] == "packet":
            o["values"]["bohm"] = 0
    h = Harness("p02_quantum", None, pr)
    sim, qs = h.sim, h.sim.qs
    wc = 100.0 / P.TESLA
    T = 2 * math.pi / wc
    out = []
    for t_end, change in ((0.25 * T, True), (0.5 * T, False)):
        t = h.sim.t
        while qs.t < t_end - qs.dt:
            t += sim.max_step()
            h.run_to(min(t, t_end * P.TU))
        rho = qs.density(1)
        g = qs.grid
        X, Y = g.mesh()
        m = [float(np.sum(X * rho) * g.dV), float(np.sum(Y * rho) * g.dV)]
        out.append((qs.t, m))
        if change:
            fid = [o for o, (k, q) in sim.ref.items() if sim.objects[o]["type"] == "bfield"][0]
            h.cmd("scene", op="set", id=fid, values={"Bz": 50.0})
    runs[name] = out
    print(f"{name}: errors {h.errors()}; <r> at the change (t = {out[0][0]:.2f}): ({out[0][1][0]:.3f}, "
          f"{out[0][1][1]:.3f}); <r> at t = {out[1][0]:.2f}: ({out[1][1][0]:.3f}, {out[1][1][1]:.3f})")
a, b = runs["whole window"], runs["region box 76 nm"]
print(f"before the change the runs differ by {math.dist(a[0][1], b[0][1]):.2e} nm; after it by "
      f"{math.dist(a[1][1], b[1][1]):.2f} nm (kick difference q dB x 38 nm = {50 / P.TESLA * 38:.2f}/nm vs k = "
      f"{2 * math.pi / 4:.2f}/nm)")
