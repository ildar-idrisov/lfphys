"""Q: the 3-D preset "ball_3d" (40 nm window, 64^3, open edges 4 nm thick): the running check reports the edges'
reflection at normal incidence for the packet's |k| (1.3e-4). The wave scattered by the ball meets the faces at all
angles and with all speeds. Independent route: the same scene in a larger window (60 nm, 96^3: the same grid step,
the faces 10 nm further out, the wrapper's own edge layers 6 nm), compared inside |x|, |y|, |z| < 14 nm (well inside
both windows' layers): the probability there and the density difference at late times, when what is left inside is
mostly what came back from the faces."""
import copy, math, sys
import numpy as np
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness
from p02_quantum import viz as P

out = {}
for size, n in ((40.0, "64"), (60.0, "96")):
    pr = copy.deepcopy(P.SCHEMA.presets["ball_3d"]["params"])
    pr["size"], pr["n3"] = size, n
    for o in pr["scene"]["objects"]:
        if o["type"] == "packet":
            o["values"]["bohm"] = 0
    h = Harness("p02_quantum", None, pr)
    sim, qs = h.sim, h.sim.qs
    g = qs.grid
    X = np.meshgrid(*g.axes, indexing="ij")
    inner = (np.abs(X[0]) < 14) & (np.abs(X[1]) < 14) & (np.abs(X[2]) < 14)
    rows = []
    for T in (6.0, 10.0, 14.0, 18.0, 22.0):
        while qs.t < T - 1e-9:
            qs.advance(min(64, int(round((T - qs.t) / qs.dt))))
        rho = qs.density(1)
        rows.append((T, float(np.sum(rho[inner])) * g.dV, rho[inner]))
    out[size] = rows
    print(f"window {size} nm, {n}^3 (d = {g.d[0]}), dt {qs.dt}, edges W0 {qs.edges.strength * P.EV:.3g} eV width "
          f"{qs.edges.width}: R(normal, |k|) = {float(qs.edge_reflection([2 * math.pi / 3.0], 1.0)[0][0]):.1e}")
for (T, p40, r40), (_, p60, r60) in zip(out[40.0], out[60.0]):
    print(f"t = {T:5.1f}: probability inside |x_i| < 14 nm: window 40: {p40:.3e}, window 60: {p60:.3e}; "
          f"difference {p40 - p60:+.2e}")
