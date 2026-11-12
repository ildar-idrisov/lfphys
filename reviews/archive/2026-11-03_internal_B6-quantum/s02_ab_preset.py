"""Q: the preset "aharonov_bohm" ("трубка потока h/2e между щелями сдвигает полосы на половину"). Is the flux where the
wave does not go (the condition of the Aharonov-Bohm effect), and does the screen show the ideal AB pattern?

Runs of the wrapper (Harness, the preset's own objects) to t = 40 units: (a) the preset as it is (tube at (4, 0) nm,
R = 1 nm, half a flux quantum); (b) no tube; (c), (d) one slit only (n_slits = 1, offset +-5), no tube. The screen's
absorbed record per y (sum over x of acc * W_screen / W_total) is the fringe pattern. The ideal AB pattern for a
phase pi between the paths is 2 (S1 + S2) - P0 (the cross term reversed; S_j the single-slit patterns). Also the
time-integrated probability inside the tube (r < R, r < 2R) and the field the wave feels, int int B |psi|^2."""
import copy, json, math, sys
import numpy as np
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness
from lfphys.core import backend
from p02_quantum import viz as P

base = copy.deepcopy(P.SCHEMA.presets["aharonov_bohm"]["params"])
T_END = 40.0  # units of scene time


def variant(tube=True, n_slits=2, offset=0.0):
    pr = copy.deepcopy(base)
    objs = []
    for o in pr["scene"]["objects"]:
        if o["type"] == "flux" and not tube:
            continue
        if o["type"] == "slit_wall":
            o["values"]["n_slits"] = n_slits
            o["values"]["offset"] = offset
        objs.append(o)
    pr["scene"]["objects"] = objs
    return pr


def run(pr, label):
    h = Harness("p02_quantum", None, pr)
    sim = h.sim
    qs = sim.qs
    g = qs.grid
    X, Y = np.meshgrid(*g.axes, indexing="ij")
    r2 = (X - 4.0) ** 2 + (Y - 0.0) ** 2
    disk1, disk2 = r2 < 1.0, r2 < 4.0
    Bprof = np.exp(-r2 / 1.0)  # the tube's field profile / (Phi / (pi R^2)), R = 1
    in1 = in2 = fb = 0.0
    det = [qid for oid, (k, qid) in sim.ref.items() if k == "object" and
           sim.objects[oid]["type"] == "detector"][0]
    t = 0.0
    step = sim.max_step()
    while qs.t < T_END - 1e-9:
        t = min(t + step, T_END * P.TU)
        h.run_to(t)
        rho = qs.density(1)
        dtu = step / P.TU
        in1 += float(np.sum(rho[disk1])) * g.dV * dtu
        in2 += float(np.sum(rho[disk2])) * g.dV * dtu
        fb += float(np.sum(rho * Bprof)) * g.dV * dtu / math.pi  # int int (B / Phi) |psi|^2  (B/Phi = e^-r^2/pi)
    p = qs.particles[1]
    acc = backend.to_numpy(p.acc)
    u = qs._arr["u"][f"detector {det}"]
    prof = np.sum(acc * u, axis=0) * g.dV  # per y-sample
    ab = qs.absorbed(1)
    print(f"{label}: t = {qs.t:.2f}, dt = {qs.dt}, absorbed {json.dumps({k: round(v, 5) for k, v in ab.items()})}, "
          f"norm {qs.norm(1):.2e}, events after start: {[e['what'] for e in qs.events][-3:]}")
    print(f"   time-integrated probability in the tube r<R: {in1:.4f}, r<2R: {in2:.4f} (units of time); "
          f"int int (B/Phi)|psi|^2 = {fb:.4f}")
    return g.axes[1], prof


y, P_ab = run(variant(True), "(a) preset: tube at (4, 0), half quantum")
_, P0 = run(variant(False), "(b) no tube")
_, S1 = run(variant(False, 1, +5.0), "(c) slit +5 only")
_, S2 = run(variant(False, 1, -5.0), "(d) slit -5 only")
ideal = 2 * (S1 + S2) - P0
pk = float(np.max(P0))
sel = np.abs(y) < 20
print("\ny (nm)  P0       ideal-AB  preset-run   (screen's absorbed probability per y-sample, /peak of P0)")
for yy in np.arange(-12, 12.01, 1.0):
    i = int(np.argmin(np.abs(y - yy)))
    print(f"{y[i]:7.2f} {P0[i] / pk:8.4f} {ideal[i] / pk:9.4f} {P_ab[i] / pk:10.4f}")
dev = np.max(np.abs(P_ab - ideal)[sel]) / np.max(ideal[sel])
print(f"\nmax |preset - ideal| over |y| < 20, relative to the ideal's peak: {dev:.3f}")
print(f"P0 at y=0 / peak: {P0[np.argmin(np.abs(y))] / pk:.3f}; ideal at y=0 / its peak: "
      f"{ideal[np.argmin(np.abs(y))] / np.max(ideal[sel]):.3f}; preset at y=0 / its peak: "
      f"{P_ab[np.argmin(np.abs(y))] / np.max(P_ab[sel]):.3f}")
np.savez("/out/s02_ab_profiles.npz", y=y, P_ab=P_ab, P0=P0, S1=S1, S2=S2)
