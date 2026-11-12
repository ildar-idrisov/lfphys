"""08: numerics of lfphys.core.quantum: Strang split-operator order (anharmonic oscillator, against a converged
reference), sinc-DVR spectrum, the radial sine-DVR + Richardson accuracy (hydrogen-like levels, the docstring claims
"Coulomb test: 1e-4 -> ~1e-6 relative"), and the transfer-matrix route for a barrier placed away from x = 0.
Usage: python3 08_quantum_numerics.py
"""
import argparse
import math

argparse.ArgumentParser(description=__doc__).parse_args()

import numpy as np

from lfphys.core.quantum import radial, schrodinger1d as S1, transfer

print("=== split-operator: error at t = 2 vs dt (V = x^4/4, packet x0 = 1.5) ===")
g = S1.Grid(np.linspace(-12, 12, 1024, endpoint=False), m=1.0)
V = 0.25 * g.x**4
psi0 = g.gaussian(1.5, 0.0, 0.5)


def run(dt, T=2.0):
    n = int(round(T / dt))
    st = g.stepper(V, dt)
    p = psi0.copy()
    for _ in range(n):
        p = st(p)
    return p


ref = run(2.0 / 64000)
prev = None
for n in (250, 500, 1000, 2000, 4000):
    e = np.sqrt(g.norm(run(2.0 / n) - ref))
    print(f"dt = 2/{n}: ||psi - ref|| = {e:.3e}" + (f"   ratio {prev / e:.2f}" if prev else ""))
    prev = e

print("\n=== sinc-DVR (Colbert-Miller) on the harmonic oscillator, omega = 1, x in [-L, L) ===")
for npts in (64, 96, 128):
    gg = S1.Grid(np.linspace(-10, 10, npts, endpoint=False), m=1.0)
    E, _ = gg.eigenstates(0.5 * gg.x**2, 10)
    print(f"N={npts}: max |E_n - (n+1/2)| over n<10 = {np.max(np.abs(E - (np.arange(10) + 0.5))):.1e}")

print("\n=== radial levels (hbar = mu = 1): Coulomb -1/r and the relative error of E_n ===")
for R, N in ((100.0, 800), (100.0, 1600), (60.0, 1600), (100.0, 3200)):
    for l in (0, 1, 2):
        E, r, u = radial.levels(lambda r: -1.0 / r, l, 1.0, R, N=N, n_states=3)
        Eraw, _, _ = radial.levels(lambda r: -1.0 / r, l, 1.0, R, N=N, n_states=3, richardson=False)
        n = np.arange(1, 4) + l
        ex = -1.0 / (2 * n**2)
        print(f"R={R:g} N={N} l={l}: rel. err (Richardson) {np.abs(E / ex - 1).max():.1e}   "
              f"(no Richardson {np.abs(Eraw / ex - 1).max():.1e})")

print("\n=== transfer.transmission: the same barrier (V0 = 1, a = 2, E = 0.5) shifted to x0 ===")
for x0 in (0.0, 100.0, 300.0, 600.0, 1000.0):
    try:
        T, R_, t, r = transfer.transmission(0.5, [x0, x0 + 2.0], [0.0, 1.0, 0.0])
        msg = f"T = {T:.15e}  T+R-1 = {T + R_ - 1:+.1e}"
    except Exception as ex:  # noqa: BLE001
        msg = f"RAISES {type(ex).__name__}: {ex}"
    try:
        Tp = transfer.transmission_profile(np.array([0.5]), lambda x: np.where((x >= x0) & (x < x0 + 2), 1.0, 0.0),
                                           x0, x0 + 2.0, 1)[0]
        msg2 = f"profile T = {Tp:.15e}"
    except Exception as ex:  # noqa: BLE001
        msg2 = f"profile RAISES {type(ex).__name__}"
    print(f"x0 = {x0:6g}: {msg};  {msg2}")
print("closed form:", transfer.rectangular_barrier(0.5, 1.0, 2.0))
