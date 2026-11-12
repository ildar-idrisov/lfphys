"""P7 review, check 10: ``pn_binary.state_from_invariants`` over a grid of (eps, j): does the returned state have the
requested invariants? The function returns after 60 Newton iterations or on convergence and checks only that r_p
and v_p are positive; a diverged iteration is returned without an error.

Run: python3 s10_state_from_invariants_map.py
"""
import argparse

import numpy as np

from lfphys.core.gravity import pn_binary as P


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    nu = 0.25
    epss = [1e-4, 3e-4, 1e-3, 2e-3, 3e-3, 5e-3, 7e-3, 1e-2, 1.5e-2, 2e-2, 3e-2, 5e-2]
    js = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0]
    bad = []
    print("rows: eps; columns: j = " + " ".join(f"{j:g}" for j in js))
    print("cell: '.' invariants reproduced to 1e-10 at a periapsis; 'A' right invariants but an apoapsis (the docstring "
          "promises the periapsis); 'X' wrong state returned silently; 'E' error raised")
    for eps in epss:
        line = []
        for j in js:
            try:
                st = P.state_from_invariants(eps, j, nu)
                gi = P.gauge_invariants(st["x"], st["v"], nu)
                ok = abs(gi["eps"] / eps - 1) < 1e-10 and abs(gi["j"] / j - 1) < 1e-10
                a = P.acceleration(st["x"], st["v"], nu, (1, 2))
                peri = float(st["x"] @ a + st["v"] @ st["v"]) > 0  # d^2(r^2/2)/dt^2 > 0 at rdot = 0: a minimum of r
                line.append(("." if peri else "A") if ok else "X")
                if not ok:
                    bad.append((eps, j, float(st["x"][0]), gi["eps"], gi["j"]))
            except ValueError:
                line.append("E")
        print(f"  eps={eps:<7g} " + " ".join(f"{c:>4}" for c in line))
    print(f"{len(bad)} silent failures (X), e.g.:")
    for b in bad[:8]:
        print(f"  eps={b[0]:g} j={b[1]:g}: r_p = {b[2]:.3e}, eps(state) = {b[3]:.3e}, j(state) = {b[4]:.3e}")
    # all nu
    for nu in (0.1, 0.01):
        n_bad = 0
        for eps in epss:
            for j in js:
                try:
                    st = P.state_from_invariants(eps, j, nu)
                    gi = P.gauge_invariants(st["x"], st["v"], nu)
                    if not (abs(gi["eps"] / eps - 1) < 1e-10 and abs(gi["j"] / j - 1) < 1e-10):
                        n_bad += 1
                except ValueError:
                    pass
        print(f"nu={nu}: {n_bad} silent failures on the same grid")


if __name__ == "__main__":
    main()
