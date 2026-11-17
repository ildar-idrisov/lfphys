# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u32: the double-slit experiment with single particles, which-path marks and observers.

What the run computes (README.md of this folder has the model in full):
* the wave of every particle behind the slits (closed-form Fresnel solution, checked against the exact
  Rayleigh-Sommerfeld integral in every run), with the particle's own wavelength, source point and kick;
* the marks it carries from each slit (polarization/spin elements, a which-path qubit, a scattered photon,
  Aharonov-Bohm phase, collapse-model hits) and the Born rule on the screen with them;
* a stream of individual detections in time; the pattern is the accumulation of these events;
* the run's own ensemble prediction, the near-field map and the Bohmian / energy-flow lines of the wave;
* checks against closed forms: wavelength, fringe period, paraxial accuracy, Englert's duality, Chapman's
  dipole coherence, Sorkin's three-slit parameter, no-signalling of the detector reading.
"""

from __future__ import annotations

import math

import numpy as np
from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from lfviz.sim import Simulation as BaseSimulation

from lfphys.core.em import slit as vslit
from lfphys.core.quantum import marks, scattering
from lfphys.core.quantum.particles import EV, H, C, SPECIES, make
from lfphys.i18n import T, is_t
from lfphys.theories.approx import kirchhoff, paraxial
from lfphys.theories.approx import paraxial_ensemble as ens
from lfphys.theories.interpretations import bohm
from lfphys.tools import stats

from .engine.experiment import (ELEMENT_NAMES, FLAG_DARK, FLAG_MIX, Apparatus, Experiment, Geometry, Laws,
                                Source, _join)


def _p(*a, **k):
    return Param(*a, **k)


def _option_show_if_supported() -> bool:
    """Whether the framework takes options (value, label, show_if) (review UX-params P17, accepted 2026-11-05): until it
    does, the options are given as pairs and the world's refusals are the only guard."""
    try:
        sch = Schema([Param("_t", "t", "select", "a", standard="a",
                            options=[("a", "A", {"_t": ["a"]}), ("b", "B", {"_t": ["b"]})])])
        sch.to_json()
        sch.resolve(None, {"_t": "zz"})
        sch.modifications({"_t": "b"})
        return True
    except Exception:  # noqa: BLE001 - an older framework unpacks options as pairs
        return False


OPTION_SHOW_IF = _option_show_if_supported()


def _opts(items):
    """Options with their own show_if where the framework supports it, else plain (value, label) pairs."""
    return [tuple(o) if OPTION_SHOW_IF else tuple(o[:2]) for o in items]


PHOT = {"species": ["photon"]}
SPIN = {"species": ["electron", "neutron", "custom"]}
POLARIZABLE = {"species": ["photon", "electron", "neutron", "custom"]}
MASSIVE = {"species": ["electron", "neutron", "he4", "c60", "custom"]}
MIC_SPECIES = ("electron", "he4", "c60", "custom")  # charged (Thomson) or polarisable (Rayleigh) dipole scatterers
ELEM_OPTIONS = _opts([("none", T("none")), ("polarizer", T("polariser (photon)"), PHOT),
                      ("hwp", T("λ/2 plate (photon)"), PHOT), ("qwp", T("λ/4 plate (photon)"), PHOT),
                      ("rot_y", T("spin rotation about y (spin ½)"), SPIN),
                      ("filter", T("spin filter (spin ½)"), SPIN), ("phase", T("phase shift")),
                      ("block", T("shutter"))])
# which elements act on which internal state (lfphys.core.quantum.marks.element_matrix)
ELEM_FOR = {"pol": ("polarizer", "hwp", "qwp", "phase", "block"), "spin": ("rot_y", "filter", "phase", "block"),
            None: ("phase", "block")}
# exact Rayleigh-Sommerfeld checks: at most this many kernel evaluations per map column or screen check (a few
# seconds); beyond it a column is reported as not verified instead of being computed for minutes
RS_BUDGET = 2e7
# review UX-params P8: every dark count is an event of the record (time, place, flags); a dark rate far above the
# source's made one frame draw ~2e9 events (31 GB). At most this many dark counts per emitted particle (beyond it the
# screen shows only noise: at 100 the dark counts per bin exceed the pattern's peak tenfold), and at most
# STEP_EVENTS events (signal + dark) per step of the world (max_step)
DARK_PER_PARTICLE_MAX = 100.0
COH_DARK = 1e-10  # a slit passing less than this share of the other's is dark: |gamma_12| undefined (P15)
STEP_EVENTS = 4000.0
# review UX-params P18: the screen's expectation is computed on the screen grid extended by the largest shift a
# particle can get on its way (the microscope's recoil, GRW hits, the source's width); its FFT convolution doubles it.
# At most this many bytes for that computation (a λ_probe of 0.001 nm asked for 2 GiB in one array)
SCREEN_BYTES_MAX = 1.0 * 2 ** 30
# vector mode: slits wider than this (k a = 130: 20.7 wavelengths) are refused (the cost of the solution: ~17 s for a
# thin screen, ~21 s for a thick one at the cap, measured in the processing of review B8; for such slits the scalar and
# vector results differ by O(1/(k a)))
VEC_KA_MAX = 130.0
VEC_WIDTH_MAX = VEC_KA_MAX / (2 * math.pi)  # the same limit in wavelengths (20.7)

_G_PART, _G_SRC, _G_SLITS = T("Particle"), T("Source"), T("Slits and screen")
_G_OBS, _G_LAWS, _G_SHOW = T("Observer and elements"), T("Laws (modifications)"), T("Display")

SCHEMA = Schema([
    _p("species", T("Particle"), "select", "photon", group=_G_PART,
       options=[(k, v[0]) for k, v in SPECIES.items()]),
    _p("energy_by", T("Set by"), "select", "lambda", group=_G_PART,
       options=_opts([("lambda", T("wavelength")), ("ekin", T("energy (photon: hν; particle: kinetic)")),
                      ("speed", T("speed (massive)"), MASSIVE), ("freq", T("frequency (photon)"), PHOT)])),
    _p("lam_nm", T("Wavelength, nm"), "float", 632.8, group=_G_PART, min=1e-6, max=1e9, log=True,
       show_if={"energy_by": ["lambda"]}),
    _p("ekin_ev", T("Energy, eV"), "float", 50000.0, group=_G_PART, min=1e-12, max=1e12, log=True,
       show_if={"energy_by": ["ekin"]}),
    _p("speed_ms", T("Speed, m/s"), "float", 200.0, group=_G_PART, min=1e-6, max=2.99e8, log=True,
       show_if={"energy_by": ["speed"]}),
    _p("freq_thz", T("Frequency, THz"), "float", 473.6, group=_G_PART, min=1e-6, max=1e12, log=True,
       show_if={"energy_by": ["freq"]}),
    _p("dlam_rel", T("Spectral width σ (ln λ)"), "float", 0.0, group=_G_PART, min=0.0, max=0.3,
       help=T("A log-normal spectrum: ln λ is normally distributed with this width; each particle gets its own "
              "wavelength and its own group velocity (temporal coherence).")),
    _p("mass_u", T("Mass, u"), "float", 1.0, group=_G_PART, min=1e-6, max=1e9, log=True,
       show_if={"species": ["custom"]}),
    _p("charge_e", T("Charge, e"), "float", 0.0, group=_G_PART, min=-100, max=100, show_if={"species": ["custom"]}),
    _p("spin_half", T("Spin ½"), "bool", False, group=_G_PART, show_if={"species": ["custom"]}),
    _p("pol_state", T("Polarisation"), "select", "H", group=_G_PART, show_if=PHOT,
       options=[("H", T("H (along x, across the slits)")), ("V", T("V (along the slits)")), ("D", T("D (+45°)")),
                ("A", T("A (−45°)")), ("R", T("R (circular)")), ("L", T("L (circular)")),
                ("custom", T("custom (azimuth, ellipticity)")), ("unpol", T("unpolarised"))]),
    _p("spin_state", T("Spin"), "select", "up_z", group=_G_PART, show_if=SPIN,
       options=[("up_z", T("↑ along z (along the beam)")), ("down_z", T("↓ along z")), ("up_x", T("↑ along x")),
                ("down_x", T("↓ along x")), ("up_y", T("↑ along y")), ("down_y", T("↓ along y")),
                ("unpol", T("unpolarised"))]),
    _p("pol_degree", T("Degree of polarisation"), "float", 1.0, group=_G_PART, min=0.0, max=1.0, show_if=POLARIZABLE),
    _p("pol_psi", T("Azimuth, °"), "float", 0.0, group=_G_PART, min=-180, max=180, show_if={"pol_state": ["custom"]}),
    _p("pol_chi", T("Ellipticity, °"), "float", 0.0, group=_G_PART, min=-45, max=45,
       show_if={"pol_state": ["custom"]}),
    # source
    _p("L1_m", T("Source: distance to the slits, m (0 = plane wave)"), "float", 0.0, group=_G_SRC, min=0.0,
       max=1e3, help=T("0: a plane wave (the source at infinity); the source's width is then not used.")),
    _p("src_width_um", T("Source: width, µm"), "float", 0.0, group=_G_SRC, min=0.0, max=1e6,
       help=T("Each particle leaves from its own point of the source: spatial coherence.")),
    _p("rate", T("Particles per second (world time)"), "float", 1000.0, group=_G_SRC, min=1e-6, max=1e15, log=True),
    # slits and screen
    _p("n_slits", T("Number of slits"), "int", 2, group=_G_SLITS, min=1, max=12),
    _p("a_um", T("Slit width, µm"), "float", 20.0, group=_G_SLITS, min=1e-4, max=1e5, log=True),
    _p("d_um", T("Slit period (centre to centre), µm"), "float", 100.0, group=_G_SLITS, min=1e-4, max=1e6,
       log=True),
    _p("L2_m", T("Distance to the screen, m"), "float", 1.0, group=_G_SLITS, min=1e-6, max=1e4, log=True),
    _p("screen_um", T("Screen half-width, µm (0 = auto)"), "float", 0.0, group=_G_SLITS, min=0.0, max=1e8),
    _p("pixel_um", T("Detector pixel, µm (0 = auto)"), "float", 0.0, group=_G_SLITS, min=0.0, max=1e6),
    _p("screen_model", T("Model of the slit screen"), "select", "kirchhoff", group=_G_SLITS,
       options=[("kirchhoff", T("scalar: Kirchhoff boundary conditions")),
                ("pec", T("perfect conductor: vector diffraction (slits up to {w:.1f} λ)", w=VEC_WIDTH_MAX))],
       help=T("Scalar: the field in a slit equals the incident one (the default). Perfect conductor: the vector "
              "solution for a screen of a perfect conductor of thickness t; photons only, a plane monochromatic wave "
              "and slits no wider than {w:.1f} λ (k·a ≤ {ka:.0f}; the default slit of {a:g} µm at {lam:g} nm, "
              "{r:.1f} λ, does not qualify, and its difference from the scalar result is of order 1/(k·a) < 1 %); "
              "both polarisations (E along the slits: TE, across them: TM); hits follow the energy flux of this "
              "solution; the scalar curve is shown next to it.",
              w=VEC_WIDTH_MAX, ka=VEC_KA_MAX, a=20.0, lam=632.8, r=20.0e-6 / 632.8e-9)),
    _p("screen_t_um", T("Screen thickness, µm (0 = infinitely thin)"), "float", 0.0, group=_G_SLITS, min=0.0,
       max=1e5, show_if={"screen_model": ["pec"]}),
    _p("eff", T("Detector efficiency"), "float", 1.0, group=_G_SLITS, min=0.0, max=1.0),
    _p("dark_rate", T("Dark counts, 1/s"), "float", 0.0, group=_G_SLITS, min=0.0, max=1e12,
       help=T("False counts of the screen, uniform over it. At most {k:g} per particle of the source (otherwise the "
              "screen shows only noise): at {r:g} particles/s, up to {d:g} 1/s.",
              k=DARK_PER_PARTICLE_MAX, r=1000.0, d=1000.0 * DARK_PER_PARTICLE_MAX)),
    # observer and elements (the initial state; changeable in the run: live parameters)
    _p("wp_mode", T("Which-path observer"), "select", "none", group=_G_OBS,
       options=_opts([("none", T("none")), ("qubit", T("qubit detector at a slit (Englert's model)")),
                      ("microscope", T("photon scattering (Heisenberg's microscope)"),
                       {"species": list(MIC_SPECIES)})])),
    _p("wp_slit", T("Detector at slit no."), "int", 1, group=_G_OBS, min=1, max=12,
       show_if={"wp_mode": ["qubit"]}),
    _p("wp_theta", T("Detector coupling θ, ° (90 = a full which-path mark)"), "float", 90.0, group=_G_OBS,
       min=0, max=180, show_if={"wp_mode": ["qubit"]}),
    _p("wp_read", T("Detector reading"), "select", "none", group=_G_OBS,
       show_if={"wp_mode": ["qubit"]},
       options=[("none", T("not read")), ("path", T("read in the path basis")),
                ("angle", T("read in a rotated basis (eraser)"))]),
    _p("wp_read_angle", T("Readout basis angle, °"), "float", 45.0, group=_G_OBS, min=-180, max=180,
       show_if={"wp_read": ["angle"]}),
    _p("mic_lambda_nm", T("Probe photon: wavelength, nm"), "float", 1000.0, group=_G_OBS,
       min=1e-3, max=1e9, log=True, show_if={"wp_mode": ["microscope"]}),
    _p("mic_prob", T("Scattering probability per particle"), "float", 1.0, group=_G_OBS, min=0, max=1,
       show_if={"wp_mode": ["microscope"]}),
    _p("mic_dir", T("Probe beam direction"), "select", "y", group=_G_OBS,
       show_if={"wp_mode": ["microscope"]},
       options=[("x", T("x (across the slits)")), ("y", T("y (along the slits)")), ("z", T("z (along the beam)"))]),
    _p("mic_pol", T("Dipole axis (probe polarisation)"), "select", "z", group=_G_OBS,
       show_if={"wp_mode": ["microscope"]}, options=[("x", "x"), ("y", "y"), ("z", "z")]),
    _p("mic_record", T("Recording of the scattered photon"), "select", "all", group=_G_OBS,
       show_if={"wp_mode": ["microscope"]},
       options=[("none", T("not recorded")), ("all", T("direction recorded (4π)")),
                ("cone", T("a lens on the z axis (cone)"))]),
    _p("mic_cone_deg", T("Lens half-angle, °"), "float", 30.0, group=_G_OBS, min=0.1, max=90,
       show_if={"mic_record": ["cone"]}),
    _p("el1", T("Element at slit {j:d}", j=1), "select", "none", group=_G_OBS, options=ELEM_OPTIONS),
    _p("el1_angle", T("Slit {j:d}: angle / phase, °", j=1), "float", 0.0, group=_G_OBS, min=-360, max=360),
    _p("el2", T("Element at slit {j:d}", j=2), "select", "none", group=_G_OBS, options=ELEM_OPTIONS),
    _p("el2_angle", T("Slit {j:d}: angle / phase, °", j=2), "float", 0.0, group=_G_OBS, min=-360, max=360),
    _p("analyzer", T("Analyser in front of the screen"), "select", "none", group=_G_OBS,
       options=[("none", T("none")), ("on", T("polariser / spin filter"))]),
    _p("analyzer_angle", T("Analyser angle, °"), "float", 45.0, group=_G_OBS, min=-180, max=180,
       show_if={"analyzer": ["on"]}),
    _p("ab_flux", T("Magnetic flux between slits 1 and 2, h/e"), "float", 0.0, group=_G_OBS,
       min=-100, max=100, help=T("The Aharonov–Bohm effect: charged particles only.")),
    # laws
    _p("born_p", T("Exponent in the Born rule P ∝ |ψ|^p"), "float", 2.0, group=_G_LAWS, min=0.5,
       max=6.0, standard=2.0,
       help=T("{p:g} is quantum mechanics. Any other value is a modification (Sorkin's test: three slits).", p=2.0)),
    _p("collapse", T("Collapse"), "select", "none", group=_G_LAWS, standard="none",
       options=[("none", T("none (linear quantum mechanics)")), ("grw", T("spontaneous collapse (GRW)")),
                ("slit", T("forced choice of a slit (no interference)"))]),
    _p("grw_lambda", T("GRW: rate per unit mass (u), 1/s"), "float", 1e-16, group=_G_LAWS, min=1e-30,
       max=1e12, log=True, show_if={"collapse": ["grw"]}),
    _p("grw_rc_nm", T("GRW: localisation width, nm"), "float", 100.0, group=_G_LAWS, min=1e-3, max=1e9,
       log=True, show_if={"collapse": ["grw"]}),
    # display
    _p("n_bohm", T("Number of flow lines (Bohm trajectories)"), "int", 40, group=_G_SHOW, min=0, max=200),
], presets={
    "photon_young": {"label": T("Photons {lam:g} nm, two slits (Young, one photon at a time)", lam=633.0),
                     "params": {}},
    "photon_pol_marks": {"label": T("Photons D: polarisers H and V on the slits, a which-path mark"),
                         "params": {"pol_state": "D", "el1": "polarizer", "el1_angle": 0, "el2": "polarizer",
                                    "el2_angle": 90}},
    "photon_eraser": {"label": T("Quantum eraser: H/V marks + {a:g}° analyser", a=45.0),
                      "params": {"pol_state": "D", "el1": "polarizer", "el1_angle": 0, "el2": "polarizer",
                                 "el2_angle": 90, "analyzer": "on", "analyzer_angle": 45}},
    "photon_eraser_minus": {"label": T("Quantum eraser: analyser at {a:g}° (anti-fringes)", a=-45.0),
                            "params": {"pol_state": "D", "el1": "polarizer", "el1_angle": 0, "el2": "polarizer",
                                       "el2_angle": 90, "analyzer": "on", "analyzer_angle": -45}},
    "photon_partial": {"label": T("Photons: a wide source (partial coherence)"),
                       "params": {"L1_m": 0.5, "src_width_um": 2000.0}},
    "photon_qubit": {"label": T("Photons: a which-path qubit detector, θ = {th:g}°", th=90.0),
                     "params": {"wp_mode": "qubit", "wp_theta": 90}},
    "electron": {"label": T("Electrons {e:g} keV (illustrative: slits {a:g} µm wide, {d:g} µm apart, screen at "
                            "{L:g} m)", e=50.0, a=0.1, d=0.5, L=1.0),
                 "params": {"species": "electron", "energy_by": "ekin", "ekin_ev": 50000.0, "a_um": 0.1,
                            "d_um": 0.5, "L2_m": 1.0}},
    "electron_qubit": {"label": T("Electrons + which-path detector (θ = {th:g}°, not read)", th=90.0),
                       "params": {"species": "electron", "energy_by": "ekin", "ekin_ev": 50000.0, "a_um": 0.1,
                                  "d_um": 0.5, "L2_m": 1.0, "wp_mode": "qubit", "wp_theta": 90}},
    "electron_weak": {"label": T("Electrons + a weak detector (θ = {th:g}°)", th=30.0),
                      "params": {"species": "electron", "energy_by": "ekin", "ekin_ev": 50000.0, "a_um": 0.1,
                                 "d_um": 0.5, "L2_m": 1.0, "wp_mode": "qubit", "wp_theta": 30}},
    "electron_eraser": {"label": T("Electrons: the which-path detector read in the {a:g}° basis (eraser)", a=45.0),
                        "params": {"species": "electron", "energy_by": "ekin", "ekin_ev": 50000.0, "a_um": 0.1,
                                   "d_um": 0.5, "L2_m": 1.0, "wp_mode": "qubit", "wp_theta": 90,
                                   "wp_read": "angle", "wp_read_angle": 45}},
    "electron_microscope": {"label": T("Electrons + photon scattering (Heisenberg's microscope, λ = {lam:g} µm)",
                                       lam=1.0),
                            "params": {"species": "electron", "energy_by": "ekin", "ekin_ev": 50000.0, "a_um": 0.1,
                                       "d_um": 0.5, "L2_m": 1.0, "wp_mode": "microscope",
                                       "mic_lambda_nm": 1000.0}},
    "electron_ab": {"label": T("Electrons: the Aharonov–Bohm effect (flux ½ h/e)"),
                    "params": {"species": "electron", "energy_by": "ekin", "ekin_ev": 50000.0, "a_um": 0.1,
                               "d_um": 0.5, "L2_m": 1.0, "ab_flux": 0.5}},
    "neutron": {"label": T("Cold neutrons {lam:g} nm (illustrative)", lam=2.0),
                "params": {"species": "neutron", "lam_nm": 2.0, "a_um": 5.0, "d_um": 25.0, "L2_m": 5.0,
                           "rate": 100.0}},
    "c60": {"label": T("Fullerenes C60, {v:g} m/s, a grating of {n:d} slits (illustrative)", v=200.0, n=10),
            "params": {"species": "c60", "energy_by": "speed", "speed_ms": 200.0, "n_slits": 10, "a_um": 0.05,
                       "d_um": 0.1, "L2_m": 1.25, "rate": 100.0}},
    "c60_grw": {"label": T("C60 with enhanced GRW collapse (modification)"),
                "params": {"species": "c60", "energy_by": "speed", "speed_ms": 200.0, "n_slits": 2, "a_um": 0.05,
                           "d_um": 0.1, "L2_m": 1.25, "rate": 100.0, "collapse": "grw", "grw_lambda": 3.0,
                           "grw_rc_nm": 100.0}},
    "vector_narrow": {"label": T("Vector diffraction: {a:g} µm slits in a {t:g} µm conducting screen, polarisation D",
                                 a=0.5, t=0.2),
                      "note": T("Slits of about λ: the scalar paraxial pattern is wrong here, and its comparison with "
                                "the exact integral fails, as expected; the world's answer is the vector solution"),
                      "params": {"screen_model": "pec", "screen_t_um": 0.2, "a_um": 0.5, "d_um": 3.0, "L2_m": 0.01,
                                 "pol_state": "D"}},
    "triple": {"label": T("Three slits: a test of the Born rule (Sorkin)"), "params": {"n_slits": 3}},
    "triple_mod": {"label": T("Three slits with P ∝ |ψ|^{p:g} (modification)", p=2.4),
                   "params": {"n_slits": 3, "born_p": 2.4},
                   "note": T("The Born rule is changed: Sorkin's parameter is not zero, and the check fails as "
                             "expected; that is the consequence of the modification")},
    "slit_collapse": {"label": T("Forced choice of a slit (modification)"), "params": {"collapse": "slit"}},
    # the Watch screen's story (design §6.1): Young's photons with 20 flow lines on a screen ±50 mm wide (the bands and the
    # single slit's hump fill it); the script changes only live parameters
    "story": {"label": T("The double slit, step by step"), "params": {"n_bohm": 20, "screen_um": 50000.0}},
})


APP_FIELDS = ["wp_mode", "wp_slit", "wp_theta", "wp_read", "wp_read_angle", "mic_lambda_nm", "mic_prob", "mic_dir",
              "mic_pol", "mic_record", "mic_cone_deg", "el1", "el1_angle", "el2", "el2_angle", "analyzer",
              "analyzer_angle", "ab_flux", "rate"]
# What a live change rebuilds (owner, 2026-10-23: the set-up changes at once, as in a laboratory; only the laws are
# fixed for a world). Particle or slits/screen: the whole set-up, particles in flight are lost (the beam path is
# rebuilt). Source: new particles only; those already emitted fly on and are transitional. Detector: at once.
SETUP_REBUILD = ("species", "energy_by", "lam_nm", "ekin_ev", "speed_ms", "freq_thz", "mass_u", "charge_e",
                 "spin_half", "n_slits", "a_um", "d_um", "L1_m", "L2_m", "screen_um", "pixel_um", "screen_model",
                 "screen_t_um")
SOURCE_FIELDS = ("dlam_rel", "pol_state", "spin_state", "pol_degree", "pol_psi", "pol_chi", "src_width_um")
DETECTOR_FIELDS = ("eff", "dark_rate")
LAW_FIELDS = ("born_p", "collapse", "grw_lambda", "grw_rc_nm")
for _par in SCHEMA.params:
    _par.live = _par.id not in LAW_FIELDS


class Simulation(BaseSimulation):
    speed_range = (1e-15, 1e9)

    @classmethod
    def check_params(cls, params):
        """Cheap refusals before anything is built (the catalogue's form shows them): dark counts against the source
        (P8)."""
        _check_rates(params)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = dict(params)
        self._adopt(self._build(self.params))
        self.dark_rate = params["dark_rate"]
        self.seg = -1
        self.src_epoch = 0  # incremented when the source changes: particles emitted before are transitional
        self.app = self._apparatus({k: params[k] for k in APP_FIELDS})
        _check_rates(self.params)
        self._check_screen_cost()
        # timeline
        self.t_next = self.rng.exponential(1.0 / self.app.rate)
        self.pid = 0
        self.batches: list = []  # Batch objects with particles still flying
        self.counts = dict(emitted=0, absorbed_slits=0, absorbed_an=0, missed=0, undetected=0, detected=0, dark=0,
                           grw_hits=0, scattered=0, mixed=0, lost=0, reflected=0)
        self.pending_stories = []
        self.hist = None
        self.seg_t0 = 0.0
        self.default_speed = max(min(40.0 / self.app.rate, 1e9), 1e-15)
        self._buf = []
        self._z_par_why = "dev"
        self._new_segment(T("start"))

    def _build(self, p):
        """Particle, slits, screen grid, source and experiment from the parameters; touches no state, so a refused
        live change leaves the world as it was."""
        by = p["energy_by"]
        value = {"lambda": p["lam_nm"] * 1e-9, "ekin": p["ekin_ev"], "speed": p["speed_ms"],
                 "freq": p["freq_thz"] * 1e12}[by]
        try:
            pt = make(p["species"], by, value, p["mass_u"], p["charge_e"], p["spin_half"])
        except ValueError as e:  # the core's own text, with what to choose (P17)
            raise Refusal(_exc_text(e), T("choose the wavelength, the energy or the frequency in “Set by”")
                          if p["species"] == "photon" else
                          T("choose the wavelength, the energy or the speed in “Set by”")) from e
        n = int(p["n_slits"])
        a = p["a_um"] * 1e-6
        d = p["d_um"] * 1e-6
        if n > 1 and d <= a:
            raise Refusal(T("the slit period must be larger than the slit width"),
                          T("increase “Slit period” or reduce “Slit width”"))
        L1 = math.inf if p["L1_m"] == 0 else p["L1_m"]
        L2 = p["L2_m"]
        lam = pt.lam
        span = (n - 1) * d + a
        half = p["screen_um"] * 1e-6 or (0.5 * span + 3.0 * lam * L2 / a)
        fine = lam * L2 / max(span, a)  # finest far-field period
        ns = int(min(max(2 * half / fine * 14, 2048), 32768))
        x = np.linspace(-half, half, ns)
        pixel = p["pixel_um"] * 1e-6 or max(fine / 8, x[1] - x[0])
        geom = Geometry(n, a, d, L1, L2, p["src_width_um"] * 1e-6, x, pixel)
        laws = Laws(p["born_p"], p["collapse"], p["grw_lambda"], p["grw_rc_nm"] * 1e-9)
        internal = pt.internal
        state = p["pol_state"] if internal == "pol" else p["spin_state"] if internal == "spin" else "none"
        source = Source(state, p["pol_degree"], (p["pol_psi"], p["pol_chi"]), p["dlam_rel"])
        exp = Experiment(pt, geom, laws, source, self.rng)
        exp.eff = p["eff"]
        vec_cache = getattr(self, "_vec_cache", None)
        if p["screen_model"] == "pec":
            exp.vec, vec_cache = _vector_screen(pt, geom, p, laws, vec_cache)
        t_flight = (0.0 if math.isinf(L1) else L1 / pt.v) + L2 / pt.v
        return dict(particle=pt, geom=geom, laws=laws, source=source, exp=exp, fine=fine,
                    pts_per_fringe=fine / (x[1] - x[0]), t_flight=t_flight, _vec_cache=vec_cache)

    def _adopt(self, b):
        for k, v in b.items():
            setattr(self, k, v)
        self._rs_cols = {}  # map column -> exact and paraxial per-slit fields (fixed while the geometry is)
        self._rs_screen = None
        self._coh_err_cache = None
        self._setup_fresh = True

    def engine_modules(self):
        mods = ["core.constants", "core.quantum.particles", "core.quantum.marks", "core.optics.scalar",
                "theories.approx.paraxial", "theories.approx.kirchhoff", "theories.approx.paraxial_ensemble",
                "core.quantum.scattering", "tools.stats"]
        if int(self.params["n_bohm"]) > 0 and self.laws.collapse != "grw":
            mods.append("theories.interpretations.bohm")
        if self.laws.collapse in ("grw", "slit"):
            mods.append("theories.alternatives.collapse")
        if self.laws.born_p != 2.0:
            mods.append("theories.alternatives.born_rule")
        if self.exp.vec is not None:
            mods.append("core.em.slit")
        return mods

    # --- live changes (command "set") ---------------------------------------------------------------------
    def live_values(self):
        return {k: self.params[k] for k in SCHEMA.live_ids()}

    def set_live(self, values):
        new, errors = SCHEMA.coerce_live(self.params, values)
        if errors:
            raise Refusal(_join(errors))
        changed = [k for k in SCHEMA.live_ids() if not _same(new[k], self.params[k])]
        if not changed:
            return T("no changes")
        rebuild = any(k in SETUP_REBUILD for k in changed)
        b = self._build(new) if (rebuild or any(k in SOURCE_FIELDS + DETECTOR_FIELDS for k in changed)) else None
        pt = b["particle"] if b else self.particle
        n = int(new["n_slits"])
        f = {k: new[k] for k in APP_FIELDS}
        notes = []
        try:
            app = self._apparatus(f, pt, n)
        except ValueError:
            if not rebuild or any(k in APP_FIELDS for k in changed):
                raise
            f, notes = _fit_apparatus(f, pt, n)  # the new particle or slits do not take some elements: remove them
            app = self._apparatus(f, pt, n)
            new.update(f)
        _check_rates(new)
        self._check_screen_cost(app, b)
        # commit (nothing above changed the world)
        desc = _join([T("{label}: {old} → {new}", label=SCHEMA.by_id[k].label, old=_val(k, self.params[k]),
                        new=_val(k, new[k])) for k in changed])
        if b is not None:
            if rebuild:
                lost = sum(int(np.sum(bb.stage < 2)) for bb in self.batches)
                self.counts["lost"] += lost
                self.batches = []
                self.pending_stories = [st for st in self.pending_stories if st["t_det"] <= self.t]
                if lost:
                    notes.append(T("the set-up is rebuilt: particles in flight lost: {n:d}", n=int(lost)))
            else:
                self.src_epoch += 1
            self._adopt(b)
        self.params = new
        self.dark_rate = new["dark_rate"]
        self.app = app
        self.t_next = self.t + self.rng.exponential(1.0 / app.rate)
        self._new_segment(T("set-up changed: {desc}", desc=desc))
        for text in notes:
            self._msg({"type": "notice", "t": self.t, "text": text})
        return desc

    # --- apparatus ------------------------------------------------------------------------------------
    def _apparatus(self, f, pt=None, n=None):
        n = int(self.params["n_slits"]) if n is None else n
        pt = self.particle if pt is None else pt
        internal = pt.internal
        els = [("none", 0.0)] * n
        who = _who(pt)
        for j, (kk, aa) in enumerate([(f["el1"], f["el1_angle"]), (f["el2"], f["el2_angle"])]):
            if j < n and kk != "none":
                if kk not in ELEM_FOR[internal]:  # P17: by its label, and what does act on this particle
                    ok = _join([T("“{x}”", x=_ELEM_LABEL[e]) for e in ELEM_FOR[internal]], ", ")
                    why = {"pol": T("a photon has polarisation"), "spin": T("the particle has spin ½"),
                           None: T("the particle has neither polarisation nor spin")}[internal]
                    raise Refusal(T("“{elem}” at slit {j:d} does not act on {who} ({why})", elem=_ELEM_LABEL[kk],
                                    j=j + 1, who=who, why=why),
                                  T("choose one of these for “Element at slit {j:d}”: {ok}", j=j + 1, ok=ok))
                marks.element_matrix(kk, aa, internal)
                els[j] = (kk, float(aa))
        if f["analyzer"] == "on" and internal is None:
            raise Refusal(T("the particle “{p}” has no internal state (polarisation or spin): the analyser has "
                            "nothing to act on", p=pt.label),
                          T("choose “Analyser in front of the screen” = none"))
        if f["wp_mode"] == "microscope":
            if pt.species not in MIC_SPECIES:
                raise Refusal(T("the probe photon's scattering is given here by a dipole pattern: charged (Thomson) "
                                "and polarisable (Rayleigh) particles have one, the particle “{p}” has not", p=pt.label),
                              T("choose “Which-path observer” = qubit detector, or marks by polarisation or spin in "
                                "“Element at slit”"))
            if f["mic_pol"] == f["mic_dir"]:
                raise Refusal(T("the probe's polarisation (its dipole axis) cannot coincide with its direction of "
                                "propagation"),
                              T("choose a “Dipole axis” other than {axis}", axis=str(f["mic_dir"])))
        if not (1 <= int(f["wp_slit"]) <= n):
            raise Refusal(T("the which-path detector is at slit no. {k:d}, but there are {n:d} slits",
                            k=int(f["wp_slit"]), n=int(n)),
                          T("choose “Detector at slit no.” from 1 to {n:d}", n=int(n)))
        if float(f["rate"]) <= 0:
            raise Refusal(T("the source's rate must be above 0"), T("set “Particles per second” above 0"))
        return Apparatus(els, (f["analyzer"], float(f["analyzer_angle"])), f["wp_mode"], int(f["wp_slit"]) - 1,
                         float(f["wp_theta"]), f["wp_read"], float(f["wp_read_angle"]), f["mic_lambda_nm"] * 1e-9,
                         float(f["mic_prob"]), f["mic_dir"], f["mic_pol"], f["mic_record"], float(f["mic_cone_deg"]),
                         float(f["ab_flux"]), float(f["rate"]), seg=self.seg + 1)

    def _app_dict(self):
        a = self.app
        e = a.elements + [("none", 0.0)] * 2
        return {"wp_mode": a.wp_mode, "wp_slit": a.wp_slit + 1, "wp_theta": a.wp_theta, "wp_read": a.wp_read,
                "wp_read_angle": a.wp_read_angle, "mic_lambda_nm": a.mic_lambda * 1e9, "mic_prob": a.mic_prob,
                "mic_dir": a.mic_dir, "mic_pol": a.mic_pol, "mic_record": a.mic_record,
                "mic_cone_deg": a.mic_cone_deg, "el1": e[0][0], "el1_angle": e[0][1], "el2": e[1][0],
                "el2_angle": e[1][1], "analyzer": a.analyzer[0], "analyzer_angle": a.analyzer[1],
                "ab_flux": a.ab_flux, "rate": a.rate}

    def _actions(self):
        # the apparatus, the source, the slits and the screen are live parameters (the player's set-up panel)
        return [{"name": "clear", "label": T("Clear the screen"), "help": T("a new segment, the same set-up"),
                 "args": []}]

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

    # --- the run's own expectation for the current apparatus (a segment) --------------------------------------
    def _model(self, p_scat=None, app=None, ctx=None):
        """The ensemble model of the set-up in force, or of ``app`` and a built set-up ``ctx`` (``_build``'s dict)
        not yet adopted (a live change checked before it is committed)."""
        c = ctx or {}
        app = app or self.app
        g, pt, src = c.get("geom", self.geom), c.get("particle", self.particle), c.get("source", self.source)
        ex, laws = c.get("exp", self.exp), c.get("laws", self.laws)
        mic = app.wp_mode == "microscope"
        return ens.Model(pt.k, src.dlam_rel, g.slits, g.a, g.L1, g.src_width,
                         (app.mic_prob if p_scat is None else p_scat) if mic else 0.0,
                         2 * math.pi / app.mic_lambda, float(_axis(app.mic_dir)[0]), float(_axis(app.mic_pol)[0]),
                         ex.grw_rate(), lambda k: float(ex.v_of_lam(2 * math.pi / k)), laws.grw_rc)

    def _check_screen_cost(self, app=None, ctx=None):
        """Refuse a set-up whose screen expectation would not fit (review UX-params P18): the screen grid is extended by
        the largest shift a particle can get on its way (``paraxial_ensemble.Model.max_shift``), its amplitudes held
        per slit and its FFT convolution on twice that length. Says which shift and what to change."""
        c = ctx or {}
        g = c.get("geom", self.geom)
        app = app or self.app
        model = self._model(app=app, ctx=ctx)
        if not model.shifts:
            return
        dx = float(g.x[1] - g.x[0])
        nsl = len(model.slits)
        worst = (0.0, 0.0, 0.0)
        for lam in model.lams:
            sh = model.max_shift(g.L2, 2 * math.pi / lam)
            n_e = len(g.x) + 2.0 * (math.ceil(sh / dx) + 4)
            m = 2.0 ** math.ceil(math.log2(2 * n_e + 2))
            nbytes = 16.0 * n_e * nsl * 4 + 16.0 * m * 3  # amplitudes and Fresnel temporaries; FFT, product, result
            if nbytes > worst[0]:
                worst = (nbytes, sh, n_e)
        nbytes, sh, n_e = worst
        if nbytes <= SCREEN_BYTES_MAX:
            try:
                from lfviz.limits import require
            except ImportError:  # pragma: no cover - a framework without the memory budget
                return
            require(nbytes, T("the expected pattern on the screen (the screen grid extended by the particles' "
                              "shifts)"),
                    T("reduce the particles' shifts: a longer probe λ, a weaker GRW collapse, a narrower source"))
            return
        half = 0.5 * (g.x[-1] - g.x[0])
        what = T("the particles are shifted on their way to the screen by up to ±{shift} with a screen of ±{half}: the "
                 "expected pattern needs a grid of {n:.3g} points (~{gb:.3g} GB; the world's limit is {lim:g} GB)",
                 shift=_len_text(sh), half=_len_text(half), n=float(n_e), gb=nbytes / 2 ** 30,
                 lim=SCREEN_BYTES_MAX / 2 ** 30)
        frac = (SCREEN_BYTES_MAX / nbytes)
        hints = []
        if app.wp_mode == "microscope" and model.p > 0:
            hints.append(T("set the probe photon's wavelength to at least ~{lam:.3g} nm (the probe's recoil ∝ 1/λ)",
                           lam=app.mic_lambda / frac * 1e9))
        if model.grw > 0:
            hints.append(T("weaken the GRW collapse (a smaller rate λ or a larger width r_C): GRW kicks shift the "
                           "particles"))
        if model.s > 0:
            hints.append(T("narrow the source or move it farther away"))
        raise Refusal(what, _join(hints) or T("reduce the particles' shifts"))

    def _avg_grams(self, analyzer=True):
        """Ensemble Gram matrices (exact for the source's density matrix): per readout, and unread. analyzer=False:
        the marks between the slits and the analyzer (the analyzer stands in front of the screen and acts only there),
        for the near-field map and the flow lines."""
        ex = self.exp
        app_scr = self.app if analyzer else Apparatus(**{**self.app.__dict__, "analyzer": ("none", 0.0)})
        rho = ex_rho(self.source, self.particle.internal)
        # E[G] = sum over the eigen-decomposition of rho of the Gram matrices of its eigenvectors
        vals, vecs = np.linalg.eigh(rho)
        G = Gf = None
        for lam_i, v in zip(vals, vecs.T):
            if lam_i <= 1e-15:
                continue
            Gi, Gfi = ex.gram(v[None, :], self.app, app_scr)
            G = lam_i * Gi[0] if G is None else G + lam_i * Gi[0]
            Gf = lam_i * Gfi[0] if Gf is None else Gf + lam_i * Gfi[0]
        return G, Gf  # (nR, n, n), (n, n)

    def _new_segment(self, reason):
        self.seg += 1
        self.app.seg = self.seg
        self.seg_t0 = self.t
        g, pt, ex = self.geom, self.particle, self.exp
        Gr, Gf = self._avg_grams()
        nR = Gr.shape[0]
        self.Gavg = Gf
        model = self._model()
        mc = self.laws.born_p != 2.0
        if mc:  # nonlinear modification: Monte Carlo over the run's own particle draws
            Pens, Pcl, self.M_last = self._mc_ensemble(np.random.default_rng([self.seed, 7919, self.seg]))
        else:
            Pens = ens.screen(model, g.x, g.L2, list(Gr), eff=ex.eff)
            Gd = [np.diag(np.diag(G)) for G in Gr]
            Pcl = ens.screen(model, g.x, g.L2, Gd, eff=ex.eff)
            self.M_last = None
        classes = {}
        if self.app.wp_mode == "microscope" and not mc:
            m0 = self._model(p_scat=0.0)
            pn = (1 - self.app.mic_prob)
            classes["noscat"] = pn * ens.screen(m0, g.x, g.L2, [Gf], eff=ex.eff)[0]
        nb = self._nbins()
        edges = np.linspace(g.x[0], g.x[-1], nb + 1)
        self.edges = edges
        dark_per_bin = self.dark_rate / self.app.rate / nb  # dark counts per emitted particle per bin
        curves = {"all": _rebin(g.x, Pens.sum(axis=0), edges) + dark_per_bin,
                  "cl": _rebin(g.x, Pcl.sum(axis=0), edges) + dark_per_bin}
        for r in range(nR if nR > 1 else 0):
            curves[f"r{r}"] = _rebin(g.x, Pens[r], edges) + dark_per_bin / nR
            curves[f"cl{r}"] = _rebin(g.x, Pcl[r], edges) + dark_per_bin / nR
        for kname, P in classes.items():
            curves[kname] = _rebin(g.x, P, edges) + dark_per_bin
        curves, vinfo = self._vector_curves(curves, edges, dark_per_bin)
        self.theory = {"Pens": Pens, "nR": nR, "curves": curves}
        self.hist = {"bins": np.zeros((nR, nb), np.int64), "n": 0}
        # near field: the ensemble map; flow lines of the averaged current (not for GRW). Both use the marks before
        # the analyzer: between the slits and the analyzer the wave has not met it yet
        Gm = Gf if self.app.analyzer[0] == "none" else self._avg_grams(analyzer=False)[1]
        want_flow = int(self.params["n_bohm"]) > 0 and self.laws.collapse != "grw"
        coherent = not model.shifts and self.source.dlam_rel == 0
        mp = ens.near_field(model, Gm, g.L2, with_current=want_flow and not coherent)
        flow = None
        if want_flow and np.trace(Gm).real > 0:
            nb_l = int(self.params["n_bohm"])
            rngb = np.random.default_rng([self.seed, 31, self.seg])
            if coherent:
                flow = bohm.slit_trajectories(pt.k, g.slits, g.a, g.L1, Gm, np.diag(Gm).real, g.L2, n=nb_l,
                                                 rng=rngb, n_steps=900)
            else:
                flow = ens.flow_lines(mp, g.slits, g.a, np.diag(Gm).real, n=nb_l, rng=rngb)
        z_ok = self._map_paraxial_start(mp, Gm)
        self._map_w0, self._map_nxi = float(mp["w"][0]), len(mp["xi"])
        approx = self._approximations(model, coherent, z_ok)
        blobs = {"map": mp["I"], "map_z": mp["z"], "map_w": mp["w"], "edges": edges}
        for kname, arr in curves.items():
            blobs["c_" + kname] = arr.astype(np.float64)
        if flow is not None:
            blobs["bohm_z"] = flow["z"]
            blobs["bohm_x"] = flow["x"].astype(np.float64)
        self._msg({"type": "segment", "t": self.t, "seg": self.seg, "reason": reason,
                   "apparatus": self.app.describe(pt.internal), "app": self._app_dict(), "nR": nR, "read": nR > 1,
                   "map_half0": mp["half0"], "map_theta": mp["theta_env"], "z_paraxial": z_ok, "z_paraxial_why": self._z_par_why,
                   "flow": ("trajectories" if coherent else "averaged") if flow is not None else None,
                   "curves": sorted(curves), "approx": approx, "expected": "MC" if mc else "exact",
                   "setup": self._setup_info(), "vector": vinfo}, blobs)
        self._segment_checks(model, Gr, Gf, Pens, mc)
        if vinfo is not None:
            self._vector_checks(vinfo)
        if self.seg > 0:
            self._msg({"type": "actions", "t": self.t, "actions": self._actions()})

    def _vector_curves(self, curves, edges, dark_per_bin):
        """Vector mode: the curves of the conductor screen next to the scalar ones, all per emitted particle and, like
        the hits, times the detector efficiency (review B8 C3: the vector curves had left it out, so with dark counts a
        correct run's chi^2 failed), plus the dark counts.

        * Hits from the vector screen (plain set-up): 'all' is the vector expectation (energy flux per photon falling on
          the strip W = n d), 'kir' the scalar Kirchhoff result propagated exactly in the same unit, 'vTE'/'vTM' the two
          polarisations; 'diff' (vector - scalar) only where it exceeds three times the estimated error of the method on
          the screen (review B8 C7: below it, the strip would show the method's error, not physics).
        * Hits from the scalar model (marks, elements, analyzer or modified laws): 'all' stays scalar; 'vec' is the
          SHAPE of the vector flux for the same slits without the elements, scaled to the same total as 'all' (its
          units differ: per photon on the open width, no elements, no analyzer); no 'diff' (review B8 C8: the
          difference was dominated by that normalisation, not by physics)."""
        V, g, ex = self.exp.vec, self.geom, self.exp
        self._vec_hits = False
        if V is None:
            return curves, None
        rho = ex_rho(self.source, self.particle.internal)
        wH, wV = float(rho[0, 0].real), float(rho[1, 1].real)
        Jmix = wH * V["J_TM"] + wV * V["J_TE"]
        self._vec_hits = ex.vec_plain(self.app)
        eff = float(ex.eff)
        why = diff_note = None
        err_screen = max(V["TE"]["err_screen"], V["TM"]["err_screen"])
        if self._vec_hits:
            unit = V["W"]
            sig = eff * _rebin(g.x, Jmix / unit, edges)
            sig_k = eff * _rebin(g.x, V["J_K"] / unit, edges)
            curves = {"all": sig + dark_per_bin, "kir": sig_k + dark_per_bin}
            dmax = float(np.max(np.abs(sig - sig_k)))
            if dmax > 3 * err_screen * float(np.max(sig)):
                curves["diff"] = sig - sig_k
            else:
                diff_note = T("the difference vector − scalar (at most {d:.2g} of the maximum) is not above three "
                              "times the estimated error of the method ({e:.2g}): not shown",
                              d=dmax / max(float(np.max(sig)), 1e-300), e=float(err_screen))
            if wH > 1e-12 and wV > 1e-12:
                curves["vTM"] = eff * _rebin(g.x, wH * V["J_TM"] / unit, edges)
                curves["vTE"] = eff * _rebin(g.x, wV * V["J_TE"] / unit, edges)
        else:
            curves = dict(curves)
            vsig = _rebin(g.x, Jmix, edges)
            ssig = curves["all"] - dark_per_bin
            tot_v, tot_s = float(np.sum(vsig)), float(np.sum(ssig))
            curves["vec"] = vsig * (tot_s / tot_v if tot_v > 0 else 0.0) + dark_per_bin
            why = (T("the changed laws (the Born exponent, a collapse) are defined only for the scalar model")
                   if not V["hits"] else
                   T("which-path marks, elements at the slits or an analyser have no vector counterpart in the engine"))
        pt_mix = wH * V["Pt_TM"] + wV * V["Pt_TE"]
        on_scr = float(np.sum(0.5 * (Jmix[1:] + Jmix[:-1])) * g.dx)
        vinfo = {"hits": "vector" if self._vec_hits else "scalar", "why": why, "t": V["t"], "W": V["W"], "n": g.n,
                 "unit": "strip" if self._vec_hits else "shape", "wH": wH, "wV": wV, "eff": eff,
                 "T_TE": V["TE"]["T"], "T_TM": V["TM"]["T"], "T_K": V["T_K"],
                 "rel_TE": V["TE"]["rel"], "rel_TM": V["TM"]["rel"], "err_TE": V["TE"]["err"], "err_TM": V["TM"]["err"],
                 "modes": V["TE"]["modes"], "method": V["TE"]["method"], "diff_note": diff_note,
                 "p_trans": pt_mix / V["W"], "screen_frac": on_scr / pt_mix if pt_mix > 0 else None}
        return curves, vinfo

    def _vector_checks(self, vi):
        V = self.exp.vec
        s = self.seg
        grp = T("Segment {s:d}: vector screen (perfect conductor)", s=s)
        for pol, lab in (("TE", T("E along the slits (TE)")), ("TM", T("H along the slits (TM)"))):
            d = V[pol]
            self._check(f"vbal{pol}{s}", T("Power balance, {pol}: P_trans + P_back − extinction (the screen's optical "
                                           "theorem), rel.", pol=lab), d["rel"], 0.0, "", grp, ok=abs(d["rel"]) < 1e-8,
                        note=T("P_trans = {pt:.6g}, P_back = {pb:.6g}, extinction = {ext:.6g} (units of the incident "
                               "wave's flux × m)", pt=float(d["P_t"]), pb=float(d["P_b"]), ext=float(d["ext"])))
            if d["rel_modes"] is not None:
                self._check(f"vmod{pol}{s}", T("Power of the modes in the slit = transmitted power, {pol}, rel.",
                                               pol=lab), d["rel_modes"],
                            0.0, "", grp, ok=abs(d["rel_modes"]) < 1e-8,
                            note=T("the flux through the slit's exit cross-section by the modes and by the far field "
                                   "behind the screen"))
            lv = d["levels"]
            if d["err_kind"] == "exponential":
                how = T("a basis with edge conditions (thin screen), converging exponentially: the estimate is the "
                        "change from {a:d} to {b:d} functions per slit (larger than the error at {b:d})",
                        a=int(lv[0]), b=int(lv[1]))
            else:
                po = d["err_order"]
                order = (T("{po:.2f} observed, taken within [{lo:g}, {hi:g}]", po=float(po), lo=0.5, hi=1.0)
                         if po is not None else T("not determined, {lo:g} taken", lo=0.5))
                how = T("waveguide modes, converging algebraically (the screen's corners): Richardson extrapolation over "
                        "{a:d}, {b:d}, {c:d} modes per slit (sub-blocks of one operator), order {order}; measured: the "
                        "estimate is {f1:g}–{f2:g} times the true error", a=int(lv[0]), b=int(lv[1]), c=int(lv[2]),
                        order=order, f1=1.4, f2=3.0)
            self._check(f"vconv{pol}{s}", T("Estimated error of the method, {pol}: truncation in the number of modes "
                                            "(T and the flux on the screen), rel.", pol=lab),
                        d["err"], None, "", grp, ok=d["err"] < VEC_ERR_TOL,
                        note=T("{how}; T: {et:.2g}, flux on the screen: {es:.2g}. Tolerance {tol:g}: less than a pixel "
                               "of the expected curve (≈ {px:d} px) and below what the histogram's χ² would notice "
                               "before ~{n:.2g} counts. This is an estimate, not a strict bound", how=how,
                               et=float(d["err_T"]), es=float(d["err_screen"]), tol=VEC_ERR_TOL, px=200, n=3e6))
        self._check(f"vT{s}", T("Transmission per slit width: TE / TM / Kirchhoff (scalar)"), vi["T_TE"], None, "", grp,
                    note=T("T_TE = {te:.5g}, T_TM = {tm:.5g}, T_Kirchhoff = {k:.5g} (1: the geometrical optics of a "
                           "wide slit)", te=float(vi["T_TE"]), tm=float(vi["T_TM"]), k=float(vi["T_K"])))
        if vi["screen_frac"] is not None:
            self._check(f"vscr{s}", T("Share of the transmitted power that reaches the screen"), vi["screen_frac"],
                        None, "", grp, note=T("the rest leaves past the edges of the finite screen"))
        g, pt = self.geom, self.particle
        if V["t"] == 0 and pt.k * g.a < 0.3 and g.n == 1:
            for pol in ("TE", "TM"):
                ref = vslit.rayleigh_narrow_transmission(pt.k, g.a, pol)
                self._check(f"vray{pol}{s}", T("Narrow slit in a thin screen: T_{pol} against Rayleigh's limit (1897)",
                                               pol=pol),
                            V[pol]["T"], ref, "", grp, tol=0.05,
                            note=T("the leading term at k·a ≪ 1; a correction of order (k·a)² (measured: {pc:g} % for "
                                   "TE at k·a = {ka:g})", pc=3.8, ka=0.3))

    def _mc_ensemble(self, rng, M=1500):
        """Monte-Carlo expectation for the nonlinear Born-exponent modification (each realisation normalised)."""
        ex, g = self.exp, self.geom
        accP = accC = None
        done = 0
        while done < M:
            B = min(200, M - done)
            b = ex.emit(np.zeros(B), 0, rng)
            idx = np.arange(B)
            ex.at_slits(b, idx, self.app, rng)
            G, Gf = ex.gram(b.chi, self.app, self.app)
            Gd = G * np.eye(g.n)[None, None]
            for GG, which in ((G, "P"), (Gd, "C")):
                I = ex.intensities(b.lam, b.xs, b.kappa, GG)
                Pw = ex.born(I)
                tot = Pw.sum(axis=(1, 2), keepdims=True) * g.dx
                w = (~b.absorbed).astype(float) * ex.eff
                Pn = Pw / np.maximum(tot, 1e-300) * w[:, None, None]
                Pn = Pn.sum(axis=0)
                if which == "P":
                    accP = Pn if accP is None else accP + Pn
                else:
                    accC = Pn if accC is None else accC + Pn
            done += B
        return accP / M, accC / M, M

    def _nbins(self):
        g = self.geom
        return int(max(16, min(4000, round((g.x[-1] - g.x[0]) / g.pixel))))

    def _map_paraxial_start(self, mp, Gf):
        """First map column where the paraxial field agrees with the exact RS integral to 1 % (review R13), found by
        bisection (about 8 exact evaluations) plus three later columns as a guard, because the deviation falls with z
        only on the whole, not monotonically. The map's columns depend only on the geometry and the particle, so the
        per-slit fields of each visited column are kept for the whole run: a new segment only recombines them with its
        own Gram matrix. The column nearest the slits (the costliest) is tried first, so the worst case is one such
        column plus columns near the boundary."""
        g, pt = self.geom, self.particle
        Gd = Gf if np.trace(Gf).real > 0 else np.eye(g.n)
        zs = mp["z"]

        def ok(iz):
            if iz not in self._rs_cols:
                xcol = np.linspace(-mp["w"][iz], mp["w"][iz], 61)
                if kirchhoff.cost(xcol, zs[iz], pt.k, g.slits, g.a, g.L1) > RS_BUDGET:
                    self._rs_cols[iz] = None  # the exact integral is not affordable: the column stays unverified
                else:
                    self._rs_cols[iz] = (kirchhoff.slit_fields(xcol, zs[iz], pt.k, g.slits, g.a, g.L1),
                                         paraxial.slit_amplitudes(xcol, zs[iz], pt.k, g.slits, g.a, g.L1))
            if self._rs_cols[iz] is None:
                return False
            U, A = self._rs_cols[iz]
            return kirchhoff.deviation(U, A, Gd)[0] < 0.01

        def bisect(lo, hi):  # not ok(lo), ok(hi)
            while hi - lo > 1:
                mid = (lo + hi) // 2
                if ok(mid):
                    hi = mid
                else:
                    lo = mid
            return hi

        last = len(zs) - 1
        if ok(0):
            b = 0
        elif not ok(last):
            self._z_par_why = "cost" if self._rs_cols[last] is None else "dev"
            return float(zs[last])
        else:
            b = bisect(0, last)
        # the deviation need not fall monotonically with z (reviewer's 07_numerics: 0.098, 0.044, 0.106 at z = 2a,
        # 5a, 20a), so three later columns are checked as well and the search goes on beyond any that fails
        while True:
            probes = sorted({b + round(f * (last - b)) for f in (0.25, 0.5, 0.75)} - {b, last})
            bad = [j for j in probes if not ok(j)]
            if not bad:
                break
            b = bisect(max(bad), last)
        return self._paraxial_result(zs, b)

    def _paraxial_result(self, zs, b):
        """z of the boundary and why the columns before it are hatched: 'dev' (exact solution differs by > 1 %) or
        'cost' (the nearest failing column was not affordable, so it is unverified rather than shown to be wrong)."""
        failed = [i for i in self._rs_cols if i < b]
        self._z_par_why = "cost" if failed and self._rs_cols[max(failed)] is None else "dev"
        return float(zs[b])

    def _approximations(self, model, coherent, z_ok):
        g, pt, app = self.geom, self.particle, self.app
        out = [T("A plane (2-D) geometry: the slits are infinitely long along y; the y coordinate of a point on the "
                 "screen is for display only.")]
        V = self.exp.vec
        if V is None:
            out += [T("Paraxial Fresnel optics with Kirchhoff boundary conditions (the field in a slit equals the "
                      "incident one); compared with the exact Rayleigh–Sommerfeld integral in “Checks”."),
                    T("Polarisation enters through the marks; in the paraxial regime both polarisations propagate "
                      "alike.")]
        else:
            th = V["t"] * 1e6
            meth = (T("a basis with edge conditions, exponential convergence") if V["TE"]["method"] == "edge" else
                    T("waveguide modes in the slits, algebraic convergence"))
            out.append(T("The screen is a perfect conductor {t:.4g} µm thick: the vector solution "
                         "lfphys.core.em.slit ({method}; the truncation error estimated in “Checks”) for both "
                         "polarisations, E along the slits (TE, V) and E across them (TM, H); no losses and no "
                         "plasmons of a real metal. The distance to the screen is measured from the exit face.",
                         t=float(th), method=meth)
                       if th != 0 else
                       T("The screen is an infinitely thin perfect conductor: the vector solution "
                         "lfphys.core.em.slit ({method}; the truncation error estimated in “Checks”) for both "
                         "polarisations, E along the slits (TE, V) and E across them (TM, H); no losses and no "
                         "plasmons of a real metal. The distance to the screen is measured from the exit face.",
                         method=meth))
            if getattr(self, "_vec_hits", False):
                out.append(T("Hits follow the energy flux of the vector solution through the screen's plane: a "
                             "photon of the source falls on a strip n·d = {w:.4g} µm wide and passes with the "
                             "probability P_trans/(n·d); otherwise the screen reflects or scatters it back; TE and TM "
                             "add with the weights of the source's polarisation (the flux has no TE–TM cross term).",
                             w=float(V["W"] * 1e6)))
                if g.n == 1:
                    out.append(T("With one slit the strip's width is nominal: the period d (otherwise unused). The "
                                 "share of transmitted photons and the number reflected depend on it, the pattern on "
                                 "the screen does not."))
                out.append(T("The scalar curve (blue): Kirchhoff's boundary values propagated exactly (the "
                             "Rayleigh–Sommerfeld integral), in the same units and with the same detector efficiency; "
                             "the difference is vector minus scalar, shown only where it exceeds three times the "
                             "estimated error of the method."))
            else:
                out.append(T("Hits are drawn from the scalar model (paraxial optics, Kirchhoff): which-path marks, "
                             "elements at the slits, an analyser or changed laws have no vector counterpart in the "
                             "engine. The vector curve (blue) is a shape only: the flux of the vector solution for the "
                             "same slits without elements and analyser, normalised to the same sum as the orange one "
                             "(their units differ); the difference is not shown."))
            out.append(T("The map of the wave at the slits and the flow lines are the scalar model (paraxial, "
                         "Kirchhoff): this visualization has no vector near field and no lines of energy flow."))
        if z_ok > 2 * g.a * 1.01:
            if self._z_par_why == "cost":
                out.append(T("The map at the slits up to z ≈ {z:.3g} m is not verified against the exact solution: "
                             "the exact integral is too costly there (k·a = {ka:.3g}); hatched as unverified.",
                             z=float(z_ok), ka=float(pt.k * g.a)))
            else:
                out.append(T("The map at the slits up to z ≈ {z:.3g} m is inaccurate (it differs from the exact "
                             "solution by > 1 %): hatched.", z=float(z_ok)))
        step0 = 2 * self._map_w0 / (self._map_nxi - 1)
        if step0 > 0.5 * g.a:
            out.append(T("At the slits the map's cross-section does not resolve the individual slits (grid step "
                         "{st:.3g} m > a/2); the comparison with the exact solution there uses {n:d} points of the "
                         "cross-section and is resolved no better.", st=float(step0), n=61))
        if g.a < 10 * pt.lam and V is None:
            out.append(T("A slit narrower than 10 wavelengths: Kirchhoff's boundary condition is inaccurate; for "
                         "photons there is the vector mode (“Model of the slit screen” → “perfect conductor”)."))
        if self.pts_per_fringe < 8:
            out.append(T("Screen grid: {p:.1f} points on the finest fringe (< 8): the pattern is under-resolved.",
                         p=float(self.pts_per_fringe)))
        if app.wp_mode == "microscope":
            out.append(T("Microscope: one photon scattered in the plane of the slits, a dipole pattern "
                         "(Thomson or Rayleigh), the longitudinal recoil neglected; “direction recorded” means the "
                         "photon in the lens's back focal plane (a direction, not an image of the slits)."))
        if self.laws.collapse == "grw":
            out.append(T("GRW: hits during the flight from the slits to the screen as random kicks (exact for the "
                         "distribution on the screen); hits before the slits are not modelled; flow lines are not "
                         "shown."))
            if pt.mass == 0:
                out.append(T("GRW does not act on a massless particle."))
        if self.laws.born_p != 2.0:
            out.append(T("A modification of the Born rule: the position from |ψ|^p normalised on the finite screen; "
                         "the probability of reaching the screen from |ψ|²; the Sorkin parameter from the "
                         "unnormalised I^(p/2). The expectation is a Monte Carlo over {n:d} particles.",
                         n=int(self.M_last)))
        if not coherent:
            out.append(T("With decoherence the flow lines are lines of the ensemble's averaged current, not Bohm "
                         "trajectories of one particle."))
        if self.source.dlam_rel > 0:
            out.append(T("A log-normal spectrum; each particle flies with its own group velocity."))
        out.append(T("The analyser and the detector's readout basis act when the particle arrives at the screen; the "
                     "elements at the slits, the which-path detector and the microscope act when it passes the "
                     "slits."))
        if app.analyzer[0] != "none":
            out.append(T("The analyser stands right in front of the screen: the map and the flow lines show the wave "
                         "before the analyser, the histogram and the expectation on the screen after it."))
        return out

    def _segment_checks(self, model, Gr, Gf, Pens, mc):
        g, pt, ex = self.geom, self.particle, self.exp
        s = self.seg
        grp = T("Segment {s:d}", s=s)
        cons = T("Segment {s:d}: consistency (identities)", s=s)
        fresh = self._setup_fresh  # first segment of this particle and geometry: their own checks again
        self._setup_fresh = False
        if fresh:
            P = self.params
            by = P["energy_by"]
            ref, how = None, ""
            if pt.mass == 0:
                if by == "ekin":
                    ref, how = H * C / (P["ekin_ev"] * EV), "hc/E"
                elif by == "freq":
                    ref, how = C / (P["freq_thz"] * 1e12), "c/ν"
            else:
                mc2 = pt.mass * C * C
                if by == "ekin":
                    ek = P["ekin_ev"] * EV
                    ref, how = H * C / math.sqrt(ek * ek + 2 * ek * mc2), "hc/√(E_k² + 2E_k mc²)"
                elif by == "speed":
                    v = P["speed_ms"]
                    ref, how = H * math.sqrt(1 - (v / C) ** 2) / (pt.mass * v), "h√(1−v²/c²)/(mv)"
            self._check("lam", T("Wavelength of the particle"), pt.lam * 1e9, None if ref is None else ref * 1e9,
                        T("nm"), _G_PART,
                        note=T("{how}; E_k = {ek:.6g} eV, v = {v:.6g} m/s",
                               how=T("reference: {f}", f=how) if ref else T("given directly"),
                               ek=float(pt.Ekin / EV), v=float(pt.v)))
            self._check("grid", T("Screen resolution: points on the finest fringe"), self.pts_per_fringe, None, "",
                        _G_PART, ok=self.pts_per_fringe >= 8,
                        note=T("≥ {k:d} are needed; otherwise the pattern and the expectation agree with each other "
                               "but not with physics (review R15)", k=8))
        # paraxial accuracy at the screen vs exact Rayleigh-Sommerfeld (per-slit fields kept for the run)
        if self._rs_screen is None:
            xs = g.x[:: max(1, len(g.x) // 400)]
            self._rs_screen = False if kirchhoff.cost(xs, g.L2, pt.k, g.slits, g.a, g.L1) > RS_BUDGET else \
                (kirchhoff.slit_fields(xs, g.L2, pt.k, g.slits, g.a, g.L1), paraxial.slit_amplitudes(xs, g.L2, pt.k, g.slits, g.a, g.L1))
        if self._rs_screen is False:
            self._check(f"rs{s}", _RS_LABEL, None, None, "", grp, ok=None,
                        note=T("not computed: the exact integral is too costly for this geometry (k·a = {ka:.3g})",
                               ka=float(pt.k * g.a)))
        else:
            Gd = Gf if np.trace(Gf).real > 0 else np.eye(g.n)
            dev, _ = kirchhoff.deviation(*self._rs_screen, Gd)
            self._check(f"rs{s}", _RS_LABEL, dev, 0.0, "", grp, ok=dev < 0.01,
                        note=T("the largest difference of the normalised patterns; > 1 %: the geometry is outside "
                               "the paraxial region"),
                        expected=T("conducting screen: this world's answer is the vector solution; the scalar paraxial "
                                   "pattern is for comparison only, and slits of {a:.3g} µm ≈ {r:.2g} λ lie outside "
                                   "the paraxial region", a=float(g.a * 1e6), r=float(g.a / pt.lam))
                        if ex.vec is not None and dev >= 0.01 else None)
        if g.a < 10 * pt.lam and ex.vec is None:
            self._msg({"type": "notice", "t": self.t, "text": T(
                "A slit narrower than 10 wavelengths: Kirchhoff's boundary condition (the field in the slit equals the "
                "incident one) is inaccurate. For photons there is the vector solution: “Model of the slit screen” → "
                "“perfect conductor” (a plane monochromatic wave).")})
        if self.pts_per_fringe < 8 and fresh:
            self._msg({"type": "notice", "t": self.t,
                       "text": T("The screen grid under-resolves the fringes (< 8 points per fringe).")})
        # fringe period of the computed pattern vs lambda L2 / d (two slits, far field); the scalar model's checks,
        # left out when the hits come from the vector screen
        if g.n == 2 and not getattr(self, "_vec_hits", False):
            fres = g.d**2 / (pt.lam * g.L2)
            A0 = ex.base_A()
            Pb = paraxial.intensity(A0, np.ones((2, 2), complex))
            Pe = paraxial.intensity(A0, np.eye(2, dtype=complex))
            guess = pt.lam * g.L2 / g.d
            per = stats.fringe_period_from_curve(g.x, Pb, Pe, guess, max(0.6 * pt.lam * g.L2 / g.a, 3 * guess))
            if per is not None:
                self._check(f"per{s}", T("Fringe period (from the computed pattern)"), per * 1e6,
                            guess * 1e6 if fres < 0.05 else None, T("µm"), grp, tol=2e-3,
                            note=(T("reference λL/d (far zone, d²/λL = {f:.3g})", f=float(fres)) if fres < 0.05
                                  else T("near zone (d²/λL = {f:.3g}): no simple formula", f=float(fres))))
            # Englert duality (identity for pure marks)
            ops_V, ops_D = self._englert(Gf)
            if ops_V is not None:
                pure = self.source.pol_degree >= 1 and self.source.pol_state != "unpol"
                self._check(f"eng{s}", T("Englert: V² + D² for the which-path marks"), ops_V**2 + ops_D**2,
                            1.0 if pure else None, "", cons, ok=None if pure else (ops_V**2 + ops_D**2 <= 1 + 1e-9),
                            note=_join([T("V = {v:.6f}, D = {d:.6f}; = 1 identically for pure marks, ≤ 1 always",
                                          v=float(ops_V), d=float(ops_D)),
                                        T("the marks at the screen, after the analyser")
                                        if self.app.analyzer[0] != "none" else None]))
            # degree of coherence of the run's own expectation (constrained fit) vs independent references
            gam_e, _ = self._coherence(Pens.sum(axis=0), smooth=True)
            self.gamma_expected = gam_e
            g11, g22, g12 = Gf[0, 0].real, Gf[1, 1].real, Gf[0, 1]
            undefined = self._coherence_undefined()
            gam_m = abs(g12) / math.sqrt(g11 * g22) if g11 > 0 and g22 > 0 and not undefined else None
            if undefined and not mc:  # P15: no fit is shown where gamma_12 means nothing
                self._check(f"coh{s}", _COH_LABEL, None, None, "", grp, note=T("undefined: {why}", why=undefined),
                            info=True)
            elif gam_e is not None and not mc:
                ref, note, tol_abs, group = None, None, None, grp
                if self.laws.collapse == "slit":
                    ref, tol_abs = 0.0, 1e-9
                    note = T("modification: the forced choice of a slit removes the cross terms; 0 is expected")
                elif not model.shifts and self.source.dlam_rel == 0 and gam_m is not None:
                    ref, tol_abs, group = gam_m, 1e-6, cons
                    note = T("reference |⟨m₂|m₁⟩|/(|m₁||m₂|) from the which-path marks; the expectation is built from "
                             "the same marks (an identity)")
                elif self.app.wp_mode == "microscope" and gam_m is not None and not model.s and not model.grw:
                    kp = 2 * math.pi / self.app.mic_lambda
                    gd = scattering.dipole_coherence(kp * g.d, _axis(self.app.mic_dir), _axis(self.app.mic_pol))
                    ref = gam_m * abs((1 - self.app.mic_prob) + self.app.mic_prob * gd)
                    tol_abs = 0.02
                    note = T("reference |1 − p + p⟨e^(iΔk_x d)⟩| for a dipole (Chapman et al. 1995), k_p d = {kd:.4g}; "
                             "it ignores the shift of the envelope by the recoil: a tolerance of {tol:g} for this "
                             "approximation of the reference", kd=float(kp * g.d), tol=tol_abs)
                elif self.laws.collapse == "grw" and not model.s and self.app.wp_mode != "microscope" and gam_m is not None \
                        and self.source.dlam_rel == 0:
                    Lam = self.exp.grw_rate() * g.L2 / pt.v
                    rc = self.laws.grw_rc
                    ref = gam_m * math.exp(-Lam * (1 - math.sqrt(math.pi) * rc / g.d * math.erf(g.d / (2 * rc))))
                    tol_abs = 0.02
                    note = T("GRW reference for hits in flight: exp(−Λ[1 − (√π r_C/d) erf(d/2r_C)]), "
                             "Λ = λ (m/u) L₂/v; a tolerance of {tol:g}: the shift of the envelope by the kicks",
                             tol=tol_abs)
                elif model.s > 0 and self.app.wp_mode != "microscope" and self.laws.collapse == "none" \
                        and self.source.dlam_rel == 0 and gam_m is not None:
                    ref = gam_m * abs(np.sinc(g.src_width * g.d / (pt.lam * g.L1)))
                    tol_abs = 0.02
                    note = T("van Cittert–Zernike reference |sinc(s·d/(λ L₁))|; a tolerance of {tol:g}: the shift of "
                             "the envelope by the source point", tol=tol_abs)
                self._check(f"coh{s}", _COH_LABEL, gam_e, ref, "", group,
                            note=note or T("fit of the computed pattern to the slit basis (envelopes from the marks)"),
                            ok=None if ref is None else abs(gam_e - ref) <= tol_abs)
        # Sorkin parameter (three slits; identity under the Born rule)
        if g.n == 3:
            A0 = ex.base_A()
            Gm = Gf

            def I(sub):
                idx = list(sub)
                return ex.born(np.maximum(paraxial.intensity(A0[idx], Gm[np.ix_(idx, idx)]), 0.0))

            ABC, AB, BC, AC = I([0, 1, 2]), I([0, 1]), I([1, 2]), I([0, 2])
            A_, B_, C_ = I([0]), I([1]), I([2])
            S = float(np.sum(np.abs(ABC - AB - BC - AC + A_ + B_ + C_)) / np.sum(ABC))
            self._check(f"sork{s}", T("Sorkin parameter ∫|I_ABC − I_AB − I_BC − I_AC + I_A + I_B + I_C| / ∫I_ABC"),
                        S, 0.0, "", cons if self.laws.born_p == 2.0 else grp, ok=S < 1e-9,
                        note=T("0 identically under the Born rule (interference is only pairwise); ≠ 0: a "
                               "consequence of the modification"),
                        expected=None if self.laws.born_p == 2.0 else
                        T("the Born rule is changed (P ∝ |ψ|^{p:g}): a non-zero Sorkin parameter is the computed "
                          "consequence of the modification, and the experiment shows exactly that",
                          p=float(self.laws.born_p)))
        # no-signalling: the SAMPLED screen marginal does not depend on reading the detector (review R7)
        if self.theory["nR"] > 1:
            rngn = np.random.default_rng([self.seed, 99, self.seg])
            b = ex.emit(np.zeros(64), 0, rngn)
            ex.at_slits(b, np.arange(64), self.app, rngn)
            G, Gf_ = ex.gram(b.chi, self.app, self.app)
            Ir = ex.born(ex.intensities(b.lam, b.xs, b.kappa, G))
            Iu = ex.born(ex.intensities(b.lam, b.xs, b.kappa, Gf_[:, None]))
            Pr = Ir.sum(axis=1) / np.maximum(Ir.sum(axis=(1, 2))[:, None], 1e-300)
            Pu = Iu[:, 0] / np.maximum(Iu.sum(axis=(1, 2))[:, None], 1e-300)
            dif = float(np.max(np.abs(Pr - Pu)) / np.max(Pu))
            self._check(f"nosig{s}", T("No signalling: the distribution on the screen with the detector read = "
                                       "without reading"), dif, 0.0, "",
                        cons if self.laws.born_p == 2.0 else grp, ok=dif < 1e-10,
                        note=T("under the Born rule an identity (the readout basis is complete); under a modification "
                               "a difference is a computed consequence: reading the detector would change the pattern "
                               "(signalling)"))

    def _englert(self, Gf):
        # both from the marks themselves (a forced-collapse modification is a law, not a mark)
        ops, rho = self._ens_ops()
        Ma = ops[0] @ rho @ ops[0].conj().T
        Mb = ops[1] @ rho @ ops[1].conj().T
        Mab = ops[0] @ rho @ ops[1].conj().T
        na, nb = np.trace(Ma).real, np.trace(Mb).real
        if na + nb <= 0:
            return None, None
        V = 2 * abs(np.trace(Mab)) / (na + nb)
        D = float(np.sum(np.abs(np.linalg.eigvalsh((Ma - Mb) / (na + nb)))))
        return float(V), D

    def _ens_ops(self):
        """Operators chi -> |m_j> (internal (x) detector) for the current apparatus, and the source's density matrix."""
        ex, app = self.exp, self.app
        J = ex.element_mats(app)
        Pa = marks.analyzer_matrix(app.analyzer[0], app.analyzer[1], self.particle.internal)
        dets = marks.detector_states(self.geom.n, app.wp_slit, app.wp_theta, app.wp_mode == "qubit")
        ph = np.exp(1j * ex.ab_phases(app))
        ops = [np.kron(Pa @ J[j], dets[j][:, None]) * ph[j] for j in range(self.geom.n)]
        return ops, ex_rho(self.source, self.particle.internal)

    def _coh_basis(self, bins):
        g = self.geom
        A0 = self.exp.base_A()
        b11, b22, b12 = np.abs(A0[0]) ** 2, np.abs(A0[1]) ** 2, A0[0] * A0[1].conj()
        if bins:
            e = self.edges
            b11, b22 = _rebin(g.x, b11, e), _rebin(g.x, b22, e)
            b12 = _rebin(g.x, b12.real, e) + 1j * _rebin(g.x, b12.imag, e)
        return b11, b22, b12, self.Gavg[0, 0].real, self.Gavg[1, 1].real

    def _coherence(self, curve, weights=None, bins=False, smooth=False, dark=None):
        """|gamma_12| of a pattern (density on the grid, or counts in bins) by the constrained fit (review R2); None
        where it is not defined (``_coherence_undefined``)."""
        if self.geom.n != 2 or self._coherence_undefined():
            return None, None
        return stats.coherence_ml(curve, *self._coh_basis(bins), dark=dark, poisson=not smooth)

    def _coherence_undefined(self):
        """Why |gamma_12| = |G12|/sqrt(G11 G22) cannot be measured here, or None (review UX-params P15: crossed
        polarisers in the slits gave |gamma| = 1.108, a fit of rounding noise). A slit whose transmission is below
        COH_DARK of the other's passes nothing (cos^2 90° = 3.7e-33): there is nothing to interfere with, G12/sqrt(G11 G22)
        is 0/0. A screen grid that does not resolve the fringes (the check “Screen resolution”, < 8 points on the
        finest fringe) gives a fit of aliased curves."""
        if self.geom.n != 2:
            return None
        g11, g22 = float(self.Gavg[0, 0].real), float(self.Gavg[1, 1].real)
        hi = max(g11, g22)
        if not hi > 0:
            return T("both slits are dark: nothing passes through them")
        if min(g11, g22) <= COH_DARK * hi:
            j = 1 if g11 < g22 else 2
            return T("slit {j:d} is dark (it passes {r:.1e} of the other's): there is nothing to interfere with, "
                     "|γ₁₂| = |G₁₂|/√(G₁₁G₂₂) is the indeterminate form 0/0", j=j, r=min(g11, g22) / hi)
        if self.pts_per_fringe < 8:
            return T("the screen grid does not resolve the fringes ({p:.2g} points on the finest fringe < 8, check "
                     "“Screen resolution”): a fit of such a pattern means nothing", p=float(self.pts_per_fringe))
        return None

    def _coherence_err(self, h, dark):
        """Error of the histogram |gamma_12| shown to the user, and why there is none: ``stats.coherence_boot``
        (a parametric bootstrap from the fit projected onto |gamma| <= 1; None with the reason below
        ``stats.COH_BOOT_MIN_HITS`` hits, when the fit fails or when too few refits succeed). Recomputed when the
        segment changes and whenever the count has grown by 10 % since the last computation (also while it is below
        the threshold, where the call is cheap); in between the last value is shown unchanged, as the error of the count
        it was computed at (review R-W F2, D9: the error does not scale as 1/sqrt(n) near |gamma| = 1, so the former
        sqrt(n_then / n) rescaling is dropped, and the former throttle of COH_ERR_FRAMES frames is dropped too, since it
        let a fast build-up show an error computed at a much smaller count). The count alone decides, so that a world
        rebuilt from its record shows the same errors (review C1-6); at most ~log(n / 300) / log(1.1) bootstraps of
        0.1–0.2 s per segment. Returns (err or None, why or None)."""
        n = float(h.sum())
        c = self._coh_err_cache
        if c is None or c[0] != self.seg or n >= 1.1 * c[1] or (c[2] is None and c[1] < stats.COH_BOOT_MIN_HITS < n + 1):
            rng = np.random.default_rng([self.seed, 4243, self.seg, int(n)])
            r = stats.coherence_boot(h, *self._coh_basis(True), dark=dark, rng=rng)
            self._coh_err_cache = c = (self.seg, n, r["err"], r["why"])
        return c[2], (None if c[2] is not None else c[3])

    # --- time -----------------------------------------------------------------------------------------
    def max_step(self):
        # every event of a step (signal and dark counts) is held at once: their number per step is bounded (P8)
        return STEP_EVENTS / (self.app.rate + self.dark_rate)

    def advance(self, t_target):
        g, ex = self.geom, self.exp
        rng = self.rng
        # 1. emissions
        te = []
        while self.t_next <= t_target:
            te.append(self.t_next)
            self.t_next += rng.exponential(1.0 / self.app.rate)
        if te:
            b = ex.emit(np.array(te), self.pid, rng)
            b.epoch = self.src_epoch
            self.pid += len(te)
            self.counts["emitted"] += len(te)
            self.batches.append(b)
        # 2. slit plane, with the apparatus present now; 3. screen, with the apparatus present now
        TD, X, Y, F, K, S, P = [], [], [], [], [], [], []
        for b in self.batches:
            idx = np.nonzero((b.stage == 0) & (b.t_slit <= t_target))[0]
            if len(idx):
                ex.at_slits(b, idx, self.app, rng)
                self.counts["absorbed_slits"] += int(b.absorbed[idx].sum())
                self.counts["scattered"] += int(b.scat[idx].sum())
                self.counts["grw_hits"] += int(b.hits[idx].sum())
                for i in idx[b.absorbed[idx]][:2]:
                    self.pending_stories.append(ex.story(b, i, T("absorbed by an element at a slit"), None))
                b.stage[idx[b.absorbed[idx]]] = 2
            idx = np.nonzero((b.stage == 1) & (b.t_det <= t_target))[0]
            chunk = max(4, int(2e6 // (g.n * len(g.x))))
            for i0 in range(0, len(idx), chunk):
                sub = idx[i0:i0 + chunk]
                out = ex.at_screen(b, sub, self.app, self.seg, rng, story_n=2 if i0 == 0 else 0)
                if getattr(b, "epoch", 0) != self.src_epoch:  # emitted by the source before it was changed
                    out.flags |= FLAG_MIX
                    out.counts["mixed"] = out.counts["detected"]
                for k2, v in out.counts.items():
                    self.counts[k2] = self.counts.get(k2, 0) + v
                self.pending_stories.extend(out.stories)
                if len(out.t_det):
                    TD.append(out.t_det); X.append(out.x); Y.append(out.y); F.append(out.flags); K.append(out.kick)
                    S.append(out.seg); P.append(out.pid)
                b.stage[sub] = 2
        self.batches = [b for b in self.batches if np.any(b.stage < 2)]
        # dark counts in (t, t_target]
        if self.dark_rate > 0 and t_target > self.t:
            nd = rng.poisson(self.dark_rate * (t_target - self.t))
            if nd:
                TD.append(np.sort(self.t + rng.random(nd) * (t_target - self.t)))
                X.append(rng.uniform(g.x[0], g.x[-1], nd)); Y.append((rng.random(nd) - 0.5).astype(np.float32))
                F.append(np.full(nd, FLAG_DARK, np.uint8)); K.append(np.zeros(nd, np.float32))
                S.append(np.full(nd, self.seg, np.uint16)); P.append(np.full(nd, 0xFFFFFFFF, np.uint32))
                self.counts["dark"] += nd
        if TD:
            Tc = np.concatenate(TD)
            order = np.argsort(Tc, kind="stable")
            arrs = {"t": Tc[order], "x": np.concatenate(X)[order], "y": np.concatenate(Y)[order],
                    "f": np.concatenate(F)[order], "k": np.concatenate(K)[order], "s": np.concatenate(S)[order],
                    "id": np.concatenate(P)[order]}
            ok = (arrs["s"] == self.seg) & ((arrs["f"] & FLAG_MIX) == 0)  # transitional particles are not counted
            if ok.any():
                nb = self._nbins()
                ib = np.clip(((arrs["x"][ok] - g.x[0]) / (g.x[-1] - g.x[0]) * nb).astype(int), 0, nb - 1)
                r = ((arrs["f"][ok] & 2) > 0).astype(int) if self.theory["nR"] > 1 else np.zeros(int(ok.sum()), int)
                np.add.at(self.hist["bins"], (r, ib), 1)
                self.hist["n"] += int(ok.sum())
            self._msg({"type": "detections", "t": t_target, "n": int(len(Tc))}, arrs)
        due = [st for st in self.pending_stories if st["t_det"] <= t_target]
        if due:
            self.pending_stories = [st for st in self.pending_stories if st["t_det"] > t_target]
            self._msg({"type": "stories", "t": t_target, "stories": due})
        self.t = t_target

    # --- frames ---------------------------------------------------------------------------------------
    def frame(self):
        st = {"counts": self.counts, "seg": self.seg, "n_seg": self.hist["n"]}
        fl = []
        for b in self.batches:
            m = b.stage < 2
            fl.append(np.stack([b.t_e[m], b.v[m]], axis=1))
        fl = np.concatenate(fl)[-200:] if fl else np.zeros((0, 2))
        h = self.hist["bins"].sum(axis=0).astype(float)
        if self.hist["n"] >= 50:
            # expected counts of the segment: the run's expectation per emitted particle, plus dark counts, scaled
            exp_bins = self.theory["curves"]["all"]
            x2, pval, dof = stats.chi2(h, exp_bins)
            st["chi2"] = {"x2": x2, "p": pval, "dof": dof}
            if self.geom.n == 2 and not getattr(self, "_vec_hits", False):
                why = self._coherence_undefined()
                if why:  # P15: said instead of a fit of noise
                    st["coh"] = {"hist": None, "err": None, "expected": None, "why": why}
                else:
                    nb = len(h)
                    dark = np.full(nb, self.dark_rate * (self.t - self.seg_t0) / nb)
                    gh, _ = self._coherence(h, bins=True, dark=dark)
                    err, err_why = self._coherence_err(h, dark) if gh is not None else (None, None)
                    st["coh"] = {"hist": gh, "err": err, "err_why": err_why, "min_hits": stats.COH_BOOT_MIN_HITS,
                                 "expected": getattr(self, "gamma_expected", None)}
        return st, {"flight": fl.astype(np.float64)}

    def next_event_time(self):
        """The next emission or the next arrival at the slits or at the screen."""
        cands = [self.t_next]
        for b in self.batches:
            m0, m1 = b.stage == 0, b.stage == 1
            if m0.any():
                cands.append(float(b.t_slit[m0].min()))
            if m1.any():
                cands.append(float(b.t_det[m1].min()))
        return min(cands)

    def action(self, name, args):
        if name == "apparatus":  # the former action form; the apparatus fields are live parameters now
            return self.set_live({k: v for k, v in args.items() if k in APP_FIELDS})
        if name == "clear":
            self.app = Apparatus(**{**self.app.__dict__, "seg": self.seg + 1})
            self._new_segment(T("screen cleared"))
            return T("a new segment: the screen is cleared, the set-up is the same")
        raise Refusal(T("unknown action {name}", name=repr(name)))

    def _setup_info(self):
        """What the view needs about the current set-up (it changes with live parameters)."""
        g, pt = self.geom, self.particle
        return {"title": T("Double-slit experiment: {particle}", particle=pt.label), "particle": pt.describe(),
                "geometry": {"n": g.n, "a": g.a, "d": g.d, "L1": None if math.isinf(g.L1) else g.L1, "L2": g.L2,
                             "slits": g.slits.tolist(), "src_width": g.src_width, "pixel": g.pixel,
                             "nbins": self._nbins(), "half": float(g.x[-1])},
                "t_flight": self.t_flight, "rate": self.app.rate}

    def header(self):
        g, pt = self.geom, self.particle
        mods = SCHEMA.modifications(self.params)
        d = pt.describe()
        return {
            "title": T("Double-slit experiment: {particle}", particle=pt.label),
            "text": T("The source emits particles one at a time (a Poisson stream). Each particle is its own wave behind "
                      "the slits (its own wavelength, source point, internal state, recoil from a scattered photon); at "
                      "the slits the elements and the observer act on it, in front of the screen the analyser; its "
                      "place on the screen follows the Born rule with its marks; the pattern is the accumulation of "
                      "these events. Left: the view from above, the expected wave (the run's ensemble), the particles "
                      "in flight, the flow lines. Right: the screen and the histogram with the run's expectation. A "
                      "change of the set-up starts a new segment; particles that passed the slits before the change "
                      "and arrived after it are marked as transitional."),
            "particle": d, "modifications": mods,
            "geometry": {"n": g.n, "a": g.a, "d": g.d, "L1": None if math.isinf(g.L1) else g.L1, "L2": g.L2,
                         "slits": g.slits.tolist(), "src_width": g.src_width, "pixel": g.pixel, "nbins": self._nbins(),
                         "half": float(g.x[-1])},
            "t_flight": self.t_flight, "rate": self.app.rate,
            "actions": self._actions(),
            "laws": {"born_p": self.laws.born_p, "collapse": self.laws.collapse},
        }, {"x": g.x}


_ELEM_LABEL = ELEMENT_NAMES  # an element by its short name (refusals, notices, the segment's description)
_RS_LABEL = T("Paraxial approximation on the screen: difference from the exact Rayleigh–Sommerfeld integral")
_COH_LABEL = T("Degree of coherence of the slits |γ₁₂| in the run's expected pattern")


def _who(pt):
    """The particle as the object of “does not act on …” (a text of its own per particle, so that each language
    can put it in the right case)."""
    return {"photon": T("a photon"), "electron": T("an electron"), "neutron": T("a neutron"),
            "he4": T("a ⁴He atom"), "c60": T("a C₆₀ fullerene")}.get(pt.species,
                                                                    T("the particle “{p}”", p=pt.label))


def _exc_text(e):
    """The text of an exception of the engine: its translatable text when it carries one, else its own words."""
    a = e.args[0] if e.args else None
    return a if is_t(a) else str(e)


def _len_text(x):
    """A length with the unit that suits it."""
    a, x = abs(x), float(x)
    if a >= 1e3:
        return T("{v:.3g} km", v=x / 1e3)
    if a >= 1.0:
        return T("{v:.3g} m", v=x)
    if a >= 1e-3:
        return T("{v:.3g} mm", v=x * 1e3)
    if a >= 1e-6:
        return T("{v:.3g} µm", v=x * 1e6)
    if a >= 1e-9:
        return T("{v:.3g} nm", v=x * 1e9)
    return T("{v:.3g} pm", v=x * 1e12)


def _check_rates(p):
    """Review UX-params P8: refuse dark counts far above the source's rate (each dark count is an event of the
    record; at 1e12 1/s one frame drew ~2e9 of them). Cheap: used by ``check_params`` as well."""
    rate, dark = float(p["rate"]), float(p["dark_rate"])
    if rate > 0 and dark > DARK_PER_PARTICLE_MAX * rate:
        raise Refusal(T("{dark:.3g} dark counts per second with a source of {rate:.3g} particles/s: that is {r:.3g} "
                        "false counts per particle; the screen would show only noise, and every count is an event of "
                        "the record (the limit is {lim:g} per particle)", dark=dark, rate=rate, r=dark / rate,
                        lim=DARK_PER_PARTICLE_MAX),
                      T("reduce “Dark counts” to {d:.3g} 1/s or increase “Particles per second” to {n:.3g}",
                        d=DARK_PER_PARTICLE_MAX * rate, n=dark / DARK_PER_PARTICLE_MAX))


def _same(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return math.isclose(float(a), float(b), rel_tol=1e-12, abs_tol=0.0)
    return a == b


def _val(pid, v):
    """A parameter's value as the event of a change shows it: a choice by its label, yes/no, a number as it is."""
    if isinstance(v, bool):
        return T("yes") if v else T("no")
    par = SCHEMA.by_id[pid]
    if par.type == "select":
        return next((o[1] for o in par.options if o[0] == v), str(v))
    if isinstance(v, (int, float)):
        return v
    return str(v)


def _fit_apparatus(f, pt, n):
    """Remove the parts of the apparatus that the new particle or slits cannot take (a live change of the particle
    must not be refused because of a polarizer left on the slits); returns the fitted fields and notices."""
    f = dict(f)
    notes = []
    for j, (ek, ak) in enumerate((("el1", "el1_angle"), ("el2", "el2_angle"))):
        if f[ek] == "none":
            continue
        try:
            marks.element_matrix(f[ek], f[ak], pt.internal)
        except ValueError:
            notes.append(T("“{elem}” at slit {j:d} removed: it does not act on {who}", elem=_ELEM_LABEL[f[ek]],
                           j=j + 1, who=_who(pt)))
            f[ek] = "none"
    if f["analyzer"] == "on" and pt.internal is None:
        notes.append(T("analyser removed: this particle has no internal state"))
        f["analyzer"] = "none"
    if f["wp_mode"] == "microscope" and pt.species not in MIC_SPECIES:
        notes.append(T("microscope switched off: the probe's dipole scattering is not defined for this particle"))
        f["wp_mode"] = "none"
    if not (1 <= int(f["wp_slit"]) <= n):
        notes.append(T("which-path detector moved to slit 1 (there are {n:d} slits now)", n=int(n)))
        f["wp_slit"] = 1
    return f, notes


# what the vector screen's display needs (review B8 C6): an estimated error below one pixel of the expected curve (the
# histogram plot is about 200 px tall) — and far below what the histogram's chi^2 can see: a shape error of 4e-3 shifts
# chi^2 by N sum p delta^2 <= 1.6e-5 N, comparable with its spread sqrt(2 dof) ~ 15 only after ~3e6 detections
VEC_ERR_TOL = 4e-3
VEC_EST_POINTS = 201  # screen points of the error estimate of the flux (a subsample of the screen grid)


def _vector_check(pt, g, p):
    """The set-ups the vector model covers (cheap; every build, also when the solution is reused)."""
    if pt.species != "photon":
        raise Refusal(T("the conducting screen (vector diffraction) is defined for photons only"),
                      T("choose “Model of the slit screen” = scalar, or photons"))
    if math.isfinite(g.L1):
        raise Refusal(T("conducting screen: the incident wave must be plane"),
                      T("set “Source: distance to the slits” to 0"))
    if p["dlam_rel"] > 0:
        raise Refusal(T("conducting screen: the source must be monochromatic"), T("set “Spectral width σ” to 0"))
    k = pt.k
    if k * g.a > VEC_KA_MAX:
        raise Refusal(T("conducting screen: the slit is wider than {w:.1f} λ (k·a = {ka:.0f} > {kmax:.0f}); the vector "
                        "solution is not computed here (too costly); for such slits the scalar model differs from the "
                        "vector one by an amount of order 1/(k·a)", w=VEC_WIDTH_MAX, ka=float(k * g.a), kmax=VEC_KA_MAX),
                      T("make the slits narrower or the wavelength longer, or choose the scalar model"))


def _vector_screen(pt, g, p, laws, cache=None):
    """The conductor screen of the vector mode for the set-up (lfphys.core.em.slit): for TE and TM the energy flux
    through the screen plane on the screen grid, the transmitted power, the checks and the estimated errors of the
    truncation in modes (``SlitSolution.error_estimate``: T, the far-field pattern and the flux on VEC_EST_POINTS points
    of the screen); the scalar Kirchhoff flux in the same plane (``theories.approx.kirchhoff``, exact propagation).
    Raises (the change is refused) for set-ups the vector model does not cover. The solutions depend only on the
    wavelength, the slits and the thickness, the fluxes also on the screen: both are kept in ``cache`` and reused, so
    that a change of the source's polarisation or of the detector does not solve again (review B8 C9: it blocked the
    world for 15-17 s); the polarisation weights are applied per segment. Returns (out, cache)."""
    _vector_check(pt, g, p)
    cache = dict(cache or {})
    k = pt.k
    t = p["screen_t_um"] * 1e-6
    W = g.n * g.d
    key_sol = ("sol", float(k), tuple(float(c) for c in g.slits), float(g.a), float(t))
    if cache.get("sol_key") != key_sol:
        sols = {pol: vslit.solve(k, g.slits, g.a, t, pol) for pol in ("TE", "TM")}
        cache = {"sol_key": key_sol, "sols": sols, "doubled": {pol: False for pol in sols},
                 "est": {pol: sols[pol].error_estimate() for pol in sols},
                 "bal": {pol: sols[pol].power_balance() for pol in sols},
                 "T_K": kirchhoff.plane_wave_transmission(k, g.slits, g.a)}
    key_scr = key_sol + (float(g.L2), float(g.x[0]), float(g.x[-1]), len(g.x))
    if cache.get("scr_key") != key_scr:
        cache = {**cache, "sols": dict(cache["sols"]), "doubled": dict(cache["doubled"]), "est": dict(cache["est"]),
                 "bal": dict(cache["bal"])}
        zs = np.full(len(g.x), t + g.L2)
        xs = g.x[np.unique(np.linspace(0, len(g.x) - 1, VEC_EST_POINTS).round().astype(int))]

        def flux_xs(s_):
            return s_.flux_z(xs, np.full(len(xs), t + g.L2))
        scr = {}
        for pol in ("TE", "TM"):
            sol = cache["sols"][pol]
            q = sol.error_estimate(quantity=flux_xs, parts=())["quantity"]
            # above the display's tolerance (on this screen, or in T) the waveguide modes are doubled once: algebraic
            # convergence of order 1.2-1.4 brings the error down about 2.5 times; the solution is kept for the screen
            # that asked (and any later one)
            if sol.method == "modal" and not cache["doubled"][pol] and max(cache["est"][pol]["T"], q) > VEC_ERR_TOL:
                sol = vslit.solve(k, g.slits, g.a, t, pol, modes=[2 * m for m in sol.modes], method="modal")
                cache["sols"][pol], cache["doubled"][pol] = sol, True
                cache["est"][pol] = sol.error_estimate()
                cache["bal"][pol] = sol.power_balance()
                q = sol.error_estimate(quantity=flux_xs, parts=())["quantity"]
            scr["J_" + pol] = sol.flux_z(g.x, zs)
            scr["est_" + pol] = {**cache["est"][pol], "quantity": q}
        uk, _, ukz = kirchhoff.plane_wave_field(k, g.slits, g.a, g.x, np.full(len(g.x), g.L2), deriv=True)
        scr["J_K"] = np.imag(np.conj(uk) * ukz) / k
        cache.update(scr_key=key_scr, scr=scr)
    sols = cache["sols"]
    scr = cache["scr"]
    out = {"W": W, "t": t, "hits": laws.born_p == 2.0 and laws.collapse == "none", "T_K": cache["T_K"],
           "J_K": scr["J_K"]}
    for pol in ("TE", "TM"):
        sol, bal, est = sols[pol], cache["bal"][pol], scr["est_" + pol]
        out["J_" + pol] = scr["J_" + pol]
        out["Pt_" + pol] = bal["P_t"]
        err = max(est["T"], est["quantity"])
        out[pol] = {"T": bal["T"], "P_t": bal["P_t"], "P_b": bal["P_b"], "ext": bal["extinction"], "rel": bal["rel"],
                    "rel_modes": bal.get("rel_modes"), "err": err, "err_T": est["T"], "err_screen": est["quantity"],
                    "err_kind": est["kind"], "err_order": est["order"], "levels": [int(m[0]) for m in est["levels"]],
                    "modes": int(sol.modes[0]), "method": sol.method}
    pmax = max(out["Pt_TE"], out["Pt_TM"]) / W
    if pmax > 1:
        raise Refusal(T("conducting screen: the transmitted power is larger than the power falling on the strip n·d "
                        "({p:.3g} > 1); the slit's capture cross-section is wider than the period", p=float(pmax)),
                      T("increase the slit period"))
    return out, cache


def ex_rho(source: Source, internal):
    if internal is None:
        return np.ones((1, 1), complex)
    if source.pol_state == "unpol":
        return 0.5 * np.eye(2, dtype=complex)
    psi = marks.sample_internal(np.random.default_rng(0), internal, source.pol_state, 1.0, source.pol_custom)
    P = source.pol_degree
    return P * np.outer(psi, psi.conj()) + (1 - P) * 0.5 * np.eye(2)


def _axis(name):
    return {"x": np.array([1.0, 0, 0]), "y": np.array([0, 1.0, 0]), "z": np.array([0, 0, 1.0])}[name]


def _rebin(x, P, edges):
    """Integrate the density P (per metre, on grid x) over histogram bins (trapezoid, the sampler's density)."""
    c = np.concatenate([[0.0], np.cumsum(0.5 * (P[1:] + P[:-1]) * np.diff(x))])
    return np.diff(np.interp(edges, x, c))


def _story_single_slit_minimum_mm() -> float:
    """The first dark minimum of one slit of the story's preset on its screen, λ·L/a in mm (the far field: the story's
    Fresnel number a²/(λL) is 6·10⁻⁴), for the caption of the stage with slit 2 closed."""
    p, _errs = SCHEMA.resolve("story", {})
    return float(p["lam_nm"]) * 1e-9 * float(p["L2_m"]) / (float(p["a_um"]) * 1e-6) * 1e3


# Watch (design §6.1): what to look at, at each step of the story (played seconds; the script changes the set-up at the
# same times)
STORY_CAPTIONS = [
    {"at": 0, "text": T("One photon at a time leaves the source on the left, passes the slits and lands at one point "
                        "of the screen on the right. Each dot is one photon.")},
    {"at": 8, "text": T("Where the next photon lands cannot be predicted: the hits look random. Only their probability "
                        "is computed: the orange curve under the screen.")},
    {"at": 16, "text": T("Ten times faster: hundreds of hits, then about two thousand. Their histogram follows the orange "
                         "curve, and bright and dark bands appear on the screen.")},
    {"at": 22, "text": T("The bands are interference: the wave of each photon passes through both slits, and the two "
                         "parts add up in some places and cancel in others. The grey dashed curve is what the two "
                         "slits would give without interference."), "hold": 3},
    # review R-W F9: one slit still diffracts; its first dark minima at ±λL/a (Fraunhofer: a²/(λL) = 6·10⁻⁴), which
    # the run's expectation for this segment shows (tests/test_u32_screens.py finds them on its curve)
    {"at": 26, "text": T("Slit 2 is closed, and the count starts again. The two-slit fringes are gone: one slit gives a "
                         "broad diffraction maximum, its first dark minima at ±{x:.3g} mm.", x=_story_single_slit_minimum_mm())},
    {"at": 36, "text": T("Both slits are open, but a detector at slit 1 marks which slit each photon took: no bands. "
                         "The hits follow the grey dashed curve, the two slits without interference.")},
    {"at": 48, "text": T("The detector is removed, and the bands come back: interference needs the two paths to be "
                         "indistinguishable.")},
]


VIZ = {
    "id": "u32_double_slit",
    "title": T("The double-slit experiment"),
    "summary": T("Particles one at a time through slits: a photon (energy, frequency, polarisation), an electron, a "
                 "neutron, an atom, C60. A which-path observer (a qubit detector, photon scattering), marks by "
                 "polarisation or spin, the quantum eraser, the Aharonov–Bohm effect, flow lines."),
    "purpose": T("A study of how a particle behaves and of why interference appears and disappears; the laws can be "
                 "changed on purpose (the exponent in the Born rule, GRW spontaneous collapse, a forced choice of "
                 "slit)."),
    "version": "1.3",
    "schema": SCHEMA,
    "simulation": Simulation,
    "audience": "university",
    "section": "quantum",
    "ui": "standard",
    "teaser": T("Particles land one by one; the fringes build up hit by hit and vanish under a which-path mark."),
    "courses": [
        {"text": T("The Feynman Lectures on Physics, vol. III"), "chapters": "1"},
        {"text": T("Griffiths & Schroeter, Introduction to Quantum Mechanics"), "chapters": ""},
        {"text": T("Halliday, Resnick & Walker, Fundamentals of Physics"), "chapters": "35, 38"},
        {"text": T("Hecht, Optics"), "chapters": "9"},
    ],
    "related": ["S38", "r12_double_slit_2d", "R01", "R02", "R05", "R08", "R09"],
    "recordings": [
        # Watch: «The double slit, step by step» (design §6.1). The source sends 1000 photons per second of world time;
        # the script's speed (world seconds per played second) goes from 2 photons per played second to 200, and each
        # change of the set-up starts a new segment, which the screen shows on its own
        {"id": "story", "preset": "story", "seconds": 60, "fps": 20, "speed": None, "seed": 1, "poster": 25,
         "script": [{"at": 0, "cmd": "speed", "args": {"value": 0.002}},
                    {"at": 8, "cmd": "speed", "args": {"value": 0.02}},
                    {"at": 16, "cmd": "speed", "args": {"value": 0.2}},
                    {"at": 26, "cmd": "set", "args": {"values": {"el2": "block"}}},
                    {"at": 36, "cmd": "set", "args": {"values": {"el2": "none", "wp_mode": "qubit", "wp_slit": 1,
                                                                 "wp_theta": 90}}},
                    {"at": 48, "cmd": "set", "args": {"values": {"wp_mode": "none"}}}],
         "captions": STORY_CAPTIONS,
         "quantize": {"segment.map": "u8sqrt", "segment.bohm_x": "u16", "detections.x": "u16", "detections.y": "u8"}},
        {"id": "young", "preset": "photon_young", "seconds": 60, "fps": 20,
         "speed": None, "seed": 1, "script": [], "poster": 55,
         "captions": [{"at": 0, "text": T("Photons of {lam:g} nm pass two slits one at a time; each dot on the screen "
                                          "is one photon.", lam=632.8)},
                      {"at": 20, "text": T("Hit by hit, bright and dark bands build up: interference. The orange curve "
                                           "is the run's computed expectation.")}]},
        {"id": "eraser", "preset": "photon_eraser", "seconds": 60, "fps": 20,
         "speed": None, "seed": 1, "script": [], "poster": 55,
         "captions": [{"at": 0, "text": T("Polarisers H and V at the two slits mark which slit each photon took; an "
                                          "analyser at {a:g}° in front of the screen erases that mark.", a=45.0)},
                      {"at": 20, "text": T("The analyser lets only part of the photons through, and among them the "
                                           "bands are back: the which-path mark is erased.")}]},
        {"id": "aharonov_bohm", "preset": "electron_ab", "seconds": 60, "fps": 20,
         "speed": None, "seed": 1, "script": [], "poster": 55,
         "captions": [{"at": 0, "text": T("Electrons pass two slits; between the slits a thin coil holds a magnetic "
                                          "flux of ½ h/e, and no magnetic field reaches the electrons' paths.")},
                      {"at": 20, "text": T("The bands are shifted by half a period: a dark band at the centre. The flux "
                                           "changes the phase between the two paths (the Aharonov–Bohm effect).")}]},
    ],
    # the screens (design §6): Watch with the captioned story and the other recordings; Explore over λ × d × a, 48
    # points of one seeded sample of 5000 photons each, with the run's expectation and its χ²
    "screens": [
        {"id": "watch", "kind": "watch", "recording": "story", "more": ["young", "eraser", "aharonov_bohm"]},
        {"id": "explore", "kind": "explore", "preset": "photon_young", "fixed": {"n_bohm": 20, "screen_um": 30000.0},
         "controls": [{"param": "lam_nm", "values": [400.0, 500.0, 600.0, 700.0], "default": 600.0,
                       "label": T("Wavelength λ"), "unit": "nm"},
                      {"param": "d_um", "values": [50.0, 100.0, 200.0, 300.0], "default": 100.0,
                       "label": T("Slit period d"), "unit": "µm"},
                      {"param": "a_um", "values": [10.0, 20.0, 40.0], "default": 20.0,
                       "label": T("Slit width a"), "unit": "µm"}],
         "acts": "now", "time": "buildup", "frame_dt": 0.25, "stop": {"world_s": 5.25}, "seed": 1,
         "drop": {"types": ["stories"], "frame_blobs": ["flight"]},
         "quantize": {"segment.map": "u8sqrt", "segment.bohm_x": "u16", "detections.t|x": "u16",
                      "detections.y": "u8", "header.x": "u16"},
         "overlays": ["expectation", "no_interference", "wave", "flow_lines"], "traces": 3},
    ],
}
