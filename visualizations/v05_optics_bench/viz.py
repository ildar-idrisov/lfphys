# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v05: the optical bench - single photons at a boundary between media, at coatings and at a thin metal film.

What the run computes (README.md of this folder has the model in full), all with the engine lfphys:
* the structure's amplitudes r, t and powers R, T, A = 1 - R - T by the transfer matrices
  (lfphys.core.optics.interfaces.stack) for the source's wavelength, angle and polarization, and the curves R(theta),
  T(theta) at the current wavelength and R(lambda), T(lambda) at the current angle;
* the field |E|^2 of s-polarized light through the structure (interfaces.field_profile);
* the stream of single photons: every photon's fate (reflected, transmitted, absorbed) drawn by the Born rule with
  the computed R, T, A when it reaches the structure, revealed when it reaches a detector (or, if absorbed, the
  structure); the counts are the accumulation of these events;
* checks against closed forms (lfphys.core.optics.thin_films): Brewster, critical angle and R = 1 beyond it, the
  evanescent decay length, the quarter-wave antireflection layer, the Bragg mirror, the Airy formula of a film, the
  Airy summation of any single layer, frustrated total reflection, Joule heating, and the photon statistics.
"""

from __future__ import annotations

import math

import numpy as np
from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from lfviz.sim import Simulation as BaseSimulation

from lfphys.core.constants import C
from lfphys.core.optics import interfaces, thin_films
from lfphys.codes import code_of, data_of
from lfphys.i18n import T, is_t, join

from .engine.bench import (ARM_M, P_5SIGMA, POL_LABEL, STRUCT_LABEL, STRUCTS, TH_MAX, Stream, Structure,
                           born_probs, brewster_from_rp, build_structure, critical_from_T, curves, field, field_grid,
                           flight_times, outcome_test, ray_angles, rta)

U = 2.0 ** -53  # unit round-off of binary64 (the derived tolerances of the evan and film checks)


def _p(*a, **k):
    k.setdefault("live", True)  # the whole bench is set-up an experimenter changes while the world runs
    return Param(*a, **k)


SHOW = lambda *kinds: {"structure": list(kinds)}  # noqa: E731

G_SRC, G_MED, G_STR = T("Source"), T("Media"), T("Structure")

SCHEMA = Schema([
    # source
    _p("lam_nm", T("Wavelength λ, nm"), "float", 633.0, group=G_SRC, min=300.0, max=1600.0),
    _p("theta_deg", T("Angle of incidence θ, °"), "float", 45.0, group=G_SRC, min=0.0, max=TH_MAX,
       help=T("The angle between the beam and the normal to the surface. The source and both detectors stand on a "
              "rotary table: when it turns, the photons already flying along the old paths are lost (the count "
              "“lost”).")),
    _p("pol", T("Polarisation"), "select", "unpol", group=G_SRC,
       options=[("s", T("s (TE): E ⊥ the plane of incidence")), ("p", T("p (TM): E in the plane of incidence")),
                ("unpol", POL_LABEL["unpol"])]),
    _p("rate", T("Photons per second (world time)"), "float", 4e9, group=G_SRC, min=1.0, max=1e15, log=True,
       help=T("A Poisson stream of single photons. The flight along an arm of {arm:.3g} cm takes about {t:.1g} ns.",
              arm=ARM_M * 100, t=ARM_M / C * 1e9)),
    # media
    _p("n0", T("Incidence medium n₀"), "float", 1.0, group=G_MED, min=1.0, max=4.0,
       help=T("The refractive index of the medium the light comes from (real, no dispersion).")),
    _p("ns", T("Exit medium (substrate) n_s"), "float", 1.5, group=G_MED, min=1.0, max=4.0,
       help=T("The medium behind the structure. In the mode “total internal reflection”: the rarer medium beyond "
              "the prism's face (and the medium of the gap, if a second prism stands behind it).")),
    # structure
    _p("structure", T("Structure"), "select", "interface", group=G_STR, options=STRUCTS,
       help=T("Every structure is computed by one and the same function of the engine: transfer matrices (lfphys "
              "interfaces.stack).")),
    _p("lam0_nm", T("Design wavelength λ₀, nm"), "float", 550.0, group=G_STR, min=300.0, max=1600.0,
       show_if=SHOW("ar", "bragg"), help=T("Every layer is λ₀/(4n) thick.")),
    _p("ar_n", T("Film index n_f"), "float", 1.38, group=G_STR, min=1.0, max=4.0, show_if=SHOW("ar"),
       help=T("{n} is like MgF₂ (illustrative); R(λ₀) = 0 at n_f = √(n₀ n_s).", n=1.38)),
    _p("nH", T("High index n_H"), "float", 2.3, group=G_STR, min=1.0, max=4.0, show_if=SHOW("bragg")),
    _p("nL", T("Low index n_L"), "float", 1.45, group=G_STR, min=1.0, max=4.0, show_if=SHOW("bragg")),
    _p("pairs", T("Number of pairs N (layers H, L)"), "int", 8, group=G_STR, min=1, max=30, show_if=SHOW("bragg")),
    _p("fp_n", T("Film index"), "float", 2.3, group=G_STR, min=1.0, max=4.0, show_if=SHOW("fp")),
    _p("fp_d_nm", T("Film thickness, nm"), "float", 2000.0, group=G_STR, min=1.0, max=20000.0, log=True,
       show_if=SHOW("fp")),
    _p("metal_n", T("Metal: n (the real part of the index)"), "float", 0.2, group=G_STR, min=0.01, max=5.0,
       show_if=SHOW("metal")),
    _p("metal_k", T("Metal: κ (the imaginary part, extinction)"), "float", 3.3, group=G_STR, min=0.0, max=20.0,
       show_if=SHOW("metal")),
    _p("metal_d_nm", T("Metal thickness, nm"), "float", 30.0, group=G_STR, min=0.1, max=500.0, log=True,
       show_if=SHOW("metal")),
    _p("tir_gap_nm", T("Gap to a second prism, nm (0: no prism)"), "float", 0.0, group=G_STR, min=0.0,
       max=5000.0, show_if=SHOW("tir"),
       help=T("A second prism of the same glass n₀ behind a gap of the medium n_s: frustrated total reflection, the "
              "light tunnels through the gap.")),
], presets={
    "brewster": {"label": T("Glass n = {n} in air at Brewster's angle (unpolarised light: only s is reflected)",
                            n=1.5),
                 "params": {"structure": "interface", "n0": 1.0, "ns": 1.5, "theta_deg": 56.31, "pol": "unpol",
                            "lam_nm": 633.0}},
    "tir": {"label": T("Total internal reflection: glass {n} → air, θ = {th}° beyond the critical angle", n=1.5,
                       th=60),
            "params": {"structure": "tir", "n0": 1.5, "ns": 1.0, "theta_deg": 60.0, "pol": "unpol", "tir_gap_nm": 0.0,
                       "lam_nm": 633.0}},
    "ftir": {"label": T("Frustrated total reflection: a {gap} nm gap to a second prism (photon tunnelling)", gap=200),
             "params": {"structure": "tir", "n0": 1.5, "ns": 1.0, "theta_deg": 45.0, "pol": "s", "tir_gap_nm": 200.0,
                        "lam_nm": 633.0}},
    "ar_mgf2": {"label": T("Anti-reflection of glass by a λ/4 layer with n_f = {n} (like MgF₂, illustrative), "
                           "λ₀ = {lam0} nm", n=1.38, lam0=550),
                "params": {"structure": "ar", "n0": 1.0, "ns": 1.5, "ar_n": 1.38, "lam0_nm": 550.0, "lam_nm": 550.0,
                           "theta_deg": 0.0, "pol": "s"}},
    "ar_ideal": {"label": T("Anti-reflection by an ideal λ/4 layer: n_f = √{ns} ≈ {nf:.5g}, R(λ₀) = 0", ns=1.5,
                            nf=math.sqrt(1.5)),
                 "params": {"structure": "ar", "n0": 1.0, "ns": 1.5, "ar_n": math.sqrt(1.5), "lam0_nm": 550.0,
                            "lam_nm": 550.0, "theta_deg": 0.0, "pol": "s"}},
    "bragg": {"label": T("Bragg mirror (H L)×{N:d}: n_H = {nH}, n_L = {nL} (like TiO₂/SiO₂, illustrative) on glass "
                         "{ns}", N=8, nH=2.3, nL=1.45, ns=1.52),
              "params": {"structure": "bragg", "n0": 1.0, "ns": 1.52, "nH": 2.3, "nL": 1.45, "pairs": 8,
                         "lam0_nm": 550.0, "lam_nm": 550.0, "theta_deg": 0.0, "pol": "s"}},
    "fp": {"label": T("Fabry–Pérot: a film n = {n}, {d} µm thick, in air (illustrative)", n=2.3, d=2),
           "params": {"structure": "fp", "n0": 1.0, "ns": 1.0, "fp_n": 2.3, "fp_d_nm": 2000.0, "lam_nm": 633.0,
                      "theta_deg": 0.0, "pol": "s"}},
    "metal": {"label": T("Metal film {d} nm, n = {n} + {k}i (like gold at {lam} nm, illustrative) on glass", d=30,
                         n=0.2, k=3.3, lam=633),
              "params": {"structure": "metal", "n0": 1.0, "ns": 1.5, "metal_n": 0.2, "metal_k": 3.3,
                         "metal_d_nm": 30.0, "lam_nm": 633.0, "theta_deg": 0.0, "pol": "unpol"}},
    "spr": {"label": T("Surface plasmon resonance (Kretschmann): prism {n0}, metal {d} nm (n = {n} + {k}i), air, p "
                       "(illustrative)", n0=1.5, d=50, n=0.2, k=3.3),
            "params": {"structure": "metal", "n0": 1.5, "ns": 1.0, "metal_n": 0.2, "metal_k": 3.3,
                       "metal_d_nm": 50.0, "lam_nm": 633.0, "theta_deg": 44.58, "pol": "p"}},
})

# what a live change touches (owner, 2026-10-23: the set-up changes at once, as in a laboratory)
PATH_FIELDS = ("n0", "ns", "theta_deg")  # the beam paths (media, goniometer): photons under way are lost
SOURCE_FIELDS = ("lam_nm", "pol", "rate")  # new photons only; those under way fly on and are transitional
STAT_STEPS = (1, 2, 5)
# joule: the Gauss-Legendre remainder is < 1e-25 (thin_films._layer_nodes); what is left is the float rounding of
# |E|^2 and of R + T, <= 1.5e-14 over 3000 random absorbing films in the ranges of this bench
JOULE_TOL = 1e-12
OUT_NAMES = ("R", "T", "A")


class Simulation(BaseSimulation):
    speed_range = (1e-15, 1e3)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = dict(params)
        self._buf = []
        self.seg = -1
        self.st = build_structure(self.params)
        self.flight = Stream()
        self.pid = 0
        self.t_next = float(self.rng.exponential(1.0 / self.params["rate"]))
        self.tot = dict(emitted=0, R=0, T=0, A=0, lost=0, transitional=0)
        self.segc: dict[int, dict] = {}
        self.cache: dict = {}
        self.times = flight_times(self.st)
        self.default_speed = self.times["t_in"] / 1.2  # one arm in about 1.2 s of wall time
        try:
            self._new_segment(T("start"))
        except ValueError:
            raise
        except Exception as e:  # reported as a refused world (the runner catches ValueError), never a crash
            err = f"{type(e).__name__}: {e}"
            raise Refusal(T("internal error of the world: {err}", err=type(e).__name__), detail=err) from e

    def engine_modules(self):
        return ["core.optics.interfaces", "core.optics.thin_films", "core.constants", "theories.approx.ray_optics"]

    # --- messages -------------------------------------------------------------------------------------
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
        """``info``: a comparison shown for information, never a pass or a failure (RULES.md §3, check message)."""
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

    # --- atomic changes -------------------------------------------------------------------------------------
    def _atomic(self, fn, *args):
        """Apply a change of the world as one transaction (review 2026-10-23, V5-1): the messages it produces are
        held back until it has succeeded as a whole; if anything raises, the world's state (parameters, structure,
        photons in flight, counters, segments, the random generator) is restored and nothing is emitted. Any
        exception becomes a ValueError, which the runner reports as a refused change, followed by the live values
        in force (the player rolls its control back)."""
        snap = {k: (v.copy() if isinstance(v, (dict, list)) else v) for k, v in self.__dict__.items()}
        flight, flight_cols = self.flight, dict(self.flight.a)  # Stream.add/keep replace its columns, never edit them
        rng_state = self.rng.bit_generator.state
        outer = self._buf
        self._buf = []
        try:
            out = fn(*args)
        except Exception as e:
            self.__dict__.clear()
            self.__dict__.update(snap)
            flight.a = flight_cols
            self.rng.bit_generator.state = rng_state
            self._buf = outer
            if isinstance(e, ValueError):
                raise
            err = f"{type(e).__name__}: {e}"
            raise Refusal(T("internal error of the world: {err} (the world is left as it was)", err=type(e).__name__),
                          detail=err) from e
        buf, self._buf = self._buf, outer
        for meta, blobs in buf:
            self._msg(meta, blobs)
        return out

    # --- live changes (command "set") ---------------------------------------------------------------------
    def live_values(self):
        return {k: self.params[k] for k in SCHEMA.live_ids()}

    def set_live(self, values):
        return self._atomic(self._set_live, values)

    def _set_live(self, values):
        new, errors = SCHEMA.coerce_live(self.params, values)
        if errors:
            raise Refusal(join(errors))
        changed = [k for k in SCHEMA.live_ids() if not _same(new[k], self.params[k])]
        if not changed:
            return T("no changes")
        st = build_structure(new)  # raises on a bad set-up; nothing of the world is touched before this point
        desc = join([T("{label}: {old} → {new}", label=SCHEMA.by_id[k].label,
                        old=_val(SCHEMA.by_id[k], self.params[k]), new=_val(SCHEMA.by_id[k], new[k]))
                      for k in changed])
        notes = []
        path = any(k in PATH_FIELDS for k in changed) or st.n_out != self.st.n_out
        if path and len(self.flight):
            lost = len(self.flight)
            self.tot["lost"] += lost
            self.flight = Stream()
            notes.append(T("the beam paths were rebuilt (media or angle): photons in flight lost: {k:d}", k=lost))
        elif len(self.flight) and not any(k in SOURCE_FIELDS for k in changed):
            n0 = int(np.sum(self.flight.a["stage"] == 0))
            if n0:
                notes.append(T("photons not yet at the structure: {k:d}; they will meet the new structure "
                               "(transitional: not counted in the new segment)", k=n0))
        self.params = new
        self.st = st
        if "rate" in changed:
            self.t_next = self.t + float(self.rng.exponential(1.0 / new["rate"]))
        self._new_segment(T("set-up changed: {changes}", changes=desc))
        for text in notes:
            self._msg({"type": "notice", "t": self.t, "text": text})
        return desc

    def action(self, name, args):
        return self._atomic(self._action, name, args)

    def _action(self, name, args):
        if name == "clear":
            self._new_segment(T("new segment: the counters reset"))
            return T("new segment: the counters reset, the set-up as it was")
        if name == "emit_one":
            self._emit_photons(np.array([self.t]))
            return T("the source emitted one photon")
        raise ValueError(f"unknown action {name!r}")

    def _actions(self):
        return [{"name": "emit_one", "label": T("Emit one photon"), "args": [],
                 "help": T("One photon now, on top of the Poisson stream")},
                {"name": "clear", "label": T("Reset the counters (new segment)"), "args": [],
                 "help": T("The same set-up; the statistics start anew")}]

    # --- one segment: the run's own numbers for the current set-up ------------------------------------------
    def _title(self):
        return T("Optical bench: {structure}", structure=STRUCT_LABEL[self.st.kind])

    def _new_segment(self, reason):
        if self.seg >= 0:
            self._stat_check(self.seg)
        self.seg += 1
        s = self.seg
        self.cache = {}
        p, st = self.params, self.st
        lam, th, pm = float(p["lam_nm"]), math.radians(p["theta_deg"]), p["pol"]
        self.times = flight_times(st)
        cur = {pol: rta(st, lam, th, pol) for pol in ("s", "p")}
        probs = {pol: born_probs(cur[pol]) for pol in ("s", "p")}
        if pm == "unpol":
            pexp = tuple(0.5 * (a + b) for a, b in zip(probs["s"], probs["p"]))
        else:
            pexp = probs[pm]
        self.segc[s] = {"n": 0, "R": 0, "T": 0, "A": 0, "pR": pexp[0], "pT": pexp[1], "pA": pexp[2]}
        self._stat_next = 20
        # angles found by the run from its own transfer matrices. The exit wave becomes evanescent where T of the bare
        # boundary n_in -> n_out vanishes: n sin(theta) is the same in every layer, so the layers do not move this
        # angle, while T of a thick structure can underflow to exactly 0 long before it (an evanescent thick film)
        th_c = critical_from_T(Structure("interface", st.n_in, st.n_out), lam)
        face = Structure("interface", st.n_in, float(p["ns"]))
        th_c_face = critical_from_T(face, lam) if st.kind == "tir" and st.layers else th_c
        single = not st.layers
        th_B = brewster_from_rp(st.n_in, st.n_out, lam, th_c) if single else None
        deg = lambda x: None if x is None else math.degrees(x)  # noqa: E731
        extra_lam = [lam] + ([float(p["lam0_nm"])] if st.kind in ("ar", "bragg") else [])
        cv, m_spec = curves(st, lam, th, pm, [deg(th_c), deg(th_c_face), deg(th_B), p["theta_deg"]], extra_lam)
        min_rp = None
        if not single:  # the minimum of R_p of the run (a multilayer has no Brewster closed form): grid, then Brent
            i = int(np.argmin(cv["Rp"]))
            if 0 < i < len(cv["th"]) - 1:
                min_rp = {"deg": float(cv["th"][i]), "Rp": float(cv["Rp"][i])}
                min_rp.update(_refine_min_rp(st, lam, float(cv["th"][i - 1]), float(cv["th"][i + 1]), min_rp))
        z = field_grid(st, lam)
        E2 = field(st, lam, th, z)
        angles = ray_angles(st, th)
        mix = {k: 0.5 * (cur["s"][k] + cur["p"][k]) for k in ("R", "T", "A")}
        curd = {"s": {k: cur["s"][k] for k in ("R", "T", "A")}, "p": {k: cur["p"][k] for k in ("R", "T", "A")},
                "mix": mix if pm == "unpol" else {k: cur[pm][k] for k in ("R", "T", "A")}}
        setup = {"title": self._title(), "kind": st.kind, "label": STRUCT_LABEL[st.kind], "n_in": st.n_in,
                 "n_out": st.n_out, "n_s": float(p["ns"]), "out_name": st.out_name, "layers": st.describe(),
                 "thickness": st.thickness, "lam": lam, "lam0": float(p["lam0_nm"]) if st.kind in ("ar", "bragg") else None,
                 "theta": float(p["theta_deg"]), "pol": pm, "pol_label": POL_LABEL[pm], "rate": float(p["rate"]),
                 "lossless": st.lossless, **self.times}
        approx = self._approximations(m_spec)
        blobs = {k: np.asarray(v, np.float64) for k, v in cv.items()}
        blobs["z"] = np.asarray(z, np.float64)
        blobs["E2"] = np.asarray(E2, np.float64)
        self._msg({"type": "segment", "t": self.t, "seg": s, "reason": reason, "setup": setup, "angles": angles,
                   "cur": curd, "expected": dict(zip(OUT_NAMES, pexp)),
                   "theta_B": None if th_B is None else {"deg": deg(th_B), "Rp": rta(face, lam, th_B, "p")["R"]},
                   "min_rp": min_rp, "theta_c": deg(th_c), "theta_c_face": deg(th_c_face), "approx": approx},
                  blobs)
        self._segment_checks(s, cur, cv, th_B, th_c, th_c_face, face)
        if s > 0:
            self._msg({"type": "actions", "t": self.t, "actions": self._actions()})

    def _approximations(self, m_spec):
        st, pm = self.st, self.params["pol"]
        profile = {"s": T("The |E|² profile is for s polarisation (the engine's function field_profile computes s "
                          "only)."),
                   "p": T("The |E|² profile is for s polarisation (the engine's function field_profile computes s "
                          "only). The source is now p: the profile shown is that of the s component."),
                   "unpol": T("The |E|² profile is for s polarisation (the engine's function field_profile computes "
                              "s only). The source is now unpolarised: the profile shown is that of the s "
                              "component.")}[pm]
        out = [T("Plane waves and infinite plane boundaries; homogeneous, isotropic, linear media without dispersion: "
                 "the indices are given numbers (complex for absorption), the same for every λ. The values “like MgF₂, "
                 "TiO₂, gold” are illustrative, not tabulated data."),
               T("Photons one by one: the fate of each (reflected, transmitted, absorbed) is drawn by the Born rule "
                 "with the probabilities R, T, A computed in this run for its wavelength, angle and polarisation."),
               T("The flight along the arms ({arm:.3g} cm) is at the speed c/n (without dispersion the phase and group "
                 "velocities are equal); the time inside the structure (microns) is not counted.", arm=ARM_M * 100),
               T("The rays in the diagram are geometrical optics (Snell's law), approximate; in an absorbing layer, by "
                 "the real part of the index. The structure is drawn to scale, the arms are not."),
               profile]
        if pm == "unpol":
            out.append(T("An unpolarised source is a 50/50 mixture of s and p photons: an isotropic planar structure "
                         "does not mix them, so this is the same as the density matrix ρ = I/2."))
        if m_spec >= 1600:
            out.append(T("The multilayer's spectrum is very dense: {n:d} points may not resolve every band at short "
                         "wavelengths.", n=1600))
        out.extend(st.notes)
        return out

    def _segment_checks(self, s, cur, cv, th_B, th_c, th_c_face, face):
        p, st = self.params, self.st
        lam, th, pm = float(p["lam_nm"]), math.radians(p["theta_deg"]), p["pol"]
        G = T("Segment {seg:d}: {structure}", seg=s, structure=STRUCT_LABEL[st.kind])
        CONS = T("Segment {seg:d}: consistency (identities)", seg=s)

        def mixed(fs, fp_):  # value for the source's polarization from per-polarization values
            return fs if pm == "s" else fp_ if pm == "p" else 0.5 * (fs + fp_)

        Rc, Tc, Ac = (mixed(cur["s"][k], cur["p"][k]) for k in ("R", "T", "A"))
        tot = Rc + Tc + Ac
        self._check(f"sum{s}", T("R + T + A = 1 (A = 1 − R − T by definition)"), tot, 1.0, "", CONS, tol=1e-12,
                    ok=abs(tot - 1.0) <= 1e-12,
                    note=T("R = {R:.10g}, T = {T:.10g}, A = {A:.3g}; an identity: the engine's absorption is the "
                           "remainder", R=Rc, T=Tc, A=Ac))
        # energy: lossless structures conserve R + T; absorbing ones are passive, and their A is Joule heating
        if st.lossless:
            dev = max(float(np.max(np.abs(1.0 - cv[pre + "R" + q] - cv[pre + "T" + q])))
                      for pre in ("", "l") for q in ("s", "p"))
            self._check(f"energy{s}", T("Lossless: max |1 − R − T| over every computed angle and wavelength (s and p)"),
                        dev, 0.0, "", G, ok=dev < 1e-10,
                        note=T("the engine computes R and T separately, from r and t; their sum = 1 is the "
                               "conservation of energy"))
        else:
            amin = min(float(np.min(cv[pre + "A" + q])) for pre in ("", "l") for q in ("s", "p"))
            self._check(f"passive{s}", T("Passive medium: the smallest A over every computed point"), amin, None, "",
                        G, ok=amin >= -1e-12, note=T("absorption cannot be negative (κ ≥ 0)"))
            jlab = T("R + T + A = 1 for s, with A the Joule heat k₀ Im(n²)∫|E|²dz / (n₀ cos θ)")
            try:
                jl = thin_films.joule_absorption_s(st.ns, st.ds, lam, th)
            except ValueError as e:
                if code_of(e) != "film.too_many_nodes":
                    raise
                self._check(f"joule{s}", jlab, None, 1.0, "", G, info=True, note=_joule_skipped(e))
                jl = None
            if jl is not None:
                AJ = jl["A"]
                val = cur["s"]["R"] + cur["s"]["T"] + AJ
                self._check(f"joule{s}", jlab, val, 1.0, "", G, tol=JOULE_TOL, ok=abs(val - 1.0) <= JOULE_TOL,
                            note=T("A from the run's field |E|² = {AJ:.10g}; 1 − R − T from r, t = {A:.10g} "
                                   "(Poynting's theorem: an independent route); Gauss–Legendre quadrature, nodes: "
                                   "{nodes}, the step set by the skin depth and the period of the standing wave",
                                   AJ=AJ, A=cur["s"]["A"], nodes=jl["nodes"]))
        # Brewster: a single boundary
        if th_B is not None:
            ref = interfaces.brewster(st.n_in, st.n_out)
            self._check(f"brew{s}", T("Brewster's angle: the zero of r_p found by the run"), math.degrees(th_B),
                        math.degrees(ref), "°", G, tol=1e-9,
                        note=T("reference arctan(n_out/n₀) = arctan({nout}/{nin})", nout=st.n_out, nin=st.n_in))
            RpB = rta(face, lam, th_B, "p")["R"]
            self._check(f"brewR{s}", T("R_p at the Brewster angle found"), RpB, 0.0, "", G, ok=RpB < 1e-24,
                        note=T("p photons are not reflected there: of an unpolarised beam only s is reflected"))
        # critical angle and total reflection
        if th_c_face is not None:
            ref = interfaces.critical(st.n_in, float(p["ns"]))
            lab = (T("Critical angle of the face: the boundary beyond which the run's T for the face without the "
                     "second prism = 0")
                   if st.kind == "tir" and st.layers else
                   T("Critical angle: the boundary beyond which the run's T for the bare boundary n₀ → n_s = 0 (the "
                     "wave in the exit medium decays)"))
            self._check(f"crit{s}", lab, math.degrees(th_c_face), None if ref is None else math.degrees(ref), "°", G,
                        tol=1e-9, note=T("reference arcsin(n_s/n₀) = arcsin({ns}/{nin})", ns=float(p["ns"]),
                                         nin=st.n_in))
        if th_c is not None and st.lossless:
            beyond = list(np.linspace(math.degrees(th_c) + 1e-6, TH_MAX, 60))
            dev = max(abs(1.0 - rta(st, lam, math.radians(x), q)["R"]) for x in beyond for q in ("s", "p"))
            self._check(f"tir{s}", T("Beyond the critical angle R = 1: max |1 − R| (s and p, {n:d} angles from θ_c "
                                     "to {th}°)", n=60, th=TH_MAX), dev, 0.0,
                        "", G, ok=dev < 1e-12, note=T("lossless: whatever is not transmitted is reflected"))
            if th >= th_c:  # th_c is the first float angle at which the run's T = 0
                self._check(f"tirnow{s}", T("R at the current angle (it is beyond the critical one)"), Rc, 1.0, "", G,
                            tol=1e-12, ok=abs(Rc - 1.0) <= 1e-12)
                if not st.layers:
                    self._evan_check(s, G, lam, th)
        # quarter-wave antireflection
        if st.kind == "ar":
            nf, lam0 = float(p["ar_n"]), float(p["lam0_nm"])
            R0 = rta(st, lam0, 0.0, "s")["R"]
            ref = thin_films.quarter_wave_R(st.n_in, nf, st.n_out)
            ideal = math.sqrt(st.n_in * st.n_out)
            self._check(f"ar{s}", T("Anti-reflection λ/4: the run's R(λ₀, 0°)"), R0, ref, "", G,
                        ok=abs(R0 - ref) <= 1e-12, tol=1e-12,
                        note=T("reference ((n₀n_s − n_f²)/(n₀n_s + n_f²))²; = 0 at n_f = √(n₀ n_s) = {ideal:.8g} "
                               "(here n_f = {nf:.8g}); the bare boundary: {bare:.6g}", ideal=ideal, nf=nf,
                               bare=rta(face, lam0, 0.0, "s")["R"]))
        # Bragg mirror
        if st.kind == "bragg":
            nH, nL, N, lam0 = float(p["nH"]), float(p["nL"]), int(p["pairs"]), float(p["lam0_nm"])
            R0 = rta(st, lam0, 0.0, "s")["R"]
            ref = thin_films.quarter_wave_stack_R(st.n_in, nH, nL, st.n_out, N)
            self._check(f"bragg{s}", T("Bragg mirror: the run's R(λ₀, 0°)"), R0, ref, "", G, tol=1e-10,
                        note=T("reference for the order “medium, H, L, …, H, L, substrate”: "
                               "R = ((n₀n_L^(2N) − n_s n_H^(2N))/(n₀n_L^(2N) + n_s n_H^(2N)))²; N = {N:d}, "
                               "1 − R = {d:.4g}", N=N, d=1 - R0))
        # any single layer: the Airy sum of multiple reflections with complex Fresnel coefficients
        if len(st.layers) == 1:
            self._film_check(s, G, cur, lam, th)
        # Fabry-Perot film: the Airy intensity formula
        if st.kind == "fp":
            self._airy_checks(s, G, cv, lam, th, Tc)
        # frustrated total internal reflection
        if st.kind == "tir" and st.layers and th_c_face is not None and th > th_c_face:
            gap = st.layers[0][1]
            ref = mixed(*(thin_films.ftir_T(st.n_in, float(p["ns"]), gap, lam, th, q) for q in ("s", "p")))
            self._check(f"ftir{s}", T("Frustrated total reflection: the run's T (tunnelling through the gap)"), Tc,
                        ref, "", G, tol=1e-9,
                        note=T("reference 1/(1 + ((a² + b²)/(2ab))² sinh²(κd)): s: a = k_z, b = κ; p: a = k_z/n₀², "
                               "b = κ/n_s²"))

    def _stat_check(self, s):
        """All three outcomes against the Born probabilities of the segment (review 2026-10-23, V5-4: the reflected
        fraction alone let a swap of T and A pass): exact binomial tail of each outcome, Bonferroni over the
        outcomes, failure below the two-sided 5-sigma tail (bench.outcome_test)."""
        c = self.segc.get(s)
        if not c or c["n"] == 0:
            return
        n = c["n"]
        k = [c[x] for x in OUT_NAMES]
        pr = [c["p" + x] for x in OUT_NAMES]
        t = outcome_test(k, pr)
        parts = [T("{x}: {k:d} (expected {e:.1f}, z = {z:+.2f})", x=x, k=int(kx), e=px * n, z=zx)
                 if math.isfinite(zx) else
                 T("{x}: {k:d} (expected {e:.3g}: an impossible outcome)", x=x, k=int(kx), e=px * n)
                 for x, kx, px, zx in zip(OUT_NAMES, k, pr, t["z"])]
        self._check(f"stat{s}", T("Outcomes R, T, A (the run's event counts) against the Born probabilities: p-value"),
                    t["p"], None, "", T("Segment {seg:d}: photon statistics", seg=s), ok=t["p"] >= P_5SIGMA,
                    note=T("n = {k:d}; {parts}. The exact binomial tail of each outcome, Bonferroni correction "
                           "(outcomes: {m:d}); fails at p < {p5:.2g} (like 5σ); Pearson's χ² = {chi2:.3g} with "
                           "{dof:d} degrees of freedom (for information)", k=int(n), parts=join(parts), m=t["m"],
                           p5=P_5SIGMA, chi2=t["chi2"], dof=t["dof"]))

    # --- checks near the critical and grazing angles (review 2026-10-23, V5-2) --------------------------------
    def _evan_check(self, s, G, lam, th):
        """The decay length of the evanescent wave from the run's field against lambda / (2 pi sqrt(q)),
        q = n0^2 sin^2 theta - n_s^2 (thin_films, exact to one rounding).

        The run's number: |E|^2 at the face and at a depth z; first z = lambda/4, then z = the length so found, so that
        ln(I(0)/I(z)) ~ 2 (the logarithm of a ratio near 1 would lose digits). Its error to first order in u = 2^-53
        (README, "evan"): the engine's cos theta_t = sqrt(1 - x^2), x = n0 sin theta / n_s, carries 9u in x^2, i.e.
        9u K in 1 - x^2 (the subtraction itself is exact near x = 1), K = n0^2 sin^2 theta / q; the root halves it,
        and 2 pi, n_s, the product and lambda add <= 5u: the decay constant to (4.5 K + 5) u. Each |E|^2 value carries
        <= (11 + ln) u and their ratio and logarithm add 1u each: ln to (15 + ln) u absolutely; the division by ln
        and the reference add 3u. Tolerance (4.5 K + 9 + 15/ln) u. Where it exceeds 1e-2 the first-order bound no
        longer holds: the angle is within rounding of theta_c and fixes the decay length only to ~K u; the line is
        then shown for information."""
        st = self.st
        n0, n2 = st.n_in, st.n_out
        cid, lab = f"evan{s}", T("Evanescent wave: the decay length of the amplitude from the run's |E|²")
        q = thin_films.evanescent_q(n0, n2, th)
        K = 1.0 + n2 * n2 / q if q > 0 else math.inf
        L_run, ln, z = None, None, None
        I0, I1 = field(st, lam, th, [0.0, 0.25 * lam])
        if I0 > I1 > 0:
            z = 0.5 * lam / math.log(I0 / I1)  # the decay length from the first pair of depths
            if math.isfinite(z) and z > 0:
                I0, I2 = field(st, lam, th, [0.0, z])
                if I0 > I2 > 0:
                    ln = math.log(I0 / I2)
                    L_run = 2 * z / ln
        L_ref = _evanescent_ref(n0, n2, lam, th) if q > 0 else None
        tol = (4.5 * K + 9 + 15 / (ln if ln else 1.0)) * U if math.isfinite(K) else math.inf
        cond = T("the condition number K = n₀² sin²θ / (n₀² sin²θ − n_s²) = {K:.3g}", K=K) if math.isfinite(K) else \
            T("n₀ sin θ = n_s within rounding")
        if tol > 1e-2:
            self._check(cid, T("{label} (for information)", label=lab), L_run, L_ref, T("nm"), G, info=True,
                        note=T("θ differs from the critical angle by about a rounding: {cond}; the angle sets the decay "
                               "length only to ~K·2⁻⁵³ (the first-order error estimate does not apply here); {tail}",
                               cond=cond,
                               tail=T("the run's field does not decay beyond the face (the wave grazes along the face)")
                               if L_run is None else T("the length from the run's field is shown for information")))
            return
        if L_run is None:
            self._check(cid, lab, None, L_ref, T("nm"), G, ok=False, tol=tol,
                        note=T("the run's field does not decay beyond the face, while the reference gives a finite "
                               "length; {cond}", cond=cond))
            return
        rel = (L_run - L_ref) / L_ref
        self._check(cid, lab, L_run, L_ref, T("nm"), G, tol=tol, ok=abs(rel) <= tol,
                    note=T("from |E|² at the face and at the depth {z:.4g} nm (ln of the ratio = {ln:.3g}); reference "
                           "λ/(2π√(n₀² sin²θ − n_s²)), the radicand in 160-bit arithmetic; tolerance "
                           "(4.5K + 9 + 15/ln)·2⁻⁵³ from the round-off error estimate, {cond}", z=z, ln=ln, cond=cond))

    def _airy_checks(self, s, G, cv, lam, th, Tc):
        """Fabry-Perot film: the run's T at (lambda, theta) and over its spectrum against the Airy intensity formula
        (thin_films.airy, with the engine's Snell cosines and phase). Tolerance: the sum of the two routes'
        first-order rounding bounds (airy err_T, growing as 1/(1 - rho) just below grazing inside the film where
        F -> infinity; thin_films.stack_error_single_layer err_T). Where that exceeds 1e-9 the routes are also
        compared 1e-3 rad further from grazing (the formula needs a propagating wave in the film)."""
        st, p, pm = self.st, self.params, self.params["pol"]
        n1, d = float(p["fp_n"]), float(p["fp_d_nm"])
        pols = ("s", "p") if pm == "unpol" else (pm,)

        def at(a_, lam_):
            """{pol: (T of the formula, bound)} at angle a_ and wavelength lam_."""
            out = {}
            for q in ("s", "p"):
                A = thin_films.airy(st.n_in, n1, st.n_out, d, lam_, a_, q)
                M = thin_films.stack_error_single_layer(st.n_in, n1, st.n_out, d, lam_, a_, q)
                out[q] = (A["T"], A["err_T"] + M["err_T"], A)
            return out

        try:
            here = at(th, lam)
        except ValueError as e:
            self._check(f"airy{s}", T("Fabry–Pérot: the run's T and the Airy formula"), Tc, None, "", G,
                        note=T("the Airy formula in intensities does not apply here: {why}", why=_airy_reason(e)))
            return
        ref = sum(here[q][0] for q in pols) / len(pols)
        bound = sum(here[q][1] for q in pols) / len(pols)
        ok = abs(Tc - ref) <= bound
        q0 = pols[0]
        note = T("reference T = T_max/(1 + F sin²(Δ/2)), F = {F:.6g}, T_max = {Tmax:.6g} ({pol}); at n₀ = n_s this is "
                 "1/(1 + F sin²(δ/2)); Snell's cosines and the layer's phase are shared with the matrices; tolerance "
                 "|ΔT| ≤ {bound:.2g}: the sum of the round-off error estimates of both routes",
                 F=here[q0][2]["F"], Tmax=here[q0][2]["T_max"], pol=q0, bound=bound)
        side_th = th - 1e-3 if th > 1e-3 else None
        side = None
        if bound > 1e-9 and side_th is not None:
            try:
                side = at(side_th, lam)
            except ValueError:
                side = None
            if side is not None:
                Ts = sum(rta(st, lam, side_th, q)["T"] for q in pols) / len(pols)
                refs = sum(side[q][0] for q in pols) / len(pols)
                bs = sum(side[q][1] for q in pols) / len(pols)
                ok = ok and abs(Ts - refs) <= bs
                note = T("{note}; F is large (the wave in the film almost grazes): the routes were also compared at "
                         "θ − {d} rad: |ΔT| = {dT:.2g} with the tolerance {tol:.2g}", note=note, d=1e-3,
                         dT=abs(Ts - refs), tol=bs)
        self._check(f"airy{s}", T("Fabry–Pérot: the run's T(λ, θ)"), Tc, ref, "", G,
                    tol=bound / abs(ref) if ref else bound, ok=ok, note=note)
        # the whole spectrum at the current angle (the cosines do not depend on lambda: no dispersion)
        lg = cv["lam"]
        dev, tol, ok = 0.0, 0.0, True
        for q in pols:
            for x, Tr in zip(lg, cv["lT" + q]):
                A = thin_films.airy(st.n_in, n1, st.n_out, d, float(x), th, q)
                b = A["err_T"] + thin_films.stack_error_single_layer(st.n_in, n1, st.n_out, d, float(x), th, q)["err_T"]
                e = abs(A["T"] - Tr)
                dev, tol, ok = max(dev, e), max(tol, b), ok and e <= b
        note = T("wavelengths at the current angle: {k:d}; the tolerance at each point is the sum of the round-off "
                 "error estimates of both routes", k=len(lg))
        if tol > 1e-9 and side is not None:
            dev_s, tol_s = 0.0, 0.0
            for q in pols:
                for x in lg:
                    A = thin_films.airy(st.n_in, n1, st.n_out, d, float(x), side_th, q)
                    b = A["err_T"] + thin_films.stack_error_single_layer(st.n_in, n1, st.n_out, d, float(x), side_th,
                                                                         q)["err_T"]
                    e = abs(A["T"] - rta(st, float(x), side_th, q)["T"])
                    dev_s, tol_s, ok = max(dev_s, e), max(tol_s, b), ok and e <= b
            note = T("{note}; and at θ − {d} rad: max |ΔT| = {dT:.2g} with the tolerance up to {tol:.2g}", note=note,
                     d=1e-3, dT=dev_s, tol=tol_s)
        self._check(f"airymax{s}", T("Fabry–Pérot: max |T − T_Airy| over the whole computed spectrum"), dev, 0.0, "",
                    G, tol=tol, ok=ok, note=note)

    def _film_check(self, s, G, cur, lam, th):
        """One layer: r, t of the transfer matrices against the Airy sum (thin_films.single_film, with the engine's
        Snell cosines, so that the routes differ in the algebra only). Tolerance: the sum of the two routes'
        first-order rounding bounds (single_film err_r/err_t, growing as 1/|D| near grazing in the layer, D = 1 +
        r01 r12 e^{2i beta}; thin_films.stack_error_single_layer). At exact grazing (0/0) or where that tolerance
        exceeds 1e-9 the routes are also compared at theta -/+ 1e-3 rad, where the sum is well-conditioned."""
        st = self.st
        n1, d = st.layers[0][0], st.layers[0][1]

        def compare(a_):
            """(max |difference|, max bound, every difference within its own bound) over r, t and s, p."""
            rows = []
            for q in ("s", "p"):
                sf = thin_films.single_film(st.n_in, n1, st.n_out, d, lam, a_, q)
                mt = cur[q] if a_ == th else rta(st, lam, a_, q)
                mb = thin_films.stack_error_single_layer(st.n_in, n1, st.n_out, d, lam, a_, q)
                rows += [(abs(sf["r"] - mt["r"]), sf["err_r"] + mb["err_r"]),
                         (abs(sf["t"] - mt["t"]), sf["err_t"] + mb["err_t"])]
            return max(x for x, _ in rows), max(b for _, b in rows), all(x <= b for x, b in rows)

        try:
            here = compare(th)
        except ValueError:  # cos theta1 = 0 exactly: the Airy sum is 0/0 (the matrices are regular)
            here = None
        side = None
        if here is None or here[1] > 1e-9:
            side = [compare(a_) for a_ in (th - 1e-3, th + 1e-3)]
        ok = all(w[2] for w in ([here] if here else []) + (side or []))
        diff, tol = (here[0], here[1]) if here else (max(w[0] for w in side), max(w[1] for w in side))
        note = T("max |Δr|, |Δt| over s and p; the transfer matrices and the sum of reflections are different routes "
                 "(Snell's cosines shared); tolerance: the sum of the round-off error estimates of both routes, "
                 "{tol:.2g}", tol=tol)
        if here is None:
            note = T("{note}; the wave in the layer now grazes along the boundaries (cos θ₁ = 0): the sum of "
                     "reflections is 0/0 here (a removable singularity), so the comparison is at θ ∓ {d} rad",
                     note=note, d=1e-3)
        elif side:
            note = T("{note}; the denominator of the sum of reflections is small (the wave in the layer almost "
                     "grazes): the tolerance is large, so the routes were also compared at θ ∓ {d} rad: "
                     "|Δ| ≤ {dev:.2g} with the tolerance {tol:.2g}", note=note, d=1e-3,
                     dev=max(w[0] for w in side), tol=max(w[1] for w in side))
        self._check(f"film{s}", T("One layer: the run's r and t = the sum of multiple reflections (Airy, complex "
                                  "Fresnel coefficients)"), diff, 0.0, "", G, tol=tol, ok=ok, note=note)

    # --- the photon stream ----------------------------------------------------------------------------
    def max_step(self):
        return 2e4 / float(self.params["rate"])

    def _emissions(self, t_target):
        rate = float(self.params["rate"])
        out = []
        while self.t_next <= t_target:
            m = int(min(2e5, max(16, (t_target - self.t_next) * rate * 1.2 + 16)))
            gaps = self.rng.exponential(1.0 / rate, m)
            times = self.t_next + np.concatenate([[0.0], np.cumsum(gaps[:-1])])
            k = int(np.searchsorted(times, t_target, side="right"))
            out.append(times[:k])
            if k < m:
                self.t_next = float(times[k])
            else:
                self.t_next = float(times[-1] + gaps[-1])
        return np.concatenate(out) if out else np.zeros(0)

    def _emit_photons(self, te):
        k = len(te)
        pm = self.params["pol"]
        if pm == "s":
            pol = np.zeros(k, np.int8)
        elif pm == "p":
            pol = np.ones(k, np.int8)
        else:  # the 50/50 mixture: each photon is s or p
            pol = (self.rng.random(k) < 0.5).astype(np.int8)
        self.flight.add(pid=np.arange(self.pid, self.pid + k), te=te, ts=te + self.times["t_in"],
                        lam=np.full(k, float(self.params["lam_nm"])), pol=pol, sege=np.full(k, self.seg),
                        stage=np.zeros(k))
        self.pid += k
        self.tot["emitted"] += k

    def _probs(self, lam, pol):
        key = (float(lam), int(pol))
        if key not in self.cache:
            th = math.radians(self.params["theta_deg"])
            self.cache[key] = born_probs(rta(self.st, float(lam), th, "sp"[int(pol)]))
        return self.cache[key]

    def _at_structure(self, idx):
        """The photons reach the structure present now: the fate of each by the Born rule with its R, T, A."""
        a = self.flight.a
        lam, pol = a["lam"][idx], a["pol"][idx]
        R = np.empty(len(idx))
        Tr = np.empty(len(idx))
        for lv in np.unique(lam):
            for pv in np.unique(pol):
                m = (lam == lv) & (pol == pv)
                if m.any():
                    R[m], Tr[m], _ = self._probs(lv, pv)
        u = self.rng.random(len(idx))
        out = np.where(u < R, 0, np.where(u < R + Tr, 1, 2)).astype(np.int8)
        ts = a["ts"][idx]
        tR, tT = ts + self.times["t_R"], ts + self.times["t_T"]
        den = R + Tr
        with np.errstate(invalid="ignore", divide="ignore"):
            wR = np.where(den > 0, R / np.where(den > 0, den, 1.0), 0.0)
        a["out"][idx] = out
        a["seg"][idx] = np.where(a["sege"][idx] == self.seg, self.seg, -1)
        a["tR"][idx], a["tT"][idx] = tR, tT
        a["wR"][idx], a["wT"][idx] = wR, np.where(den > 0, 1.0 - wR, 0.0)
        a["tdet"][idx] = np.where(out == 0, tR, np.where(out == 1, tT, ts))
        a["stage"][idx] = 1

    def _reveal(self, done, t_target):
        a = self.flight.a
        ii = np.nonzero(done)[0]
        ii = ii[np.argsort(a["tdet"][ii], kind="stable")]
        out, seg = a["out"][ii], a["seg"][ii]
        for j, name in enumerate(OUT_NAMES):
            self.tot[name] += int(np.sum(out == j))
        self.tot["transitional"] += int(np.sum(seg < 0))
        by_seg = []
        for sv in np.unique(seg):
            m = seg == sv
            row = [int(np.sum(out[m] == j)) for j in range(3)]
            by_seg.append([int(sv)] + row)
            if sv >= 0:
                c = self.segc[int(sv)]
                c["n"] += int(m.sum())
                for j, name in enumerate(OUT_NAMES):
                    c[name] += row[j]
        # the exact counts of this step per segment (-1: transitional) and outcome go into the record; the individual
        # detections (for the view's flashes) are the last 256 of the step
        sh = ii[-256:]
        self._msg({"type": "clicks", "t": t_target, "n": int(len(ii)), "by_seg": by_seg, "shown": int(len(sh))},
                  {"t": a["tdet"][sh].astype(np.float64), "det": a["out"][sh].astype(np.uint8),
                   "pol": a["pol"][sh].astype(np.uint8), "seg": a["seg"][sh].astype(np.int32),
                   "te": a["te"][sh].astype(np.float64)})
        self.flight.keep(~done)

    def advance(self, t_target):
        te = self._emissions(t_target)
        if len(te):
            self._emit_photons(te)
        a = self.flight.a
        idx = np.nonzero((a["stage"] == 0) & (a["ts"] <= t_target))[0]
        if len(idx):
            self._at_structure(idx)
        a = self.flight.a
        done = (a["stage"] == 1) & (a["tdet"] <= t_target)
        if done.any():
            self._reveal(done, t_target)
        self.t = t_target
        c = self.segc[self.seg]
        if c["n"] >= self._stat_next:
            self._stat_check(self.seg)
            while self._stat_next <= c["n"]:
                self._stat_next = _next_step(self._stat_next)

    def next_event_time(self):
        """The next emission, the next arrival at the structure or at a detector."""
        a = self.flight.a
        cands = [self.t_next]
        m0, m1 = a["stage"] == 0, a["stage"] == 1
        if m0.any():
            cands.append(float(a["ts"][m0].min()))
        if m1.any():
            cands.append(float(a["tdet"][m1].min()))
        return min(cands)

    # --- frames -----------------------------------------------------------------------------------------
    def frame(self):
        """Photons under way as the viewer may know them at time t: on the way in, a progress along the incident
        arm; after the structure, not yet detected: the reflected and transmitted packets (weights R/(R+T), T/(R+T));
        once a detector's arrival time has passed without a click, that packet is gone (Lueders update)."""
        a = self.flight.a
        t = self.t
        n = len(self.flight)
        fl = np.zeros((n, 6))
        if n:
            st0 = a["stage"] == 0
            fl[:, 0] = a["stage"]
            fl[:, 1] = a["pol"]
            fl[st0, 2] = (t - a["te"][st0]) / np.maximum(a["ts"][st0] - a["te"][st0], 1e-300)
            s1 = ~st0
            ts, tR, tT = a["ts"][s1], a["tR"][s1], a["tT"][s1]
            wR, wT = a["wR"][s1].copy(), a["wT"][s1].copy()
            goneT = t >= tT  # the transmission detector stayed silent: only the reflected packet is left
            goneR = t >= tR
            wR[goneT & ~goneR & (wR > 0)] = 1.0
            wT[goneT] = 0.0
            wT[goneR & ~goneT & (wT > 0)] = 1.0
            wR[goneR] = 0.0
            fl[s1, 2] = (t - ts) / np.maximum(tR - ts, 1e-300)
            fl[s1, 3] = wR
            fl[s1, 4] = (t - ts) / np.maximum(tT - ts, 1e-300)
            fl[s1, 5] = wT
            if n > 400:
                fl = fl[np.linspace(0, n - 1, 400).astype(int)]
        c = self.segc[self.seg]
        cnt = {k: c[k] for k in ("n", "R", "T", "A")}
        exp = {k: c["p" + k] for k in OUT_NAMES}
        sig = {k: (math.sqrt(exp[k] * (1 - exp[k]) / c["n"]) if c["n"] else None) for k in OUT_NAMES}
        z = None
        if c["n"]:
            sR = math.sqrt(c["n"] * exp["R"] * (1 - exp["R"]))
            z = (c["R"] - c["n"] * exp["R"]) / sR if sR > 0 else (0.0 if c["R"] == round(c["n"] * exp["R"]) else None)
        return ({"seg": self.seg, "counts": cnt, "expected": exp, "sigma": sig, "z": z, "totals": dict(self.tot),
                 "in_flight": n}, {"fl": fl})

    def header(self):
        return {
            "title": self._title(),
            "text": T("The source emits photons one by one (a Poisson stream) onto a planar structure: a boundary "
                      "between two media, an anti-reflection layer, a Bragg mirror, a Fabry–Pérot film, a metal film "
                      "or a prism's face (total internal reflection; with a gap, tunnelling). For every set-up the "
                      "run computes, with the transfer matrices of the engine lfphys, the amplitudes r, t and the "
                      "probabilities R, T, A, the curves R(θ), T(θ), R(λ), T(λ) and the field |E|² inside the "
                      "structure. For every photon that reaches the structure, its fate is drawn by the Born rule "
                      "with these probabilities; we learn it when the photon reaches a detector (an absorbed one "
                      "vanishes in the structure). The counters are the accumulation of these events, next to the "
                      "run's expected values."),
            "modifications": SCHEMA.modifications(self.params),
            "actions": self._actions(),
            "arm_m": ARM_M, "t_in": self.times["t_in"], "rate": float(self.params["rate"]),
        }, {}


def _refine_min_rp(st, lam, lo_deg, hi_deg, start):
    """Bounded Brent minimisation of the run's R_p(theta) between two grid neighbours of the grid minimum."""
    from scipy.optimize import minimize_scalar
    f = lambda d: rta(st, lam, math.radians(d), "p")["R"]  # noqa: E731
    try:
        r = minimize_scalar(f, bounds=(lo_deg, hi_deg), method="bounded", options={"xatol": 1e-9})
    except (ValueError, ZeroDivisionError, FloatingPointError):
        return {}
    if not (math.isfinite(r.fun) and r.fun <= start["Rp"]):
        return {}
    return {"deg": float(r.x), "Rp": float(r.fun)}


def _next_step(x):
    e = 10 ** math.floor(math.log10(x) + 1e-12)
    m = round(x / e)
    for s in STAT_STEPS + (10,):
        if s > m:
            return s * e
    return 10 * e


def _same(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return math.isclose(float(a), float(b), rel_tol=1e-12, abs_tol=0.0)
    return a == b


def _val(p, v):
    """A parameter's value for a text: an option's label (a T) or the number itself (formatted by the viewer)."""
    if p.type == "select":
        return dict(p.options).get(v, v)
    return v


def _airy_reason(e):
    """Why the Airy intensity formula does not apply, from the machine code of the engine's ValueError
    (thin_films.airy / single_film; lfphys.codes, review 2026-11-12 i18n-code F5): never from its wording."""
    reason = _AIRY_REASONS.get(code_of(e))
    if reason is not None:
        return reason
    a = e.args[0] if e.args else None
    return a if is_t(a) else T("the engine's reason: {err}", err=str(e))


def _evanescent_ref(n0, n2, lam, th):
    """The engine's decay length, or None where the engine says the angle is below the critical one (a rounding
    neighbour of θ_c: film.below_critical)."""
    try:
        return thin_films.evanescent_length(n0, n2, lam, th)
    except ValueError as e:
        if code_of(e) == "film.below_critical":
            return None
        raise


def _joule_skipped(e):
    """The note of the Joule check when the engine refuses the quadrature (film.too_many_nodes)."""
    d = data_of(e)
    return T("not checked here: the Joule integral would need {n:d} quadrature nodes in one layer (the engine's limit "
             "is {lim:d})", n=int(d.get("n", 0)), lim=int(d.get("lim", 0)))


#: the world's own words for the engine's coded refusals of the Airy formula
_AIRY_REASONS = {
    "airy.total_reflection": T("total reflection at a boundary of the film (no propagating wave in it)"),
    "airy.grazing": T("the wave grazes inside the film (the formula is 0/0)"),
    "airy.lossy_index": T("the formula needs real positive indices (a lossless film)"),
}


VIZ = {
    "id": "v05_optics_bench",
    "title": T("Optical bench: boundaries and coatings"),
    "summary": T("Photons one by one at a boundary between two media, an anti-reflection layer, a Bragg mirror, a "
                 "Fabry–Pérot film, a metal film, a prism's face (total and frustrated total reflection). Brewster's "
                 "angle, the critical angle, the spectra R(λ), T(λ), the field |E|² in the layers."),
    "purpose": T("How reflection, transmission and absorption come out of Maxwell's equations at the boundaries "
                 "(transfer matrices), and how single photons add up to these fractions by the Born rule."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
