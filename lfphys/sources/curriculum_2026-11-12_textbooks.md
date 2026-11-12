# Physics curricula, textbooks and demo collections — research for the lfphys README

Date: 2026-11-12. Web research plus a reading of `engine/visualizations/README.md`, the `vNN_*`/`pNN_*` READMEs and
preset labels (`viz.py`), and `engine/lfphys/README.md`. No project file was edited.

How to read this file:
- §1 is the catalogue of texts and curricula with the verification status of each. The full tables of contents, with
  the URL each was verified from, are in Appendices A–D at the end. Those appendices are the four research parts,
  merged unchanged.
- §2 is the merged list of sections. §3 maps v01–v17 and p01–p04. §4 lists the gaps. §5 covers the demo collections.
  §6 gives recommendations for the README, and §7 the caveats.
- Status tags as the project uses them: [useful] / [neutral] / [weakens] / [error in earlier]. Here "[error in earlier]"
  marks a correction to an assumption in the brief.

---

## 0. Corrections to the brief (found while verifying)

| # | Brief assumed | Verified fact | Status |
|---|---|---|---|
| 1 | OpenStax books are CC BY 4.0 | Only the high-school **"Physics"** is CC BY 4.0. **College Physics 2e**, **College Physics for AP Courses 2e** and **University Physics Vols 1–3** are **CC BY-NC-SA 4.0**, per openstax.org metadata and the UP preface | [error in earlier] |
| 2 | Перышкин 7–9 = А. В. Перышкин | The current Федеральный перечень учебников (приказ № 436 of 22.06.2026) lists **И. М. Перышкин, А. И. Иванов** (9 кл.: + Е. М. Гутник и др.), Просвещение. The classic А. В. Перышкин books are no longer on the list | [error in earlier] |
| 3 | Касьянов is a general 10–11 text | In the current ФПУ, Касьянов is listed only for **углублённое обучение**; the basic line is Мякишев et al. | [neutral] |
| 4 | Berkeley Physics Course is openly available | Legal status **unclear; treat as not open**. The 1965 royalty-free promise is reported as unobtainable, and the archive.org copies are lending scans or have no rights statement | [weakens] |
| 5 | Feynman Lectures online = open | **Free to read, not openly licensed**: copying and downloading are prohibited (Caltech DMCA notice 2022) | [neutral] |
| 6 | PhET is CC BY 4.0 | Sims published **before 2026-03-29** are CC BY 4.0. Current HTML5 sim metadata says **CC BY-NC 4.0**, and the sim source is no longer public (monorepo) | [error in earlier] |
| 7 | Blanchet's Living Review 2014 | Superseded by **Blanchet, Living Rev. Relativ. 27, 4 (2024)**, CC BY 4.0, arXiv:1310.1528 | [neutral] |
| 8 | «Time in Quantum Mechanics» edited by Muga, Sala Mayato, Egusquiza | That is vol. 1 (2008). **Vol. 2 (2009)** is edited by Muga, Ruschhaupt and del Campo | [neutral] |
| 9 | — | **Taylor & Wheeler "Spacetime Physics" (2nd ed.)** and **Taylor–Wheeler–Bertschinger "Exploring Black Holes" 2e** are **CC BY 4.0** (eftaylor.com), the most permissive texts found | [useful] |

---

## 1. Textbooks and curricula (catalogue; full contents in the appendices)

The "TOC" column says how much of the table of contents was verified from a fetched page: **full** (all chapters),
**parts** (main sections only), **edition only**, or **proxy** (the official programme stands in for the book).

### 1.1 School level

| Text / curriculum | Edition verified | Level | Open (legal URL, licence) | TOC | App. |
|---|---|---|---|---|---|
| OpenStax, *Physics* (Urone, Hinrichs; TEA) | 1st, 2020 (rev. 2026) | US high school | **yes**, https://openstax.org/details/books/physics, CC BY 4.0 | full (23 ch.) | A §1a |
| OpenStax, *College Physics 2e* | 2nd, 2022 | intro college, algebra | **yes**, https://openstax.org/details/books/college-physics-2e, CC BY-NC-SA 4.0 | full (34) | A §1b |
| OpenStax, *College Physics for AP Courses 2e* | 2nd, 2022 | AP Physics 1–2 | **yes**, https://openstax.org/details/books/college-physics-ap-courses-2e, CC BY-NC-SA 4.0 | full (34) | A §1c |
| P. G. Hewitt, *Conceptual Physics* | 13th, Pearson ©2022 | conceptual intro | no | full (36 ch., 8 parts) | A §2 |
| D. C. Giancoli, *Physics: Principles with Applications* | 7th, Pearson (no 8th exists) | algebra intro / AP | no | full (33) | A §3 |
| И. М. Перышкин, А. И. Иванов «Физика» 7, 8, 9 (current ФПУ line) | 6-е изд., Просвещение 2026 | ООО 7–9 | no | proxy (= ФРП ООО) | A §4a |
| А. В. Перышкин (9: + Е. М. Гутник) «Физика» 7–9 (classic) | Дрофа 2019; Экзамен 2022–25 | ООО 7–9 | no | parts (главы) | A §4b |
| Г. Я. Мякишев, Б. Б. Буховцев, Н. Н. Сотский «Физика. 10»; Мякишев, Буховцев, В. М. Чаругин «Физика. 11» | 13-е / 14-е изд., Просвещение 2026 | СОО 10–11 (basic line in ФПУ) | no | edition only | A §5 |
| В. А. Касьянов «Физика. 10», «Физика. 11» | углубл. 2025–26; базовый 2022 | СОО 10–11 | no | parts | A §6 |
| Г. С. Ландсберг (ред.) «Элементарный учебник физики», 3 т. | Физматлит 2025–26 | upper secondary / entrance | no | full for vols 1–2, parts for vol. 3 | A §7 |
| ФГОС ООО (приказ № 287) / ФГОС СОО (№ 413 в ред. № 732) | current versions confirmed | — | yes (official) | outcomes only, not read (scans) | A §8 |
| ФРП «Физика» ООО 7–9, базовый and углублённый | edsoo.ru, 2025 | 7–9 | yes, https://edsoo.ru/rabochie-programmy/ | full (sections + hours) | A §8a–b |
| ФРП «Физика» СОО 10–11, базовый and углублённый | edsoo.ru, 2025 | 10–11 | yes | full | A §8c–d |
| IB DP Physics (first assessment 2025) | subject brief, ©IBO 2022 | 16–19, SL/HL | brief public; full guide not | full (themes A–E, topics) | A §9a |
| AP Physics 1, 2, C: Mechanics, C: E&M (2024–25 framework) | College Board 2026 pages | US HS, college level | yes (course pages) | full (units + weights) | A §9b |
| AQA A-level Physics 7408 | spec, first teaching 2015 | England 16–18 | yes | full (3.1–3.13) | A §9c |

### 1.2 University level (international)

| Text | Edition verified | Level | Open | TOC | App. |
|---|---|---|---|---|---|
| Halliday, Resnick, Walker, *Fundamentals of Physics* | 12th (Extended, 44 ch.), Wiley ©2021 | intro, calculus | no | full (from bookstores; Wiley page 403) | B §1 |
| Young & Freedman, *University Physics with Modern Physics* | 16th, Pearson 2026 (©2027) | intro, calculus | no | full (44 ch., 6 parts) | B §2 |
| OpenStax, *University Physics* Vols 1–3 (Ling, Sanny, Moebs) | 1st, 2016 (rev. 2026) | intro, calculus | **yes**, https://openstax.org/details/books/university-physics-volume-1 (‑2, ‑3), CC BY-NC-SA 4.0 | full | B §3 |
| Feynman, Leighton, Sands, *The Feynman Lectures on Physics* I–III | online ed. 2013 | intro (demanding) | free to read at https://www.feynmanlectures.caltech.edu/; not open | full, but **from Wikipedia** (site blocked this client) | B §4 |
| Berkeley Physics Course 1–5 (Kittel–Knight–Ruderman; Purcell, now Purcell & Morin 3rd, CUP 2013; Crawford; Wichmann; Reif) | 1965–71; Purcell & Morin 2013 | honours intro | unclear, treat as no | full only for Purcell & Morin | B §5 |
| B. Crowell, *Light and Matter* | rev. 2020 | intro | **yes**, https://www.lightandmatter.com/lm/, CC BY-SA 3.0 (own photos only) | full | B "Open alternatives" |
| Taylor & Wheeler, *Spacetime Physics* 2nd | Freeman 1992 | intro SR | **yes**, https://www.eftaylor.com/spacetimephysics/, CC BY 4.0 | full | B §S3a |
| Taylor, Wheeler, Bertschinger, *Exploring Black Holes* 2e | online only | intro GR | **yes**, https://www.eftaylor.com/exploringblackholes/, CC BY 4.0 | full | B §S3b |
| MIT OCW 8.01SC, 8.02, 8.03SC, 8.04, 8.044 | 2013–2019 runs | intro / upper | **yes**, ocw.mit.edu, CC BY-NC-SA 4.0 | units | B "Open alternatives" |
| Griffiths, *Introduction to Electrodynamics* | 5th, CUP 2023 | upper UG | no | full | B §6 |
| Griffiths & Schroeter, *Introduction to Quantum Mechanics* | 3rd, CUP 2018 | upper UG | no | full | B §7 |
| Kittel, *Introduction to Solid State Physics* | 8th, Wiley 2004 | upper UG / grad | no | full (Wiley TOC PDF) | B §8 |
| Goldstein, Poole, Safko, *Classical Mechanics* | 3rd, Pearson ©2002 | grad | no | full | B §9 |
| Jackson, *Classical Electrodynamics* | 3rd, Wiley 1998/99 | grad | no | full (Wiley scans) | B §10 |
| Sakurai & Napolitano, *Modern Quantum Mechanics* | 3rd, CUP 2020 | grad | no | full | B §11 |
| Schroeder, *An Introduction to Thermal Physics* | OUP reissue 2021 | upper UG | no | full | B §S1 |
| Hecht, *Optics* | 5th, Pearson | upper UG | no | full | B §S2 |
| Hartle, *Gravity* | CUP reissue 2021 | upper UG GR | no | full | B §S3c |
| Krane, *Introductory Nuclear Physics*; Griffiths, *Introduction to Elementary Particles* 2nd rev. | Wiley 1988/91; Wiley-VCH 2008 | upper UG | no | full | B §S4 |
| Carroll & Ostlie, *An Introduction to Modern Astrophysics* | 2nd, CUP 2017 | upper UG | no | full | B §S5 |
| Kundu, Cohen, Dowling, Capecelatro, *Fluid Mechanics* | 7th, Elsevier 2024 | upper UG / grad | no | full | B §S6 |

### 1.3 University level (Russian)

| Text | Edition verified | Level | Open | TOC | App. |
|---|---|---|---|---|---|
| И. В. Савельев «Курс общей физики», 3 т. | Лань reprints 2023–26 (Наука 1977 orig.) | общий курс, втузы | no | full (all 3 vols) | C §1 |
| И. В. Савельев «Курс общей физики», 5 т. (Лань); 5 кн. (АСТ/Астрель) | Лань 2022–26 | same | no | full for vols 1–2; titles for 3–5 | C §1 |
| Д. В. Сивухин «Общий курс физики», 5 т. | Физматлит, current printings | physics faculties (МФТИ) | no | full (all 5) | C §2 |
| И. Е. Иродов «Задачи по общей физике» | Лань 22-е изд.; Лаборатория знаний 2021 | problems | no | parts 1–4 (from a solutions site); parts 5–6 snippet only | C §3a |
| И. Е. Иродов «… Основные законы» (Механика; Электромагнетизм; Волновые процессы; Квантовая физика; Физика макросистем) | Лаборатория знаний 2021 (Механика) | physics faculties | no | **not verified** | C §3b |
| Л. Д. Ландау, Е. М. Лифшиц «Теоретическая физика», 10 т. | Физматлит (I 2025, II 2016, III 2024, V 2021, VI 2020, VIII 2023) | senior UG / grad / research | no | full for I, II, III, VI, VIII; V in English only | C §4 |

### 1.4 Research-level references (2–4 per field; open ones marked)

Details, editions and verification URLs are in Appendix C, Part 2.
- **GR, black holes:** Misner–Thorne–Wheeler *Gravitation* (PUP 2017); Wald *General Relativity* (1984);
  Chandrasekhar *The Mathematical Theory of Black Holes* (OUP 1998); EHT Collaboration, ApJL 875, L1 (2019) — **open**.
- **Gravitational waves:** Maggiore *Gravitational Waves* vols 1–2 (OUP 2007, 2018); Blanchet, Living Rev. Relativ. 27, 4
  (2024) — **open**, CC BY 4.0.
- **SR, Thomas–Wigner rotation, visual appearance:** Gourgoulhon *Special Relativity in General Frames* (Springer 2013);
  Terrell, Phys. Rev. 116, 1041 (1959); Penrose, Proc. Camb. Phil. Soc. 55, 137 (1959); Thomas 1926; Wigner 1939.
- **Electrodynamics, optics:** Jackson (3rd ed.); Born & Wolf *Principles of Optics* (7th ed. 1999; reissued 2019);
  Bohren & Huffman (Wiley 1983/1998); Taflove & Hagness *FDTD* (3rd ed. 2005); Allen et al., PRA 45, 8185 (1992).
- **Quantum foundations:** Bell *Speakable and Unspeakable* (2nd ed. 2004); Muga et al. (eds.) *Time in QM* I (2008), II
  (2009); Breuer & Petruccione *Open Quantum Systems* (OUP 2002/2007); Nielsen & Chuang (2010).
- **Atomic:** Bethe & Salpeter (1957; Dover 2008); Foot *Atomic Physics* (OUP 2005).
- **QCD, particles:** Peskin & Schroeder (1995); Ellis, Stirling, Webber *QCD and Collider Physics* (CUP 1996); PDG
  *Review of Particle Physics* 2026 — **open**, https://pdg.lbl.gov/.
- **Statistical mechanics, MD:** Allen & Tildesley (2nd ed. 2017); Frenkel & Smit (3rd ed. 2023); Landau–Lifshitz V.
- **Fluids:** Landau–Lifshitz VI; Batchelor (CUP 1967/2000); Krüger et al. *The Lattice Boltzmann Method* (Springer 2017).
- **Cosmology:** Weinberg *Cosmology* (OUP 2008); Dodelson & Schmidt *Modern Cosmology* (2nd ed. 2020; 3rd ed.
  2024/25); Planck 2018 VI, A&A 641, A6 — **open**, arXiv:1807.06209.
- **Condensed matter:** Ashcroft & Mermin (1976).

---

## 2. Merged list of the main sections, in teaching order

Every source puts **mechanics first** and ends with the same tail: **quantum → atom → nucleus → particles →
astrophysics/cosmology**. The sources disagree on three placements:
- **Waves.** US texts put mechanical waves and sound right after mechanics. The Russian СОО course, Касьянов and
  Сивухин put one combined block, «Колебания и волны» (mechanical and electromagnetic, with AC), after electromagnetism.
- **Relativity.** OpenStax HS, IB and Савельев attach it to mechanics. Most texts put it between optics and quantum
  physics; Сивухин puts it inside optics.
- **Fluids.** US texts close mechanics with them. In Russia fluids are taught in grade 7, and Ландсберг and Сивухин
  treat them inside mechanics. IB 2025 and AQA have no fluids section.

The order below follows the mainstream sequence (HRW / Young & Freedman / OpenStax UP, which agree almost
chapter for chapter). The Russian ФРП and the general courses are cross-referenced for each section.

| # | Section | Typical subtopics: school → university intro → upper/graduate | Where it is taught (examples) |
|---|---|---|---|
| 0 | Measurement and method (cross-cutting) | units, estimation, uncertainty, scientific method | ФРП 7 «Физика и её роль…», 10 «методы научного познания»; AQA 3.1; HRW 1 |
| 1 | **Mechanics** | kinematics 1-D/2-D, projectile and circular motion; Newton's laws, friction, drag; work–energy, conservation of energy; momentum, collisions, centre of mass; rotation, torque, rolling, angular momentum; statics, elasticity; gravitation, Kepler orbits, satellites; non-inertial frames → Lagrange and Hamilton formalisms, central forces, rigid bodies, small oscillations, canonical transformations, chaos | ФРП 7 (descriptive), 9 «Механические явления», 10 «Механика»; AP1 U1–6, AP C:M; IB A.1–A.4; AQA 3.4, 3.6.1; HRW 1–13; Савельев т.1 ч.1; Сивухин I; Goldstein; ЛЛ I |
| 2 | **Fluids** | pressure, hydrostatics, Archimedes, buoyancy; continuity, Bernoulli; viscosity, Poiseuille → Navier–Stokes, vorticity, boundary layers, instability, turbulence, aerodynamics, compressible flow and shocks, CFD | ФРП 7 «Давление твёрдых тел, жидкостей и газов»; AP1 U8; HRW 14; Y&F 12; Ландсберг т.1 VII–IX; Сивухин I ch. XII; Kundu; ЛЛ VI |
| 3 | **Oscillations and waves** | SHM, pendulum, spring; damped and driven oscillations, resonance; coupled oscillators, normal modes; travelling waves, superposition, standing waves; sound, beats, Doppler; wave packets, dispersion; (RU: electromagnetic oscillations, AC and EM waves in the same block) | ФРП 9 «Механические колебания и волны», 11 «Колебания и волны»; AP1 U7, AP2 U14; IB C.1–C.5; AQA 3.3, 3.6.1; HRW 15–17; Feynman I-21…25, 47–51; Berkeley vol. 3 |
| 4 | **Thermal and molecular physics, thermodynamics** | temperature, heat, expansion, calorimetry; kinetic theory, gas laws, Maxwell distribution; first law, heat engines and refrigerators; second law, entropy; phase changes; transport (conduction, diffusion), Brownian motion → statistical mechanics (Boltzmann, Gibbs, quantum statistics), real gases, critical phenomena | ФРП 8 «Тепловые явления», 10 «Молекулярная физика и термодинамика»; AP2 U9; IB B.1–B.4; AQA 3.6.2; HRW 18–20; Савельев т.1 ч.2; Сивухин II; Schroeder; ЛЛ V |
| 5 | **Electricity and magnetism** | charge, Coulomb's law, field, field lines, Gauss's law, potential, conductors, capacitors, dielectrics; current, resistance, EMF, DC circuits; current in metals, electrolytes, gases, semiconductors; magnetic field, Lorentz force, motion of charges, fields of currents (Biot–Savart, Ampère); induction, inductance, AC circuits; Maxwell's equations, EM waves; magnetism of matter → boundary-value problems, multipoles, radiation, waveguides, relativistic electrodynamics | ФРП 8 «Электрические и магнитные явления», 9 «Электромагнитное поле…», 10–11 «Электродинамика»; AP2 U10–12, AP C:E&M; IB B.5, D.2–D.4; AQA 3.5, 3.7; HRW 21–33; Савельев т.2 ч.1; Сивухин III; Purcell; Griffiths; Jackson; ЛЛ II, VIII |
| 6 | **Optics** | propagation, reflection, refraction, total internal reflection; mirrors, lenses, image formation, instruments, prism dispersion; interference, thin films; diffraction, gratings; polarisation → Fresnel equations, coherence, Fourier optics, scattering (Rayleigh, Mie), crystal and metal optics, lasers, beams, nonlinear optics | ФРП 9 «Световые явления», 11 «Оптика»; AP2 U13–14; IB C.3; AQA 3.3.2; HRW 34–36; Савельев т.2 ч.3; Сивухин IV; Hecht; Born & Wolf |
| 7 | **Relativity** | postulates, invariance of c, simultaneity, time dilation, length contraction, Lorentz transformation, velocity addition, relativistic Doppler, energy and momentum, E = mc², spacetime diagrams → (GR) equivalence principle, gravitational redshift, light deflection, perihelion advance, GPS, black holes, gravitational waves, cosmological models | ФРП 11 «Основы СТО»; IB A.5 (HL); AQA 3.12 (option); AP: only E = mc² (AP2 U15); HRW 37; Савельев т.1 ch. VIII; Сивухин IV ch. IX; Spacetime Physics; Hartle; Exploring Black Holes; ЛЛ II |
| 8 | **Quantum physics** | blackbody radiation, photoelectric effect, Compton scattering, photons; de Broglie waves, electron diffraction, double slit; uncertainty; Schrödinger equation: wells, barriers, tunnelling, harmonic oscillator; spin, Stern–Gerlach → formalism, angular momentum, perturbation theory, scattering, identical particles, entanglement and Bell, open systems and decoherence, foundations | ФРП 11 «Квантовая физика» (кванты света, корпускулярно-волновой дуализм in углубл.); AP2 U15; IB E.2 (HL); AQA 3.2.2; HRW 38–39; Y&F 38–40; Савельев т.3 ч.1–2; Сивухин V ch. I–VII; Griffiths & Schroeter; Sakurai; Feynman III; ЛЛ III |
| 9 | **Atomic and molecular physics** | Rutherford scattering, Bohr model, line spectra (emission and absorption), energy levels, quantum numbers and orbitals, periodic table, X-rays, lasers → fine structure, Zeeman and Stark effects, multi-electron atoms, molecules | ФРП 9 «Квантовые явления», 11 «Строение атома»/«Физика атома»; IB E.1; AQA 3.2.2; HRW 40; Y&F 41; Сивухин V ch. II, VI; Foot; Bethe–Salpeter |
| 10 | **Condensed matter** (university; at school only "current in media", semiconductors) | crystal structure, X-ray diffraction, phonons, free electrons, energy bands, semiconductors, superconductivity, magnetism | ФРП 10 «Токи в различных средах»; AQA 3.13 (option); HRW 41; Y&F 42; Савельев т.3 ч.3; Kittel; Ashcroft–Mermin |
| 11 | **Nuclear physics** | composition of the nucleus, binding energy, radioactivity (α, β, γ), half-life, nuclear reactions, fission, fusion, chain reaction, detectors, dosimetry | ФРП 9 «Квантовые явления», 11 «Атомное ядро»; AP2 U15; IB E.3–E.5; AQA 3.8; HRW 42–43; Савельев т.3 ч.4; Сивухин V ch. VIII–XIV; Krane |
| 12 | **Particle physics** | elementary particles, quarks and leptons, interactions, conservation laws, accelerators → relativistic kinematics, Feynman diagrams, QED, QCD (running coupling, confinement, quarkonium), electroweak theory | ФРП 11 (элементарные частицы; углубл. «Физика атомного ядра и элементарных частиц»); AQA 3.2.1 (first section!); HRW 44; Сивухин V ch. XVI; Griffiths EP; Peskin–Schroeder; PDG |
| 13 | **Astrophysics and cosmology** | solar system, Kepler laws (shared with §1), stars (spectra, HR diagram, fusion, evolution), compact objects and black holes, galaxies; Hubble law, expansion, CMB, Big Bang, dark matter and dark energy | ФРП 11 «Элементы астрономии и астрофизики» (СОО; absent at ООО); classic А. В. Перышкин 9 «Строение и эволюция Вселенной»; IB E.5 (fusion and stars only); AQA 3.9 (option); Giancoli 33; HRW 44; Carroll & Ostlie; Weinberg; Dodelson–Schmidt |

Interdisciplinary and computational threads appear only at university and research level. Examples are numerical
methods (Kundu ch. 6 CFD, Allen & Tildesley, Taflove), nonlinear dynamics and chaos (Goldstein ch. 11), and statistical
methods. They suit a research group in the README, not a separate textbook section.

---

## 3. Mapping of the existing visualizations

Levels: **S** = school (ФРП/IB/AP/A-level scope), **U** = university, **R** = research, **P** = playground.
"S (enrichment)" means the topic is outside school curricula but one preset is accessible to upper-school students.
A range such as "S → U → R" means different presets serve different levels; the presets are named in the last column.

### 3.1 Demonstrations v01–v17

| Viz | Sections (primary; secondary) | Levels | Why (one line) | How presets/modes serve each level |
|---|---|---|---|---|
| **v01** Light travel | §7 Relativity (SR: invariance of c, simultaneity, clock synchronisation, Doppler; GR: deflection, Shapiro delay, gravitational redshift); §6 speed of light; §13 Sun–Earth, Andromeda | **S → U → R** | The 8 min 17 s Sun–Earth flight and "c is the same for every observer" are school SR (ФРП 11 «Основы СТО», OpenStax Physics ch. 10); simultaneity and lensing are university; the alternative-law worlds test the history of relativity | S: «Солнце → Земля», «Измерение c: покой, по ходу света, навстречу». U: «Парадокс Андромеды…», «Измерение c: часы по лабораторной одновременности», «Чёрная дыра 10 M☉: отклонение, тень, два изображения». R/history: «эфир», «баллистический свет», «Майкельсон–Морли, эфир», «Ньютоновы корпускулы» (modified physics) |
| **v02** Double slit | §8 Quantum (wave–particle duality, which-path information, eraser, decoherence, Aharonov–Bohm); §6 Optics (Young's interference, coherence, polarisation, vector diffraction) | **S → U → R** | Young's experiment with single photons is the textbook bridge from optics to quantum (ФРП 11 «Оптика» + «Квантовая физика»; AQA 3.3.2/3.2.2; IB C.3; HRW 35, 38) | S: «Фотоны 633 нм, две щели (Юнг, по одному фотону)». U: electrons, neutrons, C60, «детектор пути», «Квантовый ластик», «частичная когерентность», «Ааронова–Бома». R: «Векторная дифракция: щели 0.5 мкм в проводящем экране» (TE/TM), «Три щели: проверка правила Борна (Соркин)», GRW, P ∝ \|ψ\|^2.4, forced slit choice (modified) |
| **v03** Quantum 1-D | §8 Quantum (Schrödinger equation in 1-D: tunnelling, resonant tunnelling, step, well, harmonic oscillator); foundations | **U → R** | Exactly the standard 1-D problems of Griffiths & Schroeter ch. 2, HRW 39 and Y&F 40; tunnelling is in no school programme checked | U: «Туннелирование … барьер 1 эВ», «Резонансное туннелирование», «Ступенька», «Яма», «Толстый барьер», «Пакет в гармонической ловушке». R: the same run «глазами Бома» and «по Эверетту» (interpretations layer) |
| **v04** Orbits | §1 Mechanics (gravitation, Kepler orbits); §7 GR (perihelion advance, ISCO, plunge, proper time); §13 compact objects | **S (enrichment) → U → R** | The Newtonian ellipse is school gravitation; Mercury's 43″ per century is the classic GR test (Hartle ch. 10, Exploring Black Holes ch. 10); ISCO and Kerr are research-grade GR | S: «Ньютон: замкнутый эллипс (призрак — ОТО)». U: «Меркурий у Солнца (43″/век)», «Радиальное падение … (циклоида)». R: «Нейтронная звезда», «круговая орбита у ISCO», «Падение внутрь ISCO», Kerr; exact GR vs PPN |
| **v05** Optics bench | §6 Optics (reflection and refraction at interfaces, Fresnel coefficients, Brewster angle, total and frustrated TIR, thin films: AR coating, Bragg mirror, Fabry–Pérot; metal films and plasmons); §8 single photons | **S → U → R** | TIR and anti-reflection coatings are school optics (ФРП 9 «Световые явления», 11 «Оптика»; IB C.3); Fresnel and Brewster are university (Hecht ch. 4, 9; Сивухин IV ch. V) | S: «Полное внутреннее отражение…», «Просветление стекла слоем λ/4». U: «…под углом Брюстера», «Нарушенное полное отражение… (туннелирование фотонов)», «Фабри–Перо», ideal λ/4. R: «Металлическая плёнка 30 нм» (plasmon dip), multilayers by Abelès matrices |
| **v06** QCD | §12 Particle physics (strong interaction, running α_s, asymptotic freedom, quarkonium) | **U (upper) → R** | Needs QFT concepts (Griffiths *Elementary Particles* ch. 8, 10; Peskin–Schroeder); at school only "quarks exist" (AQA 3.2.1) | U: «Асимптотическая свобода и чармоний», «Боттомоний». R: «Только одна петля: насколько важны высшие порядки», «Что если α_s(M_Z) = 0,15» (modified) |
| **v07** Bell test | §8 Quantum (entanglement, polarisation and spin measurement, CHSH); §7 locality (space-like separation) | **U → R** | Bell/CHSH closes many QM courses (e.g. Sakurai ch. 3 "Theory of Angular Momentum", Griffiths & Schroeter ch. 12 "Afterword"; section placement from memory, chapter titles verified) and is a live research topic; it is in no school programme checked | U: «Фотоны \|Φ+⟩ … оптимальные углы CHSH», «Синглет спина ½…», «Кривая E(Δ)…». R: «локальные скрытые параметры» (photon and Bell sign models), «выбор за 5 мкс до прихода — лазейка локальности открыта» |
| **v08** Wave in 3-D | §6/§3 Waves and optics (diffraction by apertures: finite double slit, circular aperture with on-axis maxima and minima, Gaussian beam divergence, square aperture); computational optics | **U → R** (S possible for the double-slit preset) | Fresnel diffraction behind apertures (HRW 36; Hecht ch. 10). Its stated purpose is to show the engine's 3-D modelling and CPU/GPU choice | U: «Круглое отверстие: провалы и пики интенсивности на оси», «Гауссов пучок … расходимость», «Две щели конечной длины». R: «только срезы … упрощённой 2-D моделью (приближение)», «сетка 512: только срезы» (method accuracy, measured per world) |
| **v09** Thomas–Wigner 3-D | §7 Relativity (Lorentz group, non-commuting boosts, Thomas–Wigner rotation, SU(2) sign of spinors) | **U (advanced) → R** | Thomas precession is graduate SR/electrodynamics (Jackson ch. 11 "Special Theory of Relativity"; section placement from memory); holonomy and isoperimetric bounds are research | U: «Прецессия Томаса: равномерное движение по окружности», «Обычное пространство: траектория и гироскопы». R: «Три импульса: угол Вигнера = площадь треугольника скоростей», «Круг через покой: равенство в изопериметрической границе», «SU(2): … спинор сменил знак», non-planar loops (корона, винт, шов мяча) |
| **v10** Fast observer | §7 Relativity (aberration, Doppler colour, searchlight effect, Terrell–Penrose rotation); §6 black-body colour | **S (enrichment) → U → R** | "What you would see near c" is a strong visual for school SR (ФРП 11 «Основы СТО»); invisibility of Lorentz contraction is university (Terrell 1959, Penrose 1959; Feynman I-34) | S: «Полёт по улице при β = 0,9: аберрация, синий цвет впереди, яркость», «Сцена в покое (β = 0)». U: «Пролёт куба и шара … поворот Террелла», «мгновенный снимок (сокращение Лоренца, которого не видно)», «Поезд … мимо столбов». R: light-time ray tracing method, «Небо 4000 K … диполь» |
| **v11** Double slit in 2-D | §8 Quantum (Schrödinger diffraction at a real slit plate; single vs double slit; which-path marking; Aharonov–Bohm); foundations (Bohm) | **U → R** | Solves the full 2-D/3-D problem; shows where paraxial (textbook) theory fails | U: «Одна щель (B закрыта): огибающая без полос», «Щели a = 6λ … ближе к параксиальной теории», «Эффект Ааронова–Бома». R: «Узкие щели a = 2λ: … параксиальная теория не годится», «Частичная метка», «Наблюдатель у щели B: детектор пути…», Bohm trajectories |
| **v12** Arrival times | §8 Quantum foundations (time of arrival, probability current, backflow, detector models) | **R** (graduate U as a seminar) | QM does not define arrival time uniquely; this is research literature (Muga et al., *Time in QM*; Das & Struyve 2021) | All presets: «Один пакет: все правила почти совпадают», «Близко к источнику…: правила расходятся», «Цепочка из 4 пакетов…», «Обратный ток…», «Через две щели: совместное распределение…» |
| **v13** Hydrogen 3-D | §9 Atomic physics (orbitals, quantum numbers n, l, m, nodes, energy levels, radial distribution, probability current, superposition and Bohr frequency; He⁺, D, positronium) | **S (upper) → U → R** | Orbital shapes and energy levels are taught at school (ФРП 11 «Строение атома»; IB E.1; AQA 3.2.2; also school chemistry); real vs complex states and dynamics are university (Griffiths & Schroeter ch. 4; Y&F 41; Сивухин V) | S: «1s», «2p_z: гантель…», «3d_z²…». U: «2p_x вещественная: стоячая волна, тока нет», «2p, m = +1 комплексная: бублик и кольцевой ток», «1s + 2p_z: облако качается… (суперпозиция)», «2p_x + i·2p_y…». R: «n = 10, l = 3, m = 1…», «Ион He⁺, 3d_xy» |
| **v14** Quarkonium 3-D | §12 Particle physics (heavy-quark bound states, charmonium and bottomonium spectroscopy, potential models); §9 analogy with hydrogen | **U (upper) → R** | Quarkonium as "the hydrogen atom of QCD" (Griffiths EP ch. 5 "Bound States"); model vs PDG is research practice | U: «cc̄ 1S…», «cc̄ 1P…», «cc̄ 2S…», «bb̄ 1S: облако теснее…». R: «cc̄ 1S + 1P_z … суперпозиция», model splittings vs PDG |
| **v15** Kerr shadow | §7 GR (black holes, photon orbits, lensing, redshift); §13 astrophysics (accretion disks, EHT images of M87*, Sgr A*) | **S (enrichment) → U → R** | The EHT image is public knowledge; its explanation is GR (Hartle ch. 15; Exploring Black Holes ch. 20); tests of the Kerr metric are research | S: «Без вращения (a = 0): тень — круг радиуса √27 M». U: «Диск с ребра…», «Узкое кольцо газа у 6 M: … изображения n = 0, 1, 2». R: «Sgr A*: … сравнение с EHT 2022», «Что если: метрика Йоханнсена α₁₃ = 3» |
| **v16** Optical vortices | §6 Optics (laser beams, Laguerre–Gauss modes, orbital vs spin angular momentum of light, fork holograms, rotational Doppler) | **U (upper) → R** | OAM of light is modern optics (Allen et al. 1992), beyond Hecht's core; exact vs paraxial beams is research-grade | U: «LG₀³, σ = +1: три винтовых фронта…», «LG₂¹: три кольца…», «Голограмма-«вилка»…», «Контроль: гауссов пучок без вихря». R: «То же в параксиальной модели (приближение): чего она не видит», «Призма Дове вращается: сдвиг частоты 2\|l\|f», «Линейная поляризация, l = 1…» |
| **v17** Mie scattering | §6 Optics (refraction, reflection and dispersion in drops → rainbow; interference → supernumerary arcs; diffraction → fogbow, glory; scattering theory) | **S → U → R** | The rainbow is school optics (dispersion, refraction; ФРП 9 «Световые явления»; Ландсберг т.3); supernumeraries and Airy theory are university; the exact Mie and Debye series are research (Bohren & Huffman) | S: «Радуга: капли 0,15 мм … основная и вторичная дуги, полоса Александра». U: «Дополнительные дуги: одинаковые капли 0,1 мм», «Крупные капли … размыты», «Туманная радуга». R: «Глория…», «Ближнее поле: капля 1 мкм…», «Поглощающий шар…», Debye vs Descartes vs Airy, Wiscombe checks |

### 3.2 Playgrounds p01–p04

| Viz | Sections | Levels | Why | Presets per level |
|---|---|---|---|---|
| **p01** Space and gravity | §1 Mechanics (universal gravitation, Kepler laws, circular orbits, N-body, three-body chaos, mergers; conservation of energy and angular momentum); §13 (solar system, binaries, black holes); §7 GR (Kerr–Newman geodesics, clocks; post-Newtonian binary, gravitational waves) | **P: S → U → R** | Orbits are the one school mechanics topic the engine has (ФРП 9 «Механические явления»; IB D.1; HRW 13 Gravitation); GW inspiral and Kerr–Newman are research | S: «Солнце и Земля (круговая орбита 1 а.е.)», «Солнце, Меркурий, Венера, Земля, Марс, Юпитер». U: «Пифагорова задача трёх тел (Бурау)», «Ньютоновская чёрная дыра 1000 M☉ и звёзды: орбиты и захват». R: «ОТО: двойная 10 + 10 M☉ … детектор волн», «ОТО: эксцентрическая двойная 30 + 10 M☉», «У чёрной дыры (a = 0,9): тела, лучи, часы» |
| **p02** Quantum particles | §8 Quantum (packets in 2-D/3-D, double slit, which-path, Aharonov–Bohm, tunnelling, harmonic trap, position measurement, electron in a magnetic field, spin); foundations (decoherence, Bohm) | **P: U → R** (S enrichment with the double slit) | A sandbox for the QM course: build potentials and measure; the decoherence and Bohm layers are research | S (enrichment): «Двухщелевой опыт: электрон…». U: «Туннелирование…», «Гармоническая ловушка … измерение положения», «Электрон в магнитном поле 100 Тл…», «3-D: электрон рассеивается на шаре». R: «Метка пути в верхней щели…», «Ааронов–Бом: трубка потока h/2e…», environment (decoherence), sweeps |
| **p03** Particles and molecules | §4 Thermal and molecular physics (kinetic theory: Maxwell distribution, temperature, pressure; gas laws; first law with a piston: heat and work, adiabatic vs quasi-static vs jump; free expansion; phase transitions: melting, liquid–vapour; equipartition in diatomic molecules; hard-disk equation of state; diffusion); §10 crystals | **P: S → U → R** | The strongest school match of all 21 entries: ФРП 8 «Тепловые явления» and ФРП 10 «Основы МКТ», «Основы термодинамики», «Агрегатные состояния», AP2 U9, IB B.1–B.4 — computed from atoms rather than drawn | S: «Газ аргона из одинаковых скоростей: распределение Максвелла устанавливается само», «Газ под поршнем: сжатие поршнем и теплообмен со стенкой (первое начало)», «Плоский кристалл … нагревают … порядок ψ6 исчезает». U: «Двухатомные молекулы … столкновения» (equipartition), «Жидкость и пар в объёме при 90 K в поле», g(r), virial. R: «Твёрдые диски: давление против уравнения состояния (Колафа и Роттнер)», thermostats, NIST benchmarks, sweeps |
| **p04** Fluids | §2 Fluids (viscous flow past bodies, drag and lift, Reynolds number, Kármán vortex street, Poiseuille, lid-driven cavity, airfoil) | **P: S (enrichment) → U → R** | Flow visualisation with dye and a lifting wing work at school (Ландсберг т.1 IX «Гидродинамика и аэродинамика»; AP1 U8), but ФРП 7 covers hydrostatics, not flow; Re, C_D and Strouhal are university (Kundu ch. 9–10, 14); the DFG and Ghia benchmarks are research | S: «Профиль крыла NACA 2412 под углом атаки 8°», «Вода: обтекание цилиндра D = 1 мм…». U: «Течение в канале (Пуазейль, Re ≈ 2) и пластина поперёк», «Дорожка Кармана за цилиндром, Re = 100». R: «Обтекание цилиндра, Re = 20 (постановка DFG 2D-1…)», «Каверна с подвижной крышкой … Ghia», sweeps of Re |

### 3.3 Coverage matrix (section × level; entries with at least one suitable preset)

| Section | School | University | Research | Playground |
|---|---|---|---|---|
| 1 Mechanics | v04 (ellipse only), p01 (orbits only) | v04, p01 | p01 | p01 |
| 2 Fluids | p04 (enrichment) | p04 | p04 | p04 |
| 3 Oscillations and waves | — | v08 (diffraction); v03 (quantum oscillator) | v08 | — |
| 4 Thermal / molecular | p03 | p03 | p03 | p03 |
| 5 Electricity and magnetism | — | — (only EM waves inside optics) | — | — |
| 6 Optics | v02, v05, v17 | v02, v05, v08, v16, v17 | v02, v05, v08, v16, v17 | — (P15.2 planned) |
| 7 Relativity (SR, GR) | v01, v10 (enr.), v15 (enr.) | v01, v04, v09, v10, v15 | v01, v04, v09, v10, v15, p01 | p01 (GR only; P15.6 planned) |
| 8 Quantum | v02 | v02, v03, v07, v11, p02 | v02, v03, v07, v11, v12, p02 | p02 |
| 9 Atomic | v13 | v13 | v13 | — |
| 10 Condensed matter | — | p03 (crystal, melting) | p03 | p03 |
| 11 Nuclear | — | — | — | — |
| 12 Particle | — | v06, v14 | v06, v14 | — |
| 13 Astrophysics / cosmology | v01 (Sun–Earth), p01 (solar system) | v04, v15, p01 | v15, p01 | p01 |

Reading of the matrix, with status tags:
- [weakens] The collection is **research- and university-heavy and back-loaded**. At school level, the first half of
  every curriculum has nothing beyond orbits: mechanics, oscillations, electricity and magnetism. In the ФРП ООО basic
  programme those sections take **152 of 238 h (64 %)**: grade 7 sections 3–5 (54 h), grade 8 «Электрические и
  магнитные явления» (37 h), and grade 9 «Механические явления», «Механические колебания и волны» and «Электромагнитное
  поле…» (61 h). AP Physics 1 is entirely mechanics.
- [weakens] A "School" group today would hold **7 entries with presets that match the curriculum** (v01, v02, v05,
  v13, v17, p01, p03) and **5 enrichment entries** (v04, v10, v15, p02, p04). Apart from p03 (thermal physics),
  p01 (orbits) and p04 (enrichment), all of them sit in optics, quantum, atomic physics and relativity: the last
  chapters of a school course.
- [useful] Optics, quantum and relativity are covered at every level, with presets that span school → research.
  This is a distinctive strength. PhET, Falstad and Fendt have nothing comparable at the research end.
- [useful] p03 is a good school entry point for thermal physics. Its school presets exist already; it lacks only
  dedicated gas-law and heat-engine presets (§4).

---

## 4. Gaps: classic demonstrations without a visualization

Support codes:
- **A** — already shown (a demo or preset exists).
- **B** — the engine's existing modules support it; only a visualization or preset is needed.
- **C** — partly supported; a module needs an extension.
- **D** — new physics needed. "D-simple" means the physics is elementary (closed forms exist), but there is no module.

Module names follow `lfphys/README.md`. "Unused" means no `vNN`/`pNN` imports the module today (checked by grep on
2026-11-12).

### 4.1 By section

| Section | Classic demonstration | Code | Engine support / what is missing |
|---|---|---|---|
| Mechanics | projectile motion (with/without drag), free fall | **D-simple** | no particle-in-uniform-field module. Only a hack: p03 has a uniform field and Shift-throw of an atom, at nm/ps scale |
| | Newton's laws: forces, friction, inclined plane, Atwood machine | **D-simple** | no classical rigid-body or constraint mechanics |
| | energy conservation (track / "skate park"), work | **D-simple** | same |
| | collisions (elastic / inelastic, 1-D and 2-D), momentum conservation | **C** | `core.md.hard`: exact elastic collisions of disks and spheres of any mass and size; `core.gravity.nbody`: perfect merger. Missing: coefficient of restitution, macroscopic units |
| | rotation, torque, angular momentum, rolling, gyroscope | **D** | needs rigid-body dynamics (v09's gyroscopes are relativistic spin transport) |
| | Kepler's laws, satellites, escape speed; three-body chaos | **A** | p01, v04 |
| | non-inertial frames: Coriolis, Foucault pendulum | **D-simple** | — |
| | elasticity (stress–strain) | **C** | p03 crystal plus box deformation (`MD.deform`, `affine_stress`) at the atomic scale; no continuum elasticity |
| Fluids | pressure vs depth, communicating vessels | **C** | `core.fluids.lbm` has a hydrostatic rest state under a body force, but it is a 2-D incompressible flow solver |
| | Archimedes, buoyancy, floating | **D** | LBM bodies do not move ("bodies do not move") |
| | continuity and Bernoulli (Venturi tube) | **B** | p04: a channel with a constriction plus velocity and pressure sensors (preset only) |
| | viscosity, Poiseuille, drag, vortex street, wing lift | **A** | p04 |
| | shocks, compressible flow, free-surface waves, 3-D turbulence | **D** | Euler shock tube deferred (STATUS V41 x) |
| Oscillations and waves | spring and pendulum SHM, damped and driven oscillations, resonance | **D-simple** | (approximable in p03 with a frozen atom, a harmonic bond and a field; not a proper demo) |
| | coupled oscillators, normal modes | **C** | p03 molecules with harmonic bonds (Verlet's bond and bend frequencies are tested) |
| | standing waves on a string, in a pipe; sound; beats | **D-simple** | 1-D wave equation and acoustics: no module |
| | EM standing waves, cavity modes | **B** | `core.em.fdtd` (PEC cavity modes tested); **unused** |
| | two-source interference, ripple tank | **B** | `core.em.fdtd` 2-D with two soft sources, or `optics.angular_spectrum` (scalar waves; no water-wave dispersion) |
| | Huygens' principle, single-slit diffraction | **A** | v08, v11, v02 |
| | Doppler effect (sound), shock cone | **C** | relativistic Doppler exists (v01, v10; rotational Doppler in v16); an acoustic moving source in a wave solver is missing |
| Thermal | gas laws (Boyle, Charles, Gay-Lussac) | **B** | p03: piston, thermostats, P/V/T instruments and parameter sweeps; needs presets |
| | Maxwell distribution; kinetic meaning of T and p | **A** | p03 |
| | heat engine, Carnot cycle, PV diagram | **C** | p03 piston (driven/free), thermal walls and baths, heat/work counters and the first-law balance. Missing: scripted switching of baths within a cycle, and a P–V plot (the instruments plot quantities against time) |
| | heat conduction | **B** | thermal walls at two temperatures (Knudsen heat tested); crystal between baths |
| | diffusion, Brownian motion | **B** | `core.md`: species of different mass and size, MSD, Langevin |
| | phase transitions | **A** | p03 melting, liquid–vapour |
| | entropy and irreversibility: free expansion, mixing | **B** | p03 "wall over empty space" (Joule expansion); two species |
| | blackbody spectrum (Wien, Stefan–Boltzmann) | **B** | `core.optics.radiation` (Planck) and `tools.colour`; used only for colours in v10, v17 |
| E&M | field lines and equipotentials of point charges; superposition | **B** | `core.em.charges` (Coulomb exact; Liénard–Wiechert for moving charges); **unused** |
| | conductors, capacitors, dielectrics (statics) | **D** | needs a Poisson/Laplace solver (planned in P15.5) |
| | DC circuits (Ohm, Kirchhoff, series/parallel, RC), AC, RLC | **D** | needs a circuit solver |
| | magnetic field of wire, loop, solenoid (Biot–Savart, Ampère) | **D** | planned in P15.5 |
| | charge in E and B: cyclotron, mass spectrometer, E×B drift | **B** | `core.spin_transport` (relativistic charge in uniform fields); p02 (quantum electron in B_z) |
| | electromagnetic induction: Faraday, Lenz, generator, transformer | **D** | quasi-static induction: no module |
| | EM waves, dipole antenna, Larmor radiation, synchrotron light | **B** | `core.em.fdtd`, `core.em.charges` (Larmor, Liénard, synchrotron spectrum); **unused** |
| | waveguides, resonant cavities | **B** | `core.em.fdtd` |
| Optics | reflection and refraction (Snell), TIR | **A** | v05 |
| | lenses, mirrors, image formation, instruments | **C** | `theories.approx.ray_optics` (Snell, ABCD matrices) exists. Missing: a ray tracer with images. Wave-optics focusing needs only a thin-lens phase mask beside `beams_thin_masks` |
| | prism dispersion, spectrum | **C** | water n(λ) (IAPWS) exists; glass dispersion data are missing |
| | Young's experiment; thin films; Fabry–Pérot | **A** | v02, v08, v11; v05 |
| | diffraction grating, spectrometer | **A/C** | v02 has a 10-slit grating (C60); a dedicated grating-spectrometer demo is missing |
| | polarisation: Malus's law, wave plates, birefringence | **C** | v02 polarisers and λ/2 plate, v05 Brewster, `core.quantum.qubits`; no crystal optics |
| | Michelson interferometer fringes | **B** | scalar optics (trivial). v01 has only the Michelson–Morley timing in the ether world |
| | rainbow | **A** | v17 |
| | blue sky, Rayleigh scattering | **B** | `core.optics.mie` (small-particle limit) and `tools.colour`; a v17 preset |
| Relativity | time dilation, length contraction, twin paradox, Minkowski diagram | **B** | `core.relativity`, `core.worldlines`, `core.causality` (v01 has clocks and simultaneity lines); P15.6 planned |
| | relativistic Doppler, aberration | **A** | v01, v10 |
| | E = mc², relativistic collisions and decays (4-momenta) | **B** | `core.lorentz` |
| | GPS clock corrections | **B** | `core.gravity` and `core.relativity` (p01 has clocks near a hole) |
| | light deflection, black holes, gravitational waves | **A** | v01, v15, p01 |
| Quantum | photoelectric effect | **D-simple** | no module (Einstein's equation plus an emission model, so that it is computed, not drawn) |
| | Compton scattering | **B** | `core.quantum.compton` (shift, Klein–Nishina); **unused** |
| | electron diffraction, wave–particle duality | **A** | v02, v11, p02 |
| | particle in a box, quantum oscillator, tunnelling | **A** | v03, p02 |
| | uncertainty, measurement | **A** | p02 «Измерить положение» |
| | Stern–Gerlach, spin | **B** | p02 magnetic field with gradient g acting on spins through −μ·B; needs a preset |
| | two-level atom, Rabi oscillations, spontaneous emission (basis of lasers) | **B** | `core.quantum.two_level`, `jumps`, `open_systems`; two_level and open_systems are **unused** |
| | qubits, Bloch sphere, gates | **B** | `core.quantum.qubits` (used only by v07) |
| Atomic | hydrogen line spectrum (Lyman, Balmer), emission and absorption | **B** | `core.quantum.hydrogen` (Schrödinger and Dirac levels) and `central3d` (dipole matrix elements → line strengths); v13 has the level panel but no spectrum |
| | Bohr model | **B** | closed forms as references; v13 |
| | Rutherford scattering | **C** | Coulomb forces exist (`core.md`, walled boxes); needs a scattering set-up with the cross-section as reference |
| | Zeeman and Stark effects; multi-electron atoms; Franck–Hertz | **D** | — |
| Nuclear | radioactive decay, half-life, decay chains | **D-simple** | Monte Carlo decays and Bateman equations; needs nuclear data |
| | binding energy curve, fission, fusion, chain reaction | **D** | needs nuclear masses (e.g. AME) and a reaction model |
| | detectors (cloud chamber), absorption of radiation | **D** | — |
| Particle | running α_s; quarkonium | **A** | v06, v14 |
| | relativistic kinematics: invariant mass, decays, thresholds | **B** | `core.lorentz` |
| | particle families, conservation laws, Feynman diagrams | **D** (data, presentation) | — |
| Astro / cosmology | solar system, binaries, GW, black holes | **A** | p01, v04, v15 |
| | Hubble law, expanding universe, a(t), cosmic distances, CMB temperature, age | **B** | `core.cosmology.flrw` with Planck 2018; **unused** |
| | tides | **B** | `core.gravity.nbody` tidal tensor |
| | stars: HR diagram, structure, evolution, fusion in stars | **D** | — |
| Condensed matter | crystals, melting | **A** | p03 |
| | band structure (Kronig–Penney), Bloch waves | **C** | `core.quantum.transfer` gives the transmission of periodic piecewise potentials (bands as transmission windows); no Bloch eigenproblem |
| | X-ray (Bragg) diffraction | **C** | scalar diffraction exists; no crystal structure factor |
| | semiconductors, superconductivity, Ising / magnetism | **D** | — |

### 4.2 Gaps ranked by importance for school and university teaching

Importance weighs three things: (a) how universal the topic is across the checked programmes (ФРП 7–11, AP, IB,
A-level, HRW/Y&F/OpenStax); (b) how many teaching hours it takes; (c) how early it comes, since early sections set a
reader's first impression of a "for schools" group.

| Rank | Gap | Programmes that require it (examples) | Code | Cost note |
|---|---|---|---|---|
| 1 | **Mechanics core**: kinematics and projectile motion; Newton's laws with friction; work–energy and energy conservation; momentum and collisions | ФРП 7, 9, 10; AP1 U1–4; AP C:M; IB A.1–A.3; AQA 3.4; HRW 2–9 | D-simple (collisions C) | one new module, classical 2-D particles and rigid bodies with constraints, contact and drag. It would also serve ranks 2 and 14 |
| 2 | **Oscillations**: pendulum, spring, damped and driven, resonance | ФРП 9, 11; AP1 U7; IB C.1; AQA 3.6.1; HRW 15 | D-simple | same module as rank 1 |
| 3 | **Electric circuits**: DC, then RC, RLC, AC | ФРП 8, 10, 11; AP2 U11; AP C U11; IB B.5; AQA 3.5; HRW 26–27, 31 | D | a circuit solver (modified nodal analysis); physics elementary |
| 4 | **Electrostatics**: field lines and potential of charges; capacitors | ФРП 8, 10; AP2 U10; AP C U8–10; IB D.2; AQA 3.7.3–3.7.4; HRW 21–25 | B (point charges) / D (conductors) | point charges are cheap now via `core.em.charges`; conductors need P15.5's Poisson solver |
| 5 | **Magnetism and induction**: fields of currents, force on currents, Faraday/Lenz, generator, transformer | ФРП 8, 9, 11; AP2 U12; AP C U12–13; IB D.2–D.4; AQA 3.7.5; HRW 28–31 | D (motion of charges B) | Biot–Savart plus quasi-static induction (P15.5) |
| 6 | **Mechanical waves and sound**: superposition, standing waves, sound, Doppler, beats | ФРП 9, 11; AP2 U14; IB C.2–C.5; AQA 3.3.1; HRW 16–17 | C / D-simple | ripple tank and cavities are cheap via FDTD; strings, sound and an acoustic moving source need a small 1-D/2-D acoustic solver |
| 7 | **Geometric optics**: lenses, mirrors, image formation, prism | ФРП 9, 11; AP2 U13; HRW 34; Hecht 5–6 | C | a 2-D ray tracer on top of `approx.ray_optics`; P15.2 planned |
| 8 | **Thermodynamics as named school demos**: gas laws, heat-engine cycle with a PV diagram | ФРП 8, 10; AP2 U9; IB B.3–B.4; AQA 3.6.2; HRW 18–20 | B / C | the physics is in p03: presets plus a P–V plot. **Cheapest high-value item** |
| 9 | **Atomic line spectra**: hydrogen emission and absorption, Bohr levels | ФРП 9, 11; IB E.1; AQA 3.2.2; HRW 40 | B | `core.quantum.hydrogen` and `central3d` exist; a spectrum view next to v13. Cheap |
| 10 | **Photons**: photoelectric effect, Compton scattering, blackbody spectrum | ФРП 11; AP2 U15; IB E.2 (HL); AQA 3.2.2; HRW 38 | D-simple / B / B | Compton and Planck are unused modules; the photoelectric effect needs a small emission model |
| 11 | **Radioactivity and nuclear energy**: decay and half-life, binding energy, fission and fusion | ФРП 9, 11; AP2 U15; IB E.3–E.5; AQA 3.8; HRW 42–43 | D-simple / D | the only universal school section with no engine physics at all; needs a nuclear data source |
| 12 | **Special relativity basics**: time dilation, length contraction, twin paradox, spacetime diagram | ФРП 11 «Основы СТО»; IB A.5 (HL); AQA 3.12 (option); HRW 37 | B | `core.relativity` and `core.worldlines`; P15.6 planned. v01 and v10 cover only part of it |
| 13 | **Fluid statics and Bernoulli**: pressure vs depth, Archimedes and floating, Venturi | ФРП 7; AP1 U8; HRW 14 | C / D / B | Venturi is a p04 preset; floating needs moving bodies |
| 14 | **Rotational dynamics**: torque, angular momentum, rolling, gyroscope | AP1 U5–6; AP C; IB A.4 (HL); HRW 10–11 | D | the rank-1 module with rigid bodies; heavy in US and university courses, light in the Russian basic course |
| 15 | **Cosmology**: Hubble law, expansion history, CMB | ФРП 11 «Элементы астрономии и астрофизики»; AQA 3.9 (option); HRW 44; Y&F 44 | B | `core.cosmology.flrw` is unused. Cheap |

University-specific gaps after these (upper courses):
- Lagrangian and Hamiltonian mechanics, phase space, chaos (double pendulum, Poincaré sections). D; would come
  with the rank-1 module.
- Two-level atom, Rabi oscillations, Bloch sphere, quantum jumps. B, cheap: modules exist and are unused.
- Stern–Gerlach. B: a p02 preset.
- Dipole radiation, antennas, waveguides. B: FDTD is unused.
- Boltzmann distribution (barometric law, already tested in `core.md`). B.
- Band structure. C.
- Rutherford scattering. C.
- Ising model and magnetism. D.
- Stellar structure. D.

**Cheapest high-value additions** (code B, physics already verified in the engine): gas laws and a heat-engine cycle
(p03 presets); the hydrogen spectrum; the blackbody spectrum; Compton scattering; cosmic expansion (FLRW); fields of
point charges and dipole radiation; a ripple tank; Rabi oscillations; Stern–Gerlach; Venturi (p04 preset); the blue
sky (v17 preset); the twin paradox and spacetime diagram; relativistic collision kinematics. Each costs a
visualization or a preset, not new physics. These additions are untested hypotheses about effort until someone
scopes them.

---

## 5. What good public demo collections do (structure only)

Full findings with verification URLs are in Appendix D.

| Collection | Organisation by topic | By level | Each entry shows | Languages | Licence (verified 2026-11-12) |
|---|---|---|---|---|---|
| **PhET** (CU Boulder) | subjects → subcategories (Physics: Motion · Sound & Waves · Work, Energy & Power · Heat & Thermo · Quantum Phenomena · Light & Radiation · Electricity, Magnets & Circuits); tags, so one sim sits in several categories | Elementary / Middle / High / University as a **range** per sim; device filter | thumbnail and screenshots, title, 1–2-sentence description, **learning goals**, Teacher Tips PDF, video, related sims, standards, accessibility tags, run plus per-language download, teacher activities | 130 locales; **ru for 90 of 127 HTML5 sims, but only interface and title** (no Russian descriptions or goals) | content **CC BY-NC 4.0** since 2026-03-29 (CC BY 4.0 before); common code MIT; sim code no longer public |
| **Falstad** | one flat page, 11 sections in the author's order (not textbook order) | none | thumbnail, title, one line; the page has an **Examples menu of presets**, directions, full screen, offline version, GitHub, related applets | English; the circuit simulator interface in 15 locales, incl. ru | site terms: non-commercial modification and redistribution with credit; CircuitJS1 GPL-2.0+ |
| **oPhysics** | Kinematics · Forces · Conservation · Waves · Light · E & M · Rotation · Fluids · Modern (AP order) | none (implicitly high school / AP) | thumbnail, title, 1–3 sentences; GeoGebra applet and a description; "challenge" variants | English only | no formal licence; "non-profit educational purposes" permission |
| **myPhysicsLab** | flat gallery of about 50, ordered by model complexity, prev/next links | none | thumbnail and title; page: **Sim / Graph / Time Graph / Multi Graph** tabs, "what to try", script console, source · docs · customise, *Puzzles · Physics · Numerical Solution · Puzzle Answers* | English, German (parallel pages) | code Apache-2.0; text © author |
| **Walter Fendt** | 9 sections in **strict textbook order** with counts ("Mechanics (19)") | none | title plus first-published – last-revised dates; page: what it shows → controls → modelling assumptions; one ZIP per language | 20–21 languages; **ru full translation, but lagging** (51 vs 57 apps) | no licence on the current site; a 1998 notice allows non-commercial copying |
| OSP / ComPADRE (extra) | by resource type | several ComPADRE levels per item | library record: subjects, levels, type, format, licence, rights holder, citation | English | per item (e.g. CC BY-NC-SA 3.0; EJS GPL v3) |
| «Открытая физика» / Физикон (extra) | offline (physics.ru parked); successor is commercial ЕГЭ prep | "ЕГЭ" | — | Russian | proprietary |

Observations relevant to lfphys:
- [useful] No collection found offers what lfphys does at the research end: computed checks against references,
  modified-physics worlds, or research-grade presets. No maintained, open, Russian-first collection with Russian
  descriptions turned up (limited search). A bilingual README with Russian descriptions would therefore be uncommon.
- [neutral] The level labels in use are PhET's four grade bands and ComPADRE's multi-level tags. None of the five
  has a "research" level, so lfphys has to define it.
- [neutral] The lfphys licence (noncommercial, citation required) sits close to PhET's current CC BY-NC.

---

## 6. Recommendations for the README structure (for discussion; not done)

1. **Four groups as the owner asked**: School / University / Research / Playgrounds. Inside each group, order
   sections by §2 (mechanics → … → cosmology) and give each section heading a count, as Fendt does.
2. **One demo, several groups, distinct presets.** A demo that serves several levels (v01, v02, v05, v13, v17, p01,
   p03) should appear in each group with **the presets for that level** named and linked, not with the same card
   repeated. Each card also carries a **level-range badge** (e.g. "S → U → R"), as PhET does. §3's last column gives
   the preset names per level.
3. **Card schema** (same for EN and RU): picture or GIF · title · one line "what you will see" · level badge · section
   tags · 2–3 "try this" presets · a link to `vNN/README.md` · "computed, checked against: …" (lfphys's distinctive
   feature: the run's checks against references).
4. **Curriculum anchors** where they exist: the RU README cites ФРП sections (e.g. «11 кл., Основы СТО»); the EN
   README cites AP/IB/A-level units. Keep them one line, and only where the match is real (§3).
5. **Be honest about coverage.** Say that school coverage currently starts at optics, thermal physics and modern
   physics, and that mechanics and E&M are planned (P15.2, P15.5, P15.6 for the playgrounds; §4 for the classic
   demos). Or name the school group "Upper school (grades 9–11), enrichment" until rank 1–5 gaps are filled. A "for
   schools" heading that opens on quantum and black holes will mislead teachers.
6. **Further reading per section**: link only to legal open texts:
   - OpenStax Physics (CC BY 4.0); College Physics 2e and University Physics (CC BY-NC-SA 4.0);
   - Crowell, Light and Matter (CC BY-SA 3.0);
   - Spacetime Physics and Exploring Black Holes (CC BY 4.0);
   - MIT OCW (CC BY-NC-SA 4.0);
   - the Feynman Lectures (free to read: link only, never copy).

   For Russian readers, cite the ФРП (edsoo.ru, official) and name the textbooks without links: none has a legal free
   copy.
7. **Languages.** Build parallel EN and RU pages with the same anchors and card order, and state what is translated.
   Fendt's lagging Russian index (51 vs 57 apps) and PhET's title-only Russian are the cautionary examples.
8. **Licence block.** Separate the code licence from the content licence and give a ready attribution or citation
   line. lfphys already has `CITATION.cff`.

---

## 7. Caveats and verification limits

- [weakens] Not verified, and not to be quoted in a public README without a check:
  - **Feynman Lectures chapter list**: taken from Wikipedia; feynmanlectures.caltech.edu blocked the fetch.
  - **Berkeley vols 1, 3, 4, 5 contents**: Crawford and Reif are listed from memory and flagged in Appendix B.
  - **Current Перышкин–Иванов 7–9 and Мякишев 10–11 chapter lists**: the publisher's pages are behind a sign-in check.
    For these books the ФРП sections are used as a proxy, since the publisher states that the books follow the
    programme. That is an inference.
  - **Иродов «Основные законы»** chapter lists.
  - **ЛЛ V** chapter titles in Russian (verified in English only).
  - The **2024–25 AP move of Fluids into Physics 1**: confirmed on the course pages; only the College Board revisions
    page (403) was not read.
- [neutral] Bookstores disagree on some Russian edition numbers (Савельев); Appendix C shows both values.
- [neutral] The PhET licence change is taken from PhET's own metadata service and its Historical Software Agreement
  page. The current `/licensing` page needs JavaScript and was not read.
- [neutral] The mapping in §3 rests on the visualizations' own READMEs and preset labels, not on running them. The
  "S/U/R" level judgements are mine, based on the curriculum documents cited.
- [neutral] The "unused module" list in §4 is a text search of `visualizations/v*`, `p0*` and `server/` for module
  names (tests excluded). An import under another name would be missed.

---

# Appendices: the four research parts (verified tables of contents, with sources)


---

# Appendix A. School physics: textbooks and official curricula (verified tables of contents)

Research date: 2026-11-12. Status: complete. Each item lists what was verified and from which fetched page; anything not seen on a fetched page is marked "Not verified".

## 1. OpenStax (open textbooks)

Note on verification method: openstax.org pages are JavaScript-rendered, so the metadata and chapter trees were read from openstax.org's own JSON endpoints that feed those pages (CMS API for the details page; content archive for the book's table of contents, archive release 20260604.144757).

### 1a. OpenStax "Physics" (high-school book)
- Authors: Paul Peter Urone, Roger Hinrichs (senior authors); contributing: Fatih Gozuacik, Denise Pattison, Catherine Tabor. Licence text names the Texas Education Agency (TEA) as originator ("Physics by Texas Education Agency (TEA) is licensed under CC BY 4.0").
- Title: Physics
- Edition/year: 1st edition, publish date 2020-03-26 (content revised 2026-07-08, version dfdfd7a). Print ISBN 978-1-975076-51-1; digital ISBN 978-1-951693-21-3.
- Publisher: OpenStax (Rice University).
- Level: US high school (introductory, algebra-based).
- Open: YES. https://openstax.org/details/books/physics ; read online https://openstax.org/books/physics/pages/1-introduction . Licence: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/).
- Contents (23 chapters, no unit grouping in the book tree):
  1 What is Physics? | 2 Motion in One Dimension | 3 Acceleration | 4 Forces and Newton's Laws of Motion | 5 Motion in Two Dimensions | 6 Circular and Rotational Motion | 7 Newton's Law of Gravitation | 8 Momentum | 9 Work, Energy, and Simple Machines | 10 Special Relativity | 11 Thermal Energy, Heat, and Work | 12 Thermodynamics | 13 Waves and Their Properties | 14 Sound | 15 Light | 16 Mirrors and Lenses | 17 Diffraction and Interference | 18 Static Electricity | 19 Electrical Circuits | 20 Magnetism | 21 The Quantum Nature of Light | 22 The Atom (incl. 22.2 Nuclear Forces and Radioactivity, 22.3 Half Life, 22.4 Fission and Fusion, 22.5 Medical Applications) | 23 Particle Physics
  - Remark: special relativity is placed right after mechanics (ch. 10), before thermal physics; nuclear physics is folded into "The Atom".
- Verified from: https://openstax.org/apps/cms/api/v2/pages/415/?format=json (authors, publish date, ISBNs, licence); https://openstax.org/apps/archive/20260604.144757/contents/cce64fde-f448-43b8-ae88-27705cceb0da@dfdfd7a.json (chapter tree + licence field CC BY 4.0).

### 1b. OpenStax "College Physics 2e" (algebra-based)
- Authors: Paul Peter Urone, Roger Hinrichs (senior); contributing: Kim Dirks, Manjula Sharma, Kenneth Podolak, Henry Smith.
- Title: College Physics 2e
- Edition/year: 2nd edition, publish date 2022-07-13 (content revised 2026-07-09, version fd1b25d). Print ISBN 978-1-711470-83-2; digital 978-1-951693-60-2.
- Publisher: OpenStax (Rice University).
- Level: introductory college, algebra-based (two semesters).
- Open: YES. https://openstax.org/details/books/college-physics-2e . Licence per openstax.org metadata: **CC BY-NC-SA 4.0** (https://creativecommons.org/licenses/by-nc-sa/4.0/) — NOT CC BY 4.0 (the first edition "College Physics", now retired, was CC BY). Both the CMS record and the archive book record state BY-NC-SA.
- Contents (34 chapters): 1 Introduction: The Nature of Science and Physics | 2 Kinematics | 3 Two-Dimensional Kinematics | 4 Dynamics: Force and Newton's Laws of Motion | 5 Further Applications of Newton's Laws: Friction, Drag, and Elasticity | 6 Uniform Circular Motion and Gravitation | 7 Work, Energy, and Energy Resources | 8 Linear Momentum and Collisions | 9 Statics and Torque | 10 Rotational Motion and Angular Momentum | 11 Fluid Statics | 12 Fluid Dynamics and Its Biological and Medical Applications | 13 Temperature, Kinetic Theory, and the Gas Laws | 14 Heat and Heat Transfer Methods | 15 Thermodynamics | 16 Oscillatory Motion and Waves | 17 Physics of Hearing | 18 Electric Charge and Electric Field | 19 Electric Potential and Electric Field | 20 Electric Current, Resistance, and Ohm's Law | 21 Circuits and DC Instruments | 22 Magnetism | 23 Electromagnetic Induction, AC Circuits, and Electrical Technologies | 24 Electromagnetic Waves | 25 Geometric Optics | 26 Vision and Optical Instruments | 27 Wave Optics | 28 Special Relativity | 29 Quantum Physics | 30 Atomic Physics | 31 Radioactivity and Nuclear Physics | 32 Medical Applications of Nuclear Physics | 33 Particle Physics | 34 Frontiers of Physics
- Verified from: https://openstax.org/apps/cms/api/v2/pages/603/?format=json ; https://openstax.org/apps/archive/20260604.144757/contents/a31df062-930a-4f46-8953-605711e6d204@fd1b25d.json

### 1c. OpenStax "College Physics for AP® Courses 2e" (brief)
- Authors (as listed by OpenStax): Gregg Wolfe, Erika Gasper, John Stoke, Julie Kretchman, David Anderson, Nathan Czuba, Sudhi Oberoi, Liza Pujji, Irina Lyublinskaya, Douglas Ingram; contributing: Kenneth Podolak, Henry Smith. (Adaptation of College Physics by Urone/Hinrichs.)
- Edition/year: 2nd edition, publish date 2022-07-19. Print ISBN 978-1-711470-84-9; digital 978-1-951693-61-9.
- Publisher: OpenStax. Level: US high school AP Physics 1 & 2.
- Open: YES. https://openstax.org/details/books/college-physics-ap-courses-2e . Licence per openstax.org metadata: CC BY-NC-SA 4.0.
- Contents: the same 34 chapter titles as College Physics 2e (1 Introduction ... 34 Frontiers of Physics), each opening with a "Connection for AP® Courses" section; content beyond AP scope is kept.
- Verified from: https://openstax.org/apps/cms/api/v2/pages/604/?format=json ; https://openstax.org/apps/archive/20260604.144757/contents/fc65697b-5a9e-4dfe-ac03-035129f7be28@fd1b25d.json
- Not verified: whether OpenStax has re-aligned this book to the 2024–25 revised AP Physics 1 units (the chapter list is unchanged from the 2e structure).

## 2. Paul G. Hewitt, "Conceptual Physics"
- Author: Paul G. Hewitt (City College of San Francisco).
- Title: Conceptual Physics
- Edition/year: 13th edition; the Pearson page shows "Published 9 February 2021, © 2022" (eTextbook ISBN 9780137394975; Mastering + eText ISBN 9780135746356). A Global Edition of the 13th edition also exists (Pearson UK pages, ISBN 9781292437460 / 9781292742373). No 14th edition found in Pearson listings or search (2026-11-12).
- Publisher: Pearson.
- Level: introductory college, conceptual (minimal algebra). A separate high-school "Conceptual Physics" by Hewitt also exists (not checked here).
- Open: no (commercial).
- Contents (36 chapters in 8 parts; chapter numbers follow from the part ranges shown on the page):
  1 About Science
  - Part I Mechanics: 2 Newton's First Law of Motion: Inertia | 3 Linear Motion | 4 Newton's Second Law of Motion: Force and Acceleration | 5 Newton's Third Law of Motion: Action and Reaction | 6 Momentum | 7 Energy | 8 Rotational Motion | 9 Gravity | 10 Projectile and Satellite Motion
  - Part II Properties of Matter: 11 The Atomic Nature of Matter | 12 Solids | 13 Liquids | 14 Gases
  - Part III Heat: 15 Temperature, Heat and Expansion | 16 Heat Transfer | 17 Change of Phase | 18 Thermodynamics
  - Part IV Sound: 19 Vibrations and Waves | 20 Sound | 21 Musical Sounds
  - Part V Electricity and Magnetism: 22 Electrostatics | 23 Electric Current | 24 Magnetism | 25 Electromagnetic Induction
  - Part VI Light: 26 Properties of Light | 27 Color | 28 Reflection and Refraction | 29 Light Waves | 30 Light Emission | 31 Light Quanta
  - Part VII Atomic and Nuclear Physics: 32 The Atom and the Quantum | 33 Atomic Nucleus and Radioactivity | 34 Nuclear Fission and Fusion
  - Part VIII Relativity: 35 Special Theory of Relativity | 36 General Theory of Relativity
  - Appendices: A Systems of Measurement | B More About Motion | C Graphing | D More About Vectors | E Exponential Growth and Doubling Time
- Verified from: https://www.pearson.com/en-ca/subject-catalog/p/conceptual-physics/P200000006941 (fetched HTML; "Table of contents" block lists the parts and chapter titles above; part-to-chapter ranges 2–10, 11–14, 15–18, 19–21, 22–25, 26–31, 32–34, 35–36 as summarised from the same page).
- Not verified: original print-book ISBN/date (the page lists only digital/Mastering products).

## 3. Douglas C. Giancoli, "Physics: Principles with Applications"
- Author: Douglas C. Giancoli.
- Title: Physics: Principles with Applications (Pearson US/Canada catalogue now titles it "Physics: Principles and Applications"; the Global Edition keeps "Physics: Principles with Applications").
- Edition/year: 7th edition is the latest found (no 8th edition in Pearson listings). Pearson US page shows the current eTextbook as "Published 31 December 2021, © 2022"; the Global Edition page shows "Published 30 June 2024, © 2024" (ISBN 9781292066875). Original 7th-edition print date (commonly cited as © 2014) is NOT shown on the fetched pages.
- Publisher: Pearson.
- Level: introductory college, algebra-based (life-science/pre-med); also marketed to schools for AP (a Pearson school AP catalogue page appeared in search results; not fetched).
- Open: no (commercial).
- Contents (33 chapters; Vol. 1 = ch. 1–15, Vol. 2 = ch. 16–33):
  1 Introduction, Measurement, Estimating | 2 Describing Motion: Kinematics in One Dimension | 3 Kinematics in Two Dimensions; Vectors | 4 Dynamics: Newton's Laws of Motion | 5 Circular Motion; Gravitation | 6 Work and Energy | 7 Linear Momentum | 8 Rotational Motion | 9 Static Equilibrium; Elasticity and Fracture | 10 Fluids | 11 Oscillations and Waves | 12 Sound | 13 Temperature and Kinetic Theory | 14 Heat | 15 The Laws of Thermodynamics | 16 Electric Charge and Electric Field | 17 Electric Potential | 18 Electric Currents | 19 DC Circuits | 20 Magnetism | 21 Electromagnetic Induction and Faraday's Law | 22 Electromagnetic Waves | 23 Light: Geometric Optics | 24 The Wave Nature of Light | 25 Optical Instruments | 26 The Special Theory of Relativity | 27 Early Quantum Theory and Models of the Atom | 28 Quantum Mechanics of Atoms | 29 Molecules and Solids | 30 Nuclear Physics and Radioactivity | 31 Nuclear Energy; Effects and Uses of Radiation | 32 Elementary Particles | 33 Astrophysics and Cosmology
  - Appendices: A Mathematical Review | B Selected Isotopes | C Rotating Frames of Reference; Inertial Forces; Coriolis Effect | D Molar Specific Heats for Gases, and the Equipartition of Energy | E Galilean and Lorentz Transformations
- Verified from: https://www.pearson.com/en-us/subject-catalog/p/physics-principles-and-applications/P200000006936 (TOC with "complete version includes Chapters 1-33", volume split, appendices); https://www.pearson.com/en-gb/subject-catalog/p/physics-principles-with-applications-global-edition/P200000004289/9781292066875 (same 33 chapter titles, title "Physics: Principles with Applications, Seventh Edition"). Chapter numbers are by order in the list (consistent with "Chapters 1-33").

## Russian school textbooks — status in the official Federal list (ФПУ)

Official source checked: Федеральный перечень учебников, приказ Минпросвещения России от 22.06.2026 № 436 (replaces приказ от 26.06.2025 № 495 and its amendments), file "ФПУ от 22.06.2026 № 436.pdf" published at https://fpu.edu.ru (document list via https://fpu.edu.ru/public/api/v1/document-categories ; PDF https://fpu.edu.ru/static/uploads/files/e95647148b094257bc322506e9be5161.pdf , scanned, 312 pp.; physics rows read visually on printed pages 113–135).
- ООО, item 1.1.2.12 "Физика (учебный предмет)" — exactly ONE line is listed (the 2022+ "single textbook" policy):
  - 1.1.2.12.1.1 «Физика: 7-й класс: базовый уровень: учебник; 3-е издание, переработанное» — Перышкин И.М., Иванов А.И. — АО «Издательство «Просвещение»» — ФГОС ООО (приказ № 287) — in the list since 21.09.2022 (№ 858) — valid until 31.08.2032.
  - 1.1.2.12.1.2 «Физика: 8-й класс: базовый уровень: учебник; 3-е издание, переработанное» — Перышкин И.М., Иванов А.И. — same.
  - 1.1.2.12.1.3 «Физика: 9-й класс: базовый уровень: учебник; 3-е издание, переработанное» — Перышкин И.М., Гутник Е.М., Иванов А.И. и другие — same.
  - => The classic А. В. Перышкин books (Дрофа «Вертикаль»; also re-issued by «Экзамен») are NOT in the current ФПУ. The current line is by И. М. Перышкин (not А. В.) and А. И. Иванов.
- СОО, item 1.1.3.9 "Физика (учебный предмет)":
  - 1.1.3.9.1.1 «Физика», 10 кл. — Мякишев Г.Я., Буховцев Б.Б., Сотский Н.Н.; под редакцией Парфентьевой Н.А. — Просвещение — ФГОС СОО (приказ № 413) — since 20.05.2020 (№ 254) — until 31.08.2030.
  - 1.1.3.9.1.2 «Физика», 11 кл. — Мякишев Г.Я., Буховцев Б.Б., Чаругин В.М.; под редакцией Парфентьевой Н.А. — same.
  - 1.1.3.9.2.1 / 1.1.3.9.2.2 «Физика; углублённое обучение», 10 / 11 кл. — Касьянов В.А. — ООО «ДРОФА»; АО «Издательство «Просвещение»» — since 20.05.2020 (№ 254) — until 31.08.2030.
  - => In the current ФПУ the Мякишев line is the basic-level physics textbook (the book itself says "базовый и углублённый уровни"), and Касьянов is listed only for углублённое обучение.

## 4. Перышкин — «Физика» 7, 8, 9 класс
### 4a. Current ФПУ line: И. М. Перышкин, А. И. Иванов (7, 8); И. М. Перышкин, Е. М. Гутник, А. И. Иванов и другие (9)
- Title: «Физика. 7 класс. Базовый уровень» / «Физика. 8 класс. Базовый уровень» / «Физика. 9 класс. Базовый уровень». Series «Физика. Перышкин-Иванов. 7-9 классы».
- Edition/year verified: 6-е издание, стереотипное, Просвещение, 2026 (Labirint cards 911720 / 924474 / 924476: 7 кл. 240 pp., ISBN incl. 978-5-09-127893-4; 8 кл. 256 pp., 978-5-09-127894-1; 9 кл. 352 pp., 978-5-09-127895-8). Annotation: «Разработан в соответствии с требованиями ФГОС ООО (приказ № 287 от 31.05.2021, в ред. приказа № 31 от 22.01.2024)»; «Содержание учебника полностью соответствует примерной рабочей программе». First appeared 2022 (Litres e-book release 09.10.2022; Litres e-editions show "4-е издание, стереотипное", 2024: ISBN 978-5-09-116504-3 / -116505-0 / -116506-7). ФПУ row says 3-е издание, переработанное.
- Publisher: АО «Издательство «Просвещение»». Level: ООО, базовый уровень, 7–9 кл. Open: no.
- Contents: NOT VERIFIED. Publisher pages (prosv.ru, shop.prosv.ru, media.prosv.ru) redirect to an identity check and could not be read; Labirint/Litres show annotation only, no «Содержание». The publisher states the book follows the примерная (now федеральная) рабочая программа, so its chapter order should mirror the ФРП grade sections in item 8 — this is an inference, not a verified TOC.
- Verified from: ФПУ PDF above (authors, titles, edition in list, validity); https://www.labirint.ru/books/911720/ , https://www.labirint.ru/books/924474/ , https://www.labirint.ru/books/924476/ (edition 6, 2026, ISBN, annotation); https://www.litres.ru/book/a-i-ivanov/fizika-7-klass-68297840/ (and -8-klass-68297858, -9-klass-68297876) (e-edition data).

### 4b. Classic А. В. Перышкин line (Дрофа «Вертикаль» → Просвещение/Дрофа; now re-issued by «Экзамен»; NOT in the current ФПУ)
- Authors: А. В. Перышкин (7, 8); А. В. Перышкин, Е. М. Гутник (9). Level: ООО. Open: no.
- Editions verified (Labirint cards): 7 кл. — 9-е изд., переработанное, Просвещение/Дрофа, 2019, 224 pp. (card 352853); 9 кл. (Перышкин, Гутник) — 7-е изд., переработанное, Просвещение/Дрофа, 2019, 352 pp. (card 436176); «Экзамен» re-issues: 8 кл. 5-е изд., 2022 (726041); 9 кл. 5-е изд., 2022 (726042); 7 кл. 7-е изд., переработанное и дополненное, 2023 (970646, ISBN 978-5-377-19303-6); 8 кл. «учебное пособие» 7-е изд., 2025 (1016982).
- Contents — section (глава) list from the publisher annotations (chapter level only, no paragraphs):
  - 7 кл.: Введение | Первоначальные сведения о строении вещества | Взаимодействие тел | Давление твёрдых тел, жидкостей и газов | Работа и мощность. Энергия
  - 8 кл. (Экзамен 2022, 5-е изд.): Тепловые явления | Электрические явления | Электромагнитные явления | Световые явления. (The Экзамен 2025 edition lists only the first three — light moved to grade 9 as in the new ФРП.)
  - 9 кл. (Экзамен 2022, 5-е изд.): Законы взаимодействия и движения тел | Механические колебания и волны | Электромагнитное поле и электромагнитные волны | Строение атома и атомного ядра. Использование атомной энергии | Строение и эволюция Вселенной
- Verified from: https://www.labirint.ru/books/970646/ ; https://www.labirint.ru/books/726041/ ; https://www.labirint.ru/books/726042/ ; https://www.labirint.ru/books/1016982/ ; https://www.labirint.ru/books/352853/ ; https://www.labirint.ru/books/436176/ (annotations "Издание включает разделы: …").
- Not verified: that the Дрофа (Вертикаль) 2019 editions use exactly the same chapter titles as the Экзамен re-issues (their cards show no section list); in common knowledge they do.

## 5. Г. Я. Мякишев и др. — «Физика. 10 класс», «Физика. 11 класс» (series «Физика. Классический курс»)
- Authors: 10 кл. — Г. Я. Мякишев, Б. Б. Буховцев, Н. Н. Сотский; 11 кл. — Г. Я. Мякишев, Б. Б. Буховцев, В. М. Чаругин; под ред. Н. А. Парфентьевой.
- Title: «Физика. 10 класс. Базовый и углублённый уровни» / «Физика. 11 класс. Базовый и углублённый уровни» (Labirint titles; ФПУ row: «Физика»).
- Edition/year verified: 10 кл. — 13-е издание, стереотипное, Просвещение, 2026, 432 pp. (ISBN incl. 978-5-09-127999-3); 11 кл. — 14-е издание, стереотипное, Просвещение, 2026, 436 pp. Annotation: ФГОС СОО, «реализует базовый и углублённый уровни».
- Publisher: Просвещение. Level: СОО 10–11; in ФПУ as the basic physics line. Open: no.
- Contents: NOT VERIFIED (no fetched page shows the chapter list). The 11 кл. annotation says the book covers "теория относительности, квантовая теория, физика атомного ядра и элементарных частиц, строение Вселенной" (note: the same opening sentence — about the book that "completes" the line — also appears on the 10 кл. card, evidently copied from the 11 кл. annotation).
- Verified from: ФПУ PDF (rows 1.1.3.9.1.1–1.1.3.9.1.2); https://www.labirint.ru/books/690223/ ; https://www.labirint.ru/books/690224/
- Related, not in ФПУ main line: Мякишев, Синяков — углублённый уровень, separate volumes «Механика. 10», «Молекулярная физика. Термодинамика. 10», «Электродинамика. 10–11», «Оптика. Квантовая физика. 11» (Просвещение; seen in Labirint search results only, now sold as «учебное пособие»).

## 6. В. А. Касьянов — «Физика. 10 класс», «Физика. 11 класс» (базовый and углублённый)
- Author: В. А. Касьянов. Publisher: Дрофа → Просвещение/Дрофа → Просвещение. Level: СОО 10–11. Open: no.
- Editions verified (Labirint cards):
  - Углублённый: 10 кл. — 14-е изд., стереотипное, Просвещение, 2026 (406138); 11 кл. — 13-е изд., стереотипное, Просвещение, 2025 (445456). ФПУ: «Физика; углублённое обучение», rows 1.1.3.9.2.1–2.
  - Базовый: 10 кл. — 11-е изд., стереотипное, Просвещение/Дрофа, 2022, 304 pp. (409139); 11 кл. — 10-е изд., стереотипное, Просвещение/Дрофа, 2022, 288 pp. (766494). The базовый pair is NOT in the current ФПУ.
- Contents — main sections (разделы) only, from the publisher annotations; the same section names for базовый and углублённый:
  - 10 кл.: Механика | Молекулярная физика | Электростатика
  - 11 кл.: Электродинамика | Электромагнитное излучение | Физика высоких энергий | Элементы астрофизики
- Verified from: https://www.labirint.ru/books/406138/ ; https://www.labirint.ru/books/445456/ ; https://www.labirint.ru/books/409139/ ; https://www.labirint.ru/books/766494/ (annotations "включает следующие основные разделы: …"); ФПУ PDF.
- Not verified: chapter-level TOC (a retailer preview PDF of 11 кл. базовый contains only the first chapter pages, no TOC).

## 7. Г. С. Ландсберг (ред.) — «Элементарный учебник физики», 3 тома
- Author/editor: Labirint lists "Ландсберг Григорий Самуилович" as author; the book is traditionally "под редакцией академика Г. С. Ландсберга" (multi-author) — the editor role is NOT shown on the fetched pages.
- Title: «Элементарный учебник физики. В 3 томах».
- Editions verified: Т. 1 — 15-е издание, исправленное, Физматлит, 2026 (ISBN 978-5-9221-1256-7, 978-5-9221-1894-1); Т. 2 — 16-е издание, Физматлит, 2026 (ISBN 978-5-9221-1610-7); Т. 3 — 15-е издание, Физматлит, 2025 (ISBN 978-5-9221-1591-9).
- Level: upper secondary / self-study / university entrance ("для старшеклассников и учителей … готовящихся к поступлению в вуз"). Open: no.
- Contents (from the «Содержание» block embedded in the Labirint product pages):
  - Том 1. Механика. Теплота. Молекулярная физика
    - Раздел первый. Механика: I Кинематика | II Динамика | III Статика | IV Работа и энергия | V Криволинейное движение | VI Движение в неинерциальных системах отсчёта и силы инерции | VII Гидростатика | VIII Аэростатика | IX Гидродинамика и аэродинамика
    - Раздел второй. Теплота. Молекулярная физика: X Тепловое расширение твёрдых и жидких тел | XI Работа. Теплота. Закон сохранения энергии | XII Молекулярная теория | XIII Свойства газов | XIV Свойства жидкостей | XV Свойства твёрдых тел. Переход тел из твёрдого состояния в жидкое | XVI Упругость и прочность | XVII Свойства паров | XVIII Физика атмосферы | XIX Тепловые машины
  - Том 2. Электричество и магнетизм: I Электрические заряды | II Электрическое поле | III Постоянный электрический ток | IV Тепловое действие тока | V Прохождение электрического тока через электролиты | VI Химические и тепловые генераторы тока | VII Прохождение электрического тока через металлы | VIII Прохождение электрического тока через газы | IX Прохождение электрического тока через полупроводники | X Основные магнитные явления | XI Магнитное поле | XII Магнитные поля электрических токов | XIII Магнитное поле Земли | XIV Силы, действующие в магнитном поле на проводники с током | XV Электромагнитная индукция | XVI Магнитные свойства тел | XVII Переменный ток | XVIII Электрические машины: генераторы, двигатели, электромагниты (two typos on the page silently corrected: «отка»→«тока», «Магнитне»→«Магнитные»)
  - Том 3. Колебания и волны. Оптика. Атомная и ядерная физика: Раздел первый. Колебания и волны | Раздел второй. Геометрическая оптика | Раздел третий. Физическая оптика | Раздел четвёртый. Атомная и ядерная физика | Заключение (chapter list of vol. 3 not shown on the page)
- Verified from: https://www.labirint.ru/books/511985/ (т. 1), https://www.labirint.ru/books/509779/ (т. 2), https://www.labirint.ru/books/509780/ (т. 3).
- Not verified: chapter list of vol. 3; editor/co-author list.

## 8. Russian official curriculum: ФГОС + Федеральная рабочая программа (ФРП) по физике
- Standards (verified as listed on the official portal «Единое содержание общего образования», https://edsoo.ru/normativnye-dokumenty-_/ ):
  - ФГОС ООО — приказ Минпросвещения России от 31.05.2021 № 287 (зарег. 05.07.2021 № 64101), with later amendments (e.g. приказ № 31 от 22.01.2024). PDF on edsoo.ru (scan): /wp-content/uploads/2023/08/Приказ-№-287-от-31.05.2021-ФГОС_ООО.pdf
  - ФГОС СОО — приказ Минобрнауки России от 17.05.2012 № 413, in the version of приказ Минпросвещения от 12.08.2022 № 732 (зарег. 12.09.2022 № 70034) and later amendments.
  - The ФГОС fixes required learning outcomes ("предметные результаты"), not a chapter list; the per-grade content is set out in the ФРП (part of the федеральная образовательная программа, ФОП ООО / ФОП СОО). The ФРП text itself says it is built on the ФГОС requirements and is issued "с целью оказания методической помощи" to teachers. Not verified here: the exact legal force of the physics ФРП for a school's own programme (by my understanding, direct use is compulsory only for a few subjects, with others required to be no lower than the ФРП — check before quoting).
  - Not verified: wording of the physics outcomes in the ФГОС text (edsoo PDF is a scan; not OCR'd).
- Open: yes (official public documents, free to read).

### 8a. ФРП ООО «Физика» 7–9 классы, базовый уровень (edsoo.ru, "Москва – 2025")
- Hours: 238 total — 7 кл. 68 h (2/week), 8 кл. 68 h (2/week), 9 кл. 102 h (3/week).
- Содержание обучения (sections, hours from the тематическое планирование):
  - 7 класс: 1 Физика и ее роль в познании окружающего мира (6) | 2 Первоначальные сведения о строении вещества (5) | 3 Движение и взаимодействие тел (21) | 4 Давление твердых тел, жидкостей и газов (21) | 5 Работа и мощность. Энергия (12) | резерв 3
  - 8 класс: 1 Тепловые явления (28) | 2 Электрические и магнитные явления (37) | резерв 3
  - 9 класс: 1 Механические явления (40) | 2 Механические колебания и волны (15) | 3 Электромагнитное поле и электромагнитные волны (6) | 4 Световые явления (15) | 5 Квантовые явления (17; atom spectra, nucleus, radioactivity, nuclear reactions, energy of Sun and stars) | 6 Повторительно-обобщающий модуль (9)
  - Remarks: kinematics/dynamics proper (laws of Newton, momentum, energy conservation) are in grade 9; grade 7 is descriptive mechanics + pressure/Archimedes; optics moved to grade 9 (not 8); no relativity and no astronomy section at ООО (only "Источники энергии Солнца и звезд" inside квантовые явления).
- Verified from: https://edsoo.ru/rabochie-programmy/ (links) → https://edsoo.ru/wp-content/uploads/2025/07/2025_ooo_frp_fizika-7-9_baz.pdf (text: «СОДЕРЖАНИЕ ОБУЧЕНИЯ» 7/8/9 КЛАСС, «ТЕМАТИЧЕСКОЕ ПЛАНИРОВАНИЕ», «Итого по разделу»).

### 8b. ФРП ООО «Физика» 7–9 классы, углублённый уровень
- Hours: 340 — 7 кл. 102 (3/week), 8 кл. 102 (3/week), 9 кл. 136 (4/week).
- Sections: the same section titles per grade as the basic programme, with more hours and extra content (e.g. полупроводники, графен, вынужденные колебания/резонанс, ультразвук, ядерная энергетика):
  - 7 кл.: Физика и ее роль в познании окружающего мира (8) | Первоначальные сведения о строении вещества (7) | Движение и взаимодействие тел (34) | Давление твердых тел, жидкостей и газов (28) | Работа и мощность. Энергия (19)
  - 8 кл.: Тепловые явления (39) | Электрические и магнитные явления (58)
  - 9 кл.: Механические явления (63) | Механические колебания и волны (18) | Электромагнитное поле и электромагнитные волны (6) | Световые явления (16) | Квантовые явления (16) | Повторительно-обобщающий модуль (17)
- Verified from: https://edsoo.ru/wp-content/uploads/2025/07/2025_ooo_frp_fizika_7-9_ugl.pdf

### 8c. ФРП СОО «Физика» 10–11 классы, базовый уровень
- Hours: 136 — 10 кл. 68 (2/week), 11 кл. 68 (2/week).
- 10 класс: Раздел 1 Физика и методы научного познания (2) | Раздел 2 Механика (18): Кинематика; Динамика; Законы сохранения в механике | Раздел 3 Молекулярная физика и термодинамика (24): Основы МКТ; Основы термодинамики; Агрегатные состояния вещества. Фазовые переходы | Раздел 4 Электродинамика (22): Электростатика; Постоянный электрический ток. Токи в различных средах | резерв 2
- 11 класс: Электродинамика (11): Магнитное поле. Электромагнитная индукция | Колебания и волны (24): Механические и электромагнитные колебания; Механические и электромагнитные волны; Оптика | Основы специальной теории относительности (4) | Квантовая физика (15): Элементы квантовой оптики; Строение атома; Атомное ядро | Элементы астрономии и астрофизики (7) | Обобщающее повторение (4) | резерв 3
- Verified from: https://edsoo.ru/wp-content/uploads/2025/07/2025_soo_frp_fizika_10_11_baz.pdf

### 8d. ФРП СОО «Физика» 10–11 классы, углублённый уровень
- Hours: 340 — 10 кл. 170 (5/week), 11 кл. 170 (5/week).
- 10 класс: Научный метод познания природы (6) | Механика (35): Кинематика; Динамика; Статика твердого тела; Законы сохранения в механике | Молекулярная физика и термодинамика (49): Основы МКТ; Термодинамика. Тепловые машины; Агрегатные состояния вещества. Фазовые переходы | Электродинамика (54): Электрическое поле; Постоянный электрический ток; Токи в различных средах | Физический практикум (16) | резерв 10
- 11 класс: Электродинамика (27): Магнитное поле; Электромагнитная индукция | Колебания и волны (60): Механические колебания; Электромагнитные колебания; Механические и электромагнитные волны; Оптика | Основы СТО (5) | Квантовая физика (25): Корпускулярно-волновой дуализм; Физика атома; Физика атомного ядра и элементарных частиц | Элементы астрономии и астрофизики (12) | Физический практикум (16) | Обобщающее повторение (15) | резерв 10
- Verified from: https://edsoo.ru/wp-content/uploads/2025/07/2025_soo_frp_fizika_10_11_ugl.pdf

## 9. International official curricula

### 9a. IB Diploma Programme Physics — guide for first assessment 2025 (SL/HL)
- Body: International Baccalaureate Organization. Level: upper secondary (ages ~16–19), SL 150 h / HL 240 h overall; syllabus content 110 h SL / 180 h HL.
- Open: the subject brief is public; the full guide is not (IB programme resource centre / IB store).
- Themes and topics (• all students; •• all + additional HL content; ••• HL only); hours SL/HL per theme:
  - A Space, time and motion (27/42): A.1 Kinematics • | A.2 Forces and momentum • | A.3 Work, energy and power • | A.4 Rigid body mechanics ••• | A.5 Galilean and special relativity •••
  - B The particulate nature of matter (24/32): B.1 Thermal energy transfers • | B.2 Greenhouse effect • | B.3 Gas laws • | B.4 Thermodynamics ••• | B.5 Current and circuits •
  - C Wave behaviour (17/29): C.1 Simple harmonic motion •• | C.2 Wave model • | C.3 Wave phenomena •• | C.4 Standing waves and resonance • | C.5 Doppler effect ••
  - D Fields (19/38): D.1 Gravitational fields •• | D.2 Electric and magnetic fields •• | D.3 Motion in electromagnetic fields • | D.4 Induction •••
  - E Nuclear and quantum physics (23/39): E.1 Structure of the atom •• | E.2 Quantum physics ••• | E.3 Radioactive decay •• | E.4 Fission • | E.5 Fusion and stars •
  - Experimental programme (40/60): practical work 20/40, collaborative sciences project 10/10, scientific investigation 10/10. No options any more (Paper 3 options removed). Assessment: Paper 1 (1A MCQ + 1B data-based), Paper 2; internal scientific investigation 20%.
  - Remarks: circuits sit inside "particulate nature of matter"; special relativity and thermodynamics are HL-only; astrophysics reduced to E.5 "Fusion and stars".
- Verified from: IB "DP physics subject brief", First assessment 2025, © IBO 2022 — official URL https://ibo.org/globalassets/new-structure/recognition/pdfs/dp_sciences_physics_subject-brief_jan_2022_e.pdf (403/Cloudflare to scripts), read via the Internet Archive copy http://web.archive.org/web/20260821140742/https://ibo.org/globalassets/new-structure/recognition/pdfs/dp_sciences_physics_subject-brief_jan_2022_e.pdf (table "Recommended teaching hours").
- Not verified: sub-topic wording inside the full guide (not public).

### 9b. College Board AP Physics (course framework revised for 2024–25)
- Body: College Board. Level: US high school, college-level courses. Open: course pages and CED PDFs are free to read.
- AP Physics 1: Algebra-Based (8 units; multiple-choice weighting): 1 Kinematics (10–15%) | 2 Force and Translational Dynamics (18–23%) | 3 Work, Energy, and Power (18–23%) | 4 Linear Momentum (10–15%) | 5 Torque and Rotational Dynamics (10–15%) | 6 Energy and Momentum of Rotating Systems (5–8%) | 7 Oscillations (5–8%) | 8 Fluids (10–15%)
- AP Physics 2: Algebra-Based (units numbered on from Physics 1): 9 Thermodynamics (15–18%) | 10 Electric Force, Field, and Potential (15–18%) | 11 Electric Circuits (15–18%) | 12 Magnetism and Electromagnetism (12–15%) | 13 Geometric Optics (12–15%) | 14 Waves, Sound, and Physical Optics (12–15%) | 15 Modern Physics (12–15%; radioactive decay, E = mc², blackbody radiation, wave–particle properties, photoelectric effect)
- AP Physics C: Mechanics (calculus-based): 1 Kinematics (10–15%) | 2 Force and Translational Dynamics (20–25%) | 3 Work, Energy, and Power (15–25%) | 4 Linear Momentum (10–20%) | 5 Torque and Rotational Dynamics (10–15%) | 6 Energy and Momentum of Rotating Systems (10–15%) | 7 Oscillations (10–15%)
- AP Physics C: Electricity and Magnetism (units numbered on from C: Mechanics): 8 Electric Charges, Fields, and Gauss's Law (15–25%) | 9 Electric Potential (10–20%) | 10 Conductors and Capacitors (10–15%) | 11 Electric Circuits (15–25%) | 12 Magnetic Fields and Electromagnetism (10–20%) | 13 Electromagnetic Induction (10–20%)
- Remarks: the 2024–25 revision moved Fluids into Physics 1 (Unit 8) and all waves/sound into Physics 2 (Unit 14); no relativity unit in any AP physics course beyond E = mc² in Physics 2 Unit 15; no astrophysics.
- Verified from: https://apstudents.collegeboard.org/courses/ap-physics-1-algebra-based , .../ap-physics-2-algebra-based , .../ap-physics-c-mechanics , .../ap-physics-c-electricity-and-magnetism ("Course Content" unit lists with exam weightings); course-at-a-glance PDFs https://apcentral.collegeboard.org/media/pdf/ap-physics-1-course-at-a-glance.pdf (and -2-, -c-mechanics-, -c-electricity-and-magnetism-), © 2026 College Board, consistent unit numbering.
- Not verified directly: the College Board "AP Physics Revisions for 2024-25" page (https://apcentral.collegeboard.org/courses/ap-physics/revisions-2024-25) returned 403; the "effective fall 2024" CED title and the move of fluids/waves are known only from search-result snippets of College Board pages.

### 9c. AQA A-level Physics (7408), England
- Body: AQA. Specification for first teaching 2015 (spec PDF on the page dated 06 Jan 2017). Level: A-level (ages 16–18); AS = sections 3.1–3.5. Open: yes, free to read online.
- Subject content:
  - 3.1 Measurements and their errors: 3.1.1 SI units and prefixes | 3.1.2 Limitation of physical measurements | 3.1.3 Estimation of physical quantities
  - 3.2 Particles and radiation: 3.2.1 Particles (constituents of the atom; stable/unstable nuclei; particles, antiparticles, photons; particle interactions; classification; quarks; conservation laws) | 3.2.2 Electromagnetic radiation and quantum phenomena (photoelectric effect; electron–atom collisions; energy levels and photon emission; wave–particle duality)
  - 3.3 Waves: 3.3.1 Progressive and stationary waves | 3.3.2 Refraction, diffraction and interference
  - 3.4 Mechanics and materials: 3.4.1 Force, energy and momentum (scalars/vectors, moments, straight-line motion, projectiles, Newton's laws, momentum, work/energy/power, conservation of energy) | 3.4.2 Materials (bulk properties of solids, Young modulus)
  - 3.5 Electricity: 3.5.1 Current electricity (basics, I–V characteristics, resistivity, circuits, potential divider, EMF and internal resistance)
  - 3.6 Further mechanics and thermal physics (A-level only): 3.6.1 Periodic motion (circular motion, SHM, SH systems, forced vibrations and resonance) | 3.6.2 Thermal physics (thermal energy transfer, ideal gases, molecular kinetic theory)
  - 3.7 Fields and their consequences (A-level only): 3.7.1 Fields | 3.7.2 Gravitational fields | 3.7.3 Electric fields | 3.7.4 Capacitance | 3.7.5 Magnetic fields (incl. induction, AC, transformer)
  - 3.8 Nuclear physics (A-level only): 3.8.1 Radioactivity (Rutherford scattering, α/β/γ, decay, instability, nuclear radius, mass and energy, induced fission, safety)
  - Options (one of 3.9–3.13, Paper 3 Section B): 3.9 Astrophysics (telescopes; classification of stars; cosmology) | 3.10 Medical physics (eye; ear; biological measurement/ECG; non-ionising imaging; X-ray imaging; radionuclide imaging and therapy) | 3.11 Engineering physics (rotational dynamics; thermodynamics and engines) | 3.12 Turning points in physics (discovery of the electron; wave–particle duality; special relativity) | 3.13 Electronics (semiconductor devices; analogue/digital signals; analogue processing; op-amps; digital processing; data communication)
  - Assessment: Paper 1 = 3.1–3.5 + 3.6.1; Paper 2 = 3.6.2, 3.7, 3.8; Paper 3 = practical skills + one option.
  - Remark: in AQA, special relativity appears only in the optional section 3.12; astrophysics only as option 3.9.
- Verified from: https://www.aqa.org.uk/subjects/physics/a-level/physics-7408/specification (index 3.1–3.13), https://www.aqa.org.uk/subjects/physics/a-level/physics-7408/specification/specification-at-a-glance (papers, options), and the 13 subject-content pages .../specification/subject-content/<section> (sub-headings).

## Common section order at school level (synthesis of the items above)

Sequence per source (main blocks only; → = order of teaching in the book/programme):
- OpenStax Physics (US HS): intro → mechanics (1D/2D kinematics, Newton, circular/rotation, gravitation, momentum, energy) → special relativity → heat & thermodynamics → waves, sound → light, mirrors/lenses, diffraction/interference → electrostatics, circuits, magnetism → quantum nature of light → atom (+ nuclear) → particle physics.
- OpenStax College Physics 2e / AP 2e; Giancoli 7e (algebra-based college): mechanics (+ statics, rotation, fluids) → [CP2e: thermal → oscillations/waves/sound] or [Giancoli: oscillations/waves/sound → thermal] → electricity (charge, field, potential, current, DC circuits) → magnetism, induction (+AC) → EM waves → geometric optics, wave optics, instruments → special relativity → quantum, atomic (+molecules/solids in Giancoli) → nuclear (+ applications) → particles → cosmology/astrophysics ("Frontiers" / "Astrophysics and Cosmology").
- Hewitt (conceptual): mechanics → properties of matter → heat → sound (vibrations and waves) → electricity & magnetism → light (incl. light quanta) → atomic & nuclear → special AND general relativity (only text here with GR).
- Russian ООО (ФРП 2025 = current Перышкин–Иванов line; classic А. В. Перышкин is close): spiral course. 7: physics & method → structure of matter → motion and interaction (descriptive) → pressure, Archimedes → work, power, energy, simple machines. 8: thermal phenomena (MKT, heat transfer, phase changes, heat engines) → electric and magnetic phenomena (to induction, generators). 9: mechanics proper (kinematics, Newton, gravitation, momentum, energy) → mechanical oscillations and waves, sound → EM field and EM waves → light/optics → quantum phenomena (spectra, nucleus, radioactivity, nuclear reactions, energy of stars). Classic А. В. Перышкин 9 ends with «Строение и эволюция Вселенной»; the 2025 ФРП ООО has no astronomy section.
- Russian СОО (ФРП 2025; Мякишев «Классический курс»; Касьянов): 10: method → mechanics (kinematics, dynamics, conservation laws; statics in углублённый) → molecular physics & thermodynamics (MKT, thermodynamics, phase transitions) → electrostatics, DC current, current in media. 11: magnetic field, induction → oscillations and waves treated jointly for mechanical + EM (incl. AC, EM waves) → optics → special relativity → quantum physics (photons, atom, nucleus, elementary particles) → astronomy/astrophysics (+ обобщающее повторение; физический практикум in углублённый). Касьянов groups 11 as Электродинамика → Электромагнитное излучение → Физика высоких энергий → Элементы астрофизики (the name suggests EM waves + optics; chapter content not verified).
- Ландсберг (3 vols): mechanics (incl. hydro/aero-statics and -dynamics, non-inertial frames) → heat, molecular physics → electricity and magnetism (incl. conduction in electrolytes/metals/gases/semiconductors, AC, machines) → oscillations and waves → geometric optics → physical optics → atomic and nuclear physics.
- IB DP 2025: A space, time and motion (kinematics, forces/momentum, energy; rigid bodies and relativity HL) → B particulate nature of matter (thermal, greenhouse, gas laws, thermodynamics HL, circuits) → C wave behaviour (SHM, waves, standing waves, Doppler) → D fields (gravitational, electric/magnetic, motion in fields, induction HL) → E nuclear and quantum (atom, quantum HL, decay, fission, fusion and stars).
- AP (2024–25): Physics 1 = mechanics incl. rotation, SHM, fluids; Physics 2 = thermodynamics → electrostatics → circuits → magnetism/induction → geometric optics → waves, sound, physical optics → modern physics. Physics C = calculus mechanics (7 units) + E&M (6 units). No relativity unit; no astrophysics.
- AQA A-level 7408 (spec order, not necessarily teaching order): measurements → particles and radiation (quarks, photoelectric effect — placed first) → waves → mechanics and materials → electricity → circular motion, SHM, thermal physics → fields (gravitational, electric, capacitance, magnetic, induction) → nuclear → one option: astrophysics / medical / engineering / turning points (incl. special relativity) / electronics.

Near-universal at school level (present in every source above):
- Kinematics; forces and Newton's laws; work–energy and energy conservation; momentum and its conservation; gravitation / circular motion (orbits).
- Oscillations (SHM, pendulum/spring) and mechanical waves incl. sound/resonance.
- Heat and temperature, kinetic-molecular model, gas laws, first law / heat engines (AP keeps thermo in Physics 2; IB puts thermodynamics proper in HL).
- Electrostatics (charge, Coulomb, field, potential); DC current and circuits; magnetic field and force on currents/charges; electromagnetic induction.
- EM waves and the spectrum; geometric optics (reflection, refraction, lenses); wave optics (interference, diffraction).
- Photon / photoelectric effect; atomic structure and spectra; radioactivity and nuclear energy (fission/fusion).

Common but level- or system-dependent (candidates for optional/advanced tracks):
- Special relativity: core in Russian grade 11 (both levels), OpenStax, CP2e, Giancoli, Hewitt; HL-only in IB; option-only in AQA (3.12); absent from AP (only E = mc² in Physics 2). Absent at Russian ООО.
- Rotational dynamics, torque, angular momentum: strong in US (AP 1 and C, CP2e, Giancoli), IB HL-only (A.4), AQA option (3.11); Russian basic level has only moments/statics.
- Fluids (pressure, Archimedes, Bernoulli): Russian grade 7, Landsberg, US college texts, AP 1 (since 2024–25); no fluids section in IB 2025 or AQA 7408.
- Astronomy/astrophysics/cosmology: Russian СОО (own section), Касьянов, classic Перышкин 9, Giancoli last chapter, CP2e "Frontiers", IB E.5 only (fusion and stars), AQA option 3.9; absent from AP and OpenStax HS.
- Particle physics: OpenStax HS, CP2e, Giancoli, AQA (core, first section!), Russian 11 (elementary particles inside quantum/nuclear), Касьянов «Физика высоких энергий»; no particle-physics unit/topic in AP or IB 2025.
- Materials/elasticity: Giancoli, CP2e, AQA 3.4.2, Landsberg; marginal elsewhere. Semiconductors/electronics: Landsberg, AQA option, Russian углублённый (currents in media). General relativity: Hewitt only. Medical physics: CP2e, Giancoli applications, AQA option.
- Measurement, uncertainty and scientific method as an explicit opening section: AQA 3.1, IB "tools", Russian ФРП ("Физика и её роль в познании…", "методы научного познания"), OpenStax ch. 1.

Ordering regularities useful for a README:
1. Mechanics always comes first (AQA's numbering is the one exception on paper).
2. Thermal/molecular physics usually follows mechanics (before E&M) — Russian ООО (grade 8) and СОО (grade 10), CP2e, Giancoli, Hewitt, OpenStax, IB, AP (thermo opens Physics 2). AQA is the exception (thermal physics 3.6.2 after electricity 3.5).
3. The placement of oscillations/waves is the main point of divergence: US college texts put mechanical waves and sound before E&M; Russian СОО and Касьянов put a unified "колебания и волны" (mechanical + electromagnetic, incl. AC) AFTER electromagnetism and right before optics; IB keeps "Wave behaviour" as its own theme between matter and fields.
4. Optics normally follows E&M (as the application of EM waves) — Russian СОО, CP2e, Giancoli, Hewitt, AP 2; OpenStax HS is the exception (light and optics before electrostatics). Russian ООО puts light in grade 9 after EM waves.
5. Special relativity sits between classical E&M/optics and quantum physics in most texts (Russian 11, CP2e, Giancoli); OpenStax HS and IB attach it to mechanics; Hewitt puts it at the very end.
6. Every source ends with the same tail: quantum (photon) → atom → nucleus → (particles) → (astrophysics/cosmology).
7. Audience ladder visible in the official programmes: Russian ООО 7–9 (phenomenological, spiral; 238 h basic / 340 h advanced) → Russian СОО 10–11 (136 h basic / 340 h advanced) ≈ AP 1–2 / IB SL–HL / A-level → intro college (CP2e, Giancoli; calculus versions: AP C).

---

# Appendix B. University physics textbooks — verified tables of contents

Purpose: structure the public README of an open physics engine (browser visualizations) by physics section and audience level.
Method: WebSearch + WebFetch of publisher pages, open texts, catalogues. No full texts of copyrighted books downloaded.
Status: COMPLETE (2026-11-12). Items appear in the order they were researched (3, 4, 1, 2, 5, 6, 7, 11, 8, 9, 10, then S1–S6, open alternatives, summary).

## At a glance (verification status)

| # | Book | Edition checked | Contents verified from | Open? |
|---|------|-----------------|------------------------|-------|
| 1 | Halliday/Resnick/Walker, Fundamentals of Physics | 12th (Extended), Wiley ©2021 | two bookstore pages (Wiley page 403) | no |
| 2 | Young & Freedman, University Physics w/ Modern Physics | 16th, Pearson 2026 (©2027) | Pearson product page | no |
| 3 | OpenStax University Physics V1–V3 | 1st (2016), live 2026 version | openstax.org book pages + CMS API | yes, **CC BY-NC-SA 4.0** (not CC BY) |
| 4 | Feynman Lectures I–III | online ed. 2013 | Wikipedia (caltech site blocked 403) | free to read; copyright, no copying |
| 5 | Berkeley Physics Course 1–5 | 1965–71; Purcell & Morin 3rd 2013 | only Purcell 3rd verified (CUP page) | unclear → treat as not open |
| 6 | Griffiths, Intro to Electrodynamics | 5th, CUP 2023 | CUP page | no |
| 7 | Griffiths & Schroeter, Intro to QM | 3rd, CUP 2018 | CUP page | no |
| 8 | Kittel, Intro to Solid State Physics | 8th, Wiley 2004 | Wiley TOC PDF | no |
| 9 | Goldstein/Poole/Safko, Classical Mechanics | 3rd, Pearson ©2002 | Pearson page | no |
| 10 | Jackson, Classical Electrodynamics | 3rd, Wiley 1998/99 | Wiley TOC PDF (scanned pages) | no |
| 11 | Sakurai & Napolitano, Modern QM | 3rd, CUP 2020 | CUP page | no |
| S1 | Schroeder, Thermal Physics | OUP reissue 2021 | author's book site | no |
| S2 | Hecht, Optics | 5th, Pearson | Pearson page | no |
| S3 | Taylor & Wheeler, Spacetime Physics; Taylor/Wheeler/Bertschinger, Exploring Black Holes 2e; Hartle, Gravity | 2nd 1992; EBH2e online; CUP 2021 | eftaylor.com; CUP page | **Spacetime Physics & EBH2e: yes, CC BY 4.0**; Hartle no |
| S4 | Krane, Intro Nuclear Physics; Griffiths, Intro to Elementary Particles | Wiley 1991 ("3rd" per Wiley); 2nd rev. Wiley-VCH 2008 | Wiley pages / TOC PDF | no |
| S5 | Carroll & Ostlie, Modern Astrophysics | 2nd, CUP 2017 | CUP page | no |
| S6 | Kundu et al., Fluid Mechanics | 7th, Elsevier 2024 | Elsevier page | no |
| — | Crowell, Light and Matter | rev. 2020 | open text (archive.org) | yes, CC BY-SA 3.0 (IA metadata says 4.0) |
| — | MIT OCW 8.01SC/8.02/8.03SC/8.04/8.044 | 2013–2019 runs | ocw.mit.edu | yes, CC BY-NC-SA 4.0 |
| — | LibreTexts Physics | — | phys.libretexts.org | per-book licences vary (not checked) |

## Introductory university level

### 3. OpenStax "University Physics", Volumes 1–3
- Authors: Samuel J. Ling, Jeff Sanny, William Moebs (senior contributing authors; per OpenStax CMS record), with many contributing authors
- Title: University Physics Volume 1 / Volume 2 / Volume 3
- Edition / year: 1st edition (no "2e"); publish dates per OpenStax CMS: Vol 1 2016-09-19, Vol 2 2016-10-06, Vol 3 2016-09-29; live web version checked = archive 20260604.144757, content version d0ed34a
- Publisher: OpenStax (Rice University)
- Level: introductory, calculus-based, 2–3 semesters (science and engineering majors)
- Open: YES — read online free; PDF free.
  - Licence: **CC BY-NC-SA 4.0** (https://creativecommons.org/licenses/by-nc-sa/4.0/). NOTE: this contradicts the brief's assumption "CC BY 4.0". The current book pages state: "University Physics is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA) license, which means that you can non-commercially distribute, remix, and build upon the content, as long as you provide attribution to OpenStax…". The CMS API gives the same licence for all three volumes (and for College Physics 2e). Older printings/versions were CC BY 4.0 (from memory, not re-verified here) — for reuse of figures/text in the engine, treat the current licence as NC-SA.
  - URLs: https://openstax.org/details/books/university-physics-volume-1 , …-volume-2 , …-volume-3 ; reader: https://openstax.org/books/university-physics-volume-1/pages/1-introduction (same pattern for 2, 3); PDF Vol 1: https://assets.openstax.org/oscms-prodcms/media/documents/university-physics-volume-1_-_WEB.pdf
- Print ISBN Vol 1: 978-1-938168-27-7; digital 978-1-947172-20-3

Contents:
- Vol 1 — Unit Mechanics: 1 Units and Measurement; 2 Vectors; 3 Motion Along a Straight Line; 4 Motion in Two and Three Dimensions; 5 Newton's Laws of Motion; 6 Applications of Newton's Laws; 7 Work and Kinetic Energy; 8 Potential Energy and Conservation of Energy; 9 Linear Momentum and Collisions; 10 Fixed-Axis Rotation; 11 Angular Momentum; 12 Static Equilibrium and Elasticity; 13 Gravitation; 14 Fluid Mechanics.
  Unit Waves and Acoustics: 15 Oscillations; 16 Waves; 17 Sound.
- Vol 2 — Unit Thermodynamics: 1 Temperature and Heat; 2 The Kinetic Theory of Gases; 3 The First Law of Thermodynamics; 4 The Second Law of Thermodynamics.
  Unit Electricity and Magnetism: 5 Electric Charges and Fields; 6 Gauss's Law; 7 Electric Potential; 8 Capacitance; 9 Current and Resistance; 10 Direct-Current Circuits; 11 Magnetic Forces and Fields; 12 Sources of Magnetic Fields; 13 Electromagnetic Induction; 14 Inductance; 15 Alternating-Current Circuits; 16 Electromagnetic Waves.
- Vol 3 — Unit Optics: 1 The Nature of Light; 2 Geometric Optics and Image Formation; 3 Interference; 4 Diffraction.
  Unit Modern Physics: 5 Relativity; 6 Photons and Matter Waves; 7 Quantum Mechanics; 8 Atomic Structure; 9 Condensed Matter Physics; 10 Nuclear Physics; 11 Particle Physics and Cosmology.
- Appendices (each volume): A Units; B Conversion Factors; C Fundamental Constants; D Astronomical Data; E Mathematical Formulas; F Chemistry; G The Greek Alphabet; Answer Key; Index.

Verified from:
- https://openstax.org/books/university-physics-volume-1/pages/preface (and -volume-2, -volume-3): server-rendered page embeds the full TOC tree (units → chapters → sections) and the licence object `{"url":"http://creativecommons.org/licenses/by-nc-sa/4.0/","name":"Creative Commons Attribution-NonCommercial-ShareAlike License"}`; preface text quoted above. Chapter list extracted programmatically from the tree.
- https://openstax.org/apps/cms/api/v2/pages/?type=books.Book&… (OpenStax public CMS API): titles, slugs, licence, publish dates, ISBNs, authors, PDF URL.
Not verified: the date at which the licence changed from CC BY to CC BY-NC-SA.

### 4. The Feynman Lectures on Physics (free online edition)
- Authors: Richard P. Feynman, Robert B. Leighton, Matthew Sands
- Title: The Feynman Lectures on Physics, Vol. I "Mainly Mechanics, Radiation, and Heat"; Vol. II "Mainly Electromagnetism and Matter"; Vol. III "Quantum Mechanics"
- Edition / year: original Addison-Wesley 1963–1965; "Definitive Edition" 2006; "New Millennium Edition" (Basic Books, 2010/2011); free HTML online edition by Caltech + The Feynman Lectures Website (Michael A. Gottlieb, editor; Rudolf Pfeiffer), Vol I posted Sept 2013, last (Vol II) Dec 2013 (APS News, Oct 2014)
- Publisher: print — Basic Books (Hachette; formerly Perseus); online — Caltech
- Level: introductory (Caltech freshman/sophomore course), but in practice demanding; read by advanced undergraduates and above
- Open: free to READ online only, NOT openly licensed. URL: https://www.feynmanlectures.caltech.edu/ (I_toc.html, II_toc.html, III_toc.html). Copyright retained (Caltech; online-edition notice reported as "© 1963–1965, 2006, 2013 California Institute of Technology, Michael A. Gottlieb and Rudolf Pfeiffer" — seen only in a secondary search summary). Per the 2022 Caltech DMCA notice (GitHub dmca repo), "On the website there are copyright notices on almost every page" and the home page states that "copying it or downloading it is not permitted for any purpose". APS News (2014) quotes Gottlieb: "free-to-read high-quality online edition". => Linking is fine; copying text/figures is not.

Contents:
- Vol I (52 ch.): 1 Atoms in Motion; 2 Basic Physics; 3 The Relation of Physics to Other Sciences; 4 Conservation of Energy; 5 Time and Distance; 6 Probability; 7 The Theory of Gravitation; 8 Motion; 9 Newton's Laws of Dynamics; 10 Conservation of Momentum; 11 Vectors; 12 Characteristics of Force; 13 Work and Potential Energy (A); 14 Work and Potential Energy (conclusion); 15 The Special Theory of Relativity; 16 Relativistic Energy and Momentum; 17 Space-Time; 18 Rotation in Two Dimensions; 19 Center of Mass; Moment of Inertia; 20 Rotation in Space; 21 The Harmonic Oscillator; 22 Algebra; 23 Resonance; 24 Transients; 25 Linear Systems and Review; 26 Optics: The Principle of Least Time; 27 Geometrical Optics; 28 Electromagnetic Radiation; 29 Interference; 30 Diffraction; 31 The Origin of the Refractive Index; 32 Radiation Damping. Light Scattering; 33 Polarization; 34 Relativistic Effects in Radiation; 35 Color Vision; 36 Mechanisms of Seeing; 37 Quantum Behavior; 38 The Relation of Wave and Particle Viewpoints; 39 The Kinetic Theory of Gases; 40 The Principles of Statistical Mechanics; 41 The Brownian Movement; 42 Applications of Kinetic Theory; 43 Diffusion; 44 The Laws of Thermodynamics; 45 Illustrations of Thermodynamics; 46 Ratchet and Pawl; 47 Sound. The Wave Equation; 48 Beats; 49 Modes; 50 Harmonics; 51 Waves; 52 Symmetry in Physical Laws.
  By topic: 1–7 overview; 8–14 kinematics/dynamics/energy; 15–17 special relativity; 18–20 rotation; 21–25 oscillations and linear systems; 26–36 optics and radiation (incl. vision); 37–38 quantum behaviour; 39–46 kinetic theory, stat. mech., thermodynamics; 47–51 sound and waves; 52 symmetry.
- Vol II (42 ch.): 1 Electromagnetism; 2 Differential Calculus of Vector Fields; 3 Vector Integral Calculus; 4 Electrostatics; 5 Application of Gauss' Law; 6 The Electric Field in Various Circumstances; 7 The Electric Field in Various Circumstances (Continued); 8 Electrostatic Energy; 9 Electricity in the Atmosphere; 10 Dielectrics; 11 Inside Dielectrics; 12 Electrostatic Analogs; 13 Magnetostatics; 14 The Magnetic Field in Various Situations; 15 The Vector Potential; 16 Induced Currents; 17 The Laws of Induction; 18 The Maxwell Equations; 19 The Principle of Least Action; 20 Solutions of Maxwell's Equations in Free Space; 21 Solutions of Maxwell's Equations with Currents and Charges; 22 AC Circuits; 23 Cavity Resonators; 24 Waveguides; 25 Electrodynamics in Relativistic Notation; 26 Lorentz Transformations of the Fields; 27 Field Energy and Field Momentum; 28 Electromagnetic Mass; 29 The Motion of Charges in Electric and Magnetic Fields; 30 The Internal Geometry of Crystals; 31 Tensors; 32 Refractive Index of Dense Materials; 33 Reflection from Surfaces; 34 The Magnetism of Matter; 35 Paramagnetism and Magnetic Resonance; 36 Ferromagnetism; 37 Magnetic Materials; 38 Elasticity; 39 Elastic Materials; 40 The Flow of Dry Water; 41 The Flow of Wet Water; 42 Curved Space.
  By topic: 1–3 vector calculus; 4–12 electrostatics and dielectrics; 13–17 magnetostatics and induction; 18–24 Maxwell equations, radiation, circuits, waveguides; 25–28 relativistic electrodynamics; 29–33 charges in fields, crystals, tensors, optics of matter; 34–37 magnetism of matter; 38–39 elasticity; 40–41 fluid dynamics; 42 curved space (GR).
- Vol III (21 ch.): 1 Quantum Behavior; 2 The Relation of Wave and Particle Viewpoints; 3 Probability Amplitudes; 4 Identical Particles; 5 Spin One; 6 Spin One-Half; 7 The Dependence of Amplitudes on Time; 8 The Hamiltonian Matrix; 9 The Ammonia Maser; 10 Other Two-State Systems; 11 More Two-State Systems; 12 The Hyperfine Splitting in Hydrogen; 13 Propagation in a Crystal Lattice; 14 Semiconductors; 15 The Independent Particle Approximation; 16 The Dependence of Amplitudes on Position; 17 Symmetry and Conservation Laws; 18 Angular Momentum; 19 The Hydrogen Atom and the Periodic Table; 20 Operators; 21 The Schrödinger Equation in a Classical Context: A Seminar on Superconductivity.

Verified from:
- https://en.wikipedia.org/wiki/The_Feynman_Lectures_on_Physics — full chapter lists of all three volumes (fetched); capitalisation above normalised to title case.
- https://www.aps.org/apsnews/2014/10/feynman-lectures-now-freely-available-online — dates, who runs the online edition, "free-to-read" wording.
- https://github.com/github/dmca/blob/master/2022/03/2022-03-30-caltech.md — Caltech DMCA notice quoting the site's copyright/no-download statement.
Not verified: feynmanlectures.caltech.edu itself could not be fetched (Cloudflare 403 "Sorry, you have been blocked" for this client; the Wayback Machine has the domain excluded). So the chapter titles are from Wikipedia, not the site, and the site's own copyright wording is known only through the DMCA notice quote. A human should open https://www.feynmanlectures.caltech.edu/I_toc.html in a browser to confirm wording before quoting it in a README.

### 1. Halliday, Resnick, Walker — Fundamentals of Physics
- Authors: David Halliday, Robert Resnick, Jearl Walker
- Title: Fundamentals of Physics (also "Halliday and Resnick's Fundamentals of Physics"); "Extended" = with modern-physics chapters 38–44
- Edition / year: 12th edition, Wiley, copyright 2021 (retailer records: standard loose-leaf 2021-10-12, ISBN 978-1-119-80114-6, ch. 1–37; Extended loose-leaf ISBN 978-1-119-77351-1, ch. 1–44). No 13th edition found (search 2026-11).
- Publisher: John Wiley & Sons
- Level: introductory, calculus-based (first two years, science/engineering)
- Open: no

Contents (Extended, 44 chapters; the book itself has no named parts on the retailer TOC — groupings in brackets are mine):
- [Mechanics] 1 Measurement; 2 Motion Along a Straight Line; 3 Vectors; 4 Motion in Two and Three Dimensions; 5 Force and Motion—I; 6 Force and Motion—II; 7 Kinetic Energy and Work; 8 Potential Energy and Conservation of Energy; 9 Center of Mass and Linear Momentum; 10 Rotation; 11 Rolling, Torque, and Angular Momentum; 12 Equilibrium and Elasticity; 13 Gravitation; 14 Fluids
- [Oscillations, waves] 15 Oscillations; 16 Waves—I; 17 Waves—II
- [Thermodynamics] 18 Temperature, Heat, and the First Law of Thermodynamics; 19 The Kinetic Theory of Gases; 20 Entropy and the Second Law of Thermodynamics
- [E&M] 21 Coulomb's Law; 22 Electric Fields; 23 Gauss' Law; 24 Electric Potential; 25 Capacitance; 26 Current and Resistance; 27 Circuits; 28 Magnetic Fields; 29 Magnetic Fields Due to Currents; 30 Induction and Inductance; 31 Electromagnetic Oscillations and Alternating Current; 32 Maxwell's Equations; Magnetism of Matter; 33 Electromagnetic Waves
- [Optics] 34 Images; 35 Interference; 36 Diffraction
- [Modern] 37 Relativity; 38 Photons and Matter Waves; 39 More About Matter Waves; 40 All About Atoms; 41 Conduction of Electricity in Solids; 42 Nuclear Physics; 43 Energy from the Nucleus; 44 Quarks, Leptons, and the Big Bang

Verified from:
- https://www.ecampus.com/fundamentals-physics-12th-halliday-david/bk/9781119801146 — 12th ed., Wiley, © 2021-10-12, chapters 1–37 listed.
- https://www.biggerbooks.com/fundamentals-physics-12th-halliday/bk/9781119773511 — "Fundamentals of Physics, Twelfth Edition Extended", chapters 1–44 listed.
Not verified: Wiley's own product page / WileyPLUS page (https://www.wileyplus.com/physics/halliday-fundamentals-of-physics-12e-eprof21332/ returned 403). TOC is from two bookstore pages (consistent with each other).

### 2. Young & Freedman — University Physics with Modern Physics
- Authors: Hugh D. Young, Roger A. Freedman
- Title: University Physics with Modern Physics
- Edition / year: 16th edition, Pearson, published 16 Feb 2026 (US page), © 2027; ISBN 978-0-13-534228-2 (Pearson+). Split volumes: Vol 1 ch. 1–37 (978-0-13-590615-6), Vol 2 ch. 37–44 (978-0-13-590616-3). Previous: 15th edition, © 2021 (hardcover ISBN 978-0-13-515955-2, page says pub. 2019/2020) — same 44-chapter list.
- Publisher: Pearson
- Level: introductory, calculus-based
- Open: no

Contents (16th ed.; parts as named on Pearson's page):
- MECHANICS: 1 Units, Physical Quantities, and Vectors; 2 Motion Along a Straight Line; 3 Motion in Two or Three Dimensions; 4 Newton's Laws of Motion; 5 Applying Newton's Laws; 6 Work and Kinetic Energy; 7 Potential Energy and Energy Conservation; 8 Momentum, Impulse, and Collisions; 9 Rotation of Rigid Bodies; 10 Dynamics of Rotational Motion; 11 Equilibrium and Elasticity; 12 Fluid Mechanics; 13 Gravitation; 14 Periodic Motion
- WAVES/ACOUSTICS: 15 Mechanical Waves; 16 Sound and Hearing
- THERMODYNAMICS: 17 Temperature and Heat; 18 Thermal Properties of Matter; 19 The First Law of Thermodynamics; 20 The Second Law of Thermodynamics
- ELECTROMAGNETISM: 21 Electric Charge and Electric Field; 22 Gauss's Law; 23 Electric Potential; 24 Capacitance and Dielectrics; 25 Current, Resistance, and Electromotive Force; 26 Direct-Current Circuits; 27 Magnetic Field and Magnetic Forces; 28 Sources of Magnetic Field; 29 Electromagnetic Induction; 30 Inductance; 31 Alternating Current; 32 Electromagnetic Waves
- OPTICS: 33 The Nature and Propagation of Light; 34 Geometric Optics; 35 Interference; 36 Diffraction
- MODERN PHYSICS: 37 Relativity; 38 Photons: Light Waves Behaving as Particles; 39 Particles Behaving as Waves; 40 Quantum Mechanics I: Wave Functions; 41 Quantum Mechanics II: Atomic Structure; 42 Molecules and Condensed Matter; 43 Nuclear Physics; 44 Particle Physics and Cosmology
- Appendices: A The International System of Units; B Useful Mathematical Relations; C The Greek Alphabet; D Periodic Table of the Elements; E Unit Conversion Factors; F Numerical Constants

Verified from:
- https://www.pearson.com/en-us/subject-catalog/p/university-physics-with-modern-physics/P200000012703/9780135342282 — raw HTML fetched and parsed: "16th Edition", "© 2027", TOC exactly as above.
- https://www.pearson.com/en-ca/subject-catalog/p/university-physics-with-modern-physics/P200000006855/9780135159552 — 15th ed., © 2021, same parts and chapter titles.
Not verified: nothing material (one search snippet suggested different numbering in the 16th; the Pearson page itself shows 1–44 as above).

### 5. The Berkeley Physics Course (5 volumes)
- Series: Berkeley Physics Course, NSF-funded (Educational Services Inc. / Education Development Center), published by McGraw-Hill from 1965. Level: introductory, honours / strong first- and second-year students (more demanding than HRW/Y&F).
- Vol 1 Mechanics — Charles Kittel, Walter D. Knight, Malvin A. Ruderman; 1st ed. 1965; 2nd ed. 1973 revised by A. Carl Helmholz and Burton J. Moyer (McGraw-Hill; xix + 426 p.).
- Vol 2 Electricity and Magnetism — Edward M. Purcell; 1st ed. 1965 (McGraw-Hill), 2nd ed. 1985 (McGraw-Hill), 3rd ed. Purcell & David J. Morin, Cambridge University Press, hardback 14 March 2013 (ISBN 978-1-107-01402-2; eBook 978-1-139-01297-3), SI units.
- Vol 3 Waves — Frank S. Crawford Jr.; McGraw-Hill 1968 (ISBN 0-07-004860-6; a "preliminary edition" 1966 also exists).
- Vol 4 Quantum Physics — Eyvind H. Wichmann; preliminary ed. 1967, McGraw-Hill 1971.
- Vol 5 Statistical Physics — Frederick Reif; McGraw-Hill 1967 (catalogues also show 1965; xxi + 398 p.).

Open / legal status: **unclear — treat as NOT open.**
- Wikipedia (Berkeley Physics Course; Electricity and Magnetism (book)): because of NSF funding, the original 1965 editions carried a copyright-page notice that the material would be available to authors and publishers on a royalty-free basis after five years (for Purcell: "after 1970"), via a royalty-free licence to be obtained from Education Development Center; copyright line "© 1963, 1964, 1965 by Education Development Center, Inc."; EDC's copyright to Purcell's 1965 edition now belongs to Purcell's sons; Ben Crowell reported that Cambridge University Press would not give him the owner's contact and that the promised royalty-free licence is "effectively impossible to obtain", leaving an open first-edition reproduction "in legal limbo" (his unfinished LaTeX project was on Bitbucket). Wikipedia: "The legal status of the original editions has been befogged." A search summary (Waves copy) quotes: "Copyright © 1965, 1966, 1968 by Education Development Center, Inc. This book, or parts thereof, may not be reproduced in any form without the written permission…".
- "Royalty-free licence on application" ≠ public domain or an open licence: no volume is under a stated open licence.
- archive.org: (a) https://archive.org/details/BerkeleyPhysicsCourse — community upload ("opensource"/"community" collection) of the 1973 McGraw-Hill Mechanics, NO rights statement → unauthorised as far as can be seen; do not link. (b) mechanics00kitt (1973) and statisticalphysi0000reif — Internet Archive lending library ("inlibrary", "printdisabled", access-restricted-item = true) → borrow-only, not open.

Contents:
- Vol 2 (Purcell & Morin, 3rd ed., 2013): 1 Electrostatics: charges and fields; 2 The electric potential; 3 Electric fields around conductors; 4 Electric currents; 5 The fields of moving charges; 6 The magnetic field; 7 Electromagnetic induction; 8 Alternating-current circuits; 9 Maxwell's equations and electromagnetic waves; 10 Electric fields in matter; 11 Magnetic fields in matter. Appendices: A Differences between SI and Gaussian units; B SI units of common quantities; C Unit conversions; D SI and Gaussian formulas; E Exact relations among SI and Gaussian units; F Curvilinear coordinates; G A short review of special relativity; H Radiation by an accelerated charge; I Superconductivity; J Magnetic resonance; K Helpful formulas/facts.
- Vols 1, 3, 4, 5: chapter lists NOT VERIFIED (no catalogue page with a contents note could be fetched; Google Books API quota exhausted; library catalogues blocked/timeouts). Recollection only, do not publish without checking a physical copy:
  - Vol 3 Waves (recollection): 1 Free oscillations of simple systems; 2 Free oscillations of systems with many degrees of freedom; 3 Forced oscillations; 4 Traveling waves; 5 Reflection; 6 Modulation, pulses, and wave packets; 7 Waves in two and three dimensions; 8 Polarization; 9 Interference and diffraction.
  - Vol 5 Statistical Physics (recollection): 1 Characteristic features of macroscopic systems; 2 Basic probability concepts; 3 Statistical description of systems of particles; 4 Thermal interaction; 5 Microscopic theory and macroscopic measurements; 6 Canonical distribution in the classical approximation; 7 General thermodynamic interaction; 8 Elementary kinetic theory of transport processes.
  - Vol 1 Mechanics (topics only, recollection): vectors, Galilean invariance, Newtonian dynamics, energy and momentum conservation, harmonic oscillator, rigid bodies, inverse-square force, special relativity (several chapters), principle of equivalence.
  - Vol 4 Quantum Physics: no list given (not verified, not reliably recalled).

Verified from:
- https://en.wikipedia.org/wiki/Berkeley_Physics_Course — volumes, authors, McGraw-Hill from 1965, royalty-free notice, "befogged".
- https://en.wikipedia.org/wiki/Electricity_and_Magnetism_(book) — Purcell editions table, EDC copyright line, Crowell account.
- https://www.cambridge.org/highereducation/books/electricity-and-magnetism/0F97BB6C5D3A56F19B9835EDBEAB087C (redirect from cambridge.org/core/books/…) — raw HTML parsed: chapter and appendix labels/titles for the 3rd ed.; Core page: authors, 3rd ed., hardback 14 March 2013.
- https://archive.org/details/BerkeleyPhysicsCourse and archive.org metadata API (mechanics00kitt, statisticalphysi0000reif) — collections/access flags.
- https://www.abebooks.com/Waves-Berkeley-Physics-Course-Vol-3/32430732901/bd — Crawford, McGraw-Hill 1968, ISBN.
- Open Library (openlibrary.org works/editions JSON) — editions/years for all five volumes.
Not verified: chapter lists of Vols 1, 3, 4, 5; the exact wording of the 1965 royalty-free notices (seen only via Wikipedia and search summaries).

## Upper undergraduate / graduate standard texts

### 6. Griffiths — Introduction to Electrodynamics
- Author: David J. Griffiths (Reed College)
- Title: Introduction to Electrodynamics
- Edition / year: 5th edition, Cambridge University Press; hardback 02 November 2023 (ISBN 978-1-009-39775-9, 650 pp.), digital 06 October 2023 (ISBN 978-1-009-39773-5, DOI 10.1017/9781009397735). Copyright page (per search summary): "Fifth edition © David J. Griffiths 2024"; earlier editions Prentice Hall/Pearson, 4th ed. reissued by CUP.
- Publisher: Cambridge University Press
- Level: upper undergraduate (junior/senior E&M)
- Open: no

Contents: 1 Vector Analysis; 2 Electrostatics; 3 Potentials; 4 Electric Fields in Matter; 5 Magnetostatics; 6 Magnetic Fields in Matter; 7 Electrodynamics; 8 Conservation Laws; 9 Electromagnetic Waves; 10 Potentials and Fields; 11 Radiation; 12 Electrodynamics and Relativity. Appendices: A Vector Calculus in Curvilinear Coordinates; B The Helmholtz Theorem; C Units.

Verified from: https://www.cambridge.org/highereducation/books/introduction-to-electrodynamics/FD23E188E2BDCDB40199CFE3386EC08F — raw HTML parsed: "5th Edition (Current edition)", hardback 02 November 2023, digital 06 October 2023, "tocSimplified" chapter list as above.
Not verified: copyright-page wording (search summary only).

### 7. Griffiths & Schroeter — Introduction to Quantum Mechanics
- Authors: David J. Griffiths, Darrell F. Schroeter (Reed College)
- Title: Introduction to Quantum Mechanics
- Edition / year: 3rd edition, Cambridge University Press, hardback 16 August 2018 (ISBN 978-1-107-18963-8, 508 pp.; DOI 10.1017/9781316995433)
- Publisher: Cambridge University Press
- Level: upper undergraduate
- Open: no

Contents: Part I Theory: 1 The Wave Function; 2 Time-Independent Schrödinger Equation; 3 Formalism; 4 Quantum Mechanics in Three Dimensions; 5 Identical Particles; 6 Symmetries & Conservation Laws (CUP short TOC: "Symmetry"). Part II Applications: 7 Time-Independent Perturbation Theory; 8 The Variational Principle; 9 The WKB Approximation; 10 Scattering; 11 Quantum Dynamics; 12 Afterword. Appendix: Linear Algebra.

Verified from: https://www.cambridge.org/highereducation/books/introduction-to-quantum-mechanics/990799CA07A83FC5312402AF6860311E (via https://www.cambridge.org/highereducation/isbn/9781316995433) — raw HTML parsed: "3rd Edition", hardback 16 August 2018, short TOC "Part I. Theory: 1. The wave function … 6. Symmetry; Part II. Application: 7 … 12. Afterword; Appendix A. Linear algebra".
Not verified: the full-length title of ch. 6 (CUP short TOC says "Symmetry"; the book's own heading is, from memory, "Symmetries & Conservation Laws").

### 11. Sakurai & Napolitano — Modern Quantum Mechanics
- Authors: J. J. Sakurai, Jim Napolitano
- Title: Modern Quantum Mechanics
- Edition / year: 3rd edition, Cambridge University Press, hardback 17 September 2020 (ISBN 978-1-108-47322-4, 566 pp.; DOI 10.1017/9781108587280). (2nd ed. Addison-Wesley 2011, reissued by CUP.)
- Publisher: Cambridge University Press
- Level: graduate (first-year graduate QM; also strong seniors)
- Open: no

Contents: 1 Fundamental Concepts; 2 Quantum Dynamics; 3 Theory of Angular Momentum; 4 Symmetry in Quantum Mechanics; 5 Approximation Methods; 6 Scattering Theory; 7 Identical Particles; 8 Relativistic Quantum Mechanics. Appendices: A Electromagnetic Units; B Elementary Solutions to Schrödinger's Wave Equation; C Hamiltonian for a Charge in an Electromagnetic Field; D Proof of the Angular-Momentum Addition Rule (3.8.38); E Finding Clebsch–Gordan Coefficients; F Notes on Complex Variables.

Verified from: https://www.cambridge.org/highereducation/books/modern-quantum-mechanics/DF43277E8AEDF83CC12EA62887C277DC (via …/isbn/9781108587280) — raw HTML parsed: "3rd Edition (Current edition)", hardback 17 September 2020, chapter and appendix list as above.

### 8. Kittel — Introduction to Solid State Physics
- Author: Charles Kittel
- Title: Introduction to Solid State Physics
- Edition / year: 8th edition, Wiley, November 2004 (ISBN 978-0-471-41526-8, 704 pp.; front matter dated 9/22/04). A later "Kittel's Introduction to Solid State Physics, Global Edition" (with Paul McEuen, Wiley, 2018) exists per search summaries — not checked.
- Publisher: John Wiley & Sons
- Level: upper undergraduate / beginning graduate (condensed matter)
- Open: no

Contents: 1 Crystal Structure; 2 Wave Diffraction and the Reciprocal Lattice; 3 Crystal Binding and Elastic Constants; 4 Phonons I. Crystal Vibrations; 5 Phonons II. Thermal Properties; 6 Free Electron Fermi Gas; 7 Energy Bands; 8 Semiconductor Crystals; 9 Fermi Surfaces and Metals; 10 Superconductivity; 11 Diamagnetism and Paramagnetism; 12 Ferromagnetism and Antiferromagnetism; 13 Magnetic Resonance; 14 Plasmons, Polaritons, and Polarons; 15 Optical Processes and Excitons; 16 Dielectrics and Ferroelectrics; 17 Surface and Interface Physics; 18 Nanostructures; 19 Noncrystalline Solids; 20 Point Defects; 21 Dislocations; 22 Alloys.
Appendices: A Temperature Dependence of the Reflection Lines; B Ewald Calculation of Lattice Sums; C Quantization of Elastic Waves: Phonons; D Fermi-Dirac Distribution Function; E Derivation of the dk/dt Equation; F Boltzmann Transport Equation; G Vector Potential, Field Momentum, and Gauge Transformations; H Cooper Pairs; I Ginzburg-Landau Equation; J Electron-Phonon Collisions.

Verified from:
- https://www.wiley.com/en-us/Introduction+to+Solid+State+Physics%2C+8th+Edition-p-9780471415268 — 8th ed., Nov 2004, ISBN, 704 pp., link "Table of contents (PDF)".
- https://media.wiley.com/product_data/excerpt/6X/04714152/047141526X-13.pdf — Wiley's own TOC excerpt; text extracted with pdftotext; all chapter and appendix headings as above.

### 9. Goldstein, Poole, Safko — Classical Mechanics
- Authors: Herbert Goldstein, Charles P. Poole, John L. Safko
- Title: Classical Mechanics
- Edition / year: 3rd edition, Addison-Wesley/Pearson, published 2001, © 2002 (ISBN 978-0-201-65702-9); Pearson New International Edition 2014 (ISBN 978-1-292-03893-3).
- Publisher: Pearson (Addison-Wesley)
- Level: graduate (also advanced undergraduate)
- Open: no

Contents: 1 Survey of the Elementary Principles; 2 Variational Principles and Lagrange's Equations; 3 The Central Force Problem; 4 The Kinematics of Rigid Body Motion; 5 The Rigid Body Equations of Motion; 6 Oscillations; 7 The Classical Mechanics of the Special Theory of Relativity; 8 The Hamiltonian Equations of Motion; 9 Canonical Transformations; 10 Hamilton-Jacobi Theory and Action-Angle Variables; 11 Classical Chaos; 12 Canonical Perturbation Theory; 13 Introduction to the Lagrangian and Hamiltonian Formulations for Continuous Systems and Fields. Appendixes; Select Bibliography; Index.

Verified from: https://www.pearson.com/en-us/subject-catalog/p/classical-mechanics/P200000006871/9780201657029 — authors, 3rd ed., published 2001, © 2002, ISBN, TOC as above (with "UPDATED/NEW/REVISED" tags, stripped here). A search summary of a TAMU library record gave the same chapters 1–12.
Not verified: titles of the appendixes (Pearson page only says "Appendixes").

### 10. Jackson — Classical Electrodynamics
- Author: John David Jackson
- Title: Classical Electrodynamics
- Edition / year: 3rd edition, Wiley; Wiley page: published August 1998 (copyright 1999), ISBN 978-0-471-30932-1, 832 pp.
- Publisher: John Wiley & Sons
- Level: graduate
- Open: no

Contents: Introduction and Survey; 1 Introduction to Electrostatics; 2 Boundary-Value Problems in Electrostatics: I; 3 Boundary-Value Problems in Electrostatics: II; 4 Multipoles, Electrostatics of Macroscopic Media, Dielectrics; 5 Magnetostatics, Faraday's Law, Quasi-Static Fields; 6 Maxwell Equations, Macroscopic Electromagnetism, Conservation Laws; 7 Plane Electromagnetic Waves and Wave Propagation; 8 Waveguides, Resonant Cavities, and Optical Fibers; 9 Radiating Systems, Multipole Fields and Radiation; 10 Scattering and Diffraction; 11 Special Theory of Relativity; 12 Dynamics of Relativistic Particles and Electromagnetic Fields; 13 Collisions, Energy Loss, and Scattering of Charged Particles, Cherenkov and Transition Radiation; 14 Radiation by Moving Charges; 15 Bremsstrahlung, Method of Virtual Quanta, Radiative Beta Processes; 16 Radiation Damping, Classical Models of Charged Particles. Appendix on Units and Dimensions; Bibliography; Index.

Verified from:
- https://www.wiley.com/en-us/Classical+Electrodynamics%2C+3rd+Edition-p-9780471309321 — 3rd ed., August 1998, ISBN, 832 pp.
- https://media.wiley.com/product_data/excerpt/2X/04713093/047130932X-18.pdf — Wiley's own scanned "Contents" pages xv–xxi, read page by page; headings as above.
Not verified: the "1999" year (Wiley page says Aug 1998; 1999 is the commonly cited copyright year — not seen on a fetched page).

## Supplementary texts for sections the list above misses

### S1. Thermal / statistical physics — Schroeder, An Introduction to Thermal Physics
- Author: Daniel V. Schroeder (Weber State University)
- Edition / year / publisher: originally Addison Wesley Longman 2000 (later Pearson; ISBN 978-0-201-38027-9, 422 pp.); reissued by Oxford University Press late 2020 / early 2021 (hardback 978-0-19-289554-7, paperback 978-0-19-289555-4). No new edition number.
- Level: upper undergraduate (also strong sophomores). Open: no.
- Contents: Part I Fundamentals: 1 Energy in Thermal Physics; 2 The Second Law; 3 Interactions and Implications. Part II Thermodynamics: 4 Engines and Refrigerators; 5 Free Energy and Chemical Thermodynamics. Part III Statistical Mechanics: 6 Boltzmann Statistics; 7 Quantum Statistics; 8 Systems of Interacting Particles. Appendix A Elements of Quantum Mechanics; Appendix B Mathematical Results.
- Verified from: https://physics.weber.edu/thermal/ (author's book page: publishers, ISBNs) and https://physics.weber.edu/thermal/contents.html (full contents).
- Not verified: OUP's own page (oup.com.au returned 403). Kittel & Kroemer "Thermal Physics" not checked.

### S2. Optics — Hecht, Optics
- Author: Eugene Hecht (Adelphi University)
- Edition / year / publisher: 5th edition, Pearson; hardcover ISBN 978-0-13-397722-6 listed "Published 2015"; Pearson+ eTextbook ISBN 978-0-13-752642-0 published 14 July 2021, page shows "© 2022".
- Level: intermediate/upper undergraduate. Open: no.
- Contents: 1 A Brief History; 2 Wave Motion; 3 Electromagnetic Theory, Photons, and Light; 4 The Propagation of Light; 5 Geometrical Optics; 6 More on Geometrical Optics; 7 The Superposition of Waves; 8 Polarization; 9 Interference; 10 Diffraction; 11 Fourier Optics; 12 Basics of Coherence Theory; 13 Modern Optics: Lasers and Other Topics.
- Verified from: https://www.pearson.com/en-us/subject-catalog/p/optics/P200000006793/9780133977226 (raw HTML parsed: "5th edition", TOC as above).

### S3. Relativity
(a) Taylor & Wheeler, Spacetime Physics — **OPEN (CC BY 4.0)**
- Authors: Edwin F. Taylor, John Archibald Wheeler. 2nd edition, W. H. Freeman, New York, 1992 (ISBN 0-7167-2327-1). Level: introductory–intermediate special relativity (first/second year).
- Open: yes. The book page states "The entire contents of this book are now available under a Creative Commons license" and "licensed under a Creative Commons Attribution 4.0 International License"; full book via the Internet Archive plus per-chapter downloads. URL: https://www.eftaylor.com/spacetimephysics/
- Contents: 1 Spacetime: Overview; 2 Floating Free; 3 Same Laws for All; 4 Trip to Canopus; Special Topic: Lorentz Transformation; 5 Trekking through Spacetime; 6 Regions of Spacetime; 7 Momenergy; 8 Collide. Create. Annihilate.; 9 Gravity: Curved Spacetime in Action.
- Verified from: https://www.eftaylor.com/spacetimephysics/ (downloads list = chapter list; licence statement).
(b) Taylor, Wheeler, Bertschinger, Exploring Black Holes, 2nd ed. (EBH2e) — **OPEN (CC BY 4.0)**, online only ("There is no published hard copy textbook of EBH2e"); "you may freely download the online version … for personal and class use"; "licensed under a Creative Commons Attribution 4.0 International License". URL: https://www.eftaylor.com/exploringblackholes/ . Level: introductory general relativity (calculus only). Year not stated on the page.
- Contents: 1 Speeding; 2 The Bridge: SR to GR; 3 Curving; 4 The Global Positioning System (GPS); 5 Global and Local Metrics; 6 Diving; 7 Inside the Black Hole; 8 Circular Orbits; 9 Orbiting; 10 Advance of Mercury's Perihelion; 11 Orbits of Light; 12 Diving Panoramas; 13 Gravitational Mirages; 14 Expanding Universe; 15 Cosmology; 16 Gravitational Waves; 17 Spinning Black Hole; 18 Circular Orbits around the Spinning Black Hole; 19 Orbiting the Spinning Black Hole; 20 Orbits of Light around the Spinning Black Hole; 21 Leaving Our Universe.
- Verified from: https://www.eftaylor.com/exploringblackholes/ (downloads list, licence statement).
(c) Hartle, Gravity: An Introduction to Einstein's General Relativity
- Author: James B. Hartle. Originally Addison-Wesley 2003; reissued by Cambridge University Press: hardback 24 June 2021 (ISBN 978-1-316-51754-3, 602 pp.), digital 03 Sept 2021 (DOI 10.1017/9781009042604). Level: advanced undergraduate (one semester GR). Open: no.
- Contents: Part I Space and Time in Newtonian Physics and Special Relativity: 1 Gravitational Physics; 2 Geometry as Physics; 3 Space, Time, and Gravity in Newtonian Physics; 4 Principles of Special Relativity; 5 Special Relativistic Mechanics. Part II The Curved Spacetimes of General Relativity: 6 Gravity as Geometry; 7 Description of Curved Spacetime; 8 Geodesics; 9 The Geometry Outside a Spherical Star; 10 Solar System Tests of General Relativity; 11 Relativistic Gravity in Action; 12 Gravitational Collapse and Black Holes; 13 Astrophysical Black Holes; 14 A Little Rotation; 15 Rotating Black Holes; 16 Gravitational Waves; 17 The Universe Observed; 18 Cosmological Models; 19 Which Universe and Why?. Part III The Einstein Equation: 20 A Little More Math; 21 Curvature and the Einstein Equation; 22 The Source of Curvature; 23 Gravitational Wave Emission; 24 Relativistic Stars. Appendices A Units; B Curvature Quantities; C Curvature and the Einstein Equation; D Pedagogical Strategy.
- Verified from: https://www.cambridge.org/highereducation/books/gravity/F9085ABB699F7A3A05ADD0B3930D98E0 (raw HTML parsed: parts, chapters, dates).

### S4. Nuclear and particle physics
(a) Krane, Introductory Nuclear Physics
- Author: Kenneth S. Krane. Wiley; Wiley's page labels it "3rd Edition", publication date 16 January 1991, ISBN 978-0-471-80553-3, 864 pp. (the book is usually cited as the 1987/1988 edition — the "3rd edition" label is Wiley's catalogue wording, not checked against the book). Level: upper undergraduate / beginning graduate. Open: no.
- Contents (Wiley's TOC, chapter titles grouped in units): Unit I Basic Nuclear Structure: 1 Basic Concepts; 2 Elements of Quantum Mechanics; 3 Nuclear Properties; 4 The Force Between Nucleons; 5 Nuclear Models. Unit II Nuclear Decay and Radioactivity: 6 Radioactive Decay; 7 Detecting Nuclear Radiations; 8 Alpha Decay; 9 Beta Decay; 10 Gamma Decay. Unit III Nuclear Reactions: 11 Nuclear Reactions; 12 Neutron Physics; 13 Nuclear Fission; 14 Nuclear Fusion; 15 Accelerators. Unit IV Extensions and Applications: 16 Nuclear Spins and Moments; 17 Meson Physics; 18 Particle Physics; 19 Nuclear Astrophysics; 20 Applications of Nuclear Physics. (Chapter numbers inferred from order; Wiley's TOC lists titles without numbers.)
- Verified from: https://www.wiley.com/en-us/Introductory+Nuclear+Physics%2C+3rd+Edition-p-9780471805533 (embedded product JSON "wTableOfContents").
(b) Griffiths, Introduction to Elementary Particles
- Author: David Griffiths. 2nd, revised edition, Wiley-VCH, October 2008 (paperback ISBN 978-3-527-40601-2, 470 pp.; e-book 978-3-527-83463-1, Dec 2020). Level: upper undergraduate. Open: no.
- Contents: 1 Historical Introduction to the Elementary Particles; 2 Elementary Particle Dynamics; 3 Relativistic Kinematics; 4 Symmetries; 5 Bound States; 6 The Feynman Calculus; 7 Quantum Electrodynamics; 8 Electrodynamics and Chromodynamics of Quarks; 9 Weak Interactions; 10 Gauge Theories; 11 Neutrino Oscillations; 12 Afterword: What's Next?. Appendices A The Dirac Delta Function; B Decay Rates and Cross Sections; C Pauli and Dirac Matrices.
- Verified from: https://www.wiley.com/en-us/Introduction+to+Elementary+Particles%2C+2nd%2C+Revised+Edition-p-9783527406012 (edition, date, ISBN) and Wiley's TOC excerpt https://media.wiley.com/product_data/excerpt/18/35274060/3527406018-13.pdf (pdftotext).

### S5. Astrophysics / cosmology — Carroll & Ostlie, An Introduction to Modern Astrophysics
- Authors: Bradley W. Carroll, Dale A. Ostlie (Weber State University). 2nd edition (Pearson/Addison-Wesley 2007), reissued by Cambridge University Press: hardback 07 September 2017 (ISBN 978-1-108-42216-1, 1359 pp.), digital 16 Aug 2019 (DOI 10.1017/9781108380980). Level: upper undergraduate (astronomy/physics majors). Open: no.
- Contents: Part I The Tools of Astronomy: 1 The Celestial Sphere; 2 Celestial Mechanics; 3 The Continuous Spectrum of Light; 4 The Theory of Special Relativity; 5 The Interaction of Light and Matter; 6 Telescopes. Part II The Nature of Stars: 7 Binary Systems and Stellar Parameters; 8 The Classification of Stellar Spectra; 9 Stellar Atmospheres; 10 The Interiors of Stars; 11 The Sun; 12 The Interstellar Medium and Star Formation; 13 Main Sequence and Post-Main-Sequence Stellar Evolution; 14 Stellar Pulsation; 15 The Fate of Massive Stars; 16 The Degenerate Remnants of Stars; 17 General Relativity and Black Holes; 18 Close Binary Star Systems. Part III The Solar System: 19 Physical Processes in the Solar System; 20 The Terrestrial Planets; 21 The Realms of the Giant Planets; 22 Minor Bodies of the Solar System; 23 Formation of Planetary Systems. Part IV Galaxies and the Universe: 24 The Milky Way Galaxy; 25 The Nature of Galaxies; 26 Galactic Evolution; 27 The Structure of the Universe; 28 Active Galaxies; 29 Cosmology; 30 The Early Universe. Appendices A–N (constants, unit conversions, solar system data, constellations, brightest/nearest stars, stellar data, Messier catalog, and programming modules: Constants, Orbit, TwoStars, StatStar, Galaxy; WMAP data).
- Verified from: https://www.cambridge.org/highereducation/books/an-introduction-to-modern-astrophysics/140DDF8A480C3841DCCD76D66984D858 (via …/isbn/9781108422161; raw HTML parsed: "2nd Edition", dates, TOC).

### S6. Fluids — Kundu, Cohen, Dowling (Capecelatro), Fluid Mechanics
- Authors: Pijush K. Kundu, Ira M. Cohen, David R. Dowling, Jesse Capecelatro (7th ed.). 7th edition, Academic Press/Elsevier, 2024 (page: "7th Edition – August 6, 2024"; "Published: October 17, 2024"); ScienceDirect id 9780128198070. 6th edition (Kundu, Cohen, Dowling) 2015, ISBN 978-0-12-405935-1. Level: upper undergraduate / graduate. Open: no.
- Contents (7th ed.): 1 Introduction; 2 Cartesian Tensors; 3 Kinematics; 4 Conservation Laws; 5 Vorticity Dynamics; 6 Computational Fluid Dynamics; 7 Ideal Flow; 8 Gravity Waves; 9 Laminar Flow; 10 Boundary Layers and Related Topics; 11 Instability; 12 Turbulence; 13 Geophysical Fluid Dynamics; 14 Aerodynamics; 15 Compressible Flow; 16 Introduction to Biofluid Mechanics (online only). Appendices: A Conversion Factors, Constants, Fluid Properties; B Mathematical Tools and Resources; C Founders of Modern Fluid Dynamics; D Visual Resources.
- Verified from: https://shop.elsevier.com/books/catalog/isbn/9780128198070 .
- Not verified: 6th-edition chapter list; Tritton "Physical Fluid Dynamics" not checked.

## Open alternatives (verified licences)

- OpenStax University Physics Vols 1–3 — CC BY-NC-SA 4.0 (see item 3; NOT CC BY). https://openstax.org/details/books/university-physics-volume-1
- Benjamin Crowell, "Light and Matter" — introductory (algebra/trig with optional calculus; written for life-science majors / AP Physics 1–2). Licence: the book's copyright page (rev. May 7, 2020) says "licensed under the Creative Commons Attribution-ShareAlike license, version 3.0 … except for those photographs and drawings of which I am not the author, as listed in the photo credits"; website footer "(c) 1998-2019 Benjamin Crowell, CC-BY-SA" (link to 3.0 US); the Internet Archive item lm_20220102 metadata says CC BY-SA 4.0. URLs: https://www.lightandmatter.com/lm/ ; https://archive.org/details/lm_20220102 . Crowell also offers separate books (Mechanics; Fields and Circuits; Modern Physics; Conceptual Physics; Special Relativity; General Relativity; …) listed on https://www.lightandmatter.com/ .
  Contents ("Brief Contents" of the open text; chapter numbering reconstructed from order 0–36): Motion in one dimension: 0 Introduction and review; 1 Scaling and estimation; 2 Velocity and relative motion; 3 Acceleration and free fall; 4 Force and motion; 5 Analysis of forces. Motion in three dimensions: 6 Newton's laws in three dimensions; 7 Vectors; 8 Vectors and motion; 9 Circular motion; 10 Gravity. Conservation laws: 11 Conservation of energy; 12 Simplifying the energy zoo; 13 Work: the transfer of mechanical energy; 14 Conservation of momentum; 15 Conservation of angular momentum; 16 Thermodynamics. Vibrations and waves: 17 Vibrations; 18 Resonance; 19 Free waves; 20 Bounded waves. Relativity and electromagnetism: 21 Electricity and circuits; 22 The nonmechanical universe; 23 Relativity and magnetism; 24 Electromagnetism; 25 Capacitance and inductance; 26 The atom and E=mc²; 27 General relativity. Optics: 28 The ray model of light; 29 Images by reflection; 30 Images, quantitatively; 31 Refraction; 32 Wave optics. The modern revolution in physics: 33 Rules of randomness; 34 Light as a particle; 35 Matter as a wave; 36 The atom.
  Verified from: https://www.lightandmatter.com/ , https://www.lightandmatter.com/lm/ , archive.org metadata API for lm_20220102, and the first 80 kB of the open OCR text https://archive.org/download/lm_20220102/lm_djvu.txt (title page, licence, brief contents).
- Taylor & Wheeler "Spacetime Physics" 2nd ed. and Taylor/Wheeler/Bertschinger "Exploring Black Holes" 2nd ed. — CC BY 4.0 (see S3). The most permissive licence among the checked texts.
- MIT OpenCourseWare — all pages checked link the licence CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/), footer "© 2001–2026 Massachusetts Institute of Technology":
  - 8.01SC Classical Mechanics, Fall 2016 — https://ocw.mit.edu/courses/8-01sc-classical-mechanics-fall-2016/ — units: Review: Vectors; Kinematics; Newton's Laws; Circular Motion; Drag Forces, Constraints and Continuous Systems; Momentum and Impulse; Continuous Mass Transfer; Kinetic Energy and Work; Potential Energy and Energy Conservation; Collision Theory; Rotational Motion; Angular Momentum; Rotations and Translation – Rolling (…page list was cut at week 12; later weeks not seen).
  - 8.02 Physics II: Electricity and Magnetism, Spring 2019 — https://ocw.mit.edu/courses/8-02-physics-ii-electricity-and-magnetism-spring-2019/ — units: Electrostatics; Magnetic Fields and Forces; Maxwell's Equations.
  - 8.03SC Physics III: Vibrations and Waves, Fall 2016 — https://ocw.mit.edu/courses/8-03sc-physics-iii-vibrations-and-waves-fall-2016/ — Part I Mechanical Vibrations and Waves; Part II Electromagnetic Waves; Part III Optics.
  - 8.04 Quantum Physics I, Spring 2016 (Zwiebach) — https://ocw.mit.edu/courses/8-04-quantum-physics-i-spring-2016/ — Basic Concepts; Quantum Physics in One-dimensional Potentials; One-dimensional Scattering, Angular Momentum & Central Potentials.
  - 8.044 Statistical Physics I, Spring 2013 (Greytak) — https://ocw.mit.edu/courses/8-044-statistical-physics-i-spring-2013/ — unit list not shown on the landing page.
- LibreTexts Physics — https://phys.libretexts.org/Bookshelves — 14 shelves: Conceptual Physics; College Physics; University Physics; Classical Mechanics; Thermodynamics and Statistical Mechanics; Quantum Mechanics; Relativity; Astronomy and Cosmology; Electricity and Magnetism; Optics; Waves and Acoustics; Modern Physics; Nuclear and Particle Physics; Mathematical Physics and Pedagogy. The Bookshelves page itself: "shared under a CC BY-NC-SA 4.0 license". Licences of individual books vary (each page carries its own licence tag) — per-book licences NOT checked here; check each book before reuse.
- Feynman Lectures online — free to read, NOT openly licensed (see item 4).

## Common section order at university level

Derived only from the verified TOCs above (Feynman from Wikipedia; Berkeley vols 1/3/4/5 from titles only).

Order in the three mainstream introductory texts (HRW 12e, Young & Freedman 16e, OpenStax UP) — practically identical:
1. Mechanics (HRW 1–13, Y&F 1–13, OSUP V1 1–13)
2. Fluids — placed at the END of mechanics (HRW 14, Y&F 12 [before gravitation], OSUP V1 14)
3. Oscillations and waves, sound (HRW 15–17, Y&F 14–16, OSUP V1 15–17)
4. Thermodynamics / kinetic theory (HRW 18–20, Y&F 17–20, OSUP V2 1–4)
5. Electricity and magnetism, ending with Maxwell's equations and EM waves (HRW 21–33, Y&F 21–32, OSUP V2 5–16)
6. Optics: geometric, then interference, diffraction (HRW 34–36, Y&F 33–36, OSUP V3 1–4)
7. Special relativity (HRW 37, Y&F 37, OSUP V3 5)
8. Quantum: photons, matter waves, Schrödinger equation (HRW 38–39, Y&F 38–40, OSUP V3 6–7)
9. Atoms (HRW 40, Y&F 41, OSUP V3 8)
10. Condensed matter / solids, semiconductors (HRW 41, Y&F 42, OSUP V3 9)
11. Nuclear physics (HRW 42–43, Y&F 43, OSUP V3 10)
12. Particle physics and cosmology (HRW 44, Y&F 44, OSUP V3 11)
Astrophysics as a separate section is absent from all three; it appears only as gravitation/orbits (mechanics) and cosmology (last chapter).

Deviations in the "physics-first" courses:
- Feynman: special relativity is taught early inside mechanics (I-15…17); optics/radiation and "quantum behaviour" come before thermodynamics; sound/waves come after thermodynamics (I-47…51); Vol II mixes E&M with matter, elasticity, fluid flow (II-40, 41) and curved space (II-42); Vol III starts quantum mechanics from amplitudes and two-state systems (not from the Schrödinger equation) and ends with crystals, semiconductors, superconductivity.
- Berkeley: Mechanics (with special relativity) → E&M (magnetism derived from relativity: Purcell ch. 5 "The fields of moving charges") → Waves (incl. polarization, interference, diffraction = optics) → Quantum Physics → Statistical Physics.
- Crowell "Light and Matter": mechanics → conservation laws with thermodynamics → vibrations and waves → electricity with relativity and magnetism, incl. E=mc² and general relativity → optics → modern physics.

Typical subtopics per section (intro level → upper/graduate level, from the TOCs):
- Mechanics: units and estimation; vectors; kinematics 1D/2D/3D, projectile and circular motion; Newton's laws and applications (friction, drag); work–energy, potential energy, energy conservation; momentum, impulse, collisions, centre of mass; rotation, torque, rolling, angular momentum; equilibrium and elasticity; gravitation and orbits. → Upper/graduate (Goldstein): variational principles and Lagrange's equations; central-force problem; rigid-body kinematics and dynamics; small oscillations; relativistic mechanics; Hamilton's equations; canonical transformations; Hamilton–Jacobi and action-angle variables; classical chaos; perturbation theory; continuous systems and fields.
- Oscillations and waves: simple harmonic motion; damped and driven oscillations, resonance; coupled oscillators and normal modes (Berkeley/Crawford, Feynman "Modes"); travelling waves, superposition, standing waves; sound, beats, Doppler effect; wave packets/dispersion (Berkeley/Crawford, Jackson 7).
- Fluids: pressure, hydrostatics, buoyancy; continuity, Bernoulli; viscosity (intro, one chapter). → Upper (Kundu): tensors, kinematics, conservation laws, vorticity, ideal flow, gravity waves, laminar flow, boundary layers, instability, turbulence, geophysical, aerodynamics, compressible flow, CFD.
- Thermal and statistical physics: temperature and heat, thermal expansion, calorimetry; kinetic theory of gases; first law; second law, entropy, engines and refrigerators. → Upper (Schroeder, Reif): second law from counting states; free energy and chemical thermodynamics; Boltzmann statistics; quantum statistics; interacting particles; transport (Reif ch. 8 — unverified); Feynman adds Brownian motion, diffusion, ratchet and pawl.
- Electricity and magnetism: charge and Coulomb's law; electric field; Gauss's law; potential; capacitance and dielectrics; current, resistance, EMF; DC circuits; magnetic field and forces; sources (Biot–Savart, Ampère); induction; inductance; AC circuits; Maxwell's equations; EM waves; magnetism of matter. → Upper (Griffiths, Purcell): vector analysis; potentials and boundary-value problems; fields in matter; conservation laws; potentials and fields; radiation; relativistic electrodynamics. → Graduate (Jackson): Green functions and boundary-value problems; multipoles; waveguides and cavities; radiating systems; scattering and diffraction; relativistic particle dynamics; collisions and energy loss; radiation by moving charges; bremsstrahlung; radiation damping.
- Optics: nature and propagation of light, reflection, refraction; geometric optics and image formation (mirrors, lenses, instruments); interference; diffraction; polarization. → Upper (Hecht): wave motion; EM theory and photons; superposition; Fourier optics; coherence; lasers and modern optics.
- Relativity: postulates; Lorentz transformation; time dilation, length contraction, simultaneity; spacetime diagrams; relativistic momentum and energy; (intro texts stop here). → GR (Hartle, Taylor–Wheeler–Bertschinger): equivalence principle, gravity as geometry, geodesics, Schwarzschild geometry, Solar-System tests, GPS, black holes (incl. rotating), gravitational waves, cosmological models, Einstein equation, relativistic stars.
- Quantum physics: photons (photoelectric, Compton); matter waves; uncertainty; Schrödinger equation; particle in a box, harmonic oscillator, tunnelling; hydrogen atom; spin. → Upper (Griffiths & Schroeter): formalism; 3D; identical particles; symmetries; perturbation theory; variational principle; WKB; scattering; quantum dynamics. → Graduate (Sakurai): fundamental concepts (Stern–Gerlach, kets), quantum dynamics (pictures, propagators), angular momentum theory, symmetry, approximation methods, scattering, identical particles, relativistic QM.
- Atomic, nuclear and particle physics: atomic structure, periodic table, X-rays, lasers; nuclear properties, nuclear force, nuclear models, radioactive decay (α, β, γ), detectors, reactions, neutron physics, fission, fusion, accelerators (Krane); particles: historical introduction, relativistic kinematics, symmetries, bound states, Feynman calculus, QED, QCD, weak interactions, gauge theories, neutrino oscillations (Griffiths EP).
- Condensed matter: (intro) molecules and bonding, crystal structure, band theory, semiconductors, superconductivity. → (Kittel) crystal structure, reciprocal lattice and diffraction, binding and elastic constants, phonons (vibrations, thermal properties), free-electron Fermi gas, energy bands, semiconductors, Fermi surfaces, superconductivity, dia-/para-/ferro-/antiferromagnetism, magnetic resonance, plasmons/polaritons/polarons, optical processes, dielectrics and ferroelectrics, surfaces, nanostructures, noncrystalline solids, defects, dislocations, alloys.
- Astrophysics and cosmology: (intro) only gravitation/orbits and a closing cosmology chapter. → (Carroll & Ostlie) celestial sphere and celestial mechanics; blackbody spectrum; light–matter interaction; telescopes; binary stars and stellar parameters; spectra classification; stellar atmospheres and interiors; the Sun; ISM and star formation; stellar evolution, pulsation, supernovae, compact remnants, black holes, close binaries; solar system and planet formation; Milky Way, galaxies, galactic evolution, large-scale structure, active galaxies; cosmology and the early Universe.

Audience levels (as used by the verified texts):
- Introductory (year 1–2): HRW, Young & Freedman, OpenStax University Physics [open, NC-SA], Crowell Light and Matter [open, BY-SA], MIT OCW 8.01/8.02/8.03 [open, NC-SA], Spacetime Physics [open, BY]; honours/"physics-first": Feynman Lectures [free to read, not open], Berkeley Physics Course [not open; status of 1960s royalty-free promise unclear].
- Upper undergraduate (year 3–4): Griffiths Electrodynamics, Griffiths & Schroeter QM, Schroeder Thermal Physics, Hecht Optics, Kittel Solid State, Hartle Gravity, Exploring Black Holes [open, BY], Krane Nuclear, Griffiths Elementary Particles, Carroll & Ostlie Astrophysics, MIT OCW 8.04/8.044 [open, NC-SA].
- Graduate: Goldstein Classical Mechanics, Jackson Classical Electrodynamics, Sakurai & Napolitano QM, Kundu Fluid Mechanics (upper-undergraduate/graduate).

---

# Appendix C. Russian university physics courses and research-level references

Status: COMPLETE (2026-11-12). Web research only. Every edition and table of contents below is tied to a page that was actually fetched; anything taken only from search-result snippets is marked "(snippet)". "Not verified" lists what could not be confirmed.

Kinds of sources used: publisher catalogues (fml.ru = Физматлит, lanbook.ru = Лань, ast.ru), the Физматлит publisher's scanned table-of-contents PDFs (fml.ru/tocs/…), bookstore product cards that print «Содержание» as text (my-shop.ru), the Znanium e-library catalogue record, labirint.ru and chitai-gorod.ru cards (edition data only, no TOC text), Wikipedia, Crossref, Open Library, and arXiv/APS/IOP/Cambridge/Elsevier/OUP pages. No full texts were downloaded. Pirate or "student file" sites (studfile, studizba, alleng, obuchalka, twirpx, kzf.kpi.ua PDFs, dispace.edu.nstu.ru PDFs) turned up in searches and were deliberately not used.

Open access: none of the four Russian courses has a legal free edition that I could find. Znanium, Лань ЭБС, LitRes, Rucont and the MIPT library are paid or institution-only. So the answer is "no" for all of Part 1.

---

## Part 1: Russian university courses

### 1. И. В. Савельев «Курс общей физики»

- **Author:** Игорь Владимирович Савельев (МИФИ).
- **Editions verified:**
  - **3-volume edition, Лань** (series «Учебники для вузов. Специальная литература»). This is the current reprint of the 3-volume course that Наука first published.
    - Т. 1 «Механика. Молекулярная физика»: 21-е изд., стер., 448 с., ISBN 978-5-507-55015-9 (lanbook.ru; the year field says 2026, the page header says 2025). The 2023 printing has 436 с., ISBN 978-5-507-48093-7. labirint calls it the 19th edition and my-shop the 17th.
    - Т. 2 «Электричество и магнетизм. Волны. Оптика»: Лань 2023, 17-е изд., стер., 500 с., ISBN 978-5-507-47163-8 (labirint). urss.ru lists a 2022 printing as Изд. 16, ISBN 978-5-8114-8926-8.
    - Т. 3 «Квантовая оптика. Атомная физика. Физика твердого тела. Физика атомного ядра и элементарных частиц»: Лань 2023, 14-е изд., стер., 320 с., ISBN 978-5-507-47045-7 (labirint; full title from the lanbook.ru author page).
    - Original Наука edition: Google Books record DnYuAAAAIAAJ shows «Курс общей физики», т. 1, Наука, Главная редакция физико-математической литературы, 1977, approved for технические вузы.
  - **5-volume edition, Лань («Курс общей физики. В 5 томах»)**, based on Savelyev's lectures at МИФИ (annotation):
    - Т. 1 «Механика»: 2022, 340 с., ISBN 978-5-8114-9196-4. labirint calls it the 7th edition (stereotyped) and my-shop the 6th.
    - Т. 2 «Электричество и магнетизм»: 2024, изд. 5, 344 с., ISBN 978-5-507-49436-1 (my-shop). lanbook.ru shows 8-е изд., стер., 352 с., ISBN 978-5-507-56966-3 (year field 2026).
    - Т. 3 «Молекулярная физика и термодинамика», Т. 4 «Волны. Оптика», Т. 5 «Квантовая оптика. Атомная физика. Физика твердого тела. Физика атомного ядра и элементарных частиц»: these titles appear only in snippets of the e.lanbook.com and my-shop pages, which use JavaScript and could not be fetched. Per the snippets, Т. 4 is 2022, 6-е изд., ISBN 978-5-8114-9198-8, and Т. 5 is 2025, 6-е изд., ISBN 978-5-507-50512-8.
  - **5-book edition, АСТ/Астрель («Курс общей физики. В 5 кн.»**, редакция «Образовательные проекты»; annotation: «охватывает все разделы современной физики и выпускается в пяти книгах… соответствует программам по физике для втузов»). The pages show no years.
    - Кн. 1 «Механика»: 336 с., ISBN 978-5-17-002963-1 (chitai-gorod).
    - Кн. 2 «Электричество и магнетизм»: chitai-gorod listing only.
    - Кн. 3 «Молекулярная физика и термодинамика»: ast.ru.
    - Кн. 4 «Волны. Оптика»: 256 с., ISBN 978-5-17-004586-0 (ast.ru).
    - Кн. 5 «Квантовая оптика. Атомная физика. Физика твердого тела…»: 368 с., ISBN 5-271-01307-3 (ast.ru; the title is cut off on the page).
  - A 4-volume edition (КноРус) also exists. In it, Т. 4 is «Сборник вопросов и задач по общей физике» (chitai-gorod and labirint listings only).
- **Level:** General physics for технические вузы with an extended physics programme. It is usable with a standard programme if some sections are skipped (Лань annotation).
- **Open:** no.

**Contents, 3-volume edition (Лань 2023 printings):**

- Т. 1
  - ЧАСТЬ 1. ФИЗИЧЕСКИЕ ОСНОВЫ МЕХАНИКИ: I Кинематика; II Динамика материальной точки; III Законы сохранения; IV Неинерциальные системы отсчета; V Механика твердого тела; VI Всемирное тяготение; VII Колебательное движение; VIII Релятивистская механика; IX Гидродинамика.
  - ЧАСТЬ 2. МОЛЕКУЛЯРНАЯ ФИЗИКА И ТЕРМОДИНАМИКА: X Предварительные сведения; XI Статистическая физика; XII Термодинамика; XIII Кристаллическое состояние; XIV Жидкое состояние; XV Фазовые равновесия и превращения; XVI Физическая кинетика.
- Т. 2
  - ЧАСТЬ 1. ЭЛЕКТРИЧЕСТВО И МАГНЕТИЗМ: I Электрическое поле в вакууме; II Электрическое поле в диэлектриках; III Проводники в электрическом поле; IV Энергия электрического поля; V Постоянный электрический ток; VI Магнитное поле в вакууме; VII Магнитное поле в веществе; VIII Электромагнитная индукция; IX Уравнения Максвелла; X Движение заряженных частиц в электрических и магнитных полях; XI Классическая теория электропроводности металлов; XII Электрический ток в газах; XIII Электрические колебания.
  - ЧАСТЬ 2. ВОЛНЫ: XIV Упругие волны; XV Электромагнитные волны.
  - ЧАСТЬ 3. ОПТИКА: XVI Предварительные сведения; XVII Интерференция света; XVIII Дифракция света; XIX Поляризация света; XX Взаимодействие электромагнитных волн с веществом; XXI Оптика движущихся сред.
- Т. 3
  - Часть 1 Квантовая оптика: I Тепловое излучение; II Фотоны.
  - Часть 2 Атомная физика: III Боровская теория атома; IV Элементы квантовой механики; V Физика атомов и молекул.
  - Часть 3 Физика твердого тела: VI Колебания кристаллической решетки; VII Зонная теория твердых тел; VIII Электропроводность металлов и полупроводников; IX Контактные и термоэлектрические явления.
  - Часть 4 Физика атомного ядра и элементарных частиц: X Атомное ядро; XI Элементарные частицы.
  - Приложения: Гравитационное взаимодействие; Периодическая система элементов.

**Contents, 5-volume edition (Лань):**

- Т. 1 «Механика»: 1 Кинематика; 2 Динамика материальной точки; 3 Законы сохранения; 4 Неинерциальные системы отсчета; 5 Механика твердого тела; 6 Релятивистская механика; 7 Гравитация; 8 Колебательное движение; 9 Гидродинамика.
- Т. 2 «Электричество и магнетизм»: 1 Электрическое поле в вакууме; 2 Электрическое поле в диэлектриках; 3 Проводники в электрическом поле; 4 Энергия электрического поля; 5 Постоянный электрический ток; 6 Магнитное поле в вакууме; 7 Магнитное поле в веществе; 8 Электромагнитная индукция; 9 Уравнения Максвелла; 10 Движение заряженных частиц в электрических и магнитных полях; 11 Классическая теория электропроводности металлов; 12 Электрический ток в газах; 13 Электрические колебания. Приложение: Векторный потенциал; Основные формулы электромагнетизма в СИ и в гауссовой системе.
- Т. 3–5: by title only (see above).

**Verified from:**
- https://my-shop.ru/shop/product/4858217.html (Т. 1, 3-volume, full «Содержание»)
- https://my-shop.ru/shop/product/593320.html (Т. 2, 3-volume, «Содержание»)
- https://my-shop.ru/shop/product/162823.html (Т. 3, 3-volume, «Содержание»)
- https://my-shop.ru/shop/product/4286933.html (5-volume Т. 1, «Содержание»)
- https://my-shop.ru/shop/product/1080485.html (5-volume Т. 2, «Оглавление»)
- https://lanbook.ru/catalog/author/savelev-i.v./, https://lanbook.ru/catalog/fizika/kurs-obshchey-fiziki-v-3-t-tom-1-mekhanika-molekulyarnaya-fizika/ and https://lanbook.ru/catalog/fizika/kurs-obshchey-fiziki-v-5-t-tom-2-elektrichestvo-i-magnetizm/ (Лань catalogue: editions, ISBNs, annotations; no TOC)
- https://www.labirint.ru/books/521747/, /521748/, /580911/, /838579/ (editions)
- https://ast.ru/authors/savelev-igor-vladimirovich-ast000438/books/ and the book pages …-022695/, …-022696/ (5-book АСТ)
- https://www.chitai-gorod.ru/search?phrase=Савельев курс общей физики (all editions listed) and the product card …-1200394
- https://books.google.com.cy/books?id=DnYuAAAAIAAJ (Наука 1977)

**Not verified:**
- Chapter lists of the original Наука 3-volume editions. Search snippets suggest the 1970 Наука Т. 1 had separate chapters «Колебательное движение» and «Волны», so the numbering differs from the Лань reprint. Not checked.
- Chapter lists of 5-volume Т. 3–5, and of the 5-book АСТ edition.
- Exact edition numbers: shops disagree (see above).
- A 1998 Наука 5-book printing appears only in reading-list snippets.

### 2. Д. В. Сивухин «Общий курс физики» в 5 томах

- **Author:** Дмитрий Васильевич Сивухин. The course is based on his lectures at МФТИ (Физматлит annotation).
- **Publisher:** Физматлит (Москва).
- **Editions verified (current Физматлит printings):**
  - Т. I «Механика»: 2022 printing, 560 с., ISBN 978-5-9221-1512-4. The annotation says the edition differs only slightly from the 2nd edition of 1979.
  - Т. II «Термодинамика и молекулярная физика»: Изд. 6, 544 с., ISBN 978-5-9221-1514-8. fml.ru gives 2017; labirint and my-shop show a 2024 printing (6-е изд., стереотипное).
  - Т. III «Электричество»: 6-е изд., стер., 656 с., ISBN 978-5-9221-1643-5. Znanium gives 2015, labirint a 2020 printing.
  - Т. IV «Оптика»: Изд. 4, 792 с., ISBN 978-5-9221-1735-7. fml.ru gives 2017; fmllib.ru 2021 and my-shop 2024 are printings.
  - Т. V «Атомная и ядерная физика»: Изд. 3, 784 с., ISBN 978-5-9221-0645-0. The fml.ru year field says 2020; the 3rd edition first appeared in 2006 (description); my-shop shows a 2024 printing.
- **Level:** University physics. The annotation addresses it «для студентов физических и математических факультетов университетов, физико-технических и инженерно-физических институтов, а также вузов, где физика является основной дисциплиной» (labirint, Т. II). My assessment: a level above Savelyev.
- **Open:** no.

**Contents:**

- Т. I Механика: I Кинематика; II Законы Ньютона; III Некоторые следствия и применения законов Ньютона; IV Работа и энергия; V Момент импульса; VI Гармонические колебания; VII Механика твердого тела; VIII Тяготение; IX Движение относительно неинерциальных систем отсчета; X Механика упругих тел; XI Методы подобия и размерности; XII Механика жидкостей и газов; Приложение.
- Т. II Термодинамика и молекулярная физика: I Температура; II Первое начало термодинамики; III Второе начало термодинамики; IV Теплопроводность (the shop card prints «Теплопроводимость», probably a typo); V Простейшие вопросы молекулярно-кинетической теории вещества; VI Статистические распределения; VII Явления переноса в газах; VIII Реальные газы; IX Поверхностное натяжение; X Фазовые равновесия и фазовые превращения; XI Растворы; XII Симметрия и строение кристаллов; Приложение.
- Т. III Электричество: I Электрическое поле; II Электрический ток; III Магнитное поле; IV Уравнения Максвелла; V Движение заряженных частиц в электромагнитных полях; VI Электролиты; VII Электрические токи в металлах, полупроводниках и вакууме; VIII Электрические явления в контактах; IX Электрические токи в газах; X Колебания и волны.
- Т. IV Оптика: I Введение; II Геометрическая теория оптических изображений; III Интерференция света; IV Дифракция света; V Отражение и преломление света; VI Оптика металлов; VII Кристаллооптика; VIII Молекулярная оптика; IX Теория относительности; X Тепловое излучение; XI Лазеры и нелинейная оптика.
- Т. V Атомная и ядерная физика: I Кванты света; II Строение, энергетические уровни и спектры атома; III Волновые свойства частиц вещества; IV Уравнение Шредингера. Квантование; V Дальнейшее построение квантовой механики и спектры; VI Атомные системы со многими электронами; VII Некоторые макроскопические квантовые явления; VIII Статические свойства атомного ядра; IX Радиоактивность; X Краткие сведения о ядерных моделях; XI Прохождение заряженных частиц и гамма-квантов через вещество; XII Источники и методы регистрации ядерных частиц; XIII Ядерные реакции; XIV Нейтроны и деление атомных ядер; XV Некоторые вопросы астрофизики; XVI Элементарные частицы.

**Verified from:**
- https://my-shop.ru/shop/product/1775460.html (Т. I «Содержание»)
- https://my-shop.ru/shop/product/1775459.html (Т. II)
- https://znanium.ru/catalog/document?id=303207 (Т. III: Znanium catalogue record with chapter list)
- https://my-shop.ru/shop/product/2598324.html (Т. IV)
- https://my-shop.ru/shop/product/395448.html (Т. V)
- http://www.fml.ru/book/katalog/3 and http://www.fml.ru/book/showbook/645, /1667, /1868 (publisher catalogue: editions, ISBNs; no TOC)
- https://www.labirint.ru/books/509943/, /509944/ (editions, annotation)
- http://fmllib.ru/uchebnaya-literatura/5938/ (Т. IV, 2021, 792 с.)

**Not verified:**
- Т. II ch. IV: the shop card prints «Теплопроводимость»; «Теплопроводность» is my reading, not checked against the book.
- First-edition years of each volume (Наука, 1970s–80s).

### 3. И. Е. Иродов

#### 3a. «Задачи по общей физике» (problem book)

- **Editions verified:**
  - Лань: 22-е изд., стер., 416 с., ISBN 978-5-507-55216-0 (lanbook.ru; year field 2026, header 2025). The annotation says about 2000 problems on all sections of the general course, with the structure unchanged from the 1988 edition.
  - Лаборатория знаний (series «Общая физика»): 2021, 434 с., ISBN 978-5-93208-513-4 (LitRes card). The annotation says more than 2000 problems, distributed over механика, электромагнетизм, колебания и волны, оптика, квантовая физика, физика макросистем.
- **Level:** Physics and engineering students; usable in втузы.
- **Open:** no.

**Contents** (the parts and sections the fetched page shows; the page attributes them to the Наука edition of 1979, and they match the Лань «1988 structure» edition):
- 1 Механика: 1.1 Кинематика; 1.2 Основное уравнение динамики; 1.3 Законы сохранения энергии, импульса и момента импульса; 1.4 Всемирное тяготение; 1.5 Динамика твердого тела; 1.6 Упругие деформации твердого тела; 1.7 Гидродинамика; 1.8 Релятивистская механика.
- 2 Термодинамика и молекулярная физика: 2.1 Уравнение состояния газа. Процессы; 2.2 Первое начало термодинамики. Теплоемкость; 2.3 Молекулярно-кинетическая теория. Распределения Максвелла и Больцмана; 2.4 Второе начало термодинамики. Энтропия; 2.5 Жидкости. Капиллярные явления; 2.6 Фазовые превращения; 2.7 Явления переноса.
- 3 Электродинамика: 3.1 Постоянное электрическое поле в вакууме; 3.2 Проводники и диэлектрики в электрическом поле; 3.3 Электроемкость. Энергия электрического поля; 3.4 Электрический ток; 3.5 Постоянное магнитное поле. Магнетики; 3.6 Электромагнитная индукция. Уравнения Максвелла; 3.7 Движение заряженных частиц в электрическом и магнитном полях.
- 4 Колебания и волны: 4.1 Механические колебания; 4.2 Электрические колебания; 4.3 Упругие волны. Акустика; 4.4 Электромагнитные волны. Излучение.
- 5 Оптика; 6 Атомная и ядерная физика: (snippet) only, see below.

**Verified from:**
- https://lanbook.ru/catalog/fizika/zadachi-po-obshchey-fizike/
- https://www.litres.ru/book/igor-irodov/zadachi-po-obschey-fizike-uchebnoe-posobie-dlya-vuzov-6561843/
- https://4stu.ru/physics/irodov (a solutions site; it lists parts 1–4 with sections)

**Not verified:**
- Parts 5 «Оптика» and 6 «Атомная и ядерная физика» with their sections (search snippets only).
- The exact part structure of the Лаборатория знаний edition (its annotation lists a different grouping, ending with квантовая физика and физика макросистем).

#### 3b. Course «… Основные законы» (Лаборатория знаний, formerly БИНОМ. Лаборатория знаний)

- «Механика. Основные законы»: Лаборатория знаний, 2021, 312 с., ISBN 978-5-93208-519-6 (books.mipt.ru, LitRes). There is also a 2023 printing of 309 с., ISBN 978-5-93208-291-1 (mdk-arbat.ru). Annotation: Newtonian and relativistic mechanics; laws of motion; conservation of momentum, energy and angular momentum; many examples and problems; for students of physical specialities.
- «Электромагнетизм. Основные законы», «Волновые процессы. Основные законы», «Квантовая физика. Основные законы»: listed in the LitRes series «Общая физика (Лаборатория знаний)». The pages give no edition data.
- «Физика макросистем. Основные законы»: not in that LitRes series page. Editions (БИНОМ, 2006, изд. 3, 208 с.) appear in snippets of the MSU biophysics catalogue only.
- **Level:** physics departments. **Open:** no.

**Contents:** Chapter lists NOT verified for any of the five books. No legal page with a text TOC could be fetched: rucont.ru returned 403; e.lanbook.com and the LitRes reader are JavaScript-only; prosv.ru (the successor of lbz.ru) requires login.

**Verified from:**
- https://books.mipt.ru/book/301643
- https://www.litres.ru/series/obschaya-fizika-laboratoriya-znaniy-678727/
- https://www.litres.ru/book/igor-irodov/mehanika-osnovnye-zakony-6724450/
- https://mdk-arbat.ru/book/4326561

### 4. Л. Д. Ландау, Е. М. Лифшиц «Теоретическая физика» в 10 томах

- **Publisher (current):** Физматлит. Earlier publishers: ГИТТЛ, Гостехиздат, Физматгиз, Наука.
- **Ten volumes** (titles and authors per ru.wikipedia):
  - I Механика
  - II Теория поля
  - III Квантовая механика (нерелятивистская теория)
  - IV Квантовая электродинамика (В. Б. Берестецкий, Е. М. Лифшиц, Л. П. Питаевский)
  - V Статистическая физика. Часть 1
  - VI Гидродинамика
  - VII Теория упругости
  - VIII Электродинамика сплошных сред
  - IX Статистическая физика. Часть 2 («Теория конденсированного состояния»; Е. М. Лифшиц, Л. П. Питаевский)
  - X Физическая кинетика (Е. М. Лифшиц, Л. П. Питаевский)
  - All other volumes are by Ландау and Лифшиц.
- **Current Физматлит editions verified** (series «Теоретическая физика-N»; ред. Л. П. Питаевский):
  - I: Изд. 7, 2025, 224 с., ISBN 978-5-9221-1611-4.
  - II: Изд. 9, 2016, 508 с., ISBN 978-5-9221-1568-1.
  - III: Изд. 6, 2024, 800 с., ISBN 978-5-9221-0530-9.
  - V: 2021, 616 с., ISBN 978-5-9221-1510-0 (urss.ru).
  - VI: Изд. 6, 2020, 728 с., ISBN 978-5-9221-1625-1.
  - VIII: Изд. 4, 2023, 656 с., ISBN 978-5-9221-1702-9.
- **Level:** Theoretical physics for senior undergraduates, graduate students and researchers. The fml.ru annotation says «для студентов старших курсов физических специальностей вузов, а также аспирантов и научных работников».
- **Open:** no.
- **English edition: Course of Theoretical Physics** (Pergamon; later Butterworth-Heinemann; latest English editions per en.wikipedia):
  - 1 Mechanics: 3rd ed. 1976.
  - 2 The Classical Theory of Fields: 4th ed. 1975.
  - 3 Quantum Mechanics: Non-Relativistic Theory: 3rd ed. 1977.
  - 4 Quantum Electrodynamics: 2nd ed. 1982.
  - 5 Statistical Physics: 3rd ed. 1980.
  - 6 Fluid Mechanics: 2nd ed. 1987.
  - 7 Theory of Elasticity: 3rd ed. 1986.
  - 8 Electrodynamics of Continuous Media: 2nd ed. 1984.
  - 9 Statistical Physics Part 2: 1980.
  - 10 Physical Kinetics: 1981.

**Contents (chapter titles):**

- Т. I Механика: I Уравнения движения; II Законы сохранения; III Интегрирование уравнений движения; IV Столкновение частиц; V Малые колебания; VI Движение твердого тела; VII Канонические уравнения.
- Т. II Теория поля: I Принцип относительности; II Релятивистская механика; III Заряд в электромагнитном поле; IV Уравнения электромагнитного поля; V Постоянное электромагнитное поле; VI Электромагнитные волны; VII Распространение света; VIII Поле движущихся зарядов; IX Излучение электромагнитных волн; X Частица в гравитационном поле; XI Уравнения гравитационного поля; XII Поле тяготеющих тел; XIII Гравитационные волны; XIV Релятивистская космология.
- Т. III Квантовая механика: I Основные понятия квантовой механики; II Энергия и импульс; III Уравнение Шредингера; IV Момент импульса; V Движение в центрально-симметричном поле; VI Теория возмущений; VII Квазиклассический случай; VIII Спин; IX Тождественность частиц; X Атом; XI Двухатомная молекула; XII Теория симметрии; XIII Многоатомные молекулы; XIV Сложение моментов; XV Движение в магнитном поле; XVI Структура атомного ядра; XVII Упругие столкновения; XVIII Неупругие столкновения; Математические дополнения.
- Т. V Статистическая физика, ч. 1 (English 3rd ed.; Russian wording not verified): I The Fundamental Principles of Statistical Physics; II Thermodynamic Quantities; III The Gibbs Distribution; IV Ideal Gases; V The Fermi and Bose Distributions; VI Solids; VII Non-Ideal Gases; VIII Phase Equilibrium; IX Solutions; X Chemical Reactions; XI Properties of Matter at Very High Density; XII Fluctuations; XIII The Symmetry of Crystals; XIV Phase Transitions of the Second Kind and Critical Phenomena; XV Surfaces.
- Т. VI Гидродинамика: 1 Идеальная жидкость; 2 Вязкая жидкость; 3 Турбулентность; 4 Пограничный слой; 5 Теплопроводность в жидкости; 6 Диффузия; 7 Поверхностные явления; 8 Звук; 9 Ударные волны; 10 Одномерное движение сжимаемого газа; 11 Пересечение поверхностей разрыва; 12 Плоское течение сжимаемого газа; 13 Обтекание конечных тел; 14 Гидродинамика горения; 15 Релятивистская гидродинамика; 16 Гидродинамика сверхтекучей жидкости.
- Т. VIII Электродинамика сплошных сред: I Электростатика проводников; II Электростатика диэлектриков; III Постоянный ток; IV Постоянное магнитное поле; V Ферромагнетизм и антиферромагнетизм; VI Сверхпроводимость; VII Квазистационарное электромагнитное поле; VIII Магнитная гидродинамика; IX Уравнения электромагнитных волн; X Распространение электромагнитных волн; XI Электромагнитные волны в анизотропных средах; XII Пространственная дисперсия; XIII Нелинейная оптика; XIV Прохождение быстрых частиц через вещество; XV Рассеяние электромагнитных волн; XVI Дифракция рентгеновых лучей в кристаллах.

**Verified from:**
- http://www.fml.ru/tocs/1568.pdf (Т. II publisher TOC, 7th-edition text; read page by page) and http://www.fml.ru/tocs/530.pdf (Т. III publisher TOC)
- http://www.fml.ru/book/showbook/1755, /1678, /530, /1758, /1836 (editions, annotations)
- https://my-shop.ru/shop/product/9770.html (Т. I), https://my-shop.ru/shop/product/2056054.html (Т. VI), https://my-shop.ru/shop/product/407931.html (Т. VIII)
- https://shop.elsevier.com/books/course-of-theoretical-physics/landau/978-0-08-023038-2 (Vol. 5 English chapters)
- https://urss.ru/cgi-bin/db.pl?lang=Ru&blang=ru&page=Book&id=278407 (Т. V edition)
- https://ru.wikipedia.org/wiki/Курс_теоретической_физики_Ландау_и_Лифшица (10 titles, Russian edition history)
- https://en.wikipedia.org/wiki/Course_of_Theoretical_Physics (English editions)

**Not verified:** Russian chapter titles of Т. V. Other fml.ru TOC PDFs were tried, but /tocs/1755, 1758 and 1836 turned out to belong to other books.

---

## Part 2: Research-level references (2–4 per field)

"Open" means a legal free copy exists (OA journal, arXiv, publisher site).

### General relativity and black holes

| Reference | Edition / year / publisher | Covers | Open? | Verified from |
|---|---|---|---|---|
| C. W. Misner, K. S. Thorne, J. A. Wheeler, *Gravitation* | 2017 edition, Princeton University Press (pub. 24 Oct 2017, ©2018), 1336 pp., ISBN 9780691177793; new introduction by Misner & Thorne, preface by D. Kaiser. Orig. W. H. Freeman, 1973 | The graduate GR encyclopaedia: geometry, stars, collapse, black holes, gravitational waves, cosmology | no | https://press.princeton.edu/books/hardcover/9780691177793/gravitation ; https://en.wikipedia.org/wiki/Gravitation_(book) |
| R. M. Wald, *General Relativity* | University of Chicago Press, 1984, 506 pp., ISBN 9780226870335 | Rigorous, geometric standard graduate text (causal structure, singularities, black holes) | no | https://press.uchicago.edu/ucp/books/book/chicago/G/bo5952261.html |
| S. Chandrasekhar, *The Mathematical Theory of Black Holes* | Oxford University Press, print 3 Sep 1998 (Oxford Classic Texts reissue; written 1983), ISBN 9780198503705 | Schwarzschild, Reissner–Nordström and Kerr space-times; geodesics; perturbations; EM and gravitational waves in Kerr; spin-½ in Kerr | no | https://academic.oup.com/book/52805 |
| Event Horizon Telescope Collaboration, "First M87 Event Horizon Telescope Results. I. The Shadow of the Supermassive Black Hole" | ApJL 875, L1 (10 Apr 2019), doi:10.3847/2041-8213/ab0ec7 | Overview paper (paper I) of the first M87* results series: the shadow of the supermassive black hole | yes (OA) | https://iopscience.iop.org/article/10.3847/2041-8213/ab0ec7 |

### Gravitational waves

| Reference | Edition / year / publisher | Covers | Open? | Verified from |
|---|---|---|---|---|
| M. Maggiore, *Gravitational Waves. Vol. 1: Theory and Experiments* | Oxford University Press, 2007, ISBN 9780198570745 (retailers give 576 pp.; Open Library 288) | GW theory (linearised GR, generation, post-Newtonian sources) and detectors and data analysis | no | https://openlibrary.org/isbn/9780198570745.json (+ publisher-blurb snippets) |
| M. Maggiore, *Gravitational Waves. Vol. 2: Astrophysics and Cosmology* | Oxford University Press, 22 May 2018, ISBN 9780198570899 | Astrophysical and cosmological GW sources (optional companion) | no | https://openlibrary.org/isbn/9780198570899.json |
| L. Blanchet, "Gravitational Radiation from Post-Newtonian Sources and Inspiralling Compact Binaries" | Living Rev. Relativ. 17, 2 (2014), pub. 13 Feb 2014, doi:10.12942/lrr-2014-2; fast-track revisions Jan/Feb 2016 | PN dynamics and waveforms of compact binaries, radiation reaction, spins, eccentric orbits | yes | https://www.maths.tcd.ie/EMIS/journals/LRG/Articles/lrr-2014-2/ (EMIS mirror of Living Reviews); canonical URL https://doi.org/10.12942/lrr-2014-2 |
| L. Blanchet, "Post-Newtonian theory for gravitational waves" (the current successor of the 2014 review) | Living Rev. Relativ. 27, 4 (2024), online 10 Jul 2024, doi:10.1007/s41114-024-00050-z, CC BY 4.0 | Same scope, updated (285 pp., 600 refs) | yes | https://arxiv.org/abs/1310.1528 (v6 comments: matches LRR 27, 4 (2024)); https://api.crossref.org/works/10.1007/s41114-024-00050-z |

### Special relativity: Thomas–Wigner rotation and relativistic visual appearance

| Reference | Edition / year / publisher | Covers | Open? | Verified from |
|---|---|---|---|---|
| É. Gourgoulhon, *Special Relativity in General Frames: From Particles to Astrophysics* | Springer, 2013 (Graduate Texts in Physics), 784 pp., ISBN 978-3-642-37275-9 (print) / 978-3-642-37276-6 (online), doi:10.1007/978-3-642-37276-6; foreword T. Damour | 4D-geometric SR: Lorentz group and its Lie algebra, accelerated and rotating observers, EM field, relativistic hydrodynamics | no | https://relativite.obspm.fr/sperel/outlook.html (chapter list); https://bookshare.org/browse/book/1435032 |
| J. Terrell, "Invisibility of the Lorentz Contraction" | Phys. Rev. 116, 1041 (15 Nov 1959), doi:10.1103/PhysRev.116.1041 | Fast objects photographed appear rotated, not contracted (Terrell rotation) | no | https://journals.aps.org/pr/abstract/10.1103/PhysRev.116.1041 |
| R. Penrose, "The apparent shape of a relativistically moving sphere" | Math. Proc. Camb. Phil. Soc. 55(1), 137–139 (Jan 1959), doi:10.1017/S0305004100033776 | A moving sphere still has a circular outline | no | https://www.cambridge.org/core/product/identifier/S0305004100033776/type/journal_article |
| L. H. Thomas, "The Motion of the Spinning Electron"; E. Wigner, "On Unitary Representations of the Inhomogeneous Lorentz Group" | Nature 117, 514 (10 Apr 1926), doi:10.1038/117514a0; Ann. Math. 40(1), 149 (1939), doi:10.2307/1968551 | Original sources of Thomas precession and Wigner rotation (little group) | no | https://api.crossref.org/works/10.1038/117514a0 ; https://api.crossref.org/works/10.2307/1968551 |

### Classical electrodynamics and optics

| Reference | Edition / year / publisher | Covers | Open? | Verified from |
|---|---|---|---|---|
| J. D. Jackson, *Classical Electrodynamics* (added as the standard graduate text) | 3rd ed., Wiley, 1999, ISBN 978-0-471-30932-1 | Graduate electrodynamics; SI in ch. 1–10; radiation, relativity, scattering | no | https://en.wikipedia.org/wiki/Classical_Electrodynamics_(book) |
| M. Born, E. Wolf, *Principles of Optics* | 7th (expanded) ed., Cambridge University Press, 1999 (online 2013, doi:10.1017/CBO9781139644181); 60th Anniversary Edition = reissue of the 7th, CUP 2019, ISBN 978-1-108-47743-7 | EM theory of light propagation, interference, diffraction, coherence, crystal and metal optics | no | https://www.cambridge.org/core/books/principles-of-optics/D12868B8AE26B83D6D3C2193E94FFC32 ; https://en.wikipedia.org/wiki/Principles_of_Optics |
| C. F. Bohren, D. R. Huffman, *Absorption and Scattering of Light by Small Particles* | Wiley(-VCH), softcover April 1998, xiv+530 pp., ISBN 978-0-471-29340-8 (orig. Wiley 1983) | Mie theory, small-particle absorption and scattering, optical constants | no | https://www.wiley-vch.de/en/areas-interest/natural-sciences/absorption-and-scattering-of-light-by-small-particles-978-0-471-29340-8 |
| A. Taflove, S. C. Hagness, *Computational Electrodynamics: The Finite-Difference Time-Domain Method* | 3rd ed., Artech House, June 2005, 1038 pp., ISBN 978-1-58053-832-9 | FDTD (Yee) method: stability, dispersion, absorbing boundaries/PML, sources, dispersive media | no | https://www.schweitzer-online.de/en/buch/Taflove/Computational-Electrodynamics-Finite-Difference-Time-Domain-Method-Third-Edition/9781580538329/A15423811/ |
| L. Allen, M. W. Beijersbergen, R. J. C. Spreeuw, J. P. Woerdman, "Orbital angular momentum of light and the transformation of Laguerre-Gaussian laser modes" | Phys. Rev. A 45, 8185 (1 Jun 1992), doi:10.1103/PhysRevA.45.8185 | Laguerre–Gauss beams carry orbital angular momentum ℓħ per photon; mode converters | no | https://journals.aps.org/pra/abstract/10.1103/PhysRevA.45.8185 |

### Quantum mechanics foundations

| Reference | Edition / year / publisher | Covers | Open? | Verified from |
|---|---|---|---|---|
| J. S. Bell, *Speakable and Unspeakable in Quantum Mechanics: Collected Papers on Quantum Philosophy* | 2nd ed., introduction by A. Aspect, Cambridge University Press, 3 Jun 2004, ISBN 9780521818629 (hb) / 9780521523387 (pb), doi:10.1017/CBO9780511815676 | Bell inequalities, hidden variables, measurement problem, pilot wave | no | https://www.cambridge.org/core/books/speakable-and-unspeakable-in-quantum-mechanics/E0D032E7E7EDEF4E4AD09F458F2D9DB7 |
| J. G. Muga, R. Sala Mayato, Í. L. Egusquiza (eds.), *Time in Quantum Mechanics* [Vol. 1]; G. Muga, A. Ruschhaupt, A. del Campo (eds.), *Time in Quantum Mechanics II* [Vol. 2] | Vol. 1: Springer Lecture Notes in Physics, 2008 (2nd ed.), doi:10.1007/978-3-540-73473-4. Vol. 2: Springer LNP, 2009, doi:10.1007/978-3-642-03174-8. LNP volume numbers 734 and 789 come from snippets. **Note: the Vol. 2 editors differ from Vol. 1.** | Arrival, dwell and tunnelling times; time–energy uncertainty; quantum clocks | no | https://api.crossref.org/works/10.1007/978-3-540-73473-4 ; https://api.crossref.org/works/10.1007/978-3-642-03174-8 |
| H.-P. Breuer, F. Petruccione, *The Theory of Open Quantum Systems* | Oxford University Press; hardback 2002 (ISBN 9780198520634, snippet); paperback 25 Jan 2007, 640 pp., ISBN 978-0-19-921390-0 | Master equations (Lindblad), quantum trajectories, non-Markovian dynamics, decoherence | no | https://www.schweitzer-online.de/en/buch/Breuer/Theory-Open-Quantum-Systems/9780199213900/A1034741/ |
| M. A. Nielsen, I. L. Chuang, *Quantum Computation and Quantum Information* | 10th Anniversary Edition, Cambridge University Press, 2010, ISBN 978-1-107-00217-3 (1st ed. 2000) | Qubits, circuits, algorithms, noise, error correction, quantum information theory | no | https://en.wikipedia.org/wiki/Quantum_Computation_and_Quantum_Information |

### Atomic physics

| Reference | Edition / year / publisher | Covers | Open? | Verified from |
|---|---|---|---|---|
| H. A. Bethe, E. E. Salpeter, *Quantum Mechanics of One- and Two-Electron Atoms* | Springer (and Academic Press), 1957, doi:10.1007/978-3-662-12869-5; Dover unabridged reprint 2008, 384 pp., ISBN 9780486466675 | Hydrogen and helium exactly: fine and hyperfine structure, Lamb shift, Stark and Zeeman effects, radiative transitions | no | https://api.crossref.org/works/10.1007/978-3-662-12869-5 ; https://openlibrary.org/isbn/9780486466675.json |
| C. J. Foot, *Atomic Physics* | Oxford University Press, 2005, Oxford Master Series in Physics 7, xiii+331 pp., ISBN 0198506961 (pb) | Hydrogen, helium, alkalis, laser cooling and trapping, BEC, atom interferometry, ion traps | no | https://openlibrary.org/isbn/9780198506966.json |

### QCD and particle physics

| Reference | Edition / year / publisher | Covers | Open? | Verified from |
|---|---|---|---|---|
| M. E. Peskin, D. V. Schroeder, *An Introduction to Quantum Field Theory* | Addison-Wesley, 1995, ISBN 0-201-50397-2 | Three parts: QED with Feynman diagrams; Wilsonian renormalisation; non-Abelian gauge theories (incl. QCD) and the Standard Model | no | https://en.wikipedia.org/wiki/An_Introduction_to_Quantum_Field_Theory |
| R. K. Ellis, W. J. Stirling, B. R. Webber, *QCD and Collider Physics* | Cambridge University Press, 24 Oct 1996, Cambridge Monographs on Particle Physics, Nuclear Physics and Cosmology 8, pb ISBN 9780521545891, doi:10.1017/CBO9780511628788 | Perturbative QCD, parton distributions, jets, e⁺e⁻/DIS/hadron-collider phenomenology | no | https://www.cambridge.org/core/books/qcd-and-collider-physics/D0095E6D278BBBC74E9C3636AB4CB80C |
| Particle Data Group, *Review of Particle Physics* | 2026 edition: F. Takahashi et al. (PDG), Int. J. Mod. Phys. A 41, 2630011 (2026), doi:10.1142/S0217751X26300115 | Particle properties, constants, reviews (QCD, α_s, CKM, cosmology parameters…) | yes | https://pdg.lbl.gov/ |

### Statistical mechanics and molecular simulation

| Reference | Edition / year / publisher | Covers | Open? | Verified from |
|---|---|---|---|---|
| M. P. Allen, D. J. Tildesley, *Computer Simulation of Liquids* | 2nd ed., Oxford University Press, 22 Jun 2017, 642 pp., ISBN 978-0-19-880319-5 | MD and Monte Carlo of liquids: force fields, integrators, ensembles, long-range forces, analysis. Companion code in Fortran and Python (snippet) | no | https://www.schweitzer-online.de/en/buch/Allen/Computer-Simulation-Liquids/9780198803195/A40379464/ |
| D. Frenkel, B. Smit, *Understanding Molecular Simulation: From Algorithms to Applications* | 3rd ed., Academic Press (Elsevier), San Diego, 2023, doi:10.1016/C2009-0-63921-0 (pb ISBN 9780323902922, snippet) | MC and MD from a stat-mech viewpoint; free energies, rare events, advanced sampling | no | https://www.epfl.ch/labs/lsmo/3rd-edition-of-understanding-molecular-simulation |
| Л. Д. Ландау, Е. М. Лифшиц, *Статистическая физика*, ч. 1 (LL V) / *Statistical Physics*, Part 1 | Физматлит 2021 (ISBN 978-5-9221-1510-0); English 3rd ed. 1980 | Theory backbone (Gibbs distribution, fluctuations, phase transitions) | no | Part 1 §4 sources |

### Fluid dynamics

| Reference | Edition / year / publisher | Covers | Open? | Verified from |
|---|---|---|---|---|
| Л. Д. Ландау, Е. М. Лифшиц, *Гидродинамика* (LL VI) / *Fluid Mechanics* | Физматлит, Изд. 6, 2020, ISBN 978-5-9221-1625-1; English 2nd ed. 1987 (Pergamon/Butterworth-Heinemann) | Ideal and viscous flow, turbulence, boundary layers, sound, shocks, relativistic and superfluid hydrodynamics (16 chapters, Part 1 §4) | no | http://www.fml.ru/book/showbook/1758 ; https://my-shop.ru/shop/product/2056054.html ; en.wikipedia Course_of_Theoretical_Physics |
| G. K. Batchelor, *An Introduction to Fluid Dynamics* | Cambridge University Press, 1967; Cambridge Mathematical Library edition 15 Feb 2000, ISBN 9780521663960 (online 2012, chapter DOIs 10.1017/CBO9780511800955.*) | Classic introduction: kinematics, Navier–Stokes, viscous flow first, then high-Re flows and irrotational theory | no | https://openlibrary.org/isbn/9780521663960.json ; https://cambridge.org/core/books/an-introduction-to-fluid-dynamics/preface/CE61FF7BA7475C68B794914EF566BDC3 |
| T. Krüger, H. Kusumaatmaja, A. Kuzmin, O. Shardt, G. Silva, E. M. Viggen, *The Lattice Boltzmann Method: Principles and Practice* | Springer (Cham), ©2017 (released Nov 2016), Graduate Texts in Physics, ISBN 9783319446493 (e) / 978-3-319-44647-9 (hb), doi:10.1007/978-3-319-44649-3 | LBM theory and implementation: BGK/MRT collisions, boundaries, forces, multiphase, thermal | no | https://www.bookshare.org/browse/book/1529995 (+ snippets of the Springer page) |

### Cosmology

| Reference | Edition / year / publisher | Covers | Open? | Verified from |
|---|---|---|---|---|
| S. Weinberg, *Cosmology* | Oxford University Press, 21 Feb 2008, 624 pp., ISBN 978-0-19-852682-7 | Expansion, CMB, early universe, inflation, structure growth, lensing (graduate) | no | https://www.schweitzer-online.de/en/buch/Weinberg/Cosmology/9780198526827/A926451/ |
| S. Dodelson, F. Schmidt, *Modern Cosmology* | 2nd ed., Elsevier/Academic Press, 18 Apr 2020, ISBN 9780128159484. **A 3rd ed. exists:** Elsevier, dated 19 Dec 2024 / 27 Mar 2025, ISBN 9780443288289 | Boltzmann equations, perturbations, CMB anisotropies, LSS, nonlinear structure, data analysis | no | https://shop.elsevier.com/books/catalog/isbn/9780128159484 ; https://shop.elsevier.com/books/catalog/isbn/9780443288289 |
| Planck Collaboration (N. Aghanim et al.), "Planck 2018 results. VI. Cosmological parameters" | A&A 641, A6 (2020), doi:10.1051/0004-6361/201833910; arXiv:1807.06209 (v4 9 Aug 2021) | ΛCDM parameter constraints from Planck CMB | yes | https://arxiv.org/abs/1807.06209 ; https://api.crossref.org/works/10.1051/0004-6361/201833910 |

### Condensed matter

| Reference | Edition / year / publisher | Covers | Open? | Verified from |
|---|---|---|---|---|
| N. W. Ashcroft, N. D. Mermin, *Solid State Physics* | 1976, Holt, Rinehart and Winston (Wikipedia: Saunders College Publishing), ISBN 0-03-083993-9 | Standard introductory-graduate solid-state text: lattices, Bloch electrons, phonons, transport, semiconductors, magnetism | no | https://openlibrary.org/isbn/9780030839931.json ; https://en.wikipedia.org/wiki/Ashcroft_and_Mermin |

**Part 2 items checked only through snippets or secondary pages:**
- Maggiore Vol. 1 page count.
- Born & Wolf 60th-anniversary details (retailer pages returned 403; the Wikipedia edition table was used).
- Frenkel & Smit paperback ISBN.
- Krüger et al. hardcover ISBN and release date.
- LNP volume numbers 734 and 789.
- Breuer & Petruccione 2002 hardback ISBN.
- Peskin & Schroeder later reprints (CRC/Westview) not checked.

---

## Section order in the Russian general-physics course

Both general courses run механика → молекулярная физика и термодинамика → электричество и магнетизм → колебания и волны / оптика → атомная, квантовая и ядерная физика (Savelyev's last volume adds физика твёрдого тела and элементарные частицы).

The courses place two topics differently:
- **Special relativity.** Savelyev puts it in mechanics (Т. 1 ch. VIII «Релятивистская механика», plus «Оптика движущихся сред» at the end of optics). Sivukhin puts it in optics (Т. IV ch. IX «Теория относительности»).
- **Waves.** Savelyev puts упругие и электромагнитные волны between electromagnetism and optics. Sivukhin closes the electricity volume with «Колебания и волны».

Landau–Lifshitz, the theoretical tier, follows the same arc at a higher level: Механика → Теория поля (SR, electrodynamics, GR, GW, cosmology) → Квантовая механика → КЭД → Статфизика → Гидродинамика → Упругость → Электродинамика сплошных сред → Статфизика ч. 2 → Физическая кинетика.

---

# Appendix D. How public collections of interactive physics demos are structured

Research date: 2026-11-12. Web research only; structure described, content not copied.
Status: DONE (all 5 collections + 2 optional, comparison table, patterns).

## 1. PhET Interactive Simulations (University of Colorado Boulder)

Access note: the site renders in the browser with JavaScript, so WebFetch saw only the header and footer. The facts below come from (a) the server-side data block (`<template id="phet-ssr-data">`) in the raw HTML of a sim page, and (b) PhET's public metadata service, `/services/metadata/1.3/simulations?format=json&type=html[&locale=en][&summary]`. That service is the website's own catalogue data, not simulation code. All counts are as of 2026-11-12.

- **Organisation by topic.** The category tree in the metadata has one root with these subjects: **Physics, Biology, Chemistry, Earth & Space, Math & Statistics**, plus three cross-cutting groups: **By Grade Level, By Device, HTML5**. The hierarchy is two levels deep. Physics has 7 subcategories: *Motion · Sound & Waves · Work, Energy & Power · Heat & Thermo · Quantum Phenomena · Light & Radiation · Electricity, Magnets & Circuits*. Chemistry has *General Chemistry / Quantum Chemistry*, and Math has *Math Concepts / Math Applications*. The subcategories roughly follow the chapter order of an introductory textbook (mechanics, then waves, energy, thermo, modern physics, light, E&M), but they are tags rather than chapters: a sim belongs to several categories. A sim also carries `topicIds` and `keywordIds` (662 keywords) for search and for the "Kinematics • Vectors • …" line in the page title. The site navigation also offers "All Sims", "Translated Sims" and "Customizable Sims".
- **Organisation by level.** "By Grade Level" has 4 labels: **Elementary School, Middle School, High School, University**. Each sim stores a range (`lowGradeLevel`..`highGradeLevel`, 0–3), so one sim can carry several badges. 39 of 127 HTML5 sims are tagged High–University and 21 span all four levels. There is also a filter "By Device" (iPad/Tablet, Chromebook).
- **How an entry is presented** (fields in each sim's metadata): a 128 px thumbnail and a 600 px screenshot, plus alternate screenshots (`altImageCount`); a localized **title**; a **description** of one or two sentences; **learning goals** (a bulleted list); a **Teacher Tips** PDF (`teachersGuide`); a short **video** primer (`videoUrl`); **related simulations**; credits (design team, third-party libraries, thanks); `runUrl` (run in the browser) and `downloadUrl` (one HTML file per language), plus an "all locales" build; standards **alignments** (in the current data: Common Core Math, with ASN URIs) and AAAS Science Literacy Map keys; and **inclusive-design / accessibility features** as filterable codes. A third-party teaching hub describes the feature set as alternative input such as keyboard navigation, sound and sonification, interactive description (screen reader), interactive description on mobile, pan and zoom, and voicing. Teacher-contributed **Activities** live in a separate section with "Activity Contribution Guidelines". The website also has a paid "PhET Studio" customisation tier and PhET-iO (an interoperable build licensed separately).
- **Technology.** Current sims are HTML5. Legacy Java and Flash sims are kept as "legacy" (`legacyType`), and some Java sims run in the browser through CheerpJ (`isCheerpj`). The FAQ says offline use is supported through the PhET apps ("native, offline use of all of our HTML5 sims").
- **Languages.** Sims are translated by volunteers. The web-based **Translation Utility** is at `/<locale>/for-translators/translation-utility`, and PhET also runs a structured "PhET Translator Network". Each language is a separate build (`…_<locale>.html`) with its own language page (`/<locale>/simulations/<sim>`). Counts: **130 distinct locales** across the 127 HTML5 sims; **Russian (`ru`) is available for 90 of 127 HTML5 sims**. Translation depth varies by layer. Sim UI and title are translated per locale. The **description and learning goals are translated for far fewer locales**: for Projectile Motion, 26 of 80 locales have a description, and **Russian has the title only, with no description and no learning goals**. Website category names exist in 48 locales, **not including Russian**. On `/ru/...` the website chrome is still in English in the server-rendered data.
- **Licence** (2026 change).
  - Historical versions (published **before 2026-03-29**): "published under the Creative Commons Attribution 4.0 License (CC BY 4.0)", with a required attribution line. The agreement "does not pertain to" Regular HTML Simulation Files published after March 29, 2026, PhET-iO, or legacy Java/Flash.
  - The current per-sim metadata lists `licenseUrls = [creativecommons.org/licenses/by-nc/4.0/, creativecommons.org/licenses/GPL/2.0/]` for **all 127** HTML5 sims, so the current builds are **CC BY-NC 4.0**. This matches the "Shift to CC BY-NC License" milestone in PhET's 2025 Impact Report (seen in a search snippet; the PDF was too large to fetch). The FAQ says "all commercial use of PhET simulations requires a commercial license". The PhET name and logo are trademarks and excluded from the licence.
  - Code: the common libraries on GitHub are MIT (e.g. `phetsims/scenery` LICENSE: "The MIT License (MIT)", © University of Colorado Boulder). The README of the `phetsims/gravity-and-orbits` sim repo now says the code is "out of date and no longer actively maintained": PhET consolidated into a monorepo that is "not publicly available at this time". The current licensing page (`/en/licensing`) renders only with JS, so I could not read the current code-licence text there. Older mirrors and search snippets give GPLv3 for sim code, MIT for common code, and PhET-iO as not open source.
- **What a README could borrow.** A two-axis taxonomy (subject → subtopic, plus independent level and device tags) instead of one tree. Level as a *range* badge rather than one value. A fixed card schema: thumbnail, title, one-line description, learning goals, "related", run link, and per-entry language list. A separate "Translated" index. Accessibility features listed as tags on each entry. Licence stated per entry, with a cut-off date when the licence changes.
- Verified from:
  - https://phet.colorado.edu/en/simulations/projectile-motion (raw HTML, SSR data block)
  - https://phet.colorado.edu/ru/simulations/projectile-motion (raw HTML)
  - https://phet.colorado.edu/services/metadata/1.3/simulations?format=json&type=html&locale=en
  - https://phet.colorado.edu/services/metadata/1.3/simulations?format=json&type=html&summary
  - https://phet.colorado.edu/en/licensing/html (Historical Software Agreement)
  - https://phet.colorado.edu/el/faqs
  - https://github.com/phetsims/scenery/blob/main/LICENSE
  - https://raw.githubusercontent.com/phetsims/gravity-and-orbits/main/README.md
  - https://onlineteachinghub.education.purdue.edu/phet/ (third party; feature list and "more than 100 languages")
  - search snippets for phet.colorado.edu/<loc>/for-translators/translation-utility and PhET_Impact_Report_2025.pdf

## 2. Paul Falstad's math & physics applets (falstad.com)

- **Organisation by topic.** The index is a single flat page (`/mathphysics.html`) with 11 headed sections, in this order: *Oscillations and Waves · Acoustics · Signal Processing · Electricity and Magnetism: Statics · Electrodynamics · Quantum Mechanics · Linear Algebra · Vector Calculus · Thermodynamics · Mechanics · Miscellaneous*. Each section has 2–12 entries. Below them are a list of external educational links and a "fun stuff" list. The hierarchy is one level deep. The order is **not** textbook order: it opens with waves and quantum mechanics and puts mechanics near the end, which reflects the author's interests rather than a curriculum.
- **Organisation by level.** None. There are no level labels or filters.
- **How an entry is presented.** On the index, each entry is a **small thumbnail, a bold title and a one-line description**, and both the thumbnail and the title link to the applet page. One "new" badge marks a recent addition. Each applet page (e.g. `/ripple/`) embeds the running simulation and has a short paragraph on what it shows, a few getting-started lines that point to a built-in **Examples menu** (the presets are the main teaching device), "Full Directions" on a separate page, a "Full screen version", "Standalone (offline) versions", links to older JS and Java versions, a **GitHub link**, and **related applets**. There are no learning goals, standards, teacher materials or accessibility statement. The circuit simulator page adds an "Index of Circuit Examples" and a JavaScript interface page.
- **Technology.** The index says the applets "were originally written in Java, but they've mostly been converted to Javascript". The original Java versions stay online as legacy (e.g. `/circuit-java/`). The GitHub account shows TypeScript and WebGL ports (`ripplegl`, `ripplegl-ts`, `emstatic-ts`), and the circuit simulator repository now contains `ts/` and `cxx/` trees.
- **Languages.** The site and its descriptions are English only, with one Polish version of the circuit-examples index. The **Circuit Simulator** (CircuitJS1) is the exception: it has a UI locale system with translation files in its repo (`locale_*.txt`: csx, da, de, es, fi, fr, it, ja, kr, nb, pl, pt, **ru**, zh, zh-tw, plus the English default). Translations are community-contributed and credited in the README, so **Russian exists for the circuit simulator UI only**.
- **Licence.**
  - Site-wide terms (`/licensing.html`, custom, not an OSI licence): classroom use is permitted, and screenshots are allowed "as long as the applets are unmodified". "Modification or redistribution for non-commercial purposes is allowed, as long as you credit me", with a link back. Other uses require contacting the author. Source "is generally available on that applet's web page", and some third-party parts carry restrictions. The software is provided "AS IS".
  - Circuit simulator code (`pfalstad/circuitjs1`): **GPL-2.0** ("or any later version"). Other GitHub repos (ripplegl, emstatic, fourier, dfilter, …) show no licence file in the GitHub API, so the site terms apply to them.
- **What a README could borrow.** A sectioned list of rows with thumbnail + title + one line of "what it shows". Built-in **example presets** as the unit of demonstration ("open the Examples menu"). On each entry, links to full screen, offline and source. A plain legacy/version note. The flat, author-ordered list is also a warning: without levels or textbook order, newcomers cannot tell where to start.
- Verified from:
  - https://www.falstad.com/mathphysics.html
  - https://www.falstad.com/licensing.html
  - https://www.falstad.com/circuit/
  - https://www.falstad.com/ripple/
  - https://github.com/pfalstad/circuitjs1 (README and licence)
  - GitHub API: repos/pfalstad/circuitjs1 (licence `GPL-2.0`), the git tree listing of `locale_*.txt` file names (file names only), and users/pfalstad/repos

## 3. oPhysics: Interactive Physics Simulations (ophysics.com)

- **Organisation by topic.** A persistent sidebar menu lists these top-level categories: *Home · Kinematics · Forces · Conservation · Waves · Light · E & M · Rotation · Fluids · Modern · Drawing Tools · Fun Stuff*. The hierarchy is 2 levels deep: category page → simulation page, with an occasional sub-group such as a "Waves Tutorial" group of about 15 pages. The physics categories follow the **AP / high-school textbook order** closely: kinematics, then forces, conservation laws, waves, light, E&M, rotation, fluids and modern physics. Non-physics extras (drawing tools for teachers making diagrams, "Fun Stuff") come last. The sidebar lists every sim title, so the whole collection is visible from any page.
- **Organisation by level.** There are no level filters or badges. The level is implicit: the author is a high-school and AP Physics teacher, and "AP" appears only inside some titles (e.g. "AP Physics 2 … Problem").
- **How an entry is presented.** Each category page (e.g. Kinematics, 14 entries) is a list of **cards: thumbnail, linked title and a description of 1–3 sentences**. A simulation page has the embedded GeoGebra applet plus a short "Description" section. There are no instructions, learning goals, worksheets, standards or "try this" prompts. A few entries are framed as challenge/game variants (e.g. a "Tranquilize the Monkey" version of projectile motion) next to the plain exploration sim, which is a cheap way to add goals. Some sims have separate "iPad versions". There is a donation prompt and a "Latest Updates" list on the home page.
- **Technology.** The site says "all of the interactive simulations on this site were created using the wonderful GeoGebra software". The applets run in the browser and need no download.
- **Languages.** English only. No translations were found by fetch or search, so there is no Russian.
- **Licence.** There is no formal licence or terms page. The home page says: "Please feel free to use any of the content on this site for non-profit educational purposes." All content is by one author. No source code is published separately; the GeoGebra files are embedded.
- **What a README could borrow.** Categories in textbook order, so a reader can guess where a topic sits. Each category gets a short card list (thumbnail + title + 1–3 sentences). Exploration sims are paired with a "challenge" variant. The full menu is visible on every page. One-line permission statement on the front page.
- Verified from:
  - https://ophysics.com/
  - https://ophysics.com/k.html (Kinematics category)
  - https://ophysics.com/k8.html (single simulation page)
  - web search (no translations or terms page found)

## 4. myPhysicsLab (myphysicslab.com, Erik Neumann)

- **Organisation by topic.** The home page is one flat gallery of about 50 simulations under a single heading, "Physics Simulations". The grouping exists only in the URL folders: `springs/` (≈13), `pendulum/` (≈13), `engine2D/` (rigid-body physics engine, ≈17), `roller/` (roller coaster, ≈6), `pde/` (1). These counts are mine, inferred from the links, not from labels on the page. The order runs by **model complexity** (single spring → coupled springs → pendulums → rigid-body engine), not by textbook chapter. Every sim page has previous/next links, so the whole collection reads as a linear sequence.
- **Organisation by level.** None.
- **How an entry is presented.** In the gallery each entry is a **thumbnail and a title**, sometimes with a second line (e.g. "… with Physics Engine"), and no description. A single sim page (e.g. Simple Pendulum) has:
  - a language switch and previous/next links;
  - **tabs for views of the same run**: *Sim · Graph · Time Graph · Multi Graph*;
  - the embedded sim, with a short "what to try" paragraph (change parameters, drag the body, click preset initial conditions);
  - a "show sim terminal" toggle (a scripting console, "EasyScript");
  - links to **source code, documentation and "how to customize"**;
  - then a long physics write-up with fixed headings: *Puzzles · Physics – [method] (several derivations) · Numerical Solution · Puzzle Answers*;
  - links to related sims and a copyright footer.

  So each entry combines demo, derivation and numerics. There are no grade levels, standards or teacher worksheets, but there is a built-in **"Puzzles"** section with answers further down.
- **Technology.** HTML5 and TypeScript; the README says the code "was converted to TypeScript" in 2023. It runs in the browser, and offline downloadable versions are also offered. Typedoc API documentation is published on the site (`develop/docs/`).
- **Languages.** **English and German**, via a header switch and separate pages per language (`…-en.html`, `…-de.html`). The build produces "all language versions". No Russian was found.
- **Licence.** The code is "open source software under the **Apache 2.0 License**", per the README and the GitHub LICENSE (Apache-2.0). Page text carries a © Erik Neumann copyright footer. I found no separate content licence, so the prose is presumably all-rights-reserved.
- **What a README could borrow.** Per-entry **view tabs** (simulation / graph / time-graph). A fixed page schema: demo → things to try or puzzles → physics derivation → numerical method → answers. A "source · docs · customise" link triplet on every demo. Previous/next links that turn the gallery into a guided path. A two-language build that produces parallel pages from one source.
- Verified from:
  - https://www.myphysicslab.com/
  - https://www.myphysicslab.com/pendulum/pendulum-en.html
  - https://github.com/myphysicslab/myphysicslab (README, sidebar licence)
  - GitHub API tree (file names only)

## 5. Walter Fendt – Apps on Physics (HTML5) (walter-fendt.de/html5/phen/)

- **Organisation by topic.** The index is one static page, headed "(HTML5, 57 apps, 2025-03-31)". It has 9 sections in **classic German Gymnasium/textbook order**: *Mechanics (19) · Oscillations and Waves (9) · Electrodynamics (13) · Optics (6) · Thermodynamics (3) · Theory of Relativity (1) · Physics of Atoms (3) · Nuclear Physics (2) · Solid-State Physics (1)*. The German index uses the same order (*Mechanik … Festkörperphysik*). The hierarchy is one level deep. Within a section, entries also follow the textbook (simple → compound). The site home has the same scheme for maths and astronomy.
- **Organisation by level.** None. The scope is upper-secondary school physics, implied by the author's background and not labelled.
- **How an entry is presented.** On the index, each entry is a **text link (title) followed by a date range** (first published – last revised, e.g. "02/25/1998 - 06/17/2015"). There are no thumbnails, no descriptions and no level labels; the only images are flags and section icons. An app page has a title, the app on an HTML5 canvas, then a short **fixed sequence of paragraphs**: what is simulated; how the controls work (buttons, sliders, radio buttons choosing which quantity is displayed); and the modelling assumptions (e.g. "air resistance is ignored"). There are no learning goals, worksheets or standards. The whole collection per language is offered as **one ZIP for offline use** (`/download/html5phen.zip`, dated). The download page lists ZIPs for the maths, physics and astronomy apps in each language.
- **Technology.** HTML5 canvas and JavaScript. These replaced Fendt's well-known Java applets from 1997 onward, which survive on many university mirrors. The date ranges on entries carry that history.
- **Languages.** The index has a flag row with **20 languages**: English, Deutsch, Česky, Dansk, Ελληνικά, Español, Eesti, Français, Magyar, Italiano, Nederlands, Polski, Português, Română, **Русский**, Slovenčina, Shqip, Srpski, Thai, Türkmençe. The download page says "21 language versions" of the physics apps. Each language is a **separate static copy** (`/html5/phen/`, `/html5/phde/`, `/html5/phru/`, …) with fully translated page text and app UI (e.g. `projectile_ru.htm`). Language versions **lag behind**: the Russian index shows **51 apps (2023-09-07)** against 57 in English and German (2025-03). No translator credit is visible on the pages I fetched.
- **Licence.** The current site has **no licence or terms-of-use text**: the index, download page and Impressum were checked, and the footer has only the author name and date. The old Java-era copyright notice, preserved on university mirrors (e.g. `…/copyrightphe.htm`), allowed copying for non-commercial use; "The right of commercial use remains at the author"; and web mirroring was allowed if the copyright remarks and original URLs were kept. Treat the current terms as **all rights reserved, with informal permission for non-commercial use**. No source repository is published, although the JS is readable in the ZIP.
- **What a README could borrow.** Strict textbook section order with counts in the headings ("Mechanics (19)"). A "first published – last revised" date on each entry, as a freshness signal. A short three-paragraph page schema: what you see → how to operate → modelling assumptions. A language flag row at the top, with an explicit app count and date per language so lagging translations are visible. A one-file offline bundle of the whole collection.
- Verified from:
  - https://www.walter-fendt.de/html5/phen/
  - https://www.walter-fendt.de/html5/phde/
  - https://www.walter-fendt.de/html5/phru/
  - https://www.walter-fendt.de/html5/phen/projectile_en.htm
  - https://www.walter-fendt.de/html5/phru/projectile_ru.htm
  - https://www.walter-fendt.de/
  - https://www.walter-fendt.de/download/index.html
  - https://www.walter-fendt.de/impr.htm
  - https://www.physics.purdue.edu/class/applets/ph/copyrightphe.htm (mirror of the old Java-era notice, dated 31 Oct 1998). Fetched: it allows copying "for non-commercial purposes", says "The right of commercial use remains at the author", and allows putting the applets on a WWW server if the copyright remarks and original URLs stay

## 6. (Optional) ComPADRE / Open Source Physics (OSP) collection — one paragraph

OSP (compadre.org/osp, an NSF-funded collection inside the ComPADRE digital library) is organised by **resource type** rather than by physics topic. The top menu reads *Simulations · EJS Modeling · Curriculum · Programming · Tools · JS/HTML Materials · Browse Materials · Discussion · About OSP*. "Simulations" opens to *Overview · Java to Javascript · Data Files · Find Simulations*. Each item is a **library catalogue record** with fixed metadata fields: *Subjects · Levels · Resource Types · Intended Users · Formats · Ratings · Access Rights · License · Rights Holder · Keywords · Related Materials*, plus ready-made citation formats. Levels use ComPADRE's vocabulary and can be several at once; the EjsS "Simple Pendulum JavaScript Model" record lists *Lower Undergraduate, Middle School, High School*. JavaScript models are distributed "as downloadable html pages, as ready-to-run html pages, and (sometimes) as an app or EPub". The main item is usually a ZIP, with a "run" icon for one click. The licence is **per item**: that pendulum model is CC BY-NC-SA 3.0, and the EJS authoring tool is GPL v3, as the item records state. The portal footer reads "©2003-2026, All Rights Reserved". I saw no language switcher. What it adds for a README: a strict **metadata block per entry** (level, type, format, licence, how to cite), and an explicit "Java → JavaScript" conversion page for legacy material.

Verified from:
- https://www.compadre.org/osp/
- https://www.compadre.org/osp/search/categories.cfm?t=Simulation (raw HTML)
- https://www.compadre.org/osp/items/detail.cfm?ID=13373
- search snippets for IDs 7305 / 13356 (licence lines)

## 7. (Optional) Russian-language collection: «Открытая физика» (ООО «Физикон») — one paragraph

The classic Russian collection of interactive physics models is effectively **no longer online**. «Открытая физика» was a CD-ROM course by «Физикон» (versions 1.1 to 2.5), cited in Russian teacher guides, with a web edition on physics.ru. **http://www.physics.ru/ now returns a hosting provider's "domain not linked" parking page.** Физикон's portal `college.ru/fizika/` is now a commercial ЕГЭ exam-prep product: subject tiles with an icon, heading, short description and bullet sub-items, the level label "ЕГЭ", a "Как купить" menu item, "© ООО «Физикон», 1999 - 2026", and a "Правила использования сайта" page with no open licence. I found no interactive models there. The webpage text was fetched mis-encoded, so the Russian labels above are the fetch tool's decoding. The surviving Russian-language sources found in this survey are translations of foreign collections: PhET (90 of 127 HTML5 sims, UI and titles only), Walter Fendt (51 apps, full text, lagging the English version), and Falstad's circuit simulator (UI locale). A maintained, open, Russian-first collection with Russian descriptions did not turn up in my searches. This is an inference from a limited search, not proof that none exists.

Verified from:
- http://www.physics.ru/ (raw HTTP fetch; the HTTPS certificate belongs to the host)
- https://college.ru/fizika/
- search snippets (sgu.ru teacher-methodology PDF; Кавтрев overview cited via search) for the CD-ROM history, not fetched

## Comparison table

| Collection | Topics (top level, as shown) | Level labels | Entry card contents | Languages (count; Russian?) | Licence (code / content) |
|---|---|---|---|---|---|
| **PhET** | Physics → Motion · Sound & Waves · Work, Energy & Power · Heat & Thermo · Quantum Phenomena · Light & Radiation · Electricity, Magnets & Circuits; plus Biology, Chemistry, Earth & Space, Math & Statistics. Sims are tagged into several categories. | Elementary / Middle / High School / University, as a **range** per sim; plus a device filter (iPad/Tablet, Chromebook) | thumbnail + screenshots, title, short description, learning goals, Teacher Tips PDF, video primer, related sims, standards (Common Core Math, AAAS map keys), accessibility-feature tags, run + per-language download, teacher-contributed activities | 130 locales across the 127 HTML5 sims; **ru: 90/127 sims**, but only the sim UI and title. Descriptions, learning goals and site chrome are not in Russian. | Content: **CC BY-NC 4.0** in current metadata; versions before **2026-03-29** were CC BY 4.0; commercial use needs a licence. Code: common libraries MIT on GitHub; sim code historically GPLv3; the current monorepo is "not publicly available". |
| **Falstad** | Oscillations and Waves · Acoustics · Signal Processing · E&M: Statics · Electrodynamics · Quantum Mechanics · Linear Algebra · Vector Calculus · Thermodynamics · Mechanics · Miscellaneous (flat; not textbook order) | none | Index: thumbnail + title + one line. Page: embedded sim, **Examples menu presets**, directions, full screen, offline version, GitHub, related applets | English site; **Circuit Simulator UI in 15 locales + English, incl. ru**; other applets English only | Site terms: non-commercial modification and redistribution with credit; other uses need the author's permission. CircuitJS1: **GPL-2.0+**. Other repos: no licence file. |
| **oPhysics** | Kinematics · Forces · Conservation · Waves · Light · E & M · Rotation · Fluids · Modern (+ Drawing Tools, Fun Stuff); AP/high-school textbook order | none (implicitly HS/AP) | Category page: thumbnail + title + 1–3 sentences. Page: GeoGebra applet + "Description"; some challenge variants and iPad versions | English only; no ru | No formal licence: "non-profit educational purposes" permission. Built on GeoGebra; no source published. |
| **myPhysicsLab** | One flat gallery (~50); groups only in URL folders: springs · pendulum · engine2D · roller · pde; ordered by model complexity, with prev/next links | none | Gallery: thumbnail + title. Page: **Sim / Graph / Time Graph / Multi Graph tabs**, what-to-try text, script terminal, source · docs · customise links, *Puzzles · Physics (derivations) · Numerical Solution · Puzzle Answers* | 2 (English, German) as parallel pages; no ru | Code **Apache-2.0**; page text © the author |
| **Walter Fendt** | Mechanics · Oscillations and Waves · Electrodynamics · Optics · Thermodynamics · Theory of Relativity · Physics of Atoms · Nuclear Physics · Solid-State Physics (strict textbook order) | none (upper-secondary implied) | Index: title + **first-published – last-revised dates**; no thumbnail. Page: app + what it shows / controls / modelling assumptions. One ZIP per language. | **20 on the index flag row** (download page: 21); **ru yes**, full translation, but it lags (51 apps, 2023-09 vs 57 in English, 2025-03) | No licence on the current site. 1998 notice: non-commercial copying allowed; "commercial use remains at the author". |
| *OSP / ComPADRE* (optional) | By resource type: Simulations · EJS Modeling · Curriculum · Programming · Tools · JS/HTML Materials · Browse Materials | ComPADRE levels, several per item (e.g. Middle School, High School, Lower Undergraduate) | Catalogue record: Subjects, Levels, Resource Types, Intended Users, Formats, Ratings, Access Rights, License, Rights Holder, Keywords, Related, citation | English UI | Per item, e.g. a model CC BY-NC-SA 3.0, the EJS tool GPL v3 |
| *«Открытая физика» / Физикон* (optional) | **offline**: physics.ru is parked; the successor college.ru is commercial ЕГЭ prep | "ЕГЭ" | tiles: icon + heading + description + bullets (no models found) | Russian only | © ООО «Физикон», proprietary |

## Patterns worth borrowing for a README (structure only)

1. **Textbook-ordered sections as the spine, with counts in the headings.** For example *Mechanics (n) → Oscillations & Waves → Thermodynamics → Electrodynamics → Optics → Relativity → Quantum/Atomic*, as Fendt and oPhysics do, so a reader can guess where a topic sits. Avoid Falstad's author-ordered flat list, which has no entry point for newcomers.
2. **Second-axis tags rather than a second tree.** Show level, backend/device and accessibility as **badges on each card** (PhET's model) instead of extra sections. Give level as a range, e.g. "School → University" or "University → Research" (PhET low–high grade; OSP multi-level).
3. **Use the same card schema for every demo**: an animated thumbnail; a title; **one line of "what you will see"**; level badge(s); "▶ Run in browser"; "source"; and the languages available. PhET, oPhysics and Falstad all converge on thumbnail + title + 1–3 sentences. Fendt and the myPhysicsLab gallery leave out the description line, and their indexes are harder to scan for it.
4. **A fixed per-demo template** (in the README section or the demo's own page): *What you see → How to operate → Try this (2–3 prompts or puzzles) → Physics and modelling assumptions → Numerical method → Answers / related demos*. This combines Fendt's three paragraphs, myPhysicsLab's *Puzzles / Physics / Numerical Solution / Puzzle Answers*, and PhET's learning goals.
5. **Presets as the unit of a "try this".** Falstad's Examples menu and myPhysicsLab's preset initial conditions make each prompt one click away. A README card can link straight to a named preset URL, not just to the app.
6. **List the views available on one run** (myPhysicsLab: *Sim · Graph · Time Graph · Multi Graph*) and the "source · docs · customise" link triplet on each demo.
7. **Bilingual by parallel pages from one source, with visible coverage.** Use the same anchors and card order in EN and RU (myPhysicsLab `-en`/`-de`, Fendt `/phen/`–`/phru/`), with a language switch at the top. State **what is translated** (UI / titles / descriptions) and keep an **item count and date per language**, so lag is visible (Fendt's RU index is 51 vs 57 apps; PhET RU translates titles but not descriptions).
8. **A licence block that separates code from content and names a date.** PhET's 2026 move from CC BY to CC BY-NC with a cut-off date, OSP's per-item licences and Falstad's site terms vs a GPL repo show that readers need: code licence, content/media licence, a ready **attribution line** (PhET gives one; OSP gives citation formats), and per-entry exceptions. A one-sentence permission on the front page (oPhysics) is the minimum.
9. **Freshness and provenance signals**: "first published – last revised" dates (Fendt), a "new" badge (Falstad), a "Latest updates" list (oPhysics), and an offline bundle link (Fendt ZIP, Falstad standalone builds, PhET apps).
10. **Accessibility as a declared feature list per demo** (PhET's tags: keyboard / alternative input, sonification, screen-reader description, pan & zoom, voicing). Even "keyboard: yes/no" and "colour-blind-safe palette: yes/no" on a card sets expectations.

