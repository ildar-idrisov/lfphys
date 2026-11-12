"""04: Schwarzschild periapsis advance and light deflection, Kerr circular orbits, against independent 40-digit
mpmath routes (defining integrals; numerically solved R = R' = 0 for Kerr). Usage: python3 04_gravity.py
"""
import argparse
import math

argparse.ArgumentParser(description=__doc__).parse_args()

import mpmath as mp

from lfphys.core.constants import C, GM_SUN, R_SUN
from lfphys.core.gravity import kerr, orbits
from lfphys.core.gravity import schwarzschild as S

mp.mp.dps = 40

print("=== periapsis advance: defining integral 2 int_{u1}^{u2} du / sqrt(f(u)) - 2 pi (u = M/r) ===")


def adv_ref(u1, u2):
    u1, u2 = mp.mpf(u1), mp.mpf(u2)
    u3 = mp.mpf(1) / 2 - u1 - u2
    g = lambda ch: 2 * (u2 - u1) * mp.sin(ch) * mp.cos(ch) / mp.sqrt(  # noqa: E731
        2 * ((u2 - u1) * mp.sin(ch) ** 2) * ((u2 - u1) * mp.cos(ch) ** 2) * (u3 - u1 - (u2 - u1) * mp.sin(ch) ** 2))
    return 2 * mp.quad(g, [0, mp.pi / 4, mp.pi / 2]) - 2 * mp.pi


M = GM_SUN / C**2
a, ecc = 57.909e9, 0.2056
cases = [(1 / 30.0, 1 / 12.0), (1 / 60.0, 1 / 9.0), (1 / 1e3, 1 / 200.0), (1 / 1e5, 1 / 3e4),
         (M / (a * (1 + ecc)), M / (a * (1 - ecc)))]
for u1, u2 in cases:
    ref = adv_ref(u1, u2)
    val = orbits.advance_from_turning(u1, u2)
    print(f"r_apo/M={1/u1:.4g} r_peri/M={1/u2:.4g}: advance_from_turning rel. err {float(abs(val / ref - 1)):.2e}")

# periapsis_advance(e, l): turning points by np.roots of the cubic and e^2 - 1 formed from e
print("\nperiapsis_advance(e, l) (roots by np.roots, e^2-1 from e):")
for u1, u2 in cases:
    U1, U2 = mp.mpf(u1), mp.mpf(u2)
    U3 = mp.mpf(1) / 2 - U1 - U2
    l = 1 / mp.sqrt(U1 * U2 + U1 * U3 + U2 * U3)
    e = mp.sqrt(1 - 2 * U1 * U2 * U3 * l * l)
    try:
        val = orbits.periapsis_advance(float(e), float(l))
        print(f"  r_apo/M={1/u1:.4g}: rel. err {float(abs(val / adv_ref(u1, u2) - 1)):.2e}")
    except Exception as ex:  # noqa: BLE001
        print(f"  r_apo/M={1/u1:.4g}: raises {type(ex).__name__}: {ex}")

print("\n=== light deflection: 2 int_0^{u0} du / sqrt(1/b^2 - u^2 + rs u^3) - pi (rs = 1) ===")


def defl_ref(b):
    b = mp.mpf(b)
    # u0: smallest positive root of u^3 - u^2 + 1/b^2
    rts = mp.polyroots([1, -1, 0, 1 / b**2], maxsteps=200, extraprec=200)
    u0 = min(mp.re(z) for z in rts if abs(mp.im(z)) < mp.mpf(10) ** -30 and mp.re(z) > 0)
    q1 = u0 - 1
    f = lambda s: 2 * mp.sqrt(u0) / mp.sqrt(-(u0 * (1 - s * s)) ** 2 - q1 * u0 * (1 - s * s) - q1 * u0)  # noqa: E731
    return 2 * mp.quad(f, [0, 0.5, 0.9, 0.99, 1]) - mp.pi


bc = 1.5 * math.sqrt(3.0)
for bb in (bc * (1 + 1e-6), bc * 1.001, 2.7, 4.0, 50.0, 1e5, R_SUN / (2 * M), 1e7, 1e9):
    ref = defl_ref(bb)
    val = S.deflection_from_quadrature(bb, 1.0, 1.0)
    print(f"b/rs = {bb:.6g}: deflection {float(ref):.10e}  quadrature rel. err {float(abs(val / ref - 1)):.2e}")

print("\n=== Kerr: ISCO from dE/dr = 0 with (E, L) solved numerically from R = R' = 0 (no closed form used) ===")


def circ_EL(r, x, pro):
    r, x = mp.mpf(r), mp.mpf(x)
    E0, L0 = kerr.circular_e_l(float(r), float(x), pro)  # starting guess only

    def R(rr, E, L):
        D = rr * rr - 2 * rr + x * x
        return (E * (rr * rr + x * x) - x * L) ** 2 - D * (rr * rr + (L - x * E) ** 2)
    eqs = lambda E, L: [R(r, E, L), mp.diff(lambda rr: R(rr, E, L), r)]  # noqa: E731
    E, L = mp.findroot(eqs, (mp.mpf(E0) * (1 + 1e-6), mp.mpf(L0) * (1 + 1e-6)))
    return E, L


for x in (0.0, 0.5, 0.9, 0.998):
    for pro in (True, False):
        guess = kerr.isco(x, pro)
        r_ref = mp.findroot(lambda rr: mp.diff(lambda q: circ_EL(q, x, pro)[0], rr), guess * (1 + 1e-4))
        E_ref = circ_EL(r_ref, x, pro)[0]
        print(f"chi={x} {'pro ' if pro else 'retro'}: isco rel. err {float(abs(kerr.isco(x, pro) / r_ref - 1)):.1e}, "
              f"efficiency {1 - float(E_ref):.12f} vs engine {kerr.efficiency(x, pro):.12f}")
