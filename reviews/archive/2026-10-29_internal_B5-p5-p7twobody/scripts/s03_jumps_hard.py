"""P5 review, check 3: quantum-jump trajectories (``jumps.trajectories``) on cases the tests do not cover.

(a) coarse output grid: many jumps inside one output interval (the inner while-loop), thermal oscillator N = 6 with
    two channels (a and a^+) and a coherent drive, against the master equation at z = 5;
(b) a Lambda system with a dark state (trajectories end in the dark state), against the master equation;
(c) a long interval with strong decay (the unnormalised norm underflows inside the interval);
(d) the eig route near the exceptional point of H_eff (cond(V) just below the switch 1e4) - waiting times vs closed form;
(e) time-step independence: the same seed and physics with output grids of 5 and 401 points give the same law
    (two-sample KS on the final populations is not informative; instead compare <P_e(T)> means at z = 5).

Run: python3 s03_jumps_hard.py
"""
import argparse
import math
import time

import numpy as np

from lfphys.core.quantum import jumps as J, open_systems as OS, two_level as TL

Z = 5.0


def zcheck(name, tr, ex_vals, k=0):
    m, s = tr.mean(k), tr.stderr(k)
    z = np.abs(m - ex_vals) / np.maximum(s, 1e-300)
    z[s == 0] = 0.0
    print(f"  {name}: max |z| = {np.max(z):.2f} over {z.size} points -> {'OK' if np.max(z) <= Z else 'FAIL'}")


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    rng = np.random.default_rng(101)
    # (a) thermal oscillator with drive, coarse grid
    N, kap, nth, F = 6, 1.0, 0.8, 0.6
    a = np.diag(np.sqrt(np.arange(1, N)), 1).astype(complex)
    H = 0.4 * a.conj().T @ a + F * (a + a.conj().T)
    c = [math.sqrt(kap * (1 + nth)) * a, math.sqrt(kap * nth) * a.conj().T]
    psi0 = np.zeros(N, complex)
    psi0[0] = 1
    ts = np.array([0.0, 5.0, 20.0])
    nop = a.conj().T @ a
    t0 = time.time()
    tr = J.trajectories(H, c, psi0, ts, 4000, rng, e_ops=[nop])
    njumps = np.mean([len(x) for x in tr.jump_times])
    ex = OS.propagate(OS.liouvillian(H, c), np.outer(psi0, psi0.conj()), ts)
    print(f"(a) thermal oscillator, coarse grid: mean jumps per trajectory {njumps:.1f} over 2 intervals "
          f"({time.time()-t0:.1f} s)")
    zcheck("<n>", tr, np.real([np.trace(nop @ r) for r in ex]))

    # (b) Lambda system with dark state
    e, g1, g2 = np.eye(3, dtype=complex)
    O1, O2, De = 1.1, 0.7, 0.0
    H = -De * np.outer(e, e) + 0.5 * O1 * (np.outer(e, g1) + np.outer(g1, e)) + 0.5 * O2 * (np.outer(e, g2)
                                                                                         + np.outer(g2, e))
    c = [math.sqrt(0.6) * np.outer(g1, e), math.sqrt(0.9) * np.outer(g2, e)]
    ts = np.linspace(0, 40, 9)
    tr = J.trajectories(H, c, g1, ts, 4000, rng, e_ops=[np.outer(g1, g1), np.outer(e, e)])
    ex = OS.propagate(OS.liouvillian(H, c), np.outer(g1, g1), ts)
    print("(b) Lambda system with a dark state")
    zcheck("P_g1", tr, np.real(ex[:, 1, 1]), 0)
    zcheck("P_e", tr, np.real(ex[:, 0, 0]), 1)

    # (c) strong decay over a long interval: norm underflow inside the interval
    G = 50.0
    t0 = time.time()
    tr = J.trajectories(TL.hamiltonian(3.0, 0.0), [math.sqrt(G) * TL.SM], TL.G, [0.0, 60.0], 300, rng,
                        e_ops=[TL.PE])
    ex = OS.propagate(OS.liouvillian(TL.hamiltonian(3.0, 0.0), [math.sqrt(G) * TL.SM]), TL.density_matrix([0, 0, -1]),
                      [0.0, 60.0])
    nj = np.mean([len(x) for x in tr.jump_times])
    print(f"(c) Gamma = 50, one interval of 60 (Gamma dt = 3000): {nj:.0f} jumps per trajectory, "
          f"{time.time()-t0:.1f} s")
    zcheck("P_e(60)", tr, np.real(ex[:, 0, 0]))

    # (d) eig route near the H_eff exceptional point Omega = Gamma/2
    Gm = 1.0
    for dOm in (1e-3, 2e-5):
        Om = 0.5 * Gm + dOm
        Heff = J.effective_hamiltonian(TL.hamiltonian(Om, 0.0), [math.sqrt(Gm) * TL.SM])
        prop = J.NoJumpPropagator(Heff)
        cond = np.linalg.cond(np.linalg.eig(-1j * Heff)[1])
        Hs = np.zeros((3, 3), complex)
        Hs[:2, :2] = TL.hamiltonian(Om, 0.0)
        L = np.zeros((3, 3), complex)
        L[2, 0] = math.sqrt(Gm)
        T = 1.0
        while TL.no_emission_probability(T, Om, 0.0, Gm) > 1e-12:
            T *= 1.5
        tr = J.trajectories(Hs, [L], np.array([0, 1, 0], complex), [0.0, T], 6000, rng)
        wt = np.sort(tr.waiting_times(1, from_start=True))
        n = wt.size
        Fc = 1 - TL.no_emission_probability(wt, Om, 0.0, Gm)
        D = max(np.max(np.arange(1, n + 1) / n - Fc), np.max(Fc - np.arange(0, n) / n))
        eps = math.sqrt(math.log(2 / 1e-6) / (2 * n))
        print(f"(d) Omega = Gamma/2 + {dOm:g}: route {prop.route}, cond(V) {cond:.1e}, KS {D:.4f} vs DKW {eps:.4f} "
              f"-> {'OK' if D <= eps else 'FAIL'}")

    # (e) output grid independence
    H, c = TL.hamiltonian(2.0, 0.8), TL.collapse_operators(1.0, 1.2)
    T = 6.0
    ex = OS.propagate(OS.liouvillian(H, c), TL.density_matrix([0, 0, -1]), [T])[0]
    for npts in (2, 5, 401):
        tr = J.trajectories(H, c, TL.G, np.linspace(0, T, npts), 4000, np.random.default_rng(7), e_ops=[TL.PE])
        m, s = tr.mean(0)[-1], tr.stderr(0)[-1]
        print(f"(e) output grid of {npts} points: <P_e({T:g})> = {m:.4f} +- {s:.4f}, exact {ex[0, 0].real:.4f}, "
              f"z = {abs(m - ex[0, 0].real) / s:.2f}")


if __name__ == "__main__":
    main()
