# lfphys layers: what goes into the core and what stays outside

Owner, 2026-10-23 (verbatim): «выделяй в отдельную библиотеку движок для физики, чтобы на его основе можно было строить
подобные симуляции и визуализации. а отдельная симуляции или визуализации должна быть оберткой над этим движком.
движок должен иметь очень точную физическую модель. в ядре/core движка должно быть то, что точно доказано и
подтвержено, разные теории, которые по разному интерпретируют мир и которые повсеместно используются физиками, но
между собой могут иметь несоответствия должны быть тоже в движке, но за пределами ядра. дополни ядро и движок
дополнительными физическими механиками.»

## 1. Layers

| layer | package | admission |
|---|---|---|
| core | `lfphys.core` | (a) the law belongs to accepted physics and no experiment contradicts it in its stated domain; (b) the code computes the law or an exact consequence of it, with a stated and tested numerical error; (c) every function is tested against a closed form or an independent second method; (d) the sources are named |
| theories | `lfphys.theories` | a theory physicists use widely, which disagrees with the core or with another theory somewhere: `approx` (controlled approximations of a law the core has in fuller form: Newtonian gravity of slow bodies, paraxial and ray optics, weak-field expansions), `interpretations` (the same predictions read differently: Copenhagen, de Broglie–Bohm, Everett), `models` (phenomenology with fitted parameters: the Cornell potential), `alternatives` (modified or refuted laws for declared "what if" studies: ether, emission theory, light as Newtonian corpuscles, GRW, a modified Born rule, local hidden variables) |
| laws | `lfphys.laws` | law sets: which core laws and which theories a world uses, validated together; a world whose set differs from accepted physics is flagged "modified physics" |
| tools | `lfphys.tools` | not physics: statistics of simulated data |

**Where the core ends (made explicit after the review of 2026-10-23, E9).** Every law in physics is the limit of
a fuller theory somewhere; the line is drawn by what the engine itself contains:

* **core**: the most complete form of a law the engine has, with its domain and its error against the fuller
  theory stated in `validity` (and, where measured, a number). The non-relativistic Schrödinger equation is in the
  core because the engine has no quantum field theory; its validity says "non-relativistic". The Dirac levels say
  what QED adds (the Lamb shift, 3e-6 of the 1S–2S frequency) and are tested against the measurement. A core module
  whose law the engine also has in fuller form for special cases names those cases in `conflicts` (e.g.
  `core.gravity.nbody`: the most complete N-body gravity for N ≥ 3; for two bodies `pn_binary`, for a test body about
  one mass `kerr_newman`; review B6-gravity G14).
* **theories/approx**: a simplified form of a law the engine *also* has in fuller form, kept for comparison or
  speed, so the two can be put side by side in a world: Newtonian gravity of slow bodies against the exact
  Schwarzschild orbits, paraxial against Rayleigh–Sommerfeld diffraction, ray against wave optics, PPN against the
  exact metric.
* **theories/alternatives**: a law with no domain where it agrees with experiment (refuted) or one changed on
  purpose: ether and emission kinematics, light as Newtonian corpuscles (half the measured deflection at every
  impact parameter), GRW, a modified Born rule, local hidden variables.

Numbers enter the core only with their source: CODATA through `scipy.constants`, IAU resolutions, PDG averages and
measured spectra in `lfphys.core.data` with the edition and the page they were checked against.

## 2. Rules (checked by `tests/test_layers.py`)

1. Every module declares `ABOUT = {layer, kind, title, statement, validity, basis, conflicts}`; `layer` equals the
   package it lives in. The fields a user reads (`title`, `statement`, `validity`, `conflicts` and the descriptive
   entries of `basis`) are translatable texts, `lfphys.i18n.T("English text")`; their translations are in
   `lfphys/locales/<lang>.json` for every language of `../LANGUAGES.md` (`../visualizations/RULES.md` §7). Citations
   in `basis` (authors, journal, year) stay plain strings.
2. The core imports nothing from `theories`, `laws` or `tools`. Theories may import the core. A law set may import
   both.
3. A module in `theories` names at least one conflict: where it disagrees with the core or with another theory (that
   is why it is outside the core).
4. An interpretation adds no prediction for the outcomes it shares with the core (tested where computable, e.g. Bohmian
   positions distributed by |ψ|²). An alternative changes predictions and says which experiments bound it.
5. A visualization is a wrapper: its physics comes from the engine; its own code is orchestration (time line,
   events, apparatus logic) and drawing. It lists the engine modules a world uses (`engine_modules()`), and the
   player shows them with their layer.

## 3. What is where (current)

The catalogue is generated: `python -c "from lfphys import registry; ..."` or the player's panel "Physics of this
world". `README.md` lists the modules by topic.

**Added for EX2 (2026-11-18; design `sources/explore_EX2_2026-11-18_design.md` §3.5, §3.9, §4.7, §10, §11), by layer:**

| module | layer, kind | what it adds | why in this layer |
|---|---|---|---|
| `core.optics.polarization` (new) | core, law | Jones vectors and matrices, density matrices, Stokes parameters and Mueller matrices; a polariser and a polarising beam splitter with the principal transmittances k₁, k₂ (Malus's law); the reflection and transmission matrices of a planar structure from its Fresnel coefficients (TIR's elliptical light); the degree of polarisation, the ellipse; the Born probabilities of a photon's five outcomes | the exact classical optics of plane waves in linear media, and the same two-dimensional Hilbert space for one photon; validity: plane monochromatic waves, isotropic planar structures, an analyser without retardance |
| `core.optics.materials` (new) | core, data | the complex index n + iκ and dn/dλ of eleven real, dispersive materials (SCHOTT N-BK7, N-F2, N-SF11; MgF₂ and fused silica by Sellmeier; MgF₂, SiO₂ and Ta₂O₅ films; gold, silver, aluminium by a shape-preserving cubic), each a `core.data` DATASETS entry with its range, temperature, source and check (`sources/materials_2026-11-18.md`); a coded refusal outside a range | measured data with their sources, as §1 admits numbers into the core |
| `core.optics.interfaces` (extended) | core, law | the fields of p light and of any Jones state or density matrix; the power factors; `group_delay`: the group delays of r and t with the materials' dispersion | the same transfer matrices, differentiated exactly |
| `core.optics.thin_films` (extended) | core, law | `joule_absorption_p`: the Joule balance for p light | as for s |
| `core.quantum.qubits` (extended) | core, law | real stations as POVMs (an analyser with one or two threshold detectors, efficiency η, a dark-click probability per trial); Eberhard's states and Werner mixtures | the Born rule with a stated detector model; η = 1 without dark clicks gives the projectors |
| `core.gravity.orbit_stream` (extended) | core, law | `OrbitStream.interior`, `proper_time_to_centre`, `cycloid_proper_time`: the body's proper time past the stop at the horizon on to r = 0 | an exact consequence of the Schwarzschild geodesics (a quadrature) |
| `core.mechanics.particle` (extended) | core, law | `Medium`: a body in a fluid, with the buoyancy (exact) and the added mass C_A ρ_f V (C_A = ½ of a sphere in potential flow, stated) | buoyancy is exact; the added mass's coefficient is stated with its checked range |
| `core.mechanics.drag` (extended) | core, law | `basset_integral`, `history_bound`: Basset's history kernel along a flight by product integration, an upper bound where no history law is established | Basset's creeping-flow kernel is the law; at higher Reynolds numbers it is used only as a bound, said so |
| `core.mechanics.earth_frame` (new) | core, law | the WGS 84 normal gravity at a latitude and height; the Coriolis force −2mΩ × v as a declared force (in a vertical plane its part in the plane), the sideways offset of a planar flight to first order; the eastward drift of a dropped body as a reference | a model Earth of a standard (NIMA TR8350.2), its domain stated |
| `theories.models.photodetector` (new) | theories, model | a single-photon detector in time: efficiency, Poisson dark counts, a non-paralysable dead time, Gaussian jitter; the observed rate, the accidental coincidences, the window's share of true coincidences, locally defined time slots, a time-stream Monte Carlo; `DEVICES` from the Excelitas SPCM-AQRH and SPCM-NIR data sheets | a device model with measured parameters; its conflicts: afterpulsing, twilight events, a rate-dependent efficiency and non-Gaussian jitter tails not modelled |
| `theories.models.magnus` (new) | theories, model | the lift of a spinning smooth sphere and its spin's drag from the measurements of Zhou, Zhang & Xu (2022), with a stated band beyond their Re 3 472 (one simulated value at Re 10⁴, Muto et al. 2012) | a measured correlation, not a law (no closed form at these Reynolds numbers; the inverse Magnus effect not described) |
| `theories.models.drag_quadratic` (extended) | theories, model | `angle_flight`: the flight's equations in its velocity's angle with C_d(Re), buoyancy, added mass, a normal (Magnus, Coriolis) force: the second method for S03's flights | the second method beside the core's integration in time |
| `theories.alternatives.local_hidden` (extended) | theories, alternative | Gisin and Gisin's local model that exploits the detection loophole (75 % detection on average; CHSH 2√2 under fair sampling, CH ≤ 0) | refuted by the loophole-free tests; flagged «modified physics» in a world |
| `tools.bell_stats` (extended) | tools | CH and Eberhard's J with their multinomial errors (no fair sampling), CHSH with the accidentals subtracted, the slot probabilities with multi-pair emission and dark clicks, the efficiency thresholds (2/(1 + √2) for the maximally entangled state, → 2/3), `best_j` | statistics of simulated or measured counts, not physics |

## 4. Licence and third-party code (owner, 2026-10-24; `../AGENTS.md` §3 rule 8)

The engine is licensed by its author (the lfphys Research Licence 1.0, text of 14 November 2026, for code —
noncommercial research only, citation required, public use carries the line `lfphys — Ildar Idrisov —
https://github.com/ildar-idrisov/lfphys`, the name not licensed; CC BY-NC-SA 4.0 for documentation and the public
site's materials; commercial use only by a separate agreement: `LICENSE.md`, `NOTICE`, `COMMERCIAL.md`). To keep it free to be licensed under any
terms, it contains only its own code and permissively licensed code; runtime dependencies are permissive or weak
copyleft used unmodified; third-party physics libraries (CRunDec, KerrGeoPy, tmm, QuTiP, miepython, ...) are used only in
tests that compare the engine's results with theirs, as independent references (`CONTRIBUTING.md`); copyleft ones
(e.g. Meep) only in one-off runs kept outside the repository, of which a dated record of the results is kept
(`../AGENTS.md` §3 rule 8).
