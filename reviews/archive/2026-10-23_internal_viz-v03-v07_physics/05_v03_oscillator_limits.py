"""v03, harmonic trap: cost of a world over the allowed range (hw in [0.001, 1] eV, x0 in [0, 60] nm).

Part A (dry): the grid size n and the number of split-operator steps the world will take (viz.py:_build/_evolve with
_evolve stubbed), and the memory of the dense sinc-DVR Hamiltonian that the level check builds
(schrodinger1d.Grid.hamiltonian: several n x n float64/int64 arrays), and whether the grid was capped at 32768 points
(then 6 points per half-wave of the fastest component are no longer guaranteed).
Part B (real, argument "run <hw> <x0>"): builds the world through the harness and prints its checks and wall time.
Output: out/05_v03_oscillator_limits.txt (part A) and out/05_v03_oscillator_run_<hw>_<x0>.txt (part B)
"""
import math
import sys
import time

sys.path.insert(0, "/lf/visualizations/tests")
import v03_quantum_1d.viz as V  # noqa: E402
from harness import Harness  # noqa: E402


def dry():
    out = open("out/05_v03_oscillator_limits.txt", "w")

    def say(*a):
        s = " ".join(str(x) for x in a)
        print(s)
        out.write(s + "\n")
    orig = V.Simulation._evolve
    V.Simulation._evolve = lambda self: None
    say("hw (eV) | x0 (nm) | n_grid | capped | k_max of packet (1/nm) | pi/dx (1/nm) | steps of the run | "
        "dense H: one n x n float64 array (GB)")
    for hw in (0.001, 0.01, 0.05, 0.2, 0.5, 1.0):
        for x0 in (0.0, 15.0, 60.0):
            p, _ = V.SCHEMA.resolve("oscillator", {"hw": hw, "x0": x0})
            sim = V.Simulation.__new__(V.Simulation)
            sim.params = dict(p)
            V.Simulation._build(sim)
            w = hw / V.HBAR
            kpk = sim.m * w * (abs(x0) + 6 * sim.sigma) / V.HBAR + 4 / sim.sigma
            dx = sim.grid.dx
            t_end = 2 * 2 * math.pi * V.HBAR / hw
            steps = 600 * max(1, math.ceil((t_end / 600) / sim._dt_max()))
            n_needed = int(2 ** math.ceil(math.log2(max(1024, 2 * sim.L / (math.pi / (6 * kpk))))))
            say(f"{hw:g} | {x0:g} | {sim.n_grid} | {'YES (needed ' + str(n_needed) + ')' if n_needed > sim.n_grid else 'no'} | "
                f"{kpk:.4g} | {math.pi / dx:.4g} | {steps:.3g} | {sim.n_grid ** 2 * 8 / 1e9:.3g}")
    V.Simulation._evolve = orig


def run(hw, x0):
    out = open(f"out/05_v03_oscillator_run_{hw:g}_{x0:g}.txt", "w")
    t0 = time.time()
    h = Harness("v03_quantum_1d", "oscillator", {"hw": hw, "x0": x0})
    out.write(f"hw = {hw} eV, x0 = {x0} nm: world built in {time.time() - t0:.1f} s, n_grid = {h.sim.n_grid}\n")
    for c in h.checks().values():
        out.write(f"  {c['id']}: value {c['value']!r}, ref {c['ref']!r}, rel {c['rel']!r}, tol {c['tol']}, "
                  f"ok {c.get('ok')}\n")
    out.close()
    print(open(f"out/05_v03_oscillator_run_{hw:g}_{x0:g}.txt").read())


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        run(float(sys.argv[2]), float(sys.argv[3]))
    else:
        dry()
