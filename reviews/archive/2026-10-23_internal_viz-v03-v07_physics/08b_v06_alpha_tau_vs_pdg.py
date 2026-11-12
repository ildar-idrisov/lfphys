"""v06: alpha_s(m_tau) of the engine against the PDG 2024 statement (review "Quantum Chromodynamics", Sec. 9.4.1,
text checked in the downloaded PDF rpp2024-rev-qcd.pdf, extracted with pdftotext): "we arrive at
alpha_s(m_Z^2) = 0.1173 +- 0.0017 ... This corresponds to alpha_s(m_tau^2) = 0.314 +- 0.014."
PDG Eq. (9.4): alpha^(nf+1) = alpha^(nf) [1 + c20 alpha^2 + ...], c20 = -11/(72 pi^2) for the MS-bar mass at m_h.
The engine (4 loops, continuous matching) and the independent code of 08_v06_qcd.py (+ c2, + c3) from 0.1173.
Output: out/08b_v06_alpha_tau_vs_pdg.txt
"""
import importlib.util
import sys

from lfphys.core import data
from lfphys.core.qcd import running

spec = importlib.util.spec_from_file_location("q08", "08_v06_qcd.py")
OUT = open("out/08b_v06_alpha_tau_vs_pdg.txt", "w")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.write(s + "\n")


# reuse the independent runner of script 08 without re-running its probes: copy the functions here
import math  # noqa: E402

from scipy import integrate, special  # noqa: E402

Z3 = float(special.zeta(3.0))


def betas(nf):
    return [11 - 2 / 3 * nf, 102 - 38 / 3 * nf, 2857 / 2 - 5033 / 18 * nf + 325 / 54 * nf**2,
            (149753 / 6 + 3564 * Z3) - (1078361 / 162 + 6508 / 27 * Z3) * nf + (50065 / 162 + 6472 / 81 * Z3) * nf**2
            + 1093 / 729 * nf**3]


def run_fixed(a, mu0, mu1, nf):
    b = betas(nf)
    f = lambda L, y: [-sum(bi * y[0] ** (i + 2) for i, bi in enumerate(b))]  # noqa: E731
    s = integrate.solve_ivp(f, (2 * math.log(mu0), 2 * math.log(mu1)), [a / (4 * math.pi)], method="DOP853",
                            rtol=1e-13, atol=1e-18)
    return 4 * math.pi * s.y[0, -1]


def alpha_tau(a_mz, order, mtau=1.77693):
    x = run_fixed(a_mz, data.M_Z[0], data.M_B_MB[0], 5)
    p = x / math.pi
    if order >= 2:
        x *= 1 + 11 / 72 * p * p + (564731 / 124416 - 82043 / 27648 * Z3 - 2633 / 31104 * 4) * p**3 * (order >= 3)
    return run_fixed(x, data.M_B_MB[0], mtau, 4)


TH = {"c": data.M_C_MC[0], "b": data.M_B_MB[0], "t": data.M_T_MSBAR}
for a0 in (0.1173, 0.1180):
    e = running.alpha_s(1.77693, a0, data.M_Z[0], TH, 4)
    say(f"alpha_s(M_Z) = {a0}: engine alpha_s(m_tau) = {e:.4f}; own continuous {alpha_tau(a0, 1):.4f}, "
        f"+c2 {alpha_tau(a0, 2):.4f}, +c2+c3 {alpha_tau(a0, 3):.4f}")
say("PDG 2024 (Sec. 9.4.1): alpha_s(M_Z) = 0.1173 +- 0.0017 corresponds to alpha_s(m_tau) = 0.314 +- 0.014")
