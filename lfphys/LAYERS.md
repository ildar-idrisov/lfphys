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

## 4. Licence and third-party code (owner, 2026-10-24; `../AGENTS.md` §3 rule 8)

The engine is licensed by its author (the lfphys Research Licence 1.0 for code — noncommercial research only, citation
required; CC BY-NC-SA 4.0 for documentation; commercial use only by a separate agreement: `LICENSE.md`, `NOTICE`,
`COMMERCIAL.md`). To keep it free to be licensed under any
terms, it contains only its own code and permissively licensed code; runtime dependencies are permissive or weak
copyleft used unmodified; third-party physics libraries (CRunDec, KerrGeoPy, tmm, QuTiP, miepython, ...) are used only in
tests that compare the engine's results with theirs, as independent references (`CONTRIBUTING.md`); copyleft ones
(e.g. Meep) only in one-off runs kept outside the repository, of which a dated record of the results is kept
(`../AGENTS.md` §3 rule 8).
