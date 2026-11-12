# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""``lfphys.core.quantum.qubits`` against QuTiP 5 (plan item P13): spin-1/2 correlations of the singlet and CHSH,
polarization correlations of |Phi+>, Born probabilities and Lueders states, partial trace, Bloch vector, von Neumann
entropy, concurrence, and spin precession U = exp(-i omega t n.sigma/2).

Independence. QuTiP builds its operators from its own sigmax/sigmay/sigmaz, tensor, bell_state, expect, ptrace,
entropy_vn and concurrence. The engine's precession uses scipy.linalg.expm; QuTiP's Qobj.expm would call the same
scipy routine, so the QuTiP side is built instead from its closed-form rotation gates rx, ry, rz (entries cos(phi/2),
-i sin(phi/2)): a general axis n = (sin a cos b, sin a sin b, cos a) as rz(b) ry(a) rz(theta) ry(-a) rz(-b), an
identity in SU(2). QuTiP's ODE solvers (sesolve, mesolve) are not used: their error control is local and gives no
global bound to derive a tolerance from. An exact reference (closed forms in 50-digit mpmath for the same binary64
inputs) is computed wherever one exists, to attribute a difference to one side.

Tolerances (u = 2^-53, gamma_n = n u/(1 - n u)); each is the sum of the two sides' bounds:
* "contraction k": a sum over terms x_ij y_ji (Tr(rho K), <psi|K|psi>) with at most k roundings on the path of any
  term (entries of the state, of the observable, the products and the additions; complex products and sums counted as
  3 and 2 roundings): |error| <= gamma_k sum |x_ij||y_ji| per side. Where an entry of the observable is a cosine or
  sine of a rounded angle (the polarizer observables), its absolute error (4 + 2|angle|) u is added to the magnitudes,
  since that error does not vanish with the entry (cos(fl(pi/2)) = 6.1e-17). Counts: correlations and CHSH terms k = 34 (state
  entries 3 + 3, observable entries 5 + 5 + 3 for n/|n| and the Kronecker product, 4x4 contraction 15); Born
  probabilities and the Bloch vector k = 12 (projector 6, 2x2 contraction 6); partial trace k = 2 (one complex
  addition).
* "Lueders": entries of P rho P / p: gamma_20 (|P||rho||P|)_ij / p + |post_ij| (gamma_12 M_p / p + u) per side.
* "LAPACK eig": eigenvalues of a Hermitian n x n matrix are exact for A + E with ||E||_2 <= p(n) u ||A||_2, and of a
  general matrix with ||E|| <= p(n) u ||A|| (LAPACK Users' Guide, 3rd ed., "Error Bounds for the Symmetric
  Eigenproblem" and "Error Bounds for the Nonsymmetric Eigenproblem", netlib.org/lapack/lug); "using p(n)=10n in the
  error bound formulas will often give a reasonable bound" ("How to Measure Errors"); we take p(n) = 10 n. Entropy: the
  variation of h(x) = -x log2 x over [lambda - 2 dl, lambda + 2 dl] for every eigenvalue, plus the cut-offs (the engine
  drops eigenvalues <= 1e-15, QuTiP replaces those < 1e-17 by 1e-17), plus gamma_4 sum h. Concurrence: the matrix
  R = rho (sy sy) rho* (sy sy) carries gamma_21 |rho||Y||rho*||Y| from its three products, plus p(4) u ||R||; by
  Bauer-Fike every eigenvalue moves by at most dl = cond(X) ||E||_2 (X the eigenvectors); each sqrt(|lambda|) then
  moves by at most sqrt(|lambda| + dl) - sqrt(max(|lambda| - dl, 0)), which is sqrt(dl) at a zero eigenvalue: the
  concurrence of a pure state is only as accurate as sqrt(u) in both implementations (the same algorithm, Wootters
  1998). Sorting is 1-Lipschitz, so the concurrence moves by at most 4 max_i of that per side.
* "expm/gates": the engine's A = -i omega t n.sigma/2 carries gamma_9 ||A||; scipy's expm (Al-Mohy & Higham, SIAM J.
  Matrix Anal. Appl. 31, 970 (2009)) chooses the Pade degree and the scaling 2^s so that the backward error of the
  approximant is at most u ||A|| in exact arithmetic; exp is 1-Lipschitz on skew-Hermitian matrices (the divided
  differences of exp over imaginary eigenvalues have modulus <= 1), so the error is (gamma_9 + u) ||A||_2 + 2^s gamma_60
  sqrt 2 (the Pade evaluation, then s squarings that double it; s = max(0, ceil(log2(||A||_1 / 5.37)))). The QuTiP
  product of five gates: each entry of each gate within 2u + u theta_k/2 (libm, and the rounded angle), each of the
  four 2x2 products gamma_7 |F||G| with ||F||,||G|| = 1, and the axis n rounded by gamma_8.
"""

from __future__ import annotations

import functools
import math

import mpmath as mp
import numpy as np
import pytest
import qutip as qt
from qutip.core import gates

from lfphys.core.quantum import qubits as qb

from _common import U, Row, check, gamma, params

GROUP = "qubits (QuTiP)"
P_N = lambda n: 10 * n  # noqa: E731  (LAPACK p(n), see the module docstring)


def _q(m, dims):
    return qt.Qobj(np.asarray(m, complex), dims=dims)


D1 = [[2], [2]]
D2 = [[2, 2], [2, 2]]
QS = (qt.sigmax(), qt.sigmay(), qt.sigmaz())


def _unit(v):
    v = [float(x) for x in v]
    s = math.sqrt(sum(x * x for x in v))
    return [x / s for x in v]


def _q_nsigma(n):
    n = _unit(n)
    return n[0] * QS[0] + n[1] * QS[1] + n[2] * QS[2]


def _mag(x, y):
    """sum_ij |x_ij| |y_ji|: the scale of the rounding error of Tr(x y)."""
    return float(np.sum(np.abs(np.asarray(x)) * np.abs(np.asarray(y)).T))


def _mp_vec(n):
    n = [mp.mpf(float(x)) for x in n]
    s = mp.sqrt(sum(x * x for x in n))
    return [x / s for x in n]


# --- correlations ---------------------------------------------------------------------------------------------------

DIRS = {
    "z,z": ((0, 0, 1), (0, 0, 1)),
    "z,x": ((0, 0, 1), (1, 0, 0)),
    "z,45deg": ((0, 0, 1), (1, 0, 1)),
    "z,135deg": ((0, 0, 1), (1, 0, -1)),
    "z,-z": ((0, 0, 1), (0, 0, -1)),
    "oblique": ((0.3, -0.4, 0.866), (-0.7, 0.2, 0.5)),
    "oblique y": ((0.0, 1.0, 1e-3), (0.6, 0.8, 0.0)),
    "nearly parallel": ((1.0, 0.0, 0.0), (1.0, 1e-8, 0.0)),
    "unnormalised": ((0.0, 3.0, 4.0), (10.0, 0.0, 0.0)),
}


def _corr_rows():
    out = []
    singlet = qt.bell_state("11")  # (|01> - |10>)/sqrt 2, the engine's SINGLET
    rho = qb.dm(qb.SINGLET)
    for name, (a, b) in DIRS.items():
        eng = qb.spin_correlation(qb.SINGLET, a, b)
        K = qt.tensor(_q_nsigma(a), _q_nsigma(b))
        lib = float(np.real(qt.expect(K, singlet)))
        tol = 2 * gamma(34) * _mag(rho, K.full())
        exact = -sum(x * y for x, y in zip(_mp_vec(a), _mp_vec(b)))
        out.append(Row(GROUP, "singlet E(a,b)", name, eng, lib, tol, "contraction 34",
                       float(abs(eng - exact)), float(abs(lib - exact))))
    # CHSH at the optimal angles (in the x-z plane, E = -cos(angle)): S = -2 sqrt 2 (Tsirelson)
    ang = {"a": 0.0, "a2": math.pi / 2, "b": math.pi / 4, "b2": 3 * math.pi / 4}
    d = {k: (math.sin(v), 0.0, math.cos(v)) for k, v in ang.items()}
    eng = qb.chsh(lambda x, y: qb.spin_correlation(qb.SINGLET, x, y), d["a"], d["a2"], d["b"], d["b2"])
    lib, tol = 0.0, 0.0
    for sign, x, y in ((1, "a", "b"), (-1, "a", "b2"), (1, "a2", "b"), (1, "a2", "b2")):
        K = qt.tensor(_q_nsigma(d[x]), _q_nsigma(d[y]))
        lib += sign * float(np.real(qt.expect(K, singlet)))
        tol += 2 * gamma(34) * _mag(rho, K.full())
    tol += 2 * gamma(3) * 4.0  # the three additions of four terms of modulus <= 1, on each side
    out.append(Row(GROUP, "CHSH S (singlet)", "optimal angles", eng, lib, tol, "contraction 34 x 4",
                   float(abs(abs(eng) - 2 * mp.sqrt(2))), float(abs(abs(lib) - 2 * mp.sqrt(2)))))
    # polarization correlations of |Phi+> = (|HH> + |VV>)/sqrt 2: E = cos 2(alpha - beta)
    phi = qt.bell_state("00")
    rho = qb.dm(qb.PHI_PLUS)
    for al, be in ((0.0, 0.0), (0.0, math.pi / 8), (0.0, math.pi / 4), (math.pi / 8, 3 * math.pi / 8),
                   (0.3, 1.9), (1.0, 1.0 + 1e-7)):
        eng = qb.correlation(qb.PHI_PLUS, qb.polarizer_observable(al), qb.polarizer_observable(be))

        def obs(t):  # 2 |t><t| - I in the (H, V) basis, |t> = cos t |H> + sin t |V>
            k = math.cos(t) * qt.basis(2, 0) + math.sin(t) * qt.basis(2, 1)
            return 2 * k * k.dag() - qt.qeye(2)
        K = qt.tensor(obs(al), obs(be))
        lib = float(np.real(qt.expect(K, phi)))
        # the entries cos 2t, sin 2t (and 2 cos^2 t - 1, 2 cos t sin t) are computed from a rounded angle: an absolute
        # error of at most (4 + 2|t|) u each, also where the exact entry is 0; the magnitudes carry it
        mag_a = np.abs(qb.polarizer_observable(al)) + (4 + 2 * abs(al)) * U
        mag_b = np.abs(qb.polarizer_observable(be)) + (4 + 2 * abs(be)) * U
        tol = 2 * gamma(34) * _mag(rho, np.kron(mag_a, mag_b)) + 2 * _mag(np.abs(rho), np.kron(mag_a, mag_b)
                                                                          - np.kron(np.abs(mag_a) - (4 + 2 * abs(al)) * U,
                                                                                    np.abs(mag_b) - (4 + 2 * abs(be)) * U))
        exact = mp.cos(2 * (mp.mpf(al) - mp.mpf(be)))
        out.append(Row(GROUP, "Phi+ polarizer E(alpha,beta)", f"{al:.6g},{be:.9g}", eng, lib, tol, "contraction 34",
                       float(abs(eng - exact)), float(abs(lib - exact))))
    return out


# --- measurement ----------------------------------------------------------------------------------------------------

class _Outcome:
    """A stand-in for numpy's Generator that always returns outcome k (to get a chosen Lueders state)."""

    def __init__(self, k):
        self.k = k

    def choice(self, n, p=None):
        return self.k


STATES1 = {
    "|0>": qb.dm(qb.ket(1, 0)),
    "|+i>": qb.dm(qb.ket(1, 1j)),
    "tilted pure": qb.dm(qb.ket(math.cos(0.4), math.sin(0.4) * np.exp(0.7j))),
    "mixed r=(0.2,-0.3,0.5)": 0.5 * (qb.I2 + 0.2 * qb.SX - 0.3 * qb.SY + 0.5 * qb.SZ),
}
AXES1 = {"z": (0, 0, 1), "x": (1, 0, 0), "oblique": (0.3, -0.5, 0.81), "-z": (0, 0, -1)}


def _measure_rows():
    out = []
    for sname, rho in STATES1.items():
        Q = _q(rho, D1)
        bl_e = qb.bloch(rho)
        for i, s in enumerate(QS):
            lib = float(np.real(qt.expect(s, Q)))
            out.append(Row(GROUP, f"Bloch r_{'xyz'[i]}", sname, float(bl_e[i]), lib,
                           2 * gamma(12) * _mag(rho, s.full()), "contraction 12"))
        for aname, n in AXES1.items():
            projs = qb.projectors(n)
            p_eng = qb.measure(rho, projs)
            Pq = (qt.qeye(2) + _q_nsigma(n)) / 2
            p_lib = float(np.real(qt.expect(Pq, Q)))
            out.append(Row(GROUP, "Born P(+n)", f"{sname}; n={aname}", float(p_eng[0]), p_lib,
                           2 * gamma(12) * _mag(rho, Pq.full()), "contraction 12"))
            if p_lib > 1e-3:  # Lueders state for outcome +
                _, k, post = qb.measure(rho, projs, _Outcome(0))
                post_q = (Pq * Q * Pq / p_lib).full()
                P = np.abs(Pq.full())
                M = P @ np.abs(rho) @ P
                Mp = _mag(rho, Pq.full())
                tol = float(np.max(2 * (gamma(20) * M / p_lib + np.abs(post_q) * (gamma(12) * Mp / p_lib + U))))
                out.append(Row(GROUP, "Lueders state max|entry diff|", f"{sname}; n={aname}",
                               float(np.max(np.abs(post - post_q))), 0.0, tol, "Lueders"))
    # measuring qubit A of the singlet along n: projector P_n (x) I on the pair
    rho = qb.dm(qb.SINGLET)
    singlet = qt.bell_state("11")
    for aname, n in AXES1.items():
        Pa = qb.projectors(n)
        projs = [np.kron(P, qb.I2) for P in Pa]
        p_eng = qb.measure(rho, projs)
        Pq = qt.tensor((qt.qeye(2) + _q_nsigma(n)) / 2, qt.qeye(2))
        p_lib = float(np.real(qt.expect(Pq, singlet)))
        out.append(Row(GROUP, "Born P(A: +n) singlet", aname, float(p_eng[0]), p_lib,
                       2 * gamma(12 + 6) * _mag(rho, Pq.full()), "contraction 18"))
    # partial trace of a two-qubit mixed state
    psi = qb.ket(0.8, 0.1 + 0.3j, -0.2j, 0.45)
    rho2 = 0.7 * qb.dm(psi) + 0.3 * np.eye(4) / 4
    Q2 = _q(rho2, D2)
    for keep in (0, 1):
        eng = qb.ptrace(rho2, keep)
        lib = Q2.ptrace(keep).full()
        r = rho2.reshape(2, 2, 2, 2)
        mag = np.einsum("ijkj->ik", np.abs(r)) if keep == 0 else np.einsum("ijik->jk", np.abs(r))
        tol = float(np.max(2 * gamma(2) * mag))
        out.append(Row(GROUP, "partial trace max|entry diff|", f"keep {keep}", float(np.max(np.abs(eng - lib))), 0.0,
                       tol, "contraction 2"))
    return out


# --- entropy and concurrence -----------------------------------------------------------------------------------------

def _h(x):
    return 0.0 if x <= 0 else -x * math.log2(x)


def _var_h(lo, hi):
    """max h - min h over [lo, hi] (h = -x log2 x is concave, maximal at 1/e)."""
    lo, hi = max(lo, 0.0), min(hi, 1.0)
    vals = [_h(lo), _h(hi)] + ([_h(1 / math.e)] if lo < 1 / math.e < hi else [])
    return max(vals) - min(vals)


def _entropy_tol(rho):
    lam = np.linalg.eigvalsh(rho)
    dl = P_N(rho.shape[0]) * U * float(np.linalg.norm(rho, 2))
    tol = 0.0
    for x in lam:
        lo, hi = x - 2 * dl, x + 2 * dl
        tol += 2 * _var_h(lo, hi)
        if lo <= 1e-15:  # a side may drop it (engine) or replace it by 1e-17 (QuTiP)
            tol += max(_h(min(hi, 1e-15)), _h(1e-17)) + _h(1e-17)
    return tol + 2 * gamma(4) * sum(_h(max(x, 0.0)) for x in lam)


def _bell_like(t):
    return qb.ket(math.cos(t), 0, 0, math.sin(t))


def _werner(p):
    return p * qb.dm(qb.SINGLET) + (1 - p) * np.eye(4) / 4


def _two_qubit_states():
    """name: (rho, exact concurrence, exact entropy of rho_A in bits)."""
    hb = lambda x: 0 if x == 0 else -x * mp.log(x, 2)  # noqa: E731
    st = {"singlet": (qb.dm(qb.SINGLET), mp.mpf(1), mp.mpf(1)),
          "Phi+": (qb.dm(qb.PHI_PLUS), mp.mpf(1), mp.mpf(1)),
          "product |0+>": (qb.dm(np.kron(qb.ket(1, 0), qb.ket(1, 1))), mp.mpf(0), mp.mpf(0))}
    for t in (0.1, 0.4, 1e-4):
        c2 = mp.cos(mp.mpf(t)) ** 2
        st[f"cos t|00>+sin t|11>, t={t}"] = (qb.dm(_bell_like(t)), abs(mp.sin(2 * mp.mpf(t))), hb(c2) + hb(1 - c2))
    for p in (0.2, 1 / 3, 0.5, 0.9):
        st[f"Werner p={p:.4g}"] = (_werner(p), max(mp.mpf(0), (3 * mp.mpf(p) - 1) / 2), mp.mpf(1))
    return st


def _conc_tol(rho):
    Y = np.kron(qb.SY, qb.SY)
    A = np.abs(rho) @ np.abs(Y) @ np.abs(rho.conj()) @ np.abs(Y)
    E = (gamma(21) + P_N(4) * U) * float(np.linalg.norm(A, "fro"))
    R = rho @ Y @ rho.conj() @ Y
    lam, X = np.linalg.eig(R)
    dl = float(np.linalg.cond(X)) * E
    w = max(math.sqrt(abs(x) + dl) - math.sqrt(max(abs(x) - dl, 0.0)) for x in lam)
    s = sum(math.sqrt(abs(x)) for x in lam)
    return 2 * (4 * w + gamma(4) * s)


def _entanglement_rows():
    out = []
    for name, (rho, c_exact, s_exact) in _two_qubit_states().items():
        Q = _q(rho, D2)
        eng = qb.concurrence(rho)
        lib = float(qt.concurrence(Q))
        out.append(Row(GROUP, "concurrence", name, eng, lib, _conc_tol(rho), "LAPACK eig + sqrt",
                       float(abs(eng - c_exact)), float(abs(lib - c_exact))))
        rA = qb.ptrace(rho, 0)
        eng = qb.entropy(rA)
        lib = float(qt.entropy_vn(_q(rA, D1), base=2))
        out.append(Row(GROUP, "entropy of rho_A (bits)", name, eng, lib, _entropy_tol(rA), "LAPACK eig + h(x)",
                       float(abs(eng - s_exact)), float(abs(lib - s_exact))))
    return out


# --- precession -----------------------------------------------------------------------------------------------------

def _gate_U(theta, a, b):
    """exp(-i theta n.sigma/2), n = (sin a cos b, sin a sin b, cos a), from QuTiP's closed-form gates."""
    return (gates.rz(b) * gates.ry(a) * gates.rz(theta) * gates.ry(-a) * gates.rz(-b)).full()


def _U_exact(theta, a, b):
    th, a, b = mp.mpf(theta), mp.mpf(a), mp.mpf(b)
    n = [mp.sin(a) * mp.cos(b), mp.sin(a) * mp.sin(b), mp.cos(a)]
    c, s = mp.cos(th / 2), mp.sin(th / 2)
    return [[c - 1j * s * n[2], -1j * s * (n[0] - 1j * n[1])], [-1j * s * (n[0] + 1j * n[1]), c + 1j * s * n[2]]]


def _precession_rows():
    out = []
    TH13 = 5.371920351148152  # theta_13 of the degree-13 Pade approximant (Higham 2005; Al-Mohy & Higham 2009)
    for omega, t in ((1.0, 0.3), (2.0, 1.0), (1.0, math.pi), (5.0, 2.0), (100.0, 10.0)):
        for a, b, label in ((0.0, 0.0, "z"), (math.pi / 2, 0.0, "x"), (math.pi / 2, math.pi / 2, "y"),
                            (0.7, 2.1, "oblique"), (2.9, -0.4, "near -z")):
            n = (math.sin(a) * math.cos(b), math.sin(a) * math.sin(b), math.cos(a))
            Ue = qb.larmor(omega, t, n)
            theta = omega * t
            Ul = _gate_U(theta, a, b) if label not in ("z", "x", "y") else \
                {"z": gates.rz, "x": gates.rx, "y": gates.ry}[label](theta).full()
            A = -0.5j * omega * t * qb.n_sigma(n)
            s = max(0, math.ceil(math.log2(max(np.linalg.norm(A, 1), 1e-300) / TH13)))
            tol_e = (gamma(9) + U) * float(np.linalg.norm(A, 2)) + 2 ** s * gamma(60) * math.sqrt(2)
            nf = 5 if label not in ("z", "x", "y") else 1
            tol_l = nf * (2 * U + U * abs(theta) / 2) + (nf - 1) * gamma(7) * 2 + gamma(8)
            Ux = _U_exact(theta, a, b)
            err = lambda M: max(float(abs(M[i][j] - Ux[i][j])) for i in range(2) for j in range(2))  # noqa: E731
            out.append(Row(GROUP, "U = exp(-i w t n.sigma/2) max|entry diff|", f"w t={theta:.6g}; n={label}",
                           float(np.max(np.abs(Ue - Ul))), 0.0, tol_e + tol_l, "expm/gates", err(Ue), err(Ul)))
    return out


@functools.lru_cache(maxsize=None)
@mp.workdps(50)
def rows() -> list[Row]:
    return _corr_rows() + _measure_rows() + _entanglement_rows() + _precession_rows()


@pytest.mark.parametrize("row", params(rows()))
def test_qubits(row):
    check(row)


def test_conventions():
    """Both sides use the same basis and Pauli matrices: |0> = (1, 0) is spin up along z, sigma_z = diag(1, -1); the
    singlet and |Phi+> are QuTiP's bell_state('11') and bell_state('00')."""
    assert np.array_equal(qb.SZ, qt.sigmaz().full()) and np.array_equal(qb.SX, qt.sigmax().full())
    assert np.array_equal(qb.SY, qt.sigmay().full())
    assert np.max(np.abs(qb.SINGLET - qt.bell_state("11").full().ravel())) <= 2 * gamma(3)
    assert np.max(np.abs(qb.PHI_PLUS - qt.bell_state("00").full().ravel())) <= 2 * gamma(3)
