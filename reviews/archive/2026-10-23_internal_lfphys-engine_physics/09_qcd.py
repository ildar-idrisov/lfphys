"""09: lfphys.core.qcd.running against published RunDec numbers and against an independent mpmath integration with
the MS-bar decoupling of alpha_s at the thresholds (which the engine omits).

Sources (fetched 2026-10-23, arXiv:hep-ph/0004189v1, Chetyrkin, Kuehn, Steinhauser, "RunDec", Comput. Phys. Commun.
133, 43 (2000)), text extracted with pdftotext:
* Table 1, column (c) AlphasExact, alpha_s^(5)(M_Z = 91.18) = 0.118, n_f = 5 throughout:
  alpha_s(Mb = 4.7):  1 loop 0.2059, 2 loops 0.2161, 3 loops 0.2167 (Out[6] = 0.216712), 4 loops 0.2169
  (p. 11, Out[2] = 0.2169467);  alpha_s(1 GeV): 0.3369, 0.3965, 0.4029, 0.4065.
* Eq. (20): decoupling with the MS-bar mass at mu = m_h(m_h) (all logs vanish):
  alpha_s^(nl) = alpha_s^(nf) [1 + 11/72 a^2 + (564731/124416 - 82043/27648 zeta3 - 2633/31104 n_l) a^3],
  a = alpha_s^(nf)/pi;  "If the evolution ... is to be performed at N + 1 loops ... consistency requires the matching
  conditions to be implemented in terms of N-loop formulae."
Usage: python3 09_qcd.py
"""
import argparse

argparse.ArgumentParser(description=__doc__).parse_args()

import mpmath as mp

from lfphys.core import data
from lfphys.core.qcd import running

print("=== n_f = 5 fixed, alpha_s(91.18) = 0.118 -> RunDec Table 1 (c) ===")
nf5 = {"c": 0.01, "b": 0.02}  # both below every scale used: n_f = 5 throughout
ref_mb = {1: 0.2059, 2: 0.2161, 3: 0.216712, 4: 0.2169467}
ref_1 = {1: 0.3369, 2: 0.3965, 3: 0.4029, 4: 0.4065}
for L in (1, 2, 3, 4):
    a_mb = running.alpha_s(4.7, 0.118, 91.18, nf5, loops=L)
    a_1 = running.alpha_s(1.0, 0.118, 91.18, nf5, loops=L)
    print(f"{L} loops: alpha_s(4.7) = {a_mb:.7f} (RunDec {ref_mb[L]}), alpha_s(1) = {a_1:.4f} (RunDec {ref_1[L]})")

mp.mp.dps = 30
Z3 = mp.zeta(3)


def beta(nf):
    return [11 - mp.mpf(2) / 3 * nf, 102 - mp.mpf(38) / 3 * nf,
            mp.mpf(2857) / 2 - mp.mpf(5033) / 18 * nf + mp.mpf(325) / 54 * nf**2,
            (mp.mpf(149753) / 6 + 3564 * Z3) - (mp.mpf(1078361) / 162 + mp.mpf(6508) / 27 * Z3) * nf
            + (mp.mpf(50065) / 162 + mp.mpf(6472) / 81 * Z3) * nf**2 + mp.mpf(1093) / 729 * nf**3]


def run(a_s, mu0, mu1, nf, loops=4):
    """alpha_s from mu0 to mu1 at fixed n_f: d a / d ln mu^2 = -sum b_i a^(i+2), a = alpha_s/4pi (Taylor ODE)."""
    b = beta(nf)[:loops]
    sg = 1 if mu1 >= mu0 else -1  # odefun integrates forward only: use s = sg * ln mu^2
    f = mp.odefun(lambda s, a: -sg * sum(bi * a ** (i + 2) for i, bi in enumerate(b)),
                  sg * mp.log(mp.mpf(mu0) ** 2), mp.mpf(a_s) / (4 * mp.pi))
    return 4 * mp.pi * f(sg * mp.log(mp.mpf(mu1) ** 2))


def down(a_s, nl, order):
    """alpha_s^(nl) from alpha_s^(nl+1) at mu = m_h(m_h); order = number of decoupling loops beyond LO (0, 2, 3)."""
    a = mp.mpf(a_s) / mp.pi
    c2 = mp.mpf(11) / 72
    c3 = mp.mpf(564731) / 124416 - mp.mpf(82043) / 27648 * Z3 - mp.mpf(2633) / 31104 * nl
    z = 1 + (c2 * a**2 if order >= 2 else 0) + (c3 * a**3 if order >= 3 else 0)
    return a_s * z


mz, amz = data.M_Z[0], data.ALPHA_S_MZ[0]
mb, mc = data.M_B_MB[0], data.M_C_MC[0]
th = {"c": mc, "b": mb, "t": data.M_T_MSBAR}
print(f"\n=== PDG 2024 inputs: alpha_s(M_Z = {mz}) = {amz}, m_b(m_b) = {mb}, m_c(m_c) = {mc} ===")
print("independent 4-loop running (mpmath odefun) with decoupling at m_h(m_h) of order LO / 2-loop / 3-loop")
for target in (mb * 0.999999, 3.0, 2.0, 1.77686, mc * 0.999999, 1.0):
    eng = running.alpha_s(target, amz, mz, th, loops=4)
    out = []
    for order in (0, 2, 3):
        a = run(amz, mz, mb, 5)
        a = down(a, 4, order)
        if target >= mc:
            a = run(a, mb, target, 4)
        else:
            a = run(a, mb, mc, 4)
            a = down(a, 3, order)
            a = run(a, mc, target, 3)
        out.append(float(a))
    e3 = running.alpha_s(target, amz, mz, th, loops=3)
    print(f"mu = {target:.5g}: engine {eng:.6f} | ref LO-match {out[0]:.6f}  2-loop {out[1]:.6f}  3-loop {out[2]:.6f}"
          f" | engine-(3-loop match) {eng - out[2]:+.2e} ({(eng - out[2]) / out[2]:+.1e} rel)"
          f" | engine 4 vs 3 loops {eng - e3:+.2e}")
print("PDG uncertainty of alpha_s(M_Z): 0.0009 (0.8 %), propagated to 2 GeV it is ~ +-0.0025 (scales ~ alpha_s^2)")
