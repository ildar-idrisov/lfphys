# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v14: quarkonium in 3-D — wave functions of a heavy quark pair in the Cornell model (a wrapper over lfphys; plan
P14.9).

The pair cc̄ or bb̄ bound by V(r) = -kappa/r + r/a^2 (lfphys.theories.models.cornell: a FITTED, non-relativistic,
spin-averaged model outside the core; it predicts level splittings, not absolute masses, STATUS V17). The radial
functions come from the radial solver (lfphys.core.quantum.radial.wavefunctions, measured accuracy), interpolated by
lfphys.core.quantum.central3d.RadialTable; the 3-D clouds, currents, superpositions and slices are those of
lfviz.orbitals3d, the same as v13's. The cloud is the distribution of the relative coordinate r = r_q - r_q̄ (the
centre of mass at the origin). Lengths in femtometres, energies in MeV, time in seconds.

The state is live (review UX-ui U12): changing it prepares the new state at the current moment (an ideal preparation:
the former state is discarded; lfviz.orbitals3d ``_prepare``); a new cloud grid resamples the same state. The quark
pair is a world parameter: another pair is another system (other masses, other levels).
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.core import data
from lfphys.core.quantum import central3d as C
from lfphys.i18n import T, join
from lfphys.theories.models import cornell
from lfviz.orbitals3d import OrbitalWorld
from lfviz.errors import Refusal
from lfviz.params import Param, Schema

from .engine import pair as Q

LETTERS = "SPD"
DISPLAY_RESOLUTION = 1.0 / (2 * 255)  # half a step of the 8-bit picture (cloud texture, slice colour map)


def _p(*a, **k):
    return Param(*a, **k)


SUPER = {"mode": ["super"]}
PREP = T("Changes on the fly: the new state is prepared at the current moment (an ideal preparation; the former one "
         "is discarded); the world, its time and the slices stay")
G_STATE, G_SUPER = T("State"), T("Superposition")
SCHEMA = Schema([
    _p("system", T("Quark pair"), "select", "charm", group=T("System"),
       options=[(k, T("{name} (m = {m} GeV, model)", name=v[0], m=Q.mass(k))) for k, v in Q.SYSTEMS.items()],
       help=T("The pair sets the world (the quark masses, the levels): another pair is a new world")),
    _p("mode", T("State"), "select", "single", group=G_STATE, live=True, help=PREP,
       options=[("single", T("one stationary state")), ("super", T("a superposition of two states"))]),
    _p("n", T("n (radial: 1S, 2S, …)"), "int", 1, group=G_STATE, min=1, max=3, live=True, help=PREP),
    _p("l", T("L (0 — S, 1 — P, 2 — D)"), "int", 0, group=G_STATE, min=0, max=2, live=True, help=PREP),
    _p("m", "m (|m| ≤ L)", "int", 0, group=G_STATE, min=-2, max=2, live=True, help=PREP),
    _p("real", T("Real angular part (p_z, d_z², …) instead of e^{imφ}"), "bool", True, group=G_STATE, live=True,
       help=PREP),
    _p("n2", T("Second state: n"), "int", 1, group=G_SUPER, min=1, max=3, show_if=SUPER, live=True, help=PREP),
    _p("l2", T("Second state: L"), "int", 1, group=G_SUPER, min=0, max=2, show_if=SUPER, live=True, help=PREP),
    _p("m2", T("Second state: m"), "int", 0, group=G_SUPER, min=-2, max=2, show_if=SUPER, live=True, help=PREP),
    _p("real2", T("Second state real"), "bool", True, group=G_SUPER, show_if=SUPER, live=True,
       help=PREP),
    _p("w2", T("Weight of the second state |c₂|²"), "float", 0.5, group=G_SUPER, min=0.01, max=0.99, show_if=SUPER,
       live=True, help=PREP),
    _p("phase2", T("Phase of c₂ relative to c₁, °"), "float", 0.0, group=G_SUPER, min=-180.0, max=180.0,
       show_if=SUPER, live=True, help=PREP),
    _p("ng", T("Cloud grid, points per axis"), "select", 96, group=T("Cloud grid"), options=[(64, "64"), (96, "96")],
       live=True, help=T("Changes on the fly: the cloud is recomputed on the new grid; the state and its time stay "
                         "the same")),
], presets={
    "cc_1S": {"label": T("cc̄ 1S (J/ψ, η_c without spin): a cloud without nodes"), "params": {}},
    "cc_1P": {"label": "cc̄ 1P (χ_c, h_c), p_z", "params": {"l": 1}},
    "cc_2S": {"label": T("cc̄ 2S (ψ(2S)): one radial node"), "params": {"n": 2}},
    "cc_1D": {"label": "cc̄ 1D, d_z²", "params": {"l": 2}},
    "cc_1P_m1": {"label": T("cc̄ 1P, m = {m:+d} complex: a ring current", m=1),
                 "params": {"l": 1, "m": 1, "real": False}},
    "bb_1S": {"label": T("bb̄ 1S (Υ(1S)): a tighter cloud, heavier quarks"), "params": {"system": "bottom"}},
    "bb_1P": {"label": "bb̄ 1P (χ_b), p_z", "params": {"system": "bottom", "l": 1}},
    "bb_2S": {"label": "bb̄ 2S (Υ(2S))", "params": {"system": "bottom", "n": 2}},
    "bb_1D": {"label": "bb̄ 1D, d_z²", "params": {"system": "bottom", "l": 2}},
    "cc_super": {"label": T("cc̄ 1S + 1P_z: the pair sways at the transition frequency (a superposition)"),
                 "params": {"mode": "super", "n2": 1, "l2": 1, "m2": 0, "ng": 64}},
})


def _spec(p, suffix=""):
    n, l, m = int(p["n" + suffix]), int(p["l" + suffix]), int(p["m" + suffix])
    if not (1 <= n <= 3 and 0 <= l <= 2):
        raise Refusal(T("n must be from 1 to {nmax} and L from 0 to {lmax}", nmax=3, lmax=2))
    if abs(m) > l:
        raise Refusal(T("|m| ≤ L is required (L = {l}, m = {m})", l=l, m=m))
    return n, l, m, bool(p["real" + suffix])


def _fit_numbers(p, suffix=""):
    """Review UX-params P10: the form cannot bound m by L, so the world takes the nearest allowed m (|m| ≤ L), changes
    ``p`` in place (the header's parameters are the state shown) and says so."""
    l, m = int(p["l" + suffix]), int(p["m" + suffix])
    if abs(m) <= l:
        return []
    m_new = l if m > 0 else -l
    p["m" + suffix] = m_new
    what = T("|m{s}| = {am} exceeds L{s} = {l}: m{s} = {m1} taken; for |m| = {am} choose L ≥ {am}", s=suffix,
             am=abs(m), l=l, m1=m_new)
    if suffix:
        return [T("Quantum numbers of the second state: {what}.", what=what)]
    return [T("Quantum numbers: {what}.", what=what)]


def _fit_second(p):
    """The second state left at its defaults (1P_z) but equal to the first: the world takes 1S and says so (P10); a
    second state chosen equal to the first by hand is refused."""
    d = SCHEMA.defaults()
    if p["mode"] != "super" or any(p[k] != d[k] for k in ("n2", "l2", "m2", "real2")):
        return []
    if (int(p["n"]), int(p["l"]), int(p["m"]), bool(p["real"])) != (int(p["n2"]), int(p["l2"]), int(p["m2"]),
                                                                       bool(p["real2"])):
        return []
    p.update(n2=1, l2=0, m2=0)
    return [T("The default second state (1P_z) equals the first: 1S taken instead.")]


def _label(n, l, m, real):
    name = C.orbital_name(l, m, real)
    return f"{n}{LETTERS[l]}" + ("" if l == 0 else (name[1:] if real else f", m = {m:+d}"))


class Simulation(OrbitalWorld):
    group = T("Quarkonium (model)")

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        for text in self._set_state(self.params):
            self._msg({"type": "notice", "t": 0.0, "text": text})
        self._build()
        self._levels()
        self._checks()

    def _set_state(self, p):
        """The state of the parameters ``p`` (m fitted in place, said in the returned notices): the world's state
        attributes before ``_build``. Raises (nothing of the world changed) when it cannot be made."""
        fitted = _fit_numbers(p) + (_fit_numbers(p, "2") if p["mode"] == "super" else []) + _fit_second(p)
        self.system = p["system"]
        self.mq = Q.mass(self.system)
        specs = [_spec(p)]
        coefs = [1.0]
        if p["mode"] == "super":
            specs.append(_spec(p, "2"))
            if specs[1] == specs[0]:
                raise Refusal(T("the second state equals the first: there is no superposition"),
                              hint=T("choose another n, L or m of the second state (group “{group}”)", group=G_SUPER))
            w2 = float(p["w2"])
            coefs = [math.sqrt(1 - w2), math.sqrt(w2) * np.exp(1j * math.radians(float(p["phase2"])))]
        tabs = Q.tables(self.system, specs)
        orbs = [C.Orbital(tb["R"], l, m, real, tb["E"], _label(n, l, m, real))
                for tb, (n, l, m, real) in zip(tabs, specs)]
        if len(specs) == 2 and specs[0][:2] == specs[1][:2]:
            Th, P, W = C.angular_quadrature(specs[0][1])
            ov = abs(np.sum(W * np.conj(orbs[0].angular(Th, P)) * orbs[1].angular(Th, P)))
            if ov > 1e-12:
                raise Refusal(T("the states {a} and {b} are not orthogonal (overlap {ov:.3f}): one is expressed "
                                "through the other", a=orbs[0].label, b=orbs[1].label, ov=float(ov)),
                              hint=T("choose another m or another kind of angular part (real / complex) for the "
                                     "second state"))
        self.specs, self.tabs = specs, tabs
        self.state = C.Superposition(orbs, coefs)
        self.mu, self.hbar = 0.5 * self.mq, 1.0
        self.Lu, self.units, self.tu = Q.HBARC_GEV_FM, T("fm"), Q.HBAR_GEV_S
        self.r_max = max(tb["R_box"] for tb in self.tabs)
        self.ng = int(p["ng"])
        self.rb_state = min(C.moment(o.R, 1, self.r_max) for o in orbs)
        self.scale_min = 1.0 / (self.mu * cornell.PARAMS["kappa"])  # the Bohr radius of the Coulomb part
        self.ref_tabs = Q.tables(self.system, specs, Q.N_REF)
        return fitted

    # --- live: the state is prepared at the current moment (review UX-ui U12) -------------------------------------------
    def live_values(self):
        return {k: self.params[k] for k in SCHEMA.live_ids()}

    def set_live(self, values):
        values = dict(values)
        if isinstance(values.get("ng"), str) and values["ng"].strip().isdigit():  # a select's value comes as text
            values["ng"] = int(values["ng"])
        new, errors = SCHEMA.coerce_live(self.live_values(), values)
        if errors:
            raise ValueError(join(errors))
        changed = [k for k in values if new[k] != self.params[k]]
        if not changed:
            return T("no changes")
        p = {**self.params, **new}
        grid_only = set(changed) == {"ng"}
        notices = []

        def build():
            notices.extend(self._set_state(p))
            self.params = p
        was = " + ".join(o.label for o in self.state.orbitals)
        self._prepare(build, keep_time=grid_only, notices=notices)
        if grid_only:
            return T("cloud grid: {n} points per axis; the cloud is recomputed, the state and its time stay the same",
                     n=self.ng)
        now = " + ".join(o.label for o in self.state.orbitals)
        done = T("prepared the state {now} at t = {t} s (it was {was}; the former one is discarded: an ideal "
                 "preparation)", now=now, t=float(f"{self.t:.6g}"), was=was)
        return join([done, join(notices, " ")])

    # --- the independent route ------------------------------------------------------------------------------------------
    verify_note = T("reference: the radial function of a second solution on a finer grid, Y_lm by scipy; tolerance: "
                    "3 × the difference of the two radial solutions (their accuracy is the check “Convergence”) and "
                    "the round-off of the harmonics")

    def _reference(self, x, y, z, t):
        return Q.reference(self.system, self.specs, self.state.c, x, y, z, t, self.ref_tabs, self.tabs)

    # --- levels of the model (splittings) and the data ------------------------------------------------------------------
    def _levels(self):
        table = data.CHARMONIUM if self.system == "charm" else data.BOTTOMONIUM
        self.levels = []
        E = {}
        for L in range(3):
            EL = Q.solve(self.system, L)[0]
            for n in range(1, 4):
                E[(n, L)] = float(EL[n - 1])
        self.E1S = E[(1, 0)]
        m1s, _ = data.spin_averaged(table, 0, 1)
        for (n, L), e in E.items():
            meas, used = data.spin_averaged(table, L, n)
            self.levels.append({"key": f"{n},{L}", "label": f"{n}{LETTERS[L]}", "col": L, "E": (e - self.E1S) * 1e3,
                                "data": (meas - m1s) if meas else None, "used": used})

    # --- checks -------------------------------------------------------------------------------------------------------------
    def _checks(self):
        P = cornell.PARAMS
        V = cornell.potential(P["kappa"], P["a"])
        rr = np.linspace(0.0, self.r_max, 20001)
        for k, (o, tb, tr, (n, l, m, real)) in enumerate(zip(self.state.orbitals, self.tabs, self.ref_tabs,
                                                               self.specs)):
            tag = f" ({o.label})" if len(self.specs) > 1 else ""
            norm = C.moment(o.R, 0, self.r_max)
            self._check(f"norm_{k}", T("Normalisation ∫|ψ|²dV{tag}: quadrature of the spline", tag=tag), norm, 1.0,
                        tol=max(tb["est"], 1e-9),
                        note=T("the radial function is normalised on the solver's grid; tolerance: the estimate of "
                               "its error (the difference of the grids N and 2N + 1)"))
            Rn, Rr = o.R(rr), tr["R"](rr)
            conv = float(np.max(np.abs(Rn - Rr)) / np.max(np.abs(Rr)))
            self._check(f"conv_{k}", T("Convergence{tag}: R(r) of the grid N = {n1:d} against N = {n2:d}", tag=tag,
                                       n1=Q.N_GRID, n2=Q.N_REF), conv, 0.0,
                        tol=DISPLAY_RESOLUTION, ok=conv <= DISPLAY_RESOLUTION,
                        note=T("fraction of max|R|; tolerance: half a step of the 8-bit picture (the cloud and the "
                               "slice windows): the difference of the solutions must not be visible"))
            Tk, Vk = C.energy_terms(o.R, o.R.derivative, l, V, self.r_max, self.mu)
            Tr, Vr = C.energy_terms(tr["R"], tr["R"].derivative, l, V, self.r_max, self.mu)
            tol = 3 * (abs((Tk + Vk) - (Tr + Vr)) + abs(tb["E"] - tr["E"])) + 1e-12
            self._check(f"energy_{k}", T("Energy ⟨T⟩ + ⟨V⟩ from the wave function{tag} against the eigenvalue",
                                         tag=tag),
                        (Tk + Vk) * 1e3, tb["E"] * 1e3, T("MeV"), tol=tol / abs(tb["E"]),
                        ok=abs(Tk + Vk - tb["E"]) <= tol,
                        note=T("⟨T⟩ = ∫(R′²r² + L(L+1)R²)dr/2μ from the spline, ⟨V⟩ = ∫V R² r² dr; reference: the "
                               "solver's level (Richardson); tolerance: 3 × (the change of both at N → N_ref)"))
            r = np.linspace(1e-9, tb["R_box"], 200001)
            Rv = o.R(r)
            big = np.abs(Rv) > 1e-9 * np.max(np.abs(Rv))
            s = np.sign(Rv[big])
            nodes = int(np.sum(s[1:] != s[:-1]))
            self._check(f"nodes_{k}", T("Radial nodes{tag}: n − 1", tag=tag), nodes, n - 1, ok=nodes == n - 1,
                        note=T("sign changes of R(r) (the solver does not know n: the state's number is its place "
                               "among the levels)"))
            lev = next(v for v in self.levels if v["key"] == f"{n},{l}")
            if n == 1 and l == 0:
                continue
            if lev["data"] is not None:
                self._check(f"split_{k}", T("Splitting M({state}) − M(1S): the model against experiment (PDG)",
                                            state=o.label[:2]),
                            lev["E"], lev["data"], T("MeV"), info=True,
                            note=T("the Cornell model with fitted parameters (κ = {kappa}, a = {a} GeV⁻¹, m = {m} GeV); "
                                   "experiment: spin-averaged masses ({used}); the model does not predict absolute "
                                   "masses (STATUS V17)", kappa=P["kappa"], a=P["a"], m=self.mq,
                                   used=", ".join(lev["used"])))
        inside = min(C.moment(lambda r, o=o: np.where(r <= self.rb, o.R(r), 0.0), 0, self.r_max)
                     for o in self.state.orbitals)
        self._check("box", T("Fraction of the probability in the ball inscribed in the scene's cube"), inside, None,
                    info=True, note=T("the ball of radius {r:.4g} fm is chosen so that at most {f:.0e} lies outside",
                                      r=self.rb * self.Lu, f=1e-3))

    # --- header -----------------------------------------------------------------------------------------------------------
    def engine_modules(self):
        return ["theories.models.cornell", "core.quantum.radial", "core.quantum.central3d", "core.data", "core.geometry"]

    def header(self):
        sp = self.state
        states = []
        for o, ck, tb, (n, l, m, real) in zip(sp.orbitals, sp.c, self.tabs, self.specs):
            rms = math.sqrt(C.moment(o.R, 2, self.r_max)) * self.Lu
            states.append({"label": o.label, "key": f"{n},{l}", "n": n, "l": l, "m": m, "real": real,
                           "w": float(abs(ck) ** 2), "phase_deg": math.degrees(float(np.angle(ck))),
                           "E": (tb["E"] - self.E1S) * 1e3, "r_mean": None,
                           "r_mean_quad": C.moment(o.R, 1, self.r_max) * self.Lu,
                           "extra": [[T("energy in the potential E"), tb["E"] * 1e3, T("MeV")],
                                     ["√⟨r²⟩", rms, T("fm")]]})
        name = Q.SYSTEMS[self.system][0]
        what = " + ".join(s["label"] for s in states)
        P = cornell.PARAMS
        return {
            # the title names the pair (a world parameter), not the state: the state is live (review UX-ui U12)
            "title": T("Quarkonium in 3-D: {name}", name=name),
            "state_label": what,
            "text": T("The cloud |ψ|² is the probability density of the vector r between the quark and the antiquark "
                      "(the centre of mass at the origin) in the Cornell model V(r) = −κ/r + r/a² (a fitted model: "
                      "it predicts the splittings of the levels, not the absolute masses). The radial functions are a "
                      "numerical solution whose accuracy is measured; the arrows are the probability current; the "
                      "slices are planes at any angle with |ψ|² and the phase."),
            "actions": [],
            "approximations": [T("the Cornell model (fitted κ, a, m_q): non-relativistic, without spin forces and "
                                 "without coupling to open channels; it predicts the splittings of the levels, not the "
                                 "absolute masses")],
            "scene3d": self.scene([{"id": "cm", "label": T("Centre of mass of the pair (the cloud is the separation "
                                                           "r = r_q − r_q̄)"),
                                    "kind": "point", "pos": [0.0, 0.0, 0.0], "text": f"{Q.SYSTEMS[self.system][2]}"
                                                                                     f"{Q.SYSTEMS[self.system][2]}̄",
                                    "color": "#ffd23f"}]),
            "units": {"x": T("fm"), "t": T("s"), "E": T("MeV")},
            "system": {"label": name, "m_q": self.mq, "kappa": P["kappa"], "a": P["a"], "mu": self.mu},
            "states": states, "levels": self.levels, "energy_unit": T("MeV"), "level_columns": ["S", "P", "D"],
            "period": self.period if self.nb > 1 else None, "nb": self.nb,
            "omega_E": abs(sp.orbitals[1].energy - sp.orbitals[0].energy) * 1e3 if self.nb > 1 else None,
            "grid": self.ng,
        }, {}


VIZ = {
    "id": "v14_quarkonium_3d",
    "title": T("Quarkonium in 3-D: wave functions"),
    "summary": T("A heavy quark pair cc̄ or bb̄ in the Cornell model: the cloud |ψ|², the probability current, slices "
                 "with the phase, superpositions; the model's level splittings against experiment."),
    "purpose": T("See how the states 1S, 1P, 2S, 1D of quarkonium are built and how charmonium and bottomonium differ; "
                 "the model is fitted and marked as a model, the accuracy of the numerical solution is measured."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
