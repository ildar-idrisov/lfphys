# B3 review, check 13: the round-off tolerances of v10's checks (README "Checks"; viz.py _image_checks) against what
# root path updated to reviews/archive/ when the processed review was archived (responder, 2026-10-28)
# correct computations give. In the browser (c09) the "sky" preset with seed 5 showed the check `stars` FAILED:
# 1.94e-14 rad against 16 eps gamma^2 = 1.87e-14. Here:
#  (a) lfphys.core.raytrace.star_images against ref_aberration for 20 000 random stars at several beta and directions
#      of the observer's velocity: the largest angle in units of eps gamma^2 (the checks allow 16);
#  (b) v10's "sky" preset over seeds 1..12 (the stars are drawn from the world's seed): which seeds show `stars` or
#      `sky_T` failed at the start, and the values;
#  (c) the sky's temperature (`sky_T`, tolerance 16 eps gamma^2) over a whole-sky camera at several beta.
# Run (from engine/):
#   docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf \
#     -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server:/lf/visualizations/tests \
#     light-funnel-viz python3 reviews/archive/2026-10-28_internal_B3/c13_v10_roundoff_tolerances.py > reviews/archive/2026-10-28_internal_B3/out/c13_v10_roundoff_tolerances.txt
import numpy as np
from harness import Harness

from lfphys.core import backend as B
from lfphys.core import lorentz as LZ
from lfphys.core import raytrace as RT

B.configure({"kernels": {RT.KERNEL: {"device": "cpu"}}})
EPS = np.finfo(float).eps


def ang(a, b):
    return np.arctan2(np.linalg.norm(np.cross(a, b), axis=-1), np.sum(a * b, -1))


print("(a) star_images vs ref_aberration, 20 000 random stars, largest angle / (eps gamma^2)")
rng = np.random.default_rng(2026)
s = rng.normal(size=(20000, 3))
s /= np.linalg.norm(s, axis=1, keepdims=True)
for beta in (0.3, 0.5, 0.9, 0.95, 0.99):
    worst = []
    for k in range(5):
        e = rng.normal(size=3)
        e /= np.linalg.norm(e)
        u = beta * e
        st = RT.star_images(RT.Scene([], stars=[(tuple(x), 5000.0) for x in s]), RT.Observer(0.0, (0, 0, 0), tuple(u)))
        a = ang(st["d"], RT.ref_aberration(s, u))
        g2 = float(LZ.gamma_of(u)) ** 2
        worst.append(a.max() / (EPS * g2))
    print(f"  beta = {beta}: max angle / (eps gamma^2) over 5 directions of u: " + ", ".join(f"{w:.1f}" for w in worst)
          + f"  (tolerance 16; with 300 stars the chance per world that one exceeds it is what (b) shows)")

print("\n(b) v10 'sky' preset (beta 0.9, 300 stars, whole-sky camera) at its start, seeds 1..12")
for seed in range(1, 13):
    h = Harness("v10_fast_observer", "sky", seed=seed)
    c = h.checks()
    row = []
    for cid in ("stars", "sky_T", "energy"):
        if cid in c:
            m = c[cid]
            ok = m.get("ok")
            if ok is None and m.get("rel") is not None:
                ok = abs(m["rel"]) <= m["tol"]
            row.append(f"{cid} {m['value']:.3g} (tol {m['tol']:.3g}) {'ok' if ok else 'FAILED'}")
    print(f"  seed {seed:2d}: " + "; ".join(row))

print("\n(c) the sky's temperature over a whole-sky camera 384 x 192, relative error / (eps gamma^2)")
cam = RT.Camera(384, 192, kind="sky", forward=(0.3, 0.2, 1.0))
for beta in (0.3, 0.9, 0.99):
    vals = []
    for k in range(4):
        e = rng.normal(size=3)
        e /= np.linalg.norm(e)
        u = beta * e
        r = RT.render(RT.Scene([], sky=4000.0), RT.Observer(0.0, (0, 0, 0), tuple(u)), cam)
        ref = RT.ref_sky_temperature(4000.0, u, cam.directions())
        vals.append(np.max(np.abs(r["T_obs"] / ref - 1)) / (EPS * float(LZ.gamma_of(u)) ** 2))
    print(f"  beta = {beta}: " + ", ".join(f"{v:.1f}" for v in vals) + "  (tolerance 16)")
