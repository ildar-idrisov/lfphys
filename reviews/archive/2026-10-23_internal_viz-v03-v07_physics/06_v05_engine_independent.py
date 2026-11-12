"""v05 engine: lfphys.core.optics.interfaces.stack (Abeles matrices, rewritten 2026-10-23) against an independent
route written here: Rouard's recursion (the reflection of the stack is built from the substrate outwards, one Airy
summation per layer, with complex Fresnel coefficients of B&W convention); transmission from the same recursion.
Then the closed forms of lfphys.core.optics.thin_films against Rouard: Bragg (both layer orders), FTIR (s, p),
Airy intensity with n0 != ns, quarter-wave AR; Brewster and critical angles.
Output: out/06_v05_engine_independent.txt
"""
import cmath
import math

import numpy as np

from lfphys.core.optics import interfaces as IF
from lfphys.core.optics import thin_films as TF

OUT = open("out/06_v05_engine_independent.txt", "w")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.write(s + "\n")
    OUT.flush()


def cosines(ns, th0):
    s0 = ns[0] * math.sin(th0)
    out = []
    for n in ns:
        c = cmath.sqrt(1 - (s0 / n) ** 2)
        if (n * c).imag < 0 or ((n * c).imag == 0 and (n * c).real < 0):
            c = -c
        out.append(c)
    return out


def rouard(ns, ds, lam, th0, pol):
    """Rouard recursion. Interface coefficients (B&W): s: r = (n1c1 - n2c2)/(n1c1 + n2c2), t = 2n1c1/(...);
    p: r = (n2c1 - n1c2)/(n2c1 + n1c2), t = 2n1c1/(n2c1 + n1c2). Returns r, t (field ratios in the same convention)
    and R, T (T with the Poynting factor)."""
    ns = [complex(n) for n in ns]
    cs = cosines(ns, th0)

    def rt(i):
        n1, c1, n2, c2 = ns[i], cs[i], ns[i + 1], cs[i + 1]
        if pol == "s":
            den = n1 * c1 + n2 * c2
            return (n1 * c1 - n2 * c2) / den, 2 * n1 * c1 / den
        den = n2 * c1 + n1 * c2
        return (n2 * c1 - n1 * c2) / den, 2 * n1 * c1 / den
    N = len(ns)
    r, t = rt(N - 2)
    for j in range(N - 3, -1, -1):  # interface j between ns[j] and ns[j+1]; layer j+1 has thickness ds[j]
        r01, t01 = rt(j)
        # reverse coefficients at the same interface (from ns[j+1] to ns[j])
        n1, c1, n2, c2 = ns[j + 1], cs[j + 1], ns[j], cs[j]
        if pol == "s":
            den = n1 * c1 + n2 * c2
            r10, t10 = (n1 * c1 - n2 * c2) / den, 2 * n1 * c1 / den
        else:
            den = n2 * c1 + n1 * c2
            r10, t10 = (n2 * c1 - n1 * c2) / den, 2 * n1 * c1 / den
        beta = 2 * math.pi * ns[j + 1] * cs[j + 1] * ds[j] / lam
        e1, e2 = cmath.exp(1j * beta), cmath.exp(2j * beta)
        den = 1 - r10 * r * e2
        r_new = r01 + t01 * t10 * r * e2 / den
        t_new = t01 * t * e1 / den
        r, t = r_new, t_new
    n0, c0, nsb, cb = ns[0], cs[0], ns[-1], cs[-1]
    if pol == "s":
        fac = (nsb * cb).real / (n0 * c0).real
    else:
        fac = (nsb * cb.conjugate()).real / (n0 * c0.conjugate()).real
    return r, t, abs(r) ** 2, fac * abs(t) ** 2


rng = np.random.default_rng(20261023)
worst = {"r": 0.0, "t": 0.0, "R": 0.0, "T": 0.0}
where = {}
for trial in range(4000):
    nl = int(rng.integers(1, 7))
    n0 = float(rng.choice([1.0, 1.5, rng.uniform(1, 4)]))
    nsub = float(rng.uniform(1, 4))
    ns = [n0]
    for _ in range(nl):
        if rng.random() < 0.25:
            ns.append(complex(rng.uniform(0.05, 3), rng.uniform(0, 6)))
        else:
            ns.append(float(rng.uniform(1, 4)))
    ns.append(nsub)
    ds = list(rng.uniform(1, 800, nl))
    lam = float(rng.uniform(300, 1600))
    th = math.radians(float(rng.uniform(0, 89.9)))
    for pol in ("s", "p"):
        a = IF.stack(ns, ds, lam, th, pol)
        r, t, R, T = rouard(ns, ds, lam, th, pol)
        # Rouard's t is the ratio of the forward amplitude in the exit medium; for p the engine's t is "the ratio of
        # the total E amplitudes" (docstring) - compare |t| scaled by the same convention as fresnel's t_p
        for k, v1, v2 in (("r", a["r"], r), ("R", a["R"], R), ("T", a["T"], T), ("t", a["t"], t)):
            d = abs(v1 - v2) / max(1e-300, max(abs(v2), 1e-12))
            if d > worst[k]:
                worst[k], where[k] = d, (ns, ds, lam, math.degrees(th), pol, v1, v2)
say("A. interfaces.stack vs Rouard recursion, 4000 random stacks (1-6 layers, 25 % absorbing, 0-89.9 deg), s and p:")
for k in worst:
    say(f"   max relative |difference| of {k}: {worst[k]:.2e}")
    if worst[k] > 1e-8:
        say(f"     at {where[k]}")

say("")
say("B. grazing inside an inner lossless layer (n0 sin th = n_j), exact and +-1e-12 rad: stack vs Rouard")
for (n0, nj, nsb, d) in ((1.5, 1.0, 1.5, 200.0), (2.0, 1.5, 1.0, 300.0), (3.0, 1.2, 2.0, 1000.0)):
    thg = math.asin(nj / n0)
    for off in (0.0, 1e-12, -1e-12, 1e-9, 1e-6):
        for pol in ("s", "p"):
            a = IF.stack([n0, nj, nsb], [d], 633.0, thg + off, pol)
            try:
                r, t, R, T = rouard([n0, nj, nsb], [d], 633.0, thg + off, pol)
            except ZeroDivisionError:
                R = T = float("nan")  # the Airy recursion is singular exactly at grazing (0/0); the engine is not
            say(f"   n0={n0}, n_j={nj}, n_s={nsb}, d={d}, th_g{off:+.0e}, {pol}: stack R={a['R']:.15f} T={a['T']:.3e}"
                f" | Rouard R={R:.15f} T={T:.3e} | R+T-1 (stack) = {a['R'] + a['T'] - 1:.1e}")

say("")
say("C. closed forms of thin_films against Rouard")
for N in (1, 4, 8, 15):
    nH, nL, n0, nsb, lam0 = 2.3, 1.45, 1.0, 1.52, 550.0
    lay = []
    for _ in range(N):
        lay += [nH, nL]
    ds = [lam0 / (4 * n) for n in lay]
    R_HL = rouard([n0] + lay + [nsb], ds, lam0, 0.0, "s")[2]
    lay2 = [nL if x == nH else nH for x in lay]
    R_LH = rouard([n0] + lay2 + [nsb], [lam0 / (4 * n) for n in lay2], lam0, 0.0, "s")[2]
    cfA = TF.quarter_wave_stack_R(n0, nH, nL, nsb, N)   # H next to the incidence medium (engine's order)
    cfB = TF.quarter_wave_stack_R(n0, nL, nH, nsb, N)   # L next to the incidence medium
    say(f"   Bragg N={N}: Rouard (H L)^N: 1-R = {1 - R_HL:.6e}, closed form (A=H): {1 - cfA:.6e}; "
        f"Rouard (L H)^N: 1-R = {1 - R_LH:.6e}, closed form (A=L): {1 - cfB:.6e}")
for pol in ("s", "p"):
    for th_deg in (42.0, 45.0, 60.0, 80.0, 89.0):
        for gap in (50.0, 200.0, 1000.0):
            th = math.radians(th_deg)
            cf = TF.ftir_T(1.5, 1.0, gap, 633.0, th, pol)
            T = rouard([1.5, 1.0, 1.5], [gap], 633.0, th, pol)[3]
            if abs(cf - T) > 1e-12 * max(T, 1e-300) + 1e-15:
                say(f"   FTIR MISMATCH {pol} th={th_deg} gap={gap}: closed {cf:.15e} Rouard {T:.15e}")
    say(f"   FTIR {pol}: closed form = Rouard to 1e-12 relative at 15 angle/gap pairs unless a mismatch is printed")
dev = 0.0
for n0, n1, n2 in ((1.0, 2.3, 1.5), (1.5, 2.3, 1.0), (1.0, 1.38, 1.5), (2.0, 4.0, 1.2)):
    for th_deg in (0.0, 20.0, 40.0):
        for lam in np.linspace(400, 1500, 57):
            th = math.radians(th_deg)
            if n0 * math.sin(th) >= min(n1, n2):
                continue
            for pol in ("s", "p"):
                a = TF.airy(n0, n1, n2, 2000.0, lam, th, pol)["T"]
                T = rouard([n0, n1, n2], [2000.0], lam, th, pol)[3]
                dev = max(dev, abs(a - T))
say(f"   Airy intensity formula (n0 != ns allowed) vs Rouard: max |dT| = {dev:.2e}")
say(f"   Brewster: interfaces.brewster(1,1.5) = {math.degrees(IF.brewster(1, 1.5)):.12f} deg; "
    f"|r_p| there (Rouard) = {abs(rouard([1, 1.5], [], 633, IF.brewster(1, 1.5), 'p')[0]):.1e}")
say(f"   critical: interfaces.critical(1.5,1) = {math.degrees(IF.critical(1.5, 1)):.12f} deg = asin(2/3)")
say(f"   B&W sign: r_s(0) = {IF.fresnel(1, 1.5, 0.0, 's')[0]:.6f}, r_p(0) = {IF.fresnel(1, 1.5, 0.0, 'p')[0]:.6f} "
    "(B&W: r_p = -r_s at normal incidence, r_p = tan(ti - tt)/tan(ti + tt))")
ti = math.radians(30)
tt = math.asin(math.sin(ti) / 1.5)
say(f"   r_p(30 deg) engine {IF.fresnel(1, 1.5, ti, 'p')[0].real:.15f} vs tan form {math.tan(ti - tt) / math.tan(ti + tt):.15f}")
say(f"   r_s(30 deg) engine {IF.fresnel(1, 1.5, ti, 's')[0].real:.15f} vs -sin form {-math.sin(ti - tt) / math.sin(ti + tt):.15f}")
