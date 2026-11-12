# Prior-art check B: arrival times, backflow, triple slit, vector slits, recoiling slit

Date of search: 2026-11-12. Web research only (arXiv abstract pages, publisher abstract pages, Crossref API, search engines).
Rule: a claim is cited only if seen on a fetched page; otherwise marked "not verified".

## A1. Arrival-time distributions behind a double slit (rival rules, joint (x,t), realistic plate)

### (a) What has been done
1. **A. Ayatollah Rafsanjani, M. Kazemi, A. Bahrampour, M. Golshani, "Can the double-slit experiment distinguish between quantum interpretations?", Commun. Phys. 6, 195 (2023), doi:10.1038/s42005-023-01315-9, arXiv:2301.02641.**
   Verified: https://arxiv.org/abs/2301.02641 ; content details from https://ar5iv.labs.arxiv.org/html/2301.02641 (first 100k chars read).
   - Rules compared: semiclassical (SC), "standard" (STD, Kijowski / Aharonov-Bohm time-operator type), quantum flux (QF); in a "screen back-effect" section also the absorbing boundary rule (ABR, kappa = 1/um), path-integral with absorbing boundary (PAB) and Bohmian truncated current (BTC).
   - Slit model: NOT a plate. Each slit is a 2-D Gaussian packet ("soft edges that generate waves having identical Gaussian profiles"), free Schroedinger evolution afterwards; no thickness, no edge diffraction.
   - Geometry: metastable He; slits at y = +-10 um; sigma_x = 0.04 um, sigma_y = 0.5 um, u_x = 3 m/s; **horizontal screen** parallel to the beam at L_y = 15-30 um (main proposal); vertical screen at 240-330 mm gives near-identical mean arrival times for all rules.
   - Results (as reported on ar5iv page): ABR and PAB closer to each other than to BTC; differences up to ~40% in marginals; STD and QF similar but diverge near t ~ 0.2 ms at L_y = 15 um.
2. **S. Das, D.-A. Deckert, L. Kellers, S. Krekels, W. Struyve, "Double-slit experiment revisited", Ann. Phys. 479, 170054 (2025), doi:10.1016/j.aop.2025.170054, arXiv:2211.13362 (v1 Nov 2022 "remastered", v2 20 Nov 2024).** This is the "Das et al. 2024" paper (v2 date). Verified: https://arxiv.org/abs/2211.13362 and https://arxiv.org/html/2211.13362v2.
   - Exact numerical 2-D (x-z; y separable) Schroedinger solution; barrier = Gaussian profile of finite thickness sigma_b with smooth apertures 1/(1+xi^16) (not hard walls).
   - Computes the Bohmian first-passage (x,t) distribution and the flux density on the screen; NO other rules (no ABR/ABK/MS), NO detector model ("A rigorous justification of the FPT as an approximation to the ToF would require actually modelling the detector").
   - Also a slit closed during flight (tanh switching): banded arrivals from a "shock wave", fringe loss.
   - Conclusion: quantum timing effects need a large longitudinal spread; the Kurtsiefer-Pfau-Mlynek He* data (Nature 1997) are effectively classical in time; suggests ultracold neutrons, ion-trap or field-emission electron sources.
3. **S. Das, W. Struyve, "Questioning the adequacy of certain quantum arrival-time distributions", Phys. Rev. A 104, 042214 (2021), doi:10.1103/PhysRevA.104.042214, arXiv:2105.14744.** Verified: https://arxiv.org/abs/2105.14744. 1-D Gaussian wave train: Wlodarz, Marchewka-Schuss, Jurman-Nikolic exponential rules and the semiclassical rule behave unphysically; quantum flux (Bohm) behaves as expected.
4. **W. Cavendish, S. Das, "Absorbing detectors versus scattering theory", Phys. Rev. A 112, 062217 (2025), doi:10.1103/332p-4nl1.** Verified: https://journals.aps.org/pra/abstract/10.1103/332p-4nl1. Exactly solvable 1-D and 2-D examples: ABC (absorbing boundary) predictions conflict with scattering theory (sharp momentum- and orientation-dependent detection probabilities, secondary reflections not seen experimentally) -> "empirically inadequate as a general solution to the screen problem".
5. **A. Ayatollah Rafsanjani, W. Cavendish, "The arrival position problem in quantum mechanics", arXiv:2607.03538 (3 Jul 2026), no journal ref.** Verified: https://arxiv.org/abs/2607.03538. Compares position marginals of several screen-problem proposals; claims they are distinguishable in simple, currently feasible experiments and that many discrepancies persist in the far field. (Which proposals and set-ups: not read; abstract does not say.)
6. **A. Ayatollah Rafsanjani, M. Kazemi, V. Hosseinzadeh, M. Golshani, "Non-local temporal interference", Sci. Rep. 14, 3615 (2024), doi:10.1038/s41598-024-54018-8, arXiv:2307.04811.** Verified: https://arxiv.org/abs/2307.04811 and Crossref API (query.bibliographic). Entangled atom pairs in a double-double slit; Bohmian arrival times; complementarity of one- and two-particle visibilities in arrival time.
7. **S. Goldstein, R. Tumulka, N. Zanghi, "Arrival Times Versus Detection Times", Found. Phys. 54, 63 (2024), doi:10.1007/s10701-024-00798-y, arXiv:2405.04607.** Verified: https://arxiv.org/abs/2405.04607. Detectors change the wave function; arrival time without detector != arrival with detector != detection time.
8. **A. Jozani, R. Tumulka, "Detection Time Distribution Predicted Using Absorbing Boundary Conditions and Imaginary Potentials", Phys. Rev. Research 8, 033072 (2026), doi:10.1103/g4wn-ctbl, arXiv:2603.22044.** Verified: https://arxiv.org/abs/2603.22044. Waveguide (2-D), detector downstream; two ABCs vs imaginary potentials; partial reflection off the detector; spin-1/2 case (see A2).
9. **A. Marchewka, "The MS Unidirectional Current as a Generalization of the ABC Absorption Current", arXiv:2608.29969 (30 Aug 2026).** Verified: https://arxiv.org/abs/2608.29969. 1-D half-line: every Robin ABC is one calibration of the MS family, lambda_kappa(k) = pi kappa/(k+kappa)^2.
10. S. Roncallo, K. Sacha, L. Maccone, "When does a particle arrive?", Quantum 7, 968 (2023), arXiv:2205.02219 -- seen only in search results (quantum-journal.org/papers/q-2023-03-30-968), page not fetched: compares Kijowski, flux and quantum-clock proposals for a superposition of two Gaussians (1-D time interference); claims experimentally discriminable regimes. Status: bibliographic data from search snippet only, **not verified by fetch**.

Experiments: no time-resolved double-slit measurement designed to discriminate arrival-time rules was found (search 2024-2026). The only cited data set is Kurtsiefer, Pfau, Mlynek, Nature 1997 (He*, time-of-flight + position), which Das et al. 2025 say is classical in time. Absence of an experiment: searched, **not found** (not proof of absence).

### (b) What remains open (narrow)
- Nobody (found) has put ALL the rules (flux, Bohm first arrival, ABK/STD, ABR, MS/Wlodarz, semiclassical, soft detector) on the SAME exact 2-D/3-D solution with a hard-wall plate of finite thickness. Rafsanjani 2023 has the rules but Gaussian "soft" slits and free propagation; Das et al. 2025 has an exact finite-thickness barrier but only Bohm/flux and no detector.
- Concrete set-up: the Rafsanjani He* horizontal-screen geometry (slits +-10 um, screen 15-30 um off-axis, parallel to the beam) re-run with a real plate (hard walls, thickness d = 0, 1, 5 um), plus ABR and soft detector on the horizontal screen. Question: are the reported inter-rule differences (up to ~40%) robust to the slit model, or are they comparable to plate-induced changes (edge diffraction, back-reflection, wave in the near field next to the plate)? The horizontal screen lies a few um from the plate edge region, so the Gaussian-slit idealisation is the weakest point of that proposal.
- Second set-up: Das et al. slit-closing-in-flight scenario with all rules (does the "shock wave" banding appear in flux/ABK/ABR, or only in Bohm FPT?).

### (c) Novelty: MEDIUM-LOW
The comparison of rules in a double slit is published (Rafsanjani 2023) and the exact finite-barrier Bohm computation is published (Das et al. 2025); what remains is a robustness/realism check combining the two, plus detector models. Incremental, but not done.

### (d) Value
Tells an experimentalist whether the Rafsanjani horizontal-screen proposal survives a real plate and a real (absorbing) detector, i.e. whether the predicted rule discrimination is a property of the rules or of the idealised source. Informs He* / ultracold-neutron / field-emission-electron proposals mentioned by Das et al.

### (e) Not verified
- Whether Rafsanjani 2023 appendix discusses plate effects (last 32k chars of ar5iv page not read).
- Which proposals Rafsanjani & Cavendish 2026 compare.
- Roncallo-Sacha-Maccone details (page not fetched).

## A2. Spin-dependent arrival times (Das-Duerr) and the measurability dispute

### (a) What has been done
1. **S. Das, D. Duerr, "Arrival Time Distributions of Spin-1/2 Particles", Sci. Rep. 9, 2242 (2019), doi:10.1038/s41598-018-38261-4, arXiv:1802.07141.** Verified: https://arxiv.org/abs/1802.07141 (volume/article number 9:2242 confirmed on https://arxiv.org/abs/2309.15815). Pauli equation, Bohmian first arrival, spin-polarised particle released in a cylindrical waveguide; strong spin dependence vs flux and semiclassical; claims present-day testability.
2. **S. Das, M. Noeth, D. Duerr, "Exotic Bohmian arrival times of spin-1/2 particles: An analytical treatment", Phys. Rev. A 99, 052124 (2019), doi:10.1103/PhysRevA.99.052124.** Verified via Crossref API (query.bibliographic); abstract page not fetched.
3. **S. Goldstein, R. Tumulka, N. Zanghi, "On the Spin Dependence of Detection Times and the Nonmeasurability of Arrival Times", Sci. Rep. 14, 3775 (2024), doi:10.1038/s41598-024-53777-8, arXiv:2309.11835.** Verified: https://arxiv.org/abs/2309.11835. Distribution must come from a POVM; the Das-Duerr spin dependence is incompatible with any POVM -> no detector can measure it.
4. **S. Das, S. Aristarhov, "Comment on 'the Spin Dependence of Detection Times and the Nonmeasurability of Arrival Times'", arXiv:2312.01802 (4 Dec 2023), no journal ref.** Verified: https://arxiv.org/abs/2312.01802. (Per search snippet: agrees the distributions violate the POVM criterion, disputes that the criterion decides what experiments can see -- snippet, not seen on abstract page.)
5. **S. Goldstein, R. Tumulka, N. Zanghi, "Arrival Times Versus Detection Times", Found. Phys. 54, 63 (2024), doi:10.1007/s10701-024-00798-y, arXiv:2405.04607.** Verified: https://arxiv.org/abs/2405.04607. Detectors change psi and trajectories; the Das-Duerr curves are not what Bohmian mechanics predicts for detection times.
6. **A. Drezet, "Arrival time and Bohmian Mechanics: It is the theory which decides what we can measure", arXiv:2409.04304 (Sep 2024).** Verified: https://arxiv.org/abs/2409.04304. Each side partly right; Das-Duerr predictions measurable in principle but no signalling. (Search snippet says published in Symmetry 16, 1325 (2024), doi:10.3390/sym16101325 -- **not verified** on a fetched page.)
7. **S. Das, "Detlef Duerr, arrival-time distributions, and spin in Bohmian mechanics: Personal recollections and state-of-the-art", arXiv:2309.15815 (Sep 2023).** Verified: https://arxiv.org/abs/2309.15815. Review incl. variations of the waveguide set-up.
8. **A. Jozani, R. Tumulka, Phys. Rev. Research 8, 033072 (2026), doi:10.1103/g4wn-ctbl, arXiv:2603.22044** (see A1). Verified: https://arxiv.org/abs/2603.22044 and https://arxiv.org/html/2603.22044v2 (first 100k chars). **This is the 3-D detector-model computation of the Das-Duerr set-up**: Crank-Nicolson in Cartesian 3-D waveguide; detector models = imaginary potential -iW(z) (tanh ramp), spinless ABC d_z psi = i kappa psi, spinor ABC sigma.grad psi = i kappa n.sigma psi. Result: CAP and spinless ABC are spin-blind; spinor ABC gives only negligible spin dependence (but depends on waveguide width); Das-Duerr theta = pi/2 curve has compact support whereas detector models have tails; spinor-ABC mean time grows with omega, Das-Duerr decreases. Listed open items: analytic omega-dependence; whether reflection oscillations show in real data; hard vs soft detectors; other complex-potential shapes with less reflection; microscopic detector models with decoherence.
9. **A. Amblard, A. Drezet, "Arrival-time distributions as a probe of the preferred foliation in relativistic Bohmian mechanics", arXiv:2604.17507 (v1 19 Apr 2026, v2 14 Sep 2026).** Verified: https://arxiv.org/abs/2604.17507. EPRB + Das-Duerr arrival times; implies signalling if non-POVM predictions were empirically valid.
10. **P. Holland, C. Philippidis, "Implications of Lorentz covariance for the guidance equation in two-slit quantum interference", Phys. Rev. A 67, 062105 (2003), doi:10.1103/PhysRevA.67.062105, arXiv:quant-ph/0302076.** Verified: https://arxiv.org/abs/quant-ph/0302076. Spin term in the guidance law applied to two-slit interference with 2-D Gaussian packets; trajectories cross the symmetry axis. (Prior art for spin-dependent Bohm trajectories behind a double slit; not arrival-time distributions, no plate.)
11. Related, Crossref only: A. Mousavi, M. Golshani, "Bohmian approach to spin-dependent time of arrival for particles in a uniform field and for particles passing through a barrier", J. Phys. A 41, 375304 (2008), doi:10.1088/1751-8113/41/37/375304; P. Naidon, "Inequivalence of stochastic and Bohmian arrival times in time-of-flight experiments", Phys. Rev. A 109, 063312 (2024), doi:10.1103/PhysRevA.109.063312 (Crossref API metadata only; abstracts not read).

Experiments: none found (searched 2019-2026) measuring spin dependence of arrival times in the Das-Duerr sense.

### (b) What remains open (narrow)
- The waveguide case with detector models is now DONE (Jozani-Tumulka 2026, 3-D). Remaining narrow gaps:
  1. Same comparison in a SLIT geometry: spin-polarised packet through a single/double slit in a plate of finite thickness, joint (x,t) on a screen: Bohm with Pauli (spin) term vs without vs CAP/soft detector vs spinor ABC. The spin term rho^-1 curl(rho s) is largest where |psi|^2 has sharp transverse gradients (slit edges, fringe minima), so effects could exceed the smooth-waveguide case. Holland-Philippidis 2003 had trajectories only, Gaussian slits, no time statistics.
  2. The detector-shape question Jozani-Tumulka leave open: "soft" detectors (the engine's soft absorbing detector reproducing Das-Struyve eq. 43) and low-reflection complex potentials, spin-coupled vs spin-blind, in the Das-Duerr waveguide.
- Note: GTZ's POVM argument makes any non-POVM (Bohm first-arrival) spin dependence unmeasurable as a detector statistic; a computation can only show how large the gap is between "Bohm arrival without detector" and "detection time with any detector model".

### (c) Novelty: LOW
The key 3-D detector-model computation appeared in 2026 (PRR 8, 033072); spin-dependent double-slit Bohm trajectories exist since 2003. Only the slit-geometry (x,t) version with detector models is uncovered, and its interpretation is fenced in by the POVM no-go.

### (d) Value
Mainly pedagogical/diagnostic: a visual demonstration that the spin term changes Bohm arrivals but not (any POVM) detection statistics; could quantify the "detector tail vs compact support" difference in a slit geometry. Would not inform a pending experiment (none found).

### (e) Not verified
- Das-Aristarhov comment content beyond the abstract line; Drezet's Symmetry publication data.
- Last 73k chars of Jozani-Tumulka HTML (possible slit-geometry remarks) not read.

## A3. Quantum backflow (matter waves, 2-D / angular backflow)

### (a) What has been done
Experiments (all optical / photonic; none with matter waves found as of Nov 2026):
1. **Y. Eliezer, T. Zacharias, A. Bahabad, "Observation of optical backflow", Optica 7, 72 (2020), doi:10.1364/OPTICA.371494, arXiv:1811.09163.** Crossref API metadata (query.bibliographic); arXiv page seen only in search results.
2. **A. Daniel, B. Ghosh, B. Gorzkowski, R. Lapkiewicz, "Demonstrating backflow in classical two beams' interference", New J. Phys. 24, 123011 (2022), doi:10.1088/1367-2630/aca70b.** Crossref API metadata only.
3. **B. Ghosh, A. Daniel, B. Gorzkowski, R. Lapkiewicz, "Azimuthal backflow in light carrying orbital angular momentum", Optica 10, 1217 (2023), doi:10.1364/OPTICA.495710.** Crossref API metadata only.
4. **Z.-F. Zhang, P.-F. Huang, S.-C. Dong, Y.-X. Rong, J.-S. Xu, Y.-J. Gu, Y. Xiao, "Observation of single-photon azimuthal backflow with weak measurement", Opt. Lett. 50(2), 333-336 (2025), doi:10.1364/OL.540905, arXiv:2501.09952.** Verified: https://arxiv.org/abs/2501.09952. Heralded single photons, negative-OAM-only superposition shows positive local OAM; says demonstrations so far are "restricted to classical optical systems" (i.e., single-photon is the first quantum-light case).

Theory / proposals (matter waves):
5. **M. Palmero, E. Torrontegui, J. G. Muga, M. Modugno, "Detecting quantum backflow by the density of a Bose-Einstein condensate", Phys. Rev. A 87, 053618 (2013), doi:10.1103/PhysRevA.87.053618, arXiv:1302.3373.** Crossref metadata; Bragg pulse on a moving BEC; density below a critical threshold signals backflow.
6. **Y. Chen, Y. Tang, "Preparing Quantum Backflow States by Large Momentum Transfer", Phys. Rev. A 113, 063304 (2026), doi:10.1103/3b4f-6nfr, arXiv:2602.12767.** Verified: https://arxiv.org/abs/2602.12767. 88Sr non-interacting BEC, LMT interferometry, tunable pulse sequence; enhanced signature over Palmero; proposal only; states backflow not yet observed.
7. **T. Paterek, A. Goussev, "General quantum backflow in realistic wave packets", Phys. Rev. Lett. 136, 090202 (2026), doi:10.1103/tm9s-pkg5, arXiv:2511.10155.** Verified: https://arxiv.org/abs/2511.10155. Backflow for arbitrary momentum distributions ("general backflow" up to ~13%, vs ~4% standard bound); explicitly a route to first observation in realistic settings -> still unobserved for matter.
8. **M. Barbier, A. Goussev, S. C. L. Srivastava, "Unbounded quantum backflow in two dimensions", Phys. Rev. A 107, 032204 (2023), doi:10.1103/PhysRevA.107.032204, arXiv:2211.06539.** Verified: https://journals.aps.org/pra/abstract/10.1103/PhysRevA.107.032204. Charged particle on a punctured disk with flux line / uniform field, degenerate eigenstates -> backflow unbounded "in a certain sense"; proposed as candidate for first observation.
9. **A. Goussev, "Quantum backflow in a ring", Phys. Rev. A 103, 022217 (2021), doi:10.1103/PhysRevA.103.022217**; **M. Barbier, A. Goussev, "On the experiment-friendly formulation of quantum backflow", Quantum 5, 536 (2021), doi:10.22331/q-2021-09-07-536**; **M. Barbier, A. Goussev, "Quantum backflow for two identical particles", New J. Phys. 27, 033011 (2025), doi:10.1088/1367-2630/adb77e**; **F. Paccoia, O. Panella, P. Roy, "Angular momentum quantum backflow in the noncommutative plane", Phys. Rev. A 102, 062218 (2020), doi:10.1103/PhysRevA.102.062218.** All: Crossref API metadata only (abstracts not read).
10. **A. Goussev, "Equivalence between quantum backflow and classically forbidden probability flow in a diffraction-in-time problem", Phys. Rev. A 99, 043626 (2019), doi:10.1103/PhysRevA.99.043626, arXiv:1903.02053.** Verified: https://arxiv.org/abs/1903.02053. Backflow == classically forbidden flux of a packet released from a half-line (diffraction in time).
11. **H. Bostelmann, D. Cadamuro, G. Lechner, "Quantum backflow and scattering", Phys. Rev. A 96, 012112 (2017), doi:10.1103/PhysRevA.96.012112, arXiv:1703.04597.** Verified: https://arxiv.org/abs/1703.04597. Backflow present for any short-range potential; role of reflection/transmission (1-D).

Not verified: the "Xiao et al. arXiv:2607.10281" correlated-backflow theory paper (search snippet only).

### (b) What remains open (narrow)
- No matter-wave observation exists (as stated by Chen-Tang PRA 2026 and Paterek-Goussev PRL 2026); proposals are 1-D BEC Bragg/LMT schemes and 2-D magnetic-flux disks. Nothing found on backflow **in spatial diffraction behind real slits** for matter waves.
- Concrete set-up the engine can compute: packet with strictly positive k_z through a single/double slit in a plate of finite thickness; map regions of negative longitudinal flux j_z downstream (near-field vortex zones beside fringe minima) and the integrated probability transferred backwards through a line z = const parallel to the plate, as a function of distance from the plate, plate thickness and slit width. Then: (i) is it "backflow" in the strict sense (transmitted spectrum has only k_z > 0 downstream, evanescent part decays) or reflection/vortex circulation; (ii) the consequence for arrival-time rules: the flux rule becomes negative exactly there, while ABR/soft detector/Bohm first-arrival stay positive -> a geometry where the rules must differ in sign, not just in shape. This links A1 and A3 and is checkable against Rafsanjani's near-field horizontal screen.
- Spatial (2-D) analogue for optics exists (two-beam interference: Daniel et al. 2022), so the matter-wave slit version is the analogue, not a new effect; its value would be magnitudes for realistic He*/electron parameters.

### (c) Novelty: LOW-MEDIUM
Backflow theory is saturated in 1-D and 2-D idealised models, and 2-D interference backflow has been seen optically; the slit-plate matter-wave map with arrival-rule consequences was not found, but it is a computation of a known effect in a new geometry.

### (d) Value
Would tell whether a double-slit time-of-flight experiment with a near-field screen automatically probes backflow (and hence where the flux rule fails); gives realistic magnitudes for an electron/He* proposal competing with the BEC Bragg schemes.

### (e) Not verified
- Abstracts of items 1-3, 5, 9 (Crossref metadata only). Whether any 2026 cold-atom experiment preprint claims observation: two searches found none.

## A4. Sorkin triple-slit parameter kappa for MATTER waves from an exact solution with finite-thickness slits

### (a) What has been done
Experiments:
1. **U. Sinha, C. Couteau, T. Jennewein, R. Laflamme, G. Weihs, "Ruling Out Multi-Order Interference in Quantum Mechanics", Science 329, 418-421 (2010), doi:10.1126/science.1190545.** Crossref API metadata only (photons).
2. **T. Kauten, R. Keil, T. Kaufmann, B. Pressl, C. Brukner, G. Weihs, "Obtaining tight bounds on higher-order interferences with a 5-path interferometer", New J. Phys. 19, 033017 (2017), doi:10.1088/1367-2630/aa5d98.** Crossref metadata only (photons, interferometer, no slits).
3. **J. P. Cotter, C. Brand, C. Knobloch, Y. Lilach, O. Cheshnovsky, M. Arndt, "In search of multipath interference using large molecules", Sci. Adv. 3, e1602478 (2017), doi:10.1126/sciadv.1602478.** Crossref metadata; content from search snippets (science.org returned 403): phthalocyanine (515 amu), single/double/triple slit masks; upper bound "less than one particle in a hundred" deviating; first such test with massive particles. Mask thickness / looped-path estimate for the gratings: **not verified**.
4. **O. S. Magana-Loaiza, I. De Leon, M. Mirhosseini, R. Fickler, A. Safari, U. Mick, B. McIntyre, ... R. W. Boyd, "Exotic looped trajectories of photons in three-slit interference", Nat. Commun. 7, 13987 (2016), doi:10.1038/ncomms13987.** Crossref metadata (author list truncated at 7); per search snippet looped-path contribution enhanced with surface plasmons near metallic slits (photons) -- snippet only.
5. R. Rengaraj et al., "Measuring the deviation from the superposition principle in interference experiments", New J. Phys. 20, 063049 (2018), doi:10.1088/1367-2630/aac92c (Crossref metadata only; content not read).
Proposal: **K. S. Lee, Z. Zhuo, C. Couteau, D. Wilkowski, T. Paterek, "An atomic test of higher-order interference", Phys. Rev. A 101, 052111 (2020), arXiv:1911.12953.** Verified: https://arxiv.org/abs/1911.12953 (tripod-level atoms; slit analogues in internal states, not spatial slits).

Theory / numerics:
6. **H. De Raedt, K. Michielsen, K. Hess, "Analysis of multipath interference in three-slit experiments", Phys. Rev. A 85, 012101 (2012), doi:10.1103/PhysRevA.85.012101, arXiv:1112.2665 (earlier "Multi-order interference is generally nonzero", arXiv:1103.0121).** Seen via search result (ADS / link.aps.org abstract snippets); explicit FDTD solutions of Maxwell's equations for realistic three-slit devices incl. an idealised Sinha-2010 device -> kappa generally nonzero. **Photons/EM only.** Abstract page not fetched directly.
7. **R. Sawant, J. Samuel, A. Sinha, S. Sinha, U. Sinha, "Non-classical paths in interference experiments", Phys. Rev. Lett. 113, 120406 (2014), doi:10.1103/PhysRevLett.113.120406, arXiv:1308.2022.** Verified: https://arxiv.org/abs/1308.2022. Feynman path integral, non-classical (looped) paths -> superposition only approximately valid; proposes three-slit tests.
8. **A. Sinha, A. H. Vijay, U. Sinha, "On the superposition principle in interference experiments", Sci. Rep. 5, 10304 (2015), doi:10.1038/srep10304, arXiv:1412.2198.** Crossref metadata + search snippets from the PMC/ar5iv pages: analytic kappa in the **thin-slit, Fraunhofer** limit; claim valid for Maxwell and Schroedinger; notes the De Raedt FDTD needed days on a supercomputer.
9. **I. G. da Paz, C. H. S. Vieira, R. Ducharme, L. A. Cabral, H. Alexander, M. D. R. Sampaio, "Gouy phase in non-classical paths in triple-slit interference experiment", Phys. Rev. A 93, 033621 (2016), doi:10.1103/PhysRevA.93.033621, arXiv:1510.04186.** Verified: https://arxiv.org/abs/1510.04186. Matter waves, Gaussian-slit propagator model; Gouy phase changes kappa non-trivially. (Search snippet: electrons kappa ~ 1e-8 -- not seen on abstract page.)
10. **C. H. S. Vieira, H. Alexander, G. de Souza, M. Sampaio, I. da Paz, "Exotic looped trajectories in double-slit experiments with matter waves", arXiv:1705.07156 (2017).** Verified: https://arxiv.org/abs/1705.07156. Matter waves, kappa expressed via looped-path fringe visibility and Gouy phases; neutron interferometry estimate |kappa_max| ~ 0.2 (setup-sensitive). Journal ref not on page.
11. **F. C. V. de Brito, C. H. S. Vieira, I. G. da Paz, J. B. Araujo, M. Sampaio, "Sorkin parameter for type-I spontaneous parametric down-conversion biphotons and matter waves", Phys. Rev. A 103, 033707 (2021), arXiv:2103.02674.** Crossref metadata; arXiv page fetched (https://arxiv.org/abs/2103.02674) but the returned abstract summary did not match the title (fetch summariser issue) -> content **not verified**.
12. **J. Q. Quach, "Which-way double slit experiments and Born rule violation", Phys. Rev. A 95, 042129 (2017), doi:10.1103/PhysRevA.95.042129, arXiv:1610.06401.** Verified: https://arxiv.org/abs/1610.06401. With non-classical paths a second which-way detector changes the pattern; kappa is only an approximate Born-rule test; proposes an exact parameter from single vs double which-way detectors.

Search for an exact time-dependent Schroedinger (or Bohmian) kappa with finite-thickness hard-wall slits for electrons/atoms/molecules: **none found** (two targeted searches). Matter-wave kappa work found is Gaussian-slit propagator / path-integral thin-slit Fraunhofer; the only "exact realistic slit" computation is FDTD Maxwell (De Raedt 2012).

### (b) What remains open (narrow)
- kappa for matter waves from the exact 2-D TDSE with hard-wall (or finite-barrier) slits of finite thickness, from near field to far field, for an existing experiment's geometry: (i) electrons (lambda ~ 50 pm, slit width ~ 62 nm -- numbers from Sinha-type literature, from a search snippet, verify before use), (ii) Cotter 2017 phthalocyanine masks (needs mask parameters; not verified). Outputs: kappa(x) vs plate thickness d, vs distance; compare with the Sinha-2015 thin-slit formula and the Gouy-phase Gaussian model -> where the thin-slit/Gaussian approximations fail by orders of magnitude.
- The "blocking" systematics: kappa depends on HOW a slit is closed (hard plug flush with the plate, absorber/complex potential, recessed plug). This is Quach's point in a realistic geometry; for matter waves it seems uncomputed. The engine's absorbing detectors make "absorbing vs reflecting blocker" a one-parameter study.
- Optional: Bohm trajectories that wind between slits (looped paths in the trajectory picture) -- illustrative only.

### (c) Novelty: MEDIUM
Photonic FDTD (2012) and matter-wave approximate models (2014-2021) exist; an exact finite-thickness TDSE kappa for matter waves, and the blocker-model dependence, were not found. Expected magnitudes are tiny (1e-8 for electrons per snippet), so the result is a systematics floor rather than a discovery.

### (d) Value
Gives the systematic floor below which a matter-wave triple-slit Born-rule test cannot go with real slits; tells molecule/electron experimenters whether plate thickness or blocker type dominates kappa; complements De Raedt's Maxwell result for the Schroedinger case.

### (e) Not verified
- De Raedt 2012 abstract (search snippet only); Cotter 2017 numbers (snippet); electron kappa ~ 1e-8 and lambda/slit numbers (snippets); de Brito 2021 content.

## A5. Vector vs scalar diffraction at subwavelength slits: polarisation as a partial which-path mark, analyser as eraser

### (a) What has been done
Slits in metal, classical light (TE/TM, plasmons, coherence):
1. **H. F. Schouten, N. Kuzmin, G. Dubois, T. D. Visser, G. Gbur, P. F. A. Alkemade, H. Blok, G. W. 't Hooft, D. Lenstra, E. R. Eliel, "Plasmon-Assisted Two-Slit Transmission: Young's Experiment Revisited", Phys. Rev. Lett. 94, 053901 (2005), doi:10.1103/PhysRevLett.94.053901.** Crossref metadata + abstract text from search results (research.vu.nl / TU Delft records): total far-field intensity modulated with wavelength by SPPs travelling slit-to-slit; TM only; (search snippet: no modulation for TE; fringe visibility ~0.2; slits ~200 nm in gold).
2. **N. Kuzmin, G. W. 't Hooft, E. R. Eliel, G. Gbur, H. F. Schouten, T. D. Visser, "Enhancement of spatial coherence by surface plasmons", Opt. Lett. 32, 445 (2007), doi:10.1364/OL.32.000445.** Crossref metadata only.
3. **C. H. Gan, G. Gbur, T. D. Visser, "Surface Plasmons Modulate the Spatial Coherence of Light in Young's Interference Experiment", Phys. Rev. Lett. 98, 043908 (2007), doi:10.1103/PhysRevLett.98.043908.** Crossref metadata only.
4. **D. Li, D. Pacifici, "Strong Amplitude and Phase Modulation of Optical Spatial Coherence with Surface Plasmon Polaritons", arXiv:1612.09153 (2016).** Verified: https://arxiv.org/abs/1612.09153. SPPs correlate fields at the two slits; coherence tuned 0-80% by slit separation. (Search snippet adds: TE visibility falls with separation, TM modulated by SPPs.)
5. Y. Lee, Q-H. Park (Crossref: "Coupling of Surface Plasmon Polaritons and Light in Metallic Nanoslits", Phys. Rev. Lett. 95, 103902 (2005), doi:10.1103/PhysRevLett.95.103902) -- metadata only.
6. Search snippets only (**not verified**, no reference resolved): an Opt. Express 2007 paper on metallic double nanoslits of DIFFERENT widths shifting the Young interference order via SPPs (zendy record for doi 10.1364/OE.15.011321 appeared in results); a KAIST terahertz study of asymmetric double slits whose interference pattern changes with polarisation in the subwavelength regime (width-dependent diffraction phase); a Leiden result that real-metal nanoslits act as "lossy optical retarders" with TE cut-off slightly below lambda/2.

Polarisation which-path / complementarity / erasers:
7. **A. Norrman, K. Blomstedt, T. Setala, A. T. Friberg, "Complementarity and Polarization Modulation in Photon Interference", Phys. Rev. Lett. 119, 040401 (2017), doi:10.1103/PhysRevLett.119.040401.** Verified: https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.119.040401. General distinguishability-visibility relations for vector-light quantum fields in double-pinhole interference with polarisation modulation (formal framework covers exactly "slit-dependent polarisation as which-path"; pinholes idealised, no slit physics).
8. **E. Altewischer, M. P. van Exter, J. P. Woerdman, "Plasmon-assisted transmission of entangled photons", Nature 418, 304-306 (2002), doi:10.1038/nature00869.** Crossref metadata + search snippet: hole arrays preserve entanglement; metal's nonlocal response can act as "which way" label.
9. **C. Altuzarra, S. Vezzoli, J. Valente, W. Gao, C. Soci, D. Faccio, C. Couteau (+ N. I. Zheludev per conference record), "Coherent Perfect Absorption in Metamaterials with Entangled Photons", ACS Photonics 4, 2124-2128 (2017), doi:10.1021/acsphotonics.7b00514.** Crossref metadata; snippet: polarisation-sensitive quantum-eraser-type interferometer with a metamaterial.
10. **H. Liang, W. C. Wong, T. An, J. Li, "Metasurface-enabled quantum holograms with hybrid entanglement", Adv. Photon. 7, 026006 (2025), doi:10.1117/1.AP.7.2.026006, arXiv:2408.10485.** Crossref metadata + search snippets: metasurface makes two holograms entangled with orthogonal idler polarisations; polariser erases ("quantum holographic eraser").

Not found: any paper using the TE cut-off of a narrow slit in a thick (perfect or real) conductor, with two slits of different widths, as a polarisation-controlled partial which-path marker with analyser erasure, for single photons or classical light (three targeted searches).

### (b) What remains open (narrow)
- Concrete computation: PEC screen of thickness d with two slits, w1 < lambda/2 (TE below cut-off, TE amplitude ~ exp(-kappa_TE d)) and w2 > lambda/2; incident linear polarisation at angle theta. From the modal method: complex t_TE(w,d), t_TM(w,d) per slit -> polarisation states |e1>, |e2> behind each slit -> predicted visibility V(theta, d) = 2|<e1|e2>| sqrt(I1 I2)/(I1+I2), distinguishability D, check D^2 + V^2 <= 1 saturation (Norrman 2017 relations) and recovery with an analyser at angle phi (eraser) -- all from first-principles slit physics rather than inserted polarisers. Compare with the scalar Kirchhoff/paraxial model, which predicts no polarisation effect at all -> a clean "vector physics is the which-path mark" demonstration.
- Also: the thickness d as a knob (TE evanescent decay, Fabry-Perot TM resonances) gives continuous control of D without any polariser; FDTD cross-check.
- Caveat: a PEC model has no surface plasmons; at optical frequencies real metals add SPP slit-slit coupling (Schouten 2005, Li-Pacifici) and finite-conductivity cut-off shifts. Quantitatively the PEC result applies to microwaves/THz (where the KAIST-type experiments, unverified, live).
- Single photons add nothing beyond classical vector coherence for a one-photon state (the detection probability equals the classical normalised intensity); the "quantum" content is only the complementarity interpretation. A genuinely quantum extension would need entangled pairs (polarisation-entangled idler as remote eraser), which the engine does not model.

### (c) Novelty: LOW-MEDIUM
The ingredients (TE/TM slit transmission, polarisation which-path, complementarity relations, erasers incl. metasurface ones) are all published; the specific "slit width + plate thickness as built-in which-path marker" calculation was not found, but it is a textbook-level combination of known classical effects.

### (d) Value
Strong pedagogical value (shows where scalar diffraction gives a qualitatively wrong answer: it misses the which-path mark entirely); could inform a simple microwave/THz classroom or lab demonstration of complementarity with no polarisers at the slits. Low research value.

### (e) Not verified
- Opt. Express 2007 different-width nanoslits paper, KAIST THz paper, Leiden "lossy retarder" claim (snippets only); Schouten 2005 TE/visibility details (snippet).

## A6. Recoiling slit (Einstein-Bohr)

### (a) What has been done
Experiments:
1. **X.-J. Liu, Q. Miao, F. Gel'mukhanov, M. Patanen, O. Travnikova, C. Nicolas, H. Agren, K. Ueda, C. Miron, "Einstein-Bohr recoiling double-slit gedanken experiment performed at the molecular level", Nat. Photon. 9, 120-125 (2015; online 1 Dec 2014), doi:10.1038/nphoton.2014.289.** Crossref API metadata (first 8 authors returned; last author from memory -> **not verified**). O2 core photoionisation: the two O atoms are the slits, the photoelectron is the projectile; recoil-induced loss of interference (content: not read on a fetched page).
2. **V. Fedoseev, H. Lin, Y.-K. Lu, Y. K. Lee, J. Lyu, W. Ketterle, "Coherent and Incoherent Light Scattering by Single-Atom Wave Packets", Phys. Rev. Lett. 135, 043601 (2025), doi:10.1103/zwhd-1k2t, arXiv:2410.19671.** Crossref API (DOI lookup) + search snippets (MIT news 28 Jul 2025): ultracold atoms in a lattice as "slits"; coherence of scattered light set by the atomic wave-packet "fuzziness"; independent of whether the trap is on ("the springs do not matter").
3. **Y.-C. Zhang, H.-W. Cheng, Z.-Q. Zengxu, Z. Wu, R. Lin, Y.-C. Duan, J. Rui, M.-C. Chen, C.-Y. Lu, J.-W. Pan, "Tunable Einstein-Bohr Recoiling-Slit Gedankenexperiment at the Quantum Limit", Phys. Rev. Lett. 135, 230202 (2025), doi:10.1103/93zb-lws3, arXiv:2410.10664.** Verified: https://arxiv.org/abs/2410.10664 + Crossref DOI lookup. Single 87Rb atom in a tweezer, 3-D motional ground state, as the movable slit; trap depth tunes momentum uncertainty and the visibility; heating/precession add classical noise (quantum-to-classical transition). (Search snippet: momentum uncertainty 0.78-1.60 photon momenta -- not seen on the abstract page.)
Theory:
4. **H. Lin, Y.-K. Lu, V. Fedoseev, Y. K. Lee, J. Lyu, W. Ketterle, "Fringe visibility and which-way information in Young's double slit experiments with light scattered from single atoms", Phys. Rev. A 113, 022219 (2026), doi:10.1103/dyg4-vswk, arXiv:2507.19801.** Verified: https://arxiv.org/abs/2507.19801. Analyses and generalises both single-atom experiments (vibrational excitation as which-way marker).
5. **S. Tanimura, "Complementarity and the nature of uncertainty relations in Einstein-Bohr recoiling slit experiment", Quanta 4(1), 1-9 (2015), doi:10.12743/quanta.v4i1.35, arXiv:quant-ph/0703118.** Verified: https://arxiv.org/abs/quant-ph/0703118. Fully quantum wall + particle; Kennard-type relation governs complementarity; proposes experiment.
6. **T. Qureshi, R. Vathsan, "Einstein's Recoiling Slit Experiment, Complementarity and Uncertainty", Quanta 2, 58-65 (2013), doi:10.12743/quanta.v2i1.11, arXiv:1210.4248.** Verified: https://arxiv.org/abs/1210.4248. Entanglement particle-slit -> Englert-Greenberger-Yasin relation.
7. D. S. Starke, J. Maziero, M. L. W. Basso, T. Qureshi, "Bohr's complementarity" (review), arXiv:2605.26375 (May 2026). Verified: https://arxiv.org/abs/2605.26375 (abstract does not mention recoiling-slit experiments; coverage unknown).

Searched for an exact numerical two-body (projectile + slit-plate) TDSE with Bohm trajectories of a recoiling slit: **none found** (two searches; only reduced-density/decoherence trajectories of Sanz-Borondo, arXiv:quant-ph/0310096, which do not model the slit as a dynamical body).

### (b) What remains open (narrow)
- Standard analyses (Qureshi-Vathsan, Tanimura, Lin et al. 2026) use the impulse picture: visibility = overlap <phi_slit | e^{i q X} phi_slit> of the slit's motional state shifted by the momentum transfer. Narrow open computation: an exact configuration-space TDSE for (projectile x, z) x (plate transverse coordinate X), potential V(x - X, z) of a plate of finite thickness with two slits, plate in a harmonic trap of frequency Omega, plate mass M graded from >> m down to ~ m. Questions: (i) where the impulse/overlap formula fails -- when the transit time through a thick plate is comparable to 1/Omega or when M ~ m (slit moves during passage, recoil also shifts the fringe positions, not only visibility); (ii) Bohm trajectories of projectile AND plate showing the which-way correlation; (iii) ties to A1: does recoil change the joint (x,t) arrival distribution (timing as which-way information)?
- Engine requirement: 3-D configuration space (x, z, X) with a relative-coordinate potential -- an extension of the current single-particle 3-D solver, not an existing feature (from the task description).

### (c) Novelty: LOW-MEDIUM
Experiments (molecular 2015, single atom 2025 x2) and the textbook entanglement/overlap theory exist; the specific exact two-body finite-thickness simulation beyond the impulse approximation was not found, but its expected physics (overlap formula + small corrections) is unlikely to surprise.

### (d) Value
High pedagogical/visual value (live two-body Bohm picture of complementarity, graded-mass slider). Research value: a quantitative check of the impulse/overlap approximation in the regime of a light, finite-thickness slit with finite transit time. No experiment with slit mass comparable to the projectile mass was found (in Liu et al. 2015 the projectile is a photoelectron, much lighter than the O atoms; in the 2025 atom experiments the projectile is a photon), so the M ~ m limit is a theory-only regime.

### (e) Not verified
- Liu et al. last author and abstract content; MIT PRL abstract (DOI metadata + news snippets only); USTC numbers 0.78-1.60 photon momenta (snippet).

## Summary table

| Cand. | Done (key) | Open (narrow) | Novelty |
|---|---|---|---|
| A1 | Rafsanjani et al. Commun. Phys. 2023 (SC/STD/QF/ABR/PAB/BTC, Gaussian slits, horizontal screen); Das et al. Ann. Phys. 2025 (exact 2-D finite barrier, Bohm FPT + flux only); Cavendish-Das PRA 2025 (ABC vs scattering); Rafsanjani-Cavendish arXiv 2026 (position marginals) | All rules + detector models on one exact plate geometry; robustness of the horizontal-screen proposal to a real plate | medium-low |
| A2 | Das-Duerr 2019; GTZ Sci. Rep. 2024 + Found. Phys. 2024; Das-Aristarhov comment; Drezet 2024; Jozani-Tumulka PRR 2026 (3-D waveguide, CAP/ABC/spinor ABC) | Slit-geometry (x,t) with spin term vs detector models; soft-detector shapes | low |
| A3 | Optical only (Eliezer 2020, Daniel 2022, Ghosh 2023, Zhang 2025 single photons); matter-wave proposals (Palmero 2013, Chen-Tang PRA 2026); theory (Barbier-Goussev-Srivastava 2023, Paterek-Goussev PRL 2026) | Negative longitudinal flux behind real slits for matter waves and its consequence for flux vs positive arrival rules | low-medium |
| A4 | Sinha 2010, Kauten 2017, Cotter 2017 (molecules, <1%); De Raedt 2012 FDTD Maxwell; Sawant 2014, Sinha 2015 (thin-slit Fraunhofer); da Paz/Vieira Gaussian-slit matter-wave models; Quach 2017 | Exact TDSE kappa for matter waves with thick slits; dependence on blocker model | medium |
| A5 | Schouten 2005, Kuzmin 2007, Gan 2007, Li-Pacifici 2016 (SPP coherence); Norrman PRL 2017 (vector complementarity); metasurface erasers 2017-2025 | Slit width + thickness as built-in polarisation which-path mark (PEC modal), eraser; scalar model misses it | low-medium |
| A6 | Liu Nat. Photon. 2015; Fedoseev PRL 2025; Zhang PRL 2025; Lin PRA 2026; Tanimura 2015; Qureshi-Vathsan 2013 | Exact two-body (x,z,X) TDSE beyond impulse approximation, M ~ m, Bohm trajectories of both | low-medium |
