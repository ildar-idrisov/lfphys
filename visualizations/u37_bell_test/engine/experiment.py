# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Apparatus logic of the Bell test: a wrapper over lfphys (orchestration, not physics laws).

* ``Law``        - the world's correlation law for one pair type. Outcomes and their exact expectations come from the
                   engine: Born rule on the entangled state (lfphys.core.quantum.qubits) or a local hidden-variable
                   model (lfphys.theories.alternatives.local_hidden). Nothing here computes a probability by itself.
* ``Experiment`` - the pairs in flight (emission time, arrival time at the stations, the stations' setting choices),
                   the stations' choice events, the detections, and the space-time relations of each pair's events
                   (lfphys.core.causality).
* ``Store``      - coincidence counts N(+-,+-) per pair of analyzer angles actually used.

Geometry: the source at x = 0, Alice's station at x = -L, Bob's at x = +L (one line, lab frame). Both particles of a
pair fly at the same speed v, so they arrive at their stations at the same lab time t_e + L/v.
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.core import causality as K
from lfphys.core.quantum import qubits as Q
from lfphys.i18n import T
from lfphys.theories.alternatives import local_hidden as LHV

PAIR_LABEL = {"photon": T("photons |Φ+⟩ (polarisation)"), "spin": T("spin ½, singlet")}
MODEL_LABEL = {"polarization_model": T("polarisation model of local hidden variables (photons)"),
               "sign_model": T("Bell's sign model (spin ½)")}


def spin_direction(theta: float) -> np.ndarray:
    """Unit vector of a Stern-Gerlach direction at angle theta (rad) in the plane transverse to the flight (x, z of
    the spin's frame; theta from the z axis)."""
    return np.array([math.sin(theta), 0.0, math.cos(theta)])


class Law:
    """The correlation law of a world: pair type ("photon" | "spin") and law ("quantum" | "lhv")."""

    def __init__(self, pair: str, law: str):
        if pair not in PAIR_LABEL or law not in ("quantum", "lhv"):
            raise ValueError(f"unknown pair {pair!r} or law {law!r}")
        self.pair, self.law = pair, law
        self.state = Q.PHI_PLUS if pair == "photon" else Q.SINGLET
        self.model = None if law == "quantum" else ("polarization_model" if pair == "photon" else "sign_model")
        # period of E in the angle difference: a polarizer at alpha and alpha + 180 deg is the same element
        self.period = 180.0 if pair == "photon" else 360.0
        self._cache: dict = {}

    # --- analyzers (engine objects) ---
    def projectors(self, deg: float):
        r = math.radians(deg)
        return Q.polarizer_projectors(r) if self.pair == "photon" else Q.projectors(spin_direction(r))

    def observable(self, deg: float):
        r = math.radians(deg)
        return Q.polarizer_observable(r) if self.pair == "photon" else Q.n_sigma(spin_direction(r))

    # --- exact expectations ---
    def E_quantum(self, a_deg: float, b_deg: float) -> float:
        return Q.correlation(self.state, self.observable(a_deg), self.observable(b_deg))

    def E_lhv(self, a_deg: float, b_deg: float) -> float:
        ra, rb = math.radians(a_deg), math.radians(b_deg)
        if self.pair == "photon":
            return LHV.polarization_model_E(ra, rb)
        return LHV.sign_model_E(ra - rb)

    def E(self, a_deg: float, b_deg: float) -> float:
        """Exact correlation of the world's law at these analyzer angles (cached)."""
        key = (round(a_deg, 9), round(b_deg, 9))
        if key not in self._cache:
            E = self.E_quantum(a_deg, b_deg) if self.law == "quantum" else self.E_lhv(a_deg, b_deg)
            self._cache[key] = min(1.0, max(-1.0, E))  # round-off of the trace must not leave [-1, 1]
        return self._cache[key]

    def E_closed_form(self, a_deg: float, b_deg: float) -> float:
        """Textbook closed form of the quantum correlation (a reference for the engine's trace, not used to sample)."""
        d = math.radians(a_deg - b_deg)
        return math.cos(2 * d) if self.pair == "photon" else -math.cos(d)

    def S(self, a, a2, b, b2) -> float:
        return Q.chsh(self.E, a, a2, b, b2)

    def S_quantum(self, a, a2, b, b2) -> float:
        return Q.chsh(self.E_quantum, a, a2, b, b2)

    def marginal_A_quantum(self, a_deg: float, b_deg: float) -> float:
        """P_A(+) from the joint Born probabilities (sum over Bob's outcomes)."""
        P = Q.joint_probabilities(self.state, self.projectors(a_deg), self.projectors(b_deg))
        return float(P[0].sum())

    def marginal_B_quantum(self, a_deg: float, b_deg: float) -> float:
        P = Q.joint_probabilities(self.state, self.projectors(a_deg), self.projectors(b_deg))
        return float(P[:, 0].sum())

    # --- sampling (one call per setting pair; outcomes +1 / -1) ---
    def sample(self, a_deg: float, b_deg: float, n: int, rng) -> tuple[np.ndarray, np.ndarray]:
        if self.law == "quantum":
            iA, iB = Q.sample_pairs(self.state, self.projectors(a_deg), self.projectors(b_deg), n, rng)
            # index 0: transmitted by the polarizer / spin up along the direction = outcome +1
            return (1 - 2 * iA).astype(np.int8), (1 - 2 * iB).astype(np.int8)
        ra, rb = math.radians(a_deg), math.radians(b_deg)
        if self.pair == "photon":
            A, B = LHV.polarization_model(ra, rb, n, rng)
        else:
            A, B = LHV.sign_model(ra, rb, n, rng)
        return np.asarray(A).astype(np.int8), np.asarray(B).astype(np.int8)

    def fold(self, d):
        """Angle difference folded into [-period/2, period/2)."""
        P = self.period
        return (np.asarray(d, float) + P / 2) % P - P / 2

    def curves(self, n: int = 361):
        """E(delta) of the quantum law (engine trace) and of the matching LHV model, delta over one period."""
        d = np.linspace(-self.period / 2, self.period / 2, n)
        q = np.array([self.E_quantum(x, 0.0) for x in d])
        h = np.array([self.E_lhv(x, 0.0) for x in d])
        return d, q, h

    def describe(self) -> T:
        if self.law == "quantum":
            return T("{pair}: quantum mechanics", pair=PAIR_LABEL[self.pair])
        return T("{pair}: {model}", pair=PAIR_LABEL[self.pair], model=MODEL_LABEL[self.model])


# flags of a detected pair (bit set = space-like separation)
F_LOC_A = 1   # Alice's setting choice is space-like to Bob's detection
F_LOC_B = 2   # Bob's setting choice is space-like to Alice's detection
F_FREE_A = 4  # Alice's setting choice is space-like to the pair's emission
F_FREE_B = 8  # Bob's setting choice is space-like to the pair's emission
F_LATE = 16   # a choice had to be made at the detection itself (no earlier choice existed)

_F8 = ("te", "tarr", "tcA", "tcB", "xcA", "xcB", "id")
_I1 = ("sA", "sB")


class Experiment:
    """Pairs in flight and the stations' choices; see the module docstring for the geometry."""

    def __init__(self, law: Law, v: float, c: float, rng):
        self.law, self.v, self.c, self.rng = law, float(v), float(c), rng
        self.p = {k: np.zeros(0) for k in _F8}
        self.p.update({k: np.zeros(0, np.int8) for k in _I1})
        self.next_id = 0

    @property
    def n_flight(self) -> int:
        return len(self.p["te"])

    def emit(self, times: np.ndarray, L: float, tau: float, mode: str):
        n = len(times)
        if n == 0:
            return
        tarr = times + L / self.v
        tc = tarr - tau if mode == "random" else np.full(n, np.nan)
        new = {"te": times, "tarr": tarr, "tcA": tc, "tcB": tc.copy(), "xcA": np.full(n, np.nan),
               "xcB": np.full(n, np.nan), "id": np.arange(self.next_id, self.next_id + n, dtype=float),
               "sA": np.full(n, -1, np.int8), "sB": np.full(n, -1, np.int8)}
        self.next_id += n
        for k in self.p:
            self.p[k] = np.concatenate([self.p[k], new[k]])

    def choose(self, t_target: float, L: float, mode: str) -> int:
        """Random setting choices whose time has come (fair coin per station and particle: 0 = a/b, 1 = a'/b')."""
        if mode != "random" or self.n_flight == 0:
            return 0
        done = 0
        for s, tc, xc, x in (("sA", "tcA", "xcA", -L), ("sB", "tcB", "xcB", L)):
            m = (self.p[s] < 0) & (self.p[tc] <= t_target)
            k = int(m.sum())
            if k:
                self.p[s][m] = self.rng.integers(0, 2, k).astype(np.int8)
                self.p[xc][m] = x
                done += k
        return done

    def reschedule(self, now: float, L_old: float, L_new: float, tau: float, mode: str) -> int:
        """A live change at ``now``: stations moved (L), choice lead (tau) or mode changed. Pairs whose particle is
        already beyond the moved station are lost (returned); the others arrive when they reach it. Pending choices
        are rescheduled, never before ``now``."""
        lost = 0
        if self.n_flight and L_new != L_old:
            r = self.v * (now - self.p["te"])
            keep = r <= L_new
            lost = int((~keep).sum())
            for k in self.p:
                self.p[k] = self.p[k][keep]
            self.p["tarr"] = self.p["te"] + L_new / self.v
        if self.n_flight:
            for s, tc in (("sA", "tcA"), ("sB", "tcB")):
                m = self.p[s] < 0
                if mode == "random":
                    self.p[tc][m] = np.maximum(self.p["tarr"][m] - tau, now)
                else:
                    self.p[tc][m] = np.nan
        return lost

    def detect(self, t_target: float, L: float, mode: str, angles: dict, t_set: dict):
        """Pairs that reach the stations by ``t_target``: settings in force, outcomes by the world's law, and the
        space-time relations of their events. Returns a dict of arrays sorted by arrival time, or None."""
        due = self.p["tarr"] <= t_target
        if not np.any(due):
            return None
        d = {k: v[due] for k, v in self.p.items()}
        for k in self.p:
            self.p[k] = self.p[k][~due]
        order = np.argsort(d["tarr"], kind="stable")
        d = {k: v[order] for k, v in d.items()}
        n = len(d["te"])
        flags = np.zeros(n, np.uint8)
        if mode == "random":
            for s, tc, xc, x in (("sA", "tcA", "xcA", -L), ("sB", "tcB", "xcB", L)):
                m = d[s] < 0  # no choice was made earlier (cannot happen in a consistent run; kept as a guard)
                if np.any(m):
                    d[s][m] = self.rng.integers(0, 2, int(m.sum())).astype(np.int8)
                    d[tc][m] = d["tarr"][m]
                    d[xc][m] = x
                    flags[m] |= F_LATE
        else:  # fixed settings a and b, chosen when they were last set
            d["sA"][:] = 0
            d["sB"][:] = 0
            d["tcA"][:], d["xcA"][:] = t_set["A"]
            d["tcB"][:], d["xcB"][:] = t_set["B"]
        alA = np.where(d["sA"] == 0, angles["a"], angles["a2"])
        alB = np.where(d["sB"] == 0, angles["b"], angles["b2"])
        oA = np.zeros(n, np.int8)
        oB = np.zeros(n, np.int8)
        for i in (0, 1):
            for j in (0, 1):
                m = (d["sA"] == i) & (d["sB"] == j)
                k = int(m.sum())
                if k:
                    A, B = self.law.sample(float(alA[m][0]), float(alB[m][0]), k, self.rng)
                    oA[m], oB[m] = A, B
        # space-time relations of the events (lab frame): choices, detections, emission
        c = self.c
        chA = np.stack([d["tcA"], d["xcA"]], axis=1)
        chB = np.stack([d["tcB"], d["xcB"]], axis=1)
        detA = np.stack([d["tarr"], np.full(n, -L)], axis=1)
        detB = np.stack([d["tarr"], np.full(n, L)], axis=1)
        em = np.stack([d["te"], np.zeros(n)], axis=1)
        sp = K.SPACELIKE
        flags |= np.where(np.atleast_1d(K.relation(chA, detB, c)) == sp, F_LOC_A, 0).astype(np.uint8)
        flags |= np.where(np.atleast_1d(K.relation(chB, detA, c)) == sp, F_LOC_B, 0).astype(np.uint8)
        flags |= np.where(np.atleast_1d(K.relation(chA, em, c)) == sp, F_FREE_A, 0).astype(np.uint8)
        flags |= np.where(np.atleast_1d(K.relation(chB, em, c)) == sp, F_FREE_B, 0).astype(np.uint8)
        d.update(alA=alA, alB=alB, oA=oA, oB=oB, flags=flags, L=np.full(n, L))
        return d

    def in_flight(self, limit: int = 300) -> np.ndarray:
        """(k, 6): emission time, arrival time, Alice's and Bob's choice (-1 none), their choice times."""
        p = self.p
        k = min(limit, self.n_flight)
        sl = slice(self.n_flight - k, None)
        return np.stack([p["te"][sl], p["tarr"][sl], p["sA"][sl].astype(float), p["sB"][sl].astype(float),
                         p["tcA"][sl], p["tcB"][sl]], axis=1) if k else np.zeros((0, 6))

    def next_time(self) -> float | None:
        if not self.n_flight:
            return None
        c = [float(self.p["tarr"].min())]
        for s, tc in (("sA", "tcA"), ("sB", "tcB")):
            m = (self.p[s] < 0) & np.isfinite(self.p[tc])
            if np.any(m):
                c.append(float(self.p[tc][m].min()))
        return min(c)


class Store:
    """Coincidence counts (N++, N+-, N-+, N--) per pair of analyzer angles (deg) actually used."""

    MAX_KEYS = 200

    def __init__(self):
        self.cells: dict = {}

    @staticmethod
    def key(a: float, b: float):
        return (round(float(a), 9), round(float(b), 9))

    def clear(self):
        self.cells = {}

    def add(self, alA, alB, oA, oB, protect=()):
        idx = 2 * (oA < 0) + (oB < 0)  # 0: ++, 1: +-, 2: -+, 3: --
        for a, b in {(float(x), float(y)) for x, y in zip(alA, alB)}:
            m = (alA == a) & (alB == b)
            k = self.key(a, b)
            if k not in self.cells:
                self.cells[k] = np.zeros(4, np.int64)
            self.cells[k] += np.bincount(idx[m], minlength=4)
        while len(self.cells) > self.MAX_KEYS:  # drop the oldest angle pair that is not in use
            prot = {self.key(*p) for p in protect}
            old = next((k for k in self.cells if k not in prot), None)
            if old is None:
                break
            del self.cells[old]

    def get(self, a: float, b: float) -> np.ndarray:
        return self.cells.get(self.key(a, b), np.zeros(4, np.int64))
