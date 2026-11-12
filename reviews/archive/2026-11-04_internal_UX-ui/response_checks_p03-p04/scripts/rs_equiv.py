import sys, time, importlib.util
import numpy as np
sys.path.insert(0, "/lf/lfphys")
from lfphys.core.md import system as S
spec = importlib.util.spec_from_file_location("old", "/w/system_orig.py", submodule_search_locations=[])
# load old random_sites by exec of its source text
src = open("/w/system_orig.py").read()
i0 = src.index("def random_sites("); i1 = src.index("def _probe(")
ns = {"np": np, "math": __import__("math")}
exec(src[i0:i1], ns)
old = ns["random_sites"]
cases = []
for d in (2, 3):
    for per in ([True]*d, [False]*d, [False]+[True]*(d-1)):
        for n in (1, 7, 60, 300):
            for others in (0, 50):
                cases.append((d, per, n, others))
nbad = 0
for seed, (d, per, n, no) in enumerate(cases):
    L = np.array([12.0, 10.0, 8.0][:d])
    rng0 = np.random.Generator(np.random.PCG64(100 + seed))
    oth = rng0.random((no, d)) * L
    od = 0.5 * (1.0 + rng0.uniform(0.6, 1.4, no))
    lo, hi = np.zeros(d) + 0.5, L - 0.5
    r1 = np.random.Generator(np.random.PCG64(seed)); r2 = np.random.Generator(np.random.PCG64(seed))
    try:
        a = old(n, lo, hi, 1.0, r1, L, np.array(per), oth, od); ea = None
    except ValueError as e:
        a, ea = None, str(e)
    try:
        b = S.random_sites(n, lo, hi, 1.0, r2, L, np.array(per), oth, od); eb = None
    except ValueError as e:
        b, eb = None, str(e)
    same = (ea == eb) and (a is None or (a.shape == b.shape and np.array_equal(a, b))) and (r1.random() == r2.random() if ea is None else True)
    if not same:
        nbad += 1; print("DIFF", d, per, n, no, ea, eb)
print("cases", len(cases), "diff", nbad)
# speed
for d, n, Lb in ((2, 20000, 300.0), (3, 20000, 40.0)):
    L = np.full(d, Lb)
    t0 = time.perf_counter(); S.random_sites(n, np.zeros(d), L, 1.0, np.random.default_rng(1), L, np.ones(d, bool)); t1 = time.perf_counter()
    print("new", d, n, round(t1 - t0, 3), "s")
    if n <= 20000:
        t0 = time.perf_counter(); old(n, np.zeros(d), L, 1.0, np.random.default_rng(1), L, np.ones(d, bool)); t1 = time.perf_counter()
        print("old", d, n, round(t1 - t0, 3), "s")
