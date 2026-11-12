"""P5 review, check 1: the adaptive Magnus integrator ``open_systems.evolve`` on harder time-dependent problems.

Claim under test (open_systems docstring): the returned err[k] is the global trace-norm error to the accuracy of the
Richardson estimates and is <= tol (+ rounding allowance) by construction.

Reference for each case: fixed-step Magnus-4 with n and 2n steps per output interval, Richardson-extrapolated
(error O(h^6) of the extrapolated value, checked by comparing n=2000/4000 against n=4000/8000), so the reference is
far more accurate than the tolerances tested.

Cases: (a) a linearly polarised strong drive (counter-rotating terms, Bloch-Siegert regime Omega ~ omega0) with damping;
(b) a damped Landau-Zener chirp; (c) a 4-level random Lindbladian with a two-tone drive; (d) stiffness: Gamma >> drive
(cost of the step limit h ||L||_F <= 1).

Run: python3 s01_magnus_hard.py  (engine on PYTHONPATH)
"""
import argparse
import math
import time

import numpy as np

from lfphys.core.quantum import open_systems as OS, two_level as TL


def ref_solution(H, c_ops, rho0, ts, n):
    r1, _, _ = OS.evolve(H, c_ops, rho0, ts, steps=n)
    r2, _, _ = OS.evolve(H, c_ops, rho0, ts, steps=2 * n)
    return r2 + (r2 - r1) / 15.0, r2


def check(name, H, c_ops, rho0, ts, tols, n_ref=2000):
    t0 = time.time()
    ref, ref2 = ref_solution(H, c_ops, rho0, ts, n_ref)
    ref_b, _ = ref_solution(H, c_ops, rho0, ts, 2 * n_ref)
    ref_err = max(OS.trace_norm(a - b) for a, b in zip(ref, ref_b))
    print(f"[{name}] reference self-consistency (n={n_ref} vs {2*n_ref}, extrapolated): {ref_err:.2e}"
          f"  ({time.time()-t0:.1f} s)")
    for tol in tols:
        t1 = time.time()
        r, err, info = OS.evolve(H, c_ops, rho0, ts, tol=tol)
        meas = np.array([OS.trace_norm(a - b) for a, b in zip(r, ref_b)])
        worst = float(np.max(meas[1:] / np.maximum(err[1:], 1e-300)))
        print(f"  tol={tol:.0e}: measured max {meas.max():.3e}, returned err[-1] {err[-1]:.3e}, "
              f"max(measured/err) {worst:.3f}, steps acc/rej {info['accepted']}/{info['rejected']}, "
              f"{time.time()-t1:.1f} s  -> {'OK' if worst <= 1 else 'UNDERESTIMATED'}")


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    rho_g = TL.density_matrix([0, 0, -1])
    # (a) linear drive Omega cos(w t) sigma_x, Omega = 0.8 omega0 (strong: RWA fails), damping
    w0, w, Om = 1.0, 1.0, 0.8
    H = lambda t: 0.5 * w0 * TL.SZ + Om * math.cos(w * t) * TL.SX  # noqa: E731
    check("linear strong drive (BS regime)", H, TL.collapse_operators(20.0, 15.0), rho_g, np.linspace(0, 30, 7),
          (1e-6, 1e-9, 1e-11))
    # (b) damped Landau-Zener: Delta(t) = alpha t through resonance
    al, Om = 2.0, 1.0
    H = lambda t: -al * t * TL.PE + 0.5 * Om * TL.SX  # noqa: E731
    check("damped Landau-Zener", H, TL.collapse_operators(10.0, 5.0), rho_g, np.linspace(-15, 15, 7), (1e-6, 1e-9))
    # (c) 4 levels, random generator, two-tone drive
    rng = np.random.default_rng(3)
    d = 4
    A = rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d))
    H0 = 0.5 * (A + A.conj().T)
    B = rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d))
    V = 0.5 * (B + B.conj().T)
    Ls = [0.3 * (rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d))) for _ in range(2)]
    H = lambda t: H0 + (math.cos(1.7 * t) + 0.5 * math.sin(5.3 * t)) * V  # noqa: E731
    rho0 = np.diag([1.0, 0, 0, 0]).astype(complex)
    check("4-level random, two-tone", H, Ls, rho0, np.linspace(0, 10, 6), (1e-7, 1e-10), n_ref=2000)
    # (d) stiffness: cost of the step limit h ||L||_F <= 1
    print("[stiff] Gamma >> drive: slowly modulated drive Omega(t) = cos(0.1 t), span 10")
    for G in (1e2, 1e3, 1e4):
        H = lambda t: 0.5 * math.cos(0.1 * t) * TL.SX  # noqa: E731
        t1 = time.time()
        try:
            r, err, info = OS.evolve(H, TL.collapse_operators(1 / G, 2 / G), rho_g, [0.0, 10.0], tol=1e-8)
            print(f"  Gamma={G:.0e}: accepted {info['accepted']}, rejected {info['rejected']}, h_max {info['h_max']:.2e},"
                  f" {time.time()-t1:.1f} s")
        except RuntimeError as e:
            print(f"  Gamma={G:.0e}: RuntimeError {e} after {time.time()-t1:.1f} s")
    # Gamma = 1e5 would need ~1.7e6 steps (h <= 0.9/||L||_F, ||L||_F ~ 1.5 Gamma): above max_steps = 1e6


if __name__ == "__main__":
    main()
