"""P7 review, check 10c: a prototype of the fix proposed for state_from_invariants (finding E1): the same Newton
equations, but (i) continuation in eps from a small eps where the Newtonian start is close, with the previous solution
rescaled (r_p ~ 1/eps, v_p ~ sqrt(eps)) as the start of the next stage, (ii) step halving that keeps r_p, v_p > 0 and
lowers |F|, and (iii) a final convergence check (raise instead of returning a non-converged iterate). Run on the grid
of s10 (nu = 0.25); j <= 1 as in the engine. Reviewer's prototype only; not engine code.

Run: python3 s10c_continuation_prototype.py
"""
import argparse
import math

import numpy as np

from lfphys.core.gravity import pn_binary as P


def F(z, eps, j, nu, order=2):
    x = np.array([z[0], 0.0, 0.0])
    v = np.array([0.0, z[1], 0.0])
    E = P.energy(x, v, nu, order)
    J = P.angular_momentum(x, v, nu, order)[2]
    return np.array([-2.0 * E / eps - 1.0, -2.0 * E * J * J / j - 1.0])


def newton(y, eps, j, nu):
    f = F(y, eps, j, nu).real
    for _ in range(80):
        Jm = np.empty((2, 2))
        for k in range(2):
            hk = 1e-30 * abs(y[k])
            yc = y.astype(complex)
            yc[k] += 1j * hk
            Jm[:, k] = F(yc, eps, j, nu).imag / hk
        dy = np.linalg.solve(Jm, -f)
        lam = 1.0
        while lam > 1e-6:
            yn = y + lam * dy
            if yn[0] > 0 and yn[1] > 0:
                fn = F(yn, eps, j, nu).real
                if np.linalg.norm(fn) < np.linalg.norm(f) or np.linalg.norm(fn) < 1e-14:
                    break
            lam *= 0.5
        y, f = yn, fn
        if np.linalg.norm(f) < 1e-14:
            return y
    raise ValueError("not converged")


def solve(eps, j, nu):
    e = math.sqrt(max(1.0 - j, 0.0))
    e0 = min(eps, 1e-4)
    y = np.array([(1.0 - e) / e0, math.sqrt(e0 * (1.0 + e) / (1.0 - e))])
    y = newton(y, e0, j, nu)
    while e0 < eps:
        e1 = min(eps, 1.5 * e0)
        y = newton(np.array([y[0] * e0 / e1, y[1] * math.sqrt(e1 / e0)]), e1, j, nu)
        e0 = e1
    return y


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    nu = 0.25
    epss = [1e-4, 3e-4, 1e-3, 2e-3, 3e-3, 5e-3, 7e-3, 1e-2, 1.5e-2, 2e-2, 3e-2, 5e-2]
    js = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0]
    n_ok = n_bad = 0
    print("cell: '.' converged with the requested invariants (1e-12) at a periapsis (r_p < r of a quarter-period "
          "later); 'E' not converged; 'A' apoapsis")
    for eps in epss:
        line = []
        for j in js:
            try:
                y = solve(eps, j, nu)
                st = P.state(0.0, [y[0], 0, 0], [0, y[1], 0])
                gi = P.gauge_invariants(st["x"], st["v"], nu)
                ok = abs(gi["eps"] / eps - 1) < 1e-12 and abs(gi["j"] / j - 1) < 1e-12
                # periapsis: r grows right after the start
                a = P.acceleration(st["x"], st["v"], nu, (1, 2))
                peri = float(st["x"] @ a + st["v"] @ st["v"]) > 0  # d^2(r^2/2)/dt^2 > 0 at rdot = 0
                c = "." if (ok and peri) else ("A" if ok else "E")
            except ValueError:
                c = "E"
            n_ok += c == "."
            n_bad += c != "."
            line.append(c)
        print(f"  eps={eps:<7g} " + " ".join(f"{c:>4}" for c in line))
    print(f"{n_ok} of {n_ok + n_bad} cells converged to the periapsis state")


if __name__ == "__main__":
    main()
