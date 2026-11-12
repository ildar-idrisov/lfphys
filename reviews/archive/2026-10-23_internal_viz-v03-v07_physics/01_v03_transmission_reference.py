"""v03: the packet transmission check against the stationary reference, on legitimate inputs at the edges of the
parameter ranges.

For every case: the run's checks (abs, T, E), the run's own reference, and an independent reference that keeps the
whole momentum distribution of the packet: components with k < 0 move away from the potential and never transmit,
so  T_packet = sum_{k>0} T(k) w(k) / sum_{all k} w(k),  w(k) = exp(-(k-k0)^2 / (2 s_k^2)), s_k = 1/(2 sigma).
The run's reference instead normalises over k > 0 only (viz.py:_expected_T, ks from max(k0 - 8 s_k, 1e-6)).
Output: out/01_v03_transmission_reference.txt
"""
import math
import sys
import time

import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402
from v03_quantum_1d.viz import HBAR, FS  # noqa: E402
from lfphys.core.quantum import transfer  # noqa: E402

OUT = open("out/01_v03_transmission_reference.txt", "w")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.write(s + "\n")
    OUT.flush()


def full_reference(sim):
    """Independent: the whole Gaussian momentum distribution (k < 0 included, they never reach the potential)."""
    sk = 1 / (2 * sim.sigma)
    ks = np.linspace(sim.k0 - 10 * sk, sim.k0 + 10 * sk, 4001)
    w = np.exp(-((ks - sim.k0) ** 2) / (2 * sk * sk))
    pos = ks > 1e-9
    E = HBAR**2 * ks[pos] ** 2 / (2 * sim.m)
    x0, x1 = sim.extent
    kmax = math.sqrt(2 * sim.m * (E.max() + float(np.max(np.abs(sim.V))))) / HBAR
    h = min(sim.params["edge"] / 20, math.pi / (40 * kmax))
    n = int(math.ceil((x1 - x0) / h))
    T = transfer.transmission_profile(E, sim.Vf, x0, x1, 2 * n, sim.m, HBAR)
    return float(np.sum(T * w[pos]) / np.sum(w)), float(np.sum(w[~pos]) / np.sum(w))


CASES = [
    ("barrier, default", {}),
    ("barrier, E = 0.05 eV, sigma = 1 nm (both at range limits)", {"energy": 0.05, "sigma": 1.0}),
    ("barrier, E = 0.1 eV, sigma = 1 nm", {"energy": 0.1, "sigma": 1.0}),
    ("free particle, E = 0.05 eV, sigma = 1 nm", {"scenario": "free", "energy": 0.05, "sigma": 1.0}),
    ("free particle, E = 0.2 eV, sigma = 1 nm", {"scenario": "free", "energy": 0.2, "sigma": 1.0}),
    ("well V0 = -5, E = 0.05, sigma = 1", {"scenario": "well", "V0": -5.0, "width": 1.0, "energy": 0.05, "sigma": 1.0}),
    ("step V0 = 0.75, E = 0.8 (slow transmitted wave)", {"scenario": "step", "V0": 0.75, "energy": 0.8}),
    ("step V0 = -5, E = 0.05, sigma = 1 (step down)", {"scenario": "step", "V0": -5.0, "energy": 0.05, "sigma": 1.0}),
    ("thick barrier width 3 nm (T tiny)", {"width": 3.0}),
    ("thick barrier width 5 nm (T tiny)", {"width": 5.0}),
]

say("case | n_grid | T_run(packet) | T_ref(run) | T_ref(full, independent) | P(k<0) | |T_run-T_ref(run)| tol | "
    "T check ok | abs value | E rel | seconds")
for name, params in CASES:
    t0 = time.time()
    try:
        h = Harness("v03_quantum_1d", None, params, seed=1)
    except Exception as e:  # noqa: BLE001
        say(f"{name}: CONSTRUCTION FAILED {type(e).__name__}: {e}")
        continue
    sim = h.sim
    ch = h.checks()
    Tc, Ac, Ec = ch.get("T0"), ch.get("abs0"), ch.get("E0")
    full, pneg = full_reference(sim)
    tol = 1e-4 + 1e-3 * Tc["ref"] if Tc else float("nan")
    say(f"{name} | {sim.n_grid} | {Tc['value']:.6e} | {Tc['ref']:.6e} | {full:.6e} | {pneg:.3e} | "
        f"{abs(Tc['value'] - Tc['ref']):.2e} vs {tol:.2e} | {Tc['ok']} | {Ac['value']:.6f} (tol {Ac['tol']}) | "
        f"{Ec['rel']:.1e} | {time.time() - t0:.1f}")
say("")
say("Reading: when P(k<0) is not negligible, the run's packet result agrees with the FULL reference and the run's")
say("own reference (normalised over k > 0 only) is wrong by the factor 1/(1 - P(k<0)); the check then fails on a")
say("legitimate input. For tiny T, the absolute part 1e-4 of the tolerance exceeds T itself: the check cannot detect")
say("an error of 100 % (any value in [0, 2T] passes).")
