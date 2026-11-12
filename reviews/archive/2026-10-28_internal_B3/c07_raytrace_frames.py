# B3 review, check 7: lfphys.core.raytrace is frame-independent. What an observer sees is an invariant: the same
# root path updated to reviews/archive/ when the processed review was archived (responder, 2026-10-28)
# scene described in another inertial frame must give the same image. Take bodies moving collinearly along x (so that
# all boosts involved are collinear and compose without a Wigner rotation: the observer's camera axes and the bodies'
# rest-frame axes are the same in both descriptions) and an observer at rest in the lab; describe everything again in
# the rest frame of the first body (its centre's worldline, the others' velocities composed collinearly, the
# observation event transformed, the observer moving with -v1). Both descriptions are traced for the same
# observer-frame directions; body index, rest-frame point q, Doppler factor D and observed temperature D T must agree
# to round-off. This checks the aberration of the observer's pixels (boost(-u)), the bodies' world tubes (boost(v)) and
# the nearest-emission rule (occlusion between bodies of different speeds) against each other: an independent route,
# not a closed form.
# Run (from engine/):
#   docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf -e PYTHONPATH=/lf/lfphys light-funnel-viz \
#     python3 reviews/archive/2026-10-28_internal_B3/c07_raytrace_frames.py > reviews/archive/2026-10-28_internal_B3/out/c07_raytrace_frames.txt
import numpy as np

from lfphys.core import backend as B
from lfphys.core import lorentz as LZ
from lfphys.core import raytrace as RT

B.configure({"kernels": {RT.KERNEL: {"device": "cpu"}}})
EPS = np.finfo(float).eps


def compose(w, v1):
    """Velocity w (lab, along x) seen from the frame moving with v1 (along x)."""
    return (w - v1) / (1.0 - w * v1)


def to_frame(beta1, t, x):
    L = LZ.boost(np.array([beta1, 0.0, 0.0]))
    X = L @ np.r_[t, np.asarray(x, float)]
    return X[0], X[1:]


def moved(body, beta1):
    """The same body described in the frame moving with beta1 along x."""
    vx = float(body.velocity[0])
    w = compose(vx, beta1)
    tc, xc = to_frame(beta1, 0.0, body.center)          # the centre's event at lab time 0
    c_new = xc - np.array([w, 0.0, 0.0]) * tc          # where that centre is at the new frame's time 0
    kw = dict(center=tuple(c_new), velocity=(w, 0.0, 0.0))
    if body.kind == "sphere":
        return RT.Sphere(radius=body.radius, temps=body.temps, cells=body.cells, axes=body.axes, name=body.name, **kw)
    if body.kind == "box":
        return RT.Box(half=body.half, temps=body.temps, alt=body.alt, cells=body.cells, axes=body.axes, name=body.name,
                      **kw)
    return RT.Panel(u=body.u, v=body.v, half=body.half, temps=body.temps, cell=body.cell, name=body.name, **kw)


def compare(bodies, ob, cam, beta1, label):
    sc = RT.Scene(bodies)
    r = RT.render(sc, ob, cam)
    t2, x2 = to_frame(beta1, ob.t, ob.x)
    ob2 = RT.Observer(t2, tuple(x2), (-beta1, 0.0, 0.0))
    r2 = RT.render(RT.Scene([moved(b, beta1) for b in bodies]), ob2, cam)
    same_body = np.array_equal(r["body"], r2["body"])
    m = r["body"] >= 0
    dq = float(np.max(np.linalg.norm(r["q"][m] - r2["q"][m], axis=-1))) if m.any() else 0.0
    dD = float(np.max(np.abs(r2["D"][m] / r["D"][m] - 1))) if m.any() else 0.0
    # pixels whose emission point lies on a boundary of the pattern (a cell edge within 1e-9: e.g. a row of pixels
    # meeting the floor exactly at its cell edges) take either temperature by the last bit of q: left out of dT
    edge = np.zeros(r["body"].shape, bool)
    for ib, b in enumerate(bodies):
        mb = r["body"] == ib
        if not mb.any():
            continue
        q = r["q"][mb]
        T0 = RT.surface_temperature(b, q)
        e = np.zeros(len(q), bool)
        for k in range(3):
            for sgn in (-1e-9, 1e-9):
                dq_ = np.zeros(3)
                dq_[k] = sgn
                e |= RT.surface_temperature(b, q + dq_) != T0
        edge[mb] = e
    mm = m & ~edge
    dT = float(np.max(np.abs(r2["T_obs"][mm] / r["T_obs"][mm] - 1))) if mm.any() else 0.0
    nT = int((m & edge & (r2["T_rest"] != r["T_rest"])).sum())
    nb = int((r["body"] != r2["body"]).sum())
    g2 = max(float(LZ.gamma_of(np.asarray(b.velocity))) ** 2 for b in bodies) * float(LZ.gamma_of(np.array([beta1, 0, 0]))) ** 2
    print(f"{label}: pixels {r['body'].size}, seeing bodies {int(m.sum())}; body index differs in {nb} pixels; "
          f"max |q - q'| {dq:.2e}; max |D'/D - 1| {dD:.2e}; max |T'/T - 1| {dT:.2e} off the pattern's cell edges "
          f"({int((m & edge).sum())} pixels on an edge, {nT} of them coloured the other way); (eps gamma^2 = {EPS * g2:.1e})")
    if nb:
        k = np.argwhere(r["body"] != r2["body"])[:5]
        for j, i in k:
            print(f"   pixel ({j}, {i}): body {r['body'][j, i]} (s = {r['s'][j, i]:.6g}) vs {r2['body'][j, i]} "
                  f"(s' = {r2['s'][j, i]:.6g})")
    return same_body, dq, dD


cases = []
cube = RT.Box((-3.0, 0.0, 8.0), (1.0, 1.0, 1.0), (0.9, 0.0, 0.0), temps=(9500.0, 3600.0, 5000.0, 5000.0, 2600.0, 6500.0),
              alt=0.8, cells=4)
ball = RT.Sphere((-10.0, 0.5, 11.0), 1.3, (0.5, 0.0, 0.0), temps=(7000.0, 3800.0))
floor = RT.Panel((0.0, -2.0, 20.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), half=(60.0, 60.0), cell=2.0)
posts = [RT.Box((x, 0.5, 6.0), (0.12, 2.5, 0.12), temps=(6800.0,) * 6, alt=1.0, cells=1) for x in (-6.0, 0.0, 6.0)]
cam = RT.Camera(320, 240, fov=120)
for t in (0.0, 5.0, 12.0):
    ob = RT.Observer(t, (0.0, 0.0, 0.0))
    for beta1, frame in ((0.9, "the cube's frame"), (0.5, "the ball's frame"), (-0.6, "a frame moving with -0.6 c")):
        compare([cube, ball, floor] + posts, ob, cam, beta1, f"t = {t:4.1f}, fly-by bodies, {frame}")
# a fast observer-like case: everything at rest in the lab, seen from a frame moving at 0.99 c along x
city = [RT.Box((x, 0.0, z), (2.0, 3.0, 2.0), temps=(5200.0,) * 6, alt=0.7, cells=3) for x in (-6.0, 6.0) for z in (10.0, 20.0, 30.0)]
compare(city, RT.Observer(3.0, (0.0, 0.0, -5.0)), RT.Camera(256, 192, fov=150), 0.99, "towers at rest, frame at 0.99 c")
