"""P7 review, check 6: theories.approx.peters_mathews on high eccentricity, small eccentricity and long runs.

(a) coalescence_time against a 30-digit mpmath quadrature of Peters' integral for e0 up to 0.9999;
(b) evolve: the conserved c0 along the track and the time to a_stop against coalescence_time, for e0 = 0.9, 0.99, 0.999;
(c) evolve with a tiny e0 (1e-6 .. 1e-10): relative accuracy of e (its absolute tolerance is 1e-15);
(d) the high-eccentricity limit of the orbit-averaged formulas: an orbit with P_b-scale change per orbit (when is the
    averaging invalid?): the fractional change of a per orbit, eps_rr = |da/dt| P / a, along the track to coalescence.

Run: python3 s06_peters_hard.py
"""
import argparse
import math

import mpmath as mp
import numpy as np

from lfphys.core.constants import GM_SUN
from lfphys.theories.approx import peters_mathews as PM

GM1, GM2 = 1.4 * GM_SUN, 1.3 * GM_SUN


@mp.workdps(30)
def T_mp(a0, e0, c=PM.C):
    beta = mp.mpf(12.8) * mp.mpf(GM1) * mp.mpf(GM2) * (mp.mpf(GM1) + mp.mpf(GM2)) / mp.mpf(c) ** 5
    e0 = mp.mpf(e0)
    g = lambda e: 1 + mp.mpf(121) / 304 * e * e  # noqa: E731
    c0 = mp.mpf(a0) * (1 - e0 * e0) / (e0 ** (mp.mpf(12) / 19) * g(e0) ** (mp.mpf(870) / 2299))
    f = lambda e: e ** (mp.mpf(29) / 19) * g(e) ** (mp.mpf(1181) / 2299) / (1 - e * e) ** mp.mpf(1.5)  # noqa: E731
    pts = [0, e0 / 2, e0 - (1 - e0), e0 - (1 - e0) / 10, e0] if e0 > 0.9 else [0, e0 / 2, e0]
    pts = sorted(set(p for p in pts if 0 <= p <= e0))
    I = mp.quad(f, pts)
    return float(mp.mpf(12) / 19 * c0**4 / beta * I)


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    a0 = 2e9
    print("(a) coalescence_time against mpmath")
    for e0 in (0.1, 0.6, 0.9, 0.99, 0.999, 0.9999):
        T = PM.coalescence_time(GM1, GM2, a0, e0)
        Tm = T_mp(a0, e0)
        print(f"  e0={e0}: T = {T:.10e} s, mpmath {Tm:.10e}, relative difference {T / Tm - 1:.1e}")
    print("(b) evolve to a_stop = 1e-3 a0: conserved c0, and t + T(rest) against T(start)")
    for e0 in (0.9, 0.99, 0.999):
        st = {"t": 0.0, "a": a0, "e": e0}
        c0 = PM.c0_of(a0, e0)
        T = PM.coalescence_time(GM1, GM2, a0, e0)
        s, status = PM.evolve(st, 2 * T, GM1, GM2, a_stop=1e-3 * a0)
        rest = PM.coalescence_time(GM1, GM2, s["a"], s["e"]) if s["e"] > 0 else s["a"] ** 4 / (4 * 12.8 * GM1 * GM2 * (GM1 + GM2) / PM.C**5)
        # mid-run check of c0
        sm, _ = PM.evolve(st, 0.5 * T, GM1, GM2)
        print(f"  e0={e0}: status {status}, e_end {s['e']:.4e}, (t + T_rest)/T - 1 = {(s['t'] + rest) / T - 1:.1e}, "
              f"c0 drift at T/2 {PM.c0_of(sm['a'], sm['e']) / c0 - 1:.1e}")
    print("(c) tiny eccentricity: e after evolving for T/2 against the a(e) relation")
    for e0 in (1e-6, 1e-8, 1e-10):
        st = {"t": 0.0, "a": a0, "e": e0}
        T = PM.coalescence_time(GM1, GM2, a0, e0)
        s, _ = PM.evolve(st, 0.9 * T, GM1, GM2)
        # small e: a ~ c0 e^(12/19) => e = (a/c0)^(19/12) (1 + O(e^2))
        c0 = PM.c0_of(a0, e0)
        e_track = (s["a"] * (1 - 0) / c0) ** (19 / 12)
        print(f"  e0={e0:g}: a/a0 = {s['a'] / a0:.3e}, e = {s['e']:.4e}, from the track {e_track:.4e}, "
              f"relative error {s['e'] / e_track - 1:.1e}")
    print("(d) validity of the orbit average: fractional change of a per orbit along the track (e0 = 0.9)")
    for a in (2e9, 1e7, 1e6, 3e5, 1e5):
        e = 0.9
        Pb = PM.orbital_period(GM1 + GM2, a)
        eps = abs(float(PM.da_dt(GM1, GM2, a, e))) * Pb / a
        print(f"  a={a:.0e} m (GM/(c^2 a) = {(GM1 + GM2) / PM.C**2 / a:.1e}), e=0.9: |da/dt| P_b / a = {eps:.1e}")


if __name__ == "__main__":
    main()
