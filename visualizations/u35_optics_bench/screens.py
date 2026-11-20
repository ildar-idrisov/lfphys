# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u35's screens (design ``lfphys/sources/explore_EX2_2026-11-18_design.md`` §3): Watch («One photon at a time at a
surface», recording ``story``, and the recordings ``tir``, ``brewster``, ``spr``), three Explore screens («Boundary»,
«Coatings», «Polarisation») and Lab work, the bench «Reflection and polarisation» in four parts (dark counts, Fresnel's
reflection on the Boundary screen's atlas, Malus's law, polarisation by reflection), with its task sheet.

The story's script is placed on the computed run (design §3.1, round 3): the source sends 2·10⁵ photons per second, so
its first photon leaves about 5 µs after the start while a photon crosses the bench in 2.5 ns. The waiting phase plays
at ``STORY_WAIT`` world seconds per played second, chosen so that the first photon (the first draw of the world's
generator with seed 1, a fixed number) is emitted one frame-step after the played second ``STORY_SLOW_AT``, where the
speed drops to ``STORY_FLIGHT`` (an arm of 0.30 m in 1.2 s); from 9 s, 2 000 photons per played second.
``tests/test_u35_screens.py`` measures the recording again: every caption comes no later than its event and its
numbers are the recording's."""

from __future__ import annotations

import math

from lfphys.core.optics import materials
from lfphys.i18n import T

from .engine.bench import BLOCK_MM, rng_for
from .schema import SCHEMA

#: the story's first photon: the world's first random draw (``Simulation.__init__``: Exponential(1/rate) from the
#: generator of seed 1 and the story's set-up, ``bench.rng_for``)
STORY_RATE = 2e5


def _story_first_emission() -> float:
    params, _errs = SCHEMA.resolve("story", {})
    return float(rng_for(1, params).exponential(1.0 / float(params["rate"])))


STORY_T_E1 = _story_first_emission()
STORY_FPS = 20
STORY_SLOW_AT = 1.45  # played s: the frame after which the first photon leaves the source (a detected one: tests)
#: world seconds per played second while waiting: the frame at STORY_SLOW_AT is 1e-6 of t_e1 before the emission
STORY_WAIT = STORY_T_E1 / (STORY_SLOW_AT * (1.0 + 1e-6))
STORY_FLIGHT = 8.34e-10  # an arm of 0.30 m in air (1.0007 ns) in 1.2 played s
STORY_FAST = 0.01  # 2 000 photons per played second
N_BK7 = float(materials.index("schott_n_bk7", 632.8).real)
THETA_B = math.degrees(math.atan(N_BK7))
THETA_C = math.degrees(math.asin(1.0 / N_BK7))

# Watch (design §3.1): what to look at, at each step of the story (played seconds; the script changes the set-up at the
# same times). The numbers are the run's: the computed probabilities of the set-up (the engine) and, where a caption
# names a measured fraction, the recording's own counts (tests/test_u35_screens.py checks both)
STORY_CAPTIONS = [
    {"at": 0, "hold": 3, "text": T("Photons leave the source one at a time and fall on N-BK7 glass (n = {n:.4g}) at "
                                    "30°. Past the surface, each photon's wave goes both ways: the two faint marks "
                                    "show where it may be found.", n=N_BK7)},
    {"at": 3.5, "text": T("Watch the detectors: one of them clicks, and the photon is found in one place only, "
                          "reflected or transmitted. Which one is random; the run computes only the probabilities R "
                          "and T, from Maxwell's equations. A real detector misses about a third of the photons.")},
    {"at": 9, "text": T("Much faster: thousands of photons. The surface reflects {R:.3g} % of them; the transmitted "
                        "ones lose another {l:.2g} % in the glass block, at its curved face and in the glass. Of the "
                        "photons that reach a detector the shares settle at the computed {r:.3g} % reflected and "
                        "{t:.4g} % transmitted (the black ticks), within the counts' errors.",
                        R=4.350, l=4.775, r=4.558, t=95.44)},
    {"at": 17, "text": T("The table turns to Brewster's angle, {b:.1f}° = arctan {n:.4g}, and an analyser is put "
                         "before the reflection detector, along p (in the plane of incidence): no reflected photon "
                         "passes it. Its pass detector clicks only in the dark, about once in a played second.",
                         b=THETA_B, n=N_BK7)},
    {"at": 22, "text": T("The analyser turned along s: every reflected photon passes. At Brewster's angle reflection "
                         "polarises light completely.")},
    {"at": 27, "text": T("Now the light goes from inside the glass into air, at 30°: {r:.3g} % is reflected.",
                         r=5.850)},
    {"at": 34, "text": T("At 45°, beyond the critical angle of {c:.1f}°, no photon gets out: total internal "
                         "reflection. The detector in air clicks only in the dark.", c=THETA_C)},
    {"at": 41, "text": T("A second glass block 200 nm behind the face: now nearly half of the photons cross the air "
                         "gap. This is frustrated total reflection: the photons tunnel.")},
]

_STORY_SCRIPT = [
    {"at": 0, "cmd": "speed", "args": {"value": STORY_WAIT}},
    {"at": STORY_SLOW_AT, "cmd": "speed", "args": {"value": STORY_FLIGHT}},
    {"at": 9, "cmd": "speed", "args": {"value": STORY_FAST}},
    {"at": 17, "cmd": "set", "args": {"values": {"theta_deg": round(THETA_B, 3), "anaR": "ideal", "anaR_deg": 0.0}}},
    {"at": 22, "cmd": "set", "args": {"values": {"anaR_deg": 90.0}}},
    {"at": 27, "cmd": "set", "args": {"values": {"med_in": "schott_n_bk7", "med_out": "air", "theta_deg": 30.0,
                                                 "structure": "tir", "tir_gap_nm": 0.0, "anaR": "out"}}},
    {"at": 34, "cmd": "set", "args": {"values": {"theta_deg": 45.0}}},
    {"at": 41, "cmd": "set", "args": {"values": {"tir_gap_nm": 200.0}}},
]

#: what the recordings and the screens pack: drawn arrays quantised (QUANT_SAFE in web/view.js), the measurables never
_Q_ANGLE = {"segment.th|Rs|Ts|As|Rp|Tp|Ap|Rc|Tc|Ac": "u16"}
_Q_SPEC = {"segment.lam|lRs|lTs|lAs|lRp|lTp|lAp|lRc|lTc|lAc": "u16"}
_Q_COMMON = {"segment.z|E2": "u16", "clicks.t": "u16", "frame.fl": "u16"}
_DROP_SPEC = ["segment.lam", "segment.lR*", "segment.lT*", "segment.lA*"]
_DROP_ANGLE = ["segment.th", "segment.R*", "segment.T*", "segment.A*"]

RECORDINGS = [
    {"id": "story", "preset": "story", "seconds": 50, "fps": STORY_FPS, "speed": None, "seed": 1, "poster": 16,
     "script": _STORY_SCRIPT, "captions": STORY_CAPTIONS, "quantize": {**_Q_ANGLE, **_Q_SPEC, **_Q_COMMON}},
    {"id": "tir", "preset": "tir", "seconds": 30, "fps": 20, "speed": 1e-3, "seed": 1, "script": [], "poster": 25,
     "quantize": {**_Q_ANGLE, **_Q_SPEC, **_Q_COMMON},
     "captions": [{"at": 0, "text": T("From inside N-BK7 at 60°, beyond the critical angle of {c:.1f}°: every photon "
                                      "is reflected, none reaches the detector in air.", c=THETA_C)},
                  {"at": 10, "text": T("Beyond the face the field does not vanish: it decays within a fraction of a "
                                       "wavelength (the evanescent wave, the strip on the right). Its phase makes the "
                                       "reflected light elliptical: the s and p parts come back shifted.")}]},
    {"id": "brewster", "preset": "brewster", "seconds": 30, "fps": 20, "speed": 1e-3, "seed": 1, "script": [],
     "poster": 25, "quantize": {**_Q_ANGLE, **_Q_SPEC, **_Q_COMMON},
     "captions": [{"at": 0, "text": T("Unpolarised photons at Brewster's angle of N-BK7, {b:.2f}°: about {r:.2g} % are "
                                      "reflected.", b=THETA_B, r=7.727)},
                  {"at": 10, "text": T("The reflected beam's polarisation, computed from its density matrix, is a line "
                                       "along s: at this angle p light is not reflected at all.")}]},
    {"id": "spr", "preset": "spr", "seconds": 30, "fps": 20, "speed": 1e-3, "seed": 1, "script": [], "poster": 25,
     "quantize": {**_Q_ANGLE, **_Q_SPEC, **_Q_COMMON},
     "captions": [{"at": 0, "text": T("p photons through an N-BK7 prism onto 50 nm of gold, at {a}°: nearly all of "
                                      "them vanish in the metal.", a=43.773)},
                  {"at": 10, "text": T("Here R_p is smallest, about {r:.1g} %: the light excites a surface plasmon at "
                                       "the gold–air boundary and is absorbed (the curve R(θ) on the right).",
                                       r=0.38)}]},
]

# --- Explore ----------------------------------------------------------------------------------------------------------
#: the reflection bench's angles: 1° steps where the Brewster and critical angles of the three glasses lie
BOUNDARY_TH = [0.0, 10.0, 20.0, 30.0] + [float(x) for x in range(33, 63)] + [66.0, 70.0, 80.0, 85.0]
SAMPLES = ["bk7_air", "bk7_in", "f2_air", "f2_in", "sf11_air", "sf11_in"]
_G = {"bk7": "schott_n_bk7", "f2": "schott_n_f2", "sf11": "schott_n_sf11"}
SAMPLE_CONTROL = {
    "id": "sample", "label": T("Glass and side"), "values": SAMPLES, "default": "bk7_air",
    "labels": [T("N-BK7 from air"), T("N-BK7 inside"), T("N-F2 from air"), T("N-F2 inside"), T("N-SF11 from air"),
               T("N-SF11 inside")],
    "sets": {"med_in": ["air" if s.endswith("air") else _G[s.split("_")[0]] for s in SAMPLES],
             "med_out": [_G[s.split("_")[0]] if s.endswith("air") else "air" for s in SAMPLES]}}
#: part 4's glass, named by its catalogue name (a compound control: a select of a parameter shows its raw value,
#: STATUS V53 (v))
GLASS_CONTROL = {"id": "glass", "label": T("Glass"), "values": list(_G), "default": "bk7",
                 "labels": [T("N-BK7"), T("N-F2"), T("N-SF11")], "sets": {"med_out": list(_G.values())}}
#: a select's values named in every language (review R2-P F9: shown raw, "s" became «с», the msgid of seconds, and
#: "real" stayed English): compound controls, the way a control names its values (RULES §10 «Controls»)
LIGHT_CONTROL = {"id": "light", "label": T("Polarisation"), "values": ["s", "p"], "default": "s",
                 "labels": [T("s (TE)"), T("p (TM)")], "sets": {"pol": ["s", "p"]}}
ANALYSER_CONTROL = {"id": "analyser", "label": T("Analyser"), "values": ["ideal", "real"], "default": "ideal",
                    "labels": [T("ideal"), T("imperfect")], "sets": {"anaT": ["ideal", "real"]}}
COATINGS = ["bare", "mgf2_bulk", "mgf2_film", "hl4", "hl8", "al100", "ag100"]
COATING_CONTROL = {
    "id": "coating", "label": T("Coating"), "values": COATINGS, "default": "mgf2_film",
    "labels": [T("bare N-BK7"), T("λ/4 MgF₂ (crystal, Dodge)"), T("λ/4 MgF₂ film (Rodríguez-de Marcos et al.)"),
               T("Ta₂O₅/SiO₂ films, (H L)×4 (Gao et al.)"), T("Ta₂O₅/SiO₂ films, (H L)×8 (Gao et al.)"),
               T("aluminium, 100 nm (Rakić)"), T("silver, 100 nm (Johnson and Christy)")],
    "sets": {"structure": ["interface", "ar", "ar", "bragg", "bragg", "metal", "metal"],
             "ar_mat": ["mgf2_film_rodriguez", "mgf2_dodge_o", "mgf2_film_rodriguez", "mgf2_film_rodriguez",
                        "mgf2_film_rodriguez", "mgf2_film_rodriguez", "mgf2_film_rodriguez"],
             "pairs": [8, 8, 8, 4, 8, 8, 8],
             "metal_mat": ["au_johnson_christy"] * 5 + ["al_rakic", "ag_johnson_christy"],
             "metal_d_nm": [30.0] * 5 + [100.0, 100.0]}}
POL_TH = [35.0, 40.0, 42.0, 45.0, 48.0, 51.0, 54.0, 57.0, 60.0, 65.0, 70.0, 80.0]
ALPHA_15 = [float(x) for x in range(0, 180, 15)]

_EXPLORE_COMMON = {"acts": "now", "time": "buildup", "seed": 1, "traces": 0}
SCREEN_BOUNDARY = {
    "id": "explore", "kind": "explore", "label": T("Boundary"), "preset": "boundary", "fixed": {"ref_s": 0.1},
    "controls": [{"param": "theta_deg", "values": BOUNDARY_TH, "default": 30.0, "label": T("Angle of incidence θ"),
                  "unit": "°"},
                 SAMPLE_CONTROL,
                 LIGHT_CONTROL],
    **_EXPLORE_COMMON, "frame_dt": 0.02, "speed": 0.01, "stop": {"world_s": 0.1},
    "drop": {"blobs": _DROP_SPEC}, "quantize": {**_Q_ANGLE, **_Q_COMMON},
    "overlays": ["beams", "photons", "field", "curves", "ellipse"],
    "readouts": ["R_inc", "T_inc", "R_frac", "n_clicks"]}
SCREEN_COATINGS = {
    "id": "coatings", "kind": "explore", "label": T("Coatings"), "preset": "coatings", "fixed": {},
    "controls": [{"param": "lam_nm", "values": [float(x) for x in range(400, 701, 25)], "default": 550.0,
                  "label": T("Wavelength λ"), "unit": "nm"},
                 COATING_CONTROL],
    **_EXPLORE_COMMON, "frame_dt": 0.0005, "speed": 0.001, "stop": {"world_s": 0.01},
    "drop": {"blobs": _DROP_ANGLE}, "quantize": {**_Q_SPEC, **_Q_COMMON},
    "overlays": ["beams", "photons", "field", "curves"], "readouts": ["R_frac", "T_frac", "n_clicks"]}
SCREEN_POLARISATION = {
    "id": "polarisation", "kind": "explore", "label": T("Polarisation"), "preset": "polarisation", "fixed": {},
    "controls": [{"param": "theta_deg", "values": POL_TH, "default": 51.0, "label": T("Angle of incidence θ"),
                  "unit": "°"},
                 {"param": "anaR_deg", "values": ALPHA_15, "default": 135.0, "label": T("Analyser's angle α"),
                  "unit": "°"}],
    **_EXPLORE_COMMON, "frame_dt": 0.02, "speed": 0.01, "stop": {"world_s": 0.1},
    "drop": {"blobs": _DROP_SPEC}, "quantize": {**_Q_ANGLE, **_Q_COMMON},
    "overlays": ["beams", "photons", "field", "curves", "ellipse"], "readouts": ["fR_pass", "n_R", "n_clicks"]}

# --- Lab work: the bench «Reflection and polarisation» (design §3.4) --------------------------------------------------
# The texts of LAB (titles, goals, hints, the instruments' names, the task sheet's basis, goal, bench, procedure, record
# and variants) and their translations in locales/ are Site Materials: CC BY-NC-SA 4.0 (LICENSE.md §1 item 8, §9). The
# code and the other data around them stay under LicenseRef-lfphys-Research-1.0.
DEAD_TIME = 22e-9  # the detectors' dead time (SPCM-AQRH, Table 1), in the dead-time correction's formula columns
DARK_RATE = 100.0  # the detectors' dark-count rate (SPCM-AQRH-14 grade maximum), in the dark-subtraction columns

INSTRUMENTS = {
    "table": {"kind": "readout", "label": T("Rotary table"), "unit": "°", "division": 1, "error": 0,
              "error_note": T("the table is set at its 1° marks"), "reads": "control:theta_deg"},
    "gate": {"kind": "readout", "label": T("Counter's gate"), "unit": "s", "division": 0.1, "error": 0,
             "error_note": T("the counter's gate is set exactly"), "reads": "control:gate_s"},
    "clock": {"kind": "readout", "label": T("Counter's clock"), "unit": "s", "division": 0.001, "error": 0,
              "error_note": T("the counter's quartz clock"), "reads": "t_c"},
    "det_r": {"kind": "counter", "label": T("Reflection detector"), "unit": "", "error": "poisson", "reads": "n_R"},
    "det_t": {"kind": "counter", "label": T("Transmission detector"), "unit": "", "error": "poisson", "reads": "n_T"},
    "ref": {"kind": "counter", "label": T("Reference count N₀ (the block removed)"),
            "unit": "", "error": "poisson", "reads": "n_0"},
    "ref_t": {"kind": "readout", "label": T("Reference count's gate t₀"), "unit": "s", "division": 0.01, "error": 0,
              "error_note": T("the counter's gate is set exactly"), "reads": "control:ref_s"},
    "src": {"kind": "readout", "label": T("Source polariser's scale ψ"), "unit": "°", "division": 1, "error": 0,
            "error_note": T("the source's polariser is set at its marks"), "reads": "control:psi_deg"},
    "ana_t": {"kind": "readout", "label": T("Transmission analyser's scale α"), "unit": "°", "division": 1,
              "error": 0, "error_note": T("the analyser is set at its marks"), "reads": "control:anaT_deg"},
    "ana_r": {"kind": "readout", "label": T("Reflection analyser's scale α"), "unit": "°", "division": 1,
              "error": 0, "error_note": T("the analyser is set at its marks"), "reads": "control:anaR_deg"},
    "pass_t": {"kind": "counter", "label": T("Transmission analyser: pass-port detector"), "unit": "",
               "error": "poisson", "reads": "n_Tp"},
    "reject_t": {"kind": "counter", "label": T("Transmission analyser: reject-port detector"), "unit": "",
                 "error": "poisson", "reads": "n_Tr"},
    "pass_r": {"kind": "counter", "label": T("Reflection analyser: pass-port detector"), "unit": "",
               "error": "poisson", "reads": "n_Rp"},
    "reject_r": {"kind": "counter", "label": T("Reflection analyser: reject-port detector"), "unit": "",
                 "error": "poisson", "reads": "n_Rr"},
}

_GLASSES = (("bk7", "N-BK7"), ("f2", "N-F2"), ("sf11", "N-SF11"))
_FRESNEL_LAWS = (
    [{"x": "x", "y": "ysd", "model": "line", "quantity": "intercept", "label": T("{glass}: n²", glass=g),
      "unit": "", "reference": f"ns2_{k}"} for k, g in _GLASSES]
    + [{"x": "x", "y": "ysd", "model": "line", "quantity": "slope", "label": T("slope −1"), "unit": "",
        "reference": "ys1_bk7"}]
    + [{"x": "x", "y": "ypd", "model": "line", "quantity": "intercept", "label": T("{glass}: 1/n²", glass=g),
        "unit": "", "reference": f"inv2_{k}"} for k, g in _GLASSES]
    + [{"x": "th", "y": "Rid", "model": "quadratic", "quantity": "vertex", "label": T("N-BK7: θ_B"), "unit": "°",
        "reference": "thb_bk7"}]  # every glass's θ_B: part 4's laws
    + [{"x": "x", "y": "ypd", "model": "line", "quantity": "intercept", "label": T("N-BK7 from inside: sin²θ_c"),
        "unit": "", "reference": "thc_bk7"}])  # the teacher's variant «N-BK7 from inside»
#: the formula columns of part 2: R from the two detectors (R) and against the reference count (R_i), so with the dark
#: counts subtracted (R_d) and with the dead time also corrected (R_c), T against the reference (T_i), and the
#: linearisations y_s, y_p from R and from R_d
_D, _TD = DARK_RATE, DEAD_TIME


def _y(rid: str, kind: str) -> str:
    """y_s = (cos θ (1 + √R)/(1 − √R))² or y_p = (cos θ (1 − √R)/(1 + √R))² of the column rid."""
    a, b = ("+", "-") if kind == "s" else ("-", "+")
    return f"(cosd(th) * (1 {a} sqrt({rid})) / (1 {b} sqrt({rid})))^2"


_FRESNEL_COLUMNS = [
    {"id": "th", "label": T("θ, °"), "from": "table"},
    {"id": "tc", "label": T("t, s"), "from": "clock"},
    {"id": "NR", "label": T("N_R, clicks"), "from": "det_r"},
    {"id": "NT", "label": T("N_T, clicks"), "from": "det_t"},
    {"id": "N0", "label": T("N₀, clicks (the block removed)"), "from": "ref"},
    {"id": "t0", "label": T("t₀, s"), "from": "ref_t"},
    {"id": "R", "label": T("R = N_R/(N_R + N_T)"), "expr": "NR / (NR + NT)"},
    {"id": "Ri", "label": T("R_i = (N_R/t)/(N₀/t₀)"), "expr": "(NR / tc) / (N0 / t0)"},
    {"id": "Rid", "label": T("R_d: R_i, dark counts subtracted"),
     "expr": f"((NR - {_D!r} * tc) / tc) / ((N0 - {_D!r} * t0) / t0)"},
    {"id": "Ric", "label": T("R_c: R_d, dead time corrected"),
     "expr": f"((NR / tc) / (1 - NR / tc * {_TD!r}) - {_D!r}) / ((N0 / t0) / (1 - N0 / t0 * {_TD!r}) - {_D!r})"},
    {"id": "Ti", "label": T("T_i = (N_T/t)/(N₀/t₀)"), "expr": "(NT / tc) / (N0 / t0)"},
    {"id": "x", "label": T("x = sin²θ"), "expr": "sind(th)^2"},
    {"id": "ys", "label": T("y_s from R"), "expr": _y("R", "s")},
    {"id": "yp", "label": T("y_p from R"), "expr": _y("R", "p")},
    {"id": "ysd", "label": T("y_s from R_d"), "expr": _y("Rid", "s")},
    {"id": "ypd", "label": T("y_p from R_d"), "expr": _y("Rid", "p")},
]

STEPS = [
    {"id": "dark", "title": T("Dark counts"),
     "goal": T("With the source's shutter closed, count each detector's clicks for a set time: their dark counts."),
     "hint": T("A count N has the error √N; the rate is N divided by the counting time."),
     "preset": "lab_dark", "fixed": {},
     "controls": [{"param": "gate_s", "values": [0.1, 0.5, 1.0], "default": 0.5, "label": T("Counting time"),
                   "unit": "s"}],
     "frame_dt": 0.05, "speed": 0.1, "stop": {"events": {"gate": 1}, "after_s": 0.0, "max_world_s": 1.5},
     "drop": {"blobs": _DROP_SPEC}, "quantize": {**_Q_ANGLE, **_Q_COMMON},
     "instruments": ["gate", "det_r", "det_t"],
     "columns": [{"id": "tc", "label": T("t, s"), "from": "gate"},
                 {"id": "NR", "label": T("N_R, clicks"), "from": "det_r"},
                 {"id": "NT", "label": T("N_T, clicks"), "from": "det_t"},
                 {"id": "rR", "label": T("N_R/t, s⁻¹"), "expr": "NR / tc"},
                 {"id": "rT", "label": T("N_T/t, s⁻¹"), "expr": "NT / tc"}],
     "plot": {"x": "tc", "y": "NR", "fit": "line0", "fits": ["line0", "line"]},
     "laws": [{"x": "tc", "y": "NR", "model": "line0", "quantity": "slope", "label": T("dark-count rate"),
               "unit": T("s⁻¹"), "reference": "rate_r"},
              {"x": "tc", "y": "NT", "model": "line0", "quantity": "slope", "label": T("dark-count rate"),
               "unit": T("s⁻¹"), "reference": "rate_t"}],
     "overlays": ["beams", "photons"], "readouts": ["n_R", "n_T", "t_c"]},
    {"id": "fresnel", "atlas": "explore", "title": T("Fresnel's reflection"),
     "goal": T("Count the reflected and the transmitted photons of s and p light at angles from 0° to 85° and find the "
               "glass's index from them."),
     "hint": T("y_s and y_p are lines in x = sin²θ for light from air (y_p below θ_B); R_i, R_d: per incident photon "
               "(N₀)."),
     "speed": 0.01, "instruments": ["table", "clock", "det_r", "det_t", "ref", "ref_t"],
     "columns": _FRESNEL_COLUMNS,
     "plot": {"x": "x", "y": "ys", "fit": "line", "fits": ["line", "line0", "quadratic"]},
     "laws": _FRESNEL_LAWS, "overlays": ["beams", "photons", "field", "curves", "ellipse"],
     "readouts": ["R_frac", "T_frac", "n_clicks"]},
    {"id": "malus", "title": T("Malus's law"),
     "goal": T("Send linearly polarised photons straight into the analyser and count both its ports at every angle of "
               "the analyser."),
     "hint": T("I = N_pass/(N_pass + N_reject) against cos²(α − ψ); try the ideal and the imperfect analyser."),
     "preset": "lab_malus", "fixed": {},
     "controls": [{"param": "anaT_deg", "values": [float(x) for x in range(0, 181, 10)], "default": 0.0,
                   "label": T("Analyser's angle α"), "unit": "°"},
                  {"param": "psi_deg", "values": [0.0, 30.0, 60.0], "default": 30.0,
                   "label": T("Source's polarisation ψ"), "unit": "°"},
                  ANALYSER_CONTROL],
     "frame_dt": 0.02, "speed": 0.01, "stop": {"world_s": 0.1},
     "drop": {"blobs": _DROP_SPEC}, "quantize": {**_Q_ANGLE, **_Q_COMMON},
     "instruments": ["ana_t", "src", "pass_t", "reject_t"],
     "columns": [{"id": "a", "label": T("α, °"), "from": "ana_t"},
                 {"id": "psi", "label": T("ψ, °"), "from": "src"},
                 {"id": "Np", "label": T("N_pass, clicks"), "from": "pass_t"},
                 {"id": "Nr", "label": T("N_reject, clicks"), "from": "reject_t"},
                 {"id": "I", "label": T("I = N_pass/(N_pass + N_reject)"), "expr": "Np / (Np + Nr)"},
                 {"id": "c2", "label": T("cos²(α − ψ)"), "expr": "cosd(a - psi)^2"},
                 {"id": "c1", "label": T("cos(α − ψ)"), "expr": "cosd(a - psi)"}],
     "plot": {"x": "c2", "y": "I", "fit": "line0", "fits": ["line0", "line", "quadratic"]},
     "laws": [{"x": "c2", "y": "I", "model": "line0", "quantity": "slope", "label": T("ideal analyser: k₁ = 1"),
               "unit": "", "reference": "slope0_ideal"},
              {"x": "c2", "y": "I", "model": "line", "quantity": "slope", "label": T("imperfect analyser: k₁ − k₂"),
               "unit": "", "reference": "slope_real"},
              {"x": "c2", "y": "I", "model": "line", "quantity": "intercept", "label": T("imperfect analyser: k₂"),
               "unit": "", "reference": "icept_real"}],
     "overlays": ["beams", "photons", "ellipse"], "readouts": ["fT_pass", "n_T"]},
    {"id": "reflection", "title": T("Polarisation by reflection"),
     "goal": T("Reflect unpolarised photons from the glass and count the analyser's two ports; find the angle at which "
               "the reflected light is completely polarised."),
     "hint": T("With the analyser along p (α = 0°), f = N_pass/(N_pass + N_reject) is the share of p light in the "
               "reflected beam and P = 1 − 2f its degree of polarisation."),
     "preset": "lab_reflection", "fixed": {},
     "controls": [{"param": "theta_deg", "values": [40.0, 45.0, 50.0, 54.0, 55.0, 56.0, 57.0, 58.0, 59.0, 60.0, 61.0,
                                                    62.0, 66.0, 70.0], "default": 56.0,
                   "label": T("Angle of incidence θ"), "unit": "°"},
                  {"param": "anaR_deg", "values": [float(x) for x in range(0, 91, 15)], "default": 0.0,
                   "label": T("Analyser's angle α"), "unit": "°"},
                  GLASS_CONTROL],
     "frame_dt": 0.1, "speed": 0.05, "stop": {"world_s": 0.5},
     "drop": {"blobs": _DROP_SPEC}, "quantize": {**_Q_ANGLE, **_Q_COMMON},
     "instruments": ["table", "ana_r", "clock", "pass_r", "reject_r"],
     "columns": [{"id": "th", "label": T("θ, °"), "from": "table"},
                 {"id": "a", "label": T("α, °"), "from": "ana_r"},
                 {"id": "tc", "label": T("t, s"), "from": "clock"},
                 {"id": "Np", "label": T("N_pass, clicks"), "from": "pass_r"},
                 {"id": "Nr", "label": T("N_reject, clicks"), "from": "reject_r"},
                 {"id": "Ns", "label": T("N_pass + N_reject, both ports"), "expr": "Np + Nr"},
                 {"id": "f", "label": T("f = N_pass/(N_pass + N_reject)"), "expr": "Np / (Np + Nr)"},
                 {"id": "P", "label": T("P = 1 − 2f"), "expr": "1 - 2 * f"},
                 {"id": "fd", "label": T("f with the dark counts subtracted ({d:g} s⁻¹ × t)", d=DARK_RATE),
                  "expr": f"(Np - {DARK_RATE!r} * tc) / (Np + Nr - 2 * {DARK_RATE!r} * tc)"},
                 {"id": "Pd", "label": T("P = 1 − 2f, dark counts subtracted"), "expr": "1 - 2 * fd"}],
     "plot": {"x": "th", "y": "f", "fit": "quadratic", "fits": ["quadratic", "line"]},
     "laws": [{"x": "th", "y": "P", "model": "quadratic", "quantity": "vertex",
               "label": T("{glass}: θ_B, where P = (R_s − R_p)/(R_s + R_p) is largest", glass=g), "unit": "°",
               "reference": f"dop_{k}"} for k, g in _GLASSES],
     "overlays": ["beams", "photons", "field", "curves", "ellipse"], "readouts": ["fR_pass", "n_R"]},
]

_QUOTE_SRC_CMU = ("Carnegie Mellon University, 33-353 Intermediate Optics, Lab 1: Fresnel Relations and Snell's Law "
                  "(2010)")
_QUOTE_SRC_RUT = "Rutgers University, Physics 389: Fresnel Equations and Electromagnetic Boundary Conditions"
_QUOTE_SRC_TOR = "University of Toronto, PHY293/PHY294 laboratory: Polarization of Light"
WORKSHEET = {
    "basis": [
        {"text": T("Part 2 follows the reflection of s and p light from a glass and the angles that give its index"),
         "source": _QUOTE_SRC_CMU,
         "quote": "Find Brewster's angle, the angle for which there is no reflected beam for light polarized in the "
                  "plane of reflection.", "quote_lang": "en"},
        {"text": T("Part 2: fitting the data with Fresnel's equations"), "source": _QUOTE_SRC_RUT,
         "quote": "By fitting your data with Fresnel’s equations you will obtain the following: i) the index "
                  "refraction ii) the critical angle iii) Brewster’s angle.", "quote_lang": "en"},
        {"text": T("Part 2: the incident light, with the block removed"),
         "source": _QUOTE_SRC_RUT,
         "quote": "Observe and record I0 (the laser beam power at zero degrees before sample placement).",
         "quote_lang": "en"},
        {"text": T("Part 3: Malus's law with two polarising elements"), "source": _QUOTE_SRC_TOR,
         "quote": "It applies to any two polarizing elements whose transmission directions make an angle θ with each "
                  "other.", "quote_lang": "en"},
        {"text": T("Part 4: polarisation by reflection and Brewster's angle"), "source": _QUOTE_SRC_TOR,
         "quote": "When light is reflected from a flat surface, the reflected light is partially polarized.",
         "quote_lang": "en"},
    ],
    "goal": T("Find the refractive index of a glass from the reflection of s and p light, and check Malus's law and "
              "the polarisation of reflected light."),
    "bench": [T("A half-cylinder (a D-shaped block, radius {r:g} mm) of N-BK7, N-F2 or N-SF11 glass on a rotary table"
                " (1° marks); light from air onto the flat face or from inside through the curved face; a source of "
                "single photons (632.8 nm, 2·10⁵ per second), polarised s, p, linearly at an angle or unpolarised, "
                "with a shutter; single-photon detectors of reflected and transmitted photons (efficiency 0.65, 100 "
                "dark counts per second, dead time 22 ns), the transmission detector also counting the incident "
                "photons with the block lifted off (N₀ in 0.1 s); a rotatable analyser with a detector on each port, "
                "ideal or imperfect.",
                r=BLOCK_MM)],
    "procedure": [T("1. With the shutter closed, count each detector's dark counts."),
                  T("2. With the block lifted off, count the incident photons at the transmission detector: N₀ in t₀."),
                  T("3. For s light from air, count reflected and transmitted photons at angles from 0° to 80° and "
                    "plot y_s against sin²θ."),
                  T("4. Repeat for p light below the angle where the reflection vanishes, with y_p."),
                  T("5. Set the source at ψ and record the analyser's counts from 0° to 180°; plot them against "
                    "cos²(α − ψ)."),
                  T("6. With unpolarised light, set the analyser along p and find the angle of complete polarisation."),
                  T("Decide where the dark counts, the dead time and the block matter.")],
    "record": [T("the counts with their errors, the plots and fits (model, points used, parameters with errors, χ²)"),
               T("the dark counts and the reference count N₀, and how you used them"),
               T("the index n found in each way and Brewster's angle"),
               T("why you chose these angles")],
    "record_rows": 18,
    "variants": [
        {"id": "f2", "label": T("N-F2 glass"),
         "values": {"fresnel": {"sample": "f2_air"}, "reflection": {"glass": "f2"}}},
        {"id": "sf11", "label": T("N-SF11 glass"),
         "values": {"fresnel": {"sample": "sf11_air"}, "reflection": {"glass": "sf11"}}},
        {"id": "inside", "label": T("N-BK7 from inside: the critical angle"), "steps": ["dark", "fresnel"],
         "values": {"fresnel": {"sample": "bk7_in"}},
         "text": {"goal": T("Find the critical angle of N-BK7 from inside the glass and the index it gives.")}},
        {"id": "imperfect", "label": T("Malus's law with the imperfect analyser, ψ = 60°"), "steps": ["malus"],
         "values": {"malus": {"analyser": "real", "psi_deg": 60.0}},
         "text": {"goal": T("Check Malus's law with an imperfect analyser and find its k₁ and k₂.")}},
    ],
}

LAB = {"id": "lab", "kind": "lab", "instruments": INSTRUMENTS, "steps": STEPS, "worksheet": WORKSHEET}

SCREENS = [
    {"id": "watch", "kind": "watch", "recording": "story", "more": ["tir", "brewster", "spr"]},
    SCREEN_BOUNDARY, SCREEN_COATINGS, SCREEN_POLARISATION, LAB,
]
