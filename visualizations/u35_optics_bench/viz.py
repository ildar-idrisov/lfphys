# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u35: the optical bench - single photons at a boundary between real media, at real coatings and at a thin metal
film, with analysers before the detectors and real single-photon detectors.

What the run computes (README.md of this folder has the model in full), all with the engine lfphys:
* the indices of real, dispersive materials at every wavelength (lfphys.core.optics.materials: the SCHOTT glasses,
  fused silica, MgF2, the MgF2, SiO2 and Ta2O5 films, gold, silver, aluminium), or a model medium of a given index;
* the structure's amplitudes r, t and powers R, T, A by the transfer matrices (lfphys.core.optics.interfaces.stack),
  the curves R(theta), T(theta) at the current wavelength and R(lambda), T(lambda) at the current angle;
* the reflection and transmission Jones matrices of the structure, the polarisation state (density matrix) of each
  outgoing beam and its ellipse, the analysers' ports (polarising beam splitters with k1, k2) and the Born
  probabilities of a photon's five outcomes (lfphys.core.optics.polarization);
* the field |E|^2 of the source's polarisation state through the structure (interfaces.field_intensity);
* the stream of single photons: each photon's wavelength drawn from the source's line, its outcome drawn by the Born
  rule on its density matrix when it reaches the structure, its arrival at a detector after the flight at the group
  velocity and the structure's group delay (interfaces.group_delay), revealed there; each detector clicks with its
  efficiency, adds dark counts and loses counts to its dead time (lfphys.theories.models.photodetector);
* checks against closed forms (lfphys.core.optics.thin_films, polarization, photodetector): Brewster, critical angle and
  R = 1 beyond it, the evanescent decay length, the total reflection's phase difference, the quarter-wave
  antireflection layer, the Bragg mirror, the Airy formula, frustrated total reflection, Joule heating for s and p,
  Malus's law, the degree of polarisation of the reflected light, the photon statistics and the detectors' counts.
"""

from __future__ import annotations

import math

import numpy as np
from lfviz.errors import Refusal
from lfviz.sim import Simulation as BaseSimulation

from lfphys.codes import code_of, data_of
from lfphys.core.optics import interfaces, materials, polarization as pol_, thin_films
from lfphys.i18n import T, is_t, join
from lfphys.theories.models import photodetector as pd

from .engine.bench import (ARM_M, DARK_CODE, DETECTORS, GLASSES, MATERIAL_NAME, MEDIA, P_5SIGMA, POL_CODE, POL_LABEL,
                           SHORT, STRUCT_LABEL, STRUCTS, TH_MAX, DetectorState, Stream, Structure, analyser,
                           binom_two_sided, brewster_from_rp, build_structure, critical_from_T, curves, detector_of,
                           field, field_grid, flight_times, lam_range, line_comb, materials_of, medium_index,
                           outcome_probs, outcome_test, poisson_two_sided, ray_angles, rng_for, rta, source_state)

U = 2.0 ** -53  # unit round-off of binary64 (the derived tolerances of the evan and film checks)


from .schema import (BENCH_RATE, DET_DEFAULT, G_DEV, G_MED, G_SRC, G_STR, HENE, IMPERFECT,  # noqa: E402,F401
                     SCHEMA)


# what a live change touches (owner, 2026-10-23: the set-up changes at once, as in a laboratory)
PATH_FIELDS = ("med_in", "med_out", "n0", "ns", "theta_deg")  # the beam paths (media, goniometer): photons lost
SOURCE_FIELDS = ("lam_nm", "dlam_nm", "pol", "psi_deg", "rate", "shutter")  # new photons only
STAT_STEPS = (1, 2, 5)
# joule: the Gauss-Legendre remainder is < 1e-25 (thin_films._layer_nodes); what is left is the float rounding of
# |E|^2 and of R + T, <= 1.5e-14 over 3000 random absorbing films in the ranges of this bench
JOULE_TOL = 1e-12
OUT5 = pol_.OUTCOMES  # R_pass, R_reject, T_pass, T_reject, A
SHOWN = 8  # the events of a step sent one by one per detector (the view's flashes); the counts are exact anyway
DET_NAMES = ("Rp", "Rr", "Tp", "Tr")

MEASURABLES = [
    {"id": "t_c", "label": T("Counting time"), "unit": "s"},
    {"id": "n_R", "label": T("Clicks of the reflection detectors"), "unit": ""},
    {"id": "n_T", "label": T("Clicks of the transmission detectors"), "unit": ""},
    {"id": "n_Rp", "label": T("Reflection arm: clicks at the analyser's pass port"), "unit": ""},
    {"id": "n_Rr", "label": T("Reflection arm: clicks at the analyser's reject port"), "unit": ""},
    {"id": "n_Tp", "label": T("Transmission arm: clicks at the analyser's pass port"), "unit": ""},
    {"id": "n_Tr", "label": T("Transmission arm: clicks at the analyser's reject port"), "unit": ""},
    {"id": "n_clicks", "label": T("Clicks of all detectors"), "unit": ""},
    {"id": "n_emit", "label": T("Photons emitted"), "unit": ""},
    {"id": "n_A", "label": T("Photons absorbed in the structure (known in the simulation)"), "unit": ""},
    {"id": "n_dark", "label": T("Dark counts among the clicks (known in the simulation)"), "unit": ""},
    {"id": "R_frac", "label": T("Reflected fraction"), "unit": "", "sigma": "R_frac_se",
     "ref": "R_frac_ref", "ref_label": T("computed R/(R + T)")},
    {"id": "R_frac_se", "label": T("Binomial error of the reflected fraction"), "unit": ""},
    {"id": "R_frac_ref", "label": T("Computed R/(R + T) of the source's light"), "unit": ""},
    {"id": "T_frac", "label": T("Transmitted fraction"), "unit": "", "sigma": "T_frac_se",
     "ref": "T_frac_ref", "ref_label": T("computed T/(R + T)")},
    {"id": "T_frac_se", "label": T("Binomial error of the transmitted fraction"), "unit": ""},
    {"id": "T_frac_ref", "label": T("Computed T/(R + T) of the source's light"), "unit": ""},
    {"id": "fR_pass", "label": T("Reflected: share through the analyser"), "unit": "", "sigma": "fR_pass_se",
     "ref": "fR_pass_ref", "ref_label": T("computed")},
    {"id": "fR_pass_se", "label": T("Binomial error of the reflection analyser's fraction"), "unit": ""},
    {"id": "fR_pass_ref", "label": T("Computed fraction through the reflection analyser"), "unit": ""},
    {"id": "fT_pass", "label": T("Transmitted: share through the analyser"), "unit": "", "sigma": "fT_pass_se",
     "ref": "fT_pass_ref", "ref_label": T("computed")},
    {"id": "fT_pass_se", "label": T("Binomial error of the transmission analyser's fraction"), "unit": ""},
    {"id": "fT_pass_ref", "label": T("Computed fraction through the transmission analyser"), "unit": ""},
]


class Simulation(BaseSimulation):
    speed_range = (1e-15, 1e3)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = dict(params)
        self.rng = rng_for(seed, self.params)  # an independent sample per set-up (bench.rng_for)
        self._buf = []
        self.seg = -1
        self.st = build_structure(self.params)
        self.flight = Stream()
        self.pid = 0
        self.t_next = float(self.rng.exponential(1.0 / self.params["rate"]))
        self.tot = dict(emitted=0, R=0, T=0, A=0, lost=0, transitional=0, missed=0, dark=0, clicks=0)
        self.segc: dict[int, dict] = {}
        self.dets = self._detectors(self.params)
        self.gated = False
        try:
            self._new_segment(T("start"))
        except ValueError:
            raise
        except Exception as e:  # reported as a refused world (the runner catches ValueError), never a crash
            err = f"{type(e).__name__}: {e}"
            raise Refusal(T("internal error of the world: {err}", err=type(e).__name__), detail=err) from e
        self.default_speed = self.times["t_in"] / 1.2  # one arm in about 1.2 s of wall time

    def _detectors(self, p, old=None):
        """The four detector places (reflection pass/reject, transmission pass/reject): a DetectorState where a
        detector stands (the pass place always, the reject place behind an analyser), None elsewhere. A detector kept
        from before keeps its dead-time state."""
        det = detector_of(p)
        out = []
        for k, (arm, port) in enumerate((("R", 0), ("R", 1), ("T", 0), ("T", 1))):
            here = port == 0 or p["ana" + arm] != "out"
            if not here:
                out.append(None)
            elif old is not None and old[k] is not None and old[k].d == det:
                out.append(old[k])
            else:
                out.append(DetectorState(det, self.rng, self.t))
        return out

    def engine_modules(self):
        return ["core.optics.interfaces", "core.optics.thin_films", "core.optics.polarization",
                "core.optics.materials", "core.constants", "theories.models.photodetector",
                "theories.approx.ray_optics"]

    @classmethod
    def check_params(cls, params):
        """Refuse a wavelength outside a material's data (``materials``: a coded refusal there too)."""
        lo, hi = lam_range(params)
        lam, w = float(params["lam_nm"]), float(params["dlam_nm"])
        span = 4.0 * w * pd.FWHM_TO_SIGMA
        if not (lo <= lam - span and lam + span <= hi):
            mats = ", ".join(SHORT.get(m, m) for m in materials_of(params))
            raise Refusal(T("λ = {lam} nm (with the line's width) lies outside the measured data of {mats}: "
                            "{lo}–{hi} nm", lam=lam, mats=mats, lo=lo, hi=hi),
                          T("choose a wavelength inside the materials' range"))
        if params["structure"] in ("ar", "bragg"):
            l0 = float(params["lam0_nm"])
            if not lo <= l0 <= hi:
                raise Refusal(T("the design wavelength λ₀ = {lam} nm lies outside the materials' data {lo}–{hi} nm",
                                lam=l0, lo=lo, hi=hi), T("choose λ₀ inside the materials' range"))
        if params["anaR"] == "real" or params["anaT"] == "real":
            k1, k2 = float(params["ana_k1"]), float(params["ana_k2"])
            if not 0.0 <= k2 <= k1 <= 1.0:
                raise Refusal(T("an analyser needs 0 ≤ k₂ ≤ k₁ ≤ 1 (k₁ = {k1}, k₂ = {k2})", k1=k1, k2=k2),
                              T("make k₂ the smaller one"))

    # --- the computed values of the lab's bench (design §3.4; «Computed for this bench») ------------------------------
    @classmethod
    def lab_reference(cls, step_id, fixed, values, reference):
        lam = float(fixed.get("lam_nm", HENE))
        glass = {"bk7": "schott_n_bk7", "f2": "schott_n_f2", "sf11": "schott_n_sf11"}

        def n_of(g):
            return float(materials.index(glass[g], lam).real)

        def name(g):
            return SHORT[glass[g]]
        if step_id == "dark":
            det = detector_of(fixed)
            return {"value": det.dark_rate, "unit": T("s⁻¹"), "label": T("the dark-count rate of each detector"),
                    "how": T("the detector model's value: {title}", title=pd.DEVICES[fixed["det"]]["title"]
                             if fixed["det"] in pd.DEVICES else T("ideal")),
                    "kind": "engine"}
        if step_id == "fresnel":
            kind, _, g = reference.partition("_")
            if g not in glass:
                raise ValueError(T("no law for the step {step}", step=step_id))
            n = n_of(g)
            how = T("SCHOTT's Sellmeier formula: n = {n:.6g}", n=n)
            if kind == "ns2":
                return {"value": n * n, "unit": "", "label": T("{glass}: y_s = n² − sin²θ, the intercept n²",
                                                              glass=name(g)), "how": how, "kind": "closed form"}
            if kind == "ys1":
                return {"value": -1.0, "unit": "", "label": T("y_s = n² − sin²θ: the slope −1 (any glass)"),
                        "how": T("closed form of Fresnel's s reflection from air"), "kind": "closed form"}
            if kind == "inv2":
                return {"value": 1.0 / (n * n), "unit": "", "label": T("{glass}: the intercept 1/n² of y_p (below θ_B)",
                                                                   glass=name(g)),
                        "how": how, "kind": "closed form"}
            if kind == "inv4":
                return {"value": -1.0 / n ** 4, "unit": "", "label": T("{glass}: y_p below θ_B, the slope −1/n⁴",
                                                                       glass=name(g)), "how": how,
                        "kind": "closed form"}
            if kind == "thb":
                return {"value": math.degrees(interfaces.brewster(1.0, n)), "unit": "°",
                        "label": T("{glass}: Brewster's angle θ_B = arctan n, where R_p = 0", glass=name(g)),
                        "how": how, "kind": "closed form"}
        if step_id == "malus":
            k1, k2 = (1.0, 0.0) if reference.endswith("ideal") else IMPERFECT
            if reference.startswith("slope0"):
                return {"value": k1, "unit": "", "label": T("ideal analyser: I = cos²(α − ψ), the slope 1"),
                        "how": T("Malus's law (lfphys polarization.malus)"), "kind": "closed form"}
            if reference.startswith("slope"):
                return {"value": k1 - k2, "unit": "",
                        "label": T("imperfect analyser: I = k₂ + (k₁ − k₂) cos²(α − ψ), the slope k₁ − k₂"),
                        "how": T("Malus's law for a partial polariser, k₁ = {k1}, k₂ = {k2}", k1=k1, k2=k2),
                        "kind": "closed form"}
            if reference.startswith("icept"):
                return {"value": k2, "unit": "", "label": T("imperfect analyser: the intercept k₂"),
                        "how": T("Malus's law for a partial polariser, k₁ = {k1}, k₂ = {k2}", k1=k1, k2=k2),
                        "kind": "closed form"}
        if step_id == "reflection":
            g = reference.partition("_")[2]
            if g in glass:
                n = n_of(g)
                return {"value": math.degrees(interfaces.brewster(1.0, n)), "unit": "°",
                        "label": T("{glass}: the analyser along p passes nothing at θ_B = arctan n",
                                   glass=name(g)),
                        "how": T("SCHOTT's Sellmeier formula: n = {n:.6g}", n=n), "kind": "closed form"}
        raise ValueError(T("no law for the step {step}", step=step_id))

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
        photons in flight, counters, segments, detectors, the random generator) is restored and nothing is emitted.
        Any exception becomes a ValueError, which the runner reports as a refused change, followed by the live values
        in force (the player rolls its control back)."""
        snap = {k: (v.copy() if isinstance(v, (dict, list)) else v) for k, v in self.__dict__.items()}
        det_snap = [None if d is None else (d.last, d.t) for d in self.dets]
        flight, flight_cols = self.flight, dict(self.flight.a)  # Stream.add/keep replace its columns, never edit them
        rng_state = self.rng.bit_generator.state
        outer = self._buf
        self._buf = []
        try:
            out = fn(*args)
        except Exception as e:
            self.__dict__.clear()
            self.__dict__.update(snap)
            for d, s in zip(self.dets, det_snap):
                if d is not None:
                    d.last, d.t = s
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
        type(self).check_params(new)
        st = build_structure(new)  # raises on a bad set-up; nothing of the world is touched before this point
        desc = join([T("{label}: {old} → {new}", label=SCHEMA.by_id[k].label,
                        old=_val(SCHEMA.by_id[k], self.params[k]), new=_val(SCHEMA.by_id[k], new[k]))
                      for k in changed])
        notes = []
        path = any(k in PATH_FIELDS for k in changed) or st.n_out != self.st.n_out or st.n_in != self.st.n_in
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
        self.dets = self._detectors(new, self.dets)
        if "rate" in changed or "shutter" in changed:
            self.t_next = self.t + float(self.rng.exponential(1.0 / new["rate"]))
        if "gate_s" in changed:
            self.gated = self._gate() is not None and self.t >= self._gate()
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

    def _gate(self):
        g = float(self.params["gate_s"])
        return g if g > 0 else None

    # --- one segment: the run's own numbers for the current set-up ------------------------------------------
    def _title(self):
        return T("Optical bench: {structure}", structure=STRUCT_LABEL[self.st.kind])

    def _new_segment(self, reason):
        if self.seg >= 0:
            self._stat_check(self.seg)
        self.seg += 1
        s = self.seg
        p, st = self.params, self.st
        lam, th, pm = float(p["lam_nm"]), math.radians(p["theta_deg"]), p["pol"]
        rho = source_state(p)
        self.rho = rho
        aR, aT = analyser(p, "R"), analyser(p, "T")
        # the source's line: a comb of wavelengths, each with its own structure (dispersion) and Born probabilities
        lams, wts = line_comb(lam, float(p["dlam_nm"]))
        table = []
        for x in lams:
            sx = st if x == lam else build_structure(p, x)
            table.append([outcome_probs(sx, th, rho, aR, aT)["probs"][k] for k in OUT5])
        self.comb = (lams, wts, np.array(table))
        here = outcome_probs(st, th, rho, aR, aT)
        P = here["probs"]
        pexp = [float(v) for v in wts @ np.array(table)]  # the line-averaged Born probabilities of the five outcomes
        self.times = flight_times(st, th, rho)
        cur = {q: rta(st, lam, th, q) for q in ("s", "p")}
        self.segc[s] = {"n": 0, "fate": [0] * 5, "probs": pexp, "arr": [0] * 4, "det_in": [0] * 4, "dark": [0] * 4,
                        "rec": [0] * 4, "clk": [0] * 4, "clk_dark": [0] * 4, "nA": 0, "emit": 0, "t0": self.t,
                        "tdark": [0.0] * 4, "P": dict(P)}
        self._stat_next = 20
        # angles found by the run from its own transfer matrices. The exit wave becomes evanescent where T of the bare
        # boundary n_in -> n_out vanishes: n sin(theta) is the same in every layer, so the layers do not move this
        # angle, while T of a thick structure can underflow to exactly 0 long before it (an evanescent thick film)
        n_s = medium_index(p["med_out"], p["ns"], lam)
        self.n_s = n_s
        none = st.kind == "none"
        th_c = None if none else critical_from_T(Structure("interface", st.n_in, st.n_out), lam)
        face = Structure("interface", st.n_in, n_s)
        th_c_face = (critical_from_T(face, lam) if st.kind == "tir" and st.layers else th_c) if not none else None
        single = not st.layers and not none
        th_B = brewster_from_rp(st.n_in, st.n_out, lam, th_c) if single else None
        deg = lambda x: None if x is None else math.degrees(x)  # noqa: E731
        # the curves' grids hold the structure's own angles and design wavelength but not the set-up's θ and λ: the
        # curves of one sample (or one coating) are then the same bytes at every θ (λ) and an atlas's pool keeps them
        # once (design §5 F10); the set-up's own R, T are in the segment's "cur"
        extra_lam = [float(p["lam0_nm"])] if st.kind in ("ar", "bragg") else []
        cv, m_spec, self._spec_lossless = curves(p, st, lam, th, rho, [deg(th_c), deg(th_c_face), deg(th_B)],
                                                 extra_lam)
        min_rp = None
        if st.layers:  # the minimum of R_p of the run (a multilayer has no Brewster closed form): grid, then Brent
            i = int(np.argmin(cv["Rp"]))
            if 0 < i < len(cv["th"]) - 1:
                min_rp = {"deg": float(cv["th"][i]), "Rp": float(cv["Rp"][i])}
                min_rp.update(_refine_min_rp(st, lam, float(cv["th"][i - 1]), float(cv["th"][i + 1]), min_rp))
        z = field_grid(st, lam)
        E2 = field(st, lam, th, z, rho)
        angles = ray_angles(st, th)
        mix = {k: float(np.real(rho[0, 0]) * cur["p"][k] + np.real(rho[1, 1]) * cur["s"][k]) for k in ("R", "T", "A")}
        curd = {"s": {k: cur["s"][k] for k in ("R", "T", "A")}, "p": {k: cur["p"][k] for k in ("R", "T", "A")},
                "mix": mix}
        det = detector_of(p)
        ell = {arm: _ellipse(here["rho_" + arm]) for arm in ("R", "T")}
        setup = {"title": self._title(), "kind": st.kind, "label": STRUCT_LABEL[st.kind], "n_in": st.n_in,
                 "n_out": st.n_out, "n_s": n_s, "out_name": st.out_name, "layers": st.describe(),
                 "thickness": st.thickness, "lam": lam, "dlam": float(p["dlam_nm"]), "comb": len(lams),
                 "lam0": float(p["lam0_nm"]) if st.kind in ("ar", "bragg") else None,
                 "theta": float(p["theta_deg"]), "pol": pm, "pol_label": POL_LABEL[pm],
                 "psi": float(p["psi_deg"]) if pm == "lin" else (90.0 if pm == "s" else 0.0 if pm == "p" else None),
                 "rate": float(p["rate"]), "shutter": p["shutter"], "lossless": st.lossless,
                 "med_in": p["med_in"], "med_out": p["med_out"], "med_in_name": _medium_name(p["med_in"], st.n_in),
                 "med_out_name": _medium_name(st.med_out, st.n_out), "materials": materials_of(p),
                 "ana": {arm: _ana_dict(analyser(p, arm), p["ana" + arm]) for arm in ("R", "T")},
                 "det": {"id": p["det"], "eta": det.eta, "dark": det.dark_rate, "dead": det.dead_time,
                         "jitter": det.jitter_sigma, "title": dict(DETECTORS)[p["det"]]},
                 "gate": self._gate(), **{k: v for k, v in self.times.items() if k != "tau"}}
        approx = self._approximations(m_spec)
        blobs = {k: np.asarray(v, np.float64) for k, v in cv.items()}
        blobs["z"] = np.asarray(z, np.float64)
        blobs["E2"] = np.asarray(E2, np.float64)
        blobs.update(_analyser_curves(here, aR, aT))
        self._msg({"type": "segment", "t": self.t, "seg": s, "reason": reason, "setup": setup, "angles": angles,
                   "cur": curd, "P": {k: float(P[k]) for k in OUT5}, "expected": dict(zip(OUT5, pexp)),
                   "arms": {"R": float(P["P_R"]), "T": float(P["P_T"]), "A": float(P["P_A"])}, "ell": ell,
                   "theta_B": None if th_B is None else {"deg": deg(th_B), "Rp": rta(face, lam, th_B, "p")["R"]},
                   "min_rp": min_rp, "theta_c": deg(th_c), "theta_c_face": deg(th_c_face), "approx": approx},
                  blobs)
        self._segment_checks(s, cur, cv, th_B, th_c, th_c_face, face, here, aR, aT)
        if s > 0:
            self._msg({"type": "actions", "t": self.t, "actions": self._actions()})

    def _approximations(self, m_spec):
        st, p = self.st, self.params
        out = [T("Plane waves and infinite plane boundaries; homogeneous, isotropic, linear media. The indices are "
                 "those of real materials at each photon's wavelength (lfphys materials: SCHOTT's data sheets, "
                 "Dodge, Malitson, Gao et al., Rodríguez-de Marcos et al., Johnson and Christy, Rakić); a model "
                 "medium has one given index for every λ."),
               T("The glasses are taken by the real part of their index: their κ (at most 4·10⁻⁸ at the visible lines) "
                 "changes R and T at the boundary by less than 10⁻¹⁵. Their absorption along a path in the glass is "
                 "not modelled: the media are half-spaces and the detectors stand in them (0.30 m of N-BK7 would "
                 "absorb 7 % at 632.8 nm, of N-SF11 21 %)."),
               T("Photons one by one: each photon's wavelength is drawn from the source's line (a Gaussian sampled by "
                 "{k:d} wavelengths over ±4σ) and its outcome by the Born rule on its density matrix, with the "
                 "probabilities computed in this run for its wavelength, the angle and the analysers.", k=33),
               T("The flight along the arms ({arm:.3g} cm) is at the group velocity c/n_g of each medium; the "
                 "structure adds its group delays of reflection and transmission (femtoseconds; for light with both s "
                 "and p, the intensity-weighted mean of their delays).", arm=ARM_M * 100),
               T("The detectors: efficiency, Poisson dark counts, a non-paralysable dead time and Gaussian jitter "
                 "(lfphys photodetector). Not modelled: afterpulsing (0.5 % of the counts by the data sheet), the "
                 "efficiency's dependence on the count rate and on the wavelength (η is the sheet's value at 650 nm; "
                 "about 0.68 at 632.8 nm), the timing response's slow tail."),
               T("An analyser is a linear partial polariser without retardance, given by k₁ and k₂ (lfphys "
                 "polarization); its ports' operators are exact for a lossless polarising beam splitter."),
               T("The rays in the diagram are geometrical optics (Snell's law), approximate; in an absorbing layer, by "
                 "the real part of the index. The structure is drawn to scale, the arms are not.")]
        if m_spec >= 1600:
            out.append(T("The multilayer's spectrum is very dense: {n:d} points may not resolve every band at short "
                         "wavelengths.", n=1600))
        if p["pol"] == "unpol":
            out.append(T("An unpolarised source is the density matrix ρ = I/2: its photons carry no s or p label "
                         "(drawn grey); an isotropic planar structure does not mix s and p, so the outcomes' "
                         "probabilities are those of ρ."))
        out.extend(st.notes)
        return out

    def _segment_checks(self, s, cur, cv, th_B, th_c, th_c_face, face, here, aR, aT):
        p, st = self.params, self.st
        lam, th = float(p["lam_nm"]), math.radians(p["theta_deg"])
        rho = self.rho
        wp, ws = float(np.real(rho[0, 0])), float(np.real(rho[1, 1]))
        G = T("Segment {seg:d}: {structure}", seg=s, structure=STRUCT_LABEL[st.kind])
        CONS = T("Segment {seg:d}: consistency (identities)", seg=s)
        POLG = T("Segment {seg:d}: polarisation", seg=s)

        def mixed(fs, fp_):  # value for the source's state from per-polarization values (no s-p cross term)
            return ws * fs + wp * fp_

        Rc, Tc, Ac = (mixed(cur["s"][k], cur["p"][k]) for k in ("R", "T", "A"))
        tot = Rc + Tc + Ac
        self._check(f"sum{s}", T("R + T + A = 1 (A = 1 − R − T by definition)"), tot, 1.0, "", CONS, tol=1e-12,
                    ok=abs(tot - 1.0) <= 1e-12,
                    note=T("R = {R:.10g}, T = {T:.10g}, A = {A:.3g}; an identity: the engine's absorption is the "
                           "remainder", R=Rc, T=Tc, A=Ac))
        P = here["probs"]
        s5 = sum(P[k] for k in OUT5)
        self._check(f"born{s}", T("The five outcomes' Born probabilities add to 1 (tr ρ)"), s5, 1.0, "", CONS,
                    tol=1e-12, ok=abs(s5 - 1.0) <= 1e-12,
                    note=T("reflected and passed {a:.6g}, reflected and rejected {b:.6g}, transmitted and passed "
                           "{c:.6g}, transmitted and rejected {d:.6g}, absorbed {e:.3g}", a=P["R_pass"],
                           b=P["R_reject"], c=P["T_pass"], d=P["T_reject"], e=P["A"]))
        dR = abs(P["P_R"] - Rc) + abs(P["P_T"] - Tc)
        self._check(f"arms{s}", T("The arms' probabilities from the density matrices = R and T of the transfer "
                                  "matrices"), dR, 0.0, "", CONS, tol=1e-12, ok=dR <= 1e-12,
                    note=T("tr(M_R ρ M_R†) and tr(M_T ρ M_T†) against ρ_pp R_p + ρ_ss R_s and ρ_pp T_p + ρ_ss T_s: "
                           "two routes through the engine"))
        # energy: lossless structures conserve R + T; absorbing ones are passive, and their A is Joule heating. Each
        # wavelength of the spectrum is lossless or not on its own (a film's data may absorb in the ultraviolet only)
        ll = np.asarray(self._spec_lossless, bool)
        dev_parts = []
        for q in ("s", "p"):
            if st.lossless:
                dev_parts.append(float(np.max(np.abs(1.0 - cv["R" + q] - cv["T" + q]))))
            if ll.any():
                dev_parts.append(float(np.max(np.abs(1.0 - cv["lR" + q][ll] - cv["lT" + q][ll]))))
        if dev_parts:
            dev = max(dev_parts)
            self._check(f"energy{s}", T("Lossless: max |1 − R − T| over every computed angle and wavelength (s and p)"),
                        dev, 0.0, "", G, ok=dev < 1e-10,
                        note=T("the engine computes R and T separately, from r and t; their sum = 1 is the "
                               "conservation of energy (at the wavelengths where every material is lossless: {k:d} of "
                               "{n:d})", k=int(ll.sum()), n=len(ll)))
        if not st.lossless or not ll.all():
            vals = []
            for q in ("s", "p"):
                if not st.lossless:
                    vals.append(float(np.min(cv["A" + q])))
                if (~ll).any():
                    vals.append(float(np.min(cv["lA" + q][~ll])))
            amin = min(vals)
            self._check(f"passive{s}", T("Passive medium: the smallest A over every computed point"), amin, None, "",
                        G, ok=amin >= -1e-12, note=T("absorption cannot be negative (κ ≥ 0)"))
        if not st.lossless:
            for q, fn, cid in (("s", thin_films.joule_absorption_s, "joule"), ("p", thin_films.joule_absorption_p,
                                                                              "joulep")):
                jlab = (T("R + T + A = 1 for s, with A the Joule heat k₀ Im(n²)∫|E|²dz / (n₀ cos θ)") if q == "s" else
                        T("R + T + A = 1 for p, with A the Joule heat of the p field (E_x and E_z)"))
                try:
                    jl = fn(st.ns, st.ds, lam, th)
                except ValueError as e:
                    if code_of(e) != "film.too_many_nodes":
                        raise
                    self._check(f"{cid}{s}", jlab, None, 1.0, "", G, info=True, note=_joule_skipped(e))
                    continue
                AJ = jl["A"]
                val = cur[q]["R"] + cur[q]["T"] + AJ
                self._check(f"{cid}{s}", jlab, val, 1.0, "", G, tol=JOULE_TOL, ok=abs(val - 1.0) <= JOULE_TOL,
                            note=T("A from the run's field |E|² = {AJ:.10g}; 1 − R − T from r, t = {A:.10g} "
                                   "(Poynting's theorem: an independent route); Gauss–Legendre quadrature, nodes: "
                                   "{nodes}, the step set by the skin depth and the period of the standing wave",
                                   AJ=AJ, A=cur[q]["A"], nodes=jl["nodes"]))
        if st.kind == "none":
            dev = abs(cur["s"]["R"]) + abs(cur["p"]["R"]) + abs(1 - cur["s"]["T"]) + abs(1 - cur["p"]["T"])
            self._check(f"none{s}", T("No boundary: R = 0 and T = 1 exactly"), dev, 0.0, "", G, tol=1e-15,
                        ok=dev <= 1e-15, note=T("the same medium on both sides: no reflection"))
        # Brewster: a single boundary
        if th_B is not None:
            ref = interfaces.brewster(st.n_in, st.n_out)
            self._check(f"brew{s}", T("Brewster's angle: the zero of r_p found by the run"), math.degrees(th_B),
                        math.degrees(ref), "°", G, tol=1e-9,
                        note=T("reference arctan(n_out/n₀) = arctan({nout}/{nin})", nout=st.n_out, nin=st.n_in))
            RpB = rta(face, lam, th_B, "p")["R"]
            self._check(f"brewR{s}", T("R_p at the Brewster angle found"), RpB, 0.0, "", G, ok=RpB < 1e-24,
                        note=T("p light is not reflected there: unpolarised light comes back pure s"))
        # critical angle and total reflection
        if th_c_face is not None:
            ref = interfaces.critical(st.n_in, self.n_s)
            lab = (T("Critical angle of the face: the boundary beyond which the run's T for the face without the "
                     "second prism = 0")
                   if st.kind == "tir" and st.layers else
                   T("Critical angle: the boundary beyond which the run's T for the bare boundary n₀ → n_s = 0 (the "
                     "wave in the exit medium decays)"))
            self._check(f"crit{s}", lab, math.degrees(th_c_face), None if ref is None else math.degrees(ref), "°", G,
                        tol=1e-9, note=T("reference arcsin(n_s/n₀) = arcsin({ns}/{nin})", ns=self.n_s, nin=st.n_in))
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
                    self._tir_phase_check(s, POLG, here, th)
        # quarter-wave antireflection
        if st.kind == "ar":
            lam0 = float(p["lam0_nm"])
            s0 = build_structure(p, lam0)
            nf = complex(s0.layers[0][0])
            R0 = rta(s0, lam0, 0.0, "s")["R"]
            ideal = math.sqrt(s0.n_in * s0.n_out)
            lab = T("Anti-reflection λ/4: the run's R(λ₀, 0°)")
            note = T("reference ((n₀n_s − n_f²)/(n₀n_s + n_f²))² at λ₀ with each material's index there; = 0 at "
                     "n_f = √(n₀ n_s) = {ideal:.8g} (here n_f = {nf:.8g}); the bare boundary: {bare:.6g}", ideal=ideal,
                     nf=nf.real, bare=rta(Structure("interface", s0.n_in, s0.n_out), lam0, 0.0, "s")["R"])
            if nf.imag == 0:
                ref = thin_films.quarter_wave_R(s0.n_in, nf.real, s0.n_out)
                self._check(f"ar{s}", lab, R0, ref, "", G, ok=abs(R0 - ref) <= 1e-12, tol=1e-12, note=note)
            else:
                ref = thin_films.quarter_wave_R(s0.n_in, nf.real, s0.n_out)
                self._check(f"ar{s}", T("{label} (for information: the film absorbs, κ = {k:.3g}; the closed form is "
                                        "for a lossless film)", label=lab, k=nf.imag), R0, ref, "", G, info=True,
                            note=note)
        # Bragg mirror
        if st.kind == "bragg":
            N, lam0 = int(p["pairs"]), float(p["lam0_nm"])
            s0 = build_structure(p, lam0)
            nH, nL = complex(s0.layers[0][0]), complex(s0.layers[1][0])
            R0 = rta(s0, lam0, 0.0, "s")["R"]
            ref = thin_films.quarter_wave_stack_R(s0.n_in, nH.real, nL.real, s0.n_out, N)
            lossless = nH.imag == 0 and nL.imag == 0
            self._check(f"bragg{s}", T("Bragg mirror: the run's R(λ₀, 0°)"), R0, ref, "", G, tol=1e-10,
                        info=not lossless,
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
            ref = mixed(*(thin_films.ftir_T(st.n_in, self.n_s, gap, lam, th, q) for q in ("s", "p")))
            self._check(f"ftir{s}", T("Frustrated total reflection: the run's T (tunnelling through the gap)"), Tc,
                        ref, "", G, tol=1e-9,
                        note=T("reference 1/(1 + ((a² + b²)/(2ab))² sinh²(κd)): s: a = k_z, b = κ; p: a = k_z/n₀², "
                               "b = κ/n_s²"))
        # polarisation: the reflected light's degree of polarisation (unpolarised source), Malus's law at an analyser
        if p["pol"] == "unpol" and here["probs"]["P_R"] > 1e-300 and st.kind != "none":
            dop = pol_.degree_of_polarisation(here["rho_R"])
            ref = pol_.degree_from_powers(cur["s"]["R"], cur["p"]["R"])
            self._check(f"dop{s}", T("Degree of polarisation of the reflected light, from its density matrix"), dop,
                        ref, "", POLG, tol=1e-10, ok=abs(dop - ref) <= 1e-10,
                        note=T("reference (R_s − R_p)/(R_s + R_p) of the transfer matrices: unpolarised light comes "
                               "back polarised along s, completely at Brewster's angle"))
        for arm, a in (("R", aR), ("T", aT)):
            self._malus_check(s, POLG, arm, a, here)
        # the source's line: how much the probabilities change over it
        lams, wts, table = self.comb
        if len(lams) > 1:
            spread = float(np.max(table.max(axis=0) - table.min(axis=0)))
            self._check(f"line{s}", T("The source's line: the largest change of an outcome's probability over ±4σ"),
                        spread, None, "", POLG, info=True,
                        note=T("Δλ = {w:.3g} nm (FWHM), {k:d} wavelengths; each photon's own wavelength sets its "
                               "probabilities", w=float(p["dlam_nm"]), k=len(lams)))

    def _malus_check(self, s, G, arm, a, here):
        """An analyser in an arm whose light has no circular part (S3 = 0 to 1e-12 of S0: linear, partly polarised or
        unpolarised): the pass port's probability from the density matrix against Malus's law for partially polarised
        light, (k1 + k2)/2 + (k1 - k2)/2 P cos 2(α - ψ) with ψ the beam's own azimuth and P its degree of polarisation
        (k1 cos²(α - ψ) + k2 sin²(α - ψ) for P = 1, (k1 + k2)/2 for unpolarised light); elliptical light (total
        reflection) has no such closed form: shown for information."""
        if a is None:
            return
        rho = here["rho_" + arm]
        P_arm = float(np.real(np.trace(rho)))
        if not P_arm > 1e-300:
            return
        S = pol_.stokes(rho / P_arm)
        alpha, k1, k2 = a
        frac = here["probs"][arm + "_pass"] / P_arm
        lab = (T("Malus's law at the reflection analyser: the pass port's share of the reflected photons")
               if arm == "R" else T("Malus's law at the transmission analyser: the pass port's share of the "
                                    "transmitted photons"))
        if abs(S[3]) <= 1e-12:
            Pl = math.hypot(S[1], S[2])
            psi = 0.5 * math.atan2(S[2], S[1])
            ref = 0.5 * (k1 + k2) + 0.5 * (k1 - k2) * Pl * math.cos(2.0 * (alpha - psi))
            closed = pol_.malus(psi, alpha, k1, k2) if Pl > 1 - 1e-12 else None
            ref = ref if closed is None else closed
            self._check(f"malus{arm}{s}", lab, frac, ref, "", G, tol=1e-12, ok=abs(frac - ref) <= 1e-12,
                        note=T("reference (k₁ + k₂)/2 + (k₁ − k₂)/2 · P cos 2(α − ψ) = k₁cos²(α − ψ) + k₂sin²(α − ψ) "
                               "for P = 1: the beam's polarisation ψ = {psi:.6g}°, its degree P = {P:.10g}, α = "
                               "{a:.6g}°, k₁ = {k1}, k₂ = {k2}; the run: tr(A†A ρ)/tr ρ", psi=math.degrees(psi), P=Pl,
                               a=math.degrees(alpha), k1=k1, k2=k2)
                        if closed is None else
                        T("reference k₁cos²(α − ψ) + k₂sin²(α − ψ) (lfphys polarization.malus), ψ = {psi:.6g}° the "
                          "beam's polarisation, α = {a:.6g}°, k₁ = {k1}, k₂ = {k2}; the run: tr(A†A ρ)/tr ρ",
                          psi=math.degrees(psi), a=math.degrees(alpha), k1=k1, k2=k2))
        else:
            e = pol_.ellipse(rho / P_arm)
            self._check(f"malus{arm}{s}", lab, frac, None, "", G, info=True,
                        note=T("the light in the arm is elliptical (axis ratio {r:.3g}, degree {d:.6g}): no closed "
                               "form of Malus's kind; the pass share is tr(A†A ρ)/tr ρ", d=e["degree"],
                               r=e["axis_ratio"]))

    def _tir_phase_check(self, s, G, here, th):
        """Total reflection at a bare boundary: the phase difference δ = arg r_s − arg r_p of the run's coefficients
        against Stratton's closed form tan(δ/2) = cos θ √(sin²θ − n²)/sin²θ (``polarization.tir_phase_closed_form``)."""
        bm = here["bm"]
        d_run = math.atan2((bm["r_s"] * np.conj(bm["r_p"])).imag, (bm["r_s"] * np.conj(bm["r_p"])).real)
        n = self.st.n_out / self.st.n_in
        ref = pol_.tir_phase_closed_form(n, th)
        diff = abs(d_run - ref)
        # near θ_c the phase goes as √(sin²θ − n²): a rounding of a few u in the radicand q moves √q by up to
        # √(q + 16u) − √q (√(16u) ≈ 6e-8 at q = 0), times 2cos θ/sin²θ ≤ 2/sin²θ_c of the closed form
        q = abs(math.sin(th) ** 2 - n * n)
        tol = 1e-11 + 4.0 / math.sin(th) ** 2 * (math.sqrt(q + 16 * U) - math.sqrt(q))
        self._check(f"tirphase{s}", T("Total reflection: the phase difference δ = arg r_s − arg r_p of the run"),
                    math.degrees(d_run), math.degrees(ref), "°", G, tol=tol / max(abs(ref), 1e-300), ok=diff <= tol,
                    note=T("reference 2 arctan(cos θ √(sin²θ − n²)/sin²θ), n = n_s/n₀ (Stratton 1941, §9.7); "
                           "linear light at 45° comes back elliptical, left-handed; tolerance {tol:.2g} rad from the "
                           "rounding of sin²θ − n² near the critical angle", tol=tol))

    def _stat_check(self, s):
        """The five outcomes against the Born probabilities of the segment (exact binomial tails, Bonferroni; review
        V5-4), and the detectors against their model (exact binomial tail of the detected photons, exact Poisson tail of
        the dark counts, the non-paralysable dead time's closed form); fails below the two-sided 5σ tail."""
        c = self.segc.get(s)
        if not c:
            return
        n = c["n"]
        if n:
            k, pr = c["fate"], c["probs"]
            t = outcome_test(k, pr)
            names = [T("reflected and passed"), T("reflected and rejected"), T("transmitted and passed"),
                     T("transmitted and rejected"), T("absorbed")]
            parts = [T("{x}: {k:d} (expected {e:.1f}, z = {z:+.2f})", x=x, k=int(kx), e=px * n, z=zx)
                     if math.isfinite(zx) else
                     T("{x}: {k:d} (expected {e:.3g}: an impossible outcome)", x=x, k=int(kx), e=px * n)
                     for x, kx, px, zx in zip(names, k, pr, t["z"]) if px > 0 or kx > 0]
            self._check(f"stat{s}", T("The photons' outcomes (the run's event counts) against the Born probabilities: "
                                      "p-value"),
                        t["p"], None, "", T("Segment {seg:d}: photon statistics", seg=s), ok=t["p"] >= P_5SIGMA,
                        note=T("n = {k:d}; {parts}. The exact binomial tail of each outcome, Bonferroni correction "
                               "(outcomes: {m:d}); fails at p < {p5:.2g} (like 5σ); Pearson's χ² = {chi2:.3g} with "
                               "{dof:d} degrees of freedom (for information)", k=int(n), parts=join(parts), m=t["m"],
                               p5=P_5SIGMA, chi2=t["chi2"], dof=t["dof"]))
        det = detector_of(self.params)
        tails, parts = [], []
        for d in range(4):
            if self.dets[d] is None or (c["arr"][d] == 0 and c["dark"][d] == 0 and c["tdark"][d] == 0):
                continue
            pa = binom_two_sided(c["det_in"][d], c["arr"][d], det.eta)
            pb = poisson_two_sided(c["dark"][d], det.dark_rate * c["tdark"][d])
            Tw = c["tdark"][d]
            nin = c["det_in"][d] + c["dark"][d]
            if Tw > 0 and det.dead_time > 0:
                expect = float(pd.observed_rate(nin / Tw, det.dead_time)) * Tw
                lost = max(nin - expect, 0.0)
                zc = (c["rec"][d] - expect) / math.sqrt(lost + 1.0)
                pc = math.erfc(abs(zc) / math.sqrt(2.0))
            else:
                expect, zc, pc = float(nin), 0.0, 1.0 if c["rec"][d] == nin else 0.0
            tails += [pa, pb, pc]
            parts.append(T("{det}: {a:d} photons arrived, {k:d} detected (η = {eta}); {dk:d} dark counts in {tw:.4g} s "
                           "(expected {de:.4g}); {r:d} recorded, {e:.6g} by the dead-time formula (z = {z:+.2f})",
                           det=_det_name(d), a=c["arr"][d], k=c["det_in"][d], eta=det.eta, dk=c["dark"][d], tw=Tw,
                           de=det.dark_rate * Tw, r=c["rec"][d], e=expect, z=zc))
        if tails:
            pmin = min(1.0, len(tails) * min(tails))
            self._check(f"det{s}", T("The detectors' counts against their model: p-value"), pmin, None, "",
                        T("Segment {seg:d}: photon statistics", seg=s), ok=pmin >= P_5SIGMA,
                        note=T("{parts}. Exact binomial tails of the detected photons, Poisson tails of the dark "
                               "counts and the non-paralysable dead time m = n/(1 + n t_d) (lfphys photodetector); "
                               "Bonferroni over {m:d} tests; fails at p < {p5:.2g}", parts=join(parts), m=len(tails),
                               p5=P_5SIGMA))

    # --- checks near the critical and grazing angles (review 2026-10-23, V5-2) --------------------------------
    def _evan_check(self, s, G, lam, th):
        """The decay length of the evanescent wave from the run's field against lambda / (2 pi sqrt(q)),
        q = n0^2 sin^2 theta - n_s^2 (thin_films, exact to one rounding).

        The run's number: |E|^2 of s light at the face and at a depth z; first z = lambda/4, then z = the length so
        found, so that ln(I(0)/I(z)) ~ 2 (the logarithm of a ratio near 1 would lose digits). Its error to first order
        in u = 2^-53 (README, "evan"): the engine's cos theta_t = sqrt(1 - x^2), x = n0 sin theta / n_s, carries 9u in
        x^2, i.e. 9u K in 1 - x^2 (the subtraction itself is exact near x = 1), K = n0^2 sin^2 theta / q; the root
        halves it, and 2 pi, n_s, the product and lambda add <= 5u: the decay constant to (4.5 K + 5) u. Each |E|^2
        value carries <= (11 + ln) u and their ratio and logarithm add 1u each: ln to (15 + ln) u absolutely; the
        division by ln and the reference add 3u. Tolerance (4.5 K + 9 + 15/ln) u. Where it exceeds 1e-2 the
        first-order bound no longer holds: the angle is within rounding of theta_c and fixes the decay length only to
        ~K u; the line is then shown for information."""
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
                        note=T("θ differs from the critical angle by about a rounding: {cond}; the angle sets the "
                               "decay length only to ~K·2⁻⁵³ (the first-order error estimate does not apply here); "
                               "{tail}",
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
        compared 1e-3 rad further from grazing (the formula needs a propagating wave in the film). Over the spectrum
        each wavelength has its own indices (a dispersive film or medium)."""
        st, p = self.st, self.params
        pm = p["pol"]
        pols = ("s", "p") if pm not in ("s", "p") else (pm,)
        wq = {"s": float(np.real(self.rho[1, 1])), "p": float(np.real(self.rho[0, 0]))}

        def at(s_, a_, lam_):
            """{pol: (T of the formula, bound)} at angle a_ and wavelength lam_ for the structure s_ at lam_."""
            n1, d = complex(s_.layers[0][0]).real, s_.layers[0][1]
            out = {}
            for q in ("s", "p"):
                A = thin_films.airy(s_.n_in, n1, s_.n_out, d, lam_, a_, q)
                M = thin_films.stack_error_single_layer(s_.n_in, n1, s_.n_out, d, lam_, a_, q)
                out[q] = (A["T"], A["err_T"] + M["err_T"], A)
            return out

        def avg(vals):
            return sum(wq[q] * vals[q] for q in pols) / sum(wq[q] for q in pols)

        try:
            here = at(st, th, lam)
        except ValueError as e:
            self._check(f"airy{s}", T("Fabry–Pérot: the run's T and the Airy formula"), Tc, None, "", G,
                        note=T("the Airy formula in intensities does not apply here: {why}", why=_airy_reason(e)))
            return
        ref = avg({q: here[q][0] for q in pols})
        bound = avg({q: here[q][1] for q in pols})
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
                side = at(st, side_th, lam)
            except ValueError:
                side = None
            if side is not None:
                Ts = avg({q: rta(st, lam, side_th, q)["T"] for q in pols})
                refs = avg({q: side[q][0] for q in pols})
                bs = avg({q: side[q][1] for q in pols})
                ok = ok and abs(Ts - refs) <= bs
                note = T("{note}; F is large (the wave in the film almost grazes): the routes were also compared at "
                         "θ − {d} rad: |ΔT| = {dT:.2g} with the tolerance {tol:.2g}", note=note, d=1e-3,
                         dT=abs(Ts - refs), tol=bs)
        self._check(f"airy{s}", T("Fabry–Pérot: the run's T(λ, θ)"), Tc, ref, "", G,
                    tol=bound / abs(ref) if ref else bound, ok=ok, note=note)
        # the whole spectrum at the current angle, each wavelength with its own indices
        lg = cv["lam"]
        dev, tol, ok = 0.0, 0.0, True
        for q in pols:
            for x, Tr in zip(lg, cv["lT" + q]):
                sx = build_structure(p, float(x))
                n1, d = complex(sx.layers[0][0]).real, sx.layers[0][1]
                A = thin_films.airy(sx.n_in, n1, sx.n_out, d, float(x), th, q)
                b = A["err_T"] + thin_films.stack_error_single_layer(sx.n_in, n1, sx.n_out, d, float(x), th,
                                                                     q)["err_T"]
                e = abs(A["T"] - Tr)
                dev, tol, ok = max(dev, e), max(tol, b), ok and e <= b
        note = T("wavelengths at the current angle: {k:d}; the tolerance at each point is the sum of the round-off "
                 "error estimates of both routes", k=len(lg))
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
        if self.params["shutter"] != "open":
            self.t_next = max(self.t_next, t_target)
            return np.zeros(0)
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
        lams, wts, _ = self.comb
        kl = self.rng.choice(len(lams), size=k, p=wts) if len(lams) > 1 else np.zeros(k, np.int64)
        code = POL_CODE[self.params["pol"]]
        self.flight.add(pid=np.arange(self.pid, self.pid + k), te=te, ts=te + self.times["t_in"], lam=lams[kl], kl=kl,
                        pol=np.full(k, code, np.int8), sege=np.full(k, self.seg), stage=np.zeros(k))
        self.pid += k
        self.tot["emitted"] += k
        self.segc[self.seg]["emit"] += k

    def _at_structure(self, idx):
        """The photons reach the structure present now: each one's outcome by the Born rule with the five
        probabilities of its own wavelength (the comb's), on the source's density matrix."""
        a = self.flight.a
        _, _, table = self.comb
        kl = a["kl"][idx]
        out = np.empty(len(idx), np.int8)
        u = self.rng.random(len(idx))
        for k in np.unique(kl):
            m = kl == k
            cum = np.cumsum(table[k])
            out[m] = np.minimum(np.searchsorted(cum / cum[-1], u[m], side="right"), 4)
        P = self.segc[self.seg]["P"]
        PR, PT = P["P_R"], P["P_T"]
        ts = a["ts"][idx]
        tR, tT = ts + self.times["t_R"], ts + self.times["t_T"]
        wR = PR / (PR + PT) if PR + PT > 0 else 0.0
        a["out"][idx] = out
        a["seg"][idx] = np.where(a["sege"][idx] == self.seg, self.seg, -1)
        a["tR"][idx], a["tT"][idx] = tR, tT
        a["wR"][idx], a["wT"][idx] = wR, (1.0 - wR) if PR + PT > 0 else 0.0
        a["tdet"][idx] = np.where(out <= 1, tR, np.where(out <= 3, tT, ts))
        a["stage"][idx] = 1

    def _reveal(self, t_target):
        """Everything that happens on (t, t_target]: photons absorbed at the structure, photons arriving at the
        detectors, the detectors' clicks (efficiency, dark counts, dead time, jitter), counted up to the gate."""
        a = self.flight.a
        done = (a["stage"] == 1) & (a["tdet"] <= t_target)
        ii = np.nonzero(done)[0]
        ii = ii[np.argsort(a["tdet"][ii], kind="stable")]
        out, seg = a["out"][ii], a["seg"][ii]
        c = self.segc[self.seg]
        gate = self._gate()
        g_end = t_target if gate is None else min(t_target, gate)
        # the fates (simulation-known) of the photons of this segment that are revealed now
        for sv in np.unique(seg):
            if sv < 0:
                continue
            m = seg == sv
            cs = self.segc[int(sv)]
            cs["n"] += int(m.sum())
            for j in range(5):
                cs["fate"][j] += int(np.sum(out[m] == j))
        self.tot["transitional"] += int(np.sum(seg < 0))
        nA = int(np.sum((out == 4) & (seg == self.seg) & (a["tdet"][ii] <= g_end)))
        c["nA"] += nA
        self.tot["A"] += int(np.sum(out == 4))
        # the detectors: arrivals (any segment's photons: a detector does not know) merged with dark counts
        ev_t, ev_det, ev_pol = [a["tdet"][ii][out == 4]], [np.full(int(np.sum(out == 4)), 4, np.uint8)], \
            [a["pol"][ii][out == 4].astype(np.uint8)]
        per_seg = {}
        for d, ds in enumerate(self.dets):
            m = out == d
            arr_t = a["tdet"][ii][m]
            if ds is None:
                if m.any():  # no detector stands there (cannot happen: such an outcome has probability 0)
                    self.tot["missed"] += int(m.sum())
                continue
            t0 = ds.t
            times, tags, dark, used, n_det, n_dark = ds.step(t_target, arr_t)
            c["arr"][d] += int(m.sum())
            c["det_in"][d] += n_det
            c["dark"][d] += n_dark
            c["rec"][d] += len(times)
            c["tdark"][d] += t_target - t0
            self.tot["missed"] += int(m.sum()) - int(len(used))
            counted = times <= g_end
            src_seg = np.full(len(times), self.seg, np.int64)
            ph = ~dark
            src_seg[ph] = seg[m][used]
            for sv in np.unique(src_seg[counted]):
                row = per_seg.setdefault(int(sv), [0, 0, 0, 0, 0])
                row[d] += int(np.sum(counted & (src_seg == sv)))
            cnt_here = counted & (src_seg == self.seg)
            c["clk"][d] += int(np.sum(cnt_here))
            c["clk_dark"][d] += int(np.sum(cnt_here & dark))
            self.tot["dark"] += int(np.sum(dark))
            self.tot["clicks"] += len(times)
            pol = np.full(len(times), DARK_CODE, np.uint8)
            pol[ph] = a["pol"][ii][m][used].astype(np.uint8)
            ev_t.append(tags)
            ev_det.append(np.full(len(times), d, np.uint8))
            ev_pol.append(pol)
        if nA:
            per_seg.setdefault(self.seg, [0, 0, 0, 0, 0])[4] += nA
        self.tot["R"] += int(np.sum(out <= 1))
        self.tot["T"] += int(np.sum((out == 2) | (out == 3)))
        t_all = np.concatenate(ev_t)
        if len(t_all) or per_seg:
            order = np.argsort(t_all, kind="stable")
            det_all, pol_all = np.concatenate(ev_det)[order], np.concatenate(ev_pol)[order]
            t_all = t_all[order]
            # the individual events the view flashes: the last SHOWN of the step at each detector and at the structure
            # (the exact counts are by_seg's)
            sh = np.zeros(len(t_all), bool)
            for code in np.unique(det_all):
                sh[np.nonzero(det_all == code)[0][-SHOWN:]] = True
            by_seg = [[s_] + row for s_, row in sorted(per_seg.items())]
            self._msg({"type": "clicks", "t": t_target, "n": int(len(t_all)), "by_seg": by_seg,
                       "shown": int(sh.sum())},
                      {"t": t_all[sh].astype(np.float64), "det": det_all[sh], "pol": pol_all[sh]})
        self.flight.keep(~done)

    def advance(self, t_target):
        te = self._emissions(t_target)
        if len(te):
            self._emit_photons(te)
        a = self.flight.a
        idx = np.nonzero((a["stage"] == 0) & (a["ts"] <= t_target))[0]
        if len(idx):
            self._at_structure(idx)
        self._reveal(t_target)
        gate = self._gate()
        if gate is not None and not self.gated and t_target >= gate:
            self.gated = True
            self._msg({"type": "event", "t": gate, "kind": "gate",
                       "text": T("the counting time is over: the counters stop at {g:.4g} s", g=gate)})
        self.t = t_target
        c = self.segc[self.seg]
        if c["n"] >= self._stat_next:
            self._stat_check(self.seg)
            while self._stat_next <= c["n"]:
                self._stat_next = _next_step(self._stat_next)

    def next_event_time(self):
        """The next emission, the next arrival at the structure or at a detector, the gate."""
        a = self.flight.a
        cands = [self.t_next] if self.params["shutter"] == "open" else []
        m0, m1 = a["stage"] == 0, a["stage"] == 1
        if m0.any():
            cands.append(float(a["ts"][m0].min()))
        if m1.any():
            cands.append(float(a["tdet"][m1].min()))
        g = self._gate()
        if g is not None and not self.gated:
            cands.append(g)
        return min(cands) if cands else None

    # --- frames -----------------------------------------------------------------------------------------
    def frame(self):
        """Photons under way as the viewer may know them at time t: on the way in, a progress along the incident
        arm; after the structure, not yet detected: the reflected and transmitted packets (weights P_R/(P_R+P_T) and
        P_T/(P_R+P_T)); once one arm's arrival time has passed without a click there, its packet is gone and the other
        one's weight is the conditional probability with that detector's efficiency (Bayes; Lüders for an ideal
        detector). The counters and the measurables of the segment (none before the counting starts)."""
        a = self.flight.a
        t = self.t
        n = len(self.flight)
        fl = np.zeros((n, 6))
        eta = detector_of(self.params).eta
        if n:
            st0 = a["stage"] == 0
            fl[:, 0] = a["stage"]
            fl[:, 1] = a["pol"]
            fl[st0, 2] = (t - a["te"][st0]) / np.maximum(a["ts"][st0] - a["te"][st0], 1e-300)
            s1 = ~st0
            ts, tR, tT = a["ts"][s1], a["tR"][s1], a["tT"][s1]
            wR, wT = a["wR"][s1].copy(), a["wT"][s1].copy()
            goneT, goneR = t >= tT, t >= tR
            # one arm passed without a click: the other arm's weight by Bayes with the efficiency
            onlyR = goneT & ~goneR & (wR > 0)
            wR[onlyR] = wR[onlyR] / (wR[onlyR] + wT[onlyR] * (1.0 - eta))
            wT[goneT] = 0.0
            onlyT = goneR & ~goneT & (wT > 0)
            wT[onlyT] = wT[onlyT] / (wT[onlyT] + a["wR"][s1][onlyT] * (1.0 - eta))
            wR[goneR] = 0.0
            fl[s1, 2] = (t - ts) / np.maximum(tR - ts, 1e-300)
            fl[s1, 3] = wR
            fl[s1, 4] = (t - ts) / np.maximum(tT - ts, 1e-300)
            fl[s1, 5] = wT
            if n > 400:
                fl = fl[np.linspace(0, n - 1, 400).astype(int)]
        c = self.segc[self.seg]
        clk = c["clk"]
        gate = self._gate()
        t_c = (min(t, gate) if gate is not None else t) - c["t0"]
        started = t_c > 0
        here = [d is not None for d in self.dets]
        cnt = lambda d: (int(clk[d]) if here[d] else None) if started else None  # noqa: E731
        nR = (clk[0] + clk[1]) if started else None
        nT = (clk[2] + clk[3]) if started else None
        meas = {"t_c": t_c if started else None, "n_R": nR, "n_T": nT, "n_Rp": cnt(0), "n_Rr": cnt(1),
                "n_Tp": cnt(2), "n_Tr": cnt(3), "n_clicks": sum(clk) if started else None,
                "n_emit": c["emit"] if started else None, "n_A": c["nA"] if started else None,
                "n_dark": sum(c["clk_dark"]) if started else None}
        P = c["P"]
        # the computed fractions describe the photons: with none sent in this segment (the shutter closed: only dark
        # counts) there is nothing to compare them with, and none is shown
        sent = c["emit"] > 0
        R_ref = P["P_R"] / (P["P_R"] + P["P_T"]) if sent and P["P_R"] + P["P_T"] > 0 else None
        meas.update(_frac(nR, nT, "R_frac", R_ref))
        meas.update(_frac(nT, nR, "T_frac", None if R_ref is None else 1.0 - R_ref))
        for arm, i0 in (("R", 0), ("T", 2)):
            key = f"f{arm}_pass"
            if here[i0 + 1] and started:
                ref = P[arm + "_pass"] / P["P_" + arm] if sent and P["P_" + arm] > 0 else None
                meas.update(_frac(clk[i0], clk[i0 + 1], key, ref))
            else:
                meas.update({key: None, key + "_se": None, key + "_ref": None})
        counts = {"Rp": int(clk[0]), "Rr": int(clk[1]), "Tp": int(clk[2]), "Tr": int(clk[3]), "A": int(c["nA"]),
                  "dark": int(sum(c["clk_dark"])), "n": int(sum(clk)), "here": here}
        return ({"seg": self.seg, "counts": counts, "meas": meas, "expected": dict(zip(OUT5, c["probs"])),
                 "totals": dict(self.tot), "in_flight": n, "gated": bool(self.gated)}, {"fl": fl})

    def header(self):
        return {
            "title": self._title(),
            "text": T("The source emits photons one by one (a Poisson stream, each photon's wavelength from the "
                      "source's line) onto a planar structure of real materials: a boundary between two media, an "
                      "anti-reflection layer, a Bragg mirror, a Fabry–Pérot film, a metal film or a prism's face "
                      "(total internal reflection; with a gap, tunnelling). For every set-up the run computes, with "
                      "the transfer matrices of the engine lfphys, the amplitudes r, t, the polarisation of each "
                      "outgoing beam, the curves R(θ), T(θ), R(λ), T(λ) and the field |E|² inside the structure. Each "
                      "photon's outcome (reflected or transmitted, and through which port of an analyser, or absorbed) "
                      "is drawn by the Born rule; we learn it when a detector clicks. Real detectors miss photons, "
                      "count in the dark and are dead for a while after each click."),
            "modifications": SCHEMA.modifications(self.params),
            "actions": self._actions(),
            "arm_m": ARM_M, "t_in": self.times["t_in"], "rate": float(self.params["rate"]),
            "measurables": MEASURABLES,
        }, {}


def _frac(a, b, key, ref):
    """A fraction a/(a + b) of two counts with its binomial standard error √(f(1 − f)/N) (None without counts)."""
    if a is None or b is None or a + b == 0:
        return {key: None, key + "_se": None, key + "_ref": ref}
    n = a + b
    f = a / n
    return {key: f, key + "_se": math.sqrt(max(f * (1 - f), 1.0 / n) / n), key + "_ref": ref}


def _ellipse(rho):
    """The polarisation ellipse of a beam (``polarization.ellipse``) in degrees, with its intensity (the arm's
    probability); None for a beam that carries nothing."""
    P = float(np.real(np.trace(rho)))
    if not P > 1e-300:
        return None
    e = pol_.ellipse(rho / P)
    deg = lambda x: None if not math.isfinite(x) else math.degrees(x)  # noqa: E731
    return {"P": P, "azimuth": deg(e["azimuth"]), "chi": deg(e["chi"]), "degree": e["degree"],
            "hand": int(e["handedness"]), "ratio": e["axis_ratio"] if math.isfinite(e["axis_ratio"]) else None}


ANA_GRID = np.linspace(0.0, 180.0, 181)


def _analyser_curves(here, aR, aT) -> dict:
    """With an analyser in an arm: the share of that arm's light through its pass port at every angle 0°..180° (its own
    k1, k2), tr(A(α)†A(α) ρ)/tr ρ of the arm's density matrix (``polarization.beam_splitter``): the run's Malus curve
    for the light the arm carries (the analyser's own angle is one point of it)."""
    out = {}
    for arm, a in (("R", aR), ("T", aT)):
        rho = here["rho_" + arm]
        P = float(np.real(np.trace(rho)))
        if a is None or not P > 1e-300:
            continue
        f = []
        for x in ANA_GRID:
            A, _ = pol_.beam_splitter(math.radians(float(x)), a[1], a[2])
            f.append(float(np.real(np.trace(A.conj().T @ A @ rho))) / P)
        out["ana" + arm + "_f"] = np.asarray(f, np.float64)
    if out:
        out["ana_a"] = ANA_GRID.copy()
    return out


def _ana_dict(a, dev):
    if a is None:
        return None
    return {"alpha": math.degrees(a[0]), "k1": a[1], "k2": a[2], "dev": dev}


def _medium_name(mid, n):
    if mid == "model":
        return T("model medium n = {n:.5g}", n=n)
    return MATERIAL_NAME[mid]


def _det_name(d):
    return [T("reflection, pass port"), T("reflection, reject port"), T("transmission, pass port"),
            T("transmission, reject port")][d]


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

from .screens import RECORDINGS, SCREENS  # noqa: E402

VIZ = {
    "id": "u35_optics_bench",
    "title": T("Optical bench: boundaries, coatings, polarisation"),
    "summary": T("Photons one by one at a boundary between real media (SCHOTT glasses), at real coatings (MgF₂, "
                 "Ta₂O₅/SiO₂, aluminium, silver), a gold film, a prism's face (total and frustrated total reflection); "
                 "analysers and Malus's law, polarisation by reflection, the phase of total reflection; real "
                 "single-photon detectors with dark counts and dead time."),
    "purpose": T("How reflection, transmission, absorption and polarisation come out of Maxwell's equations at the "
                 "boundaries of real materials (transfer matrices, Jones matrices), and how single photons add up to "
                 "these fractions by the Born rule, as real detectors count them."),
    "version": "1.1",
    "schema": SCHEMA,
    "simulation": Simulation,
    "audience": "university",
    "section": "optics",
    "ui": "standard",
    "teaser": T("Photons hit a boundary one by one and split in the fractions that Maxwell's equations give."),
    "courses": [
        {"text": T("Hecht, Optics"), "chapters": "4, 8, 9"},
        {"text": T("Sivukhin, General Course of Physics, vol. IV: Optics"), "chapters": "V"},
    ],
    "related": ["S35"],
    "recordings": RECORDINGS,
    "screens": SCREENS,
}
