# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Open quantum systems: the Lindblad (GKSL) master equation for small Hilbert spaces (plan item P5).

    drho/dt = -i [H, rho] + sum_k ( L_k rho L_k^+ - 1/2 {L_k^+ L_k, rho} )

(hbar = 1: H in angular-frequency units of the chosen time unit; the jump operators L_k carry the square roots of
their rates, as C_m in Castin, Dalibard & Moelmer 1993, eq. 2). This is the most general Markovian (time-local,
completely positive, trace-preserving) generator; derived from a microscopic model it needs weak coupling (Born),
a bath correlation time short against the system's relaxation (Markov) and, for the Davies form, the secular
approximation. Those approximations belong to the model that produced H and L_k; this module computes the equation
itself exactly or with a stated error.

Vectorisation: column stacking, vec(rho)[i + d j] = rho[i, j] (``vec``, ``unvec``), so vec(A rho B) = (B^T kron A)
vec(rho) and the Liouvillian is the d^2 x d^2 matrix

    L = -i (I kron H - H^T kron I) + sum_k [ conj(L_k) kron L_k - 1/2 I kron (L_k^+ L_k) - 1/2 (L_k^+ L_k)^T kron I ].

* **Exact propagation** (``propagate``): rho(t) = unvec(exp(L t) vec rho0) by scipy's scaling-and-squaring expm
  (Al-Mohy & Higham, SIAM J. Matrix Anal. Appl. 31, 970 (2009): backward error u ||L t|| in exact arithmetic), or by
  the eigendecomposition L = V diag(lambda) V^-1 (Manzano 2020, eq. 101), accepted only while cond(V) stays below
  ``max_cond``; the error is rounding only (tests: against 30-digit mpmath and between the two routes). Every time
  is measured from the initial state, so the times may come in any order; t < 0 is refused (exp(L t) is not a
  physical map backwards).
* **Steady state** (``steady_state``): the null space of L (Evans' theorem: at least one zero eigenvalue; Manzano
  2020). Route "svd": the right singular vector of the smallest singular value, with uniqueness from the next one
  (two singular values below the threshold: no unique steady state, ValueError) and the bound of Wedin's theorem;
  route "lstsq": [L; vec(I)^T] x = [0; 1] by least squares (independent second route).
* **Time-dependent H(t)** (``evolve``, constant jump operators; times non-decreasing, else ValueError). Three
  one-step methods with step-doubling error control:

  - "radau5" (default): the 3-stage Radau IIA collocation method (order 5, stage order 3, L-stable, stiffly accurate:
    the step ends on the last collocation point t_{n+1}): for this linear equation one solve of size 3 d^2 per step.
    A stiff dissipator (Gamma >> the drive) does not limit the step: in the stiff limit the step returns the state
    that is stationary for L(t_{n+1}), the quasi-static solution. It keeps the trace (any Runge-Kutta method keeps
    linear invariants) and the hermiticity (real coefficients); positivity up to the local error.
  - "cf4": the commutator-free fourth-order Magnus scheme of Blanes, Casas, Oteo & Ros, Phys. Rep. 470, 151 (2009),
    eqs. (293), (295), with the Gauss-Legendre nodes A_i = L(t_n + c_i h), c_{1,2} = 1/2 -+ sqrt(3)/6 (eq. 252):
        vec rho_{n+1} = exp(h (b A1 + a A2)) exp(h (a A1 + b A2)) vec rho_n,  a = 1/4 + sqrt(3)/6, b = 1/4 - sqrt(3)/6
    (a + b = 1/2; by Baker-Campbell-Hausdorff the product is exp(Omega_4) + O(h^5), Omega_4 of eq. 254; time-symmetric,
    eq. 292). With constant jump operators each exponent is h/2 times a Lindblad generator h/2 (D - i[H~, .]) with a
    hermitian H~, so every factor is exactly completely positive and trace preserving, for any h. Stable for any
    step, but in the stiff regime it loses order (review B5, S3, measured): each factor relaxes to the steady state
    of its frozen generator and the last one acts at the effective time t_n + 5h/6, so the quasi-static state lags
    by h/6: first order. Use it where exact positivity of every step matters and the dissipator is not stiff.
  - "magnus4": the commutator form of eq. (254), Omega = h/2 (A1 + A2) - h^2 sqrt(3)/12 [A1, A2], one exponential per
    step, positive only up to the local error; its steps keep h max ||A_i||_F <= 1 (the Magnus series converges for
    h ||A|| < pi), so its cost grows like span ||L||_F: a generator needing more than ``max_steps`` steps is refused
    before the run (ValueError, advice: "radau5").

  Error control by step doubling: one step h against two steps h/2. In the asymptotic regime (h max ||A_i||_F <= 1)
  the Richardson estimate of the error of the two half steps is ||rho_h/2 - rho_h||_1 / (2^p - 1) with the local
  order p = 6 ("radau5") or 5; beyond it (stiff steps) the full difference ||rho_h/2 - rho_h||_1 is taken, which
  bounds the error of the half steps whenever halving the step at least halves the error of the step. Each estimate
  must not exceed tol h / (t_end - t_0). The exact propagator between any two times is completely positive and trace
  preserving, hence a contraction in the trace norm on all operators (its dual is unital and positive; Russo-Dye), and
  the equation is linear: the global error is the sum of the local errors carried by contractions, so the accumulated
  estimate (returned with the result) is the global error in the trace norm to the accuracy of the estimates, and it
  is <= tol by construction (plus the stated rounding allowance).
  Cost, measured on a two-level atom driven by Omega(t) = cos(0.1 t), Gamma = 1/T1 = 2/T2, span 10, tol 1e-8 (the
  review's case): "radau5" 54 steps (0.07 s) at Gamma = 1e4, 55 (0.06 s) at 1e5, 51 (0.05 s) at 1e6, within 7e-11
  of scipy's Radau on the real Bloch equations (rtol 1e-12); "cf4" 63 375 steps (34 s) at 1e4, 325 688 (180 s) at
  1e5; "magnus4" 88 s at 1e4 (the review measured 351 k attempts, 123 s, before its step growth was capped) and
  refused at 1e5. On the exact lab-frame drive (omega0 = 8, Gamma = 1/T1 = 2/T2, span 6, tol 1e-9) "radau5" takes
  760 steps at Gamma = 1e4 and 146 at 1e5.
* **Checks**: trace, hermiticity and the smallest eigenvalue of a state (``state_checks``); trace and hermiticity
  preservation of a generator (``generator_checks``).

Monte Carlo wave-function trajectories of the same equation: ``core.quantum.jumps``; the two-level atom (Rabi, optical
Bloch equations, Torrey's solutions): ``core.quantum.two_level``; which-path decoherence: ``core.quantum.decoherence``.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import linalg

ABOUT = {
    "layer": "core", "kind": "law",
    "title": "Открытые квантовые системы: управляющее уравнение Линдблада",
    "statement": "dρ/dt = −i[H, ρ] + Σ_k (L_k ρ L_k† − ½{L_k†L_k, ρ}) — общий марковский генератор (вполне "
                 "положительный, сохраняющий след): супероператор Лиувилля, точное решение через экспоненту матрицы "
                 "(или её спектральное разложение), стационарное состояние как ядро 𝓛, для H(t) — метод Радо IIA "
                 "5-го порядка (жёстко устойчивый) или схемы Магнуса 4-го порядка с контролем ошибки, проверки "
                 "следа, эрмитовости и положительности.",
    "validity": "марковское приближение: слабая связь с резервуаром (борновское), время корреляции резервуара много "
                "меньше времени релаксации системы, при выводе из микроскопической модели — секулярное приближение; "
                "конечномерное пространство (матрица 𝓛 размера d²×d², практически d ≲ 30). Ошибка: точное решение — "
                "только округление (обратная ошибка u‖𝓛t‖); для H(t) — 4-й порядок, суммарная ошибка в следовой норме "
                "≤ заданного tol (оценка удвоением шага, сжимаемость CPTP-эволюции); число шагов задаётся изменением "
                "H(t) и tol, а не жёсткостью диссипатора (метод radau5; метод magnus4 — не меньше ‖𝓛‖·T шагов)",
    "basis": ["Lindblad, Commun. Math. Phys. 48, 119 (1976); Gorini, Kossakowski, Sudarshan, J. Math. Phys. 17, 821 "
              "(1976)",
              "Castin, Dalibard, Mølmer, AIP Conf. Proc. 275, 143 (1993), arXiv:0805.4002 — eq. (2)",
              "Manzano, AIP Advances 10, 025106 (2020), arXiv:1906.04478 — спектральное решение, теорема Эванса",
              "Blanes, Casas, Oteo, Ros, Phys. Rep. 470, 151 (2009), eqs. (254), (293), (295) — методы Магнуса "
              "4-го порядка",
              "Hairer & Wanner, Solving ODEs II (1996), §IV.5 — Radau IIA (коэффициенты проверены условиями "
              "коллокации)",
              "Al-Mohy & Higham, SIAM J. Matrix Anal. Appl. 31, 970 (2009) — expm",
              "lfphys/sources/verification_2026-10-29_p5.md — проверка цитат и выводов"],
    "conflicts": [],
}

U = 2.0 ** -53  # unit round-off of binary64


# --- vectorisation and superoperators -------------------------------------------------------------------------------

def vec(rho) -> np.ndarray:
    """Column stacking: vec(rho)[i + d j] = rho[i, j]."""
    return np.asarray(rho, complex).reshape(-1, order="F")


def unvec(v, d: int | None = None) -> np.ndarray:
    """Inverse of ``vec`` (also for a stack of vectors (..., d^2) -> (..., d, d))."""
    v = np.asarray(v, complex)
    if d is None:
        d = math.isqrt(v.shape[-1])
    return np.swapaxes(v.reshape(v.shape[:-1] + (d, d)), -1, -2)


def spre(A) -> np.ndarray:
    """vec(A rho) = spre(A) vec(rho)."""
    A = np.asarray(A, complex)
    return np.kron(np.eye(A.shape[0]), A)


def spost(B) -> np.ndarray:
    """vec(rho B) = spost(B) vec(rho)."""
    B = np.asarray(B, complex)
    return np.kron(B.T, np.eye(B.shape[0]))


def sprepost(A, B) -> np.ndarray:
    """vec(A rho B) = sprepost(A, B) vec(rho)."""
    return np.kron(np.asarray(B, complex).T, np.asarray(A, complex))


def hamiltonian_superop(H) -> np.ndarray:
    """-i [H, .] as a d^2 x d^2 matrix."""
    return -1j * (spre(H) - spost(H))


def dissipator(L) -> np.ndarray:
    """D[L] rho = L rho L^+ - 1/2 {L^+ L, rho} as a d^2 x d^2 matrix."""
    L = np.asarray(L, complex)
    LdL = L.conj().T @ L
    return sprepost(L, L.conj().T) - 0.5 * (spre(LdL) + spost(LdL))


def liouvillian(H, c_ops=()) -> np.ndarray:
    """The Lindblad generator as a d^2 x d^2 matrix (column stacking)."""
    out = hamiltonian_superop(H)
    for L in c_ops:
        out = out + dissipator(L)
    return out


def rhs(H, c_ops, rho) -> np.ndarray:
    """drho/dt evaluated directly with d x d matrices (the second route to ``liouvillian``)."""
    rho = np.asarray(rho, complex)
    H = np.asarray(H, complex)
    out = -1j * (H @ rho - rho @ H)
    for L in c_ops:
        L = np.asarray(L, complex)
        LdL = L.conj().T @ L
        out = out + L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL)
    return out


# --- checks ---------------------------------------------------------------------------------------------------------

def state_checks(rho) -> dict:
    """|Tr rho - 1|, max |rho - rho^+| and the smallest eigenvalue of the hermitian part."""
    rho = np.asarray(rho, complex)
    herm = 0.5 * (rho + rho.conj().T)
    return {"trace_err": float(abs(np.trace(rho) - 1.0)),
            "herm_err": float(np.max(np.abs(rho - rho.conj().T))),
            "min_eig": float(np.linalg.eigvalsh(herm)[0])}


def is_state(rho, tol: float = 1e-12) -> bool:
    c = state_checks(rho)
    return c["trace_err"] <= tol and c["herm_err"] <= tol and c["min_eig"] >= -tol


def generator_checks(Lsup) -> dict:
    """Trace preservation max |vec(I)^+ L| (Tr of L(X) vanishes for every X) and hermiticity preservation
    max |L(E_ij)^+ - L(E_ji)| over the matrix units."""
    Lsup = np.asarray(Lsup, complex)
    d = math.isqrt(Lsup.shape[0])
    tr = float(np.max(np.abs(vec(np.eye(d)).conj() @ Lsup)))
    h = 0.0
    for i in range(d):
        for j in range(d):
            Eij = np.zeros((d, d), complex)
            Eij[i, j] = 1.0
            a = unvec(Lsup @ vec(Eij), d)
            b = unvec(Lsup @ vec(Eij.T), d)
            h = max(h, float(np.max(np.abs(a.conj().T - b))))
    return {"trace_preservation": tr, "hermiticity_preservation": h}


def trace_norm(X) -> float:
    return float(np.sum(linalg.svdvals(np.asarray(X, complex))))


# --- time grids -----------------------------------------------------------------------------------------------------

def check_times(times, *, non_negative: bool = False, increasing: bool = True) -> np.ndarray:
    """A validated 1-D float array of output times: finite, at least one, non-decreasing if ``increasing`` (repeated
    times are allowed and give the same state twice), all >= 0 if ``non_negative``; ValueError otherwise (review B5,
    S4: an unsorted grid would otherwise label states with the wrong times)."""
    t = np.atleast_1d(np.asarray(times, float))
    if t.ndim != 1 or t.size == 0:
        raise ValueError("times: a non-empty 1-D sequence is required")
    if not np.all(np.isfinite(t)):
        raise ValueError("times: all times must be finite")
    if increasing and np.any(np.diff(t) < 0):
        k = int(np.flatnonzero(np.diff(t) < 0)[0])
        raise ValueError(f"times must be non-decreasing: times[{k + 1}] = {t[k + 1]!r} < times[{k}] = {t[k]!r}")
    if non_negative and np.any(t < 0):
        raise ValueError(f"times must be >= 0 (exp(L t) is not a physical map for t < 0): got {float(t.min())!r}")
    return t


# --- exact propagation ----------------------------------------------------------------------------------------------

def propagate(Lsup, rho0, times, method: str = "expm", max_cond: float = 1e8) -> np.ndarray:
    """rho(t) for each t in ``times`` (relative to the initial time 0) for a time-independent generator: (n_t, d, d).
    The times may come in any order (each is measured from rho0); they must be finite and >= 0 (ValueError).

    method "expm": exp(L t) per time (scaling and squaring); "eig": one eigendecomposition, ValueError if
    cond(V) > max_cond (near an exceptional point; use "expm" there)."""
    Lsup = np.asarray(Lsup, complex)
    v0 = vec(rho0)
    d = math.isqrt(v0.size)
    times = check_times(times, non_negative=True, increasing=False)
    if method == "expm":
        out = np.array([linalg.expm(Lsup * t) @ v0 for t in times])
    elif method == "eig":
        lam, V = linalg.eig(Lsup)
        c = np.linalg.cond(V)
        if not np.isfinite(c) or c > max_cond:
            raise ValueError(f"propagate: eigenvector matrix ill-conditioned (cond {c:.3g} > {max_cond:.1g}); "
                             "use method='expm'")
        y0 = linalg.solve(V, v0)
        out = (V @ (np.exp(np.outer(lam, times)) * y0[:, None])).T
    else:
        raise ValueError(f"propagate: unknown method {method!r}")
    return unvec(out, d)


def expm_error_bound(Lsup, t: float) -> float:
    """Stated bound on ||rho_computed(t) - rho(t)||_1 of ``propagate(method="expm")`` for ||rho0||_1 = 1, to first
    order in u. Norms: the exact maps exp(L s) are contractions in the trace norm (CPTP; Russo-Dye), and for a
    superoperator X, ||X||_{1->1} <= sqrt(d) ||X||_2 <= sqrt(d) sqrt(n) ||X||_1 (n = d^2). Terms:
    * the backward error of scaling and squaring, ||Delta A||_1 <= u ||A||_1 for A = L t (Al-Mohy & Higham 2009),
      carried by the contraction: d^{3/2} u ||A||_1;
    * the rounding of the Pade evaluation at B = A/2^s (||B||_1 <= theta_13 = 5.37) and of the s squarings, each
      product of n x n matrices within gamma_n |X||Y| entrywise: e_{j+1} <= 2 e_j + gamma_n n d^{3/2} (in 1->1),
      with e_0 <= gamma_60 n d^{3/2} for the Pade evaluation (a rounding budget of 60 operations per entry, as in the
      qubit comparisons of tests/external): 2^s (gamma_60 + gamma_n) n d^{3/2}.
    A worst-case bound: the measured errors are 1e-2 ... 2e-6 of it, smaller for larger d (review B5, N7: the norm
    conversions n d^{3/2} dominate). A test against it detects a wrong generator, time or route, not the loss of a few
    digits; the agreement of the routes (expm, eig, 30-digit mpmath: 2e-15) is the stronger evidence and is recorded
    with the tests."""
    A = np.asarray(Lsup, complex) * t
    n = A.shape[0]
    d = math.isqrt(n)
    a1 = float(np.linalg.norm(A, 1))
    s = max(0, math.ceil(math.log2(max(a1, 1e-300) / 5.371920351148152)))
    g = lambda k: k * U / (1 - k * U)  # noqa: E731
    return d ** 1.5 * (U * a1 + 2.0 ** s * (g(60) + g(n)) * n)


def propagator(Lsup, t: float) -> np.ndarray:
    """exp(L t): the map vec rho(0) -> vec rho(t)."""
    return linalg.expm(np.asarray(Lsup, complex) * t)


# --- steady state ---------------------------------------------------------------------------------------------------

def steady_state(H, c_ops=(), method: str = "svd", Lsup=None) -> tuple[np.ndarray, dict]:
    """The stationary state rho_ss (L rho_ss = 0, Tr rho_ss = 1) and a dict with its residual ||L vec rho||_2, the
    singular values s_min, s_next, s_max of L and (route "svd") the bound ``err_bound`` on ||rho - rho_exact||_F.

    "svd": null vector v of L; unique if s_next > 1000 n u s_max (n = d^2), else ValueError. Wedin: the angle between
    the computed and the exact null vector is <= e / (s_next - e) with the backward error e = p(n) u s_max of the SVD
    (p(n) = 10 n, LAPACK Users' Guide); rho = v / Tr v has |Tr v| = 1/||rho||_F in [1, sqrt d], so
    ||delta rho||_F <= angle (1 + sqrt d).
    "lstsq": [L; vec(I)^T] x = [0; 1] in the least-squares sense (an independent route)."""
    if Lsup is None:
        Lsup = liouvillian(H, c_ops)
    Lsup = np.asarray(Lsup, complex)
    n = Lsup.shape[0]
    d = math.isqrt(n)
    _, s, Vh = linalg.svd(Lsup)
    smax, snext, smin = float(s[0]), float(s[-2]), float(s[-1])
    if snext <= 1000 * n * U * smax:
        raise ValueError(f"steady_state: no unique steady state (second smallest singular value {snext:.3g} "
                         f"against {smax:.3g})")
    info = {"s_min": smin, "s_next": snext, "s_max": smax}
    if method == "svd":
        v = Vh[-1].conj()  # the right singular vector of the smallest singular value
        rho = unvec(v, d)
        rho = rho / np.trace(rho)
        e = 10 * n * U * smax + smin  # backward error of the SVD; the computed smallest singular value is part of it
        info["err_bound"] = float(e / max(snext - e, 1e-300) * (1 + math.sqrt(d)))
    elif method == "lstsq":
        A = np.vstack([Lsup, vec(np.eye(d)).conj()[None, :]])
        b = np.zeros(n + 1, complex)
        b[-1] = 1.0
        x = linalg.lstsq(A, b)[0]
        rho = unvec(x, d)
    else:
        raise ValueError(f"steady_state: unknown method {method!r}")
    rho = 0.5 * (rho + rho.conj().T)
    info["residual"] = float(np.linalg.norm(Lsup @ vec(rho)))
    return rho, info


# --- time-dependent Hamiltonians: fourth-order Magnus integrators with step doubling ------------------------------

_C1 = 0.5 - math.sqrt(3.0) / 6.0
_C2 = 0.5 + math.sqrt(3.0) / 6.0
_K = math.sqrt(3.0) / 12.0
_A = 0.25 + math.sqrt(3.0) / 6.0  # commutator-free weights (Blanes et al. 2009, eqs. 293, 295)
_B = 0.25 - math.sqrt(3.0) / 6.0


def magnus4_step(Lfun, t: float, h: float, v) -> np.ndarray:
    """One step of the fourth-order Magnus integrator (Blanes et al. 2009, eq. 254) for dv/dt = L(t) v."""
    A1 = Lfun(t + _C1 * h)
    A2 = Lfun(t + _C2 * h)
    Om = 0.5 * h * (A1 + A2) - (h * h * _K) * (A1 @ A2 - A2 @ A1)
    return linalg.expm(Om) @ v


def cf4_step(Lfun, t: float, h: float, v) -> np.ndarray:
    """One step of the fourth-order commutator-free Magnus integrator (Blanes et al. 2009, eqs. 293, 295):
    exp(h (b A1 + a A2)) exp(h (a A1 + b A2)) v; each factor is a CPTP map when only H depends on time."""
    A1 = Lfun(t + _C1 * h)
    A2 = Lfun(t + _C2 * h)
    return linalg.expm(h * (_B * A1 + _A * A2)) @ (linalg.expm(h * (_A * A1 + _B * A2)) @ v)


_S6 = math.sqrt(6.0)
RADAU_C = np.array([(4 - _S6) / 10, (4 + _S6) / 10, 1.0])
RADAU_A = np.array([[(88 - 7 * _S6) / 360, (296 - 169 * _S6) / 1800, (-2 + 3 * _S6) / 225],
                    [(296 + 169 * _S6) / 1800, (88 + 7 * _S6) / 360, (-2 - 3 * _S6) / 225],
                    [(16 - _S6) / 36, (16 + _S6) / 36, 1.0 / 9]])


def radau5_step(Lfun, t: float, h: float, v) -> np.ndarray:
    """One step of the 3-stage Radau IIA collocation method (order 5, stage order 3, L-stable, stiffly accurate) for
    the linear dv/dt = L(t) v: the stages Y_i = v + h sum_j a_ij L(t + c_j h) Y_j solve one linear system of size
    3 d^2, and v_{n+1} = Y_3. The nodes are the Radau points (zeros of d^2/dx^2 [x^2 (x - 1)^3]) and A is fixed by
    the collocation conditions sum_j a_ij c_j^(k-1) = c_i^k / k, k = 1, 2, 3 (tested)."""
    n = len(v)
    As = [Lfun(t + c * h) for c in RADAU_C]
    M = np.eye(3 * n, dtype=complex)
    for i in range(3):
        for j in range(3):
            M[i * n:(i + 1) * n, j * n:(j + 1) * n] -= h * RADAU_A[i, j] * As[j]
    Y = linalg.solve(M, np.tile(v, 3))
    return Y[2 * n:]


def _norm2(A) -> float:
    """An upper bound of the spectral norm (the Frobenius norm: cheaper, and conservative for the step limit)."""
    return float(np.linalg.norm(A))


def evolve(H, c_ops, rho0, times, tol: float = 1e-10, h0: float | None = None, steps: int | None = None,
           max_steps: int = 1_000_000, method: str = "radau5") -> tuple[np.ndarray, np.ndarray, dict]:
    """rho(t) at ``times`` (non-decreasing, the first is the initial time; ValueError otherwise) for H(t) (a callable
    t -> d x d matrix, or a constant matrix) and constant jump operators: (rhos (n_t, d, d), err (n_t,), info).

    method "radau5" (default: Radau IIA, stiffly accurate, steps not limited by stiffness), "cf4" (commutator-free
    Magnus, every factor exactly CPTP) or "magnus4" (module docstring).
    Adaptive (default): err[k] is the accumulated estimate of the global error in the trace norm at times[k] plus a
    rounding allowance of 20 n u per step (n = d^2; times (1 + h max||A_i||_F) for "radau5", whose linear solve
    amplifies rounding by up to its condition); it is <= tol + rounding by construction. A step whose estimate is
    above its share of tol but within twice its rounding allowance is accepted (the difference is rounding noise:
    a tol below the rounding floor cannot be resolved) and counted in ``info["floor_steps"]``; a step accepted at the
    smallest step size 1e-14 t is accepted too; both are still summed into err, so err stays honest.
    ``steps``: a fixed number of equal steps per output interval (no control, err = nan): for convergence studies.
    info: accepted and rejected steps, the smallest and largest step, how many accepted steps were stiff
    (h max ||A_i||_F > 1) and how many were accepted at the rounding floor. RuntimeError if more than ``max_steps``
    attempts are needed."""
    times = check_times(times)
    steppers = {"radau5": radau5_step, "cf4": cf4_step, "magnus4": magnus4_step}
    if method not in steppers:
        raise ValueError(f"evolve: unknown method {method!r}")
    step = steppers[method]
    v = vec(rho0)
    d = math.isqrt(v.size)
    D = sum((dissipator(L) for L in c_ops), np.zeros((d * d, d * d), complex))
    if callable(H):
        def Lfun(t):
            return hamiltonian_superop(H(t)) + D
    else:
        Lc = hamiltonian_superop(H) + D

        def Lfun(t):
            return Lc
    out = [unvec(v, d)]
    err = [0.0]
    info = {"accepted": 0, "rejected": 0, "h_min": math.inf, "h_max": 0.0, "stiff_steps": 0, "floor_steps": 0}
    if steps is not None:
        for k in range(len(times) - 1):
            h = (times[k + 1] - times[k]) / steps
            for j in range(steps):
                v = step(Lfun, times[k] + j * h, h, v)
            out.append(unvec(v, d))
            err.append(math.nan)
        info["accepted"] = steps * (len(times) - 1)
        return np.array(out), np.array(err), info
    span = float(times[-1] - times[0])
    if span <= 0:
        return np.array([unvec(v, d)] * len(times)), np.zeros(len(times)), info
    if method == "magnus4":
        need = span * _norm2(Lfun(float(times[0]))) / 0.9
        if need > max_steps:
            raise ValueError(f"evolve(method='magnus4'): the generator is stiff for this method: span x ||L||_F / 0.9 "
                             f"= {need:.3g} steps > max_steps = {max_steps}; use method='cf4', whose steps are not "
                             "limited by ||L||")
    rate = tol / span  # allowed error per unit time
    t = float(times[0])
    a0 = _norm2(Lfun(t))
    if h0:
        h = h0
    elif method == "magnus4":
        h = min(span, 1.0 / max(a0, 1e-300)) * 0.1
    else:
        h = min(span * 1e-3, 1.0 / max(a0, 1e-300))
    acc = 0.0
    n = d * d
    for k in range(1, len(times)):
        t_end = float(times[k])
        while t < t_end:
            if info["accepted"] + info["rejected"] > max_steps:
                raise RuntimeError(f"evolve: more than max_steps = {max_steps} step attempts (t = {t:.6g} of "
                                   f"[{times[0]:.6g}, {times[-1]:.6g}], step {h:.3g}): H(t) varies too fast for tol "
                                   f"= {tol:.3g}")
            last = t + h >= t_end
            hh = t_end - t if last else h
            a = max(_norm2(Lfun(t + _C1 * hh)), _norm2(Lfun(t + _C2 * hh)))
            if method == "magnus4" and hh * a > 1.0:  # stay inside the convergence domain of the Magnus series
                info["rejected"] += 1
                h = 0.9 / a
                continue
            stiff = hh * a > 1.0
            full = step(Lfun, t, hh, v)
            half = step(Lfun, t + hh / 2, hh / 2, step(Lfun, t, hh / 2, v))
            factor = 1.0 if stiff else (1.0 / 31.0 if method == "radau5" else 1.0 / 15.0)
            est = trace_norm(unvec(half - full, d)) * factor
            noise = 20 * n * U * (1.0 + (hh * a if method == "radau5" else 0.0))  # rounding allowance of a step
            floor = est > rate * hh and est <= 2 * noise  # the difference is at the rounding level
            if est <= rate * hh or floor or hh <= 1e-14 * max(abs(t), span):
                v = half
                t = t_end if last else t + hh
                acc += est + noise
                info["floor_steps"] += int(floor)
                info["accepted"] += 1
                info["stiff_steps"] += int(stiff)
                info["h_min"] = min(info["h_min"], hh)
                info["h_max"] = max(info["h_max"], hh)
                # at the rounding floor the estimate does not shrink with the step: grow, never shrink, there
                fac = 4.0 if (est == 0 or floor) else min(4.0, max(0.2, 0.9 * (rate * hh / est) ** 0.25))
                h_new = hh * fac if not last else max(h, hh * fac)
                if method == "magnus4":  # do not grow past the guard: half of the attempts would be rejections
                    h_new = min(h_new, 0.9 / a)
                h = h_new
            else:
                info["rejected"] += 1
                h = hh * max(0.1, 0.9 * (rate * hh / est) ** 0.25)
        out.append(unvec(v, d))
        err.append(acc)
    return np.array(out), np.array(err), info
