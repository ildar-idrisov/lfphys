# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Apparatus logic of the Bell test with real detectors: a wrapper over lfphys (orchestration, not physics laws).

* ``Law``      - the world's law for one pair type: the outcome probabilities of the analysers' ports come from the
                 engine (the Born rule on the source's state, ``lfphys.core.quantum.qubits``, or a local model of
                 ``lfphys.theories.alternatives.local_hidden``), and so do the outcome probabilities of a time slot
                 (``lfphys.tools.bell_stats.slot_probabilities``). Nothing here computes a probability of the physics
                 by itself; ``or_tables`` combines independent click patterns by their union (the logic of a
                 threshold detector).
* ``Stream``   - the time stream of a run (EX2 design §4.7): Poisson emissions, locally defined slots with a random
                 setting bit per station and slot, the ports by the law, each detector by the engine's model
                 (``lfphys.theories.models.photodetector.detect``: efficiency, dark and background counts, the
                 non-paralysable dead time carried from one step of the run to the next, Gaussian jitter added to the
                 recorded times), coincidences within a window on the delay-compensated time tags, the trials (slots)
                 with their outcomes «+», «−», «0», «+−», the space-time relations of each coincidence
                 (``lfphys.core.causality``).
* ``Store``    - the counts per pair of analyser angles: coincidences N(++, +−, −+, −−), of them the accidental ones
                 (known only in a simulation), the singles and the time each angle was in force, the trials' outcome
                 tables.

Geometry: the source at x = 0, Alice's station at x = −L_A, Bob's at x = +L_B (one line, lab frame); a pair's
particles reach the stations at t_e + L_A/v and t_e + L_B/v. Each station's clock starts its slots when the first
particle could arrive (L/v): slot k of station X is [L_X/v + k·T_s, L_X/v + (k + 1)·T_s), so the two particles of a
pair fall into slots of the same index (Giustina et al. 2015: «locally defined time slots»). With the random choice,
each station draws its setting bit for slot k from its own generator and makes it τ before the slot starts.
"""

from __future__ import annotations

import hashlib
import json
import math

import numpy as np

from lfphys.core import causality as K
from lfphys.core.quantum import qubits as Q
from lfphys.i18n import T
from lfphys.theories.alternatives import local_hidden as LHV
from lfphys.theories.models import photodetector as PD
from lfphys.tools import bell_stats as BS

PAIR_LABEL = {"photon": T("photons (polarisation)"), "spin": T("spin ½, singlet")}
MODEL_LABEL = {"polarization_model": T("polarisation model of local hidden variables (photons)"),
               "sign_model": T("Bell's sign model (spin ½)"),
               "gisin_gisin": T("Gisin and Gisin's local model (the detection loophole)")}

# the outcomes of a station with two detectors in one trial (bell_stats.outcome_labels(2)): "+" only, "−" only, none,
# both; their click sets as bit masks (bit 0: the "+" detector, bit 1: the "−" detector)
OUTCOMES = Q.TWO_DETECTOR_OUTCOMES
CLICKS = np.array([0b01, 0b10, 0b00, 0b11], np.int64)
CODE_OF = np.array([2, 0, 1, 3], np.int64)  # click set (mask) -> outcome index


def setup_key(params: dict) -> int:
    """The set-up's key: its parameters as sorted JSON, hashed to 64 bits (as u35's ``engine/bench.py rng_for``). Every
    generator of a run is seeded by the world's seed and this key together, so that every set-up of an atlas, all of
    which share one seed, draws its own independent sample (RULES §10). With the seed alone every point of a grid drew
    the same emission times, setting bits and outcome draws (common random numbers): E's residuals at β = 22.5° and 30°
    correlated with r = 0.36 over 400 seeds (0.07 with different seeds), and τ = 5 µs gave the same draws as
    τ = 100 ns (integrator I-P, 2026-11-19)."""
    text = json.dumps({k: params[k] for k in sorted(params)}, sort_keys=True, default=repr)
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "little")


def spin_direction(theta: float) -> np.ndarray:
    """Unit vector of a Stern-Gerlach direction at angle theta (rad) in the plane transverse to the flight (x, z of
    the spin's frame; theta from the z axis)."""
    return np.array([math.sin(theta), 0.0, math.cos(theta)])


def or_tables(p1, p2) -> np.ndarray:
    """The outcome table (4 x 4, ``OUTCOMES`` at A and B) of a trial in which two independent processes each give a
    click pattern (``p1``, ``p2``): a threshold detector clicks when either process makes it click, so the patterns
    combine by the union of the click sets."""
    out = np.zeros((4, 4))
    for a1 in range(4):
        for b1 in range(4):
            w = p1[a1, b1]
            if w == 0.0:
                continue
            for a2 in range(4):
                for b2 in range(4):
                    out[CODE_OF[CLICKS[a1] | CLICKS[a2]], CODE_OF[CLICKS[b1] | CLICKS[b2]]] += w * p2[a2, b2]
    return out


_PZ = [np.diag([1.0, 0.0]).astype(complex), np.diag([0.0, 1.0]).astype(complex)]  # the computational basis's ports


class Law:
    """The law of a world: the pair ("photon" | "spin"), the law ("quantum" | "lhv" | "gg"), the source's state
    ("max": |Φ+⟩ for photons, the singlet for spins; "eberhard": (|VH⟩ + r|HV⟩)/√(1 + r²), photons) and its
    visibility V (ρ = V|ψ⟩⟨ψ| + (1 − V) I/4)."""

    def __init__(self, pair: str, law: str, state: str = "max", r: float = -2.9, V: float = 1.0):
        if pair not in PAIR_LABEL or law not in ("quantum", "lhv", "gg") or state not in ("max", "eberhard"):
            raise ValueError(f"unknown pair {pair!r}, law {law!r} or state {state!r}")
        self.pair, self.law, self.state, self.r, self.V = pair, law, state, float(r), float(V)
        if state == "eberhard":
            base = Q.eberhard_state(self.r)
        else:
            base = Q.PHI_PLUS if pair == "photon" else Q.SINGLET
        self.psi = base
        self.rho = Q.werner(base, self.V) if law == "quantum" else None
        self.model = {"quantum": None, "lhv": "polarization_model" if pair == "photon" else "sign_model",
                      "gg": "gisin_gisin"}[law]
        self.gg_state = "phi_plus" if pair == "photon" else "singlet"
        # the period of E in the angle difference: a polariser at α and α + 180° is the same element
        self.period = 180.0 if pair == "photon" else 360.0
        self._cache: dict = {}

    # --- analysers (engine objects) ---
    def projectors(self, deg: float):
        r = math.radians(deg)
        return Q.polarizer_projectors(r) if self.pair == "photon" else Q.projectors(spin_direction(r))

    def observable(self, deg: float):
        r = math.radians(deg)
        return Q.polarizer_observable(r) if self.pair == "photon" else Q.n_sigma(spin_direction(r))

    def direction(self, deg: float) -> np.ndarray:
        """The analyser's Bloch (Poincaré) vector, for Gisin and Gisin's model."""
        r = math.radians(deg)
        return LHV.poincare(r) if self.pair == "photon" else spin_direction(r)

    # --- exact expectations ---
    def E_quantum(self, a_deg: float, b_deg: float, rho=None) -> float:
        return Q.correlation(self.rho if rho is None else rho, self.observable(a_deg), self.observable(b_deg))

    def E_lhv(self, a_deg: float, b_deg: float) -> float:
        ra, rb = math.radians(a_deg), math.radians(b_deg)
        if self.pair == "photon":
            return LHV.polarization_model_E(ra, rb)
        return LHV.sign_model_E(ra - rb)

    def E_gg(self, a_deg: float, b_deg: float) -> float:
        """Gisin and Gisin's model: the correlation of the pairs detected at both sides (−a·b for the singlet)."""
        return LHV.gisin_gisin_E(self.direction(a_deg), self.direction(b_deg), self.gg_state)

    def E(self, a_deg: float, b_deg: float) -> float:
        """The correlation of the world's law at these analyser angles (of the detected pairs for Gisin and Gisin's
        model; cached)."""
        key = (round(a_deg, 9), round(b_deg, 9))
        if key not in self._cache:
            E = {"quantum": self.E_quantum, "lhv": self.E_lhv, "gg": self.E_gg}[self.law](a_deg, b_deg)
            self._cache[key] = min(1.0, max(-1.0, E))  # round-off of the trace must not leave [-1, 1]
        return self._cache[key]

    def E_closed_form(self, a_deg: float, b_deg: float) -> float:
        """The textbook closed form of the quantum correlation of the source (a reference for the engine's trace, not
        used to sample): V cos 2(α − β) for |Φ+⟩, −V cos(θ_A − θ_B) for the singlet, and for Eberhard's state
        V(−cos 2α cos 2β + 2r/(1 + r²) sin 2α sin 2β)."""
        if self.state == "eberhard":
            a, b = math.radians(2 * a_deg), math.radians(2 * b_deg)
            return self.V * (-math.cos(a) * math.cos(b) + 2 * self.r / (1 + self.r ** 2) * math.sin(a) * math.sin(b))
        d = math.radians(a_deg - b_deg)
        return self.V * (math.cos(2 * d) if self.pair == "photon" else -math.cos(d))

    def S(self, a, a2, b, b2) -> float:
        return Q.chsh(self.E, a, a2, b, b2)

    def fold(self, d):
        """Angle difference folded into [-period/2, period/2)."""
        P = self.period
        return (np.asarray(d, float) + P / 2) % P - P / 2

    # --- the ports of one pair ---
    def port_table(self, a_deg: float, b_deg: float) -> np.ndarray:
        """P[i, j]: the probability that a pair's particle leaves Alice's analyser by port i and Bob's by port j (0:
        "+", the transmitted or "up" port; 1: "−"; for Gisin and Gisin's model 2: no outcome, the particle is not
        detected). Quantum: the engine's joint Born probabilities; the polarisation and sign models: outcomes ±1 with
        the model's fair marginals (½) and its correlation E, P = (1 + A·B·E)/4; Gisin and Gisin's model: the engine's
        closed form ``gisin_gisin_table``."""
        key = ("pt", round(a_deg, 9), round(b_deg, 9))
        if key in self._cache:
            return self._cache[key]
        if self.law == "quantum":
            P = Q.joint_probabilities(self.rho, self.projectors(a_deg), self.projectors(b_deg))
        elif self.law == "lhv":
            E = self.E(a_deg, b_deg)
            P = np.array([[1 + E, 1 - E], [1 - E, 1 + E]]) / 4.0
        else:
            P = LHV.gisin_gisin_table(self.direction(a_deg), self.direction(b_deg), self.gg_state)
        self._cache[key] = P
        return P

    def marginal_A(self, a_deg: float) -> np.ndarray:
        """Alice's port probabilities, whatever Bob's setting (quantum: the Born rule on the reduced state)."""
        if self.law == "quantum":
            return Q.joint_probabilities(self.rho, self.projectors(a_deg), [np.eye(2)])[:, 0]
        return self.port_table(a_deg, 0.0).sum(axis=1)

    def marginal_B(self, b_deg: float) -> np.ndarray:
        if self.law == "quantum":
            return Q.joint_probabilities(self.rho, [np.eye(2)], self.projectors(b_deg))[0, :]
        return self.port_table(0.0, b_deg).sum(axis=0)

    def sample(self, a_deg: float, b_deg: float, n: int, rng) -> tuple[np.ndarray, np.ndarray]:
        """The ports (0, 1; −1: no outcome) of n pairs measured together at these angles: quantum by the joint Born
        probabilities (``qubits.sample_pairs``), the local models by the engine's own samplers."""
        if n == 0:
            return np.zeros(0, np.int8), np.zeros(0, np.int8)
        if self.law == "quantum":
            iA, iB = Q.sample_pairs(self.rho, self.projectors(a_deg), self.projectors(b_deg), n, rng)
            return iA.astype(np.int8), iB.astype(np.int8)
        ra, rb = math.radians(a_deg), math.radians(b_deg)
        if self.law == "lhv":
            A, B = (LHV.polarization_model(ra, rb, n, rng) if self.pair == "photon" else LHV.sign_model(ra, rb, n, rng))
        else:
            A, B = LHV.gisin_gisin(self.direction(a_deg), self.direction(b_deg), n, rng, state=self.gg_state)
        A, B = np.asarray(A), np.asarray(B)
        return (np.where(A > 0, 0, np.where(A < 0, 1, -1)).astype(np.int8),
                np.where(B > 0, 0, np.where(B < 0, 1, -1)).astype(np.int8))

    def sample_first(self, side: str, deg: float, n: int, rng) -> np.ndarray:
        """Quantum only: the ports of the particles that reach their station first (the Born rule on the reduced
        state); the partner's port follows from ``sample_second`` (Lüders)."""
        p = self.marginal_A(deg) if side == "A" else self.marginal_B(deg)
        p = np.asarray(p, float) / float(np.sum(p))
        return (rng.random(n) >= p[0]).astype(np.int8)

    def sample_second(self, side: str, deg_first: float, deg: float, first: np.ndarray, rng) -> np.ndarray:
        """Quantum only: the ports of the partners measured second, conditioned on the first port of each pair."""
        P = self.port_table(deg_first, deg) if side == "B" else self.port_table(deg, deg_first).T
        out = np.empty(len(first), np.int8)
        u = rng.random(len(first))
        for i in (0, 1):
            m = first == i
            row = P[i] / max(float(P[i].sum()), 1e-300)
            out[m] = (u[m] >= row[0]).astype(np.int8)
        return out

    # --- the outcome probabilities of one trial (slot) ---
    def slot_table(self, a_deg: float, b_deg: float, eta_a: float, eta_b: float, pd_a: float, pd_b: float,
                   mu: float) -> np.ndarray:
        """P[o_A, o_B] over ``OUTCOMES`` for one slot with a Poisson number of pairs (mean μ), two detectors per
        station of efficiencies η and dark-click probabilities p_d (``bell_stats.slot_probabilities``). The local
        models: a classical port table is a state diagonal in the computational basis measured in that basis (exact
        for the table); Gisin and Gisin's pairs split (Poisson splitting) into three independent streams, both
        particles with an outcome (½ of the pairs, the table (1 + A·B·E)/4), Alice's alone (¼), Bob's alone (¼), whose
        click patterns combine by ``or_tables``."""
        key = ("st", round(a_deg, 9), round(b_deg, 9), eta_a, eta_b, pd_a, pd_b, mu)
        if key in self._cache:
            return self._cache[key]
        if self.law == "quantum":
            out = BS.slot_probabilities(self.rho, list(self.projectors(a_deg)), list(self.projectors(b_deg)), eta_a,
                                        eta_b, pd_a, pd_b, mu)
        elif self.law == "lhv":
            rho = np.diag(self.port_table(a_deg, b_deg).ravel()).astype(complex)
            out = BS.slot_probabilities(rho, _PZ, _PZ, eta_a, eta_b, pd_a, pd_b, mu)
        else:
            P = self.port_table(a_deg, b_deg)
            both = P[:2, :2] / P[:2, :2].sum()
            w_both, w_a, w_b = float(P[:2, :2].sum()), float(P[:2, 2].sum()), float(P[2, :2].sum())
            t1 = BS.slot_probabilities(np.diag(both.ravel()).astype(complex), _PZ, _PZ, eta_a, eta_b, pd_a, pd_b,
                                       mu * w_both)
            pa = P[:2, 2] / max(P[:2, 2].sum(), 1e-300)
            t2 = BS.slot_probabilities(np.diag(np.kron(pa, [0.5, 0.5])).astype(complex), _PZ, _PZ, eta_a, 0.0, 0.0,
                                       0.0, mu * w_a)
            pb = P[2, :2] / max(P[2, :2].sum(), 1e-300)
            t3 = BS.slot_probabilities(np.diag(np.kron([0.5, 0.5], pb)).astype(complex), _PZ, _PZ, 0.0, eta_b, 0.0,
                                       0.0, mu * w_b)
            out = or_tables(or_tables(t1, t2), t3)
        self._cache[key] = out
        return out

    # --- curves for the view ---
    def curves(self, n: int = 361):
        """E(Δ) over one period of the quantum law of this world's source (or of the ideal source in a local world),
        of the matching polarisation or sign model, of Gisin and Gisin's detected pairs."""
        d = np.linspace(-self.period / 2, self.period / 2, n)
        rho = self.rho if self.law == "quantum" else Q.dm(self.psi)
        q = np.array([self.E_quantum(x, 0.0, rho) for x in d])
        h = np.array([self.E_lhv(x, 0.0) for x in d])
        return d, q, h

    def s_curves(self, n: int = 181):
        """S(Δ) in the CHSH geometry a = 0, b = Δ, a′ = 2Δ, b′ = 3Δ, Δ from 0 to 90° (photons) or 180° (spins): the
        quantum law of the source (ideal in a local world), the local model, and this world's own law."""
        top = 90.0 if self.pair == "photon" else 180.0
        d = np.linspace(0.0, top, n)
        rho = self.rho if self.law == "quantum" else Q.dm(self.psi)
        qE = lambda a, b: self.E_quantum(a, b, rho)  # noqa: E731
        q = np.array([Q.chsh(qE, 0.0, 2 * x, x, 3 * x) for x in d])
        h = np.array([Q.chsh(self.E_lhv, 0.0, 2 * x, x, 3 * x) for x in d])
        w = np.array([self.S(0.0, 2 * x, x, 3 * x) for x in d])
        return d, q, h, w

    def describe(self) -> T:
        if self.law == "quantum":
            return T("{pair}: quantum mechanics", pair=PAIR_LABEL[self.pair])
        return T("{pair}: {model}", pair=PAIR_LABEL[self.pair], model=MODEL_LABEL[self.model])


# --- the counts --------------------------------------------------------------------------------------------------
def _key(a: float, b: float):
    return (round(float(a), 9), round(float(b), 9))


class Store:
    """The counts per pair of analyser angles (deg) actually used: ``coinc`` (N++, N+−, N−+, N−−) of all coincidences
    and ``acc`` of the accidental ones (the two particles of different pairs, or a dark or background count: known only
    in a simulation); per station and angle the singles of each detector and the time the angle was in force (closed
    trials × T_s); per pair of angles the trials and their outcome table (4 x 4, ``OUTCOMES``)."""

    MAX_KEYS = 200

    def __init__(self):
        self.clear()

    key = staticmethod(_key)

    def clear(self):
        self.coinc: dict = {}
        self.acc: dict = {}
        self.slots: dict = {}
        # the counting by slots: the outcome tables of the slots simulated in time (``Slots``), and their expectation
        # from the engine's slot probabilities accumulated with them (so that a live change of the rate or the angles
        # keeps the comparison exact)
        self.timed: dict = {}
        self.timed_exp: dict = {}
        self.singles = {"A": {}, "B": {}}
        self.time = {"A": {}, "B": {}}

    def _cell(self, d, k, shape):
        if k not in d:
            d[k] = np.zeros(shape, np.int64)
        return d[k]

    @staticmethod
    def _pairs(alA, alB):
        """The distinct angle pairs of two arrays (vectorised)."""
        if len(alA) == 0:
            return []
        u = np.unique(np.stack([np.asarray(alA, float), np.asarray(alB, float)], axis=1), axis=0)
        return [(float(a), float(b)) for a, b in u]

    def add_coinc(self, alA, alB, idx, true, protect=()):
        for a, b in self._pairs(alA, alB):
            m = (alA == a) & (alB == b)
            k = _key(a, b)
            self._cell(self.coinc, k, 4)[:] += np.bincount(idx[m], minlength=4)
            self._cell(self.acc, k, 4)[:] += np.bincount(idx[m & ~true], minlength=4)
        self._trim(protect)

    def add_trials(self, alA, alB, oA, oB):
        for a, b in self._pairs(alA, alB):
            m = (alA == a) & (alB == b)
            np.add.at(self._cell(self.slots, _key(a, b), (4, 4)), (oA[m], oB[m]), 1)

    def add_singles(self, side, angles, det, counts):
        """``counts[k]`` singles of detector ``det[k]`` at angle ``angles[k]``."""
        for a in np.unique(np.asarray(angles, float)).tolist():
            m = angles == a
            c = self.singles[side].setdefault(round(a, 9), np.zeros(2, np.int64))
            c += np.bincount(det[m], weights=counts[m], minlength=2).astype(np.int64)

    def add_time(self, side, angles, dt):
        """``dt`` of time for each entry of ``angles``."""
        u, n = np.unique(np.asarray(angles, float), return_counts=True)
        for a, k_ in zip(u.tolist(), n.tolist()):
            k = round(a, 9)
            self.time[side][k] = self.time[side].get(k, 0.0) + dt * int(k_)

    def _trim(self, protect):
        prot = {_key(*p) for p in protect}
        while len(self.coinc) > self.MAX_KEYS:  # drop the oldest angle pair that is not in use
            old = next((k for k in self.coinc if k not in prot), None)
            if old is None:
                break
            for d in (self.coinc, self.acc, self.slots):
                d.pop(old, None)

    def get(self, a: float, b: float) -> np.ndarray:
        return self.coinc.get(_key(a, b), np.zeros(4, np.int64))

    def get_acc(self, a: float, b: float) -> np.ndarray:
        return self.acc.get(_key(a, b), np.zeros(4, np.int64))

    def get_slots(self, a: float, b: float) -> np.ndarray:
        return self.slots.get(_key(a, b), np.zeros((4, 4), np.int64))

    def get_singles(self, side: str, a: float) -> np.ndarray:
        return self.singles[side].get(round(float(a), 9), np.zeros(2, np.int64))

    def get_time(self, side: str, a: float) -> float:
        return self.time[side].get(round(float(a), 9), 0.0)


# --- the time stream ---------------------------------------------------------------------------------------------
class Bits:
    """A station's random setting bits, one per slot index k ≥ 0, drawn from its own generator in blocks (the same
    bits whatever the steps of the run)."""

    BLOCK = 1 << 15

    def __init__(self, rng):
        self.rng = rng
        self.blocks: dict = {}
        self.drawn = 0  # blocks drawn so far

    def get(self, k) -> np.ndarray:
        k = np.asarray(k, np.int64)
        if k.size == 0:
            return np.zeros(0, np.int8)
        b = k // self.BLOCK
        hi = int(b.max())
        while self.drawn <= hi:
            self.blocks[self.drawn] = self.rng.integers(0, 2, self.BLOCK).astype(np.int8)
            self.drawn += 1
        lo = int(b.min())
        for old in [x for x in self.blocks if x < lo - 2]:
            del self.blocks[old]
        out = np.empty(k.shape, np.int8)
        for blk in np.unique(b):
            m = b == blk
            out[m] = self.blocks[int(blk)][k[m] - int(blk) * self.BLOCK]
        return out


class Emissions:
    """The source's Poisson stream: unit exponential gaps from its own generator in blocks; a block's emission times
    are computed at once (the same times whatever the steps of the run; a change of the rate starts a new block at the
    moment of the change: the stream is memoryless)."""

    BLOCK = 4096

    def __init__(self, rng, rate: float, t0: float = 0.0):
        self.rng, self.rate = rng, float(rate)
        self.times = np.zeros(0)
        self.i = 0
        self._block(t0)

    def _block(self, base: float):
        g = self.rng.standard_exponential(self.BLOCK) / self.rate
        self.times = base + np.cumsum(g)
        self.i = 0

    def until(self, t_hi: float) -> np.ndarray:
        """The emission times before t_hi not given before."""
        out = []
        while True:
            j = int(np.searchsorted(self.times, t_hi, side="left"))
            out.append(self.times[self.i:j])
            if j < len(self.times):
                self.i = j
                break
            self._block(float(self.times[-1]))
        return np.concatenate(out)

    def next_time(self) -> float:
        return float(self.times[self.i])

    def set_rate(self, rate: float, now: float):
        self.rate = float(rate)
        self._block(now)


F_LOC_A = 1   # Alice's setting choice is space-like to Bob's detection
F_LOC_B = 2   # Bob's setting choice is space-like to Alice's detection
F_FREE_A = 4  # Alice's setting choice is space-like to the pair's emission (true coincidences only)
F_FREE_B = 8
F_TRUE = 16   # both clicks come from the same pair (known only in a simulation)

TAIL_S = 2e-6  # tags kept from the previous steps for the coincidences that straddle a step (compensated time)


class Stream:
    """The time stream of the run; see the module's docstring. ``P``: the world's parameters (the devices in SI
    units: ``eta_A``, ``eta_B``, ``dark``, ``dead``, ``sigma``, ``w``, ``Ts``, ``tau``, ``L_A``, ``L_B``, ``rate``,
    ``switch``, the four angles), ``seed``: the world's seed and its set-up's key (``setup_key``; the emissions and the
    setting bits take their own generators from them)."""

    def __init__(self, law: Law, v: float, c: float, P: dict, rng, seed: tuple[int, int]):
        self.law, self.v, self.c, self.rng = law, float(v), float(c), rng
        self.P = dict(P)
        ss = np.random.SeedSequence([*(int(x) for x in seed), 37])
        g_em, g_a, g_b = (np.random.default_rng(s) for s in ss.spawn(3))
        self.em = Emissions(g_em, P["rate"])
        self.bits = {"A": Bits(g_a), "B": Bits(g_b)}
        self.t_lo = 0.0
        self.next_id = 0
        self.fl = {k: np.zeros(0) for k in ("te", "tA", "tB")}
        self.fl.update(id=np.zeros(0, np.int64), pA=np.zeros(0, np.int8), pB=np.zeros(0, np.int8),
                       aA=np.zeros(0), aB=np.zeros(0))
        self.dead_until = {(s, i): -math.inf for s in "AB" for i in (0, 1)}
        self.tail = {s: self._empty_tags() for s in "AB"}
        self.open = {s: self._empty_tags() for s in "AB"}  # tags of slots not yet closed (by trial)
        self.next_trial = 0
        self.angle_log = [(-math.inf, self.angles())]
        self.t_set = {"A": (0.0, -P["L_A"]), "B": (0.0, P["L_B"])}  # when (and where) the fixed settings were set
        self.counts = dict(emitted=0, arrived=0, lost=0, both=0)
        self.recent_slots = np.zeros((0, 6))  # the latest closed trials: k, sA, sB, oA, oB, flags (for the view)

    @staticmethod
    def _empty_tags():
        return {"t": np.zeros(0), "c": np.zeros(0), "det": np.zeros(0, np.int8), "id": np.zeros(0, np.int64),
                "k": np.zeros(0, np.int64), "s": np.zeros(0, np.int8), "al": np.zeros(0), "te": np.zeros(0),
                "tc": np.zeros(0), "xc": np.zeros(0)}

    # --- the set-up ---
    def angles(self) -> dict:
        P = self.P
        return {"a": P["a_deg"], "a2": P["a2_deg"], "b": P["b_deg"], "b2": P["b2_deg"]}

    def off(self, side: str) -> float:
        return (self.P["L_A"] if side == "A" else self.P["L_B"]) / self.v

    def slot_of(self, side: str, t) -> np.ndarray:
        return np.floor((np.asarray(t, float) - self.off(side)) / self.P["Ts"]).astype(np.int64)

    def setting(self, side: str, k) -> np.ndarray:
        """The setting bit (0: a or b; 1: a′ or b′) of slot k; fixed settings: always 0."""
        k = np.asarray(k, np.int64)
        if self.P["switch"] != "random":
            return np.zeros(k.shape, np.int8)
        return self.bits[side].get(np.maximum(k, 0))

    def angle_of(self, side: str, s, t) -> np.ndarray:
        """The analyser angle of setting s in force at time t (the angles change only by the experimenter's hand)."""
        s = np.asarray(s)
        t = np.asarray(t, float)
        ts = np.array([x[0] for x in self.angle_log])
        j = np.searchsorted(ts, t, side="right") - 1
        names = ("a", "a2") if side == "A" else ("b", "b2")
        tab = np.array([[x[1][names[0]], x[1][names[1]]] for x in self.angle_log])
        return tab[np.maximum(j, 0), s.astype(np.int64)]

    def choice_time(self, side: str, k) -> np.ndarray:
        """When the setting of slot k was chosen: τ before the slot starts (random), or when it was set (fixed)."""
        k = np.asarray(k, np.int64)
        if self.P["switch"] == "random":
            return self.off(side) + k * self.P["Ts"] - self.P["tau"]
        return np.full(k.shape, self.t_set[side][0], float)

    def detector(self, side: str) -> PD.Detector:
        P = self.P
        return PD.Detector(eta=P["eta_A"] if side == "A" else P["eta_B"], dark_rate=P["dark"], dead_time=P["dead"],
                           jitter_sigma=0.0)

    # --- live changes ---
    def change(self, new: dict, now: float):
        """A change of the set-up at ``now``: new angles from now on, the rate (a new block of the memoryless stream),
        the mode of the choice, τ, the window."""
        old = self.P
        self.P = dict(new)
        if any(old[k] != new[k] for k in ("a_deg", "a2_deg", "b_deg", "b2_deg")):
            self.angle_log.append((now, self.angles()))
        if old["rate"] != new["rate"]:
            self.em.set_rate(new["rate"], now)
        if old["switch"] != new["switch"]:
            self.t_set = {"A": (now, -new["L_A"]), "B": (now, new["L_B"])}
        if old["a_deg"] != new["a_deg"]:
            self.t_set["A"] = (now, -new["L_A"])
        if old["b_deg"] != new["b_deg"]:
            self.t_set["B"] = (now, new["L_B"])

    # --- one step ---
    def step(self, t_target: float, store: Store, protect) -> dict:
        """Advance to t_target: emissions, arrivals with their ports, detections, coincidences, closed trials.
        Returns what happened in this step (the new coincidences and the latest tags, for the run's messages)."""
        t_lo, t_hi = self.t_lo, float(np.nextafter(t_target, math.inf))
        P, law = self.P, self.law
        te = self.em.until(t_hi)
        n = len(te)
        if n:
            ids = np.arange(self.next_id, self.next_id + n, dtype=np.int64)
            self.next_id += n
            self.counts["emitted"] += n
            new = {"te": te, "tA": te + P["L_A"] / self.v, "tB": te + P["L_B"] / self.v, "id": ids,
                   "pA": np.full(n, -2, np.int8), "pB": np.full(n, -2, np.int8), "aA": np.full(n, np.nan),
                   "aB": np.full(n, np.nan)}
            for k in self.fl:
                self.fl[k] = np.concatenate([self.fl[k], new[k]])
        self._arrivals(t_hi)
        tags = {s: self._detect(s, t_lo, t_hi) for s in "AB"}
        f = self.fl
        done = (f["pA"] != -2) & (f["pB"] != -2) & (f["tA"] < t_hi) & (f["tB"] < t_hi)
        if np.any(done):  # pairs whose both particles have arrived leave the flight
            for k in f:
                f[k] = f[k][~done]
        out = self._coincidences(tags, t_hi, store, protect)
        for s in "AB":
            self.open[s] = {k: np.concatenate([self.open[s][k], tags[s][k]]) for k in tags[s]}
        self._close_trials(t_hi, store)
        self.t_lo = t_hi
        out["tags"] = tags
        return out

    def _arrivals(self, t_hi: float):
        """The ports of the particles that reach their stations before t_hi: the setting of the slot of the arrival,
        the law's outcome probabilities at those angles (quantum: the first particle by the reduced state, its partner
        conditioned on it; the local models need both at once, L_A = L_B)."""
        f, law = self.fl, self.law
        for side, other in (("A", "B"), ("B", "A")):
            due = (f["p" + side] == -2) & (f["t" + side] < t_hi)
            if not np.any(due):
                continue
            idx = np.flatnonzero(due)
            t = f["t" + side][idx]
            s = self.setting(side, self.slot_of(side, t))
            f["a" + side][idx] = self.angle_of(side, s, t)
            partner_done = f["p" + other][idx] != -2
            together = (~partner_done) & (f["t" + other][idx] < t_hi)
            if law.law != "quantum" or np.any(together):
                # both particles arrive in this step: their ports together, at both settings
                j = idx[together] if law.law == "quantum" else idx
                to = f["t" + other][j]
                so = self.setting(other, self.slot_of(other, to))
                f["a" + other][j] = self.angle_of(other, so, to)
                aS, aO = f["a" + side][j], f["a" + other][j]
                pS = np.empty(len(j), np.int8)
                pO = np.empty(len(j), np.int8)
                for x in np.unique(aS):
                    for y in np.unique(aO):
                        m = (aS == x) & (aO == y)
                        if np.any(m):
                            a, b = (x, y) if side == "A" else (y, x)
                            iA, iB = law.sample(float(a), float(b), int(m.sum()), self.rng)
                            pS[m], pO[m] = (iA, iB) if side == "A" else (iB, iA)
                f["p" + side][j], f["p" + other][j] = pS, pO
                if law.law != "quantum":
                    continue
            first = idx[~partner_done & ~together]
            if len(first):
                for x in np.unique(f["a" + side][first]):
                    m = f["a" + side][first] == x
                    f["p" + side][first[m]] = law.sample_first(side, float(x), int(m.sum()), self.rng)
            second = idx[partner_done]
            if len(second):
                for x in np.unique(f["a" + other][second]):
                    for y in np.unique(f["a" + side][second]):
                        m = (f["a" + other][second] == x) & (f["a" + side][second] == y)
                        if np.any(m):
                            jj = second[m]
                            f["p" + side][jj] = law.sample_second(side, float(x), float(y), f["p" + other][jj],
                                                                  self.rng)

    def _detect(self, side: str, t_lo: float, t_hi: float) -> dict:
        """The detectors of a station in [t_lo, t_hi): the particles that arrived at each port, the engine's detector
        (efficiency, dark and background counts, dead time) from the end of its last dead time, the recorded times
        jittered; each tag knows its pair (an arrival time is recorded unchanged) or −1 (a dark or background
        count)."""
        f, P = self.fl, self.P
        t_arr = f["t" + side]
        arrived = (t_arr >= t_lo) & (t_arr < t_hi) & (f["p" + side] != -2)
        self.counts["arrived"] += int(np.sum(arrived))
        self.counts["lost"] += int(np.sum(arrived & (f["p" + side] == -1)))
        det = self.detector(side)
        parts = []
        for i in (0, 1):
            m = arrived & (f["p" + side] == i)
            order = np.argsort(t_arr[m], kind="stable")
            at, aid, ate = t_arr[m][order], f["id"][m][order], f["te"][m][order]
            t0 = max(t_lo, self.dead_until[(side, i)])
            raw = PD.detect(at, det, t0, t_hi, self.rng) if t0 < t_hi else np.zeros(0)
            if len(raw):
                self.dead_until[(side, i)] = float(raw[-1]) + P["dead"]
            j = np.minimum(np.searchsorted(at, raw), max(len(at) - 1, 0))
            hit = (len(at) > 0) & (at[j] == raw) if len(at) else np.zeros(len(raw), bool)
            tid = np.where(hit, aid[j] if len(at) else -1, -1).astype(np.int64)
            tte = np.where(hit, ate[j] if len(at) else np.nan, np.nan)
            tag = raw + self.rng.normal(0.0, P["sigma"], len(raw)) if P["sigma"] > 0 else raw.copy()
            parts.append((tag, np.full(len(raw), i, np.int8), tid, tte))
        t = np.concatenate([p[0] for p in parts])
        o = np.argsort(t, kind="stable")
        tg = {"t": t[o], "det": np.concatenate([p[1] for p in parts])[o], "id": np.concatenate([p[2] for p in parts])[o],
              "te": np.concatenate([p[3] for p in parts])[o]}
        tg["c"] = tg["t"] - self.off(side)
        tg["k"] = np.floor(tg["c"] / P["Ts"]).astype(np.int64)
        keep = tg["k"] >= 0  # before the station's first slot its clock has not started
        tg = {k: v[keep] for k, v in tg.items()}
        tg["s"] = self.setting(side, tg["k"])
        tg["al"] = self.angle_of(side, tg["s"], tg["t"])
        tg["tc"] = self.choice_time(side, tg["k"])
        tg["xc"] = np.full(len(tg["t"]), -P["L_A"] if side == "A" else P["L_B"])
        return tg

    def _coincidences(self, tags: dict, t_hi: float, store: Store, protect) -> dict:
        """Every pair of tags (A, B) within the window, |c_B − c_A| ≤ w/2 on the delay-compensated times c, that
        involves a tag of this step (the tags of the previous steps' tail were matched there): the same rule as
        ``photodetector.coincidences`` (every pair counted), enumerated."""
        P = self.P
        w = P["w"]
        cat = {}
        for s in "AB":
            tl, nw = self.tail[s], tags[s]
            cat[s] = {k: np.concatenate([tl[k], nw[k]]) for k in nw}
            cat[s]["new"] = np.concatenate([np.zeros(len(tl["t"]), bool), np.ones(len(nw["t"]), bool)])
        A, B = cat["A"], cat["B"]
        lo = np.searchsorted(B["c"], A["c"] - 0.5 * w, side="left")
        hi = np.searchsorted(B["c"], A["c"] + 0.5 * w, side="right")
        cnt = hi - lo
        ia = np.repeat(np.arange(len(A["c"])), cnt)
        ib = (np.repeat(lo - np.cumsum(np.concatenate([[0], cnt[:-1]])), cnt) + np.arange(int(cnt.sum()))) \
            if len(ia) else np.zeros(0, np.int64)
        keep = A["new"][ia] | B["new"][ib]
        ia, ib = ia[keep], ib[keep]
        # the pairs whose both particles were detected (any time difference: the window's share of them)
        both = np.intersect1d(A["id"][(A["id"] >= 0)], B["id"][(B["id"] >= 0)])
        old_both = np.intersect1d(self.tail["A"]["id"][self.tail["A"]["id"] >= 0],
                                  self.tail["B"]["id"][self.tail["B"]["id"] >= 0])
        self.counts["both"] += len(both) - len(old_both)
        for s in "AB":  # the tail for the next step: the latest tags in compensated time
            m = cat[s]["c"] >= t_hi - self.off(s) - TAIL_S
            self.tail[s] = {k: v[m] for k, v in cat[s].items() if k != "new"}
        out = {"n": len(ia)}
        if not len(ia):
            return out
        true = (A["id"][ia] == B["id"][ib]) & (A["id"][ia] >= 0)
        idx = (2 * A["det"][ia] + B["det"][ib]).astype(np.int64)
        store.add_coinc(A["al"][ia], B["al"][ib], idx, true, protect)
        c = self.c
        chA = np.stack([A["tc"][ia], A["xc"][ia]], axis=1)
        chB = np.stack([B["tc"][ib], B["xc"][ib]], axis=1)
        detA = np.stack([A["t"][ia], np.full(len(ia), -P["L_A"])], axis=1)
        detB = np.stack([B["t"][ib], np.full(len(ia), P["L_B"])], axis=1)
        sp = K.SPACELIKE
        fl = np.where(true, F_TRUE, 0).astype(np.uint8)
        fl |= np.where(np.atleast_1d(K.relation(chA, detB, c)) == sp, F_LOC_A, 0).astype(np.uint8)
        fl |= np.where(np.atleast_1d(K.relation(chB, detA, c)) == sp, F_LOC_B, 0).astype(np.uint8)
        te = np.where(true, A["te"][ia], np.nan)
        em = np.stack([np.nan_to_num(te), np.zeros(len(ia))], axis=1)
        fA = np.atleast_1d(K.relation(chA, em, c)) == sp
        fB = np.atleast_1d(K.relation(chB, em, c)) == sp
        fl |= np.where(true & fA, F_FREE_A, 0).astype(np.uint8)
        fl |= np.where(true & fB, F_FREE_B, 0).astype(np.uint8)
        order = np.argsort(np.maximum(A["t"][ia], B["t"][ib]), kind="stable")
        out.update({"tA": A["t"][ia][order], "tB": B["t"][ib][order], "te": te[order], "id": A["id"][ia][order],
                    "sA": A["s"][ia][order], "sB": B["s"][ib][order], "oA": (1 - 2 * A["det"][ia][order]).astype(np.int8),
                    "oB": (1 - 2 * B["det"][ib][order]).astype(np.int8), "alA": A["al"][ia][order],
                    "alB": B["al"][ib][order], "tcA": A["tc"][ia][order], "tcB": B["tc"][ib][order],
                    "fl": fl[order], "true": true[order]})
        return out

    def _close_trials(self, t_hi: float, store: Store):
        """The trials (slot indices) whose slots have ended at both stations, with a margin for the jitter (10 σ):
        each station's outcome («+», «−», «0», «+−») from the tags in its slot, the singles of each detector, the time
        of each angle; tallied per pair of angles (by integer codes: the angle-log entry and the setting bit of each
        station)."""
        P = self.P
        margin = 10.0 * P["sigma"] + 1e-12
        k_end = int(math.floor((t_hi - margin - max(self.off("A"), self.off("B"))) / P["Ts"]))  # trials < k_end closed
        k0 = self.next_trial
        if k_end <= k0:
            return
        ks = np.arange(k0, k_end, dtype=np.int64)
        n = len(ks)
        log_t = np.array([x[0] for x in self.angle_log])
        names = {"A": ("a", "a2"), "B": ("b", "b2")}
        codes, outc = {}, {}
        for s in "AB":
            op = self.open[s]
            m = op["k"] < k_end
            ok = m & (op["k"] >= k0)  # (a tag of a closed trial would need a jitter beyond the margin)
            kk, dd = op["k"][ok] - k0, op["det"][ok].astype(np.int64)
            mask = np.zeros(n, np.int64)
            np.bitwise_or.at(mask, kk, 1 << dd)
            outc[s] = CODE_OF[mask]
            j = np.maximum(np.searchsorted(log_t, self.off(s) + ks * P["Ts"], side="right") - 1, 0)
            codes[s] = 2 * j + self.setting(s, ks).astype(np.int64)
            M = 2 * len(self.angle_log)
            angle = lambda c, s=s: float(self.angle_log[c // 2][1][names[s][c % 2]])  # noqa: E731
            for c, cnt in enumerate(np.bincount(codes[s], minlength=M)):
                if cnt:
                    store.add_time(s, np.array([angle(c)]), P["Ts"] * float(cnt))
            if len(kk):
                sg = np.bincount(codes[s][kk] * 2 + dd, minlength=2 * M).reshape(M, 2)
                for c in np.flatnonzero(sg.sum(axis=1)):
                    store.add_singles(s, np.array([angle(int(c)), angle(int(c))]), np.array([0, 1]), sg[c])
            self.open[s] = {k: v[~m] for k, v in op.items()}
        M = 2 * len(self.angle_log)
        pc = codes["A"] * M + codes["B"]
        tab = np.bincount(pc * 16 + outc["A"] * 4 + outc["B"], minlength=M * M * 16).reshape(M * M, 4, 4)
        for c in np.flatnonzero(tab.reshape(M * M, 16).sum(axis=1)):
            cA, cB = divmod(int(c), M)
            a = float(self.angle_log[cA // 2][1][names["A"][cA % 2]])
            b = float(self.angle_log[cB // 2][1][names["B"][cB % 2]])
            store._cell(store.slots, _key(a, b), (4, 4))[:] += tab[c]
        self.next_trial = k_end
        n_show = 48
        sl = slice(max(0, n - n_show), None)
        rec = np.stack([ks[sl].astype(float), (codes["A"][sl] % 2).astype(float), (codes["B"][sl] % 2).astype(float),
                        outc["A"][sl].astype(float), outc["B"][sl].astype(float), np.zeros(len(ks[sl]))], axis=1)
        self.recent_slots = np.concatenate([self.recent_slots, rec])[-n_show:]

    def in_flight(self, limit: int = 120) -> np.ndarray:
        """(k, 4): the latest pairs in flight: emission time, arrival at A, arrival at B, pair id."""
        f = self.fl
        k = min(limit, len(f["te"]))
        sl = slice(len(f["te"]) - k, None)
        return np.stack([f["te"][sl], f["tA"][sl], f["tB"][sl], f["id"][sl].astype(float)], axis=1) if k \
            else np.zeros((0, 4))

    @property
    def n_flight(self) -> int:
        return len(self.fl["te"])

    def next_time(self) -> float:
        c = [self.em.next_time()]
        f = self.fl
        for s in "AB":
            m = f["p" + s] == -2
            if np.any(m):
                c.append(float(f["t" + s][m].min()))
        return min(c)


# --- the counting by slots (part 4 of the lab) ----------------------------------------------------------------------
class Slots:
    """The counting of many slots at once (EX2 design §4.7, «Statistics of long runs»): the trials whose slots end in
    a step are split among the setting pairs (each station's fair bit per slot: a multinomial of ¼ each; fixed
    settings: all at (a, b)); for each setting pair the trials' outcome counts are drawn from the engine's exact
    multinomial (``bell_stats.sample_counts`` of ``Law.slot_table``: η, dark and background clicks, a Poisson number
    of pairs per slot), the coincidences and the singles from Poisson laws of the engine's rates over the time of that
    setting pair (``photodetector.coincidence_rates``: true and accidental separately, so the run knows its own
    accidentals). The slots are independent trials when (t_d + 5σ)/T_s ≪ 1 (the world refuses this mode otherwise).
    The two draws are each exact in distribution; that the same clicks make a slot's outcome and a coincidence is not
    modelled here (it is in the time stream). ``N_TIME`` slots before the end of each step are simulated in time
    (``photodetector.pair_slots``, its own generator: Poisson emissions, the ports by the law, each detector's
    efficiency, dark counts, dead time and jitter, the clicks binned into the slots): a separate sample of the same
    process, not added to the counts. Its outcome tables against the engine's slot probabilities are the run's
    independent check of the counting by slots (review R2-W F2: the counts themselves are drawn from those
    probabilities); its last ``N_SHOW`` slots are shown."""

    N_SHOW = 40
    N_TIME = 100_000

    def __init__(self, law: Law, P: dict, rng, seed: tuple[int, int], v: float):
        self.law, self.rng, self.v = law, rng, float(v)
        self.P = dict(P)
        ss = np.random.SeedSequence([*(int(x) for x in seed), 38])
        self.g_show = np.random.default_rng(ss.spawn(1)[0])
        self.k_done = 0
        self.counts = dict(emitted=0, arrived=0, lost=0, both=0)
        self.t_set = {"A": (0.0, -P["L_A"]), "B": (0.0, P["L_B"])}
        self.recent_slots = np.zeros((0, 6))

    def angles(self) -> dict:
        P = self.P
        return {"a": P["a_deg"], "a2": P["a2_deg"], "b": P["b_deg"], "b2": P["b2_deg"]}

    def change(self, new: dict, now: float):
        old, self.P = self.P, dict(new)
        if old["switch"] != new["switch"]:
            self.t_set = {"A": (now, -new["L_A"]), "B": (now, new["L_B"])}

    def detectors(self, side: str, jitter: bool = True) -> PD.Detector:
        P = self.P
        return PD.Detector(eta=P["eta_A"] if side == "A" else P["eta_B"], dark_rate=P["dark"], dead_time=P["dead"],
                           jitter_sigma=P["sigma"] if jitter else 0.0)

    def step(self, t_target: float, store: Store) -> dict:
        P, law = self.P, self.law
        Ts = P["Ts"]
        k_end = int(math.floor((t_target - max(P["L_A"], P["L_B"]) / self.v) / Ts + 1e-9))
        n = k_end - self.k_done
        out = {"coinc": 0, "true": 0, "shown": None}
        if n <= 0:
            return out
        self.counts["emitted"] += int(self.rng.poisson(P["rate"] * n * Ts))
        if P["switch"] == "random":
            split = self.rng.multinomial(n, [0.25] * 4).reshape(2, 2)
        else:
            split = np.array([[n, 0], [0, 0]])
        names = (("a", "a2"), ("b", "b2"))
        ang = self.angles()
        pd = PD.dark_click_probability(P["dark"], Ts)
        mu = P["rate"] * Ts
        dA, dB = self.detectors("A"), self.detectors("B")
        for sA in (0, 1):
            for sB in (0, 1):
                ns = int(split[sA, sB])
                if ns == 0:
                    continue
                a, b = ang[names[0][sA]], ang[names[1][sB]]
                tab = BS.sample_counts(law.slot_table(a, b, P["eta_A"], P["eta_B"], pd, pd, mu), ns, self.rng)
                key = _key(a, b)
                cell = store._cell(store.slots, key, (4, 4))
                cell += tab
                T_ = ns * Ts
                r = PD.coincidence_rates(P["rate"], law.port_table(a, b), [dA, dA], [dB, dB], P["w"])
                true = self.rng.poisson(r["true"][:2, :2].ravel() * T_)
                acc = self.rng.poisson(r["accidental"].ravel() * T_)
                store._cell(store.coinc, key, 4)[:] += true + acc
                store._cell(store.acc, key, 4)[:] += acc
                out["coinc"] += int(np.sum(true + acc))
                out["true"] += int(np.sum(true))
                store.add_singles("A", np.array([a, a]), np.array([0, 1]), self.rng.poisson(r["singles_a"] * T_))
                store.add_singles("B", np.array([b, b]), np.array([0, 1]), self.rng.poisson(r["singles_b"] * T_))
                store.add_time("A", np.array([a]), T_)
                store.add_time("B", np.array([b]), T_)
        self.k_done = k_end
        out["shown"] = self._in_time(k_end, store)
        return out

    def _in_time(self, k_end: int, store: Store) -> np.ndarray:
        """``N_TIME`` trials ending at slot k_end simulated in time, their outcome tables added to ``store.timed`` and
        the engine's slot probabilities times their numbers to ``store.timed_exp`` (per pair of angles); the last
        ``N_SHOW`` returned for the view: (k, setting A, setting B, outcome A, outcome B, clicks of pairs)."""
        P, law = self.P, self.law
        m = self.N_TIME
        g = self.g_show
        if P["switch"] == "random":
            sa, sb = g.integers(0, 2, m), g.integers(0, 2, m)
        else:
            sa, sb = np.zeros(m, np.int64), np.zeros(m, np.int64)
        ang = self.angles()
        A, B = (ang["a"], ang["a2"]), (ang["b"], ang["b2"])
        ports = [[law.port_table(A[x], B[y]) for y in (0, 1)] for x in (0, 1)]
        dA, dB = self.detectors("A"), self.detectors("B")
        t0 = (k_end - m) * P["Ts"]
        (ca, cb), _tags = PD.pair_slots(m, P["Ts"], P["rate"], ports, sa, sb, [dA, dA], [dB, dB], g, t0=t0)
        oA = CODE_OF[ca[0].astype(np.int64) | (ca[1].astype(np.int64) << 1)]
        oB = CODE_OF[cb[0].astype(np.int64) | (cb[1].astype(np.int64) << 1)]
        pd = PD.dark_click_probability(P["dark"], P["Ts"])
        mu = P["rate"] * P["Ts"]
        for x in (0, 1):
            for y in (0, 1):
                sel = (sa == x) & (sb == y)
                n = int(sel.sum())
                if not n:
                    continue
                key = _key(A[x], B[y])
                np.add.at(store._cell(store.timed, key, (4, 4)), (oA[sel], oB[sel]), 1)
                if key not in store.timed_exp:
                    store.timed_exp[key] = np.zeros((4, 4))
                store.timed_exp[key] += n * law.slot_table(A[x], B[y], P["eta_A"], P["eta_B"], pd, pd, mu)
        k = self.N_SHOW
        rec = np.stack([np.arange(k_end - k, k_end, dtype=float), sa[-k:].astype(float), sb[-k:].astype(float),
                        oA[-k:].astype(float), oB[-k:].astype(float), np.zeros(k)], axis=1)
        self.recent_slots = rec
        return rec

    def in_flight(self, limit: int = 120) -> np.ndarray:
        return np.zeros((0, 4))

    @property
    def n_flight(self) -> int:
        return 0

    def next_time(self):
        return None
