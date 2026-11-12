"""Review B8 (charges): reproduce the key claims of lfphys.core.em.charges with independent routes.

1. Heaviside's field at beta = 0.99 against the Lienard-Wiechert route (and against a 50-digit mpmath evaluation of
   the same physical field, independent of both double-precision formulas).
2. Lienard's power against the sphere integral of dP/dOmega (retarded time) by ADAPTIVE quadrature around the forward
   lobe (beta = 0.9, 0.99, 0.999), and the observer-time pattern against its own closed form for collinear motion.
3. The synchrotron spectrum: integral = Lienard power, sigma:pi = 7:1, fraction below omega_c.
Run: docker ... python3 /out/c01_charges_core.py
"""
import math
import sys

import mpmath as mp
import numpy as np
from scipy import integrate

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.em import charges as ch  # noqa: E402

Q = 1.602176634e-19
C = ch.C
mp.mp.dps = 50

print("== 1. Heaviside at beta = 0.99 ==")
rng = np.random.default_rng(11)
for beta_dir in ([0.99, 0, 0], [0, 0.7, 0.7 * 0.99 / 0.99]):
    bvec = np.array(beta_dir, float)
    bvec = 0.99 * bvec / np.linalg.norm(bvec)
    v = bvec * C
    w = ch.uniform([0.0, 0.0, 0.0], v)
    for t in (0.0, 3e-9, 1.0):  # t = 1 s: the charge 3e8 m away from its start; field points near its present position
        rp = w.position(np.array(t))
        pts = rp + rng.normal(size=(200, 3)) * np.array([1.0, 1.0, 1.0])
        # include points exactly ahead / behind / abeam
        vh = v / np.linalg.norm(v)
        pts[:3] = rp + np.array([vh * 2.0, -vh * 2.0, np.cross(vh, [0, 0, 1.0]) * 2.0 if abs(vh[2]) < 0.9 else
                                 np.cross(vh, [1.0, 0, 0]) * 2.0])
        try:
            E, B = ch.fields(ch.Charge(Q, w), pts, t)
        except Exception as exc:  # noqa: BLE001
            print(f"dir {np.round(vh, 3)} t = {t:g}: fields() raised {type(exc).__name__}: {exc}")
            continue
        Eh, Bh = ch.heaviside_field(Q, rp, v, pts)
        err = np.max(np.linalg.norm(E - Eh, axis=1) / np.linalg.norm(Eh, axis=1))
        errB = np.max(np.linalg.norm(B - Bh, axis=1) * C / np.linalg.norm(Eh, axis=1))
        print(f"dir {np.round(vh, 3)} t = {t:g}: max rel |E_LW - E_H| = {err:.2e}, c|B_LW - B_H|/|E_H| {errB:.2e}")

# 50-digit reference of the same field: retarded point of uniform motion solved exactly in mpmath
def heaviside_mp(q, v, rp, x):
    v = [mp.mpf(float(c)) for c in v]
    d = [mp.mpf(float(a)) - mp.mpf(float(b)) for a, b in zip(x, rp)]
    c = mp.mpf(C)
    b2 = sum(vi * vi for vi in v) / c ** 2
    R = mp.sqrt(sum(di * di for di in d))
    cospsi = sum(di * vi for di, vi in zip(d, v)) / (R * mp.sqrt(sum(vi * vi for vi in v)))
    s2 = 1 - cospsi ** 2
    k = mp.mpf(q) / (4 * mp.pi * mp.mpf(ch.EPS0))
    return [k * (1 - b2) * di / (R ** 3 * (1 - b2 * s2) ** mp.mpf(1.5)) for di in d]

print("\n-- double-precision cancellation at large gamma (uniform motion along x, field point ahead / abeam) --")
for gam in (1e2, 1e4, 1e6, 1e7):
    beta = math.sqrt(1 - 1 / gam ** 2)
    v = np.array([beta * C, 0, 0])
    w = ch.uniform([0, 0, 0], v)
    rp = w.position(np.array(0.0))
    for name, x in (("ahead", np.array([1.0, 0, 0])), ("abeam", np.array([0.0, 1.0, 0])),
                    ("oblique", np.array([1.0, 1e-3, 0]))):
        E, _ = ch.fields(ch.Charge(Q, w), x[None], 0.0)
        Eh, _ = ch.heaviside_field(Q, rp, v, x[None])
        Em = np.array([float(e) for e in heaviside_mp(Q, v, rp, x)])
        nm = np.linalg.norm(Em)
        print(f"gamma = {gam:.0e} {name:8s}: LW vs mp {np.linalg.norm(E[0] - Em) / nm:.2e}; "
              f"heaviside_field vs mp {np.linalg.norm(Eh[0] - Em) / nm:.2e}")

print("\n== 2. Lienard against the sphere integral of dP/dOmega (adaptive in the polar angle about beta) ==")


def sphere_adaptive(fun, axis_b):
    """int fun(n) dOmega with the polar axis along beta; theta adaptive (quad), phi Gauss-Legendre 64."""
    e3 = axis_b / np.linalg.norm(axis_b)
    tmp = np.array([1.0, 0, 0]) if abs(e3[0]) < 0.9 else np.array([0, 1.0, 0])
    e1 = np.cross(e3, tmp)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(e3, e1)
    xg, wg = np.polynomial.legendre.leggauss(64)
    ph = np.pi * (xg + 1)
    wph = np.pi * wg

    def ring(th):
        n = (np.sin(th) * (np.cos(ph)[:, None] * e1 + np.sin(ph)[:, None] * e2) + np.cos(th) * e3)
        return float(np.sum(wph * fun(n))) * math.sin(th)
    pts = sorted({1e-6, 1e-4, 1e-3, 1e-2, 0.03, 0.1, 0.3, 1.0})
    edges = [0.0] + pts + [math.pi]
    return sum(integrate.quad(ring, a, b, epsabs=0, epsrel=1e-12, limit=400)[0] for a, b in zip(edges[:-1], edges[1:]))


for beta in (0.9, 0.99, 0.999):
    for case in ("linear", "circular", "general"):
        if case == "linear":
            v, a = np.array([0, 0, beta * C]), np.array([0, 0, 1e18])
        elif case == "circular":
            v, a = np.array([beta * C, 0, 0]), np.array([0, 1e18, 0])
        else:
            u = np.array([0.5, 0.2, -0.3])
            v, a = beta * C * u / np.linalg.norm(u), np.array([3e17, -1e17, 2e17])
        P = ch.lienard_power(Q, v, a)
        Pi = sphere_adaptive(lambda n: ch.angular_power(Q, v, a, n, per="retarded"), v)
        Po = sphere_adaptive(lambda n: ch.angular_power(Q, v, a, n, per="observer"), v)
        line = f"beta = {beta}: {case:8s} int dP/dOmega(ret) / Lienard - 1 = {Pi / P - 1:+.2e}"
        if case == "linear":  # collinear: int (1-mu^2)/(1-b mu)^6 dmu closed form (mpmath) vs observer pattern
            b = mp.mpf(beta)
            I6 = mp.quad(lambda m: (1 - m * m) / (1 - b * m) ** 6, [-1, 1 - 1 / (1 / (1 - b)), 1])
            I5 = mp.quad(lambda m: (1 - m * m) / (1 - b * m) ** 5, [-1, 1])
            ratio = float(I6 / I5)
            line += f"; observer/retarded = {Po / Pi:.12g} (closed-form ratio {ratio:.12g})"
        print(line)

print("\n== 3. Synchrotron spectrum ==")
for gam, rho in ((2000.0, 10.0), (1e4, 100.0)):
    wc = ch.critical_frequency(gam, rho)
    f = lambda y, comp: ch.synchrotron_spectrum(Q, gam, rho, y * wc, comp) * wc  # noqa: E731
    parts = ((0, 1e-3), (1e-3, 1), (1, 10), (10, 60))
    tot = sum(integrate.quad(lambda y: f(y, "total"), a, b, limit=400, epsabs=0, epsrel=1e-13)[0] for a, b in parts)
    sig = sum(integrate.quad(lambda y: f(y, "sigma"), a, b, limit=400, epsabs=0, epsrel=1e-13)[0] for a, b in parts)
    pi_ = sum(integrate.quad(lambda y: f(y, "pi"), a, b, limit=400, epsabs=0, epsrel=1e-13)[0] for a, b in parts)
    below = sum(integrate.quad(lambda y: f(y, "total"), a, b, limit=400, epsabs=0, epsrel=1e-13)[0]
                for a, b in parts[:2])
    beta = math.sqrt(1 - 1 / gam ** 2)
    PL = ch.lienard_power(Q, np.array([beta * C, 0, 0]), np.array([0, beta * beta * C * C / rho, 0]))
    print(f"gamma = {gam:g}: int spectrum / Lienard - 1 = {tot / PL - 1:+.2e}; sigma/pi = {sig / pi_:.10f}; "
          f"(sigma+pi)/total - 1 = {(sig + pi_) / tot - 1:+.1e}; fraction below omega_c = {below / tot:.10f}")
# 25-digit fraction below omega_c for the record
mp.mp.dps = 25
F = lambda y: y * mp.quad(lambda s: mp.besselk(mp.mpf(5) / 3, s), [y, y + 1, mp.inf])  # noqa: E731
num = mp.quad(F, [0, 0.01, 0.3, 1])
den = mp.mpf(8) * mp.pi / (9 * mp.sqrt(3))
print("mpmath: int_0^1 F / int_0^inf F =", mp.nstr(num / den, 12))
