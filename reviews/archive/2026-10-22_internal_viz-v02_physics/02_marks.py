"""Review check 02: Jones / spin conventions, state sampling, Englert duality, readout and no-signalling.

Independent references: hand-built matrices (exp of Pauli matrices via scipy.linalg.expm), projective identities,
and Monte-Carlo averages of the engine's own samplers.
Time convention of the engine: the Fresnel kernel exp(+ik(x-x')^2/2z) and the outgoing H^(1) imply
exp(i(kz - wt)). In this convention (1, -i)/sqrt2 rotates clockwise as seen by the receiver = right-circular in the
optics (Born & Wolf / Hecht) convention, and its Stokes S3 = I_R - I_L = +1.
"""
import math

import numpy as np
from scipy.linalg import expm

from v02_double_slit.engine import marks
from v02_double_slit.engine.experiment import _state_label

SX, SY, SZ = marks.SX, marks.SY, marks.SZ
I2 = np.eye(2)

print("== 1. Jones conventions ==")
R = np.array(marks.POL_STATES["R"])
L = np.array(marks.POL_STATES["L"])
# field of R at z=0 in the exp(i(kz - wt)) convention
for wt in (0.0, math.pi / 2):
    E = (R * np.exp(-1j * wt)).real * math.sqrt(2)
    print(f"  R=(1,-i)/sqrt2 at wt={wt:.2f}: E = ({E[0]:+.2f}, {E[1]:+.2f})")
print("  -> E goes +x -> -y: clockwise seen by the receiver = RIGHT circular (Hecht/Born&Wolf)")
print(f"  engine Stokes label of R: {_state_label(R, 'pol')}   of L: {_state_label(L, 'pol')}")
IR = abs(np.vdot(R, R)) ** 2
print("  S3 = I_R - I_L for the state R (projective definition with the engine's own R, L):",
      abs(np.vdot(R, R)) ** 2 - abs(np.vdot(L, R)) ** 2)
psi, chi = 0.0, 45.0
cust = marks.sample_internal(np.random.default_rng(0), "pol", "custom", 1.0, (psi, chi))
print(f"  custom (azimuth 0, ellipticity +45 deg) = {np.round(cust, 4)} -> equals L? {np.allclose(cust, L)}"
      "  (Born&Wolf: chi > 0 is right-handed, S3 = sin 2chi > 0)")
q = marks.element_matrix("qwp", 45, "pol")
outq = q @ np.array([1, 0], complex)
print(f"  QWP(axis 45 deg) on H -> {np.round(outq / outq[0] * abs(outq[0]), 4)}; "
      f"|<R|out>|^2 = {abs(np.vdot(R, outq)) ** 2:.3f} (axis = fast axis in exp(-iwt))")
h = marks.element_matrix("hwp", 22.5, "pol")
outh = h @ np.array([1, 0], complex)
D = np.array(marks.POL_STATES["D"])
print(f"  HWP(22.5 deg) on H: |<D|out>|^2 = {abs(np.vdot(D, outh)) ** 2:.12f}")
# HWP is a mirror: HWP(a) maps linear angle t to 2a - t
t = 0.3
lin = np.array([math.cos(t), math.sin(t)], complex)
hh = marks.element_matrix("hwp", 40, "pol") @ lin
tt = math.radians(80) - t
print(f"  HWP(40 deg) on linear {math.degrees(t):.1f} deg -> overlap with linear {math.degrees(tt):.1f} deg: "
      f"{abs(np.vdot(np.array([math.cos(tt), math.sin(tt)]), hh)) ** 2:.12f}")
P = marks.element_matrix("polarizer", 30, "pol")
print(f"  polarizer: P^2 = P: {np.allclose(P @ P, P)}, Hermitian: {np.allclose(P, P.conj().T)}, Malus at 30 deg on H: "
      f"{np.linalg.norm(P @ np.array([1, 0])) ** 2:.6f} vs cos^2 = {math.cos(math.radians(30)) ** 2:.6f}")

print("\n== 2. spin ==")
for ang in (30, 90, 180, 270):
    a = math.radians(ang)
    ref = expm(-1j * a * SY / 2)
    print(f"  rot_y({ang}) = exp(-i a sy/2): {np.allclose(marks.element_matrix('rot_y', ang, 'spin'), ref)}")
for ang in (0, 60, 90, 180):
    F = marks.element_matrix("filter", ang, "spin")
    a = math.radians(ang)
    n = np.array([math.sin(a), 0, math.cos(a)])
    up_n = np.array([math.cos(a / 2), math.sin(a / 2)], complex)
    print(f"  filter({ang}): projector {np.allclose(F @ F, F)}, passes |+n> {np.allclose(F @ up_n, up_n)}, "
          f"<sigma> of |+n> = {np.round([np.vdot(up_n, S @ up_n).real for S in (SX, SY, SZ)], 6)}")
for s in ("up_x", "up_y", "down_y"):
    v = np.array(marks.SPIN_STATES[s])
    print(f"  {s}: label {_state_label(v, 'spin')}")

print("\n== 3. unpolarized and partially polarized sampling (engine sampler, 200000 draws) ==")
rng = np.random.default_rng(1)
for state, deg in (("unpol", 1.0), ("H", 0.3), ("R", 0.6)):
    acc = np.zeros((2, 2), complex)
    N = 200000
    for _ in range(N):
        v = marks.sample_internal(rng, "pol", state, deg)
        acc += np.outer(v, v.conj())
    acc /= N
    if state == "unpol":
        ref = I2 / 2
    else:
        p = np.array(marks.POL_STATES[state])
        ref = deg * np.outer(p, p.conj()) + (1 - deg) * I2 / 2
    print(f"  {state} P={deg}: max|rho_MC - rho| = {np.max(np.abs(acc - ref)):.4f} (MC sigma ~ {1 / math.sqrt(N):.4f})")
# uniformity on the sphere: <S1^2> = <S2^2> = <S3^2> = 1/3, <S1^4> = 1/5 for the uniform sphere
S = []
for _ in range(100000):
    v = marks.sample_internal(rng, "pol", "unpol", 1.0)
    a, b = v
    S.append([abs(a) ** 2 - abs(b) ** 2, 2 * (a * np.conj(b)).real, -2 * (a * np.conj(b)).imag])
S = np.array(S)
print(f"  Haar: <S_i^2> = {np.round((S ** 2).mean(0), 4)} (1/3), <S_i^4> = {np.round((S ** 4).mean(0), 4)} (1/5)")

print("\n== 4. Englert duality and readout ==")
for th in (0, 30, 60, 90, 135, 180):
    dets = marks.detector_states(2, 0, th, True)
    m = marks.marks(np.ones(1, complex), [np.eye(1)] * 2, np.eye(1), dets)
    V, Dd = marks.englert(m[0], m[1])
    print(f"  theta={th:3d}: V={V:.6f} (|cos|={abs(math.cos(math.radians(th))):.6f}) D={Dd:.6f} (|sin|="
          f"{abs(math.sin(math.radians(th))):.6f}) V^2+D^2={V * V + Dd * Dd:.12f}")
# unequal weights: polarizer at 30 deg on one slit (absorbs part), detector theta=50
chi = np.array([1, 0], complex)
J = [marks.element_matrix("polarizer", 30, "pol"), np.eye(2, dtype=complex)]
dets = marks.detector_states(2, 1, 50, True)
m = marks.marks(chi, J, np.eye(2), dets)
V, Dd = marks.englert(m[0], m[1])
na, nb = np.vdot(m[0], m[0]).real, np.vdot(m[1], m[1]).real
Pred = abs(na - nb) / (na + nb)
print(f"  unequal weights: V={V:.6f}, D={Dd:.6f}, predictability={Pred:.6f}; V^2+D^2={V * V + Dd * Dd:.12f}, D>=P: {Dd >= Pred}")
# readout completeness and no-signalling for random bases
rng = np.random.default_rng(3)
worst = 0
for _ in range(200):
    th, b = rng.uniform(0, 180), rng.uniform(-180, 180)
    dets = marks.detector_states(3, 1, th, True)
    m = marks.marks(np.array([0.6, 0.8j]), [np.eye(2)] * 3, np.eye(2), dets)
    Gs = marks.gram_by_readout(m, 2, marks.readout_basis(b))
    G = marks.gram_by_readout(m, 2, None)[0]
    worst = max(worst, np.max(np.abs(Gs[0] + Gs[1] - G)))
print(f"  sum_r G^(r) = G (200 random theta, basis): max dev {worst:.1e}")
