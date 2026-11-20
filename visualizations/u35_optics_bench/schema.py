# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u35's parameters and presets (the schema): the source, the media (real materials or a model medium) and their glass
blocks, the structure, the devices (analysers, detectors, the counters' gate, the reference count). Every parameter is
live: the set-up an experimenter changes while the world runs. Real materials everywhere (design §3.9); a constant
index only as a «model medium»."""

from __future__ import annotations

from lfviz.params import Param, Schema

from lfphys.i18n import T

from .engine.bench import ARM_M, BLOCK_MM, DETECTORS, MATERIAL_NAME, MEDIA, POL_LABEL, STRUCTS, TH_MAX

def _p(*a, **k):
    k.setdefault("live", True)  # the whole bench is set-up an experimenter changes while the world runs
    return Param(*a, **k)


SHOW = lambda *kinds: {"structure": list(kinds)}  # noqa: E731

G_SRC, G_MED, G_STR, G_DEV = T("Source"), T("Media"), T("Structure"), T("Devices")
HENE = 632.8  # the He-Ne laser's line in air, nm (the SCHOTT indices are relative to air at the wavelength in air)
BENCH_RATE = 2e5  # photons per second on the benches: a rate a single-photon detector counts (design §11, item 36)
DET_DEFAULT = "spcm_aqrh_14_650nm"  # the integrator's decision of 2026-11-18: a real device is the default
IMPERFECT = (0.90, 0.009)  # an imperfect analyser: k1 and k2 (extinction ratio 1e-2), a model device

_ANA_OPTIONS = [("out", T("out (one detector)")), ("ideal", T("ideal polarising beam splitter (k₁ = 1, k₂ = 0)")),
                ("real", T("imperfect polarising beam splitter (k₁, k₂ below)"))]

SCHEMA = Schema([
    # source
    _p("lam_nm", T("Wavelength λ, nm"), "float", HENE, group=G_SRC, min=300.0, max=1600.0,
       help=T("The centre of the source's line, in air for the SCHOTT glasses (their indices are relative to air).")),
    _p("dlam_nm", T("Line width Δλ (FWHM), nm"), "float", 0.002, group=G_SRC, min=0.0, max=50.0,
       help=T("A Gaussian line; each photon's wavelength is drawn from it. {w} nm is a He-Ne laser's line (about 1.5 "
              "GHz); an LED's is tens of nanometres.", w=0.002)),
    _p("theta_deg", T("Angle of incidence θ, °"), "float", 45.0, group=G_SRC, min=0.0, max=TH_MAX,
       help=T("The angle between the beam and the normal to the surface. The source and both detectors stand on a "
              "rotary table: when it turns, the photons already flying along the old paths are lost (the count "
              "“lost”).")),
    _p("pol", T("Polarisation"), "select", "unpol", group=G_SRC,
       options=[("s", T("s (TE): E ⊥ the plane of incidence")), ("p", T("p (TM): E in the plane of incidence")),
                ("lin", T("linear at the angle ψ from p towards s")), ("unpol", POL_LABEL["unpol"])]),
    _p("psi_deg", T("Polarisation angle ψ, °"), "float", 45.0, group=G_SRC, min=-180.0, max=180.0,
       show_if={"pol": ["lin"]}, help=T("ψ = 0°: p; ψ = 90°: s.")),
    _p("rate", T("Photons per second (world time)"), "float", BENCH_RATE, group=G_SRC, min=1.0, max=1e15, log=True,
       help=T("A Poisson stream of single photons. The flight along an arm of {arm:.3g} cm takes about {t:.1g} ns.",
              arm=ARM_M * 100, t=ARM_M / 2.99792458e8 * 1e9)),
    _p("shutter", T("Shutter"), "select", "open", group=G_SRC,
       options=[("open", T("open")), ("closed", T("closed (no photons: the detectors count only their dark counts)"))]),
    # media
    _p("med_in", T("Incidence medium"), "select", "air", group=G_MED, options=MEDIA,
       help=T("The medium the light comes from. A glass here is the inside of a glass block.")),
    _p("n0", T("Model medium of incidence: n₀"), "float", 1.0, group=G_MED, min=1.0, max=4.0,
       show_if={"med_in": ["model"]}, help=T("A constant index, the same for every λ: a model, not a material.")),
    _p("med_out", T("Exit medium (substrate)"), "select", "schott_n_bk7", group=G_MED, options=MEDIA,
       help=T("The medium behind the structure. In the mode “total internal reflection”: the rarer medium beyond "
              "the prism's face (and the medium of the gap, if a second prism stands behind it).")),
    _p("ns", T("Model exit medium: n_s"), "float", 1.5, group=G_MED, min=1.0, max=4.0,
       show_if={"med_out": ["model"]}, help=T("A constant index, the same for every λ: a model, not a material.")),
    _p("block_mm", T("Glass blocks: radius of the half-cylinders, mm (0: half-spaces)"), "float", BLOCK_MM,
       group=G_MED, min=0.0, max=200.0,
       help=T("Every medium other than air is a half-cylinder (a D-shaped block) on the rotary table, its flat face "
              "the "
              "structure's and its axis the table's: a beam crosses it along a radius, meets its curved face at normal "
              "incidence (Fresnel: about 4 % reflected back) and is absorbed along the radius by the glass (its κ). 0: "
              "the media are half-spaces and the detectors stand inside them, an idealisation.")),
    # structure
    _p("structure", T("Structure"), "select", "interface", group=G_STR, options=STRUCTS,
       help=T("Every structure is computed by one and the same function of the engine: transfer matrices (lfphys "
              "interfaces.stack).")),
    _p("lam0_nm", T("Design wavelength λ₀, nm"), "float", 550.0, group=G_STR, min=300.0, max=1600.0,
       show_if=SHOW("ar", "bragg"), help=T("Every layer is λ₀/(4n(λ₀)) thick, with its material's own index at λ₀.")),
    _p("ar_mat", T("Film material"), "select", "mgf2_film_rodriguez", group=G_STR, show_if=SHOW("ar"),
       options=[("mgf2_film_rodriguez", MATERIAL_NAME["mgf2_film_rodriguez"]),
                ("mgf2_dodge_o", MATERIAL_NAME["mgf2_dodge_o"]), ("model", T("model film, index n_f"))]),
    _p("ar_n", T("Model film index n_f"), "float", 1.38, group=G_STR, min=1.0, max=4.0,
       show_if={"structure": ["ar"], "ar_mat": ["model"]}),
    _p("bragg_mat", T("Layer materials"), "select", "ta2o5_sio2", group=G_STR, show_if=SHOW("bragg"),
       options=[("ta2o5_sio2", T("Ta₂O₅ (H) and SiO₂ (L) films (Gao et al.)")),
                ("model", T("model layers, indices n_H and n_L"))]),
    _p("nH", T("Model high index n_H"), "float", 2.3, group=G_STR, min=1.0, max=4.0,
       show_if={"structure": ["bragg"], "bragg_mat": ["model"]}),
    _p("nL", T("Model low index n_L"), "float", 1.45, group=G_STR, min=1.0, max=4.0,
       show_if={"structure": ["bragg"], "bragg_mat": ["model"]}),
    _p("pairs", T("Number of pairs N (layers H, L)"), "int", 8, group=G_STR, min=1, max=30, show_if=SHOW("bragg")),
    _p("fp_mat", T("Film material"), "select", "model", group=G_STR, show_if=SHOW("fp"),
       options=[("model", T("model film, index n")), ("sio2_malitson", MATERIAL_NAME["sio2_malitson"]),
                ("schott_n_bk7", MATERIAL_NAME["schott_n_bk7"]), ("ta2o5_film_gao", MATERIAL_NAME["ta2o5_film_gao"])]),
    _p("fp_n", T("Film index"), "float", 2.3, group=G_STR, min=1.0, max=4.0,
       show_if={"structure": ["fp"], "fp_mat": ["model"]}),
    _p("fp_d_nm", T("Film thickness, nm"), "float", 2000.0, group=G_STR, min=1.0, max=20000.0, log=True,
       show_if=SHOW("fp")),
    _p("metal_mat", T("Metal"), "select", "au_johnson_christy", group=G_STR, show_if=SHOW("metal"),
       options=[("au_johnson_christy", MATERIAL_NAME["au_johnson_christy"]),
                ("ag_johnson_christy", MATERIAL_NAME["ag_johnson_christy"]), ("al_rakic", MATERIAL_NAME["al_rakic"]),
                ("model", T("model metal, index n + iκ"))]),
    _p("metal_n", T("Metal: n (the real part of the index)"), "float", 0.2, group=G_STR, min=0.01, max=5.0,
       show_if={"structure": ["metal"], "metal_mat": ["model"]}),
    _p("metal_k", T("Metal: κ (the imaginary part, extinction)"), "float", 3.3, group=G_STR, min=0.0, max=20.0,
       show_if={"structure": ["metal"], "metal_mat": ["model"]}),
    _p("metal_d_nm", T("Metal thickness, nm"), "float", 30.0, group=G_STR, min=0.1, max=500.0, log=True,
       show_if=SHOW("metal")),
    _p("tir_gap_nm", T("Gap to a second prism, nm (0: no prism)"), "float", 0.0, group=G_STR, min=0.0,
       max=5000.0, show_if=SHOW("tir"),
       help=T("A second prism of the same glass behind a gap of the exit medium: frustrated total reflection, the "
              "light tunnels through the gap.")),
    # devices: the analysers and the detectors (a device, not modified physics: design §3.5)
    _p("anaR", T("Analyser before the reflection detector"), "select", "out", group=G_DEV, options=_ANA_OPTIONS,
       help=T("A rotatable polarising beam splitter with a detector on each port; its angle α is in the reflected "
              "beam's own frame (p in the plane of incidence).")),
    _p("anaR_deg", T("Reflection analyser's angle α, °"), "float", 0.0, group=G_DEV, min=-180.0, max=180.0,
       show_if={"anaR": ["ideal", "real"]}),
    _p("anaT", T("Analyser before the transmission detector"), "select", "out", group=G_DEV, options=_ANA_OPTIONS,
       help=T("A rotatable polarising beam splitter with a detector on each port; its angle α is in the transmitted "
              "beam's own frame (p in the plane of incidence).")),
    _p("anaT_deg", T("Transmission analyser's angle α, °"), "float", 0.0, group=G_DEV, min=-180.0, max=180.0,
       show_if={"anaT": ["ideal", "real"]}),
    _p("ana_k1", T("Imperfect analyser: k₁ (along its axis)"), "float", IMPERFECT[0], group=G_DEV, min=0.0, max=1.0,
       help=T("The principal transmittances of a linear partial polariser: the pass port takes k₁ of the light "
              "along the axis and k₂ across it; the reject port the rest (1 − k₁, 1 − k₂).")),
    _p("ana_k2", T("Imperfect analyser: k₂ (across its axis)"), "float", IMPERFECT[1], group=G_DEV, min=0.0, max=1.0),
    _p("det", T("Detectors"), "select", DET_DEFAULT, group=G_DEV, options=DETECTORS,
       help=T("Every detector of the bench is this device: its efficiency, dark counts, dead time and timing jitter "
              "(lfphys photodetector, the values from the manufacturer's data sheet).")),
    _p("gate_s", T("Counting time (gate), s; 0: counting all the time"), "float", 0.0, group=G_DEV, min=0.0,
       max=1000.0, help=T("The counters count the clicks from the start until this time and then stop.")),
    _p("ref_s", T("Reference count with the block removed: its counting time t₀, s (0: none)"), "float", 0.0,
       group=G_DEV, min=0.0, max=10.0,
       help=T("Before the count the block is lifted off the table and the transmission detector, in line with the "
              "source, counts the incident photons for t₀: the reference N₀ (in the laboratory manuals, the power I₀ "
              "measured before the sample is placed). The world counts it when it starts; a later change of the "
              "source or the detectors makes it void.")),
], presets={})

# --- presets: real materials (design §3.9); a model medium only where it says so --------------------------------------
_BENCH = {"rate": BENCH_RATE, "det": DET_DEFAULT, "lam_nm": HENE}
SCHEMA.presets.update({
    "brewster": {"label": T("N-BK7 glass at Brewster's angle from air (unpolarised light: only s is reflected)"),
                 "params": {**_BENCH, "structure": "interface", "med_in": "air", "med_out": "schott_n_bk7",
                            "theta_deg": 56.574, "pol": "unpol"}},
    "brewster_analyser": {"label": T("N-BK7 at Brewster's angle with an analyser along p before the reflection "
                                     "detector"),
                          "params": {**_BENCH, "structure": "interface", "med_in": "air", "med_out": "schott_n_bk7",
                                     "theta_deg": 56.574, "pol": "unpol", "anaR": "ideal", "anaR_deg": 0.0}},
    "tir": {"label": T("Total internal reflection: N-BK7 → air at {th}°, beyond the critical angle", th=60),
            "params": {**_BENCH, "structure": "tir", "med_in": "schott_n_bk7", "med_out": "air", "theta_deg": 60.0,
                       "pol": "unpol", "tir_gap_nm": 0.0}},
    "ftir": {"label": T("Frustrated total reflection: a {gap} nm air gap to a second N-BK7 prism (photon tunnelling)",
                        gap=200),
             "params": {**_BENCH, "structure": "tir", "med_in": "schott_n_bk7", "med_out": "air", "theta_deg": 45.0,
                        "pol": "s", "tir_gap_nm": 200.0}},
    "ar_mgf2": {"label": T("Anti-reflection of N-BK7 by a λ/4 MgF₂ film (λ₀ = {lam0} nm)", lam0=550),
                "params": {**_BENCH, "structure": "ar", "med_in": "air", "med_out": "schott_n_bk7",
                           "ar_mat": "mgf2_film_rodriguez", "lam0_nm": 550.0, "lam_nm": 550.0, "theta_deg": 0.0,
                           "pol": "s"}},
    "ar_mgf2_bulk": {"label": T("Anti-reflection of N-BK7 by λ/4 of crystalline MgF₂ (λ₀ = {lam0} nm)", lam0=550),
                     "params": {**_BENCH, "structure": "ar", "med_in": "air", "med_out": "schott_n_bk7",
                                "ar_mat": "mgf2_dodge_o", "lam0_nm": 550.0, "lam_nm": 550.0, "theta_deg": 0.0,
                                "pol": "s"}},
    "bragg": {"label": T("Bragg mirror (H L)×{N:d} of Ta₂O₅ and SiO₂ films on N-BK7, λ₀ = {lam0} nm", N=8, lam0=550),
              "params": {**_BENCH, "structure": "bragg", "med_in": "air", "med_out": "schott_n_bk7",
                         "bragg_mat": "ta2o5_sio2", "pairs": 8, "lam0_nm": 550.0, "lam_nm": 550.0, "theta_deg": 0.0,
                         "pol": "s"}},
    "fp": {"label": T("Fabry–Pérot: a model film n = {n}, {d} µm thick, in air", n=2.3, d=2),
           "params": {**_BENCH, "structure": "fp", "med_in": "air", "med_out": "air", "fp_mat": "model", "fp_n": 2.3,
                      "fp_d_nm": 2000.0, "theta_deg": 0.0, "pol": "s"}},
    "metal": {"label": T("A gold film of {d} nm on N-BK7", d=30),
              "params": {**_BENCH, "structure": "metal", "med_in": "air", "med_out": "schott_n_bk7",
                         "metal_mat": "au_johnson_christy", "metal_d_nm": 30.0, "theta_deg": 0.0, "pol": "unpol"}},
    "spr": {"label": T("Surface plasmon resonance (Kretschmann): N-BK7 prism, {d} nm of gold, air, p light", d=50),
            "params": {**_BENCH, "structure": "metal", "med_in": "schott_n_bk7", "med_out": "air",
                       "metal_mat": "au_johnson_christy", "metal_d_nm": 50.0, "theta_deg": 43.773, "pol": "p"}},
    "malus": {"label": T("Malus's law: linear light at ψ = {psi}° straight into an analyser", psi=30),
              "params": {**_BENCH, "structure": "none", "med_in": "air", "med_out": "air", "theta_deg": 0.0,
                         "pol": "lin", "psi_deg": 30.0, "anaT": "ideal", "anaT_deg": 0.0}},
    # the screens' set-ups (design §3)
    "story": {"label": T("One photon at a time at N-BK7 glass: the Watch story"),
              "params": {**_BENCH, "structure": "interface", "med_in": "air", "med_out": "schott_n_bk7",
                         "theta_deg": 30.0, "pol": "unpol"}},
    "boundary": {"label": T("The reflection bench: one boundary of a SCHOTT glass at the He-Ne line"),
                 "params": {**_BENCH, "structure": "interface", "med_in": "air", "med_out": "schott_n_bk7",
                            "theta_deg": 30.0, "pol": "s", "ref_s": 0.1}},
    "coatings": {"label": T("Real coatings on N-BK7 at normal incidence"),
                 "params": {**_BENCH, "structure": "interface", "med_in": "air", "med_out": "schott_n_bk7",
                            "theta_deg": 0.0, "pol": "unpol", "lam0_nm": 550.0}},
    "polarisation": {"label": T("Total internal reflection in N-BK7 with an analyser: the phase of s and p"),
                     "params": {**_BENCH, "structure": "interface", "med_in": "schott_n_bk7", "med_out": "air",
                                "theta_deg": 51.0, "pol": "lin", "psi_deg": 45.0, "anaR": "ideal", "anaR_deg": 0.0}},
    "lab_dark": {"label": T("The bench with the shutter closed: dark counts"),
                 "params": {**_BENCH, "structure": "interface", "med_in": "air", "med_out": "schott_n_bk7",
                            "theta_deg": 30.0, "pol": "s", "shutter": "closed", "gate_s": 0.5}},
    "lab_malus": {"label": T("Malus's law on the bench: linear light straight into an analyser"),
                  "params": {**_BENCH, "structure": "none", "med_in": "air", "med_out": "air", "theta_deg": 0.0,
                             "pol": "lin", "psi_deg": 30.0, "anaT": "ideal", "anaT_deg": 0.0}},
    "lab_reflection": {"label": T("Polarisation by reflection: unpolarised light, an analyser before the reflection "
                                  "detector"),
                       "params": {**_BENCH, "structure": "interface", "med_in": "air", "med_out": "schott_n_bk7",
                                  "theta_deg": 56.0, "pol": "unpol", "anaR": "ideal", "anaR_deg": 0.0}},
})

