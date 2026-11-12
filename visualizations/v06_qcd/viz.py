# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v06: quantum chromodynamics — asymptotic freedom and quarkonium (a wrapper over lfphys).

* The running coupling alpha_s(mu) (lfphys.core.qcd.running): the renormalisation-group equation with the MS-bar beta
  function to 1-4 loops, quark thresholds at the PDG masses, from the world average alpha_s(M_Z) (lfphys.core.data,
  PDG 2024). Pressing play sweeps the probe scale mu over the decades: the world's time is the logarithm of the scale.
* The colour algebra (lfphys.core.qcd.su3): the Casimirs C_F, C_A computed from the Gell-Mann matrices.
* Quarkonium (lfphys.theories.models.cornell, a fitted model outside the core): the radial Schroedinger equation
  (lfphys.core.quantum.radial) in V = -kappa/r + r/a^2 for charm or bottom; the spin-averaged level splittings
  against the PDG masses; the model's kappa compared with the running coupling of the core (kappa = 4/3 alpha_s at
  the scale of the bound state is the one-gluon-exchange reading of the Coulomb term).
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.core import data
from lfphys.core.qcd import running, su3
from lfphys.i18n import T
from lfphys.theories.models import cornell
from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from lfviz.sim import Simulation as BaseSimulation


def _p(*a, **k):
    return Param(*a, **k)


def _join(items, sep="; "):
    """Several texts as one (a nested T: each part stays translatable)."""
    items = [x for x in items if x]
    if not items:
        return None
    out = items[0]
    for x in items[1:]:
        out = T("{a}; {b}", a=out, b=x) if sep == "; " else T("{a}, {b}", a=out, b=x)
    return out


LAWS = T("Laws")
RUNNING = T("Running of the coupling")
QUARKONIUM = T("Quarkonium (model)")


SCHEMA = Schema([
    _p("alpha_mz", T("α_s(M_Z), the coupling constant"), "float", data.ALPHA_S_MZ[0], group=LAWS, min=0.05, max=0.3,
       standard=data.ALPHA_S_MZ[0],
       help=T("PDG 2024 world average: {v} ± {dv}", v=data.ALPHA_S_MZ[0], dv=data.ALPHA_S_MZ[1])),
    _p("loops", T("Order of the β function (loops)"), "int", 4, group=RUNNING, min=1, max=4, live=True),
    _p("mu", T("Probe scale μ, GeV"), "float", 10.0, group=RUNNING, min=1.0, max=1e4, log=True, live=True,
       help=T("“Play” sweeps the probe over the scales: the world's time is the logarithm of the scale")),
    _p("sweep", T("Sweep speed, decades per world second"), "float", 0.5, group=RUNNING, min=0.01, max=10,
       log=True, live=True),
    _p("system", T("Quarkonium"), "select", "charm", group=QUARKONIUM, live=True,
       options=[("charm", T("charmonium (c c̄)")), ("bottom", T("bottomonium (b b̄)"))]),
    _p("kappa", T("κ (Coulomb part, dimensionless)"), "float", cornell.PARAMS["kappa"], group=QUARKONIUM,
       min=0.0, max=1.5, live=True),
    _p("a_conf", T("a, GeV⁻¹ (string tension 1/a²)"), "float", cornell.PARAMS["a"], group=QUARKONIUM,
       min=1.0, max=5.0, live=True),
    _p("m_q", T("Quark mass in the model, GeV (0 = from the EGKLY model)"), "float", 0.0, group=QUARKONIUM,
       min=0.0, max=10.0, live=True),
], presets={
    "standard": {"label": T("Asymptotic freedom and charmonium (PDG 2024, Cornell model)"), "params": {}},
    "bottom": {"label": T("Bottomonium"), "params": {"system": "bottom"}},
    "one_loop": {"label": T("One loop only: how much the higher orders matter"), "params": {"loops": 1}},
    "strong": {"label": T("What if α_s(M_Z) = {a} (a changed coupling)", a=0.15), "params": {"alpha_mz": 0.15},
               "note": T("With this coupling the perturbation series does not converge at {mu} GeV: the convergence "
                         "check fails, as expected", mu=2)},
})

def _val(k, v):
    """A parameter's value as the change log shows it: a select by its option's label, a number as a number."""
    p = SCHEMA.by_id[k]
    if p.type == "select":
        return dict((o[0], o[1]) for o in p.options).get(v, v)
    return v


THRESH = {"c": data.M_C_MC[0], "b": data.M_B_MB[0], "t": data.M_T_MSBAR}
MU_MIN, MU_MAX = 1.0, 1e4
MQ_MIN = 1.0  # GeV: the lightest quark mass the (heavy-quark, non-relativistic) model is offered for


class Simulation(BaseSimulation):
    speed_range = (0.01, 100.0)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = dict(params)
        self.seg = -1
        self._buf = []
        self.default_speed = 1.0
        self._recompute(T("start"))

    # --- computation ----------------------------------------------------------------------------------------
    def _alpha(self, mu, loops=None, a_mz=None):
        """alpha_s(mu); NaN below a Landau pole (the perturbative solution does not exist there)."""
        try:
            return running.alpha_s(mu, a_mz or self.params["alpha_mz"], data.M_Z[0], THRESH,
                                   loops or self.params["loops"])
        except running.LandauPole:
            return float("nan")
        except ValueError as e:  # not a pole: the integrator itself failed (review UX-params P4/P5): said to the user
            raise Refusal(T("the renormalisation-group equation was not solved at α_s(M_Z) = {a:.4g}, μ = {mu:.4g} GeV",
                            a=a_mz or self.params["alpha_mz"], mu=mu),
                          hint=T("take α_s(M_Z) closer to the world average {avg}", avg=data.ALPHA_S_MZ[0]),
                          detail=str(e)) from e

    def _recompute(self, reason):
        p = self.params
        if 0 < p["m_q"] < MQ_MIN:
            raise Refusal(T("quark mass {m:.4g} GeV: the Cornell model is non-relativistic and describes heavy quarks "
                            "(c, b); for m_q < {mmin:.4g} GeV the binding energy is comparable to the mass, and its "
                            "levels mean nothing", m=p["m_q"], mmin=MQ_MIN),
                          hint=T("set the quark mass to at least {mmin:.4g} GeV, or 0 for the model's own mass",
                                 mmin=MQ_MIN))
        seg = self.seg + 1
        mus = np.geomspace(MU_MIN, MU_MAX, 160)
        curves = {}
        for L in (1, 2, 3, 4):
            curves[f"L{L}"] = np.array([self._alpha(m, L) for m in mus])
        lo = np.array([self._alpha(m, None, p["alpha_mz"] - data.ALPHA_S_MZ[1]) for m in mus])
        hi = np.array([self._alpha(m, None, p["alpha_mz"] + data.ALPHA_S_MZ[1]) for m in mus])
        # quarkonium
        mq = p["m_q"] or (cornell.PARAMS["m_c"] if p["system"] == "charm" else cornell.PARAMS["m_b"])
        table = data.CHARMONIUM if p["system"] == "charm" else data.BOTTOMONIUM
        box = {}
        sp = cornell.spectrum(mq, p["kappa"], p["a_conf"], L_max=2, n_max=3, info=box)
        base = sp[(1, 0)]
        m1s, used1s = data.spin_averaged(table, 0, 1)
        levels = []
        for (n, L), M in sorted(sp.items()):
            meas, used = data.spin_averaged(table, L, n)
            levels.append({"n": n, "L": L, "model": (M - base) * 1e3 + m1s, "split_model": (M - base) * 1e3,
                           "measured": meas, "split_measured": None if meas is None else meas - m1s, "states": used})
        # radial wave functions of the lowest states for drawing
        from lfphys.core.quantum import radial
        V = cornell.potential(p["kappa"], p["a_conf"])
        Rb = box.get("R", 25.0)  # the box the spectrum needed (grows for large states: review V6-5)
        E0, r, u0 = radial.levels(V, 0, 0.5 * mq, Rb, N=600, n_states=2)
        E1, _, u1 = radial.levels(V, 1, 0.5 * mq, Rb, N=600, n_states=1)
        # the bound state's size and the running coupling there: kappa vs 4/3 alpha_s(1/<r>)
        r_mean = float(np.sum(r * u0[:, 0] ** 2) * (r[1] - r[0]))
        mu_bs = 1.0 / r_mean
        a_bs = self._alpha(mu_bs) if mu_bs >= 1.0 else None
        if a_bs is not None and not math.isfinite(a_bs):
            a_bs = None
        self.seg = seg
        self.state = {"mus": mus, "curves": curves, "lo": lo, "hi": hi, "levels": levels, "mq": mq,
                      "r": r, "u": np.stack([u0[:, 0], u0[:, 1], u1[:, 0]]), "r_mean": r_mean, "mu_bs": mu_bs,
                      "a_bs": a_bs}
        blobs = {"mus": mus, "lo": lo, "hi": hi, "r": r.astype(np.float64),
                 "u": np.stack([u0[:, 0], u0[:, 1], u1[:, 0]]).astype(np.float64).ravel(),
                 "V": V(r).astype(np.float64)}
        for k, v in curves.items():
            blobs[k] = v
        self._msg({"type": "segment", "t": self.t, "seg": self.seg, "reason": reason, "levels": levels,
                   "mq": mq, "system": p["system"], "thresholds": THRESH, "mz": data.M_Z[0],
                   "alpha_mz": p["alpha_mz"], "alpha_mz_pdg": list(data.ALPHA_S_MZ), "loops": p["loops"],
                   "r_mean": r_mean, "mu_bs": mu_bs, "a_bs": a_bs, "kappa": p["kappa"], "a_conf": p["a_conf"]},
                  blobs)
        self._checks()

    def _checks(self):
        p = self.params
        g = T("Segment {seg:d}", seg=self.seg)
        a0, mz = p["alpha_mz"], data.M_Z[0]
        for mu in (2.0, 1000.0):
            try:
                val = running.alpha_s(mu, a0, mz, {"c": 0.1, "b": 0.2}, 1)
            except running.LandauPole as e:  # a large alpha_s(M_Z): the pole lies above this scale (review V6-1)
                self._check(f"one{self.seg}_{mu:g}", T("One loop, α_s({mu:.4g} GeV), n_f = 5 without thresholds", mu=mu),
                            None, None, "", g, info=True,
                            note=T("not computed: a Landau pole, α_s diverges near μ ≈ {mu:.3g} GeV (perturbation "
                                   "theory does not apply)", mu=e.mu))
                continue
            self._check(f"one{self.seg}_{mu:g}", T("One loop, α_s({mu:.4g} GeV), n_f = 5 without thresholds", mu=mu),
                        val, running.one_loop(mu, a0, mz, 5), "",
                        g, tol=1e-10, note=T("reference: the closed-form solution α/(1 + α β₀/(4π) ln(μ²/M_Z²))"))
        b0, b1 = running.beta_coefficients(5, 2)
        mu = 500.0
        a = running.alpha_s(mu, a0, mz, {"c": 0.1, "b": 0.2}, 2) / (4 * math.pi)
        A0 = a0 / (4 * math.pi)
        lhs = math.log(mu**2 / mz**2)
        rhs = 1 / (b0 * a) - 1 / (b0 * A0) + b1 / b0**2 * math.log(a * (b0 + b1 * A0) / (A0 * (b0 + b1 * a)))
        self._check(f"two{self.seg}", T("Two loops: the exact implicit solution"), rhs, lhs, "", g, tol=1e-9,
                    note=T("ln(μ²/M_Z²) from 1/(β₀a) + (β₁/β₀²) ln(...) at the computed α_s({mu} GeV)", mu=mu))
        L = p["loops"]
        for q, m in THRESH.items():
            up, dn = self._alpha(m * (1 + 1e-9)), self._alpha(m * (1 - 1e-9))
            if not (math.isfinite(up) and math.isfinite(dn)):
                continue
            # the decoupling relation at mu = m_q(m_q), written out here (RunDec Eqs. 20 and 23; CKS 1997), of one loop
            # less than the running; the side the run comes from (M_Z) is the input
            n_l = 3 + sum(1 for x in THRESH.values() if x < m)
            c2 = 11 / 72 if L >= 3 else 0.0
            c3 = (564731 / 124416 - 82043 / 27648 * 1.2020569031595942 - 2633 / 31104 * n_l) if L >= 4 else 0.0
            if m < mz:
                x = up / math.pi
                ref, val = up * (1 + c2 * x * x + c3 * x**3), dn
                label = T("Matching at the {q}-quark threshold ({m:.4g} GeV): α_s below the threshold", q=q, m=m)
            else:
                x = dn / math.pi
                ref, val = dn * (1 - c2 * x * x - c3 * x**3), up
                label = T("Matching at the {q}-quark threshold ({m:.4g} GeV): α_s above the threshold", q=q, m=m)
            order = {1: T("continuous"), 2: T("continuous"), 3: T("a jump (11/72)(α_s/π)²"),
                     4: T("a jump (11/72)(α_s/π)² + c₃(α_s/π)³")}[L]
            self._check(f"thr{self.seg}{q}", label, val, ref, "", g, tol=1e-7,
                        note=T("the decoupling relation at μ = m_q(m_q), loops: {lm:d} (running: {l:d}); {order}; "
                               "relative jump {jump:.2g}", lm=L - 1, l=L, order=order, jump=abs(up / dn - 1)))
        a3, a4 = self._alpha(2.0, 3), self._alpha(2.0, 4)
        if math.isfinite(a3) and math.isfinite(a4):
            self._check(f"conv{self.seg}", T("Convergence of the series: α_s({mu} GeV) at 3 and 4 loops", mu=2.0),
                        a4, a3, "", g, ok=abs(a4 - a3) < 0.01 * a4,
                        note=T("the truncation of the β function is a theoretical uncertainty; threshold {p} %", p=1),
                        expected=None if a0 == data.ALPHA_S_MZ[0] else
                        T("α_s(M_Z) = {a:.4g} is changed (what if): at {mu} GeV the perturbation series does not "
                          "converge, which is what this world shows", a=a0, mu=2.0))
        pole = [m for m, v in zip(self.state["mus"], self.state["curves"][f"L{p['loops']}"]) if not math.isfinite(v)]
        if pole:
            self._msg({"type": "notice", "t": self.t,
                       "text": T("Below μ ≈ {mu:.3g} GeV α_s diverges (a Landau pole): perturbation theory does not work "
                                 "there, and the curve ends.", mu=max(pole))})
        if self.seg == 0:
            CF = sum(su3.T[a] @ su3.T[a] for a in range(8))
            F, _ = su3.structure_constants()
            CA = float(np.einsum("acd,acd->", F, F)) / 8
            self._check("cf", T("Casimir C_F from the Gell-Mann matrices"), float(np.real(CF[0, 0])), 4 / 3, "",
                        T("Colour"), tol=1e-14, note="Σ T_a T_a = C_F·1")
            self._check("ca", T("Casimir C_A from the structure constants"), CA, 3.0, "", T("Colour"), tol=1e-13,
                        note="Σ f_acd f_bcd = C_A δ_ab")
        st = self.state
        fitted = (p["kappa"] == cornell.PARAMS["kappa"] and p["a_conf"] == cornell.PARAMS["a"] and p["m_q"] == 0.0)
        for lv in st["levels"]:
            if lv["split_measured"] is None or (lv["n"], lv["L"]) == (1, 0):
                continue
            rel = lv["split_model"] / lv["split_measured"] - 1
            self._check(f"lev{self.seg}_{lv['n']}{lv['L']}",
                        T("Model: the splitting {state} − 1S", state=f"{lv['n']}{'SPD'[lv['L']]}"),
                        lv["split_model"], lv["split_measured"], T("MeV"), g, ok=abs(rel) < 0.10,
                        note=T("measured (PDG 2024, spin-averaged over {states}); a model outside the core, tolerance "
                               "{tol} %", states=", ".join(lv["states"]), tol=10),
                        expected=None if fitted else T("the Cornell model's parameters differ from the EGKLY fit: the "
                                                       "levels need not agree with the measured ones"))
        if st["a_bs"] is not None:
            self._check(f"kap{self.seg}", T("The model's κ against the core's 4/3·α_s at the scale 1/⟨r⟩"), p["kappa"],
                        4 / 3 * st["a_bs"], "", g, info=True,
                        note=T("⟨r⟩ = {r:.3g} GeV⁻¹, μ = 1/⟨r⟩ = {mu:.3g} GeV; a comparison of two layers, not a "
                               "check: the model's κ is a fit", r=st["r_mean"], mu=st["mu_bs"]))

    # --- messages ---------------------------------------------------------------------------------------------
    def _msg(self, meta, blobs=None):
        if self._buf is not None:
            self._buf.append((meta, blobs))
        else:
            self.emit(meta, blobs)

    def after_header(self):
        buf, self._buf = self._buf, None
        for meta, blobs in buf:
            self.emit(meta, blobs)

    def _check(self, cid, label, value, ref, unit="", group="", note="", tol=1e-9, ok=None, info=False,
               expected=None):
        rel = None
        if ref is not None and value is not None and ref != 0 and math.isfinite(value):
            rel = (value - ref) / abs(ref)
        d = {"type": "check", "t": self.t, "id": cid, "label": label, "value": value, "ref": ref, "unit": unit,
             "rel": rel, "group": group, "note": note, "tol": tol}
        if ok is not None:
            d["ok"] = bool(ok)
        if info:
            d["info"] = True
        if expected:  # a failure that is the point of the world (review UX-params P23): drawn as expected
            d["expected"] = expected
        self._msg(d)

    # --- live ---------------------------------------------------------------------------------------------------
    def live_values(self):
        return {k: self.params[k] for k in SCHEMA.live_ids()}

    def set_live(self, values):
        new, errors = SCHEMA.coerce_live(self.params, values)
        if errors:
            raise Refusal(_join(errors))
        changed = [k for k in values if new.get(k) != self.params.get(k)]
        if not changed:
            return T("no change")
        desc = _join([T("{label}: {old} → {new}", label=SCHEMA.by_id[k].label, old=_val(k, self.params[k]),
                        new=_val(k, new[k])) for k in changed])
        old = self.params
        self.params = new
        if set(changed) <= {"mu", "sweep"}:
            # a new start scale moves the probe; a new speed continues from where the probe is (review V6-4)
            self.mu_dec0 = math.log10(new["mu"]) if "mu" in changed else math.log10(self._mu_at(old, self.t))
            self.mu_t0 = self.t
            return desc
        try:
            self._recompute(T("changed: {what}", what=desc))
        except Exception:
            self.params = old
            raise
        return desc

    # --- time: the probe sweeps the scales ------------------------------------------------------------------
    mu_t0 = 0.0
    mu_dec0 = None  # log10 of the probe scale at mu_t0 (None: the parameter mu)

    def _mu_at(self, p, t):
        dec0 = math.log10(p["mu"]) if self.mu_dec0 is None else self.mu_dec0
        dec = dec0 + p["sweep"] * (t - self.mu_t0)
        span = math.log10(MU_MAX) - math.log10(MU_MIN)
        dec = math.log10(MU_MIN) + (dec - math.log10(MU_MIN)) % span
        return 10 ** dec

    def mu_now(self):
        return self._mu_at(self.params, self.t)

    def advance(self, t_target):
        self.t = t_target

    def frame(self):
        mu = self.mu_now()
        a = self._alpha(mu)
        nf = 3 + sum(1 for m in THRESH.values() if mu > m)
        return {"mu": mu, "alpha": a if math.isfinite(a) else None, "nf": nf, "seg": self.seg}, {}

    def engine_modules(self):
        return ["core.qcd.running", "core.qcd.su3", "core.data", "core.quantum.radial", "theories.models.cornell"]

    def header(self):
        return {
            "title": T("QCD: the running coupling and quarkonium"),
            "text": T("The strong coupling α_s runs with the scale: the run solves the renormalisation-group equation "
                      "with the QCD β function (up to four loops) from the world average α_s(M_Z), with the heavy-quark "
                      "thresholds. “Play” sweeps the probe over the scales. On the right: quarkonium in the Cornell "
                      "potential (a model outside the core), its levels from the radial Schrödinger equation against "
                      "the measured ones."),
            "actions": [],
            "modifications": SCHEMA.modifications(self.params),
        }, {}


VIZ = {
    "id": "v06_qcd",
    "title": T("QCD: asymptotic freedom and quarkonium"),
    "summary": T("The running α_s(μ) from {lo} GeV to {hi} TeV by the β function up to four loops (PDG 2024), the "
                 "colour Casimirs, the charmonium and bottomonium spectra in the Cornell model against the measured "
                 "ones.", lo=1, hi=10),
    "purpose": T("How the coupling weakens at short distances, and how a model of quark confinement relates to the "
                 "core of QCD."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
