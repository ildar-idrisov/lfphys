# B3 review, check 17 (follows check 13): which side of v10's `stars` check carries the round-off that exceeds
# root path updated to reviews/archive/ when the processed review was archived (responder, 2026-10-28)
# 16 eps gamma^2 — the tracer's stars (raytrace.star_images: a 4 x 4 boost of the photon) or the reference
# (raytrace.ref_aberration: cos theta' = (cos theta + beta)/(1 + beta cos theta), then sin theta' = sqrt(1 - cos^2),
# which loses precision for stars near the line of motion). Both are compared with the aberrated direction in
# 50-digit arithmetic (mpmath), for the 300 stars of v10's "sky" preset at seed 5 (whose check failed in the browser) and
# for 20 000 random stars at beta = 0.5.
# Run (from engine/):
#   docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf \
#     -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server:/lf/visualizations/tests \
#     light-funnel-viz python3 reviews/archive/2026-10-28_internal_B3/c17_aberration_attribution.py > reviews/archive/2026-10-28_internal_B3/out/c17_aberration_attribution.txt
import mpmath as mp
import numpy as np
from harness import Harness

from lfphys.core import backend as B
from lfphys.core import lorentz as LZ
from lfphys.core import raytrace as RT
from v10_fast_observer.viz import C

B.configure({"kernels": {RT.KERNEL: {"device": "cpu"}}})
mp.mp.dps = 50
EPS = np.finfo(float).eps


def exact(s, b):
    """Observer-frame look direction of a star at lab direction s for an observer with velocity b (units of c):
    d' = (s + (gamma_factor) b) / (gamma (1 + b.s)) form, from the boost of the photon k = (1, -s), in 50 digits."""
    s = [mp.mpf(float(x)) for x in s]
    bb = [mp.mpf(float(x)) for x in b]
    b2 = sum(x * x for x in bb)
    g = 1 / mp.sqrt(1 - b2)
    bs = sum(x * y for x, y in zip(bb, s))
    # boost of k = (1, -s) into the frame moving with b: k0' = g (1 + b.s), k' = -s + ((g - 1)(b.(-s))/b2 - g) b
    k0 = g * (1 + bs)
    kv = [-si + ((g - 1) * (-bs) / b2 - g) * bi for si, bi in zip(s, bb)]
    d = [-x / k0 for x in kv]
    n = mp.sqrt(sum(x * x for x in d))
    return [x / n for x in d]


def angle_to(dirs, ex):
    out = []
    for d, e in zip(dirs, ex):
        dm = [mp.mpf(float(x)) for x in d]
        c = [dm[1] * e[2] - dm[2] * e[1], dm[2] * e[0] - dm[0] * e[2], dm[0] * e[1] - dm[1] * e[0]]
        out.append(float(mp.atan2(mp.sqrt(sum(x * x for x in c)), sum(x * y for x, y in zip(dm, e)))))
    return np.array(out)


def report(label, s, u):
    b = np.asarray(u, float)
    st = RT.star_images(RT.Scene([], stars=[(tuple(x), 5000.0) for x in s]), RT.Observer(0.0, (0, 0, 0), tuple(b)))
    ref = RT.ref_aberration(s, b)
    ex = [exact(x, b) for x in s]
    a_tr, a_ref = angle_to(st["d"], ex), angle_to(ref, ex)
    g2 = float(LZ.gamma_of(b)) ** 2
    k_tr, k_ref = int(np.argmax(a_tr)), int(np.argmax(a_ref))
    th = np.degrees(np.arccos(np.clip(s @ (b / np.linalg.norm(b)), -1, 1)))
    print(f"{label}: tracer max error {a_tr.max():.2e} rad = {a_tr.max() / (EPS * g2):.1f} eps gamma^2 (star at "
          f"{th[k_tr]:.2f} deg from the velocity); reference max error {a_ref.max():.2e} rad = "
          f"{a_ref.max() / (EPS * g2):.1f} eps gamma^2 (star at {th[k_ref]:.3f} deg from the velocity)")


h = Harness("v10_fast_observer", "sky", seed=5)
sim = h.sim
s = np.array([x[0] for x in sim.scene.stars])
u = np.asarray(sim.observer(0.0).u) / C
report("v10 sky preset, seed 5 (300 stars, beta 0.9)", s, u)
rng = np.random.default_rng(2026)
s2 = rng.normal(size=(20000, 3))
s2 /= np.linalg.norm(s2, axis=1, keepdims=True)
e = rng.normal(size=3)
report("20 000 random stars, beta 0.5", s2, 0.5 * e / np.linalg.norm(e))
