"""06: multilayer optics of lfphys.core.optics.interfaces.stack (Abeles matrices, rewritten 2026-10-23) and
thin_films.ftir_T against an independent route: direct solution of the boundary-value problem for the amplitudes of
the forward and backward waves in every medium (s: E_y continuous, H_x ~ k_z E; p: H_y continuous, E_x ~ (k_z/eps) H),
with phases referenced at the boundary each wave starts from (no overflow for thick evanescent layers), and the
transmitted power from the Poynting flux S_z of the computed fields. p: r = H_r/H_i (equals the Born & Wolf r_p),
t = E_t/E_i. 2000 random stacks (absorbing, evanescent, grazing), plus targeted cases. Usage: python3 06_optics_stack.py
"""
import argparse
import cmath
import math

argparse.ArgumentParser(description=__doc__).parse_args()

import numpy as np

from lfphys.core.optics import interfaces, thin_films as tf


def kz_branch(n, s0):
    q = cmath.sqrt(n * n - s0 * s0)
    if q.imag < 0 or (q.imag == 0 and q.real < 0):
        q = -q
    return q  # k_z / k0, decaying or forward


def solve(ns, ds, lam, th, pol):
    ns = [complex(n) for n in ns]
    k0 = 2 * math.pi / lam
    s0 = ns[0] * math.sin(th)
    q = [kz_branch(n, s0) for n in ns]
    # admittance-like factor relating the 'other' tangential field to the amplitude: s: H_x ~ q A; p: E_x ~ q/n^2 A
    y = [qq if pol == "s" else qq / (n * n) for qq, n in zip(q, ns)]
    N = len(ns)
    # unknowns: A_0..A_{N-1} (forward, referenced at the left boundary of medium j), B_0..B_{N-1} (backward,
    # referenced at the right boundary). A_0 = 1, B_{N-1} = 0. Medium 0: right boundary at z = 0.
    nunk = 2 * N
    M = np.zeros((nunk + 2, nunk), complex)
    rhs = np.zeros(nunk + 2, complex)
    row = 0
    M[row, 0] = 1.0; rhs[row] = 1.0; row += 1          # A_0 = 1
    M[row, N + N - 1] = 1.0; row += 1                  # B_{N-1} = 0
    for j in range(N - 1):
        dj = 0.0 if j == 0 else ds[j - 1]
        ph = cmath.exp(1j * k0 * q[j] * dj) if j > 0 else 1.0  # forward wave of medium j at its right boundary
        # medium 0: forward referenced at z = 0 (its right boundary); treat its 'left boundary' as z = 0 as well
        if j == 0:
            ph = 1.0
        eB_next = cmath.exp(1j * k0 * q[j + 1] * (ds[j] if j + 1 < N - 1 else 0.0))  # backward of j+1 at its left
        # field continuity:  A_j ph + B_j = A_{j+1} + B_{j+1} eB_next
        M[row, j] = ph; M[row, N + j] = 1.0; M[row, j + 1] = -1.0; M[row, N + j + 1] = -eB_next; row += 1
        # other tangential field: y_j (A_j ph - B_j) = y_{j+1} (A_{j+1} - B_{j+1} eB_next)
        M[row, j] = y[j] * ph; M[row, N + j] = -y[j]; M[row, j + 1] = -y[j + 1]
        M[row, N + j + 1] = y[j + 1] * eB_next; row += 1
    sol = np.linalg.lstsq(M, rhs, rcond=None)[0]
    r = sol[N + 0]
    tA = sol[N - 1]
    if pol == "s":
        t = tA
        T = (q[-1]).real / (q[0]).real * abs(tA) ** 2
    else:
        t = tA * ns[0] / ns[-1]          # E amplitude = H amplitude / n (impedance units)
        T = (q[-1] / ns[-1] ** 2).real / (q[0] / ns[0] ** 2).real * abs(tA) ** 2
    return complex(r), complex(t), abs(r) ** 2, float(T)


rng = np.random.default_rng(7)
worst = {"r": 0.0, "t": 0.0, "R": 0.0, "T": 0.0}
for it in range(2000):
    nl = int(rng.integers(0, 6))
    n_in = float(rng.uniform(1.0, 2.0))
    ns = [n_in] + [complex(rng.uniform(1.0, 3.5), rng.choice([0.0, 0.0, rng.uniform(0, 4)])) for _ in range(nl)]
    ns += [complex(rng.uniform(1.0, 3.5), rng.choice([0.0, rng.uniform(0, 3)]))]
    ds = list(rng.uniform(5.0, 400.0, nl))
    lam = 633.0
    th = float(rng.uniform(0, math.pi / 2 * 0.999))
    for pol in "sp":
        st = interfaces.stack(ns, ds, lam, th, pol)
        r, t, R, T = solve(ns, ds, lam, th, pol)
        worst["r"] = max(worst["r"], abs(st["r"] - r))
        worst["t"] = max(worst["t"], abs(st["t"] - t) / max(1.0, abs(t)))
        worst["R"] = max(worst["R"], abs(st["R"] - R))
        worst["T"] = max(worst["T"], abs(st["T"] - T))
print("2000 random stacks x 2 polarisations, max |difference| stack vs boundary-value solve:")
print("  ", {k: f"{v:.1e}" for k, v in worst.items()})

print("\nB&W sign at normal incidence (n 1 -> 1.5): r_s, r_p =",
      interfaces.stack([1, 1.5], [], 1.0, 0.0, "s")["r"], interfaces.stack([1, 1.5], [], 1.0, 0.0, "p")["r"])

print("\nthick evanescent gap (n 1.5 | 1.0, d | 1.5) at 60 deg, s and p (the reference solver's own floor is ~1e-31:")
print("lstsq conditioning; only the d = 1000 row compares values; the rest checks that the engine returns at all):")
for d in (1e3, 1e4, 3e4, 8e4, 1e5, 3e5):
    for pol in "sp":
        kd = 2 * math.pi / 633.0 * math.sqrt(1.5**2 * math.sin(math.radians(60)) ** 2 - 1) * d
        try:
            st = interfaces.stack([1.5, 1.0, 1.5], [d], 633.0, math.radians(60), pol)
            s1 = f"stack T={st['T']:.3e} R={st['R']:.15f}"
        except Exception as ex:  # noqa: BLE001
            s1 = f"stack RAISES {type(ex).__name__}: {ex}"
        try:
            s2 = f"ftir_T={tf.ftir_T(1.5, 1.0, d, 633.0, math.radians(60), pol):.3e}"
        except Exception as ex:  # noqa: BLE001
            s2 = f"ftir_T RAISES {type(ex).__name__}: {ex}"
        print(f"  d={d:g} nm (kappa d = {kd:.0f}) {pol}: {s1}; {s2}")

print("\nftir_T across the critical angle (n1 = 1.5, gap 1.0, d = 300 nm), relative difference to the reference:")
thc = math.asin(1 / 1.5)
for dth in (-1e-2, -1e-6, -1e-12, 0.0, 1e-12, 1e-6, 1e-2):
    th = thc + dth
    for pol in "sp":
        r, t, R, T = solve([1.5, 1.0, 1.5], [300.0], 633.0, th, pol)
        f = tf.ftir_T(1.5, 1.0, 300.0, 633.0, th, pol)
        print(f"  dtheta={dth:+.0e} {pol}: {abs(f / T - 1):.1e}", end="")
    print()
print("(at dtheta = 0 the plane-wave basis of the reference degenerates (k_z = 0 in the gap: the field is linear in z),")
print(" so the reference is invalid there; compare ftir_T with stack instead:)")
for pol in "sp":
    st = interfaces.stack([1.5, 1.0, 1.5], [300.0], 633.0, thc, pol)
    f = tf.ftir_T(1.5, 1.0, 300.0, 633.0, thc, pol)
    print(f"  theta_c {pol}: ftir_T {f:.15f}  stack {st['T']:.15f}  rel {abs(f / st['T'] - 1):.1e}")
