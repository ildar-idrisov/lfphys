"""v07 (Bell test) probes.
A. joint Born probabilities of the engine (qubits.joint_probabilities) at analyzer angles where one cell is exactly 0
   (photons a = b, spins a = b): sign of the round-off, and whether qubits.sample_pairs (numpy Generator.choice, which
   rejects negative p) raises; then the same through the run (fixed settings a = b).
B. degenerate settings a' = a (allowed): cells (a,b) and (a',b) share one store key, so S = 2 E(a,b) uses the same
   pairs twice while its error assumes four independent cells. Monte Carlo over seeds: the empirical spread of S
   against the run's reported sigma.
C. statistics of the standard presets over seeds: z of S against the law, the fraction |z| > 3 (calibration of the
   5-sigma checks).
D. cost of the pairs in flight: n_in_flight = rate * L / v; the run keeps every pair in flight in arrays
   (np.concatenate per step).
Output: out/09_v07_bell.txt
"""
import math
import sys
import time

import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402
from lfphys.core.quantum import qubits as Q  # noqa: E402
from v07_bell_test.engine.experiment import Law  # noqa: E402

OUT = open("out/09_v07_bell.txt", "w")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.write(s + "\n")
    OUT.flush()


say("A. zero cells of the joint Born probabilities")
neg = []
for pair in ("photon", "spin"):
    law = Law(pair, "quantum")
    for deg in np.round(np.arange(-360, 360.01, 0.5), 6):
        P = Q.joint_probabilities(law.state, law.projectors(float(deg)), law.projectors(float(deg)))
        if P.min() < 0:
            neg.append((pair, float(deg), float(P.min())))
say(f"  angles a = b (step 0.5 deg over [-360, 360]) with a negative joint probability: {len(neg)}; first: {neg[:6]}")
if neg:
    pair, deg, pmin = neg[0]
    law = Law(pair, "quantum")
    try:
        law.sample(deg, deg, 100, np.random.default_rng(1))
        say(f"  qubits.sample_pairs at {pair} a = b = {deg}: no exception")
    except ValueError as e:
        say(f"  qubits.sample_pairs at {pair} a = b = {deg}: ValueError: {e}")
    h = Harness("v07_bell_test", "scan" if pair == "photon" else "spin_chsh",
                {"switch": "fixed", "a_deg": deg, "b_deg": deg})
    try:
        h.run_to(20 * h.sim._flight())
        say(f"  run (fixed a = b = {deg}, {pair}): errors {h.errors()[:2]}, detected {h.sim.counts['detected']}")
    except Exception as e:  # noqa: BLE001 (the runner's play loop would catch it, pause and print the traceback)
        say(f"  run (fixed a = b = {deg}, {pair}): EXCEPTION in advance: {type(e).__name__}: {e}")

say("\nB. a' = a (degenerate settings): spread of S over seeds vs the run's sigma")
for (a, a2, b, b2) in ((0.0, 0.0, 45.0, 0.0), (0.0, 0.0, 0.0, 45.0)):
    S, se = [], []
    for seed in range(60):
        h = Harness("v07_bell_test", "photon_chsh", {"a_deg": a, "a2_deg": a2, "b_deg": b, "b2_deg": b2}, seed=seed)
        h.run_to(h.sim._flight() + 4000 / h.sim.params["rate"])
        s = h.sim._S(h.sim._cells())
        S.append(s["S"])
        se.append(s["se"])
    S = np.array(S)
    say(f"  a = a' = {a}, b = {b}, b' = {b2}: S mean {S.mean():+.4f} (law {h.sim._S_law:+.4f}), empirical SD "
        f"{S.std(ddof=1):.4f}, mean reported sigma {np.mean(se):.4f}, ratio {S.std(ddof=1) / np.mean(se):.2f}")

say("\nC. calibration of z(S) for the presets (60 seeds, ~4000 pairs each)")
for preset in ("photon_chsh", "spin_chsh", "photon_lhv", "spin_lhv"):
    z = []
    for seed in range(60):
        h = Harness("v07_bell_test", preset, seed=seed)
        h.run_to(h.sim._flight() + 4000 / h.sim.params["rate"])
        s = h.sim._S(h.sim._cells())
        z.append(s["z"])
    z = np.array(z)
    say(f"  {preset}: mean z {z.mean():+.3f}, SD {z.std(ddof=1):.3f}, max |z| {np.abs(z).max():.2f}")

say("\nD. pairs in flight")
for pair, beta, L, rate in (("photon", None, 1e5, 1e9), ("spin", 1e-3, 1e3, 1e8)):
    params = {"pair": pair, "L_m": L, "rate": rate}
    if beta:
        params["spin_beta"] = beta
    h = Harness("v07_bell_test", None, params)
    fl = h.sim._flight()
    t0 = time.time()
    h.run_to(0.25 * fl)
    dt = time.time() - t0
    say(f"  {pair}, v/c = {beta or 1}, L = {L:g} m, rate = {rate:g}/s: flight {fl:.3g} s, in flight now "
        f"{h.sim.exp.n_flight}, wall time for a quarter of the flight {dt:.1f} s "
        f"(the default speed plays one flight in {2.0:.0f} s of wall time)")
say(f"  upper corner of the allowed ranges (spin, v/c = 1e-4, L = 1e5 m, rate 1e9/s): rate L / v = "
    f"{1e9 * 1e5 / (1e-4 * 299792458):.2e} pairs in flight (~{1e9 * 1e5 / (1e-4 * 299792458) * 66 / 1e9:.0f} GB)")
