# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v07: the Bell test with entangled pairs, a wrapper over the physics engine lfphys.

What the run computes (README.md of this folder has the model in full):
* a Poisson stream of pairs from a source between two stations at distance L; each particle flies to its station
  and its outcome is revealed only when it arrives (both at t_e + L/v);
* the stations' settings: fixed (a and b) or a fresh random choice for every particle, made a time tau before it
  arrives; the space-time relation of every choice to the other side's detection and to the emission
  (lfphys.core.causality);
* the outcomes by the world's law: the Born rule on the entangled state (lfphys.core.quantum.qubits) or a local
  hidden-variable model (lfphys.theories.alternatives.local_hidden);
* coincidence counts per setting pair, E with its error, CHSH S with its error, the marginals (no-signalling) and the
  measured E(delta) points (lfphys.tools.bell_stats);
* checks: each measured quantity against the exact expectation of the world's law (z-scores), the classical bound 2,
  the Tsirelson bound 2 sqrt 2, no-signalling, and the space-time relations against closed forms and the Lorentz
  matrices.
"""

from __future__ import annotations

import math

import numpy as np
from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from lfviz.sim import Simulation as BaseSimulation

from lfphys.core import causality as K
from lfphys.core import relativity as R
from lfphys.core.constants import C
from lfphys.core.quantum import qubits as Q
from lfphys.i18n import T, join
from lfphys.tools import bell_stats as BS

from .engine.experiment import (F_FREE_A, F_FREE_B, F_LOC_A, F_LOC_B, MODEL_LABEL, PAIR_LABEL, Experiment, Law,
                                Store)

TSIRELSON = 2.0 * math.sqrt(2.0)
NMIN = 30          # pairs per cell before an estimate is compared with its reference (normal approximation)
ZTOL = 5.0         # tolerance of the statistical checks, in standard errors
DETAIL = 16        # per-pair detail sent per step (all pairs enter the statistics; the view needs the newest)


def _p(*a, **k):
    return Param(*a, **k)


G_WSRC, G_CHOICE = T("Source (world)"), T("Choice of the settings")
G_A, G_B = T("Alice's settings (A)"), T("Bob's settings (B)")

SCHEMA = Schema([
    _p("pair", T("Pairs"), "select", "photon", group=G_WSRC,
       options=[("photon", T("photons: polarisation |Φ+⟩ = (|HH⟩ + |VV⟩)/√2, polarisers")),
                ("spin", T("spin ½: singlet (|↑↓⟩ − |↓↑⟩)/√2, Stern–Gerlach magnets"))],
       help=T("The type of the pair sets the state, the analysers and the particles' speed; it changes only with a "
              "new world.")),
    _p("spin_beta", T("Speed of the spin pair's particles, v/c"), "float", 0.5, group=G_WSRC, min=1e-4, max=0.999,
       log=True, show_if={"pair": ["spin"]},
       help=T("Illustrative: massive particles with spin ½ (protons, for example). Photons fly at the speed c.")),
    _p("law", T("Law of the correlations"), "select", "quantum", group=T("Laws (modifications)"), standard="quantum",
       options=[("quantum", T("quantum mechanics: the Born rule for the entangled state")),
                ("lhv", T("local hidden variables (photons: a polarisation model; spin: Bell's sign model)"))],
       help=T("Quantum mechanics is the accepted physics. Local hidden variables are a “what if” modification: the "
              "outcome of each side is set by its setting and by a common parameter from the source.")),
    _p("L_m", T("Distance from the source to a station L, m"), "float", 500.0, group=T("Geometry"), min=0.01, max=1e5,
       log=True, live=True,
       help=T("Alice's (−L) and Bob's (+L) stations stand on one line with the source; the distance between them is "
              "2L.")),
    _p("rate", T("Pairs per second (world time)"), "float", 1e6, group=T("Source"), min=1e-3, max=1e9, log=True,
       live=True),
    _p("switch", T("Choice of the setting"), "select", "random", group=G_CHOICE,
       options=[("fixed", T("fixed: Alice a, Bob b")),
                ("random", T("random for every particle (as in loophole-free experiments)"))], live=True),
    _p("tau_ns", T("The choice is made τ before the particle arrives, ns"), "float", 100.0, group=G_CHOICE, min=1e-3,
       max=1e7, log=True, show_if={"switch": ["random"]}, live=True,
       help=T("The station's random number generator gives its bit τ before the particle arrives (the delay of the "
              "generator and the switch). The choice is outside the light cone of the detection on the other side if "
              "cτ < 2L.")),
    _p("a_deg", T("Alice: setting a, °"), "float", 0.0, group=G_A, min=-360, max=360, live=True),
    _p("a2_deg", T("Alice: setting a′, °"), "float", 45.0, group=G_A, min=-360, max=360, live=True),
    _p("b_deg", T("Bob: setting b, °"), "float", 22.5, group=G_B, min=-360, max=360, live=True),
    _p("b2_deg", T("Bob: setting b′, °"), "float", 67.5, group=G_B, min=-360, max=360, live=True),
], presets={
    "photon_chsh": {"label": T("Photons |Φ+⟩, quantum mechanics: optimal CHSH angles {a}°, {a2}° / {b}°, {b2}°, random "
                               "choice", a=0, a2=45, b=22.5, b2=67.5), "params": {}},
    "spin_chsh": {"label": T("Spin-½ singlet, quantum mechanics: optimal angles {a}°, {a2}° / {b}°, {b2}°, random "
                             "choice", a=0, a2=90, b=45, b2=135),
                  "params": {"pair": "spin", "a_deg": 0.0, "a2_deg": 90.0, "b_deg": 45.0, "b2_deg": 135.0}},
    "photon_lhv": {"label": T("Photons, local hidden variables: a polarisation model (modification)"),
                   "params": {"law": "lhv"}},
    "spin_lhv": {"label": T("Spin-½ singlet, local hidden variables: Bell's sign model (modification)"),
                 "params": {"pair": "spin", "law": "lhv", "a_deg": 0.0, "a2_deg": 90.0, "b_deg": 45.0,
                            "b2_deg": 135.0}},
    "scan": {"label": T("The curve E(Δ): photons, fixed settings a = b = {a}°; move b", a=0),
             "params": {"switch": "fixed", "a_deg": 0.0, "b_deg": 0.0}},
    "photon_slow_choice": {"label": T("Photons: the choice made {tau} µs before arrival (cτ > 2L), the locality "
                                      "loophole is open", tau=5),
                           "params": {"tau_ns": 5000.0}},
})

ANGLES = ("a_deg", "a2_deg", "b_deg", "b2_deg")
G_ST = T("Spacetime: the choice of a setting and the detection")


class Simulation(BaseSimulation):
    speed_range = (1e-12, 1e3)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = dict(params)
        self.law = Law(params["pair"], params["law"])
        self.v = C if params["pair"] == "photon" else float(params["spin_beta"]) * C
        self.exp = Experiment(self.law, self.v, C, self.rng)
        self.store = Store()
        L = self.params["L_m"]
        self.t_set = {"A": (0.0, -L), "B": (0.0, L)}  # when (and where) the fixed settings were last chosen
        self.t_next = self.rng.exponential(1.0 / self.params["rate"])
        self.counts = dict(emitted=0, detected=0, lost=0)
        self.seg = 0
        self.seg_t0 = 0.0
        self.seg_counts = dict(detected=0, loc=0, free=0)
        self.n_checked = 0
        self.viol_said = False
        self._buf = []
        self.default_speed = min(max(self._flight() / 2.0, self.speed_range[0]), self.speed_range[1])
        self._engine_checks()
        self._setup_checks()
        self._spacetime_checks()
        self._stat_checks()

    # --- helpers ---------------------------------------------------------------------------------------
    def _flight(self):
        return self.params["L_m"] / self.v

    def _tau(self):
        return self.params["tau_ns"] * 1e-9

    def _angles(self):
        P = self.params
        return {"a": P["a_deg"], "a2": P["a2_deg"], "b": P["b_deg"], "b2": P["b2_deg"]}

    def _cell_angles(self):
        P = self.params
        return [("a", "b", P["a_deg"], P["b_deg"]), ("a", "b′", P["a_deg"], P["b2_deg"]),
                ("a′", "b", P["a2_deg"], P["b_deg"]), ("a′", "b′", P["a2_deg"], P["b2_deg"])]

    def engine_modules(self):
        mods = ["core.constants", "core.quantum.qubits", "core.causality", "core.relativity", "tools.bell_stats"]
        if self.law.law == "lhv":
            mods.append("theories.alternatives.local_hidden")
        return mods

    # --- messages -----------------------------------------------------------------------------------------
    def _msg(self, meta, blobs=None):
        if self._buf is not None:
            self._buf.append((meta, blobs))
        else:
            self.emit(meta, blobs)

    def after_header(self):
        buf, self._buf = self._buf, None
        for meta, blobs in buf:
            self.emit(meta, blobs)

    def _check(self, cid, label, value, ref, unit="", group="", note="", tol=1e-9, ok=None, info=False):
        """``info``: a comparison shown for information (an identity of the model, say), never a pass or a failure
        (RULES.md §3, check message)."""
        rel = None
        if ref is not None and value is not None and ref != 0 and math.isfinite(value):
            rel = (value - ref) / abs(ref)
        d = {"type": "check", "t": self.t, "id": cid, "label": label, "value": value, "ref": ref, "unit": unit,
             "rel": rel, "group": group, "note": note, "tol": tol}
        if info:
            d["info"] = True
        elif ok is not None:
            d["ok"] = bool(ok)
        self._msg(d)

    def _actions(self):
        return [{"name": "clear", "label": T("Reset the statistics"),
                 "help": T("The coincidence counts start anew; the set-up and the pairs in flight stay the same."),
                 "args": []}]

    # --- checks: the law and the set-up ---------------------------------------------------------------------
    def _engine_checks(self):
        """Once per world: properties of the source state computed by the engine."""
        g = T("Source: the state of the pair")
        if self.law.law == "quantum":
            rho = Q.dm(self.law.state)
            self._check("conc", T("Entanglement of the state: Wootters' concurrence"), Q.concurrence(rho), 1.0, "", g,
                        tol=1e-12,
                        note=T("1: a maximally entangled state (the engine: lfphys.core.quantum.qubits)"))
            ent = Q.entropy(Q.ptrace(rho, 0))
            self._check("ent", T("Entropy of one particle of the pair (bits)"), ent, 1.0, "", g, tol=1e-12,
                        note=T("a particle on its own is completely unpolarised: its marginals are 1/2 at any setting"))
        else:
            self._check("conc", T("Source by the LHV model: a common hidden parameter λ, no quantum state"), None,
                        None, "", g, note=T("{model}: the outcome of a side is a function of its setting and λ (local by "
                                            "construction)", model=MODEL_LABEL[self.law.model]))

    def _setup_checks(self):
        """After every change of the settings: the exact expectation of the world's law."""
        law, P = self.law, self.params
        a, a2, b, b2 = (P[k] for k in ANGLES)
        g = T("Set-up: the expectation of the world's law (exact)")
        S_law = law.S(a, a2, b, b2)
        if law.law == "quantum":
            S_cf = sum(s * law.E_closed_form(x, y) for s, (_, _, x, y) in zip(BS.CHSH_SIGNS, self._cell_angles()))
            self._check("S_law", T("S at the current settings: the engine's trace Tr(ρ A⊗B)"), S_law, S_cf, "", g,
                        tol=1e-12,
                        note=T("reference: the closed form E = cos 2(α_A − α_B) for |Φ+⟩; S = E(a,b) − E(a,b′) + "
                               "E(a′,b) + E(a′,b′)") if law.pair == "photon" else
                        T("reference: the closed form E = −cos(θ_A − θ_B) for the singlet; S = E(a,b) − E(a,b′) + "
                          "E(a′,b) + E(a′,b′)"))
            mA = [abs(law.marginal_A_quantum(x, b) - law.marginal_A_quantum(x, b2)) for x in (a, a2)]
            mB = [abs(law.marginal_B_quantum(a, y) - law.marginal_B_quantum(a2, y)) for y in (b, b2)]
            dmax = max(mA + mB)
            self._check("nosig_law", T("No signalling in the law (exact): the marginal of one side against the setting "
                                       "of the other"),
                        dmax, 0.0, "", g, ok=dmax < 1e-14,
                        note=T("max |P_A(+|x,b) − P_A(+|x,b′)|, |P_B(+|a,y) − P_B(+|a′,y)| from the joint Born "
                               "probabilities Tr(ρ Π⊗Π)"))
        else:
            self._check("S_law", T("S at the current settings by the LHV model"), S_law, None, "", g,
                        note=T("{model}: E is a function of the engine's model, {formula}", model=MODEL_LABEL[law.model],
                               formula="½cos 2(α_A − α_B)" if law.pair == "photon" else "−1 + 2θ/π"))
            self._check("nosig_law", T("No signalling in the law of the LHV model: by construction (for information)"),
                        0.5, None, "", g, info=True,
                        note=T("the outcome of each side is a function of its setting and λ only (local by "
                               "construction), and λ is distributed isotropically: P(+) = 1/2 at any setting of the "
                               "other side. This is an identity of the model, not a check; the check by the run's "
                               "counts is in the group “No signalling”"))
        if law.law == "quantum":
            self._check("tsir_law", T("Expectation of the law: |S| ≤ 2√2 (the Tsirelson bound)"), abs(S_law),
                        TSIRELSON, "", g, ok=abs(S_law) <= TSIRELSON + 1e-12,
                        note=T("no quantum theory gives more"))
        else:
            self._check("tsir_law", T("Expectation of the LHV model and the Tsirelson bound 2√2 (for information)"),
                        abs(S_law), TSIRELSON, "", g, info=True,
                        note=T("in an LHV world it follows from the check |S| ≤ 2 (the next line): not a separate "
                               "check"))
        bound_ok = abs(S_law) <= 2.0 + 1e-12
        if law.law == "lhv":
            self._check("chsh_law", T("Expectation of the LHV model: |S| ≤ 2 (the CHSH bound)"), abs(S_law), 2.0, "",
                        g, ok=bound_ok, note=T("every local model must keep this bound"))
        else:  # information, not a test: quantum mechanics may exceed 2
            self._check("chsh_law", T("Quantum expectation |S| and the classical bound 2"), abs(S_law), None, "", g,
                        note=T("exceeds 2: quantum mechanics violates the CHSH inequality at these settings")
                        if not bound_ok else T("at these settings the quantum expectation does not exceed 2"))
        self._S_law = S_law

    def _spacetime_checks(self):
        """The space-time relation of the setting choices for a pair emitted now (nominal geometry)."""
        P = self.params
        L, c, v = P["L_m"], C, self.v
        g = G_ST
        # events of a pair emitted now, counted from its emission (intervals are translation invariant; this avoids
        # the cancellation of large world times)
        te = 0.0
        tarr = L / v
        detB = (tarr, L)
        em = (te, 0.0)
        if P["switch"] == "random":
            tau = self._tau()
            chA = (tarr - tau, -L)
            s2 = K.interval(chA, detB, c)
            rel = K.relation(chA, detB, c)
            txt = {K.SPACELIKE: T("space-like: the locality loophole is closed"),
                   K.TIMELIKE: T("time-like: the locality loophole is OPEN"),
                   K.LIGHTLIKE: T("light-like (on the boundary of the cone)")}[rel]
            note = (T("s² = c²τ² − (2L)², cτ = {ct:.4g} m, 2L = {L2:.4g} m: a signal from the choice at A cannot reach "
                      "the detection at B in time (nor one from B reach A); reference: the closed form",
                      ct=c * tau, L2=2 * L) if rel == K.SPACELIKE else
                    T("s² = c²τ² − (2L)², cτ = {ct:.4g} m, 2L = {L2:.4g} m: a signal from the choice at A can reach "
                      "the detection at B in time (and one from B can reach A); reference: the closed form",
                      ct=c * tau, L2=2 * L))
            self._check("st_loc", T("Choice at A ↔ detection at B: {rel}", rel=txt), s2, (c * tau) ** 2 - (2 * L) ** 2,
                        T("m²"), g, tol=1e-9, note=note)
            if rel == K.SPACELIKE:
                beta = K.order_reversal_speed(chA, detB, c)
                self._check("st_rev", T("The order “choice at A → detection at B” reverses in a frame moving from A to B "
                                        "faster than v*; v*/c ="), beta, _reversal_by_boosts(chA, detB), "", g,
                            tol=1e-9,
                            note=T("v* = c²τ/(2L) < c: the time between the events is not absolute, there is no causal "
                                   "link; reference: the zero of Δt′ found with the Lorentz matrices "
                                   "(lfphys.core.relativity.boost_matrix)"))
            else:
                self._check("st_rev", T("The order “choice at A → detection at B” is absolute (time-like events)"),
                            None, None, "", g, note=T("it reverses in no inertial frame"))
            s2e = K.interval(chA, em, c)
            rel_e = K.relation(chA, em, c)
            before = tarr - tau < te
            txe = {K.SPACELIKE: T("space-like: the choice and the source are independent"),
                   K.TIMELIKE: (T("the choice is in the past cone of the emission: a signal from the choice reaches the "
                                  "source in time")
                                if before else T("the choice is in the future cone of the emission: the "
                                                 "freedom-of-choice loophole is open")),
                   K.LIGHTLIKE: T("light-like")}[rel_e]
            self._check("st_free", T("Choice at A ↔ emission of the pair: {rel}", rel=txe), s2e,
                        (c * (tarr - tau - te)) ** 2 - L ** 2, T("m²"), g, tol=1e-9,
                        note=T("s² = c²(L/v − τ)² − L²; the flight time L/v = {tf:.4g} s, τ = {tau:.4g} s", tf=L / v,
                               tau=tau))
        else:
            tA, xA = self.t_set["A"]
            tA -= self.t  # the same origin: the emission of a pair now
            chA = (tA, xA)
            s2 = K.interval(chA, detB, c)
            rel = K.relation(chA, detB, c)
            txt = {K.SPACELIKE: T("space-like (the setting was set just now)"),
                   K.TIMELIKE: T("time-like: the settings are known in advance, the locality loophole is OPEN"),
                   K.LIGHTLIKE: T("light-like")}[rel]
            self._check("st_loc", T("Fixed setting a ↔ detection at B of the next pair: {rel}", rel=txt), s2,
                        (c * (tarr - tA)) ** 2 - (L - xA) ** 2, T("m²"), g, tol=1e-9,
                        note=T("the setting a was set {dt:.6g} s before the emission of the pair, the pair arrives "
                               "{tf:.6g} s after the emission", dt=abs(tA), tf=tarr))
            for cid in ("st_rev", "st_free"):
                self._check(cid, T("Only for a random choice of the settings"), None, None, "", g,
                            note=T("with fixed settings the choice was made at the set-up"))

    # --- checks: the statistics of the run's own pairs ------------------------------------------------------
    def _cells(self):
        out = []
        for x, y, al, be in self._cell_angles():
            n = self.store.get(al, be)
            E, se, N = BS.correlation(n)
            Eref = self.law.E(al, be)
            z = BS.zscore(E, Eref, BS.se_under(Eref, N)) if N else None
            out.append({"x": x, "y": y, "alA": al, "alB": be, "n": [int(q) for q in n], "N": N, "E": E, "se": se,
                        "Eref": Eref, "z": z})
        return out

    def _S(self, cells):
        """S of the four cells and its error. With coinciding settings (a' = a or b' = b) two cells are the same
        angle pair, i.e. the same counts (Store keys by angle pair): the error counts them once (bell_stats.chsh with
        keys; review 2026-10-23, V7-2) and ``same`` lists the coinciding cells."""
        keys = [Store.key(c["alA"], c["alB"]) for c in cells]
        same = [f"({c['x']},{c['y']})" for k, c in enumerate(cells) if keys.index(keys[k]) != k]
        Sref = sum(s * c["Eref"] for s, c in zip(BS.CHSH_SIGNS, cells))
        S, se = BS.chsh([c["n"] for c in cells], keys=keys)
        if S is None:
            return {"S": None, "se": None, "Sref": Sref, "z": None, "excess": None, "Nmin": min(c["N"] for c in cells),
                    "same": same}
        seu = BS.chsh_se_under([c["Eref"] for c in cells], [c["N"] for c in cells], keys=keys)
        excess = (abs(S) - 2.0) / se if se and se > 0 else None
        return {"S": S, "se": se, "Sref": Sref, "z": BS.zscore(S, Sref, seu), "excess": excess,
                "Nmin": min(c["N"] for c in cells), "same": same}

    @staticmethod
    def _with_same(note, s):
        """``note`` with the warning about coinciding settings, when they coincide."""
        if not s["same"]:
            return note
        return T("{note}; the settings coincide (a′ = a or b′ = b): the cells {cells} are the same pairs as another "
                 "cell; S reduces to 2E of one pair of angles, this is not a CHSH test; the error of S counts each pair "
                 "of angles once", note=note, cells=", ".join(s["same"]))

    def _points(self):
        """All measured angle pairs: delta, E, se, N, E of the law (for the E(delta) plot and the chi-square)."""
        rows = []
        for (al, be), n in self.store.cells.items():
            E, se, N = BS.correlation(n)
            if N == 0:
                continue
            rows.append((float(self.law.fold(al - be)), E, se, N, self.law.E(al, be)))
        return np.array(rows, float) if rows else np.zeros((0, 5))

    def _stat_checks(self):
        self.n_checked = self.seg_counts["detected"]
        law = self.law
        cells = self._cells()
        fixed = self.params["switch"] == "fixed"
        g = T("Statistics of the pairs: measured ↔ the world's law")
        ref_txt = T("the quantum expectation (the engine)") if law.law == "quantum" else \
            T("the expectation of the LHV model")
        for k, c in enumerate(cells):
            lab = T("E({x},{y}) at α_A = {a}°, α_B = {b}°", x=c["x"], y=c["y"], a=float(c["alA"]), b=float(c["alB"]))
            if c["N"] >= NMIN:
                self._check(f"E{k}", lab, c["E"], c["Eref"], "", g, ok=abs(c["z"]) < ZTOL,
                            note=T("N = {N:d}, ± {se:.3g}; z = {z:+.2f} (tolerance {ztol}σ); reference: {ref}",
                                   N=int(c["N"]), se=float(c["se"]), z=float(c["z"]), ztol=ZTOL, ref=ref_txt))
            else:
                self._check(f"E{k}", lab, None, c["Eref"], "", g,
                            note=T("accumulating: N = {N:d} < {nmin:d}; in the mode “fixed” only the pair (a, b) "
                                   "accumulates", N=int(c["N"]), nmin=NMIN) if fixed and k else
                            T("accumulating: N = {N:d} < {nmin:d}", N=int(c["N"]), nmin=NMIN))
        s = self._S(cells)
        lab_S = T("S = E(a,b) − E(a,b′) + E(a′,b) + E(a′,b′)")
        lab_tsir = T("Tsirelson bound: |S| ≤ 2√2 (with a tolerance of {ztol}σ)", ztol=ZTOL)
        lab_viol = T("Violation of the CHSH inequality: (|S| − 2)/σ")
        if s["S"] is not None and s["Nmin"] >= NMIN:
            self._check("S", lab_S, s["S"], s["Sref"], "", g, ok=abs(s["z"]) < ZTOL,
                        note=self._with_same(T("± {se:.3g}; z = {z:+.2f} (tolerance {ztol}σ); reference: {ref}",
                                               se=float(s["se"]), z=float(s["z"]), ztol=ZTOL, ref=ref_txt), s))
            aS = abs(s["S"])
            self._check("tsir", lab_tsir, aS, TSIRELSON, "", g,
                        ok=aS - TSIRELSON < ZTOL * s["se"], note=T("|S| = {S:.4f} ± {se:.3g}", S=float(aS),
                                                                    se=float(s["se"])))
            if law.law == "lhv":
                self._check("bound", T("CHSH bound for local models: |S| ≤ 2 (with a tolerance of {ztol}σ)", ztol=ZTOL),
                            aS, 2.0, "", g, ok=aS - 2.0 < ZTOL * s["se"],
                            note=T("(|S| − 2)/σ = {x:+.2f}", x=float(s["excess"])) if s["excess"] is not None else "")
            else:
                exc = s["excess"]
                if abs(s["Sref"]) > 2.0:
                    need = self._pairs_needed(cells)
                    self._check("bound", lab_viol, exc, None, "σ", g,
                                ok=True if exc is not None and exc > ZTOL else None,
                                note=(T("|S| = {S:.4f} ± {se:.3g} > 2 by {x:.1f}σ", S=float(aS), se=float(s["se"]),
                                        x=float(exc))
                                      if exc is not None and exc > ZTOL else
                                      T("accumulating: the expected |S| = {S:.4f}; {ztol}σ needs about {need:.0f} pairs "
                                        "with a random choice", S=float(abs(s["Sref"])), ztol=ZTOL, need=float(need))))
                else:
                    self._check("bound", lab_viol, exc, None, "σ", g,
                                note=T("at these settings the quantum expectation |S| = {S:.4f} ≤ 2",
                                       S=float(abs(s["Sref"]))))
        else:
            why = (T("accumulating: at least {nmin:d} pairs per cell are needed for each of the four pairs of settings; "
                     "in the mode “fixed” only (a, b) accumulates: switch on the random choice", nmin=NMIN) if fixed else
                   T("accumulating: at least {nmin:d} pairs per cell are needed for each of the four pairs of settings",
                     nmin=NMIN))
            self._check("S", lab_S, None, s["Sref"], "", g, note=self._with_same(why, s))
            self._check("tsir", lab_tsir, None, TSIRELSON, "", g, note=why)
            self._check("bound", T("CHSH bound |S| ≤ 2") if law.law == "lhv" else lab_viol,
                        None, 2.0 if law.law == "lhv" else None, "" if law.law == "lhv" else "σ", g, note=why)
        # E(delta): all measured angle pairs against the law
        pts = self._points()
        m = pts[:, 3] >= NMIN if len(pts) else np.zeros(0, bool)
        if np.any(m):
            x2, dof, p = BS.chi2_points(pts[m, 1], pts[m, 4], np.sqrt(np.maximum(1 - pts[m, 4] ** 2, 0) / pts[m, 3]))
            if dof:
                self._check("curve", T("The curve E(Δ): χ² of the measured points against the world's law"), x2,
                            float(dof), "", g, ok=p > 1e-6,
                            note=T("points with N ≥ {nmin:d}: {k:d}; p = {p:.3g}; reference: χ² ≈ the number of points",
                                   nmin=NMIN, k=int(dof), p=float(p)))
        # no-signalling from the run's own counts
        gn = T("No signalling: the marginal of one side does not depend on the setting of the other")
        for i, (x, c1, c2) in enumerate((("a", cells[0], cells[1]), ("a′", cells[2], cells[3]))):
            self._nosig(f"nsA{i}", T("P_A(+ | {x}, b) − P_A(+ | {x}, b′)", x=x), c1, c2, "A", gn, fixed)
        for i, (y, c1, c2) in enumerate((("b", cells[0], cells[2]), ("b′", cells[1], cells[3]))):
            self._nosig(f"nsB{i}", T("P_B(+ | a, {y}) − P_B(+ | a′, {y})", y=y), c1, c2, "B", gn, fixed)
        # space-time relations of the pairs actually detected in this segment
        gs = G_ST
        n = self.seg_counts["detected"]
        if n:
            self._check("st_frac", T("Fraction of pairs: the choice of the settings of both sides is outside the light "
                                     "cone of the detection on the other side"), self.seg_counts["loc"] / n, None, "",
                        gs, note=T("pairs: {k:d} of {m:d} (by the events of each pair, lfphys.core.causality)",
                                   k=self.seg_counts["loc"], m=n))
            self._check("st_frac_free", T("Fraction of pairs: the choice of the settings of both sides is space-like to "
                                          "the emission of the pair"),
                        self.seg_counts["free"] / n, None, "", gs,
                        note=T("pairs: {k:d} of {m:d}", k=self.seg_counts["free"], m=n))

    def _nosig(self, cid, label, c1, c2, side, group, fixed):
        if Store.key(c1["alA"], c1["alB"]) == Store.key(c2["alA"], c2["alB"]):  # b' = b (or a' = a): one cell
            self._check(cid, label, 0.0 if c1["N"] else None, None, "", group, info=True,
                        note=T("the settings of the other side coincide: both cells are the same pairs, the difference "
                               "is 0 identically (not a check)"))
            return
        if c1["N"] >= NMIN and c2["N"] >= NMIN:
            k1 = c1["n"][0] + (c1["n"][1] if side == "A" else c1["n"][2])
            k2 = c2["n"][0] + (c2["n"][1] if side == "A" else c2["n"][2])
            d, se = BS.difference(k1, c1["N"], k2, c2["N"])
            z = BS.zscore(d, 0.0, se)
            self._check(cid, label, d, 0.0, "", group, ok=abs(z) < ZTOL,
                        note=T("P = {p1:.4f} (N = {N1:d}) and {p2:.4f} (N = {N2:d}); ± {se:.3g}; z = {z:+.2f} "
                               "(tolerance {ztol}σ)", p1=float(k1 / c1["N"]), N1=int(c1["N"]), p2=float(k2 / c2["N"]),
                               N2=int(c2["N"]), se=float(se), z=float(z), ztol=ZTOL))
        else:
            self._check(cid, label, None, 0.0, "", group,
                        note=T("accumulating; with fixed settings the second setting is not used") if fixed else
                        T("accumulating"))

    @staticmethod
    def _pairs_needed(cells):
        """Pairs for a 5-sigma excess over 2 with random choice (N/4 per cell) at the law's expectation."""
        Sref = abs(sum(s * c["Eref"] for s, c in zip(BS.CHSH_SIGNS, cells)))
        if Sref <= 2.0:
            return math.inf
        return 4.0 * sum(1 - c["Eref"] ** 2 for c in cells) * (ZTOL / (Sref - 2.0)) ** 2

    # --- live changes -------------------------------------------------------------------------------------
    def live_values(self):
        return {k: self.params[k] for k in SCHEMA.live_ids()}

    def set_live(self, values):
        new, errors = SCHEMA.coerce_live(self.params, values)
        if errors:
            raise Refusal(join(errors))
        changed = [k for k in SCHEMA.live_ids() if not _same(new[k], self.params[k])]
        if not changed:
            return T("no changes")
        now = self.t
        old = self.params
        lost = self.exp.reschedule(now, old["L_m"], new["L_m"], new["tau_ns"] * 1e-9, new["switch"])
        if lost:
            self.counts["lost"] += lost
            self._msg({"type": "notice", "t": now,
                       "text": T("The stations were moved: pairs in flight lost: {k:d} (the particle had already passed "
                                 "the station's new place)", k=int(lost))})
        if "switch" in changed:
            self.t_set = {"A": (now, -new["L_m"]), "B": (now, new["L_m"])}
        if "a_deg" in changed:
            self.t_set["A"] = (now, -new["L_m"])
        if "b_deg" in changed:
            self.t_set["B"] = (now, new["L_m"])
        if "rate" in changed:
            self.t_next = now + self.rng.exponential(1.0 / new["rate"])  # Poisson stream: memoryless
        desc = join([T("{label}: {old} → {new}", label=SCHEMA.by_id[k].label, old=_val(SCHEMA.by_id[k], old[k]),
                        new=_val(SCHEMA.by_id[k], new[k])) for k in changed])
        self.params = new
        if new["switch"] == "random" and C * new["tau_ns"] * 1e-9 >= 2 * new["L_m"] and \
                any(k in changed for k in ("tau_ns", "L_m", "switch")):
            self._msg({"type": "notice", "t": now,
                       "text": T("cτ ≥ 2L: the choice of a setting is time-like to the detection on the other side, the "
                                 "locality loophole is open")})
        if any(k in changed for k in ANGLES):
            self._setup_checks()
        self._spacetime_checks()
        self._stat_checks()
        return desc

    def action(self, name, args):
        if name == "clear":
            self.store.clear()
            self.seg += 1
            self.seg_t0 = self.t
            self.seg_counts = dict(detected=0, loc=0, free=0)
            self.viol_said = False
            self._stat_checks()
            return T("the statistics reset; the set-up and the pairs in flight as they were")
        raise ValueError(f"unknown action {name!r}")

    # --- time -----------------------------------------------------------------------------------------
    def max_step(self):
        return 2000.0 / self.params["rate"]

    def _emissions(self, t_target):
        rate = self.params["rate"]
        out = []
        while self.t_next <= t_target:
            k = int(min(max(16, rate * (t_target - self.t_next) * 1.2 + 16), 1_000_000))
            gaps = self.rng.exponential(1.0 / rate, k)
            ts = self.t_next + np.concatenate([[0.0], np.cumsum(gaps[:-1])])
            m = ts <= t_target
            if m.all():
                out.append(ts)
                self.t_next = float(ts[-1] + gaps[-1])
            else:
                j = int(np.argmin(m))
                out.append(ts[:j])
                self.t_next = float(ts[j])
        return np.concatenate(out) if out else np.zeros(0)

    def advance(self, t_target):
        P = self.params
        L, mode = P["L_m"], P["switch"]
        te = self._emissions(t_target)
        if len(te):
            self.exp.emit(te, L, self._tau(), mode)
            self.counts["emitted"] += len(te)
        self.exp.choose(t_target, L, mode)
        d = self.exp.detect(t_target, L, mode, self._angles(), self.t_set)
        if d is not None:
            self._detected(d, t_target)
        self.t = t_target
        n = self.seg_counts["detected"]
        if n - self.n_checked >= max(100, 0.3 * self.n_checked):
            self._stat_checks()
            self._maybe_violation_event()
            if P["switch"] == "fixed":  # the age of the fixed settings grows: their relation to the next pair changes
                self._spacetime_checks()

    def _detected(self, d, t_target):
        n = len(d["te"])
        first = self.counts["detected"] == 0
        self.counts["detected"] += n
        self.seg_counts["detected"] += n
        fl = d["flags"]
        self.seg_counts["loc"] += int(np.sum((fl & F_LOC_A > 0) & (fl & F_LOC_B > 0)))
        self.seg_counts["free"] += int(np.sum((fl & F_FREE_A > 0) & (fl & F_FREE_B > 0)))
        self.store.add(d["alA"], d["alB"], d["oA"], d["oB"],
                       protect=[(x, y) for _, _, x, y in self._cell_angles()])
        sl = slice(max(0, n - DETAIL), None)
        blobs = {"t": d["tarr"][sl], "te": d["te"][sl], "id": d["id"][sl], "sA": d["sA"][sl], "sB": d["sB"][sl],
                 "oA": d["oA"][sl], "oB": d["oB"][sl], "alA": d["alA"][sl].astype(np.float64),
                 "alB": d["alB"][sl].astype(np.float64), "tcA": d["tcA"][sl], "tcB": d["tcB"][sl],
                 "xcA": d["xcA"][sl], "xcB": d["xcB"][sl], "L": d["L"][sl], "fl": fl[sl]}
        self._msg({"type": "pairs", "t": t_target, "n": n, "seg": self.seg}, blobs)
        if first:
            i = 0
            sg = lambda o: "+" if o > 0 else "−"  # noqa: E731
            self._msg({"type": "event", "kind": "detection", "t": float(d["tarr"][0]),
                       "text": T("The first pair detected: A {oA} at {aA}°, B {oB} at {aB}° (flight {tf:.4g} s)",
                                 oA=sg(d["oA"][i]), aA=float(d["alA"][i]), oB=sg(d["oB"][i]), aB=float(d["alB"][i]),
                                 tf=float(self._flight()))})

    def _maybe_violation_event(self):
        if self.viol_said or self.law.law != "quantum":
            return
        s = self._S(self._cells())
        if s["excess"] is not None and s["Nmin"] >= NMIN and s["excess"] > ZTOL:
            self.viol_said = True
            self._msg({"type": "event", "kind": "result", "t": self.t,
                       "text": T("Violation of the CHSH inequality by {x:.1f}σ: S = {S:.4f} ± {se:.3g} (pairs counted: "
                                 "{k:d})", x=float(s["excess"]), S=float(s["S"]), se=float(s["se"]),
                                 k=int(self.seg_counts["detected"]))})

    def next_event_time(self):
        c = [self.t_next]
        nt = self.exp.next_time()
        if nt is not None:
            c.append(nt)
        return min(c)

    # --- frames ---------------------------------------------------------------------------------------
    def frame(self):
        P = self.params
        cells = self._cells()
        st = {"settings": {"a": P["a_deg"], "a2": P["a2_deg"], "b": P["b_deg"], "b2": P["b2_deg"],
                           "switch": P["switch"], "L": P["L_m"], "tau": self._tau(), "rate": P["rate"]},
              "flight": self._flight(),
              "counts": {**self.counts, "in_flight": self.exp.n_flight, "seg": self.seg,
                         "seg_detected": self.seg_counts["detected"], "loc": self.seg_counts["loc"],
                         "free": self.seg_counts["free"]},
              "cells": cells, "S": self._S(cells), "S_law": self._S_law}
        return st, {"flight": self.exp.in_flight(120), "pts": self._points()}

    def header(self):
        law = self.law
        d, q, h = law.curves()
        P = self.params
        return {
            "title": T("Bell test: {law}", law=law.describe()),
            "text": T("The source in the middle emits pairs one at a time (a Poisson stream); the particles fly to the "
                      "stations of Alice (−L) and Bob (+L). Each station has two settings of its analyser; in the mode of "
                      "random choice, a bit of the station's generator chooses the setting τ before the particle "
                      "arrives. The outcome (+ or −) of each particle is computed and shown at the moment it arrives: "
                      "by the Born rule for the entangled state, or by a model of local hidden variables. The "
                      "statistics are the coincidence counts of this run; the expectations of the law and the bounds 2 "
                      "and 2√2 are in “Checks”. The LHV curve on the plot E(Δ) in a quantum world is for comparison "
                      "only (lfphys.theories.alternatives.local_hidden)."),
            "pair": P["pair"], "pair_label": PAIR_LABEL[P["pair"]], "law": law.law, "model": law.model,
            "model_label": MODEL_LABEL.get(law.model), "v": self.v, "c": C, "period": law.period,
            "modifications": SCHEMA.modifications(P), "actions": self._actions(),
        }, {"cd": d, "cq": q, "ch": h}


def _reversal_by_boosts(e1, e2):
    """beta at which t2' - t1' = 0 in a frame moving along +x, found by bisection on the 3x3 Lorentz matrices of
    lfphys.core.relativity (an independent route to the closed form c^2 dt / dx). The matrix acts on the separation
    e2 - e1 (the transformation is linear): boosting the two events apart and subtracting cancelled terms of the size
    of c t ~ L and lost ~eps L / (c tau) of the root — 1.2e-8 at tau = 1 ps, L = 1e5 m, beyond the 1e-9 tolerance
    (review UX-params P21)."""
    d = np.array([C * (e2[0] - e1[0]), e2[1] - e1[1], 0.0])

    def dt_prime(beta):
        M = R.boost_matrix(np.array([beta * C, 0.0]), C)
        return (M @ d)[0] / C
    lo, hi = 0.0, 1.0 - 1e-15
    s0 = math.copysign(1.0, dt_prime(lo))
    if math.copysign(1.0, dt_prime(hi)) == s0:
        return None
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if math.copysign(1.0, dt_prime(mid)) == s0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _same(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return math.isclose(float(a), float(b), rel_tol=1e-12, abs_tol=0.0)
    return a == b


def _val(p, v):
    """A parameter's value for a text: an option's label (a T) or the number itself (formatted by the viewer)."""
    if p.type == "select":
        return dict(p.options).get(v, v)
    return v


VIZ = {
    "id": "v07_bell_test",
    "title": T("The Bell test with entangled pairs"),
    "summary": T("Pairs of photons |Φ+⟩ or of spins ½ in the singlet fly to two stations; each has two settings, "
                 "chosen fixed or at random before the particle arrives (outside the other side's light cone). "
                 "Coincidence counts, the correlations E, the CHSH parameter S against the bounds 2 and 2√2, the curve "
                 "E(Δ), no signalling."),
    "purpose": T("A study of nonlocal correlations and of the conditions of a loophole-free experiment; the law can be "
                 "replaced on purpose by local hidden variables to see that |S| does not exceed 2."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
