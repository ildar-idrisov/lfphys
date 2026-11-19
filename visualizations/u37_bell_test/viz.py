# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u37: the Bell test with entangled pairs and real detectors, a wrapper over the physics engine lfphys.

What the run computes (README.md of this folder has the model in full; EX2 design
``lfphys/sources/explore_EX2_2026-11-18_design.md`` §4):
* a Poisson stream of pairs from a source between two stations at distances L_A and L_B; each particle's outcome is
  revealed only when it reaches its station;
* the stations' settings: fixed (a and b) or a random bit per locally defined time slot, chosen τ before the slot
  starts; the space-time relation of every choice to the other side's detection and to the emission
  (lfphys.core.causality);
* the ports by the world's law: the Born rule on the source's state (|Φ+⟩, the singlet or Eberhard's state, of a
  visibility V; lfphys.core.quantum.qubits) or a local model (the polarisation or sign model, or Gisin and Gisin's
  model that exploits the detection loophole; lfphys.theories.alternatives.local_hidden);
* two real detectors per station (lfphys.theories.models.photodetector: efficiency, dark and background counts,
  dead time, timing jitter; by default the Excelitas SPCM-NIR's data-sheet values), coincidences within a window, the
  accidentals' estimate w·N_A·N_B/T;
* CHSH S from the coincidences under the fair-sampling assumption (so named), with and without the accidentals
  subtracted; CH and the CH–Eberhard J from all the trials (slots), which need no fair sampling (lfphys.tools.bell_stats);
* part 4 of the lab («slots»): 10⁹ slots counted from the engine's exact multinomial of the slot outcomes, the
  coincidences from the engine's rates, a few slots shown in time;
* checks: each estimator against the engine's prediction for the same devices and source (z-scores), the bounds 2,
  2√2 and 0, no signalling, the space-time relations against closed forms and the Lorentz matrices.
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
from lfphys.theories.models import photodetector as PD
from lfphys.tools import bell_stats as BS

from .engine.experiment import (F_FREE_A, F_FREE_B, F_LOC_A, F_LOC_B, F_TRUE, MODEL_LABEL, PAIR_LABEL, Law, Slots,
                                Store, Stream)

TSIRELSON = 2.0 * math.sqrt(2.0)
EFFS_BENCH = (0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 1.00)  # part 4's efficiencies
NMIN = 30          # coincidences per cell before an estimate is compared with its reference (normal approximation)
ZTOL = 5.0         # tolerance of the statistical checks, in standard errors
DETAIL = 6         # coincidences sent per step in detail (all enter the statistics; the view needs the newest)
CLICKS = 8         # the latest clicks of each station sent per step (the flashes)
MILESTONES = (100, 1000, 4000, 10000, 100000)  # events «N coincidences counted» (the screens' stop rules)
DEVICE = PD.DEVICES["spcm_nir_800_13"]
DEV = DEVICE["detector"]
JITTER_FWHM_PS = 350.0  # the data sheet's timing resolution, read as FWHM (photodetector.DEVICES)
# Giustina et al. 2015: the state r ≈ −2.9 and their angles a1 = 94.4°, a2 = 62.4°, b1 = −6.5°, b2 = 25.5°; in this
# world's labels the odd setting pair of J (a2, b2) is CHSH's (a, b′): a = a2, a′ = a1, b = b1, b′ = b2
GIUSTINA = {"a_deg": 62.4, "a2_deg": 94.4, "b_deg": -6.5, "b2_deg": 25.5}
CHSH_PHOTON = {"a_deg": 0.0, "a2_deg": 45.0, "b_deg": 22.5, "b2_deg": 67.5}
CHSH_SPIN = {"a_deg": 0.0, "a2_deg": 90.0, "b_deg": 45.0, "b2_deg": 135.0}
# the efficiency thresholds of J (the smallest equal η with J > 0 at the best angles), computed with
# bell_stats.threshold_efficiency for the bench's sources and slots (μ = 0.01, T_s = 1 µs) and checked by
# tests/test_u37_screens.py; keyed by (state, r, dark and background counts per second)
# (NaN: J ≤ 0 at every efficiency)
THRESHOLDS = {("max", -1.0, 0.0): 0.8288688659667969, ("eberhard", -2.9, 0.0): 0.7259254455566406,
              ("max", -1.0, 250.0): 0.8762245178222656, ("eberhard", -2.9, 250.0): 0.9023323059082031,
              ("max", -1.0, 100250.0): math.nan, ("eberhard", -2.9, 100250.0): math.nan}


def _p(*a, **k):
    return Param(*a, **k)


G_WSRC, G_CHOICE = T("Source (world)"), T("Choice of the settings")
G_A, G_B = T("Alice's settings (A)"), T("Bob's settings (B)")
G_DEV, G_SRC = T("Devices"), T("Source")

SCHEMA = Schema([
    _p("pair", T("Pairs"), "select", "photon", group=G_WSRC,
       options=[("photon", T("photons: polarisation, polarisers")),
                ("spin", T("spin ½: singlet (|↑↓⟩ − |↓↑⟩)/√2, Stern–Gerlach magnets"))],
       help=T("The type of the pair sets the state, the analysers and the particles' speed; it changes only with a "
              "new world.")),
    _p("spin_beta", T("Speed of the spin pair's particles, v/c"), "float", 0.5, group=G_WSRC, min=1e-4, max=0.999,
       log=True, show_if={"pair": ["spin"]},
       help=T("Illustrative: massive particles with spin ½ (protons, for example). Photons fly at the speed c.")),
    _p("law", T("Law of the correlations"), "select", "quantum", group=T("Laws (modifications)"), standard="quantum",
       options=[("quantum", T("quantum mechanics: the Born rule for the entangled state")),
                ("lhv", T("local hidden variables (photons: a polarisation model; spin: Bell's sign model)")),
                ("gg", T("Gisin and Gisin's local model: detection depends on the hidden variable"))],
       help=T("Quantum mechanics is the accepted physics. Local hidden variables are a “what if” modification: the "
              "outcome of each side is set by its setting and by a common parameter from the source. Gisin and "
              "Gisin's model also decides by that parameter whether a particle is detected at all.")),
    _p("state", T("State of the source"), "select", "max", group=G_SRC,
       options=[("max", T("maximally entangled: photons |Φ+⟩ = (|HH⟩ + |VV⟩)/√2, spins the singlet")),
                ("eberhard", T("Eberhard's state (|VH⟩ + r|HV⟩)/√(1 + r²) (photons)"), {"pair": ["photon"]})],
       help=T("A weakly entangled state (|r| far from 1) violates the CH–Eberhard inequality with less efficient "
              "detectors than the maximally entangled one.")),
    _p("r", T("Eberhard's parameter r"), "float", -2.9, group=G_SRC, min=-100.0, max=100.0,
       show_if={"state": ["eberhard"]},
       help=T("r = −1: the singlet; Giustina et al. (2015) used r ≈ −2.9.")),
    _p("visibility", T("Visibility of the source V"), "float", 1.0, group=G_SRC, min=0.0, max=1.0,
       help=T("ρ = V|ψ⟩⟨ψ| + (1 − V) I/4: a real source's pairs are partly mixed; every correlation is V times the "
              "pure state's.")),
    _p("rate", T("Pairs per second (world time)"), "float", 1e4, group=G_SRC, min=1.0, max=1e7, log=True, live=True),
    _p("bg_rate", T("Stray light: background counts per second per detector"), "float", 0.0, group=G_SRC, min=0.0,
       max=1e7,
       help=T("Counts of light that does not come from the pairs (room light, fluorescence): a Poisson process like "
              "the dark counts.")),
    _p("L_A_m", T("Distance from the source to Alice's station L_A, m"), "float", 500.0, group=T("Geometry"),
       min=0.01, max=1e5, log=True),
    _p("L_B_m", T("Distance from the source to Bob's station L_B, m"), "float", 500.0, group=T("Geometry"),
       min=0.01, max=1e5, log=True),
    _p("switch", T("Choice of the setting"), "select", "random", group=G_CHOICE,
       options=[("fixed", T("fixed: Alice a, Bob b")),
                ("random", T("random for every time slot (as in loophole-free experiments)"))], live=True),
    _p("tau_ns", T("The choice is made τ before its slot starts, ns"), "float", 100.0, group=G_CHOICE, min=1e-3,
       max=1e7, log=True, show_if={"switch": ["random"]}, live=True,
       help=T("Each station's random number generator gives its bit for the next time slot τ before the slot starts "
              "(the delay of the generator and the switch). The choice is outside the light cone of the detection on "
              "the other side when c(τ + T_s) < L_A + L_B.")),
    _p("eta_A", T("Detection efficiency of Alice's detectors η_A"), "float", DEV.eta, group=G_DEV, min=0.0, max=1.0,
       help=T("The default values of the devices are those of a real detector, the Excelitas SPCM-NIR "
              "(SPCM-800-13) at 800 nm, from its data sheet; η = 1 is an idealisation.")),
    _p("eta_B", T("Detection efficiency of Bob's detectors η_B"), "float", DEV.eta, group=G_DEV, min=0.0, max=1.0),
    _p("dark_rate", T("Dark counts per second of each detector"), "float", DEV.dark_rate, group=G_DEV, min=0.0,
       max=1e7),
    _p("dead_ns", T("Dead time of a detector, ns"), "float", DEV.dead_time * 1e9, group=G_DEV, min=0.0, max=1e5),
    _p("jitter_ps", T("Timing jitter of a detector (FWHM), ps"), "float", JITTER_FWHM_PS, group=G_DEV, min=0.0,
       max=1e6, help=T("A Gaussian of this full width at half maximum (the data sheet's timing resolution).")),
    _p("window_ns", T("Coincidence window w (full width), ns"), "float", 2.0, group=G_DEV, min=0.01, max=1e4,
       log=True),
    _p("slot_ns", T("Time slot T_s, ns"), "float", 1000.0, group=G_DEV, min=10.0, max=1e8, log=True,
       help=T("Each station divides its time into slots on its own clock; a slot is one trial of the CH and J "
              "inequalities.")),
    _p("counting", T("How the run counts"), "select", "stream", group=G_DEV,
       options=[("stream", T("every pair in time")),
                ("slots", T("10⁹ slots: the counts from the exact probabilities, a few slots shown in time"))],
       help=T("“every pair in time” follows each pair, detection and coincidence; “10⁹ slots” draws the counts of "
              "many slots at once from the engine's exact probabilities (needed for CH and J, whose violation per "
              "slot is small), and shows only a few slots in time.")),
    _p("a_deg", T("Alice: setting a, °"), "float", 0.0, group=G_A, min=-360, max=360, live=True),
    _p("a2_deg", T("Alice: setting a′, °"), "float", 45.0, group=G_A, min=-360, max=360, live=True),
    _p("b_deg", T("Bob: setting b, °"), "float", 22.5, group=G_B, min=-360, max=360, live=True),
    _p("b2_deg", T("Bob: setting b′, °"), "float", 67.5, group=G_B, min=-360, max=360, live=True),
], presets={
    "photon_chsh": {"label": T("Photons |Φ+⟩, quantum mechanics: optimal CHSH angles {a}°, {a2}° / {b}°, {b2}°, random "
                               "choice", a=0, a2=45, b=22.5, b2=67.5), "params": {}},
    "spin_chsh": {"label": T("Spin-½ singlet, quantum mechanics: optimal angles {a}°, {a2}° / {b}°, {b2}°, random "
                             "choice", a=0, a2=90, b=45, b2=135), "params": {"pair": "spin", **CHSH_SPIN}},
    "photon_lhv": {"label": T("Photons, local hidden variables: a polarisation model (modification)"),
                   "params": {"law": "lhv"}},
    "spin_lhv": {"label": T("Spin-½ singlet, local hidden variables: Bell's sign model (modification)"),
                 "params": {"pair": "spin", "law": "lhv", **CHSH_SPIN}},
    "scan": {"label": T("The curve E(Δ): photons, fixed settings a = b = {a}°; move b", a=0),
             "params": {"switch": "fixed", "a_deg": 0.0, "b_deg": 0.0}},
    "photon_slow_choice": {"label": T("Photons: the choice made {tau} µs before its slot (cτ > L_A + L_B), the "
                                      "locality loophole is open", tau=5),
                           "params": {"tau_ns": 5000.0}},
    "real_source": {"label": T("Photons from a real source of visibility V = {v}", v=0.85),
                    "params": {"visibility": 0.85}},
    "detectors": {"label": T("10⁹ slots: |Φ+⟩ at the CHSH angles, CHSH from the coincidences beside CH and J"),
                  "params": {"counting": "slots"}},
    "giustina": {"label": T("10⁹ slots: Eberhard's state r = {r} at Giustina's angles and efficiencies ({ea} %, {eb} %)",
                            r=-2.9, ea=78.6, eb=76.2),
                 "params": {"counting": "slots", "state": "eberhard", "r": -2.9, "eta_A": 0.786, "eta_B": 0.762,
                            **GIUSTINA}},
    "gisin": {"label": T("10⁹ slots: Gisin and Gisin's local model at the CHSH angles (modification)"),
              "params": {"counting": "slots", "law": "gg"}},
    "ideal_detectors": {"label": T("Ideal detectors (an idealisation): η = 1, no dark counts, no dead time, no "
                                   "jitter"),
                        "params": {"eta_A": 1.0, "eta_B": 1.0, "dark_rate": 0.0, "dead_ns": 0.0, "jitter_ps": 0.0}},
})

ANGLES = ("a_deg", "a2_deg", "b_deg", "b2_deg")
G_ST = T("Spacetime: the choice of a setting and the detection")
G_LAW = T("Set-up: the expectation of the world's law (exact)")
G_STAT = T("Statistics of the coincidences: measured ↔ the engine's prediction for these devices")
G_SLOT = T("All the trials (slots): CH and J, no fair sampling")
G_DEVS = T("The detectors and the coincidence window")

#: the frame's measurables (the screens' readouts and the lab's instruments; EX2 §5 F4, F7)
MEASURABLES = [
    {"id": "n_pp", "label": T("N₊₊ of (a, b)"), "unit": ""},
    {"id": "n_pm", "label": T("N₊₋ of (a, b)"), "unit": ""},
    {"id": "n_mp", "label": T("N₋₊ of (a, b)"), "unit": ""},
    {"id": "n_mm", "label": T("N₋₋ of (a, b)"), "unit": ""},
    {"id": "E_ab", "label": T("E(a, b)"), "unit": "", "sigma": "E_ab_se", "ref": "E_ab_ref",
     "ref_label": T("the law")},
    {"id": "E_ab2", "label": T("E(a, b′)"), "unit": "", "sigma": "E_ab2_se", "ref": "E_ab2_ref",
     "ref_label": T("the law")},
    {"id": "E_a2b", "label": T("E(a′, b)"), "unit": "", "sigma": "E_a2b_se", "ref": "E_a2b_ref",
     "ref_label": T("the law")},
    {"id": "E_a2b2", "label": T("E(a′, b′)"), "unit": "", "sigma": "E_a2b2_se", "ref": "E_a2b2_ref",
     "ref_label": T("the law")},
    {"id": "E_ab_se", "label": T("Standard error of E(a, b)"), "unit": ""},
    {"id": "E_ab2_se", "label": T("Standard error of E(a, b′)"), "unit": ""},
    {"id": "E_a2b_se", "label": T("Standard error of E(a′, b)"), "unit": ""},
    {"id": "E_a2b2_se", "label": T("Standard error of E(a′, b′)"), "unit": ""},
    {"id": "E_ab_ref", "label": T("E(a, b) of the law"), "unit": ""},
    {"id": "E_ab2_ref", "label": T("E(a, b′) of the law"), "unit": ""},
    {"id": "E_a2b_ref", "label": T("E(a′, b) of the law"), "unit": ""},
    {"id": "E_a2b2_ref", "label": T("E(a′, b′) of the law"), "unit": ""},
    {"id": "S", "label": T("S (fair sampling)"), "unit": "", "sigma": "S_se", "ref": "S_law",
     "ref_label": T("the law")},
    {"id": "S_se", "label": T("Standard error of S"), "unit": ""},
    {"id": "S_law", "label": T("S of the world's law and source"), "unit": ""},
    {"id": "excess", "label": T("(|S| − 2)/σ"), "unit": "σ"},
    {"id": "S_sub", "label": T("S with the accidentals subtracted"), "unit": "", "sigma": "S_sub_se"},
    {"id": "S_sub_se", "label": T("Standard error of S with the accidentals subtracted"), "unit": ""},
    {"id": "coinc", "label": T("Coincidences counted"), "unit": ""},
    {"id": "acc_est", "label": T("Accidental coincidences, estimate w·N_A·N_B/T"), "unit": ""},
    {"id": "singles_A", "label": T("Singles of Alice's detectors"), "unit": ""},
    {"id": "singles_B", "label": T("Singles of Bob's detectors"), "unit": ""},
    {"id": "herald", "label": T("Coincidences per single, C/√(N_A·N_B)"), "unit": ""},
    {"id": "local_frac", "label": T("Coincidences with both choices outside the other side's light cone"),
     "unit": ""},
    {"id": "trials", "label": T("Trials (slots) counted"), "unit": ""},
    {"id": "J", "label": T("J per slot (CH–Eberhard)"), "unit": "", "sigma": "J_se", "ref": "J_ref",
     "ref_label": T("the engine")},
    {"id": "J_se", "label": T("Standard error of J per slot"), "unit": ""},
    {"id": "J_ref", "label": T("J per slot predicted by the engine"), "unit": ""},
    {"id": "J_pair", "label": T("J per pair, J/μ"), "unit": "", "sigma": "J_pair_se"},
    {"id": "J_pair_se", "label": T("Standard error of J per pair"), "unit": ""},
    {"id": "CH", "label": T("CH per slot (Gisin and Gisin's form)"), "unit": "", "sigma": "CH_se", "ref": "CH_ref",
     "ref_label": T("the engine")},
    {"id": "CH_se", "label": T("Standard error of CH per slot"), "unit": ""},
    {"id": "CH_ref", "label": T("CH per slot predicted by the engine"), "unit": ""},
]
CELL_NAMES = ("ab", "ab2", "a2b", "a2b2")


class Simulation(BaseSimulation):
    speed_range = (1e-12, 1e4)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = dict(params)
        P = self.params
        self.law = Law(P["pair"], P["law"], P["state"] if P["pair"] == "photon" else "max", P["r"], P["visibility"])
        self.v = C if P["pair"] == "photon" else float(P["spin_beta"]) * C
        self.slots_mode = P["counting"] == "slots"
        self.store = Store()
        if self.slots_mode:
            self.counter = Slots(self.law, self._si(), self.rng, seed, self.v)
        else:
            self.counter = Stream(self.law, self.v, C, self._si(), self.rng, seed)
        self.seg = 0
        self.seg_counts = dict(coinc=0, loc=0, free=0, true=0)
        self.n_checked = 0
        self._next_slot_check = 1000
        self.said = set()
        self._buf = []
        self._exp_cache: dict = {}
        self.default_speed = 100.0 if self.slots_mode else \
            min(max(max(P["L_A_m"], P["L_B_m"]) / self.v / 2.0, self.speed_range[0]), self.speed_range[1])
        self._engine_checks()
        self._setup_checks()
        self._device_checks()
        self._spacetime_checks()
        self._stat_checks()

    # --- the parameters in SI units ------------------------------------------------------------------------------
    def _si(self, params=None) -> dict:
        P = params or self.params
        return dict(eta_A=float(P["eta_A"]), eta_B=float(P["eta_B"]), dark=float(P["dark_rate"]) + float(P["bg_rate"]),
                    dead=float(P["dead_ns"]) * 1e-9, sigma=float(P["jitter_ps"]) * 1e-12 * PD.FWHM_TO_SIGMA,
                    w=float(P["window_ns"]) * 1e-9, Ts=float(P["slot_ns"]) * 1e-9, tau=float(P["tau_ns"]) * 1e-9,
                    L_A=float(P["L_A_m"]), L_B=float(P["L_B_m"]), rate=float(P["rate"]), switch=P["switch"],
                    a_deg=float(P["a_deg"]), a2_deg=float(P["a2_deg"]), b_deg=float(P["b_deg"]),
                    b2_deg=float(P["b2_deg"]))

    @classmethod
    def check_params(cls, params):
        local = params["law"] != "quantum"
        if local and float(params["L_A_m"]) != float(params["L_B_m"]):
            raise Refusal(T("The engine's local models give the two outcomes of a pair together, so both particles must "
                            "arrive at the same moment"), T("set L_A = L_B for a local model"))
        if params["pair"] == "spin" and params["state"] == "eberhard":
            raise Refusal(T("Eberhard's state is a state of two photons' polarisations"),
                          T("choose photons, or the maximally entangled state"))
        if local and (params["state"] != "max" or float(params["visibility"]) != 1.0):
            raise Refusal(T("A local model has no quantum state: its source has no Eberhard parameter and no "
                            "visibility"), T("choose the maximally entangled state and V = 1, or quantum mechanics"))
        if params["counting"] == "slots" and params["law"] == "lhv":
            raise Refusal(T("The counting by slots is built for quantum mechanics and Gisin and Gisin's model"),
                          T("count every pair in time for this local model"))
        P = {k: float(params[k]) for k in ("dead_ns", "jitter_ps", "slot_ns")}
        coupling = PD.slot_coupling(P["dead_ns"] * 1e-9, P["jitter_ps"] * 1e-12 * PD.FWHM_TO_SIGMA,
                                    P["slot_ns"] * 1e-9)
        if params["counting"] == "slots" and coupling > 0.1:
            raise Refusal(T("The counting by slots treats the slots as independent trials, which needs the dead time "
                            "and the jitter far below a slot: (t_d + 5σ)/T_s = {x:.3g}", x=coupling),
                          T("lengthen the slot, or count every pair in time"))
        mu = float(params["rate"]) * float(params["slot_ns"]) * 1e-9
        if params["counting"] == "slots" and mu > 1.0:
            raise Refusal(T("{mu:.3g} pairs per slot on average: a slot is no longer a trial of one pair", mu=mu),
                          T("lower the rate or shorten the slot"))

    @classmethod
    def lab_reference(cls, step_id, fixed, values, reference):
        """The world's computed values for the bench (EX2 §5 F6 (d)): the slopes of the linearised laws, computed with
        the world's own law (the engine's trace) at an angle away from the zeros of the abscissa."""
        ph, sp = Law("photon", "quantum"), Law("spin", "quantum")
        how_q = T("the engine's trace Tr(ρ A⊗B) of the source's state, divided by the abscissa")
        if reference == "slope_photons":
            return {"value": ph.E(0.0, 30.0) / math.cos(math.radians(60.0)), "unit": "",
                    "label": T("E = V cos 2(β − α), |Φ+⟩, V = 1"), "how": how_q, "kind": "engine"}
        if reference == "slope_spins" and step_id == "correlation":
            return {"value": sp.E(0.0, 30.0) / math.cos(math.radians(30.0)), "unit": "",
                    "label": T("E = −cos(β − α), the singlet"), "how": how_q, "kind": "engine"}
        d = 22.5
        x_ph = 3 * math.cos(math.radians(2 * d)) - math.cos(math.radians(6 * d))
        if reference == "slope_quantum":
            return {"value": ph.S(0.0, 2 * d, d, 3 * d) / x_ph, "unit": "", "label": T("S = 3 cos 2Δ − cos 6Δ, |Φ+⟩"),
                    "how": how_q, "kind": "engine"}
        if reference == "slope_visibility":
            v = Law("photon", "quantum", V=0.85)
            return {"value": v.S(0.0, 2 * d, d, 3 * d) / x_ph, "unit": "",
                    "label": T("S = V(3 cos 2Δ − cos 6Δ), V = 0.85"), "how": how_q, "kind": "engine"}
        if reference == "slope_spins":
            ds = 45.0
            x_sp = -(3 * math.cos(math.radians(ds)) - math.cos(math.radians(3 * ds)))
            return {"value": sp.S(0.0, 2 * ds, ds, 3 * ds) / x_sp, "unit": "",
                    "label": T("S = −(3 cos Δ − cos 3Δ), the singlet"), "how": how_q, "kind": "engine"}
        if reference == "slope_local":
            h = Law("photon", "lhv")
            return {"value": h.S(0.0, 2 * d, d, 3 * d) / x_ph, "unit": "",
                    "label": T("S = ½(3 cos 2Δ − cos 6Δ), the polarisation model"),
                    "how": T("the engine's E of the model, ½ cos 2(α − β)"), "kind": "engine"}
        if reference in ("j_slope", "j_intercept"):
            # J per pair of |Φ+⟩ at the CHSH angles without dark counts, at the bench's μ = R·T_s and efficiencies: the
            # engine's slot probabilities (one pair per trial it is η² (1 + √2)/2 − η; the Poisson pairs lower it
            # slightly); J/η against η fitted by a straight line through the bench's seven efficiencies
            mu = 1e4 * 1e-6

            def jp(e):
                return BS.j_value([[ph.slot_table(A, B, e, e, 0.0, 0.0, mu) for B in (22.5, 67.5)]
                                   for A in (45.0, 0.0)]) / mu
            etas = np.array(EFFS_BENCH)
            slope, icpt = np.polyfit(etas, np.array([jp(float(e)) / e for e in etas]), 1)
            how = T("bell_stats.slot_probabilities of the stations, μ = 0.01 pairs per slot, no dark counts, at the "
                    "bench's efficiencies; one pair per trial would give (1 + √2)/2 and −1")
            if reference == "j_slope":
                return {"value": float(slope), "unit": "", "label": T("J/η = a + b·η: the slope b"), "how": how,
                        "kind": "engine"}
            return {"value": float(icpt), "unit": "", "label": T("J/η = a + b·η: the intercept a"), "how": how,
                    "kind": "engine"}
        raise ValueError(T("no law for the step {step}", step=step_id))

    def engine_modules(self):
        mods = ["core.constants", "core.quantum.qubits", "core.causality", "core.relativity", "tools.bell_stats",
                "theories.models.photodetector"]
        if self.law.law != "quantum":
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
                 "help": T("The counts start anew; the set-up and the pairs in flight stay the same."), "args": []}]

    # --- the cells ------------------------------------------------------------------------------------------
    def _cell_angles(self):
        P = self.params
        return [("a", "b", P["a_deg"], P["b_deg"]), ("a", "b′", P["a_deg"], P["b2_deg"]),
                ("a′", "b", P["a2_deg"], P["b_deg"]), ("a′", "b′", P["a2_deg"], P["b2_deg"])]

    def _devices(self, side):
        S = self._si()
        return PD.Detector(eta=S["eta_A"] if side == "A" else S["eta_B"], dark_rate=S["dark"], dead_time=S["dead"],
                           jitter_sigma=S["sigma"])

    def _expect(self, a, b) -> dict:
        """The engine's prediction for a pair of analyser angles with these devices and source: the rates of the
        true and the accidental coincidences of each detector pair (``photodetector.coincidence_rates``: η, the
        live fractions, the window's share of the jittered pairs, w·m_A·m_B) and so E of the coincidences, with and
        without the accidentals; the singles; the slot's outcome table (``Law.slot_table``)."""
        key = (round(a, 9), round(b, 9))
        if key in self._exp_cache:
            return self._exp_cache[key]
        S = self._si()
        dA, dB = self._devices("A"), self._devices("B")
        r = PD.coincidence_rates(S["rate"], self.law.port_table(a, b), [dA, dA], [dB, dB], S["w"])
        tr = r["true"][:2, :2].ravel()  # (a port without a detector, Gisin and Gisin's «no outcome», is not filled)
        tot = tr + r["accidental"].ravel()
        sg = np.array([1.0, -1.0, -1.0, 1.0])
        out = {"E": float(np.sum(sg * tot) / np.sum(tot)) if np.sum(tot) > 0 else 0.0,
               "E_true": float(np.sum(sg * tr) / np.sum(tr)) if np.sum(tr) > 0 else 0.0,
               "rate": float(np.sum(tot)), "true": tr, "acc": r["accidental"].ravel(),
               "singles_a": r["singles_a"], "singles_b": r["singles_b"]}
        self._exp_cache[key] = out
        return out

    def _slot_expect(self, a, b) -> np.ndarray:
        S = self._si()
        pd = PD.dark_click_probability(S["dark"], S["Ts"])
        return self.law.slot_table(a, b, S["eta_A"], S["eta_B"], pd, pd, S["rate"] * S["Ts"])

    def _cells(self):
        out = []
        for x, y, al, be in self._cell_angles():
            n = self.store.get(al, be)
            E, se, N = BS.correlation(n)
            ex = self._expect(al, be)
            Eref = ex["E"]
            # the error under the prediction, floored at the step one count makes (2/N): near |E| = 1 the rarer
            # outcomes are a few counts and the normal approximation's error vanishes
            z = BS.zscore(E, Eref, max(BS.se_under(Eref, N), 2.0 / N)) if N else None
            out.append({"x": x, "y": y, "alA": al, "alB": be, "n": [int(q) for q in n],
                        "acc": [int(q) for q in self.store.get_acc(al, be)], "N": N, "E": E, "se": se, "Eexp": Eref,
                        "Elaw": self.law.E(al, be), "z": z})
        return out

    def _S(self, cells):
        """S of the four cells and its error. With coinciding settings (a' = a or b' = b) two cells are the same
        angle pair, i.e. the same counts (Store keys by angle pair): the error counts them once (bell_stats.chsh with
        keys; review 2026-10-23, V7-2) and ``same`` lists the coinciding cells."""
        keys = [Store.key(c["alA"], c["alB"]) for c in cells]
        same = [f"({c['x']},{c['y']})" for k, c in enumerate(cells) if keys.index(keys[k]) != k]
        Sexp = sum(s * c["Eexp"] for s, c in zip(BS.CHSH_SIGNS, cells))
        Slaw = sum(s * c["Elaw"] for s, c in zip(BS.CHSH_SIGNS, cells))
        S, se = BS.chsh([c["n"] for c in cells], keys=keys)
        base = {"Sexp": Sexp, "Slaw": Slaw, "Nmin": min(c["N"] for c in cells), "same": same}
        if S is None:
            return {**base, "S": None, "se": None, "z": None, "excess": None}
        seu = BS.chsh_se_under([c["Eexp"] for c in cells], [c["N"] for c in cells], keys=keys)
        # a floor of one count of the rarer outcome per cell (2/N), with the largest weight a cell has in S (2)
        floor = 2.0 * math.sqrt(sum((2.0 / c["N"]) ** 2 for c in self._distinct(cells)))
        excess = (abs(S) - 2.0) / se if se and se > 0 else None
        return {**base, "S": S, "se": se, "z": BS.zscore(S, Sexp, max(seu, floor)), "excess": excess,
                "se_floor": max(seu, floor)}

    def _accidentals(self, al, be) -> tuple[np.ndarray, np.ndarray]:
        """The accidentals' estimate of a cell, per detector pair (N++, N+−, N−+, N−−): Dehlinger and Mitchell's
        w·N_A·N_B/T (``bell_stats.accidentals``) with the singles of each station counted while its angle was in
        force (time t_A, t_B) and T = t_A·t_B/t_AB, t_AB the time both angles were in force together (with
        independent random settings T is the run's time); its error from the singles' Poisson errors."""
        S = self._si()
        nA, nB = self.store.get_singles("A", al), self.store.get_singles("B", be)
        tA, tB = self.store.get_time("A", al), self.store.get_time("B", be)
        tAB = float(self.store.get_slots(al, be).sum()) * S["Ts"]
        if tA <= 0 or tB <= 0 or tAB <= 0:
            return np.zeros(4), np.zeros(4)
        acc = BS.accidentals(nA, nB, S["w"], tA * tB / tAB).ravel()
        with np.errstate(divide="ignore", invalid="ignore"):
            rel = np.sqrt(np.where(np.outer(nA, nB).ravel() > 0,
                                   (1.0 / np.maximum(np.repeat(nA, 2), 1)) + (1.0 / np.maximum(np.tile(nB, 2), 1)), 0.0))
        return acc, acc * rel

    def _S_sub(self, cells):
        keys = [Store.key(c["alA"], c["alB"]) for c in cells]
        accs, ses = [], []
        for c in cells:
            a, s = self._accidentals(c["alA"], c["alB"])
            accs.append(a)
            ses.append(s)
        if min(c["N"] for c in cells) == 0:
            return None, None, accs
        S, se = BS.chsh_subtracted([c["n"] for c in cells], accs, ses, keys=keys)
        return S, se, accs

    def _j_tables(self):
        """The four cells' trial tables in bell_stats's order of J and CH: index 0 = a′ (A) and b (B), index 1 = a and
        b′ (the odd setting pair of J, (a2, b2), is CHSH's (a, b′))."""
        P = self.params
        A = (P["a2_deg"], P["a_deg"])
        B = (P["b_deg"], P["b2_deg"])
        meas = [[self.store.get_slots(A[i], B[j]) for j in (0, 1)] for i in (0, 1)]
        exp = [[self._slot_expect(A[i], B[j]) for j in (0, 1)] for i in (0, 1)]
        return meas, exp

    def _J(self):
        meas, exp = self._j_tables()
        n = min(int(np.sum(meas[i][j])) for i in (0, 1) for j in (0, 1))
        J, Jse = BS.j_estimate(meas) if n > 0 else (None, None)
        CH, CHse = BS.ch_estimate(meas) if n > 0 else (None, None)
        mu = self._si()["rate"] * self._si()["Ts"]
        return {"J": J, "se": Jse, "Jexp": BS.j_value(exp), "CH": CH, "CHse": CHse, "CHexp": BS.ch_value(exp),
                "mu": mu, "n": n, "trials": int(sum(np.sum(meas[i][j]) for i in (0, 1) for j in (0, 1)))}

    def _points(self):
        """All measured angle pairs: delta, E, se, N, E predicted for these devices (the E(delta) plot and its χ²)."""
        rows = []
        for (al, be), n in self.store.coinc.items():
            E, se, N = BS.correlation(n)
            if N == 0:
                continue
            rows.append((float(self.law.fold(al - be)) if hasattr(self.law, "fold") else float(al - be), E, se, N,
                         self._expect(al, be)["E"]))
        return np.array(rows, float) if rows else np.zeros((0, 5))

    # --- checks: the law and the set-up ---------------------------------------------------------------------
    def _engine_checks(self):
        """Once per world: properties of the source state computed by the engine."""
        g = T("Source: the state of the pair")
        law, P = self.law, self.params
        if law.law == "quantum":
            rho = law.rho
            V = law.V
            if law.state == "max":
                ref, note = max(0.0, (3.0 * V - 1.0) / 2.0), T("reference: (3V − 1)/2 for a Werner mixture of a "
                                                              "maximally entangled state (1 at V = 1)")
            elif V == 1.0:
                ref, note = 2 * abs(law.r) / (1 + law.r ** 2), T("reference: 2|r|/(1 + r²) for Eberhard's state")
            else:
                ref, note = None, T("a Werner mixture of Eberhard's state: computed by the engine (no closed form here)")
            self._check("conc", T("Entanglement of the state: Wootters' concurrence"), Q.concurrence(rho), ref, "", g,
                        tol=1e-6, note=note)
            ent = Q.entropy(Q.ptrace(rho, 0))
            if law.state == "max":
                self._check("ent", T("Entropy of one particle of the pair (bits)"), ent, 1.0, "", g, tol=1e-9,
                            note=T("a particle on its own is completely unpolarised: its marginals are 1/2 at any "
                                   "setting"))
            else:
                p = 1.0 / (1.0 + law.r ** 2)
                h = -(p * math.log2(p) + (1 - p) * math.log2(1 - p)) if 0 < p < 1 else 0.0
                self._check("ent", T("Entropy of one particle of the pair (bits)"), ent, h if V == 1.0 else None, "",
                            g, tol=1e-9, note=T("reference: the binary entropy of 1/(1 + r²) for Eberhard's state"))
        else:
            self._check("conc", T("Source by the local model: a common hidden parameter λ, no quantum state"), None,
                        None, "", g, note=T("{model}: the outcome of a side is a function of its setting and λ (local "
                                            "by construction)", model=MODEL_LABEL[law.model]))

    def _setup_checks(self):
        """After every change of the settings: the exact expectation of the world's law."""
        law, P = self.law, self.params
        a, a2, b, b2 = (P[k] for k in ANGLES)
        g = G_LAW
        S_law = law.S(a, a2, b, b2)
        if law.law == "quantum":
            S_cf = sum(s * law.E_closed_form(x, y) for s, (_, _, x, y) in zip(BS.CHSH_SIGNS, self._cell_angles()))
            self._check("S_law", T("S at the current settings: the engine's trace Tr(ρ A⊗B)"), S_law, S_cf, "", g,
                        tol=1e-12, ok=abs(S_law - S_cf) < 1e-12, note=T("reference: the closed form E = V cos 2(α_A − α_B) for |Φ+⟩; S = E(a,b) − "
                                          "E(a,b′) + E(a′,b) + E(a′,b′)") if law.pair == "photon" and law.state == "max"
                        else T("reference: the closed form E = V(−cos 2α cos 2β + 2r/(1 + r²) sin 2α sin 2β) for "
                               "Eberhard's state") if law.state == "eberhard" else
                        T("reference: the closed form E = −V cos(θ_A − θ_B) for the singlet; S = E(a,b) − E(a,b′) + "
                          "E(a′,b) + E(a′,b′)"))
            mA = [abs(law.port_table(x, b)[0].sum() - law.port_table(x, b2)[0].sum()) for x in (a, a2)]
            mB = [abs(law.port_table(a, y)[:, 0].sum() - law.port_table(a2, y)[:, 0].sum()) for y in (b, b2)]
            dmax = max(mA + mB)
            self._check("nosig_law", T("No signalling in the law (exact): the marginal of one side against the setting "
                                       "of the other"),
                        dmax, 0.0, "", g, ok=dmax < 1e-14,
                        note=T("max |P_A(+|x,b) − P_A(+|x,b′)|, |P_B(+|a,y) − P_B(+|a′,y)| from the joint Born "
                               "probabilities Tr(ρ Π⊗Π)"))
        else:
            self._check("S_law", T("S at the current settings by the local model"), S_law, None, "", g,
                        note=T("{model}: E is a function of the engine's model, {formula}", model=MODEL_LABEL[law.model],
                               formula="½cos 2(α_A − α_B)" if law.law == "lhv" and law.pair == "photon" else
                               ("−1 + 2θ/π" if law.law == "lhv" else
                                ("cos 2(α_A − α_B)" if law.pair == "photon" else "−cos(θ_A − θ_B)"))))
            self._check("nosig_law", T("No signalling in the law of the local model: by construction (for "
                                       "information)"), 0.5, None, "", g, info=True,
                        note=T("the outcome of each side is a function of its setting and λ only (local by "
                               "construction), and λ is distributed isotropically: P(+) does not depend on the "
                               "setting of the other side. This is an identity of the model, not a check; the check "
                               "by the run's counts is in the group “No signalling”"))
        if law.law == "quantum":
            self._check("tsir_law", T("Expectation of the law: |S| ≤ 2√2 (the Tsirelson bound)"), abs(S_law),
                        TSIRELSON, "", g, ok=abs(S_law) <= TSIRELSON + 1e-12, note=T("no quantum theory gives more"))
        else:
            self._check("tsir_law", T("Expectation of the local model and the Tsirelson bound 2√2 (for information)"),
                        abs(S_law), TSIRELSON, "", g, info=True,
                        note=T("of the pairs detected at both sides: not a separate check"))
        bound_ok = abs(S_law) <= 2.0 + 1e-12
        if law.law == "lhv":
            self._check("chsh_law", T("Expectation of the local model: |S| ≤ 2 (the CHSH bound)"), abs(S_law), 2.0,
                        "", g, ok=bound_ok, note=T("every local model must keep this bound"))
        elif law.law == "gg":
            self._check("chsh_law", T("Gisin and Gisin's model: |S| of the detected pairs and the classical bound 2"),
                        abs(S_law), None, "", g,
                        note=T("a local model above 2 under fair sampling: only the pairs detected at both sides are "
                               "counted, and the model decides by λ which of them are detected (the detection "
                               "loophole); CH and J of all the trials stay ≤ 0") if not bound_ok else
                        T("at these settings the detected pairs give |S| ≤ 2"))
        else:  # information, not a test: quantum mechanics may exceed 2
            self._check("chsh_law", T("Quantum expectation |S| and the classical bound 2"), abs(S_law), None, "", g,
                        note=T("exceeds 2: quantum mechanics violates the CHSH inequality at these settings")
                        if not bound_ok else T("at these settings the quantum expectation does not exceed 2"))
        self._S_law = S_law
        self._exp_cache = {}

    def _device_identity(self):
        P = self.params
        vals = (P["eta_A"], P["eta_B"], P["dark_rate"], P["dead_ns"], P["jitter_ps"])
        if vals == (DEV.eta, DEV.eta, DEV.dark_rate, DEV.dead_time * 1e9, JITTER_FWHM_PS):
            return T("{title}: its data-sheet values ({values})", title=DEVICE["title"], values=DEVICE["values"])
        if vals == (1.0, 1.0, 0.0, 0.0, 0.0):
            return T("ideal detectors: η = 1, no dark counts, no dead time, no jitter (an idealisation)")
        return T("detectors of the values set here (the default values are those of {title})", title=DEVICE["title"])

    def _device_checks(self):
        """Once per world: the detectors and the slots against their closed forms."""
        S, g = self._si(), G_DEVS
        self._check("devices", T("The detectors"), None, None, "", g, note=self._device_identity())
        coupling = PD.slot_coupling(S["dead"], S["sigma"], S["Ts"])
        self._check("slot_coupling", T("Independent slots: (t_d + 5σ)/T_s ≪ 1"), coupling, None, "", g,
                    ok=coupling < 0.1,
                    note=T("t_d = {td:.3g} ns, σ = {sg:.3g} ps, T_s = {ts:.4g} ns: a count can reach into the next slot "
                           "only within this fraction of a slot; the slots are treated as independent trials below "
                           "0.1", td=S["dead"] * 1e9, sg=S["sigma"] * 1e12, ts=S["Ts"] * 1e9))
        share = PD.window_share(S["w"], S["sigma"], S["sigma"])
        self._check("window_cf", T("Share of a pair's two clicks inside the window, erf(w/(4σ))"), share, None, "", g,
                    note=T("w = {w:.3g} ns, σ = {sg:.3g} ps per detector (closed form of the Gaussian jitter)",
                           w=S["w"] * 1e9, sg=S["sigma"] * 1e12))
        mu = S["rate"] * S["Ts"]
        self._check("mu", T("Pairs per slot μ = R·T_s"), mu, None, "", g,
                    note=T("a Poisson number of pairs per slot: two or more in {p:.3g} of the slots",
                           p=float(1 - math.exp(-mu) * (1 + mu))))
        th = self._threshold()
        if th is not None and math.isnan(th):
            self._check("threshold", T("The efficiency needed for J > 0 with this state and background"), None, None,
                        "", g, note=T("none: with this background no efficiency gives J > 0 at any analyser angles "
                                      "(computed by bell_stats.threshold_efficiency)"))
        elif th is not None:
            eta = min(S["eta_A"], S["eta_B"])
            self._check("threshold", T("The efficiency needed for J > 0 with this state and background"), th, None, "",
                        g, note=T("the smallest equal η at which some analyser angles give J > 0 (computed by "
                                  "bell_stats.threshold_efficiency); here η = {eta:.4g}: {verdict}", eta=eta,
                                  verdict=T("above the threshold") if eta > th else T("below the threshold")))

    def _threshold(self):
        P = self.params
        if self.law.law != "quantum" or P["visibility"] != 1.0 or P["pair"] != "photon":
            return None
        key = (P["state"], -1.0 if P["state"] == "max" else float(P["r"]), float(P["dark_rate"]) + float(P["bg_rate"]))
        if float(P["rate"]) * float(P["slot_ns"]) * 1e-9 != 0.01 or float(P["slot_ns"]) != 1000.0:
            return None
        return THRESHOLDS.get(key)

    def _spacetime_checks(self):
        """The space-time relation of the setting choices for a pair emitted now (nominal geometry): the latest
        detection in a slot, c(τ + T_s) after the choice."""
        S = self._si()
        LA, LB, c, v = S["L_A"], S["L_B"], C, self.v
        g = G_ST
        te = 0.0
        tB = LB / v
        detB = (tB, LB)
        em = (te, 0.0)
        if S["switch"] == "random":
            tau, Ts = S["tau"], S["Ts"]
            lead = tau + Ts  # the latest detection in a slot comes τ + T_s after the choice
            chA = (tB - lead, -LA)
            s2 = K.interval(chA, detB, c)
            rel = K.relation(chA, detB, c)
            txt = {K.SPACELIKE: T("space-like: the locality loophole is closed"),
                   K.TIMELIKE: T("time-like: the locality loophole is OPEN"),
                   K.LIGHTLIKE: T("light-like (on the boundary of the cone)")}[rel]
            note = (T("s² = c²(τ + T_s)² − (L_A + L_B)², c(τ + T_s) = {ct:.4g} m, L_A + L_B = {L2:.4g} m: a signal "
                      "from the choice at A cannot reach the detection at B in time; reference: the closed form",
                      ct=c * lead, L2=LA + LB) if rel == K.SPACELIKE else
                    T("s² = c²(τ + T_s)² − (L_A + L_B)², c(τ + T_s) = {ct:.4g} m, L_A + L_B = {L2:.4g} m: a signal "
                      "from the choice at A can reach the detection at B in time; reference: the closed form",
                      ct=c * lead, L2=LA + LB))
            self._check("st_loc", T("Choice at A ↔ the latest detection at B in its slot: {rel}", rel=txt), s2,
                        (c * lead) ** 2 - (LA + LB) ** 2, T("m²"), g, tol=1e-9, note=note)
            if rel == K.SPACELIKE:
                beta = K.order_reversal_speed(chA, detB, c)
                self._check("st_rev", T("The order “choice at A → detection at B” reverses in a frame moving from A to B "
                                        "faster than v*; v*/c ="), beta, _reversal_by_boosts(chA, detB), "", g,
                            tol=1e-9,
                            note=T("v* = c²Δt/Δx < c: the time between the events is not absolute, there is no causal "
                                   "link; reference: the zero of Δt′ found with the Lorentz matrices "
                                   "(lfphys.core.relativity.boost_matrix)"))
            else:
                self._check("st_rev", T("The order “choice at A → detection at B” is absolute (time-like events)"),
                            None, None, "", g, note=T("it reverses in no inertial frame"))
            tA_arr = LA / v
            chA_first = (tA_arr - tau, -LA)  # a choice made τ before the slot in which the particle arrives at once
            s2e = K.interval(chA_first, em, c)
            rel_e = K.relation(chA_first, em, c)
            before = tA_arr - tau < te
            txe = {K.SPACELIKE: T("space-like: the choice and the source are independent"),
                   K.TIMELIKE: (T("the choice is in the past cone of the emission: a signal from the choice reaches the "
                                  "source in time")
                                if before else T("the choice is in the future cone of the emission: the "
                                                 "freedom-of-choice loophole is open")),
                   K.LIGHTLIKE: T("light-like")}[rel_e]
            self._check("st_free", T("Choice at A ↔ emission of the pair: {rel}", rel=txe), s2e,
                        (c * (tA_arr - tau - te)) ** 2 - LA ** 2, T("m²"), g, tol=1e-9,
                        note=T("s² = c²(L_A/v − τ)² − L_A², a particle arriving at the start of its slot; the flight "
                               "time L_A/v = {tf:.4g} s, τ = {tau:.4g} s", tf=LA / v, tau=tau))
        else:
            tA, xA = self.counter.t_set["A"] if not self.slots_mode else (0.0, -LA)
            tA -= self.t  # the same origin: the emission of a pair now
            chA = (tA, xA)
            s2 = K.interval(chA, detB, c)
            rel = K.relation(chA, detB, c)
            txt = {K.SPACELIKE: T("space-like (the setting was set just now)"),
                   K.TIMELIKE: T("time-like: the settings are known in advance, the locality loophole is OPEN"),
                   K.LIGHTLIKE: T("light-like")}[rel]
            self._check("st_loc", T("Fixed setting a ↔ detection at B of the next pair: {rel}", rel=txt), s2,
                        (c * (tB - tA)) ** 2 - (LB - xA) ** 2, T("m²"), g, tol=1e-9,
                        note=T("the setting a was set {dt:.6g} s before the emission of the pair, the pair arrives "
                               "{tf:.6g} s after the emission", dt=abs(tA), tf=tB))
            for cid in ("st_rev", "st_free"):
                self._check(cid, T("Only for a random choice of the settings"), None, None, "", g,
                            note=T("with fixed settings the choice was made at the set-up"))

    # --- checks: the statistics of the run's own counts -------------------------------------------------------
    def _stat_checks(self):
        self.n_checked = self.seg_counts["coinc"]
        law = self.law
        cells = self._cells()
        fixed = self.params["switch"] == "fixed"
        g = G_STAT
        ref_txt = T("the engine's prediction for these devices and this source (photodetector.coincidence_rates)")
        for k, c in enumerate(cells):
            lab = T("E({x},{y}) at α_A = {a}°, α_B = {b}°", x=c["x"], y=c["y"], a=float(c["alA"]), b=float(c["alB"]))
            if c["N"] >= NMIN:
                self._check(f"E{k}", lab, c["E"], c["Eexp"], "", g, ok=abs(c["z"]) < ZTOL,
                            note=T("N = {N:d}, ± {se:.3g}; z = {z:+.2f} (tolerance {ztol}σ); reference: {ref}; the law "
                                   "alone: {law:.4f}", N=int(c["N"]), se=float(c["se"]), z=float(c["z"]), ztol=ZTOL,
                                   ref=ref_txt, law=float(c["Elaw"])))
            else:
                self._check(f"E{k}", lab, None, c["Eexp"], "", g,
                            note=T("accumulating: N = {N:d} < {nmin:d}; in the mode “fixed” only the pair (a, b) "
                                   "accumulates", N=int(c["N"]), nmin=NMIN) if fixed and k else
                            T("accumulating: N = {N:d} < {nmin:d}", N=int(c["N"]), nmin=NMIN))
        s = self._S(cells)
        lab_S = T("S = E(a,b) − E(a,b′) + E(a′,b) + E(a′,b′) from the coincidences (fair sampling)")
        lab_tsir = T("Tsirelson bound: |S| ≤ 2√2 (with a tolerance of {ztol}σ)", ztol=ZTOL)
        lab_viol = T("Violation of the CHSH inequality under fair sampling: (|S| − 2)/σ")
        ok_n = s["S"] is not None and s["Nmin"] >= NMIN
        if ok_n:
            self._check("S", lab_S, s["S"], s["Sexp"], "", g, ok=abs(s["z"]) < ZTOL,
                        note=self._with_same(T("± {se:.3g}; z = {z:+.2f} (tolerance {ztol}σ); reference: {ref}; the "
                                               "law alone: {law:.4f}", se=float(s["se"]), z=float(s["z"]), ztol=ZTOL,
                                               ref=ref_txt, law=float(s["Slaw"])), s))
            aS = abs(s["S"])
            self._check("tsir", lab_tsir, aS, TSIRELSON, "", g, ok=aS - TSIRELSON < ZTOL * s["se_floor"],
                        note=T("|S| = {S:.4f} ± {se:.3g}", S=float(aS), se=float(s["se"])))
            if law.law == "lhv":
                self._check("bound", T("CHSH bound for local models: |S| ≤ 2 (with a tolerance of {ztol}σ)",
                                       ztol=ZTOL), aS, 2.0, "", g, ok=aS - 2.0 < ZTOL * s["se_floor"],
                            note=T("(|S| − 2)/σ = {x:+.2f}", x=float(s["excess"])) if s["excess"] is not None else "")
            else:
                exc = s["excess"]
                if abs(s["Sexp"]) > 2.0:
                    self._check("bound", lab_viol, exc, None, "σ", g,
                                note=(T("|S| = {S:.4f} ± {se:.3g} > 2 by {x:.1f}σ", S=float(aS), se=float(s["se"]),
                                        x=float(exc)) if exc is not None and exc > ZTOL else
                                      T("accumulating: the expected |S| = {S:.4f}", S=float(abs(s["Sexp"])))) if
                                law.law == "quantum" else
                                T("|S| = {S:.4f} ± {se:.3g}: a local model above 2, only because the counted pairs are "
                                  "the detected ones (the detection loophole)", S=float(aS), se=float(s["se"])))
                else:
                    self._check("bound", lab_viol, exc, None, "σ", g,
                                note=T("with these devices the expected |S| = {S:.4f} ≤ 2", S=float(abs(s["Sexp"]))))
        else:
            why = (T("accumulating: at least {nmin:d} coincidences per cell are needed for each of the four pairs of "
                     "settings; in the mode “fixed” only (a, b) accumulates: switch on the random choice", nmin=NMIN)
                   if fixed else T("accumulating: at least {nmin:d} coincidences per cell are needed for each of the "
                                   "four pairs of settings", nmin=NMIN))
            self._check("S", lab_S, None, s["Sexp"], "", g, note=self._with_same(why, s))
            self._check("tsir", lab_tsir, None, TSIRELSON, "", g, note=why)
            self._check("bound", T("CHSH bound |S| ≤ 2") if law.law == "lhv" else lab_viol,
                        None, 2.0 if law.law == "lhv" else None, "" if law.law == "lhv" else "σ", g, note=why)
        # the accidentals: subtracted, and their estimate against the run's own count
        Ssub, Ssub_se, accs = self._S_sub(cells)
        if ok_n and Ssub is not None:
            Strue = sum(sg * self._expect(c["alA"], c["alB"])["E_true"] for sg, c in zip(BS.CHSH_SIGNS, cells))
            z = (Ssub - Strue) / max(Ssub_se or 0.0, s["se_floor"])
            self._check("S_sub", T("S with the accidentals' estimate w·N_A·N_B/T subtracted"), Ssub, Strue, "", g,
                        ok=abs(z) < ZTOL,
                        note=T("± {se:.3g}; z = {z:+.2f}; reference: S of the true coincidences predicted by the engine "
                               "(the window's share, the live fractions)", se=float(Ssub_se), z=float(z)))
        est = float(sum(np.sum(a) for a in accs))
        own = int(sum(sum(c["acc"]) for c in cells))
        if est > 0 or own > 0:
            sd = math.sqrt(max(est, 1.0))
            self._check("acc", T("Accidental coincidences: the estimate w·N_A·N_B/T ↔ the run's own count"), est,
                        float(own), "", g, ok=abs(own - est) < ZTOL * sd + 2.0,
                        note=T("the run knows which clicks of a coincidence come from different pairs, dark or "
                               "background counts (a simulation only); {k:d} counted, {e:.4g} estimated, Poisson σ "
                               "{sd:.3g}", k=own, e=est, sd=sd))
        # all the trials: CH and J
        j = self._J()
        gs = G_SLOT
        if j["n"] >= 1000:
            zJ = (j["J"] - j["Jexp"]) / j["se"] if j["se"] else 0.0
            self._check("J", T("J = p₊₊(a′b) − p₊₀(a′b′) − p₀₊(ab) − p₊₊(ab′) per slot"), j["J"], j["Jexp"], "", gs,
                        ok=abs(zJ) < ZTOL,
                        note=T("± {se:.3g} (the multinomial error of each setting pair); z = {z:+.2f}; reference: the "
                               "engine's slot probabilities (bell_stats.slot_probabilities) for these devices; per pair "
                               "J/μ = {jp:.4g}", se=float(j["se"]), z=float(zJ), jp=float(j["J"] / j["mu"])))
            zC = (j["CH"] - j["CHexp"]) / j["CHse"] if j["CHse"] else 0.0
            self._check("CH", T("CH = p₊₊(a′b) + p₊₊(a′b′) + p₊₊(ab) − p₊₊(ab′) − p₊·(a′) − p·₊(b) per slot"),
                        j["CH"], j["CHexp"], "", gs, ok=abs(zC) < ZTOL,
                        note=T("± {se:.3g}; z = {z:+.2f} (Gisin and Gisin's inequality (15); local realism: CH ≤ 0)",
                               se=float(j["CHse"]), z=float(zC)))
            xJ = j["J"] / j["se"] if j["se"] else None
            if law.law == "quantum":
                self._check("J_bound", T("Violation of the CH–Eberhard inequality J ≤ 0 (no fair sampling): J/σ"),
                            xJ, None, "σ", gs,
                            note=T("J > 0 by {x:.1f}σ: no local model gives this, whatever it detects", x=float(xJ))
                            if xJ is not None and xJ > ZTOL else
                            T("no violation: J/σ = {x:+.2f}; with these detectors {why}", x=float(xJ or 0.0),
                              why=T("the predicted J per slot is {j:.3g} ≤ 0", j=float(j["Jexp"])) if j["Jexp"] <= 0
                              else T("more slots are needed")))
            else:
                self._check("J_bound", T("A local model keeps J ≤ 0 (with a tolerance of {ztol}σ)", ztol=ZTOL),
                            j["J"], 0.0, "", gs, ok=j["J"] < ZTOL * (j["se"] or 0.0),
                            note=T("J/σ = {x:+.2f}", x=float(xJ or 0.0)))
        else:
            for cid, lab in (("J", T("J = p₊₊(a′b) − p₊₀(a′b′) − p₀₊(ab) − p₊₊(ab′) per slot")),
                             ("CH", T("CH = p₊₊(a′b) + p₊₊(a′b′) + p₊₊(ab) − p₊₊(ab′) − p₊·(a′) − p·₊(b) per slot")),
                             ("J_bound", T("J and the bound 0"))):
                self._check(cid, lab, None, None, "", gs,
                            note=T("accumulating: at least {n:d} trials of each setting pair are needed", n=1000))
        # E(delta): all measured angle pairs against the prediction
        pts = self._points()
        m = pts[:, 3] >= NMIN if len(pts) else np.zeros(0, bool)
        if np.any(m):
            se = np.maximum(np.sqrt(np.maximum(1 - pts[m, 4] ** 2, 0) / pts[m, 3]), 2.0 / pts[m, 3])
            x2, dof, p = BS.chi2_points(pts[m, 1], pts[m, 4], se)
            if dof:
                self._check("curve", T("The curve E(Δ): χ² of the measured points against the prediction"), x2,
                            float(dof), "", g, ok=p > 1e-6,
                            note=T("points with N ≥ {nmin:d}: {k:d}; p = {p:.3g}; reference: χ² ≈ the number of "
                                   "points", nmin=NMIN, k=int(dof), p=float(p)))
        # no-signalling from the run's own counts
        gn = T("No signalling: the marginal of one side does not depend on the setting of the other")
        for i, (x, c1, c2) in enumerate((("a", cells[0], cells[1]), ("a′", cells[2], cells[3]))):
            self._nosig(f"nsA{i}", T("P_A(+ | {x}, b) − P_A(+ | {x}, b′)", x=x), c1, c2, "A", gn, fixed)
        for i, (y, c1, c2) in enumerate((("b", cells[0], cells[2]), ("b′", cells[1], cells[3]))):
            self._nosig(f"nsB{i}", T("P_B(+ | a, {y}) − P_B(+ | a′, {y})", y=y), c1, c2, "B", gn, fixed)
        # space-time relations of the coincidences actually counted in this segment
        n = self.seg_counts["coinc"]
        if n and not self.slots_mode:
            self._check("st_frac", T("Fraction of coincidences: the choice of the settings of both sides is outside the "
                                     "light cone of the detection on the other side"), self.seg_counts["loc"] / n,
                        None, "", G_ST, note=T("coincidences: {k:d} of {m:d} (by the events of each, "
                                               "lfphys.core.causality)", k=self.seg_counts["loc"], m=n))
            nt = self.seg_counts["true"]
            if nt:
                self._check("st_frac_free", T("Fraction of true coincidences: the choice of the settings of both sides "
                                              "is space-like separated from the emission of the pair"),
                            self.seg_counts["free"] / nt, None, "", G_ST,
                            note=T("coincidences: {k:d} of {m:d}", k=self.seg_counts["free"], m=nt))
        if not self.slots_mode:
            self._stream_checks()

    def _stream_checks(self):
        """The time stream's counts against the detectors' closed forms."""
        g, S = G_DEVS, self._si()
        st = self.counter
        both, true = st.counts["both"], self.seg_true_total
        if both >= 100:
            share = PD.window_share(S["w"], S["sigma"], S["sigma"])
            p = true / both
            se = math.sqrt(max(share * (1 - share), 1.0 / both) / both)
            self._check("window", T("Share of the pairs detected at both sides that fall inside the window"), p, share,
                        "", g, ok=abs(p - share) < ZTOL * se,
                        note=T("{k:d} of {n:d} pairs (a simulation knows the pairs); reference: erf(w/(4σ))", k=true,
                               n=both))
        tot_t, tot_n, exp_n = 0.0, 0, 0.0
        P = self.params
        for side, angs in (("A", (P["a_deg"], P["a2_deg"])), ("B", (P["b_deg"], P["b2_deg"]))):
            for a in set(angs):
                t = self.store.get_time(side, a)
                if t <= 0:
                    continue
                n = int(self.store.get_singles(side, a).sum())
                det = self._devices(side)
                pm = self.law.marginal_A(a) if side == "A" else self.law.marginal_B(a)
                rate = float(np.sum(PD.detector_rate(S["rate"] * np.asarray(pm[:2], float), det)))
                tot_t += t
                tot_n += n
                exp_n += rate * t
        if exp_n > 100:
            z = (tot_n - exp_n) / math.sqrt(exp_n)
            self._check("singles", T("Singles of all the detectors ↔ the closed form (ηR + d)/(1 + (ηR + d)t_d)"),
                        float(tot_n), exp_n, "", g, ok=abs(z) < ZTOL,
                        note=T("z = {z:+.2f} (Poisson); the non-paralysable dead time, dark and background counts "
                               "(photodetector.detector_rate)", z=float(z)))

    @property
    def seg_true_total(self) -> int:
        return int(self.seg_counts["true"])

    @staticmethod
    def _with_same(note, s):
        """``note`` with the warning about coinciding settings, when they coincide."""
        if not s["same"]:
            return note
        return T("{note}; the settings coincide (a′ = a or b′ = b): the cells {cells} are the same pairs as another "
                 "cell; S reduces to 2E of one pair of angles, this is not a CHSH test; the error of S counts each pair "
                 "of angles once", note=note, cells=", ".join(s["same"]))

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
        desc = join([T("{label}: {old} → {new}", label=SCHEMA.by_id[k].label, old=_val(SCHEMA.by_id[k], old[k]),
                        new=_val(SCHEMA.by_id[k], new[k])) for k in changed])
        self.params = new
        self.counter.change(self._si(new), now)
        S = self._si()
        if new["switch"] == "random" and C * (S["tau"] + S["Ts"]) >= S["L_A"] + S["L_B"] and \
                any(k in changed for k in ("tau_ns", "switch")):
            self._msg({"type": "notice", "t": now,
                       "text": T("c(τ + T_s) ≥ L_A + L_B: the choice of a setting is time-like separated from the "
                                 "detection on the other side; the locality loophole is open")})
        if any(k in changed for k in ANGLES) or "rate" in changed:
            self._setup_checks()
        self._spacetime_checks()
        self._stat_checks()
        return desc

    def action(self, name, args):
        if name == "clear":
            self.store.clear()
            self.seg += 1
            self.seg_counts = dict(coinc=0, loc=0, free=0, true=0)
            self.said = set()
            self._stat_checks()
            return T("the statistics reset; the set-up and the pairs in flight as they were")
        raise ValueError(f"unknown action {name!r}")

    # --- time -----------------------------------------------------------------------------------------
    def max_step(self):
        if self.slots_mode:
            return None
        return 2000.0 / self.params["rate"]

    def _protect(self):
        return [(x, y) for _, _, x, y in self._cell_angles()]

    def advance(self, t_target):
        first = self.seg_counts["coinc"] == 0 and not self.said
        if self.slots_mode:
            got = self.counter.step(t_target, self.store)
            n_new = got["coinc"]
            self.seg_counts["coinc"] += n_new
            self.seg_counts["true"] += got["true"]
            if got.get("shown") is not None:
                self._msg({"type": "slots", "t": t_target, "seg": self.seg}, {"slots": got["shown"]})
        else:
            got = self.counter.step(t_target, self.store, self._protect())
            n_new = got["n"]
            if n_new:
                fl = got["fl"]
                self.seg_counts["coinc"] += n_new
                self.seg_counts["true"] += int(np.sum(got["true"]))
                self.seg_counts["loc"] += int(np.sum((fl & F_LOC_A > 0) & (fl & F_LOC_B > 0)))
                self.seg_counts["free"] += int(np.sum((fl & F_FREE_A > 0) & (fl & F_FREE_B > 0)))
            self._pairs_message(got, t_target)
        self.t = t_target
        self._milestones(got, first)
        n = self.seg_counts["coinc"]
        if n - self.n_checked >= max(250, 0.5 * self.n_checked) if not self.slots_mode else self._slots_due():
            self._stat_checks()
            self._maybe_violation_event()
            if self.params["switch"] == "fixed" and not self.slots_mode:  # the age of the fixed settings grows
                self._spacetime_checks()

    def _slots_due(self) -> bool:
        """The counting by slots updates its checks at 1, 2, 5 × 10ⁿ trials."""
        n = self.counter.k_done
        if n < self._next_slot_check:
            return False
        while self._next_slot_check <= n:
            m = self._next_slot_check
            e = 10 ** int(math.floor(math.log10(m)))
            self._next_slot_check = {1: 2, 2: 5, 5: 10}[int(round(m / e))] * e
        return True

    def _pairs_message(self, got, t_target):
        """The step's newest coincidences in detail and the newest clicks of each station, for the view: the times of
        a coincidence relative to its click at A (float32 keeps them to 10⁻¹³ s), the clicks' times relative to the
        message's time."""
        tags = got["tags"]
        blobs = {}
        any_click = False
        for s in "AB":
            tg = tags[s]
            sl = slice(max(0, len(tg["t"]) - CLICKS), None)
            any_click = any_click or len(tg["t"]) > 0
            blobs[f"k{s}_dt"] = (tg["t"][sl] - t_target).astype(np.float32)
            blobs[f"k{s}_d"] = tg["det"][sl].astype(np.int8)
            blobs[f"k{s}_s"] = tg["s"][sl].astype(np.int8)
        if not got["n"] and not any_click:
            return
        meta = {"type": "pairs", "t": t_target, "n": int(got["n"]), "seg": self.seg}
        if got["n"]:
            n = got["n"]
            sl = slice(max(0, n - DETAIL), None)
            tA = got["tA"][sl]
            blobs["c_tA"] = tA.astype(np.float64)
            for k in ("tB", "te", "tcA", "tcB"):
                blobs["c_d" + k] = (got[k][sl] - tA).astype(np.float32)
            blobs["c_id"] = got["id"][sl].astype(np.int32)
            for k in ("sA", "sB", "oA", "oB"):
                blobs["c_" + k] = got[k][sl].astype(np.int8)
            blobs["c_fl"] = got["fl"][sl].astype(np.uint8)
            blobs["c_alA"] = got["alA"][sl].astype(np.float32)
            blobs["c_alB"] = got["alB"][sl].astype(np.float32)
        self._msg(meta, blobs)

    def _milestones(self, got, first):
        n = self.seg_counts["coinc"]
        if first and n and not self.slots_mode:
            i = 0
            sg = lambda o: "+" if o > 0 else "−"  # noqa: E731
            self._msg({"type": "event", "kind": "detection", "t": float(max(got["tA"][i], got["tB"][i])),
                       "text": T("The first coincidence: A {oA} at {aA}°, B {oB} at {aB}°", oA=sg(got["oA"][i]),
                                 aA=float(got["alA"][i]), oB=sg(got["oB"][i]), aB=float(got["alB"][i]))})
            self.said.add("first")
        for m in MILESTONES:
            if n >= m and m not in self.said:
                self.said.add(m)
                if self.slots_mode:
                    tm = self.t
                else:
                    tA, tB = got.get("tA"), got.get("tB")
                    k = m - (n - got["n"]) - 1  # the m-th coincidence of the segment within this step
                    tm = float(max(tA[k], tB[k])) if tA is not None and 0 <= k < len(tA) else self.t
                self._msg({"type": "event", "kind": "count", "name": f"coincidences_{m}", "t": tm,
                           "text": T("{n:d} coincidences counted", n=m)})

    def _maybe_violation_event(self):
        if "viol" not in self.said and self.law.law == "quantum":
            s = self._S(self._cells())
            if s["excess"] is not None and s["Nmin"] >= NMIN and s["excess"] > ZTOL:
                self.said.add("viol")
                self._msg({"type": "event", "kind": "result", "t": self.t,
                           "text": T("Violation of the CHSH inequality under fair sampling by {x:.1f}σ: S = {S:.4f} ± "
                                     "{se:.3g} ({k:d} coincidences)", x=float(s["excess"]), S=float(s["S"]),
                                     se=float(s["se"]), k=int(self.seg_counts["coinc"]))})
        if "jviol" not in self.said and self.law.law == "quantum":
            j = self._J()
            if j["J"] is not None and j["se"] and j["n"] >= 1000 and j["J"] / j["se"] > ZTOL:
                self.said.add("jviol")
                self._msg({"type": "event", "kind": "result", "t": self.t,
                           "text": T("Violation of the CH–Eberhard inequality without fair sampling by {x:.1f}σ: J = "
                                     "{J:.3g} ± {se:.2g} per slot", x=float(j["J"] / j["se"]), J=float(j["J"]),
                                     se=float(j["se"]))})

    def next_event_time(self):
        return None if self.slots_mode else self.counter.next_time()

    # --- frames ---------------------------------------------------------------------------------------
    def _meas(self, cells, s, j, Ssub, Ssub_se, accs):
        P = self.params
        est = float(sum(np.sum(a) for a in accs))
        sA = int(sum(self.store.get_singles("A", x).sum() for x in {P["a_deg"], P["a2_deg"]}))
        sB = int(sum(self.store.get_singles("B", x).sum() for x in {P["b_deg"], P["b2_deg"]}))
        coinc = int(sum(c["N"] for c in self._distinct(cells)))
        meas = {"n_pp": cells[0]["n"][0], "n_pm": cells[0]["n"][1], "n_mp": cells[0]["n"][2],
                "n_mm": cells[0]["n"][3], "coinc": coinc, "singles_A": sA, "singles_B": sB,
                "acc_est": est if est > 0 else (0.0 if coinc else None),
                "herald": coinc / math.sqrt(sA * sB) if sA and sB else None,
                "trials": j["trials"] if j["trials"] else None,
                "S_law": self._S_law}
        for name, c in zip(CELL_NAMES, cells):
            ok = c["N"] >= 1 and c["se"] is not None
            meas[f"E_{name}"] = c["E"] if ok else None
            meas[f"E_{name}_se"] = c["se"] if ok and c["se"] > 0 else (1.0 / math.sqrt(c["N"]) if ok else None)
            meas[f"E_{name}_ref"] = c["Elaw"]
        okS = s["S"] is not None and s["Nmin"] >= 1
        meas["S"] = s["S"] if okS else None
        meas["S_se"] = s["se"] if okS else None
        meas["excess"] = s["excess"] if okS else None
        meas["S_sub"] = Ssub
        meas["S_sub_se"] = Ssub_se
        n = self.seg_counts["coinc"]
        meas["local_frac"] = (self.seg_counts["loc"] / n) if n and not self.slots_mode else None
        okJ = j["J"] is not None
        meas["J"] = j["J"] if okJ else None
        meas["J_se"] = j["se"] if okJ else None
        meas["J_ref"] = j["Jexp"]
        meas["J_pair"] = j["J"] / j["mu"] if okJ else None
        meas["J_pair_se"] = j["se"] / j["mu"] if okJ else None
        meas["CH"] = j["CH"] if okJ else None
        meas["CH_se"] = j["CHse"] if okJ else None
        meas["CH_ref"] = j["CHexp"]
        return meas

    @staticmethod
    def _distinct(cells):
        seen, out = set(), []
        for c in cells:
            k = Store.key(c["alA"], c["alB"])
            if k not in seen:
                seen.add(k)
                out.append(c)
        return out

    def _delta(self):
        """Δ of the CHSH geometry a = a0, b = a0 + Δ, a′ = a0 + 2Δ, b′ = a0 + 3Δ when the settings have it, else None."""
        P = self.params
        d = P["b_deg"] - P["a_deg"]
        if abs(P["a2_deg"] - P["a_deg"] - 2 * d) < 1e-9 and abs(P["b2_deg"] - P["a_deg"] - 3 * d) < 1e-9:
            return d
        return None

    def frame(self):
        P = self.params
        S = self._si()
        cells = self._cells()
        s = self._S(cells)
        j = self._J()
        Ssub, Ssub_se, accs = self._S_sub(cells)
        st = {"settings": {"a": P["a_deg"], "a2": P["a2_deg"], "b": P["b_deg"], "b2": P["b2_deg"],
                           "switch": P["switch"], "LA": S["L_A"], "LB": S["L_B"], "tau": S["tau"], "rate": S["rate"],
                           "Ts": S["Ts"], "w": S["w"], "etaA": S["eta_A"], "etaB": S["eta_B"],
                           "counting": P["counting"], "delta": self._delta()},
              "flight": [S["L_A"] / self.v, S["L_B"] / self.v],
              "counts": {"emitted": self.counter.counts["emitted"], "in_flight": self.counter.n_flight,
                         "seg": self.seg, "coinc": self.seg_counts["coinc"], "loc": self.seg_counts["loc"],
                         "free": self.seg_counts["free"], "true": self.seg_counts["true"]},
              "now_slots": self._now_slots(),
              "cells": cells, "S": s, "S_law": self._S_law, "S_sub": [Ssub, Ssub_se],
              "J": {k: j[k] for k in ("J", "se", "Jexp", "CH", "CHse", "CHexp", "mu", "trials")},
              "meas": self._meas(cells, s, j, Ssub, Ssub_se, accs)}
        st["cells"] = [{k: _r6(c[k]) for k in ("x", "y", "alA", "alB", "n", "N", "E", "se", "Eexp", "z")} for c in cells]
        st["S"] = {k: _r6(v) for k, v in s.items()}
        st["J"] = {k: _r6(v) for k, v in st["J"].items()}
        st["S_sub"] = [_r6(Ssub), _r6(Ssub_se)]
        st["meas"] = {k: _r6(v) for k, v in st["meas"].items()}
        rs = np.asarray(self.counter.recent_slots, float)
        blobs = {"flight": self.counter.in_flight(120)[:, :1].ravel() if self.counter.n_flight else np.zeros(0),
                 "pts": self._points(), "slots": rs[:, 1:5].astype(np.int8) if len(rs) else np.zeros((0, 4), np.int8)}
        return st, blobs

    def _now_slots(self) -> dict:
        """Each station's current slot and its setting (chosen τ before the slot starts, so known now)."""
        if self.slots_mode:
            return {}
        S, st = self._si(), self.counter
        out = {}
        for side in "AB":
            k = int(math.floor((self.t - st.off(side)) / S["Ts"]))
            if k >= 0:
                out[side] = [k, int(st.setting(side, np.array([k]))[0])]
        return out

    def _j_curve(self):
        """J per pair against an equal efficiency η of all the detectors, for this source, background and slots (the
        engine's slot probabilities; the view's curve J(η) in the counting by slots)."""
        P, S = self.params, self._si()
        A = (P["a2_deg"], P["a_deg"])
        B = (P["b_deg"], P["b2_deg"])
        pd = PD.dark_click_probability(S["dark"], S["Ts"])
        mu = S["rate"] * S["Ts"]
        etas = np.linspace(0.5, 1.0, 26)
        js = [BS.j_value([[self.law.slot_table(A[i], B[j], float(e), float(e), pd, pd, mu) for j in (0, 1)]
                          for i in (0, 1)]) / mu for e in etas]
        return etas, np.array(js)

    def header(self):
        law = self.law
        d, q, h = law.curves()
        sd, sq, sh, sw = law.s_curves()
        if self.slots_mode:
            je, jq = self._j_curve()
        P = self.params
        return {
            "title": T("Bell test: {law}", law=law.describe()),
            "text": T("The source in the middle emits pairs one at a time (a Poisson stream); the particles fly to the "
                      "stations of Alice (−L_A) and Bob (+L_B). Each station divides its time into slots on its own "
                      "clock and, in the mode of random choice, draws a bit for each slot τ before it starts: the "
                      "setting a or a′ (b or b′) of its analyser. Two real detectors behind each analyser click with "
                      "their efficiency, dark counts, dead time and jitter; a coincidence is a click at each station "
                      "within the window w. S comes from the coincidences, which assumes that the detected pairs are "
                      "a fair sample; CH and J come from all the slots and need no such assumption."),
            "pair": P["pair"], "pair_label": PAIR_LABEL[P["pair"]], "law": law.law, "model": law.model,
            "model_label": MODEL_LABEL.get(law.model), "v": self.v, "c": C, "period": law.period,
            "counting": P["counting"], "device": self._device_identity(),
            "modifications": SCHEMA.modifications(P), "actions": self._actions(), "measurables": MEASURABLES,
        }, {"cd": d, "cq": q, "ch": h, "sd": sd, "sq": sq, "sh": sh, "sw": sw,
            **({"je": je, "jq": jq} if self.slots_mode else {})}


def _r6(x):
    """A shown value to six significant digits (the frames' display values; the checks keep full precision)."""
    if isinstance(x, (float, np.floating)) and math.isfinite(x):
        return float(f"{float(x):.6g}")
    return x


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


# --- the screens (EX2 design §4) -------------------------------------------------------------------------------------
DELTAS = [7.5 * k for k in range(13)]  # Δ 0 … 90°: a = 0, b = Δ, a′ = 2Δ, b′ = 3Δ
SOURCE_VALUES = ["quantum", "visibility", "local"]
EFFS = list(EFFS_BENCH)
# after_s longer than one frame (0.08 s): the stop event's frame is not the last one (EX2 §5 F1, step F's notes)
STOP_4000 = {"events": {"coincidences_4000": 1}, "after_s": 0.1, "max_world_s": 2.0}
# the pair type: a compound control, so that its values carry their own names (a parameter's control shows its raw value)
PARTICLES = {"id": "particles", "label": T("Pairs"), "values": ["photon", "spin"], "default": "photon",
             "labels": [T("photons"), T("spin ½")], "sets": {"pair": ["photon", "spin"]}}
QUANT_CURVES = {"header.cq": "u16", "header.ch": "u16", "header.sq": "u16", "header.sh": "u16", "header.sw": "u16"}

EXPLORE = {
    "id": "explore", "kind": "explore", "preset": "photon_chsh",
    "fixed": {"switch": "random", "L_A_m": 500.0, "L_B_m": 500.0, "rate": 1e4, "a_deg": 0.0},
    "controls": [
        PARTICLES,
        {"id": "delta", "label": T("Angle step Δ"), "unit": "°", "values": DELTAS, "default": 22.5,
         "sets": {"b_deg": DELTAS, "a2_deg": [2 * d for d in DELTAS], "b2_deg": [3 * d for d in DELTAS]}},
        {"param": "tau_ns", "values": [100.0, 5000.0], "default": 100.0, "label": T("Choice before its slot τ"),
         "unit": "ns"},
        {"id": "source", "label": T("Law and source"), "values": SOURCE_VALUES, "default": "quantum",
         "labels": [T("quantum, an ideal source"), T("quantum, a source of visibility 0.85"),
                    T("local hidden variables (modified physics)")],
         "sets": {"law": ["quantum", "quantum", "lhv"], "visibility": [1.0, 0.85, 1.0]}}],
    "acts": "now", "time": "buildup", "frame_dt": 0.08, "speed": 0.08, "stop": STOP_4000, "seed": 1,
    "quantize": QUANT_CURVES,
    "overlays": ["spacetime", "cones", "slots", "e_delta", "s_delta", "other_law"], "traces": 5,
    "readouts": ["S", "excess", "coinc"],
}

INSTRUMENTS = {
    "pol_a": {"kind": "readout", "label": T("Alice's analyser scale α"), "unit": "°", "division": 0.5, "error": 0,
              "error_note": T("the analyser is set at the marks of its scale"), "reads": "control:a_deg"},
    "pol_b": {"kind": "readout", "label": T("Bob's analyser scale β"), "unit": "°", "division": 0.5, "error": 0,
              "error_note": T("the analyser is set at the marks of its scale"), "reads": "control:b_deg"},
    # the step Δ of the CHSH geometry is Bob's angle b (Alice's a = 0): read on Bob's scale (a lab step on a shared
    # atlas reads the parameters a compound control sets, not the compound itself)
    "delta": {"kind": "readout", "label": T("Bob's analyser scale b = Δ"), "unit": "°", "division": 0.5, "error": 0,
              "error_note": T("the analysers are set at their marks"), "reads": "control:b_deg"},
    "c_pp": {"kind": "counter", "label": T("Coincidence counter N₊₊ of (a, b)"), "unit": "", "error": "poisson",
             "reads": "n_pp"},
    "c_pm": {"kind": "counter", "label": T("Coincidence counter N₊₋ of (a, b)"), "unit": "", "error": "poisson",
             "reads": "n_pm"},
    "c_mp": {"kind": "counter", "label": T("Coincidence counter N₋₊ of (a, b)"), "unit": "", "error": "poisson",
             "reads": "n_mp"},
    "c_mm": {"kind": "counter", "label": T("Coincidence counter N₋₋ of (a, b)"), "unit": "", "error": "poisson",
             "reads": "n_mm"},
    "e_1": {"kind": "readout", "label": T("E(a, b) of the run"), "unit": "", "division": 0.0001, "sigma": "E_ab_se",
            "reads": "E_ab"},
    "e_2": {"kind": "readout", "label": T("E(a, b′) of the run"), "unit": "", "division": 0.0001,
            "sigma": "E_ab2_se", "reads": "E_ab2"},
    "e_3": {"kind": "readout", "label": T("E(a′, b) of the run"), "unit": "", "division": 0.0001,
            "sigma": "E_a2b_se", "reads": "E_a2b"},
    "e_4": {"kind": "readout", "label": T("E(a′, b′) of the run"), "unit": "", "division": 0.0001,
            "sigma": "E_a2b2_se", "reads": "E_a2b2"},
    "frac": {"kind": "readout", "label": T("Space-like fraction of the coincidences"), "unit": "", "division": 0.001,
             "error": 0, "error_note": T("a fraction of the run's own coincidences"), "reads": "local_frac"},
    "eff": {"kind": "readout", "label": T("Detection efficiency η of the detectors"), "unit": "", "division": 0.01,
            "error": 0, "error_note": T("a property of the detectors, set here"), "reads": "control:eff"},
    "s_raw": {"kind": "readout", "label": T("S from the coincidences"), "unit": "", "division": 0.0001,
              "sigma": "S_se", "reads": "S"},
    "s_sub": {"kind": "readout", "label": T("S with the accidentals subtracted"), "unit": "", "division": 0.0001,
              "sigma": "S_sub_se", "reads": "S_sub"},
    "j_pair": {"kind": "readout", "label": T("J per pair"), "unit": "", "division": 1e-5, "sigma": "J_pair_se",
               "reads": "J_pair"},
    "ch": {"kind": "readout", "label": T("CH per slot"), "unit": "", "division": 1e-7, "sigma": "CH_se", "reads": "CH"},
    "acc": {"kind": "readout", "label": T("Accidentals' estimate w·N_A·N_B/T"), "unit": "", "division": 0.1,
            "reads": "acc_est"},
    "coinc": {"kind": "counter", "label": T("Coincidences of the four setting pairs"), "unit": "", "error": "poisson",
              "reads": "coinc"},
}

_E_COLS = [{"id": "D", "label": T("Δ, °"), "from": "delta"},
           {"id": "E1", "label": T("E(a, b)"), "from": "e_1"},
           {"id": "E2", "label": T("E(a, b′)"), "from": "e_2"},
           {"id": "E3", "label": T("E(a′, b)"), "from": "e_3"},
           {"id": "E4", "label": T("E(a′, b′)"), "from": "e_4"},
           {"id": "S", "label": T("S = E₁ − E₂ + E₃ + E₄"), "expr": "E1 - E2 + E3 + E4"},
           {"id": "x_ph", "label": T("3 cos 2Δ − cos 6Δ"), "expr": "3 * cosd(2 * D) - cosd(6 * D)"},
           {"id": "x_sp", "label": T("−(3 cos Δ − cos 3Δ)"), "expr": "-(3 * cosd(D) - cosd(3 * D))"},
           {"id": "frac", "label": T("outside the cone"), "from": "frac"}]

LAB = {
    "id": "lab", "kind": "lab", "instruments": INSTRUMENTS,
    "steps": [
        {"id": "correlation", "title": T("The correlation E(α, β)"),
         "goal": T("Count the four coincidences at fixed analyser angles and find how the correlation E depends on "
                   "the angle between the analysers"),
         "preset": "scan", "fixed": {"switch": "fixed", "rate": 1e4, "L_A_m": 500.0, "L_B_m": 500.0},
         "controls": [PARTICLES,
                      {"param": "a_deg", "values": [0.0, 45.0, 90.0], "default": 0.0, "label": T("Alice's angle α"),
                       "unit": "°"},
                      {"param": "b_deg", "values": [7.5 * k for k in range(25)], "default": 22.5,
                       "label": T("Bob's angle β"), "unit": "°"}],
         "instruments": ["pol_a", "pol_b", "c_pp", "c_pm", "c_mp", "c_mm", "e_1"],
         "columns": [{"id": "a", "label": T("α, °"), "from": "pol_a"}, {"id": "b", "label": T("β, °"), "from": "pol_b"},
                     {"id": "npp", "label": T("N₊₊"), "from": "c_pp"}, {"id": "npm", "label": T("N₊₋"), "from": "c_pm"},
                     {"id": "nmp", "label": T("N₋₊"), "from": "c_mp"}, {"id": "nmm", "label": T("N₋₋"), "from": "c_mm"},
                     {"id": "E", "label": T("E from the four counts"),
                      "expr": "(npp + nmm - npm - nmp) / (npp + nmm + npm + nmp)"},
                     {"id": "c2", "label": T("cos 2(β − α)"), "expr": "cosd(2 * (b - a))"},
                     {"id": "c1", "label": T("cos(β − α)"), "expr": "cosd(b - a)"}],
         "plot": {"x": "c2", "y": "E", "fit": "line0", "fits": ["line0", "line", "quadratic", "power"]},
         "laws": [{"x": "c2", "y": "E", "model": "line0", "quantity": "slope",
                   "label": T("slope of E against cos 2(β − α), photons"), "unit": "", "reference": "slope_photons"},
                  {"x": "c1", "y": "E", "model": "line0", "quantity": "slope",
                   "label": T("slope of E against cos(β − α), spins"), "unit": "", "reference": "slope_spins"}],
         "frame_dt": 0.025, "speed": 0.025,
         "stop": {"events": {"coincidences_1000": 1}, "after_s": 0.03, "max_world_s": 2.0}, "seed": 1,
         "quantize": QUANT_CURVES,
         "overlays": ["spacetime", "cones", "slots", "e_delta", "s_delta", "other_law"],
         "readouts": ["E_ab", "coinc"]},
        {"id": "chsh", "atlas": "explore", "title": T("The CHSH test"),
         "goal": T("With settings chosen at random per slot, read the four correlations, compute S with its error and "
                   "compare it with the bound 2"),
         "instruments": ["delta", "e_1", "e_2", "e_3", "e_4", "frac"], "columns": _E_COLS,
         "plot": {"x": "x_ph", "y": "S", "fit": "line0", "fits": ["line0", "line", "quadratic"]},
         "laws": [{"x": "x_ph", "y": "S", "model": "line0", "quantity": "slope",
                   "label": T("slope of S against 3 cos 2Δ − cos 6Δ, photons, an ideal source"), "unit": "",
                   "reference": "slope_quantum"},
                  {"x": "x_ph", "y": "S", "model": "line0", "quantity": "slope",
                   "label": T("slope of S against 3 cos 2Δ − cos 6Δ, a source of visibility 0.85"), "unit": "",
                   "reference": "slope_visibility"},
                  {"x": "x_sp", "y": "S", "model": "line0", "quantity": "slope",
                   "label": T("slope of S against −(3 cos Δ − cos 3Δ), spins"), "unit": "",
                   "reference": "slope_spins"}],
         "speed": 0.08, "overlays": ["spacetime", "cones", "slots", "e_delta", "s_delta", "other_law"],
         "readouts": ["S", "excess", "coinc"]},
        {"id": "local", "atlas": "explore", "title": T("The same test in a local world"),
         "goal": T("Repeat the CHSH test in the world of local hidden variables (modified physics) and compare"),
         "hint": T("choose the law “local hidden variables” of the control “Law and source”"),
         "instruments": ["delta", "e_1", "e_2", "e_3", "e_4", "frac"], "columns": _E_COLS,
         "plot": {"x": "x_ph", "y": "S", "fit": "line0", "fits": ["line0", "line", "quadratic"]},
         "laws": [{"x": "x_ph", "y": "S", "model": "line0", "quantity": "slope",
                   "label": T("slope of S against 3 cos 2Δ − cos 6Δ in the polarisation model"), "unit": "",
                   "reference": "slope_local"}],
         "speed": 0.08, "overlays": ["spacetime", "cones", "slots", "e_delta", "s_delta", "other_law"],
         "readouts": ["S", "excess"]},
        {"id": "detectors", "title": T("Real detectors"),
         "goal": T("Compare S from the coincidences, which assumes fair sampling, with CH and J from all the slots, "
                   "which do not, at several efficiencies, sources, backgrounds and windows"),
         "preset": "detectors", "fixed": {"rate": 1e4, "slot_ns": 1000.0},
         "controls": [{"id": "eff", "label": T("Detection efficiency η"), "values": EFFS, "default": 0.75,
                       "sets": {"eta_A": EFFS, "eta_B": EFFS}},
                      {"id": "source", "label": T("Source"), "values": ["phi", "eberhard", "gisin"], "default": "phi",
                       "labels": [T("|Φ+⟩ at the CHSH angles"), T("Eberhard's state r = −2.9 at Giustina's angles"),
                                  T("Gisin and Gisin's local model (modified physics)")],
                       "sets": {"law": ["quantum", "quantum", "gg"], "state": ["max", "eberhard", "max"],
                                "r": [-2.9, -2.9, -2.9],
                                "a_deg": [0.0, GIUSTINA["a_deg"], 0.0], "a2_deg": [45.0, GIUSTINA["a2_deg"], 45.0],
                                "b_deg": [22.5, GIUSTINA["b_deg"], 22.5],
                                "b2_deg": [67.5, GIUSTINA["b2_deg"], 67.5]}},
                      {"id": "bg", "label": T("Dark and background counts"), "values": ["dark", "bright", "none"],
                       "default": "dark",
                       "labels": [T("the detectors' 250 dark counts per second"),
                                  T("10⁵ background counts per second"),
                                  T("none (an idealisation)")],
                       "sets": {"bg_rate": [0.0, 1e5, 0.0], "dark_rate": [DEV.dark_rate, DEV.dark_rate, 0.0]}},
                      {"param": "window_ns", "values": [0.5, 2.0, 25.0], "default": 2.0,
                       "label": T("Coincidence window w"), "unit": "ns"}],
         "instruments": ["eff", "coinc", "acc", "s_raw", "s_sub", "j_pair", "ch"],
         "columns": [{"id": "eta", "label": T("η"), "from": "eff"},
                     {"id": "C", "label": T("N_c"), "from": "coinc"},
                     {"id": "acc", "label": T("N_acc"), "from": "acc"},
                     {"id": "S", "label": T("S"), "from": "s_raw"},
                     {"id": "Ssub", "label": T("S − acc."), "from": "s_sub"},
                     {"id": "Jp", "label": T("J per pair"), "from": "j_pair"},
                     {"id": "CH", "label": T("CH per slot"), "from": "ch"},
                     {"id": "Jeta", "label": T("J per pair / η"), "expr": "Jp / eta"}],
         "plot": {"x": "eta", "y": "Jeta", "fit": "line", "fits": ["line", "line0", "quadratic"]},
         "laws": [{"x": "eta", "y": "Jeta", "model": "line", "quantity": "slope",
                   "label": T("slope of J/η against η, |Φ+⟩ at the CHSH angles, no dark counts"), "unit": "",
                   "reference": "j_slope"},
                  {"x": "eta", "y": "Jeta", "model": "line", "quantity": "intercept",
                   "label": T("intercept of J/η against η, |Φ+⟩ at the CHSH angles, no dark counts"), "unit": "",
                   "reference": "j_intercept"}],
         "frame_dt": 100.0, "speed": 100.0, "stop": {"world_s": 1000.0}, "seed": 1, "quantize": QUANT_CURVES,
         "overlays": ["slots", "other_law"], "readouts": ["S", "J_pair", "coinc"]}],
    "worksheet": {
        "basis": [
            {"text": T("A Bell test in the undergraduate laboratory: four coincidence counts give E, sixteen give S, "
                       "each count with its counting error"),
             "source": "D. Dehlinger, M. W. Mitchell, «Entangled photons, nonlocality, and Bell inequalities in the "
                       "undergraduate laboratory», Am. J. Phys. 70, 903 (2002), arXiv:quant-ph/0205171",
             "quote": "The experiments described can be performed in an afternoon.", "quote_lang": "en"},
            {"text": T("The error of S from counting statistics, and the conclusion they drew from S = 2.307 ± 0.035"),
             "source": "D. Dehlinger, M. W. Mitchell, Am. J. Phys. 70, 903 (2002)",
             "quote": "To be sure of the result, we compute its statistical uncertainty.", "quote_lang": "en"},
            {"text": T("CH and the CH–Eberhard J need no fair sampling; locally defined time slots"),
             "source": "M. Giustina et al., «Significant-loophole-free test of Bell's theorem with entangled "
                       "photons», Phys. Rev. Lett. 115, 250401 (2015), arXiv:1511.03190",
             "quote": "These inequalities can be violated with system heralding efficiencies larger than 2/3.",
             "quote_lang": "en"},
            {"text": T("A local model that passes the CHSH bound through the detection loophole"),
             "source": "N. Gisin, B. Gisin, Phys. Lett. A 260, 323 (1999), arXiv:quant-ph/9905018",
             "quote": "On average the detector efficiency is limited to 75%.", "quote_lang": "en"}],
        "goal": T("Measure the polarisation correlation of entangled photons and test the CHSH form of Bell's "
                  "inequality."),
        "bench": [T("A source of entangled pairs (photons |Φ+⟩ or spin-½ singlets) between two stations 500 m away on "
                    "each side; at each station an analyser with two outputs and two detectors, set by hand or chosen "
                    "at random τ before each time slot; detectors with their efficiency, dark counts, dead time and "
                    "jitter (by default an Excelitas SPCM-NIR's data-sheet values); coincidence counters; a source of "
                    "ideal or imperfect visibility; a world with local hidden variables for comparison (modified "
                    "physics)."),
                  T("In part 4, 10⁹ slots of 1 µs at 10⁴ pairs per second: the efficiency, the source (|Φ+⟩, "
                    "Eberhard's state, Gisin and Gisin's local model), the dark and background counts and the "
                    "coincidence window can be chosen.")],
        "procedure": [T("1. With fixed settings, count the four coincidences for α = 0° and β from 0° to 180°; compute "
                        "E and plot it against cos 2(β − α)."),
                      T("2. With random settings at Δ = 22.5°, read E of the four setting pairs and compute S with its "
                        "error."),
                      T("3. Repeat at other Δ and in the local world."),
                      T("4. With the detectors of part 4, compare S from the coincidences with J (or CH) from all the "
                        "slots at several efficiencies and windows.")],
        "record": [T("the counts and E with their errors, S with its error and (S − 2)/σ"),
                   T("the fits: the model, the points, the parameters, χ²"),
                   T("the settings and τ you used; in part 4 the devices, J or CH with its error and the accidentals"),
                   T("your conclusion")],
        "record_rows": 13,
        "variants": [
            {"id": "spins", "label": T("Spin-½ pairs"),
             "values": {"correlation": {"particles": "spin"}, "chsh": {"particles": "spin", "delta": 45.0}},
             "text": {"goal": T("Measure the spin correlation of singlet pairs and test the CHSH inequality.")}},
            {"id": "slow_choice", "label": T("A slow choice of the settings: τ = 5 µs"),
             "values": {"chsh": {"tau_ns": 5000.0}}},
            {"id": "real_source", "label": T("A real source of visibility 0.85"),
             "values": {"chsh": {"source": "visibility"}}},
            {"id": "local_world", "label": T("The local world"), "values": {"local": {"source": "local"}}},
            {"id": "alice_45", "label": T("Alice's analyser at 45°"), "values": {"correlation": {"a_deg": 45.0}}},
            {"id": "eberhard", "label": T("Eberhard's state without background"),
             "values": {"detectors": {"source": "eberhard", "bg": "none", "eff": 0.8}}},
            {"id": "gisin", "label": T("Gisin and Gisin's local model"),
             "values": {"detectors": {"source": "gisin", "eff": 1.0}}}]},
}


# the story's script and the numbers its captions quote, from the run itself (tests/test_u37_screens.py): the first
# pairs' flights are shown slowly, the waits between them fast (pairs come about 100 µs apart and fly 1.67 µs)
STORY_SCRIPT = [{"at": 0, "cmd": "speed", "args": {"value": 2.193e-4}},   # to 0.5 µs before the first emission
                {"at": 1, "cmd": "speed", "args": {"value": 8.34e-7}},    # a flight of 1.67 µs in 2 s
                {"at": 5, "cmd": "speed", "args": {"value": 1.3366e-4}},  # to 0.3 µs before the second emission
                {"at": 6, "cmd": "speed", "args": {"value": 8.34e-7}},
                {"at": 10, "cmd": "speed", "args": {"value": 0.045}},     # about 200 coincidences per played second
                {"at": 34, "cmd": "new_world", "args": {"preset": "photon_lhv"}},
                {"at": 34, "cmd": "speed", "args": {"value": 0.045}}]
STORY_NUMBERS = {"n": 5000, "S": 2.82, "se": 0.04, "z": 20}  # the run at 33.9 s (tests/test_u37_screens.py)

# Watch (design §4.1, revised for real detectors): what to look at, at each step of the story (played seconds; the
# script's speed changes sit on the run's own emission times, tests/test_u37_screens.py checks the numbers)
STORY_CAPTIONS = [
    {"at": 0, "hold": 3,
     "text": T("A source in the middle sends pairs of polarisation-entangled photons to Alice (left) and Bob (right), "
               "500 m away on each side, one pair at a time.")},
    {"at": 3, "text": T("At the start of each microsecond, each station picks one of its two polariser settings at "
                        "random (Alice a or a′, Bob b or b′). Each detected photon gives + or −; a real detector misses "
                        "about a third of them, so only about half of the pairs give a coincidence.")},
    {"at": 10, "hold": 4,
     "text": T("Much faster: thousands of pairs. From the counts the run computes the correlations E and S = E(a,b) − "
               "E(a,b′) + E(a′,b) + E(a′,b′). No local theory allows S above 2; here S passes 2 and settles near "
               "2√2 ≈ 2.83.")},
    {"at": 20, "text": T("The error of S shrinks as 1/√N: after about {n:d} coincidences S = {S} ± {se}, more than {z:d} "
                         "standard errors above 2. This assumes that the detected pairs are a fair sample of all "
                         "pairs.", n=STORY_NUMBERS["n"], S=STORY_NUMBERS["S"], se=STORY_NUMBERS["se"],
                         z=STORY_NUMBERS["z"])},
    {"at": 34, "text": T("The same experiment in a world of local hidden variables, a deliberately changed law: each pair "
                         "carries a common hidden polarisation, and each outcome depends only on it and on its own "
                         "polariser.")},
    {"at": 44, "text": T("Here S stays below 2: about 1.4, the most this model gives at any settings (√2).")},
]

VIZ = {
    "id": "u37_bell_test",
    "title": T("The Bell test with entangled pairs"),
    "summary": T("Pairs of photons or of spins ½ fly to two stations with real detectors; each station chooses its "
                 "setting per time slot, fixed or at random (outside the other side's light cone). Coincidences, the "
                 "correlations E, the CHSH parameter S against the bounds 2 and 2√2 under fair sampling, CH and J from "
                 "all the slots without it, accidental coincidences, no signalling."),
    "purpose": T("A study of nonlocal correlations and of the conditions of a loophole-free experiment; the law can be "
                 "replaced on purpose by local hidden variables to see that |S| does not exceed 2, or by Gisin and "
                 "Gisin's model to see a local model pass 2 through the detection loophole."),
    "version": "1.1",
    "schema": SCHEMA,
    "simulation": Simulation,
    "audience": "university",
    "section": "quantum",
    "ui": "standard",
    "teaser": T("Entangled pairs reach two distant stations; the CHSH parameter exceeds 2, the bound of any local theory."),
    "courses": [
        {"text": T("Sakurai & Napolitano, Modern Quantum Mechanics"), "chapters": "3"},
        {"text": T("Griffiths & Schroeter, Introduction to Quantum Mechanics"), "chapters": "12"},
        {"text": T("Bell, Speakable and Unspeakable in Quantum Mechanics"), "chapters": ""},
    ],
    "related": [],
    "recordings": [
        {"id": "story", "preset": "photon_chsh", "seconds": 50, "fps": 20, "speed": None, "seed": 1, "poster": 30,
         "script": STORY_SCRIPT, "captions": STORY_CAPTIONS},
        {"id": "chsh", "preset": "photon_chsh", "seconds": 30, "fps": 10, "speed": 0.04, "seed": 1, "script": [],
         "poster": 25,
         "captions": [{"at": 0, "text": T("Photon pairs, settings chosen at random per slot, real detectors: the four "
                                          "correlations and S build up from the coincidences.")},
                      {"at": 15, "text": T("S settles near 2√2 ≈ 2.83, above the bound 2 of any local theory, under "
                                           "the assumption that the detected pairs are a fair sample.")}]},
        {"id": "local_model", "preset": "photon_lhv", "seconds": 30, "fps": 10, "speed": 0.04, "seed": 1,
         "script": [], "poster": 25,
         "captions": [{"at": 0, "text": T("The same bench in a world of local hidden variables (modified physics).")},
                      {"at": 15, "text": T("S stays near √2 ≈ 1.41, below 2: a local model keeps the bound.")}]},
        {"id": "scan", "preset": "scan", "seconds": 30, "fps": 10, "speed": 0.04, "seed": 1, "script": [],
         "poster": 25,
         "captions": [{"at": 0, "text": T("Fixed settings a = b = 0°: every coincidence is (a, b); the polarisations "
                                          "agree, E = 1.")},
                      {"at": 15, "text": T("With fixed settings the locality loophole is open: the settings are known "
                                           "long before each pair arrives.")}]},
    ],
    # the screens (design §4): Watch with the captioned story and more recordings; Explore = the CHSH bench (156
    # points, shared with Lab work's parts 2 and 3, §5 F9); Lab work, four parts
    "screens": [
        {"id": "watch", "kind": "watch", "recording": "story", "more": ["chsh", "local_model", "scan"]},
        EXPLORE,
        LAB,
    ],
}
