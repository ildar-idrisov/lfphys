# Review B8-mie, script s02: the optical theorem and energy balance tested physically, through the engine's near
# fields: the power flows through a sphere of radius R around the drop, from mie.near_field(parts=True).
#   Q_ext = -(1/(pi a^2)) oint Re(E_i x H_s* + E_s x H_i*) . r dA,  Q_sca = (1/(pi a^2)) oint Re(E_s x H_s*) . r dA,
#   Q_abs = -(1/(pi a^2)) oint Re(E x H*) . r dA   (H in the engine is Z H, |E0| = 1, intensity |E0|^2/(2Z))
# (Bohren & Huffman Sec. 3.4). Gauss-Legendre in cos(theta) with enough nodes for exp(i k R cos theta) times the
# partial waves, trapezoid in phi. Unlike the engine's check "theorem" (Q_ext against 4 Re S(0)/x^2 from the same
# coefficients, an identity of the sums), this route involves the fields' radial functions, the incident wave, the
# vector harmonics, Z H and the coefficients together.
import math
import sys

import numpy as np

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.optics import mie  # noqa: E402


def flux(m, x, R=2.0, nphi=8):
    a, b = (mie.coefficients_pec(x) if m == "pec" else mie.coefficients(m, x))
    N = mie.n_terms(x)
    ngl = int(2 * N + x * R + 60)
    mu, w = np.polynomial.legendre.leggauss(ngl)
    ph = np.arange(nphi) * 2 * math.pi / nphi
    MU, PH = np.meshgrid(mu, ph, indexing="ij")
    st = np.sqrt(1 - MU ** 2)
    rhat = np.stack([st * np.cos(PH), st * np.sin(PH), MU], -1)
    f = mie.near_field(m, x, R * rhat, parts=True)
    Ei, Es, Hi, Hs = f["E_inc"], f["E_sca"], f["H_inc"], f["H_sca"]
    W = w[:, None] * (2 * math.pi / nphi) * R ** 2

    def surf(v):
        return float(np.sum(W * np.sum(v.real * rhat, -1)))
    q_ext = -surf(np.cross(Ei, np.conj(Hs)) + np.cross(Es, np.conj(Hi))) / math.pi
    q_sca = surf(np.cross(Es, np.conj(Hs))) / math.pi
    q_abs = -surf(np.cross(Ei + Es, np.conj(Hi + Hs))) / math.pi
    q = mie.efficiencies("pec" if m == "pec" else m, x)
    return q, q_ext, q_sca, q_abs


print("Power through a sphere of radius R = 2a around the drop, from the engine's near fields, against the series")
for m, x in [(1.33, 5.0), (1.5 + 0.1j, 10.0), (0.75, 8.0), (2.0 + 1.0j, 3.0), ("pec", 6.0), (1.33, 30.0),
             (1.333, 11.4)]:
    q, qe, qs, qa = flux(m, x)
    print(f"m = {m}, x = {x}: Qext series {q['Qext']:.12f} flux {qe:.12f} rel {abs(qe / q['Qext'] - 1):.1e}; "
          f"Qsca rel {abs(qs / q['Qsca'] - 1):.1e}; Qabs series {q['Qabs']:.3e} flux {qa:.3e} "
          f"(abs diff / Qext {abs(qa - q['Qabs']) / q['Qext']:.1e})")

print("\nNegative control: the scattered H with the sign of a_n flipped in the magnetic part (a convention error)")
orig = mie._vsh_sum


def bad(coef_e, coef_m, R, Rp, rho, th, ph, kind):
    if kind == "H":  # outside the drop only the scattered H uses this path at R = 2a
        coef_m = -coef_m
    return orig(coef_e, coef_m, R, Rp, rho, th, ph, kind)


mie._vsh_sum = bad
q, qe, qs, qa = flux(1.33, 5.0)
mie._vsh_sum = orig
print(f"  with the flipped sign: Qext flux {qe:.6f} against {q['Qext']:.6f} (rel {abs(qe / q['Qext'] - 1):.1e})")
