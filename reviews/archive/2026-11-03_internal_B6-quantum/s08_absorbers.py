"""Q: the absorbers' strengths the wrapper chooses (_auto_W: the W0 of a log-spaced set that minimises the worst
reflection + leak at NORMAL incidence over |k|, |k| +- 2 sigma_k) and the README's numbers ("edges 4e-7 (plane) and
1.3e-4 (volume), the 3-nm-edged screen 1e-11"). Reproduced on the presets; then the same layers at oblique incidence
(k_n = k cos theta), which the running check (normal incidence at |k| only) does not show."""
import copy, math, sys
import numpy as np
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness
from lfphys.core.quantum import scene as QS, schrodinger_nd as SND
from p02_quantum import viz as P

for preset in ("double_slit", "ball_3d", "tunnel", "trap", "cyclotron"):
    pr = copy.deepcopy(P.SCHEMA.presets[preset]["params"])
    for o in pr["scene"]["objects"]:
        if o["type"] == "packet":
            o["values"]["bohm"] = 0
    h = Harness("p02_quantum", None, pr)
    sim, qs = h.sim, h.sim.qs
    waves = sim._waves()
    e = qs.edges
    worst = max(float(np.sum(SND.layer_reflection([k], e.width, e.strength, m))) for k, m in waves)
    line = f"{preset:12s}: edges W0 = {e.strength:.3g} ({e.strength * P.EV:.3g} eV), width {e.width} nm; worst R+T over " \
           f"the waves {worst:.2e}"
    for oid, (kind, qid) in sim.ref.items():
        ob = qs.objects.get(qid) if kind == "object" else None
        if isinstance(ob, QS.Detector):
            ax = sim._det_axis(ob)
            wr = max(float(np.sum(ob.reflection([k], m, axis=ax))) for k, m in waves)
            line += f"; detector W0 = {ob.strength * P.EV:.3g} eV, edge {ob.edge}, worst R+T {wr:.2e}"
    print(line)
    # oblique incidence on the edges for the packet's |k|
    k, m = max(waves, key=lambda km: km[0])[0], waves[0][1]
    k0 = float(np.linalg.norm(qs.particles[1].packet.k)) or k
    ths = [0, 30, 60, 75, 85]
    R = [float(SND.layer_reflection([k0 * math.cos(math.radians(t))], e.width, e.strength, m)[0][0]) for t in ths]
    print("     edges' R at |k| = %.3f for theta = %s deg: %s" % (k0, ths, ", ".join(f"{r:.1e}" for r in R)))
