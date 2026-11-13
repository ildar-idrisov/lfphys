# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u40: the hydrogen atom in 3-D — orbital clouds (a wrapper over lfphys; plan P14.5).

The exact bound states of a hydrogen-like atom (lfphys.core.quantum.hydrogen: R_nl by the log-scaled Laguerre
recurrence; lfphys.core.quantum.central3d: Y_lm, real orbitals, superpositions, the probability current), with the
reduced mass of the electron and the nucleus (hydrogen, deuterium, He+, positronium). The scene: the nucleus, the cloud
|psi|^2 of the relative coordinate (computed on a grid of up to 96^3 points), the probability current (rings around z
for complex m != 0, none for real orbitals, a sloshing flow for a superposition), up to three slice planes computed
exactly for their plane (|psi|^2 and the phase of psi) and checked at points against an independent route (the
Laguerre power series and scipy's harmonics). A superposition of two levels oscillates at the Bohr frequency: its
phases are revealed as the world's time reaches them (lfviz.orbitals3d). Lengths in angstroms, time in seconds.

The state is live (review UX-ui U12): changing it prepares the new state at the current moment (an ideal preparation:
the former state is discarded; lfviz.orbitals3d ``_prepare``); a new cloud grid resamples the same state. The atom is a
world parameter: no operation turns one atom into another while keeping its electron's state.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import constants as sc

from lfphys.core.quantum import central3d as C
from lfphys.core.quantum import hydrogen as H
from lfphys.i18n import T, join
from lfviz.orbitals3d import OrbitalWorld
from lfviz.errors import Refusal
from lfviz.params import Param, Schema

from .engine import atoms as A

N_MAX = 12


def _p(*a, **k):
    return Param(*a, **k)


SUPER = {"mode": ["super"]}
PREP = T("Changes on the fly: the new state is prepared at the current moment (an ideal preparation; the former one "
         "is discarded); the world, its time and the slices stay")
G_STATE, G_SUPER = T("State"), T("Superposition")
SCHEMA = Schema([
    _p("atom", T("Atom"), "select", "H", group=T("Atom"), options=[(k, v[0]) for k, v in A.ATOMS.items()],
       help=T("The nucleus sets the world: another nucleus is a new world (no operation turns one atom into another "
              "with the same state of the electron)")),
    _p("mode", T("State"), "select", "single", group=G_STATE, live=True, help=PREP,
       options=[("single", T("one stationary state")), ("super", T("a superposition of two states"))]),
    _p("n", T("n (principal, n ≥ 1)"), "int", 2, group=G_STATE, min=1, max=N_MAX, live=True, help=PREP),
    _p("l", T("l (orbital, 0 ≤ l < n)"), "int", 1, group=G_STATE, min=0, max=N_MAX - 1, live=True, help=PREP),
    _p("m", T("m (magnetic, |m| ≤ l)"), "int", 0, group=G_STATE, min=-(N_MAX - 1), max=N_MAX - 1, live=True,
       help=PREP),
    _p("real", T("Real orbital (p_x, d_xy, …) instead of a complex one with e^{imφ}"), "bool", True, group=G_STATE,
       live=True,
       help=T("Real orbitals are sums of m and −m: standing waves without a current. Complex ones have a definite m: "
              "the probability current flows in rings around the z axis. {prep}", prep=PREP)),
    _p("n2", T("Second state: n"), "int", 1, group=G_SUPER, min=1, max=N_MAX, show_if=SUPER, live=True,
       help=T("1s by default: “a superposition of two states” with the default first state (2p_z) gives a cloud that sways at the "
              "frequency of the 2p → 1s transition. {prep}", prep=PREP)),
    _p("l2", T("Second state: l"), "int", 0, group=G_SUPER, min=0, max=N_MAX - 1, show_if=SUPER, live=True,
       help=PREP),
    _p("m2", T("Second state: m"), "int", 0, group=G_SUPER, min=-(N_MAX - 1), max=N_MAX - 1,
       show_if=SUPER, live=True, help=PREP),
    _p("real2", T("Second state: real"), "bool", True, group=G_SUPER, show_if=SUPER, live=True,
       help=PREP),
    _p("w2", T("Weight of the second state |c₂|²"), "float", 0.5, group=G_SUPER, min=0.01, max=0.99,
       show_if=SUPER, live=True, help=PREP),
    _p("phase2", T("Phase of c₂ relative to c₁, °"), "float", 0.0, group=G_SUPER, min=-180.0, max=180.0,
       show_if=SUPER, live=True, help=PREP),
    _p("ng", T("Cloud grid, points per axis"), "select", 96, group=T("Cloud grid"), options=[(64, "64"), (96, "96")],
       live=True, help=T("Changes on the fly: the cloud is recomputed on the new grid; the state and its time stay "
                         "the same")),
], presets={
    "1s": {"label": T("1s: the ground state of hydrogen"), "params": {"n": 1, "l": 0, "m": 0}},
    "2pz": {"label": T("2p_z: a dumbbell along z, the nodal plane z = 0"), "params": {"n": 2, "l": 1, "m": 0}},
    "3dz2": {"label": T("3d_z²: lobes along z and a ring"), "params": {"n": 3, "l": 2, "m": 0}},
    "2px_real": {"label": T("2p_x real: a standing wave, no current"),
                 "params": {"n": 2, "l": 1, "m": 1, "real": True}},
    "2p_m1": {"label": T("2p, m = {m:+d} complex: a doughnut and a ring current", m=1),
              "params": {"n": 2, "l": 1, "m": 1, "real": False}},
    "3d_m2": {"label": T("3d, m = {m:+d} complex: the current flows in rings around z", m=2),
              "params": {"n": 3, "l": 2, "m": 2, "real": False}},
    "super_1s2p": {"label": T("1s + 2p_z: the cloud sways along z at the Bohr frequency (a superposition)"),
                   "params": {"mode": "super", "n": 1, "l": 0, "m": 0, "n2": 2, "l2": 1, "m2": 0, "ng": 64}},
    "px_ipy": {"label": T("2p_x + i·2p_y: this is 2p with m = {m:+d} (a superposition of states of equal energy: stationary)",
                          m=1),
               "params": {"mode": "super", "n": 2, "l": 1, "m": 1, "real": True, "n2": 2, "l2": 1, "m2": -1,
                          "real2": True, "phase2": 90.0, "ng": 64}},
    "n10": {"label": T("n = {n}, l = {l}, m = {m}: a large cloud, {k} radial nodes", n=10, l=3, m=1, k=6),
            "params": {"n": 10, "l": 3, "m": 1, "real": True}},
    "he_3dxy": {"label": T("The ion He⁺, 3d_xy: the cloud is smaller by a factor Z = {Z}", Z=2),
                "params": {"atom": "He+", "n": 3, "l": 2, "m": -2, "real": True}},
})


def _spec(p, suffix=""):
    n, l, m = int(p["n" + suffix]), int(p["l" + suffix]), int(p["m" + suffix])
    if not (1 <= n <= N_MAX):
        raise Refusal(T("n{s} must be from 1 to {max}", s=suffix, max=N_MAX))
    if not (0 <= l < n):
        raise Refusal(T("0 ≤ l < n is required (n = {n}, l = {l})", n=n, l=l))
    if abs(m) > l:
        raise Refusal(T("|m| ≤ l is required (l = {l}, m = {m})", l=l, m=m))
    return n, l, m, bool(p["real" + suffix])


def _fit_numbers(p, suffix=""):
    """Review UX-params P10 (owner, 2026-11-04: a choice the form offers must work): the form cannot bound l by n and
    m by l, so the world takes the nearest allowed numbers — n first, then 0 ≤ l < n, then |m| ≤ l — changes ``p`` in
    place (the header's parameters are the state shown) and says what it changed and how to get what was asked."""
    n, l, m = int(p["n" + suffix]), int(p["l" + suffix]), int(p["m" + suffix])
    s = suffix
    out = []
    if l > n - 1:
        out.append(T("l{s} = {l} is impossible with n{s} = {n} (0 ≤ l < n): l{s} = {l1} taken; for l = {l} choose "
                     "n ≥ {n1}", s=s, l=l, n=n, l1=n - 1, n1=l + 1))
        l = n - 1
    if abs(m) > l:
        m_new = l if m > 0 else -l
        out.append(T("|m{s}| = {am} exceeds l{s} = {l}: m{s} = {m1} taken; for |m| = {am} you need l ≥ {am} and "
                     "n ≥ {n1}", s=s, am=abs(m), l=l, m1=m_new, n1=abs(m) + 1))
        m = m_new
    p["l" + suffix], p["m" + suffix] = l, m
    if suffix:
        return [T("Quantum numbers of the second state: {what}.", what=x) for x in out]
    return [T("Quantum numbers: {what}.", what=x) for x in out]


def _fit_second(p):
    """The second state left at its defaults but equal to the first (a first state of 1s with the default second 1s):
    the world takes another one, 2p_z for 1s and 1s otherwise, and says so (P10). A second state chosen equal to the
    first by hand is refused."""
    d = SCHEMA.defaults()
    if p["mode"] != "super" or any(p[k] != d[k] for k in ("n2", "l2", "m2", "real2")):
        return []
    if (int(p["n"]), int(p["l"]), int(p["m"]), bool(p["real"])) != (int(p["n2"]), int(p["l2"]), int(p["m2"]),
                                                                       bool(p["real2"])):
        return []
    if int(p["n"]) == 1:
        p.update(n2=2, l2=1, m2=0)
        return [T("The default second state (1s) equals the first: 2p_z taken instead; the cloud sways at the "
                  "frequency of the 2p → 1s transition.")]
    p.update(n2=1, l2=0, m2=0)
    return [T("The second state equals the first: 1s taken instead.")]


def _ng_as_number(values):
    """The player sends a select's value as text («64»); the cloud grid's options are numbers (64, 96)."""
    v = dict(values)
    if isinstance(v.get("ng"), str) and v["ng"].strip().isdigit():
        v["ng"] = int(v["ng"])
    return v


class Simulation(OrbitalWorld):
    group = T("Hydrogen atom")

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        for text in self._set_state(self.params):
            self._msg({"type": "notice", "t": 0.0, "text": text})
        self._build()
        self._checks()

    def _set_state(self, p):
        """The state of the parameters ``p`` (quantum numbers fitted in place, said in the returned notices): the
        world's state attributes before ``_build``. Raises (nothing of the world changed) when it cannot be made."""
        fitted = _fit_numbers(p) + (_fit_numbers(p, "2") if p["mode"] == "super" else []) + _fit_second(p)
        self.u = A.units(p["atom"])
        self.Z = self.u["Z"]
        specs = [_spec(p)]
        coefs = [1.0]
        if p["mode"] == "super":
            specs.append(_spec(p, "2"))
            if specs[1] == specs[0]:
                raise Refusal(T("the second state equals the first: there is no superposition"),
                              hint=T("choose another n, l or m of the second state (group “{group}”)", group=G_SUPER))
            w2 = float(p["w2"])
            coefs = [math.sqrt(1 - w2), math.sqrt(w2) * np.exp(1j * math.radians(float(p["phase2"])))]
        orbs = [H.orbital(n, l, m, Z=self.Z, real=real) for n, l, m, real in specs]
        if len(specs) == 2 and specs[0][:2] == specs[1][:2]:  # same n, l: the angular parts must be orthogonal
            Th, P, W = C.angular_quadrature(specs[0][1])
            ov = abs(np.sum(W * np.conj(orbs[0].angular(Th, P)) * orbs[1].angular(Th, P)))
            if ov > 1e-12:
                raise Refusal(T("the states {a} and {b} are not orthogonal (overlap {ov:.3f}): one is expressed "
                                "through the other", a=orbs[0].label, b=orbs[1].label, ov=float(ov)),
                              hint=T("choose another m or another kind of orbital (real / complex) for the second "
                                     "state"))
        self.specs = specs
        self.state = C.Superposition(orbs, coefs)
        self.Lu, self.units, self.tu = self.u["Lu"], "Å", self.u["tu"]  # Å: the same symbol in every language
        nmax = max(s[0] for s in specs)
        self.r_max = (2.0 * nmax * nmax + 40.0 * nmax) / self.Z
        self.ng = int(p["ng"])
        self.rb_state = min(H.expectation(n, l, 1, self.Z) for n, l, _, _ in specs)
        self.scale_min = 1.0 / self.Z  # psi varies on a / Z at the nucleus (the cusp of s states)
        return fitted

    # --- live: the state is prepared at the current moment (review UX-ui U12) -------------------------------------------
    def live_values(self):
        return {k: self.params[k] for k in SCHEMA.live_ids()}

    def set_live(self, values):
        values = _ng_as_number(values)
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

    # --- the independent route -------------------------------------------------------------------------------------
    verify_note = T("reference: R_nl by the power series (exact coefficients), Y_lm by scipy; tolerance: bounds of "
                    "their round-off")

    def _reference(self, x, y, z, t):
        return A.reference(self.specs, self.state.c, self.Z, x, y, z, t)

    def _dipole_ref(self):
        (n1, l1, m1, r1), (n2, l2, m2, r2) = self.specs
        if {(n1, l1), (n2, l2)} == {(1, 0), (2, 1)} and m1 == m2 == 0 and self.Z == 1:
            return np.array([0.0, 0.0, H.DIPOLE_1S_2P0]), T("⟨1s|z|2p₀⟩ = 2⁷√2/3⁵ a (Bethe and Salpeter)"), True
        return super()._dipole_ref()

    # --- checks of the states (closed forms of the exact solution) ------------------------------------------------------
    def _checks(self):
        eV, Lu = self.u["eV"], self.Lu
        for k, (o, (n, l, m, real)) in enumerate(zip(self.state.orbitals, self.specs)):
            tag = f" ({o.label})" if len(self.specs) > 1 else ""
            norm = C.moment(o.R, 0, self.r_max)
            n2 = C.moment(o.R, 0, self.r_max, panels=800)
            self._check(f"norm_{k}", T("Normalisation ∫|ψ|²dV{tag}: quadrature", tag=tag), norm, 1.0,
                        tol=1e-12 + 10 * abs(norm - n2),
                        note=T("Gauss–Legendre radial panels (the angular part is normalised exactly); tolerance: "
                               "{a:.0e} + 10 × the difference with twice as many panels", a=1e-12))
            rm = C.moment(o.R, 1, self.r_max)
            self._check(f"r_{k}", T("Mean radius ⟨r⟩{tag}", tag=tag), rm * Lu, H.expectation(n, l, 1, self.Z) * Lu,
                        "Å", tol=1e-10, note=T("quadrature of |ψ|² against a/(2Z)·[3n² − l(l+1)]"))
            Tk, Vk = C.energy_terms(o.R, C.derivative_fd(o.R, n / self.Z), l, lambda r: -self.Z / r, self.r_max)
            self._check(f"energy_{k}", T("Energy ⟨T⟩ + ⟨V⟩ from the wave function{tag}", tag=tag), (Tk + Vk) * eV,
                        o.energy * eV, T("eV"), tol=1e-9,
                        note=T("⟨T⟩ = ½∫(R′²r² + l(l+1)R²)dr (R′ by 4th-order differences), ⟨V⟩ = −Z⟨1/r⟩; reference "
                               "−μc²(Zα)²/2n² with the reduced mass; virial −⟨V⟩/⟨T⟩ = {vir:.12f} (exactly 2)",
                               vir=float(-Vk / Tk)))
            r = np.linspace(1e-9, self.r_max, 400001)
            R = o.R(r)
            big = np.abs(R) > 1e-12 * np.max(np.abs(R))
            sgn = np.sign(R[big])
            nodes = int(np.sum(sgn[1:] != sgn[:-1]))
            self._check(f"nodes_{k}", T("Radial nodes{tag}: n − l − 1", tag=tag), nodes, n - l - 1,
                        ok=nodes == n - l - 1, note=T("sign changes of R(r) on a grid; points: {npts:d}", npts=400001))
        inside = min(C.moment(lambda r, o=o: np.where(r <= self.rb, o.R(r), 0.0), 0, self.r_max)
                     for o in self.state.orbitals)
        self._check("box", T("Fraction of the probability in the ball inscribed in the scene's cube"), inside, None,
                    info=True, note=T("the ball of radius {r:.4g} Å is chosen so that at most {f:.0e} lies outside",
                                      r=self.rb * Lu, f=1e-3))

    # --- header -----------------------------------------------------------------------------------------------------------
    def engine_modules(self):
        return ["core.quantum.hydrogen", "core.quantum.central3d", "core.geometry"]

    def header(self):
        u, sp = self.u, self.state
        states = []
        for o, ck, (n, l, m, real) in zip(sp.orbitals, sp.c, self.specs):
            states.append({"label": o.label, "n": n, "l": l, "m": m, "real": real, "w": float(abs(ck) ** 2),
                           "phase_deg": math.degrees(float(np.angle(ck))), "E": o.energy * u["eV"],
                           "r_mean": H.expectation(n, l, 1, self.Z) * self.Lu,
                           "r_mean_quad": C.moment(o.R, 1, self.r_max) * self.Lu})
        nmax = max(6, max(s[0] for s in self.specs))
        lmax = max(3, max(s[1] for s in self.specs))
        letters = "spdfghik"
        levels = [{"key": f"{n},{l}", "label": T("n = {n}", n=n) if l == 0 and n <= 4 else "", "col": l,
                   "E": H.level(n, self.Z, u["mu"]) / sc.e} for l in range(lmax + 1) for n in range(l + 1, nmax + 1)]
        for st in states:
            st["key"] = f"{st['n']},{st['l']}"
        what = " + ".join(s["label"] for s in states)
        return {
            # the title names the atom (a world parameter), not the state: the state is live (review UX-ui U12)
            "title": T("The hydrogen atom in 3-D") if self.params["atom"] == "H" else T(
                "A hydrogen-like atom in 3-D: {atom}", atom=u["label"]),
            "state_label": what,
            "text": join([T("The cloud |ψ|² is the probability density of finding the electron at a point relative to "
                            "the nucleus (the exact solution of the Schrödinger equation with the reduced mass). The "
                            "arrows are the probability current. The slices are planes at any angle: |ψ|² and the "
                            "phase of ψ, computed for the plane and verified against an independent calculation."),
                          T("A superposition of two levels: the cloud oscillates at the Bohr frequency; the phases "
                            "of the period are revealed when the world's time reaches them.") if self.nb > 1 else ""],
                         " "),
            "actions": [],
            "scene3d": self.scene([{"id": "nucleus", "label": T("Nucleus ({mark}) at the origin", mark=u["mark"]),
                                    "kind": "point", "pos": [0.0, 0.0, 0.0], "text": u["mark"], "color": "#ffd23f"}]),
            "units": {"x": "Å", "t": T("s"), "E": T("eV")},
            "atom": {"label": u["label"], "Z": self.Z, "mu_over_me": u["mu"] / sc.m_e, "a_A": self.Lu,
                     "Eh_eV": u["eV"], "tu": self.tu},
            "states": states, "levels": levels, "energy_unit": T("eV"), "levels_top": 0.0,
            "level_columns": [letters[l] if l < len(letters) else f"l={l}" for l in range(lmax + 1)],
            "period": self.period if self.nb > 1 else None, "nb": self.nb,
            "omega_E": (abs(sp.orbitals[1].energy - sp.orbitals[0].energy) * u["eV"]) if self.nb > 1 else None,
            "grid": self.ng,
        }, {}


VIZ = {
    "id": "u40_hydrogen_3d",
    "title": T("The hydrogen atom in 3-D: orbitals"),
    "summary": T("The exact wave functions of a hydrogen-like atom: the cloud |ψ|², the probability current, slices "
                 "at any angle with the phase; real and complex orbitals, superpositions oscillating at the Bohr "
                 "frequency."),
    "purpose": T("See the shapes of the orbitals, their nodes, the difference between real and complex states (a "
                 "standing wave or a ring current) and the motion of the cloud in a superposition — all computed by "
                 "the engine and verified against an independent calculation."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
    "audience": "university",
    "section": "atom",
    "ui": "standard",
    "teaser": T("The orbitals of hydrogen in 3-D: clouds, nodes, ring currents and a superposition swaying at the Bohr frequency."),
    "courses": [
        {"text": T("Griffiths & Schroeter, Introduction to Quantum Mechanics"), "chapters": "4"},
        {"text": T("Young & Freedman, University Physics"), "chapters": "41"},
        {"text": T("Sivukhin, General Course of Physics, vol. V: Atomic and Nuclear Physics"), "chapters": ""},
    ],
    "related": ["S42"],
    "recordings": [
        {"id": "3dz2", "preset": "3dz2", "seconds": 30, "fps": 20, "speed": None, "seed": 1, "script": [], "poster": 10},
        {"id": "ring_current", "preset": "2p_m1", "seconds": 30, "fps": 20, "speed": None, "seed": 1, "script": [], "poster": 10},
        {"id": "superposition", "preset": "super_1s2p", "seconds": 30, "fps": 20, "speed": None, "seed": 1, "script": [], "poster": 20},
    ],
}
