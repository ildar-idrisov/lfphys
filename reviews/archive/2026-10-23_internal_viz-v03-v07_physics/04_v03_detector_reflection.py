"""v03: reflection of the detector model (complex absorbing potential W(x) = 2 eV (x/DET)^2 on a ramp of DET = 15 nm,
viz.py:_build) as a function of the electron energy at the detector. An independent stationary computation:
transfer matrices over fine slices of the complex potential V = -i W (own code, not lfphys), the ramp followed by the
constant W = 2 eV (beyond it the run's periodic box continues into the mirror ramp of the other detector; the wave
that survives 15 nm of W = 2 eV is negligible for E >~ 0.02 eV, printed). README claim: "their reflection is below
the checks' tolerance" (T check: 1e-4 + 1e-3 T; absorbed check: 2e-3).
Output: out/04_v03_detector_reflection.txt
"""
import numpy as np
from scipy import constants as sc

HBAR = sc.hbar / sc.e * 1e15  # eV fs
M = sc.m_e * 1e12 / sc.e      # eV fs^2 / nm^2
DET = 15.0

OUT = open("out/04_v03_detector_reflection.txt", "w")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.write(s + "\n")


def reflection(E, n=6000):
    """|r|^2 for a wave from the left (V = 0) onto V = -i W(x), W = 2 (x/DET)^2 on [0, DET], then W = 2 constant."""
    x = np.linspace(0.0, DET, n + 1)
    mid = 0.5 * (x[1:] + x[:-1])
    V = np.concatenate([[0.0], -1j * 2.0 * (mid / DET) ** 2, [-2j]])
    k = np.sqrt(2 * M * (E - V) + 0j) / HBAR
    k = np.where(k.imag < 0, -k, k)  # decaying branch in the absorber
    Mt = np.eye(2, dtype=complex)
    for j, xe in enumerate(x):
        k1, k2 = k[j], k[j + 1]
        r = k2 / k1
        a00 = 0.5 * (1 + r) * np.exp(1j * (k2 - k1) * xe)
        a01 = 0.5 * (1 - r) * np.exp(-1j * (k2 + k1) * xe)
        a10 = 0.5 * (1 - r) * np.exp(1j * (k2 + k1) * xe)
        a11 = 0.5 * (1 + r) * np.exp(-1j * (k2 - k1) * xe)
        Mt = Mt @ np.array([[a00, a01], [a10, a11]])
    rr = Mt[1, 0] / Mt[0, 0]
    return abs(rr) ** 2


say("E at the detector (eV) | lambda (nm) | R of the absorbing ramp | R with 2x slices (convergence) | "
    "surviving 15 nm of W=2 eV (one pass)")
for E in (0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 0.8, 2.0):
    k = np.sqrt(2 * M * E) / HBAR
    kc = np.sqrt(2 * M * (E + 2j) + 0j) / HBAR
    surv = np.exp(-2 * abs(kc.imag) * DET)
    say(f"{E:g} | {2 * np.pi / k:.3g} | {reflection(E):.3e} | {reflection(E, 12000):.3e} | {surv:.1e}")
say("")
say("Reading: for slow electrons the detector reflects more than the tolerances: e.g. a transmitted wave with")
say("E - V0 = 0.05 eV (step preset family) or a 0.05 eV packet (energy at its minimum) is reflected at the 1e-3..1e-2")
say("level and then counted by the opposite detector (the box is periodic), i.e. as the wrong outcome.")
