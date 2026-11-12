# [root path fixed after archiving, 2026-10-28, by the responder: reviews/ -> reviews/archive/]
# Review B4, check c06: v13/v14 wave functions and their checks.
# (a) hydrogen.radial (log-scaled recurrence) against mpmath at 50 digits (an independent closed form: the explicit
#     Laguerre polynomial and factorials) for n <= 12, all l, over 0 < r < r_max of v13;
# (b) central3d.sph_harm / real_harm against mpmath's spherharm (its own Condon-Shortley convention) and the Cartesian
#     forms p_x = sqrt(3/4pi) x/r, d_xy = sqrt(15/4pi) xy/r^2, d_z2 = sqrt(5/16pi)(3z^2 - r^2)/r^2;
# (c) what the shared `dipole` check of lfviz.orbitals3d compares: both sides come from the same Orbital objects;
#     a wrong radial function for state 2 (2p replaced by a normalised but wrong function) still passes it for a
#     pair without a closed form, while `energy_1` and the slice check catch it;
# (d) the record's size of a superposition world per placement of a plane (all phases re-sent).
#
# Root (fix after archiving): engine mounted at /lf (host /home/ildar/hdd/projects/i/light-funnel/engine); this
# script in /lf/reviews/archive/2026-10-28_internal_B4/. CPU only.
# Run:
#   docker run --rm --user "$(id -u):$(id -g)" -v <engine>:/lf:ro \
#     -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server:/lf/lfphys:/lf/visualizations/tests light-funnel-viz \
#     python3 /lf/reviews/archive/2026-10-28_internal_B4/c06_orbitals.py > out/c06_orbitals.txt
import math

import mpmath as mp
import numpy as np

from lfphys.core.quantum import central3d as C
from lfphys.core.quantum import hydrogen as H

mp.mp.dps = 50
print("== (a) R_nl against mpmath (50 digits), relative to max|R| over the grid ==")
worst = (0, None)
for n in range(1, 13):
    r_max = 2.0 * n * n + 40.0 * n
    r = np.concatenate([np.linspace(1e-6, 3 * n * n, 120), np.linspace(3 * n * n, r_max, 60)])
    for l in range(n):
        got = H.radial(n, l, r)
        k, a = n - l - 1, 2 * l + 1
        N = mp.sqrt((mp.mpf(2) / n) ** 3 * mp.factorial(k) / (2 * n * mp.factorial(n + l)))
        ref = np.array([float(N * mp.e ** (-mp.mpf(2) * x / n / 2) * (mp.mpf(2) * x / n) ** l
                              * mp.laguerre(k, a, mp.mpf(2) * x / n)) for x in r])
        err = float(np.max(np.abs(got - ref)) / np.max(np.abs(ref)))
        if err > worst[0]:
            worst = (err, (n, l))
print(f"largest max|R - R_mp| / max|R| = {worst[0]:.2e} at (n, l) = {worst[1]}")

print("\n== (b) Y_lm against mpmath.spherharm and real orbitals against Cartesian forms ==")
rng = np.random.default_rng(1)
th, ph = np.arccos(rng.uniform(-1, 1, 40)), rng.uniform(-math.pi, math.pi, 40)
mx = 0.0
for l in range(0, 12):
    for m in range(-l, l + 1):
        ours = C.sph_harm(l, m, th, ph)
        ref = np.array([complex(mp.spherharm(l, m, t, p)) for t, p in zip(th, ph)])
        mx = max(mx, float(np.max(np.abs(ours - ref))))
print(f"max |Y_lm - mpmath| over l <= 11, all m, 40 random directions: {mx:.2e}")
x, y, z = np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)
for (l, m, name, f) in ((1, 1, "p_x", math.sqrt(3 / (4 * math.pi)) * x), (1, -1, "p_y", math.sqrt(3 / (4 * math.pi)) * y),
                        (2, -2, "d_xy", math.sqrt(15 / (4 * math.pi)) * x * y),
                        (2, 0, "d_z2", math.sqrt(5 / (16 * math.pi)) * (3 * z * z - 1)),
                        (2, 2, "d_x2-y2", math.sqrt(15 / (16 * math.pi)) * (x * x - y * y))):
    print(f"  real_harm({l},{m:+d}) vs {name}: max diff {float(np.max(np.abs(C.real_harm(l, m, th, ph) - f))):.2e}; "
          f"name {C.orbital_name(l, m, True)}")

print("\n== (c) the `dipole` check with a wrong radial function for state 2 ==")
from harness import Harness  # noqa: E402

def run_super(spec, wrong=False):
    import v13_hydrogen_3d.viz as V13
    orig = H.orbital
    if wrong:
        def bad(n, l, m, Z=1.0, a=1.0, real=False):
            o = orig(n, l, m, Z, a, real)
            if (n, l) == (3, 1):  # replace R_31 by R_21 (normalised, wrong: other nodes, other size)
                o.R = lambda r: H.radial(2, 1, r, Z, a)
            return o
        V13.H.orbital = bad
    try:
        h = Harness("v13_hydrogen_3d", None, {**spec, "ng": 64})
        h.run_to(h.sim.period * 1.01)
        ck = h.checks()
        return {k: (v.get("value"), v.get("ref"), v.get("ok"), v.get("rel"), v.get("tol")) for k, v in ck.items()
                if k.startswith(("dipole", "energy", "slice", "r_", "continuity", "nodes"))}
    finally:
        V13.H.orbital = orig

def verdict(v):
    val, ref, ok, rel, tol = v
    if ok is not None:
        return "ok" if ok else "FAIL"
    if rel is None:
        return "—"
    return "ok" if abs(rel) <= tol else "FAIL"

spec = {"mode": "super", "n": 2, "l": 0, "m": 0, "n2": 3, "l2": 1, "m2": 0}
for wrong in (False, True):
    res = run_super(spec, wrong)
    print(f"  2s + 3p_z, {'R_31 replaced by R_21 (WRONG state 2)' if wrong else 'correct'}:")
    for k in sorted(res):
        val, ref = res[k][0], res[k][1]
        fmt = lambda q: "None" if q is None else f"{q:.6g}"  # noqa: E731
        print(f"    {k:12s} {verdict(res[k]):4s} value {fmt(val)} ref {fmt(ref)}")

print("\n== (d) the record's size per placement of a plane (superposition, 24 phases) ==")
from lfviz import protocol  # noqa: E402
h = Harness("v13_hydrogen_3d", "super_1s2p")
h.run_to(h.sim.period * 1.05)
size = lambda: sum(len(protocol.encode(m, b)) for m, b in h.msgs if m.get("type") != "frame")  # noqa: E731
s0 = size()
for i in range(5):
    h.cmd("view", op="plane", id=1, origin=[0.0, 0.0, 0.1 * i], normal=[0.0, math.sin(0.2 * i), math.cos(0.2 * i)])
s1 = size()
print(f"after one period: {s0 / 1e6:.2f} MB; five placements of plane 1: +{(s1 - s0) / 1e6:.2f} MB "
      f"({(s1 - s0) / 5e6:.2f} MB each)")
