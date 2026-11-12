# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""``lfphys.core.quantum.open_systems``, ``two_level`` and ``jumps`` against QuTiP 5 (plan items P5, P13): the
Lindblad superoperator, time evolution (constant generators: QuTiP's diagonalising integrator; a time-dependent drive:
QuTiP's Verner 9(8) integrator), steady states, and quantum-jump trajectories (QuTiP's mcsolve).

Independence. QuTiP builds its Liouvillian with its own spre/spost/sprepost and lindblad_dissipator; it propagates a
constant generator by its own eigendecomposition (``method="diag"``: eig, inv, then exp(lambda dt) multiplied in at
each output time), a time-dependent one by its own Cython Runge-Kutta (Verner's 9(8) pair, adaptive), solves the
steady state as a linear system with one row replaced by the trace (``method="direct"``, numpy's LAPACK solve), and
samples quantum jumps by integrating the non-Hermitian Schroedinger equation with an ODE solver and a secant search
for the collapse time. The engine uses scaling-and-squaring expm, Radau IIA with step doubling (``evolve``'s default),
the SVD null vector, and exact exponentials with Newton's method for the jumps. Exact references: the same equations
in 30-digit mpmath for the same binary64 inputs (the Liouvillian, its exponential; the closed forms of the steady
states; the lab-frame solution through the exact rotating frame; the closed-form waiting-time distribution).

Tolerances (u = 2^-53, gamma_k = k u/(1 - k u)); each row's tolerance is the sum of the two sides' bounds:
* "superop rounding": every entry of a Liouvillian is a sum of kron products, the entries of L^+ L and up to
  2 + 3 n_c terms; counting complex products as 3 roundings and sums as 2, the entry is within gamma_k M_ij with
  k = 3 + 2d + 2(2 + 3 n_c) and M = |I (x) H| + |H^T (x) I| + sum_k (|L_k^*| (x) |L_k| + 1/2 I (x) |L_k|^T|L_k| +
  1/2 (|L_k|^T|L_k|)^T (x) I), per side.
* "expm + diag a posteriori" (rho(t), constant generators). Engine: ``open_systems.expm_error_bound`` (trace norm;
  derivation in its docstring) plus the construction error E_c of its Liouvillian carried by the contractions,
  d t ||E_c||_2 ||rho0||_F (first order: exp(L s) has 2-norm <= sqrt(d) on vec rho because it contracts the trace
  norm). QuTiP: its decomposition (lambda, U, Uinv) is read from the integrator after the run and checked a
  posteriori in mpmath: R = L_q U - U diag(lambda) and S = U Uinv - I; the computed map U e^{Lambda t} Uinv differs
  from exp(L_q t) by at most d t ||R||_2 ||Uinv||_2 (L~ = U Lambda U^-1 = L_q - R U^-1, first order) plus
  ||U||_2 E ||Uinv||_2 ||S||_2 (E = max |exp(lambda t)|), plus the rounding of y0 = Uinv rho0 (||U|| E gamma_n
  || |Uinv||rho0| ||), of the k multiplications by exp(lambda dt) since the start ((k (2 + sqrt 5) + max|lambda t| +
  2) u ||U|| ||y||) and of the final product (gamma_n || |U||y| ||), plus its construction error as for the engine.
* "engine estimate + Verner control" (time-dependent drive). Engine: the error ``evolve`` returns (the sum of its
  step-doubling estimates in the trace norm, plus its rounding allowance). QuTiP: each accepted step keeps QuTiP's
  weighted RMS error norm <= 1, i.e. ||e||_2 <= sqrt(n)(atol + rtol max|y|) <= d (atol + rtol) on vec rho (n = d^2,
  |y_i| <= 1), so ||e||_1 <= d^{3/2}(atol + rtol) per step; the number of attempted steps is at most the number of
  evaluations of a coefficient function of H(t) (counted) divided by 16: QuTiP's Verner 9(8) tableau has
  ``rk_step = b.shape[0] = 16`` stages, is not first-same-as-last (``first_same_as_last`` is False for it) and, with
  ``interpolate=False``, evaluates no extra dense-output stages (``qutip/solver/integrator/explicit_rk.pyx``,
  ``_compute_step``, read in the image; review B5, N7: the bound was 16 times looser with all calls counted as
  steps); the exact evolution is completely positive and trace preserving, hence
  a trace-norm contraction, and the equation is linear: the global error is at most the sum of the local errors. Both
  sides' error controls are estimates (embedded pair, step doubling), stated by the methods; that is the basis.
* "Wedin + LU" (steady states). Engine: the Wedin bound ``steady_state`` returns, with the backward error enlarged by
  the construction error ||E_c||_2. QuTiP: the solve of A x = b (A = L_q with weight vec(I)^T added to its first
  row) is backward stable: ||dx||_2/||x||_2 <= cond(A)(p(n) u + ||E_c||_2/||A||_2), p(n) = 10 n (LAPACK Users' Guide,
  as in the qubit comparisons), plus 2 u ||x|| for its hermitisation.
* "MC z = 5" (trajectory averages): both sides are Monte Carlo estimates of the same expectation with sample standard
  errors s_e/sqrt(N_e), s_q/sqrt(N_q); |mean_e - mean_q| <= 5 sqrt(se_e^2 + se_q^2) + QuTiP's deterministic bias
  (the collapse norm within norm_tol relative, the collapse time within norm_t_tol, the ODE error per trajectory
  <= nsteps_cap d^{3/2} (atol + rtol)), 2 (n_jumps (norm_tol + w_max norm_t_tol) + ODE) for an observable in [-1, 1]
  (the engine has no deterministic bias beyond round-off). 5 standard errors: two-sided normal tail 5.7e-7 per row.
* "DKW two-sample" (waiting-time distributions): sup |F_e - F_q| <= eps(N_e) + eps(N_q) + QuTiP's bias in the CDF
  (norm_tol + w_max norm_t_tol), with eps(N) = sqrt(ln(2/alpha)/(2N)) at alpha = 1e-6 per sample (Dvoretzky-Kiefer-
  Wolfowitz with Massart's constant). eng err and lib err: each sample's sup distance to the closed-form CDF. The
  atom decays into a dark level so that every trajectory jumps once (the time to the first photon from |g> has the
  waiting-time distribution of resonance fluorescence); both samplers invert the same law, so with equal seeds the
  sample of one case is a monotone image of the sample of another: each case has its own seed.
"""

from __future__ import annotations

import functools
import math

import mpmath as mp
import numpy as np
import pytest
import qutip as qt
from qutip.core.data import mean as qmean

from lfphys.core.quantum import jumps as J, open_systems as OS, two_level as TL

from _common import U, Row, check, gamma, params

GROUP = "open systems (QuTiP)"
Z = 5.0
ALPHA = 1e-6
DPS = 30


def _Q(m):
    return qt.Qobj(np.asarray(m, complex))


# --- systems --------------------------------------------------------------------------------------------------------

def _systems():
    """name: (H, c_ops, rho0) with dense numpy matrices."""
    out = {}
    out["OBE Omega=1.3 Delta=0.7 T1=2 T2=1.5"] = (TL.hamiltonian(1.3, 0.7), TL.collapse_operators(2.0, 1.5),
                                                   TL.density_matrix([0.0, 0.0, -1.0]))
    out["OBE Omega=5 Delta=-2 T2=2T1"] = (TL.hamiltonian(5.0, -2.0), TL.collapse_operators(1.0, 2.0),
                                          TL.density_matrix([0.3, -0.2, 0.5]))
    # Lambda system (e, g1, g2), equal detunings: the dark state Omega2|g1> - Omega1|g2> is stationary
    e, g1, g2 = np.eye(3, dtype=complex)
    O1, O2, De = 1.1, 0.7, 0.4
    H = -De * np.outer(e, e) + 0.5 * O1 * (np.outer(e, g1) + np.outer(g1, e)) + 0.5 * O2 * (np.outer(e, g2)
                                                                                         + np.outer(g2, e))
    out["Lambda O1=1.1 O2=0.7 Delta=0.4"] = (H, [math.sqrt(0.6) * np.outer(g1, e), math.sqrt(0.9) * np.outer(g2, e)],
                                            np.outer(g1, g1))
    # damped driven oscillator (N = 4) in a thermal bath
    N, w, F, kap, nth = 4, 1.0, 0.3, 0.5, 0.3
    a = np.diag(np.sqrt(np.arange(1, N)), 1).astype(complex)
    out["oscillator N=4 driven, nth=0.3"] = (w * a.conj().T @ a + F * (a + a.conj().T),
                                            [math.sqrt(kap * (1 + nth)) * a, math.sqrt(kap * nth) * a.conj().T],
                                            np.diag([1.0, 0, 0, 0]).astype(complex))
    # two qubits, exchange coupling and collective decay
    sm = TL.SM
    s1, s2 = np.kron(sm, np.eye(2)), np.kron(np.eye(2), sm)
    Hq = 0.8 * (s1.conj().T @ s2 + s2.conj().T @ s1) + 0.3 * np.kron(TL.SZ, np.eye(2))
    out["two qubits, collective decay"] = (Hq, [math.sqrt(0.5) * (s1 + s2), math.sqrt(0.2) * np.kron(TL.SZ, np.eye(2))],
                                           np.outer(np.kron(TL.E, TL.G), np.kron(TL.E, TL.G)))
    return out


def _mag(H, c_ops):
    """M of the "superop rounding" basis."""
    d = H.shape[0]
    Id = np.eye(d)
    aH = np.abs(H)
    M = np.kron(Id, aH) + np.kron(aH.T, Id)
    for L in c_ops:
        aL = np.abs(L)
        LdL = aL.T @ aL
        M = M + np.kron(aL, aL) + 0.5 * np.kron(Id, LdL) + 0.5 * np.kron(LdL.T, Id)
    return M


def _k_rounding(d, nc):
    return 3 + 2 * d + 2 * (2 + 3 * nc)


@mp.workdps(DPS)
def _mp_liouvillian(H, c_ops):
    """The exact Liouvillian of the binary64 inputs, in mpmath (column stacking)."""
    d = H.shape[0]

    def M(A):
        return mp.matrix([[mp.mpc(complex(x)) for x in row] for row in A])

    def kron(A, B):
        n, m = A.rows, B.rows
        K = mp.matrix(n * m, n * m)
        for i in range(n):
            for j in range(n):
                if A[i, j] != 0:
                    for k in range(m):
                        for l in range(m):
                            K[i * m + k, j * m + l] = A[i, j] * B[k, l]
        return K

    def T(A):
        return A.T

    def dag(A):
        return A.H

    Id = mp.eye(d)
    Hm = M(H)
    out = mp.mpc(0, -1) * (kron(Id, Hm) - kron(T(Hm), Id))
    for L in c_ops:
        Lm = M(L)
        LdL = dag(Lm) * Lm
        Lc = mp.matrix([[mp.conj(Lm[i, j]) for j in range(d)] for i in range(d)])
        out += kron(Lc, Lm) - kron(Id, LdL) / 2 - kron(T(LdL), Id) / 2
    return out


def _to_np(A):
    return np.array([[complex(A[i, j]) for j in range(A.cols)] for i in range(A.rows)])


@mp.workdps(DPS)
def _mp_expm_apply(Lm, v, t):
    w = mp.expm(Lm * mp.mpf(t)) * mp.matrix([mp.mpc(complex(x)) for x in v])
    return np.array([complex(w[i]) for i in range(w.rows)])


def _ec_norm(H, c_ops):
    """||E_c||_2 <= ||gamma_k M||_F: the construction error of a Liouvillian (either side)."""
    d = H.shape[0]
    return float(gamma(_k_rounding(d, len(c_ops))) * np.linalg.norm(_mag(H, c_ops)))


# --- Liouvillian ----------------------------------------------------------------------------------------------------

def _liouvillian_rows():
    out = []
    for name, (H, c_ops, _) in _systems().items():
        Le = OS.liouvillian(H, c_ops)
        Lq = qt.liouvillian(_Q(H), [_Q(L) for L in c_ops]).full()
        ex = _to_np(_mp_liouvillian(H, c_ops))
        tol = float(np.max(2 * gamma(_k_rounding(H.shape[0], len(c_ops))) * _mag(H, c_ops)))
        out.append(Row(GROUP, "Liouvillian max|entry diff|", name, float(np.max(np.abs(Le - Lq))), 0.0, tol,
                       "superop rounding", float(np.max(np.abs(Le - ex))), float(np.max(np.abs(Lq - ex)))))
    return out


# --- constant generators: engine expm against QuTiP's diagonalising integrator --------------------------------------

@mp.workdps(DPS)
def _diag_bound(integ, Lq, rho0, ts):
    """QuTiP-side bound for each output time (module docstring, "expm + diag a posteriori")."""
    Um = integ.U.to_array()
    Ui = integ.Uinv.to_array()
    lam = np.asarray(integ.diag).ravel()
    n = Um.shape[0]
    d = math.isqrt(n)
    mU, mUi, mL = mp.matrix(Um.tolist()), mp.matrix(Ui.tolist()), mp.matrix(Lq.tolist())
    R = _to_np(mL * mU - mU * mp.diag([mp.mpc(complex(x)) for x in lam]))
    S = _to_np(mU * mUi - mp.eye(n))
    nU, nUi = float(np.linalg.norm(Um, 2)), float(np.linalg.norm(Ui, 2))
    nR, nS = float(np.linalg.norm(R, 2)), float(np.linalg.norm(S, 2))
    v0 = OS.vec(rho0)
    r0 = float(np.linalg.norm(v0))
    y0r = float(np.linalg.norm(np.abs(Ui) @ np.abs(v0)))
    out = []
    for k, t in enumerate(ts):
        E = float(np.max(np.abs(np.exp(lam * t))))
        y = (Ui @ v0) * np.exp(lam * t)
        lt = float(np.max(np.abs(lam * t)))
        b = d * t * nR * nUi * r0 + nU * E * nUi * nS * r0
        b += nU * E * gamma(n) * y0r
        b += (k * (2 + math.sqrt(5)) + lt + 2) * U * nU * float(np.linalg.norm(y))
        b += gamma(n) * float(np.linalg.norm(np.abs(Um) @ np.abs(y)))
        out.append(b)
    return out


TIMES = (0.0, 0.5, 2.0, 6.0)


def _propagation_rows():
    out = []
    for name, (H, c_ops, rho0) in _systems().items():
        Le = OS.liouvillian(H, c_ops)
        solver = qt.MESolver(_Q(H), [_Q(L) for L in c_ops],
                             options={"method": "diag", "normalize_output": False, "store_states": True})
        res = solver.run(_Q(rho0), list(TIMES))
        Lq = qt.liouvillian(_Q(H), [_Q(L) for L in c_ops]).full()
        qb = _diag_bound(solver._integrator, Lq, rho0, TIMES)
        Lx = _mp_liouvillian(H, c_ops)
        ec = _ec_norm(H, c_ops)
        d = H.shape[0]
        r0 = float(np.linalg.norm(rho0))
        for k, t in enumerate(TIMES):
            re = OS.propagate(Le, rho0, [t])[0]
            rq = res.states[k].full()
            ex = OS.unvec(_mp_expm_apply(Lx, OS.vec(rho0), t), d)
            eb = OS.expm_error_bound(Le, t) + d * t * ec * r0
            tol = eb + qb[k] + d * t * ec * r0
            out.append(Row(GROUP, "rho(t) max|entry diff| (constant L)", f"{name}; t={t:g}",
                           float(np.max(np.abs(re - rq))), 0.0, tol, "expm + diag a posteriori",
                           float(np.max(np.abs(re - ex))), float(np.max(np.abs(rq - ex)))))
    return out


# --- a time-dependent drive: engine Radau IIA against QuTiP's Verner 9(8) -------------------------------------------

@mp.workdps(DPS)
def _lab_exact(t, w0, w, Om, c_ops, rho0):
    """Circular drive: the exact rotating-frame solution (detuning w - w0 in mpmath), rotated back."""
    Hr = TL.hamiltonian(Om, 0.0)  # Omega part; the detuning is added exactly below
    Lm = _mp_liouvillian(Hr, c_ops)
    De = mp.mpf(w) - mp.mpf(w0)
    Pe = _mp_liouvillian(TL.PE, [])  # -i[|e><e|, .]
    Lm = Lm - De * Pe
    v = _mp_expm_apply(Lm, OS.vec(rho0), t)
    rr = mp.matrix(OS.unvec(v, 2).tolist())
    ph = mp.expj(mp.mpf(w) * mp.mpf(t) / 2)
    R = mp.diag([ph, mp.conj(ph)])
    return _to_np(R.H * rr * R)


def _time_dependent_rows():
    w0, w, Om, T1, T2 = 8.0, 7.2, 1.5, 2.0, 1.0
    c_ops = TL.collapse_operators(T1, T2)
    rho0 = TL.density_matrix([0.0, 0.0, -1.0])
    ts = np.linspace(0.0, 6.0, 7)
    re, err, _ = OS.evolve(lambda t: TL.lab_hamiltonian_circular(t, w0, w, Om), c_ops, rho0, ts, tol=1e-10)
    calls = [0]

    def fc(t):
        calls[0] += 1
        return math.cos(w * t)

    def fs(t):
        return math.sin(w * t)
    Ht = [_Q(0.5 * w0 * TL.SZ), [_Q(0.5 * Om * TL.SX), fc], [_Q(0.5 * Om * TL.SY), fs]]
    atol = rtol = 1e-12
    res = qt.mesolve(Ht, _Q(rho0), ts, [_Q(L) for L in c_ops],
                     options={"method": "vern9", "atol": atol, "rtol": rtol, "normalize_output": False,
                              "interpolate": False, "nsteps": 10 ** 6, "store_states": True})
    from qutip.solver.integrator import verner9efficient as v9
    stages = len(v9.vern9_coeff["b"])  # 16; checked not first-same-as-last in test_qutip_verner9_stage_count
    qb = math.ceil(calls[0] / stages) * 2 ** 1.5 * (atol + rtol)
    out = []
    for k, t in enumerate(ts):
        rq = res.states[k].full()
        ex = _lab_exact(t, w0, w, Om, c_ops, rho0)
        out.append(Row(GROUP, "rho(t) max|entry diff| (lab-frame circular drive)",
                       f"w0={w0:g} w={w:g} Omega={Om:g} T1={T1:g} T2={T2:g}; t={t:g}",
                       float(np.max(np.abs(re[k] - rq))), 0.0, float(err[k]) + qb, "engine estimate + Verner control",
                       float(np.max(np.abs(re[k] - ex))), float(np.max(np.abs(rq - ex)))))
    return out


# --- steady states --------------------------------------------------------------------------------------------------

@mp.workdps(DPS)
def _exact_obe_ss(Om, De, T1, T2):
    Om, De = mp.mpf(Om), mp.mpf(De)
    G1, g = 1 / mp.mpf(T1), 1 / mp.mpf(T2)
    D = G1 * (g * g + De * De) + Om * Om * g
    u, v, w = Om * De * G1 / D, Om * G1 * g / D, -G1 * (g * g + De * De) / D
    return np.array([[complex((1 + w) / 2), complex((u - 1j * v) / 2)], [complex((u + 1j * v) / 2),
                                                                         complex((1 - w) / 2)]])


@mp.workdps(DPS)
def _exact_dark(O1, O2):
    n = mp.sqrt(mp.mpf(O1) ** 2 + mp.mpf(O2) ** 2)
    v = [mp.mpf(0), mp.mpf(O2) / n, -mp.mpf(O1) / n]
    return np.array([[complex(a * b) for b in v] for a in v])


@mp.workdps(DPS)
def _exact_thermal(N, nth):
    q = mp.mpf(nth) / (1 + mp.mpf(nth))
    p = [q ** k for k in range(N)]
    s = sum(p)
    return np.diag([complex(x / s) for x in p])


def _steady_cases():
    out = []
    for Om, De, T1, T2 in ((1.3, 0.7, 2.0, 1.5), (5.0, -2.0, 1.0, 2.0), (0.2, 0.0, 1.0, 2.0)):
        out.append((f"OBE Omega={Om:g} Delta={De:g} T1={T1:g} T2={T2:g}", TL.hamiltonian(Om, De),
                    TL.collapse_operators(T1, T2), _exact_obe_ss(Om, De, T1, T2)))
    H, c_ops, _ = _systems()["Lambda O1=1.1 O2=0.7 Delta=0.4"]
    out.append(("Lambda dark state O1=1.1 O2=0.7", H, c_ops, _exact_dark(1.1, 0.7)))
    N, nth, kap = 5, 0.4, 0.5
    a = np.diag(np.sqrt(np.arange(1, N)), 1).astype(complex)
    out.append((f"thermal oscillator N={N} nth={nth:g}", a.conj().T @ a,
                [math.sqrt(kap * (1 + nth)) * a, math.sqrt(kap * nth) * a.conj().T], _exact_thermal(N, nth)))
    return out


def _steady_rows():
    out = []
    for name, H, c_ops, ex in _steady_cases():
        re, info = OS.steady_state(H, c_ops)
        rq = qt.steadystate(_Q(H), [_Q(L) for L in c_ops], method="direct").full()
        Lq = qt.liouvillian(_Q(H), [_Q(L) for L in c_ops])
        n = Lq.shape[0]
        d = H.shape[0]
        w = float(qmean.mean_abs_nonzero(Lq.data))
        A = Lq.full().copy()
        A[0, :] += w * OS.vec(np.eye(d)).conj()
        ec = _ec_norm(H, c_ops)
        nA = float(np.linalg.norm(A, 2))
        xq = float(np.linalg.norm(rq))
        tq = float(np.linalg.cond(A)) * (10 * n * U + ec / nA) * xq + 2 * U * xq
        e_bw = 10 * n * U * info["s_max"] + info["s_min"] + ec
        te = e_bw / max(info["s_next"] - e_bw, 1e-300) * (1 + math.sqrt(d))
        out.append(Row(GROUP, "steady state max|entry diff|", name, float(np.max(np.abs(re - rq))), 0.0, te + tq,
                       "Wedin + LU", float(np.max(np.abs(re - ex))), float(np.max(np.abs(rq - ex)))))
    return out


# --- quantum jumps --------------------------------------------------------------------------------------------------

MC = {"norm_tol": 1e-7, "norm_t_tol": 1e-9, "norm_steps": 60, "atol": 1e-10, "rtol": 1e-10, "nsteps": 2000}


def _qutip_bias(n_jumps, w_max, n_intervals):
    """QuTiP's deterministic bias on an observable in [-1, 1] (module docstring)."""
    ode = MC["nsteps"] * (n_intervals + n_jumps * MC["norm_steps"]) * 2 ** 1.5 * (MC["atol"] + MC["rtol"])
    return 2 * (n_jumps * (MC["norm_tol"] + w_max * MC["norm_t_tol"]) + ode)


def _mc_mean_rows():
    Om, De, T1, T2 = 2.0, 0.8, 1.0, 1.2
    H, c_ops = TL.hamiltonian(Om, De), TL.collapse_operators(T1, T2)
    ts = np.linspace(0.0, 8.0, 17)
    N = 3000
    ops = {"P_e": TL.PE, "sigma_x": TL.SX, "sigma_y": TL.SY}
    tr = J.trajectories(H, c_ops, TL.G, ts, N, np.random.default_rng(2027), e_ops=list(ops.values()))
    res = qt.mcsolve(_Q(H), qt.Qobj(TL.G.reshape(2, 1)), ts, [_Q(L) for L in c_ops],
                     e_ops=[_Q(A) for A in ops.values()], ntraj=N, seeds=2027,
                     options=dict(MC, progress_bar=False, keep_runs_results=True))
    q = np.real(np.asarray(res.runs_expect))  # (n_ops, ntraj, n_t)
    ex = OS.propagate(OS.liouvillian(H, c_ops), TL.density_matrix([0, 0, -1]), ts)
    exv = {"P_e": np.real(ex[:, 0, 0]), "sigma_x": np.array([TL.bloch_vector(r)[0] for r in ex]),
           "sigma_y": np.array([TL.bloch_vector(r)[1] for r in ex])}
    nj = max(len(c) for c in res.col_times)
    G1, gp, _ = TL.rates(T1, T2)
    bias = _qutip_bias(nj, 1.0 / T1 + 2 * (gp - 0.5 * G1), len(ts))  # w_max <= total jump rate
    out = []
    for i, name in enumerate(ops):
        me, se = tr.mean(i).real, tr.stderr(i)
        mq = q[i].mean(axis=0)
        sq = q[i].std(axis=0, ddof=1) / math.sqrt(q.shape[1])
        for k, t in enumerate(ts):
            out.append(Row(GROUP, f"trajectory mean <{name}>", f"Omega={Om:g} Delta={De:g} T1={T1:g} T2={T2:g}; "
                           f"N={N}; t={t:g}", float(me[k]), float(mq[k]),
                           Z * math.hypot(se[k], sq[k]) + bias, "MC z = 5",
                           float(abs(me[k] - exv[name][k])), float(abs(mq[k] - exv[name][k]))))
    return out


def _t_complete(Om, De, G, p_miss=1e-12):
    """A run length T with P0(T) < p_miss: the first emission happens before T with probability > 1 - p_miss."""
    t = 1.0
    while TL.no_emission_probability(t, Om, De, G) > p_miss:
        t *= 1.5
    return t


def _ks_one(x, F):
    n = x.size
    return max(float(np.max(np.arange(1, n + 1) / n - F)), float(np.max(F - np.arange(0, n) / n)))


def _ks_two(a, b):
    a, b = np.sort(a), np.sort(b)
    xs = np.concatenate([a, b])
    Fa = np.searchsorted(a, xs, side="right") / a.size
    Fb = np.searchsorted(b, xs, side="right") / b.size
    return float(np.max(np.abs(Fa - Fb)))


def _eps(n):
    return math.sqrt(math.log(2 / ALPHA) / (2 * n))


def _sink_system(Om, De, G):
    """(e, g, d): the driven transition g-e decays at rate Gamma into a dark level d, so every trajectory jumps once.
    The no-jump evolution on span{e, g} is that of resonance fluorescence (the same L^+ L = Gamma |e><e|), so the time
    of the first jump from |g> has the closed-form CDF 1 - P0 of ``two_level``: the waiting time between photons."""
    H = np.zeros((3, 3), complex)
    H[:2, :2] = TL.hamiltonian(Om, De)
    L = np.zeros((3, 3), complex)
    L[2, 0] = math.sqrt(G)
    return H, [L], np.array([0, 1, 0], complex)


def _waiting_rows():
    out = []
    G = 1.0
    N = 4000
    for (Om, De), seed in zip(((1.0, 0.0), (3.0, 1.0), (0.5, 0.0)), (77, 78, 79)):
        T = _t_complete(Om, De, G)
        H, c_ops, psi0 = _sink_system(Om, De, G)
        tr = J.trajectories(H, c_ops, psi0, [0.0, T], N, np.random.default_rng(seed))
        we = np.sort(tr.waiting_times(1, from_start=True))
        res = qt.mcsolve(_Q(H), qt.Qobj(psi0.reshape(3, 1)), [0.0, T], [_Q(L) for L in c_ops], ntraj=N, seeds=seed,
                         options=dict(MC, progress_bar=False))
        if any(len(c) != 1 for c in res.col_times):
            raise ValueError("a QuTiP trajectory has no jump before T: lengthen the run")
        wq = np.sort(np.array([c[0] for c in res.col_times]))
        w_max = float(np.max(TL.waiting_time_density(np.linspace(0, T, 4001), Om, De, G)))
        bias = MC["norm_tol"] + w_max * MC["norm_t_tol"]
        tol = _eps(we.size) + _eps(wq.size) + 2 * bias
        label = f"Omega={Om:g} Delta={De:g} Gamma={G:g}" + ("; exceptional point" if Om == 0.5 * G else "")
        out.append(Row(GROUP, "waiting-time CDF sup|F_engine - F_qutip|", f"{label}; N={N}",
                       _ks_two(we, wq), 0.0, tol, "DKW two-sample",
                       _ks_one(we, 1 - TL.no_emission_probability(we, Om, De, G)),
                       _ks_one(wq, 1 - TL.no_emission_probability(wq, Om, De, G))))
    return out


@functools.lru_cache(maxsize=None)
def rows() -> list[Row]:
    return (_liouvillian_rows() + _propagation_rows() + _time_dependent_rows() + _steady_rows() + _mc_mean_rows()
            + _waiting_rows())


@pytest.mark.parametrize("row", params(rows()))
def test_open_systems(row):
    check(row)


def test_conventions():
    """Both sides stack columns (vec(A rho B) = (B^T kron A) vec rho) and use the same jump-operator form: the engine's
    and QuTiP's superoperators of a non-symmetric A rho B agree exactly on 0/1 matrices."""
    A = np.array([[0, 1], [0, 0]], complex)
    B = np.array([[0, 0], [1, 1]], complex)
    assert np.array_equal(OS.sprepost(A, B), qt.sprepost(_Q(A), _Q(B)).full())
    assert np.array_equal(OS.spre(A), qt.spre(_Q(A)).full())
    assert np.array_equal(OS.spost(B), qt.spost(_Q(B)).full())
    assert np.array_equal(OS.vec(np.arange(4).reshape(2, 2)), qt.operator_to_vector(_Q(np.arange(4).reshape(2, 2)))
                          .full().ravel())


def test_qutip_verner9_stage_count():
    """The step count behind the "engine estimate + Verner control" rows: QuTiP's Verner 9(8) has 16 stages and is
    not first-same-as-last (so every attempted step evaluates the right-hand side 16 times), and a coefficient
    function is evaluated at least once per right-hand side: counted calls / 16 >= attempted steps."""
    from qutip.solver.integrator import verner9efficient as v9
    c = v9.vern9_coeff
    assert len(c["b"]) == 16 and len(c["e"]) == 16
    assert not np.allclose(np.asarray(c["a"])[15, :16], np.asarray(c["b"]), atol=1e-14)


def test_qutip_jump_scheme_is_the_waiting_time_form():
    """QuTiP's mcsolve draws a target norm r and collapses when ||psi||^2 falls to r (the same waiting-time form the
    engine uses), so the two samples estimate the same distribution; checked here on a pure decay, where the collapse
    time is -ln(r)/Gamma: QuTiP's collapse times are exponential with rate Gamma (DKW at alpha = 1e-6)."""
    G, N = 1.3, 3000
    res = qt.mcsolve(qt.Qobj(np.zeros((2, 2))), qt.Qobj(TL.E.reshape(2, 1)), [0.0, 60.0],
                     [qt.Qobj(math.sqrt(G) * TL.SM)], ntraj=N, seeds=5, options=dict(MC, progress_bar=False))
    t = np.sort(np.array([c[0] for c in res.col_times]))
    assert t.size == N
    assert _ks_one(t, 1 - np.exp(-G * t)) <= _eps(N) + MC["norm_tol"] + G * MC["norm_t_tol"]
