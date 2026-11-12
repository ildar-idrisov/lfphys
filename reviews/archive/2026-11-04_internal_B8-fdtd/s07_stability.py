# Review B8-fdtd, script s07: the stability analysis behind the refusal (fdtd.amplification_radius, FDTD._check_medium).
# (a) is the engine's amplification matrix the scheme it runs? (long runs of homogeneous periodic worlds vs. the
#     predicted spectral radius), including the Lorentz explicit (Young-type) update at Courant numbers up to the
#     vacuum limit, compared with Bidegaray-Fesquet, SIAM J. Numer. Anal. 46, 2551 (2008), arXiv:math/0506289, Table 7;
# (b) is the 257-point sampling of the curl-curl eigenvalue fine enough?
# (c) the check cache keyed by id(Medium);
# (d) a world whose E nodes take eps from one medium and H nodes mu from another (no per-medium check sees it).
import argparse
import gc
import math

import numpy as np

from lfphys.core.em import fdtd as F

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--steps", type=int, default=20000)
args = ap.parse_args()

print("== (a) predicted spectral radius vs. growth in a long run (1-D: grid one cell wide, periodic) ==")


def growth_1d(med, S, steps, dx=0.05, L=1.6):
    w = F.FDTD((L, dx), dx, pol="tm", boundary="periodic", courant=S)
    rng = np.random.default_rng(0)
    w.set_field("ez", rng.standard_normal(w.shape[:2]))
    w.set_field("hy", rng.standard_normal(w.shape[:2]))
    w.add_body(F.Box((-1.0, -1.0), (L + 1.0, 1.0)), med)
    lam = np.linspace(0, w.lam_max, 257)
    rho = F.amplification_radius(med, w.dt, lam)
    a0 = np.abs(w.field("ez")).max()
    try:
        w.advance(steps)
        a1 = np.abs(w.field("ez")).max()
    except F.Unstable as e:
        a1 = math.inf
    return rho, a1 / a0


for S in (0.5, 0.7, 0.75, 0.9, 0.99):
    for name, med in (("Lorentz eps_inf=1 de=1.25 f0=0.2 g=0.1", F.Medium(poles=[F.Lorentz(1.25, 0.2, 0.1)])),
                      ("Lorentz eps_inf=1 de=1.25 f0=0.2 g=0  ", F.Medium(poles=[F.Lorentz(1.25, 0.2, 0.0)])),
                      ("Drude fp=1 g=0.1                     ", F.Medium(poles=[F.Drude(1.0, 0.1)])),
                      ("Debye de=3 tau=0.2                   ", F.Medium(poles=[F.Debye(3.0, 0.2)]))):
        try:
            rho, gr = growth_1d(med, S, args.steps)
            print(f"S = {S:4.2f}  {name}  rho_pred = {rho:.12f}  growth over {args.steps} steps = {gr:.3e}")
        except F.Unstable as e:
            print(f"S = {S:4.2f}  {name}  REFUSED: {str(e)[:80]}")

print()
print("== (a') Bidegaray's Young-scheme conditions (1-D, Table 7): q <= 2 i.e. c_inf dt <= dx/sqrt(2), and "
      "omega = w1^2 dt^2/2 <= 2/(2 eps_s' - 1) ==")
for S in (0.6, 0.7071, 0.75, 0.9):
    dt = S * 0.05
    med = F.Medium(poles=[F.Lorentz(1.25, 0.2, 0.1)])
    lam = np.linspace(0, 4 / 0.05 ** 2, 2001)
    rho = F.amplification_radius(med, dt, lam)
    print(f"  S = {S}: engine's spectral radius over q in [0, 4 S^2]: {rho:.15f}")

print()
print("== (b) sampling: 257 points vs 20001 points of the curl-curl eigenvalue ==")
rng = np.random.default_rng(5)
worst = []
for trial in range(300):
    kind = rng.integers(3)
    eps_inf = float(rng.uniform(0.3, 3.0))
    dt = 0.025
    if kind == 0:
        p = F.Lorentz(float(rng.uniform(0.1, 5.0)), float(rng.uniform(0.5, 1.6)) / (2 * math.pi * dt) * 2 / 2,
                      float(rng.uniform(0, 2.0)))
    elif kind == 1:
        p = F.Drude(float(rng.uniform(0.5, 1.2)) * math.sqrt(eps_inf) / (math.pi * dt) / 2, float(rng.uniform(0, 2)))
    else:
        p = F.Debye(float(rng.uniform(0.1, 10)), float(rng.uniform(0.2, 5)) * dt)
    m = F.Medium(eps=eps_inf, poles=[p])
    lam_max = 8 / 0.05 ** 2
    r1 = F.amplification_radius(m, dt, np.linspace(0, lam_max, 257))
    r2 = F.amplification_radius(m, dt, np.linspace(0, lam_max, 20001))
    worst.append((r2 - r1, r1, r2, p.params(), eps_inf))
worst.sort(key=lambda t: -t[0])
print("largest (dense - coarse):")
for d, r1, r2, pp, e in worst[:5]:
    flag = "  <-- coarse says stable, dense says unstable" if (r1 <= 1 + 1e-6 < r2) else ""
    print(f"  {d:.3e}  coarse {r1:.12f}  dense {r2:.12f}  eps_inf {e:.3f} {pp}{flag}")
n_miss = sum(1 for d, r1, r2, _, _ in worst if r1 <= 1 + 1e-6 < r2)
print(f"cases accepted by the 257-point check but unstable on the dense grid: {n_miss} of {len(worst)}")

print()
print("== (c) the check cache is keyed by id(Medium): a freed medium's id reused by an unstable one ==")
hits = 0
for attempt in range(50):
    w = F.FDTD((1.0, 1.0), 0.05, courant=0.6)
    good = F.Medium(eps=2.0)
    w.add_body(F.Cylinder((0.5, 0.5), 0.2), good)
    gid = id(good)
    w.remove_body(1)
    del good
    gc.collect()
    bad = None
    for _ in range(200):
        cand = F.Medium(eps=0.3)  # n = 0.55: the 2-D limit at S = 0.6 is 0.707 * 0.55 = 0.39 -> unstable
        if id(cand) == gid:
            bad = cand
            break
    if bad is None:
        continue
    try:
        w.add_body(F.Cylinder((0.5, 0.5), 0.2), bad)
    except F.Unstable:
        print("  refused (cache not hit)")
        continue
    w.set_field("ez", lambda x, y: np.exp(-((x - 0.5) ** 2 + (y - 0.5) ** 2) / 0.01))
    try:
        w.advance(400)
        res = f"max|Ez| after 400 steps {np.abs(w.field('ez')).max():.3e}"
    except F.Unstable as e:
        res = f"blew up: {str(e)[:60]}"
    print(f"  attempt {attempt}: Medium(eps=0.3) got id of the freed Medium(eps=2.0) and was ACCEPTED; {res}")
    hits += 1
    if hits >= 2:
        break
w2 = F.FDTD((1.0, 1.0), 0.05, courant=0.6)
try:
    w2.add_body(F.Cylinder((0.5, 0.5), 0.2), F.Medium(eps=0.3))
    print("  control: fresh world accepted eps=0.3 (unexpected)")
except F.Unstable:
    print("  control: a fresh world refuses Medium(eps=0.3) at S = 0.6")

print()
print("== (d) E nodes in medium A (eps=0.25, mu=4), H nodes in medium B (eps=4, mu=0.25): each medium alone n = 1 ==")
dx = 0.05
L = 1.0
w = F.FDTD((L, dx), dx, pol="tm", boundary="periodic", courant=0.5)
w.add_body(F.Box((-1.0, -1.0), (2.0, 1.0)), F.Medium(eps=4.0, mu=0.25, label="B"))
fine = 400
xs = (np.arange(fine) + 0.5) / fine * L
arr = (np.abs(xs / dx - np.round(xs / dx)) < 0.25)[:, None] * np.ones((1, 1), bool)
w.add_body(F.Mask(array=arr, lo=(0.0, -1.0), hi=(L, 1.0)), F.Medium(eps=0.25, mu=4.0, label="A"))
eps_e = w._mats["ez"][0][:, 0, 0]
mu_h = w._mats["hy"][0][:, 0, 0]
print(f"  eps at Ez nodes: {np.unique(eps_e)}, mu at Hy nodes: {np.unique(mu_h)}; accepted at S = 0.5 "
      f"(local wave speed 1/sqrt(0.25*0.25) = 4: 1-D limit S = 0.25)")
w.set_field("ez", np.random.default_rng(1).standard_normal(w.shape[:2]))
try:
    for k in range(10):
        w.advance(50)
    print(f"  after 500 steps max|Ez| = {np.abs(w.field('ez')).max():.3e}")
except F.Unstable as e:
    print(f"  the run blew up: {e}")
