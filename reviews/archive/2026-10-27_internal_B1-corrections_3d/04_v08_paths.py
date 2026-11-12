# Review of the B1 corrections (reviewer's script). v08's slice planes through the runner (the test harness of
# visualizations/tests, the same Runner the server uses; CPU): fixed by default on every path, "auto" (motion along
# the normal, wrap, clipping of the origin), at most three planes, removal, the preview op, the reduced model only on
# y = c and flagged, origins outside the box, the record's growth with "auto".
import argparse
import math
import sys
import time

import numpy as np

sys.path.insert(0, "/lf/lfphys")
sys.path.insert(0, "/lf/visualizations/tests")
from common_rev import Tee  # noqa: E402
from harness import Harness  # noqa: E402
from lfphys.core import backend  # noqa: E402
from lfviz import protocol  # noqa: E402

argparse.ArgumentParser(description=__doc__).parse_args()
out = Tee("out/04_v08_paths.txt")
backend.configure({"kernels": {"optics.angular_spectrum": {"device": "cpu"}}})
V = "v08_wave_3d"
SMALL = {"n": 128, "zmax": 10.0}


def planes(h):
    return {p["id"]: p for p in h.of("planes")[-1]["planes"]}


def nbytes(h, typ):
    return sum(len(protocol.encode(m, b)) for m, b in h.msgs if m.get("type") == typ)


out("(1) fixed by default: play, step, next_event, new world")
h = Harness(V, "double", SMALL)
p0 = planes(h)
ns0 = len(h.of("slice"))
h.cmd("play")
h.run_to(30.0)
h.cmd("step", dt=5.0)
h.cmd("next_event")
out(f"   after play to t = 30, step 5, next_event: planes unchanged {planes(h) == p0}; new slice messages "
    f"{len(h.of('slice')) - ns0}; auto flags {[p['auto'] for p in planes(h).values()]}")
h.cmd("view", op="plane", id=2, normal=[1, 0, 0])
h.cmd("new_world", preset="circle", params={"n": 128, "zmax": 10.0})
out(f"   new world: planes {sorted(planes(h))} (plane 2 of the previous world not carried over); "
    f"origin of 1 {planes(h)[1]['origin']}, normal {planes(h)[1]['normal']}")

out("(2) auto: a plane along y (the test's case) and a tilted one; distance d = o.n against speed x time")
for nrm in ([0.0, -1.0, 0.0], [1.0, 0.0, 0.2], [0.6, 0.0, 0.8]):
    h = Harness(V, "double", SMALL)
    nn = np.asarray(nrm) / np.linalg.norm(nrm)
    h.cmd("view", op="plane", id=1, normal=nrm, origin=[0.0, 0.0, 5.0], auto=True, speed=1.0)
    lo, hi = np.asarray(h.sim.box[0]), np.asarray(h.sim.box[1])
    corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    dmin, dmax = float((corners @ nn).min()), float((corners @ nn).max())
    track = []
    t = 0.0
    errs = 0
    for step in range(120):
        t += 0.5
        n_err = len(h.errors())
        h.run_to(t)
        errs += len(h.errors()) - n_err
        pl = planes(h)[1]
        track.append((t, float(np.asarray(pl["origin"]) @ np.asarray(pl["normal"]))))
    d = np.array(track)
    jumps = np.diff(d[:, 1])
    wraps = int(np.sum(jumps < -0.5 * (dmax - dmin)))
    fwd = jumps[jumps > -0.5 * (dmax - dmin)]
    out(f"   normal {nrm}: d range of the box [{dmin:.2f}, {dmax:.2f}] (span {dmax - dmin:.2f}); over t = 0..60 "
        f"(speed 1): wraps {wraps}, expected ~{60 / (dmax - dmin):.1f}; mean advance per 0.5 s {np.mean(fwd):.3f} "
        f"(expected 0.5), min {np.min(fwd):.3f}, slices sent {len(h.of('slice'))}, errors {errs}")
    out(f"      d(t) samples: {[round(v, 2) for v in d[::10, 1]]}")
    if nrm == [0.0, -1.0, 0.0]:
        sl_bytes = nbytes(h, "slice")
        out(f"      record: {len(h.of('slice'))} slice messages, {sl_bytes / 1e6:.1f} MB in 60 s of world time at n = 128 "
            f"-> {sl_bytes / 1e6 * 60:.0f} MB per hour at speed 1")

out("(2b) the same at the default grid n = 256 (bytes per slice message)")
h = Harness(V, "double", {"zmax": 10.0})
sl = [(m, b) for m, b in h.msgs if m.get("type") == "slice"][-1]
out(f"   one slice message: {len(protocol.encode(*sl)) / 1e6:.2f} MB (I and phase, {sl[0]['shape']})")

out("(3) at most three planes, ids, removal")
h = Harness(V, "double", SMALL)
for pid, nrm in ((2, [1, 0, 0]), (3, [0, 0, 1])):
    h.cmd("view", op="plane", id=pid, normal=nrm)
n_err = len(h.errors())
for bad in ({"id": 4, "normal": [1, 0, 0]}, {"id": 0}, {"id": 2, "normal": [0, 0, 0]}, {"id": 2, "origin": "x"},
            {"id": 2, "normal": [float("nan"), 0, 1]}):
    h.cmd("view", op="plane", **bad)
out(f"   ids {sorted(planes(h))}; five bad requests -> {len(h.errors()) - n_err} errors: "
    f"{[e[:60] for e in h.errors()[n_err:]]}")
h.cmd("view", op="remove", id=2)
h.cmd("view", op="plane", id=2)
out(f"   remove 2, add 2 again (no normal given): ids {sorted(planes(h))}, normal of 2 {planes(h)[2]['normal']}")

out("(4) preview: nothing changes but the record")
h = Harness(V, "double_slices", SMALL)
before = (dict(h.sim.planes), {k: v["U"].copy() for k, v in h.sim.slices.items()}, dict(h.checks()),
          backend.used().get("optics.angular_spectrum", {}).get("drawn"))
nmsg = len(h.msgs)
h.cmd("view", op="preview", id=1, origin=[0.0, 1.0, 5.0], normal=[0.3, -1.0, 0.2])
after_used = backend.used().get("optics.angular_spectrum", {}).get("drawn")
same = (h.sim.planes == before[0] and all(np.array_equal(h.sim.slices[k]["U"], before[1][k], equal_nan=True)
                                          for k in before[1]) and h.checks() == before[2])
out(f"   planes, slices, checks unchanged: {same}; messages added to the record: {len(h.msgs) - nmsg} "
    f"({[m.get('type') for m, _ in h.msgs[nmsg:]]}); backend 'drawn' record before {before[3]} after {after_used}")

out("(5) the reduced model: which planes, flags")
h = Harness(V, "double_slices", SMALL)
res = {}
for nrm in ([0, -1, 0], [0, 1, 0], [0, -1, 1e-6], [0, -1, 0.05], [1, 0, 0]):
    h.cmd("view", op="plane", id=2, normal=nrm, origin=[0.0, 1.0, 5.0])
    s = h.of("slice")[-1]
    res[str(nrm)] = (s["route"], s["approximation"], s["label"])
out(f"   {res}")
m = h.of("modelling")[-1]
out(f"   modelling message: approximations {m['approximations']}; header approximations {h.of('header')[0]['approximations']}")

out("(6) origin outside the box: the plane asked for vs the plane computed")
h = Harness(V, "double", SMALL)
nrm = np.array([1.0, 0.0, 1.0]) / math.sqrt(2)
o_req = np.array([12.0, 0.0, 5.0])  # outside x (box half-width 8): the plane o.n = 12 cuts the box
box = h.sim.box
lo, hi = np.asarray(box[0]), np.asarray(box[1])
corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
h.cmd("view", op="plane", id=1, normal=nrm.tolist(), origin=o_req.tolist())
pl = planes(h)[1]
out(f"   box x in [{lo[0]:.2f}, {hi[0]:.2f}], d of the box [{(corners @ nrm).min():.2f}, {(corners @ nrm).max():.2f}]; "
    f"asked d = o.n = {o_req @ nrm:.3f}; computed d = {np.asarray(pl['origin']) @ np.asarray(pl['normal']):.3f} "
    f"(origin clipped to {pl['origin']})")

out("(7) the check of a slice: one id for all planes")
h = Harness(V, "double", SMALL)
h.cmd("view", op="plane", id=2, normal=[0.4, 0.3, 0.86], origin=[0.3, -0.4, 4.0])
c2 = h.checks().get("plane_exact", {}).get("label")
h.cmd("view", op="plane", id=3, normal=[0, 0, 1], origin=[0, 0, 6.0])
c3 = h.checks().get("plane_exact", {}).get("label")
h.cmd("view", op="remove", id=3)
c4 = h.checks().get("plane_exact", {}).get("label")
out(f"   after plane 2: {c2!r}; after plane 3: {c3!r}; after removing 3: {c4!r}")

out("(8) timing of one auto step (CPU, n = 256, double, tilted plane)")
h = Harness(V, "double", {"zmax": 30.0})
t0 = time.time()
h.cmd("view", op="plane", id=2, normal=[0.4, 0.3, 0.86], origin=[0.3, -0.4, 15.0], auto=True, speed=5.0)
t1 = time.time()
h.run_to(1.0)
out(f"   placing a tilted plane (window for its azimuth measured): {t1 - t0:.1f} s; one auto step: {time.time() - t1:.1f} s")
out("done")
