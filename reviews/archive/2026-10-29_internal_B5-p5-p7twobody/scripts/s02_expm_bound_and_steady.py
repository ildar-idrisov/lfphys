"""P5 review, check 2: ``propagate`` / ``expm_error_bound`` and ``steady_state`` on hard generators.

(a) expm route against 40-digit mpmath for stiff generators (rates over 6 decades), long times and a thermal
    oscillator (d = 8): is the stated bound respected, and how loose is it?
(b) the 'eig' route next to the Liouvillian's exceptional point: accepted while cond(V) <= max_cond; its actual error.
(c) steady_state: err_bound honesty on near-degenerate generators (slow decay, metastability), and a larger d
    (thermal ladder, d = 20) against the closed form.

Run: python3 s02_expm_bound_and_steady.py
"""
import argparse
import math

import mpmath as mp
import numpy as np
from scipy import linalg

from lfphys.core.quantum import open_systems as OS, two_level as TL


@mp.workdps(40)
def mp_prop(Lsup, rho0, t):
    Lm = mp.matrix([[mp.mpc(complex(x)) for x in row] for row in Lsup])
    v = mp.matrix([mp.mpc(complex(x)) for x in OS.vec(rho0)])
    w = mp.expm(Lm * mp.mpf(t)) * v
    return np.array([complex(w[i]) for i in range(len(v))])


def thermal(N, nth, kap, w=1.0, F=0.0):
    a = np.diag(np.sqrt(np.arange(1, N)), 1).astype(complex)
    H = w * a.conj().T @ a + F * (a + a.conj().T)
    return H, [math.sqrt(kap * (1 + nth)) * a, math.sqrt(kap * nth) * a.conj().T]


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    print("(a) expm route against 40-digit mpmath")
    cases = {
        "OBE stiff Gamma=1e4, Omega=1, T2=2T1": OS.liouvillian(TL.hamiltonian(1.0, 0.3), TL.collapse_operators(1e-4, 2e-4)),
        "OBE Gamma=1e-3, Omega=50 (underdamped, long)": OS.liouvillian(TL.hamiltonian(50.0, 3.0), TL.collapse_operators(1e3, 1e3)),
        "thermal oscillator N=8 nth=2 kappa=0.5 drive": OS.liouvillian(*thermal(8, 2.0, 0.5, 1.0, 0.7)),
    }
    for name, Ls in cases.items():
        d = math.isqrt(Ls.shape[0])
        rho0 = np.zeros((d, d), complex)
        rho0[0, 0] = 1.0
        for t in (1.0, 100.0, 1e4):
            ex = mp_prop(Ls, rho0, t)
            a = OS.vec(OS.propagate(Ls, rho0, [t])[0])
            err = OS.trace_norm(OS.unvec(a - ex, d))
            b = OS.expm_error_bound(Ls, t)
            print(f"  {name}; t={t:g}: trace-norm error {err:.2e}, bound {b:.2e}, ratio {err / b:.1e}")

    print("(b) 'eig' route near the Liouvillian exceptional point Omega = Gamma/4 (Delta = 0, T2 = 2 T1)")
    rho0 = TL.density_matrix([0, 0, -1])
    for dOm in (1e-2, 1e-4, 1e-6, 1e-8):
        Ls = OS.liouvillian(TL.hamiltonian(0.25 + dOm, 0.0), TL.collapse_operators(1.0, 2.0))
        lam, V = linalg.eig(Ls)
        c = np.linalg.cond(V)
        t = 3.0
        ex = mp_prop(Ls, rho0, t)
        try:
            b = OS.vec(OS.propagate(Ls, rho0, [t], method="eig")[0])
            e = float(np.max(np.abs(b - ex)))
            print(f"  Omega = 0.25 + {dOm:g}: cond(V) {c:.2e}, eig route accepted, max error {e:.2e}")
        except ValueError:
            print(f"  Omega = 0.25 + {dOm:g}: cond(V) {c:.2e}, eig route refused (max_cond 1e8)")

    print("(c) steady_state: err_bound against the exact steady state")
    for G in (1e-3, 1e-6, 1e-9, 1e-11):
        # weakly decaying, strongly driven atom: unique steady state, slow relaxation
        Om, De, T1, T2 = 1.0, 0.5, 1 / G, 2 / G
        try:
            rho, info = OS.steady_state(TL.hamiltonian(Om, De), TL.collapse_operators(T1, T2))
            ex = TL.density_matrix(TL.bloch_steady_state(Om, De, T1, T2))
            err = float(np.linalg.norm(rho - ex))
            print(f"  Gamma={G:g}: s_next/s_max {info['s_next'] / info['s_max']:.1e}, error_F {err:.2e}, "
                  f"err_bound {info['err_bound']:.2e} -> {'OK' if err <= info['err_bound'] else 'BOUND VIOLATED'}")
        except ValueError as e:
            print(f"  Gamma={G:g}: refused: {e}")
    for N, nth in ((20, 0.5), (30, 3.0)):
        H, c = thermal(N, nth, 1.0)
        rho, info = OS.steady_state(H, c)
        q = nth / (1 + nth)
        p = q ** np.arange(N)
        ex = np.diag(p / p.sum())
        err = float(np.linalg.norm(rho - ex))
        print(f"  thermal ladder N={N} nth={nth}: error_F {err:.2e}, err_bound {info['err_bound']:.2e} "
              f"(truncated ladder: exact closed form)")


if __name__ == "__main__":
    main()
