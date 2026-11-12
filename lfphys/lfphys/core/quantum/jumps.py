# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Monte Carlo wave-function (quantum jump) trajectories of the Lindblad equation (plan item P5).

Dalibard, Castin & Moelmer (PRL 68, 580 (1992); the method as in Castin, Dalibard & Moelmer, AIP Conf. Proc. 275, 143
(1993), arXiv:0805.4002, eqs. 2-11): between jumps a wave function evolves with the non-Hermitian Hamiltonian

    H_eff = H - (i/2) sum_m L_m^+ L_m,

and a jump replaces psi by L_m psi / ||L_m psi||. The average of |psi><psi| over the trajectories is the solution of
the master equation (``core.quantum.open_systems``). The first-order scheme of the PRL decides a jump in each step
dt with probability dp = dt sum_m <psi|L_m^+ L_m|psi> and is biased by O(dt). This module uses the equivalent
waiting-time form (Dum, Zoller & Ritsch, PRA 45, 4879 (1992), cited by Plenio & Knight, RMP 70, 101 (1998)):
the probability of no jump up to t is the squared norm of the unnormalised state exp(-i H_eff t) psi (Plenio &
Knight, eqs. 66, 67), so

  1. draw r uniform in [0, 1);
  2. evolve psi with exp(-i H_eff t) until ||psi(t)||^2 = r (the norm decreases monotonically:
     d||psi||^2/dt = -sum_m ||L_m psi||^2);
  3. choose the channel m with probability ||L_m psi||^2 / sum_k ||L_k psi||^2, jump, normalise, and go to 1.

For time-independent H and L_m the no-jump evolution is the exact matrix exponential (``NoJumpPropagator``: the
eigendecomposition of H_eff, or scaling and squaring near its exceptional points) and the jump time is found by a
safeguarded Newton iteration to round-off (|g| <= 8 u r, g(s) = ||psi(s)||^2 - r): there is no time-step bias, only
the statistical error of N trajectories. Trajectory averages are unbiased estimates of Tr(rho(t) A).

Error bars (review B5, S5). ``stderr`` is the sample standard error s/sqrt(N): a central-limit error bar, meaningful
only when many trajectories contribute to the average (for a small population p, N p >> 1). For a rare event it
fails silently: in a Lambda system pumped into its dark state, P_e(t = 40) = 1.4e-6 is carried by ~1e-5 of the
trajectories, and N = 4000 trajectories give means of 3e-9 ... 1.5e-6 with stderr 2e-9 ... 1.5e-6 (z up to 592).
``interval`` gives instead a confidence interval that holds for every N: the per-trajectory values of a Hermitian A
lie in [lambda_min(A), lambda_max(A)], and for independent variables in [0, 1] Hoeffding's Theorem 1 (JASA 58, 13
(1963), eq. 2.1) bounds each tail by exp(-N KL(m || mu)) (KL the Bernoulli relative entropy), so
{mu : N KL(m || mu) <= ln(2/alpha)} covers the exact value with probability >= 1 - alpha; with no contributing
trajectory (m = 0) its upper end is 1 - (alpha/2)^(1/N) ~ ln(2/alpha)/N: what N trajectories cannot resolve.
``contributors`` counts the trajectories that carry a population. The tests compare averages with the master equation
at a stated z-score where many trajectories contribute, through ``interval`` in the rare-event case, and the
jump-time distribution with its closed form by the Dvoretzky-Kiefer-Wolfowitz bound.

Randomness: only the numpy Generator passed in (``numpy.random.default_rng(seed)``), drawn in a fixed order, so a
seed reproduces every trajectory. Limitation: H and the L_m must be time-independent (a periodically driven atom
in the rotating frame is); time-dependent H(t) goes through the master equation (``open_systems.evolve``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy import linalg

from lfphys.core.quantum.open_systems import check_times

ABOUT = {
    "layer": "core", "kind": "law",
    "title": "Траектории квантовых скачков (метод Монте-Карло волновых функций)",
    "statement": "Волновая функция эволюционирует с неэрмитовым H_eff = H − (i/2)Σ L†L до момента, когда квадрат "
                 "нормы падает до случайного r, затем скачок ψ → L_mψ/‖L_mψ‖ с вероятностью ∝ ‖L_mψ‖²; среднее "
                 "|ψ⟩⟨ψ| по траекториям равно решению уравнения Линдблада.",
    "validity": "то же уравнение Линдблада (марковская динамика), H и L_m не зависят от времени; без ошибки шага по "
                "времени (точная экспонента, момент скачка до округления); статистическая ошибка s/√N только при "
                "многих вкладывающих траекториях, для редких событий — неасимптотический интервал Хёфдинга",
    "basis": ["Dalibard, Castin, Mølmer, PRL 68, 580 (1992); Castin, Dalibard, Mølmer, AIP Conf. Proc. 275, 143 "
              "(1993), arXiv:0805.4002",
              "Dum, Zoller, Ritsch, PRA 45, 4879 (1992)",
              "Plenio & Knight, Rev. Mod. Phys. 70, 101 (1998), eqs. (30), (66), (67)",
              "Hoeffding, J. Am. Stat. Assoc. 58, 13 (1963), Theorem 1 — интервал для средних",
              "lfphys/sources/verification_2026-10-29_p5.md — проверка цитат и выводов"],
    "conflicts": [],
}

U = 2.0 ** -53


@dataclass
class Trajectories:
    """Result of ``trajectories``: times (n_t,); expect (n_ops, ntraj, n_t) of the normalised states (complex unless
    every operator is Hermitian); states (ntraj, n_t, d) when stored; jump times and channels per trajectory."""

    times: np.ndarray
    expect: np.ndarray
    states: np.ndarray | None
    jump_times: list = field(default_factory=list)
    jump_channels: list = field(default_factory=list)
    ranges: list = field(default_factory=list)  # (lambda_min, lambda_max) of each Hermitian e_op, else None

    @property
    def ntraj(self) -> int:
        return self.expect.shape[1] if self.expect.size else len(self.jump_times)

    def mean(self, k: int = 0) -> np.ndarray:
        return self.expect[k].mean(axis=0)

    def stderr(self, k: int = 0) -> np.ndarray:
        """Standard error of the mean (sample standard deviation / sqrt N; real and imaginary parts together).

        A central-limit error bar: valid only when many trajectories contribute (module docstring). For a rare
        population it can be orders of magnitude too small (the trajectories that would carry the value are
        missing from the sample, and so is their variance); use ``interval`` and ``contributors`` there."""
        x = self.expect[k]
        return np.sqrt(np.var(x.real, axis=0, ddof=1) + np.var(x.imag, axis=0, ddof=1)) / np.sqrt(x.shape[0])

    def _scaled(self, k: int):
        if not self.ranges or self.ranges[k] is None:
            raise ValueError("a bounded Hermitian e_op is needed (its eigenvalue range scales the values to [0, 1])")
        a, b = self.ranges[k]
        if b <= a:
            return np.zeros_like(self.expect[k].real), a, b
        return np.clip((self.expect[k].real - a) / (b - a), 0.0, 1.0), a, b

    def contributors(self, k: int = 0, level: float = 1e-3) -> np.ndarray:
        """Number of trajectories, at each time, whose value of e_op k exceeds the bottom of its range by more than
        ``level`` times the range: for a population, the trajectories that carry it (a population decaying towards a
        dark state leaves every trajectory a tiny remainder, so the level matters: 1e-3 by default)."""
        x, _, _ = self._scaled(k)
        return np.sum(x > level, axis=0)

    def interval(self, k: int = 0, alpha: float = 1e-6) -> tuple[np.ndarray, np.ndarray]:
        """(lower, upper) at each time: a confidence interval for Tr(rho(t) A) at level 1 - alpha that holds for any
        N (no central-limit approximation): {mu : N KL(m || mu) <= ln(2/alpha)} on the values scaled to [0, 1] by
        the eigenvalue range of A (Hoeffding 1963, Theorem 1, both tails at alpha/2), solved by bisection."""
        x, a, b = self._scaled(k)
        N = x.shape[0]
        m = x.mean(axis=0)
        c = math.log(2.0 / alpha) / N

        def kl(p, q):
            q = np.clip(q, 1e-300, 1 - 1e-16)
            with np.errstate(divide="ignore", invalid="ignore"):
                t1 = np.where(p > 0, p * np.log(p / q), 0.0)
                t2 = np.where(p < 1, (1 - p) * np.log((1 - p) / (1 - q)), 0.0)
            return t1 + t2

        lo_u, hi_u = m.copy(), np.ones_like(m)  # upper end in [m, 1]
        lo_l, hi_l = np.zeros_like(m), m.copy()  # lower end in [0, m]
        for _ in range(200):
            mid = 0.5 * (lo_u + hi_u)
            inside = kl(m, mid) <= c
            lo_u, hi_u = np.where(inside, mid, lo_u), np.where(inside, hi_u, mid)
            mid = 0.5 * (lo_l + hi_l)
            inside = kl(m, mid) <= c
            lo_l, hi_l = np.where(inside, lo_l, mid), np.where(inside, mid, hi_l)
        upper = np.where(kl(m, np.ones_like(m)) <= c, 1.0, hi_u)
        lower = np.where(kl(m, np.zeros_like(m)) <= c, 0.0, lo_l)
        return a + (b - a) * lower, a + (b - a) * upper

    def rho_mean(self) -> np.ndarray:
        """Average of |psi><psi| over the trajectories: (n_t, d, d) (needs stored states)."""
        if self.states is None:
            raise ValueError("rho_mean needs store_states=True")
        s = self.states
        return np.einsum("kti,ktj->tij", s, s.conj()) / s.shape[0]

    def waiting_times(self, n_per_traj: int, from_start: bool = False) -> np.ndarray:
        """The first ``n_per_traj`` intervals between successive jumps of every trajectory (counting the time from
        times[0] to the first jump as the first interval if ``from_start``), pooled: i.i.d. samples whenever every
        jump resets the state to the same vector. Taking all intervals inside the window [times[0], times[-1]]
        instead would bias the sample towards short intervals (the window censors the long ones), so a trajectory
        with fewer jumps than needed raises ValueError: lengthen the run."""
        out = []
        for jt in self.jump_times:
            jt = np.asarray(jt, float)
            iv = np.diff(np.concatenate([[self.times[0]], jt])) if from_start else np.diff(jt)
            if iv.size < n_per_traj:
                raise ValueError(f"waiting_times: a trajectory has only {iv.size} complete intervals "
                                 f"(< {n_per_traj}); lengthen the run")
            out.append(iv[:n_per_traj])
        return np.concatenate(out) if out else np.zeros(0)


def effective_hamiltonian(H, c_ops) -> np.ndarray:
    H = np.asarray(H, complex)
    return H - 0.5j * sum((np.asarray(L, complex).conj().T @ np.asarray(L, complex) for L in c_ops),
                          np.zeros_like(H))


class NoJumpPropagator:
    """exp(-i H_eff s_k) psi_k for a batch of times s_k and states psi_k.

    Route "eig" (used while cond(V) <= ``max_cond``): H_eff = V diag(mu) V^-1, so the batch costs one product with
    V^-1 per state and one with V; the rounding is within about cond(V) u. Route "taylor" (near an exceptional point
    of H_eff, where V is ill-conditioned, e.g. a resonantly driven decaying atom at Omega = Gamma/2): scaling and
    squaring with a degree-18 Taylor polynomial, vectorised over the batch: B = A/2^m with ||B||_1 <= 1/2, truncation
    error <= (1/2)^19/19! < 2e-23 relative, then m squarings."""

    def __init__(self, Heff, max_cond: float = 1e4):
        self.A = -1j * np.asarray(Heff, complex)
        mu, V = linalg.eig(self.A)
        c = float(np.linalg.cond(V))
        self.route = "eig" if np.isfinite(c) and c <= max_cond else "taylor"
        if self.route == "eig":
            self.mu, self.V, self.Vi = mu, V, linalg.inv(V)

    def __call__(self, s, psi) -> np.ndarray:
        s = np.asarray(s, float)
        if self.route == "eig":
            c = psi @ self.Vi.T
            return (np.exp(s[:, None] * self.mu[None, :]) * c) @ self.V.T
        a = float(np.max(np.abs(s))) * float(np.linalg.norm(self.A, 1))
        m = max(0, math.ceil(math.log2(max(a, 1e-300) / 0.5)))
        B = (s / 2.0 ** m)[:, None, None] * self.A[None]
        d = self.A.shape[0]
        P = np.broadcast_to(np.eye(d, dtype=complex), B.shape).copy()
        for k in range(18, 0, -1):  # Horner: I + B/1 (I + B/2 (I + ... ))
            P = np.eye(d) + (B @ P) / k
        for _ in range(m):
            P = P @ P
        return np.einsum("kij,kj->ki", P, psi)


def _jump_times(prop, C, psi, r, s_hi):
    """Solve ||exp(-i Heff s) psi_k||^2 = r_k for s in (0, s_hi_k] (the norm at 0 is >= r_k > the norm at s_hi_k)
    by Newton steps kept inside a shrinking bracket. Returns s and exp(-i Heff s) psi."""
    m = len(r)
    lo = np.zeros(m)
    hi = np.array(s_hi, float)
    s = 0.5 * hi
    phi = None
    for _ in range(200):
        phi = prop(s, psi)
        n2 = np.sum(np.abs(phi) ** 2, axis=1)
        g = n2 - r
        dg = -np.real(np.einsum("ki,ij,kj->k", phi.conj(), C, phi))
        done = (np.abs(g) <= 8 * U * np.maximum(r, U)) | (hi - lo <= 4 * U * np.maximum(hi, 1e-300))
        if np.all(done):
            break
        lo = np.where(g > 0, s, lo)
        hi = np.where(g <= 0, s, hi)
        with np.errstate(divide="ignore", invalid="ignore"):
            newton = s - g / dg
        ok = np.isfinite(newton) & (newton > lo) & (newton < hi)
        s = np.where(done, s, np.where(ok, newton, 0.5 * (lo + hi)))
    return s, phi


def trajectories(H, c_ops, psi0, times, ntraj: int, rng, e_ops=(), store_states: bool = False) -> Trajectories:
    """``ntraj`` quantum-jump trajectories from psi0, recorded at ``times`` (non-decreasing, times[0] the start;
    ValueError otherwise).

    rng: a numpy Generator (seeded by the caller). e_ops: operators whose expectation values in the normalised states
    are recorded per trajectory."""
    H = np.asarray(H, complex)
    c_ops = [np.asarray(L, complex) for L in c_ops]
    d = H.shape[0]
    Heff = effective_hamiltonian(H, c_ops)
    prop = NoJumpPropagator(Heff)
    C = sum((L.conj().T @ L for L in c_ops), np.zeros((d, d), complex))
    times = check_times(times)  # finite, non-decreasing (ValueError otherwise; repeated times are allowed)
    nt = len(times)
    psi0 = np.asarray(psi0, complex)
    psi0 = psi0 / np.linalg.norm(psi0)
    psi = np.tile(psi0, (ntraj, 1))
    r = rng.random(ntraj)
    e_ops = [np.asarray(A, complex) for A in e_ops]
    herm = all(np.allclose(A, A.conj().T, atol=0, rtol=0) for A in e_ops)
    ranges = []
    for A in e_ops:
        if np.allclose(A, A.conj().T, atol=0, rtol=0):
            w = np.linalg.eigvalsh(A)
            ranges.append((float(w[0]), float(w[-1])))
        else:
            ranges.append(None)
    expect = np.zeros((len(e_ops), ntraj, nt), float if herm else complex)
    states = np.zeros((ntraj, nt, d), complex) if store_states else None
    jt = [[] for _ in range(ntraj)]
    jc = [[] for _ in range(ntraj)]

    def record(k):
        nrm = psi / np.linalg.norm(psi, axis=1)[:, None]
        for i, A in enumerate(e_ops):
            val = np.einsum("ki,ij,kj->k", nrm.conj(), A, nrm)
            expect[i, :, k] = val.real if herm else val
        if store_states:
            states[:, k] = nrm

    record(0)
    for k in range(nt - 1):
        dt = times[k + 1] - times[k]
        if dt == 0:  # a repeated time: the same states, recorded again
            expect[:, :, k + 1] = expect[:, :, k]
            if store_states:
                states[:, k + 1] = states[:, k]
            continue
        phi = prop(np.full(ntraj, dt), psi)  # the same propagation as the jump-time search, so the two agree
        n2 = np.sum(np.abs(phi) ** 2, axis=1)
        jump = n2 <= r
        psi[~jump] = phi[~jump]
        act = np.flatnonzero(jump)
        start = np.zeros(act.size)  # time already elapsed in this interval
        while act.size and c_ops:
            s, phi = _jump_times(prop, C, psi[act], r[act], dt - start)
            tau = start + s
            w = np.stack([np.sum(np.abs(phi @ L.T) ** 2, axis=1) for L in c_ops], axis=1)
            cw = np.cumsum(w, axis=1)
            x = rng.random(act.size) * cw[:, -1]
            ch = np.minimum(np.sum(cw <= x[:, None], axis=1), len(c_ops) - 1)
            new = np.stack([phi[i] @ c_ops[ch[i]].T for i in range(act.size)])
            new /= np.linalg.norm(new, axis=1)[:, None]
            for i, j in enumerate(act):
                jt[j].append(times[k] + tau[i])
                jc[j].append(int(ch[i]))
            r[act] = rng.random(act.size)
            rest = dt - tau
            phi2 = prop(rest, new)
            n2 = np.sum(np.abs(phi2) ** 2, axis=1)
            again = n2 <= r[act]
            psi[act[~again]] = phi2[~again]
            psi[act[again]] = new[again]
            start = tau[again]
            act = act[again]
        # renormalise to keep the numbers O(1); the thresholds r are relative to the norm at the last jump, so the
        # remaining threshold is rescaled with the norm
        nn = np.sum(np.abs(psi) ** 2, axis=1)
        psi /= np.sqrt(nn)[:, None]
        r = r / nn
        record(k + 1)
    return Trajectories(times, expect, states, [np.array(a) for a in jt], [np.array(a, int) for a in jc], ranges)
