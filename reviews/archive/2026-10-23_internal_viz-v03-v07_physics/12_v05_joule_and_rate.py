"""v05: (A) the 'joule' check (Simpson, 2001 points per layer) for strongly absorbing metal films in the allowed
ranges: A_J against 1 - R - T and its convergence with the number of points (skin depth lambda/(4 pi kappa) for
|E|^2 vs the point spacing). (B) cost of the photon stream at the largest allowed rate (1e15 /s).
Output: out/12_v05_joule_and_rate.txt
"""
import math
import sys
import time

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402
from lfphys.core.optics import interfaces, thin_films  # noqa: E402

OUT = open("out/12_v05_joule_and_rate.txt", "w")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.write(s + "\n")
    OUT.flush()


say("A. Joule absorption (s) vs 1 - R - T")
for n0, kap, d, lam, th in ((1.0, 3.3, 30.0, 633.0, 0.0), (1.0, 20.0, 500.0, 300.0, 0.0), (1.0, 20.0, 50.0, 300.0, 0.0),
                            (1.0, 10.0, 100.0, 300.0, 0.0), (4.0, 20.0, 500.0, 300.0, 70.24), (1.0, 5.0, 200.0, 400.0, 0.0)):
    ns, ds = [n0, complex(0.2, kap), 1.07], [d]
    st = interfaces.stack(ns, ds, lam, math.radians(th), "s")
    row = []
    for pts in (2001, 8001, 32001):
        AJ = thin_films.joule_absorption_s(ns, ds, lam, math.radians(th), points=pts)["A"]
        row.append(AJ + st["R"] + st["T"] - 1)
    skin = lam / (4 * math.pi * kap)
    say(f"  n0={n0}, n=0.2+{kap}i, d={d} nm, lambda={lam}, theta={th}: |E|^2 decay length {skin:.3g} nm, "
        f"spacing at 2001 pts {d / 2000:.3g} nm; R+T+A_J-1 at 2001/8001/32001 pts: "
        + ", ".join(f"{x:+.2e}" for x in row) + "  (check tolerance 1e-8)")

say("\nB. the photon stream at rate 1e15 /s (allowed maximum)")
h = Harness("v05_optics_bench", "brewster", {"rate": 1e15})
t0 = time.time()
target = 0.2e-9
h.run_to(target)
say(f"  world time 0.2 ns (0.2 of a flight time): wall {time.time() - t0:.1f} s, photons in flight {len(h.sim.flight)}")
