"""s06: the cost of v16 worlds over the corners of the legal parameter space (viz.py SCHEMA: l -6..6, p 0..3, w0 0.3..6,
lam 0.4..1.6, zspan 0.4..3, gen mode/spp, model exact/paraxial), by replaying Beam.__init__'s sizing (apparatus.py:43-84)
without building the tables: the radial grid, the quadrature nodes of VortexBeam.table(estimate=True) (two passes, the
finer with factor 2) or of fresnel_table, and the size of the largest dense matrix (the Bessel matrix nr x nq, float64)
plus the phase matrix nz x nq (complex). Nothing heavy is allocated here.
Then, with --run, builds one world given as key=value pairs through the harness with a wall-clock report."""
import itertools
import math
import sys
import time

import numpy as np

for p in ("/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys", "/lf/visualizations/tests"):
    sys.path.insert(0, p)
from lfphys.core.optics import beams as B  # noqa: E402
from lfphys.theories.approx import beams_paraxial as PX  # noqa: E402
from v16_optical_vortices.engine import apparatus as A  # noqa: E402


def sizing(gen, model, l, p, w0, lam, zspan):
    k = 2 * math.pi / lam
    zr = PX.rayleigh(k, w0)
    if gen == "mode":
        z0, z1 = -zspan * zr, zspan * zr
        fn, qmax = B.lg_waist_spectrum(p, l, w0)
    else:
        p = 0
        z0, z1 = 0.0, 2 * zspan * zr
        fn, qmax = B.gaussian_vortex_spectrum(l, w0)
    zmax = max(abs(z0), abs(z1))
    wmax = float(PX.params(zmax, k, w0)[0])
    half = wmax * (2.2 + 0.75 * math.sqrt(2 * p + abs(l) + 1))
    qs = np.linspace(0.0, min(k, qmax), 2001)
    a = np.abs(np.asarray(fn(qs), complex))
    edge = float(a[-1] / max(float(a.max()), 1e-300)) if qmax >= k else 0.0
    am_half = half if (model != "exact" or edge < 1e-6) else max(half, 10 * lam)
    r_far = 1.45 * max(half, am_half)
    nr = max(A.NR, int(math.ceil(r_far / (lam / 16))))
    nz = A.NZ
    if model == "exact":
        th_max = math.asin(min(1.0, qmax / k))
        osc = k * (r_far + zmax) * th_max
        nq = 2 * (int(math.ceil(osc / (2 * math.pi))) + 12) * 16  # the finer pass of estimate=True
        n_mats = 2 * len({1: 1, -1: 1} if model == "exact" else {1: 1})  # helicities (lin: 2)
    else:
        if gen == "mode":
            nq = 0
        else:
            osc = k * r_far + k * k * zmax / (2 * k)
            nq = (int(math.ceil(osc / (2 * math.pi))) + 16) * 16
    gb = (nr * nq * 8 + nz * nq * 16) / 1e9
    return {"nr": nr, "nq": nq, "GB": gb, "half": half, "zmax": zmax, "edge": edge}


if "--run" in sys.argv:
    from harness import Harness  # noqa: E402
    kv = dict(a.split("=") for a in sys.argv[sys.argv.index("--run") + 1:])
    params = {}
    for k_, v in kv.items():
        try:
            params[k_] = int(v)
        except ValueError:
            try:
                params[k_] = float(v)
            except ValueError:
                params[k_] = v
    t0 = time.time()
    h = Harness("v16_optical_vortices", None, params)
    print(f"built {params} in {time.time() - t0:.1f} s; errors {h.errors()}")
    sys.exit()

rows = []
for gen, model, l, p, w0, lam, zspan in itertools.product(("mode", "spp"), ("exact", "paraxial"), (0, 6), (0, 3),
                                                          (0.3, 6.0), (0.4, 1.6), (0.4, 3.0)):
    if gen == "spp" and p:
        continue
    s = sizing(gen, model, l, p, w0, lam, zspan)
    rows.append(((gen, model, l, p, w0, lam, zspan), s))
rows.sort(key=lambda r: -r[1]["GB"])
print("largest dense matrices (one helicity, the finer pass): gen model l p w0 lam zspan -> nr x nq, GB")
for key, s in rows[:14]:
    print(f"  {key}: nr = {s['nr']}, nq = {s['nq']}, ~{s['GB']:.2f} GB  (half {s['half']:.1f} um, z_max {s['zmax']:.0f} um,"
          f" edge {s['edge']:.2g})")
print("defaults for comparison:")
for key in [("mode", "exact", 3, 0, 1.5, 1.0, 1.5), ("spp", "exact", 2, 0, 1.5, 1.0, 1.5)]:
    s = sizing(*key)
    print(f"  {key}: nr = {s['nr']}, nq = {s['nq']}, ~{s['GB']:.3f} GB")
print("a modest legal world: spp exact l=2 w0=6 lam=1 zspan=1.5 ->", sizing("spp", "exact", 2, 0, 6.0, 1.0, 1.5))
print("                      spp exact l=2 w0=3 lam=0.6 zspan=1.5 ->", sizing("spp", "exact", 2, 0, 3.0, 0.6, 1.5))
