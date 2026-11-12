# Prior-art check A: marking / erasing / AB / time-modulated slits / wall tunnelling (D1–D6)

Date: 2026-11-12. Method: WebSearch + WebFetch of arXiv abstract pages, publisher abstract pages, Crossref API (no mailto). Each claim lists the URL fetched. "not verified" = not seen on a fetched page.

## D1. Graded which-path mark (0..180 deg) for massive particles in a real double slit; Bohm trajectories non-crossing -> crossing

### (a) What has been done
Foundations
- B.-G. Englert, M. O. Scully, G. Süssmann, H. Walther, "Surrealistic Bohm Trajectories", Z. Naturforsch. A 47, 1175–1186 (1992), doi:10.1515/zna-1992-1201. Verified via Crossref https://api.crossref.org/works/10.1515/zna-1992-1201 (metadata only; content of the argument from memory + secondary descriptions in search results, not read).
- B.-G. Englert, "Fringe Visibility and Which-Way Information: An Inequality", PRL 77, 2154 (1996), doi:10.1103/PhysRevLett.77.2154. Crossref https://api.crossref.org/works/10.1103/PhysRevLett.77.2154.

Graded marking with massive particles (no trajectories, not a spatial slit)
- S. Dürr, T. Nonn, G. Rempe, "Fringe Visibility and Which-Way Information in an Atom Interferometer", PRL 81, 5705 (1998), doi:10.1103/PhysRevLett.81.5705. Abstract fetched https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.81.5705 : incomplete which-way information stored in internal atomic state; D and V measured independently; agreement with D^2+V^2<=1. (Bragg-grating atom interferometer, not slits.)
- S. Dürr, T. Nonn, G. Rempe, "Origin of quantum-mechanical complementarity probed by a 'which-way' experiment in an atom interferometer", Nature 395, 33 (1998), doi:10.1038/25653 (Crossref metadata only).
- M. S. Chapman et al., "Photon Scattering from Atoms in an Atom Interferometer: Coherence Lost and Regained", PRL 75, 3783 (1995), doi:10.1103/PhysRevLett.75.3783 (Crossref metadata only; graded loss of contrast vs path separation — content not re-verified here).

Graded marking WITH Bohm/weak-value trajectories (photons)
- Y. Xiao, H. M. Wiseman, J.-S. Xu, Y. Kedem, C.-F. Li, G.-C. Guo, "Observing momentum disturbance in double-slit 'which-way' measurements", Sci. Adv. 5, eaav9547 (2019), doi:10.1126/sciadv.aav9547, arXiv:1805.02059. Fetched https://arxiv.org/abs/1805.02059 and https://ar5iv.arxiv.org/html/1805.02059 : single photons, birefringent double slit, Bohmian trajectories reconstructed by weak measurement; PARTIAL which-way measurements implemented ("WWMs with partial information, allowing a nonzero visibility V to remain"); the Bohmian momentum change "nonclassically accumulates during the propagation"; relation <|p|> >= (1-V) 2hbar/(pi d) tested. Text does not state explicitly whether trajectories cross x=0.
- D. H. Mahler, L. Rozema, K. Fisher, L. Vermeyden, K. J. Resch, H. M. Wiseman, A. Steinberg, "Experimental nonlocal and surreal Bohmian trajectories", Sci. Adv. 2, e1501466 (2016), doi:10.1126/sciadv.1501466. Crossref https://api.crossref.org/works/10.1126/sciadv.1501466 (title/authors/teaser only; publisher and PMC pages blocked). Entangled photon pairs; surreal trajectories reproduced. Whether intermediate marks were used: not verified.
- S. Kocsis et al., "Observing the Average Trajectories of Single Photons in a Two-Slit Interferometer", Science 332, 1170 (2011), doi:10.1126/science.1202218 (Crossref metadata).

Bohm trajectories with partial coherence / decoherence (matter waves, theory, numerics)
- A. S. Sanz, F. Borondo, "A quantum trajectory description of decoherence", Eur. Phys. J. D 44, 319 (2007), doi:10.1140/epjd/e2007-00191-8, arXiv:quant-ph/0310096. Fetched https://arxiv.org/abs/quant-ph/0310096 : reduced-density-matrix quantum trajectories with a time-dependent damping (coherence) factor, applied to decoherence in the double-slit.
- A. S. Sanz, F. Borondo, "Contextuality, decoherence and quantum trajectories", Chem. Phys. Lett. 478, 301 (2009), doi:10.1016/j.cplett.2009.07.061, arXiv:0803.2581. Fetched https://arxiv.org/abs/0803.2581 : matter-particle interference; reduced trajectories approximating projections of system+environment Bohm trajectories; explains crossing of subsystem trajectories as interference quenching + erased which-way information.
- A. S. Sanz, F. Borondo, M. J. Bastiaans, "Loss of coherence in double-slit diffraction experiments", PRA 71, 042103 (2005), arXiv:quant-ph/0310095 (search-result snippet; cold-neutron double slit of Zeilinger et al.; incoherence + decoherence both needed). Abstract page not fetched -> partly not verified.
- A. Luis, A. S. Sanz, "What dynamics can be expected for mixed states in two-slit experiments?", Ann. Phys. 357, 95 (2015), doi:10.1016/j.aop.2015.03.030, arXiv:1311.2612. Fetched https://arxiv.org/abs/1311.2612v5 : average (weak-measurement) trajectories for mixed states; even at maximal mixedness both slits shape the average trajectories.
- A. S. Sanz, M. Davidović, M. Božić, S. Miret-Artés, "Understanding interference experiments with polarized light through photon trajectories", Ann. Phys. 325, 763 (2010), doi:10.1016/j.aop.2009.12.005, arXiv:0907.2667. Fetched abstract + ar5iv: polarizers behind slits; ONLY parallel and orthogonal axes computed (no intermediate angles).
- F. Daem, A. Matzkin, "Dynamics, locality and weak measurements: trajectories and which-way information in the case of a simplified double-slit setup", Quantum Stud.: Math. Found. (2024), doi:10.1007/s40509-024-00337-4, arXiv:2403.10197. Fetched https://arxiv.org/abs/2403.10197 : weakly coupled pointers, "weak trajectories" vs Bohm. Search-snippet (not on the abstract page): with sufficiently strong coupling Bohm trajectories of one branch cross and reach the other detector.

### (b) What remains open (narrow)
- No paper found that computes, for a MASSIVE particle passing a finite-thickness, non-paraxial double slit, the full family of Bohm (Pauli-current) trajectories as a function of a continuously graded spin mark theta = 0..180 deg (overlap |<chi1|chi2>| = cos(theta/2)), i.e. the fraction of trajectories that cross the symmetry plane vs theta, against D(theta), V(theta) from the same run. Sanz–Borondo do a damped-coherence reduced model (not a spin marker, not exact system+marker dynamics); Xiao et al. 2019 do graded WWM for photons with weak-value reconstruction; Sanz et al. 2010 do photons with only 0/90 deg polarizers.
- Also open-looking: whether with the Pauli (spin) current the crossing set appears continuously or abruptly in theta, and where along z the crossing occurs (near field inside the thick slit vs far field) — Xiao et al. state momentum disturbance accrues late for photons; a matter-wave counterpart with real slits was not found.
- Caveat: the "crossing vs theta" is a fairly direct consequence of the reduced-current formula j = Re(psi1* grad psi1 + psi2* grad psi2 + 2 Re<chi1|chi2> ...) — a theorist may consider it a textbook exercise. Novelty is in the exact, non-paraxial, thick-slit numerics for He/C60 and the comparison with an actual experiment, not in the concept.

### (c) Novelty: LOW–MEDIUM
Concept (graded mark -> visibility and trajectory crossing) is covered by Sanz–Borondo (theory, matter waves, decoherence factor) and Xiao et al. 2019 (experiment, photons, partial WWM); only the specific exact-numerics combination (spin mark, thick slits, massive particles, crossing fraction vs theta) seems unpublished.

### (d) Value
A clean, reproducible teaching/benchmark figure (D^2+V^2 vs theta with trajectory crossing fraction); a prediction for a possible matter-wave weak-measurement trajectory experiment (none found for atoms/electrons). Moderate research value; high pedagogical value.

### (e) Not verified
- Whether Mahler et al. 2016 used intermediate measurement bases.
- Whether Xiao et al. 2019 trajectories cross x=0 (paper text silent).
- Any matter-wave weak-measurement trajectory experiment (none found in two searches; absence not proven).
- Hiley/Callaghan/Maroney "Quantum trajectories, real, surreal or an approximation to a deeper process?" (2000) and Dürr–Fusseder–Goldstein–Zanghì 1993 comment: not fetched.

## D2. Delayed-choice marking / erasing for massive particles in a SPATIAL double slit (time-dependent spin rotation; pattern, Bohm trajectories, arrival times)

### (a) What has been done
Photon experiments (spatial double slit or interferometer)
- Y.-H. Kim, R. Yu, S. P. Kulik, Y. Shih, M. O. Scully, "Delayed 'Choice' Quantum Eraser", PRL 84, 1 (2000), doi:10.1103/PhysRevLett.84.1 (Crossref metadata).
- S. P. Walborn, M. O. Terra Cunha, S. Pádua, C. H. Monken, "Double-slit quantum eraser", PRA 65, 033818 (2002), doi:10.1103/PhysRevA.65.033818 (Crossref metadata).
- V. Jacques, E. Wu, F. Grosshans, F. Treussart, P. Grangier, A. Aspect, J.-F. Roch, "Experimental Realization of Wheeler's Delayed-Choice Gedanken Experiment", Science 315, 966 (2007), doi:10.1126/science.1136303 (Crossref metadata).
- X.-s. Ma, J. Kofler, A. Zeilinger, "Delayed-choice gedanken experiments and their realizations", Rev. Mod. Phys. 88, 015005 (2016), doi:10.1103/RevModPhys.88.015005, arXiv:1407.2930. Fetched https://arxiv.org/abs/1407.2930 : review covers delayed-choice quantum erasure; abstract does not name a massive-particle delayed eraser. (A search snippet says the review has a "Matter-wave quantum erasure" section; not read.)

Massive particles — delayed choice, but NOT a which-path eraser and NOT spatial slits
- A. G. Manning, R. I. Khakimov, R. G. Dall, A. G. Truscott, "Wheeler's delayed-choice gedanken experiment with a single atom", Nat. Phys. 11, 539 (2015), doi:10.1038/nphys3343 (Crossref metadata; Bragg-pulse momentum-space Mach–Zehnder with the second beam splitter chosen late — Wheeler type, no marker).

Massive particles — quantum erasure / graded which-path (NOT delayed, NOT spatial slits)
- S. Dürr, T. Nonn, G. Rempe, PRL 81, 5705 (1998) and Nature 395, 33 (1998) (see D1).
- Y. Margalit, Z. Zhou, S. Machluf, D. Rohrlich, Y. Japha, R. Folman, "A self-interfering clock as a 'which path' witness", Science 349, 1205 (2015), doi:10.1126/science.aac6498, arXiv:1505.05765. Fetched https://arxiv.org/abs/1505.05765 : 87Rb on an atom chip, internal spin superposition "ticks" at different rates in the two arms -> which-path information -> reduced visibility (graded by time lag per search summary; the abstract itself does not state grading explicitly).
- C. J. Wood, M. O. Abutaleb, M. G. Huber, M. Arif, D. G. Cory, D. A. Pushin, "Quantum correlations in a noisy neutron interferometer", PRA 90, 032315 (2014), doi:10.1103/PhysRevA.90.032315 (Crossref metadata; search snippet: spin–path entangled neutron interferometer used to implement a quantum eraser and a which-way measurement). Perfect-crystal interferometer, not slits; not delayed.
- I. Weisz et al., "An electronic quantum eraser", Science 344, 1363 (2014), doi:10.1126/science.1248459 (Crossref; editor summary fetched via Crossref: which-path acquired and then erased; search snippet: smooth variation of the degree of erasure). Quantum-Hall electronic interferometer, not free electrons, not delayed.

Bohm-theory treatments of delayed choice
- B. J. Hiley, R. E. Callaghan, "Delayed-choice experiments and the Bohm approach", Phys. Scr. 74, 336 (2006), doi:10.1088/0031-8949/74/3/007, arXiv:1602.06100. Fetched https://arxiv.org/abs/1602.06100 : Wheeler and ESSW (cavity in one arm) set-ups; correct Bohm analysis is local and agrees with QM. Abstract does not mention a spin marker or a spatial double slit.
- A. S. Sanz, "Investigating puzzling aspects of the quantum theory by means of its hydrodynamic formulation", Found. Phys. 45, 1153 (2015), doi:10.1007/s10701-015-9917-2, arXiv:1501.05783. Fetched https://arxiv.org/abs/1501.05783 : Bohmian treatment of Young's two-slit and a "realistic simulation" of Wheeler's delayed choice (photon interferometer).
- J. Fankhauser, "Taming the Delayed Choice Quantum Eraser", Quanta 8, 44 (2019), arXiv:1707.07884. Fetched https://arxiv.org/abs/1707.07884 : standard QM + de Broglie–Bohm resolution, no retrocausality (photon pair set-up, no numerics stated).
- C. Dewdney, L. Hardy, E. J. Squires, "How late measurements of quantum trajectories can fool a detector", Phys. Lett. A 184, 6 (1993) — NOT verified (from memory; not fetched).

Arrival times in a double slit (relevant to the "arrival times" observable)
- A. Ayatollah Rafsanjani, M. Kazemi, A. Bahrampour, M. Golshani, "Can the double-slit experiment distinguish between quantum interpretations?", Commun. Phys. 6, 195 (2023), doi:10.1038/s42005-023-01315-9, arXiv:2301.02641. Fetched https://arxiv.org/abs/2301.02641v2 : joint space–time detection distributions differ between interpretations; testable in a modified double slit with single-atom interferometry; v2 adds Aharonov–Bohm and relative-phase analyses.
- Same group, "Non-local interference in arrival time", Sci. Rep. (2024), doi:10.1038/s41598-024-54018-8, arXiv:2307.04811 (search snippet only; entangled atom pairs, Bohmian arrival times).
- S. Das, M. Nöth, D. Dürr, "Exotic Bohmian arrival times of spin-1/2 particles: An analytical treatment", PRA 99, 052124 (2019), doi:10.1103/PhysRevA.99.052124 (Crossref metadata) — spin-dependent Bohmian arrival times (waveguide, not double slit).

### (b) What remains open (narrow)
- No experiment found of a delayed which-path MARK or ERASER for massive particles in a spatial double slit (all massive-particle erasers found are interferometers: Bragg atom interferometer, atom-chip Stern–Gerlach, neutron crystal, quantum-Hall). Massive-particle delayed choice exists only in Wheeler form (Manning 2015).
- No numerical study found that, for a massive spin-1/2 (or spin-carrying atom) wave packet in a finite-thickness double slit, applies a time-dependent, spatially local spin rotation (i) after the packet leaves the slits but before the two beams overlap, (ii) after partial overlap, (iii) never, and compares spin-resolved patterns, Pauli/Bohm trajectories (crossing vs non-crossing, and the moment trajectories re-route) and arrival-time distributions. Bohmian discussions (Hiley–Callaghan, Fankhauser, Sanz) are for photon interferometers/cavity markers and largely analytic or schematic.
- Physics caution for the plan: with a single-particle spin marker, "erasure" after the beams overlap is only possible by post-selecting the spin in a rotated basis (spin-resolved flux), not by a unitary; a unitary "unmark" works only while beams are spatially separated. The engine must report spin-resolved fringe/anti-fringe patterns, otherwise the demo is trivially "no effect". This makes the demo partly a re-statement of the textbook eraser — novelty sits in trajectories and arrival times.

### (c) Novelty: MEDIUM (numerics) / HIGH (as an experiment proposal)
Concept and Bohm interpretation are well discussed for photons; the exact matter-wave spatial-slit computation with time-dependent spin rotation and arrival-time readout was not found, and no massive-particle spatial-slit delayed eraser experiment was found.

### (d) Value
Would give a concrete, quantitative proposal (timing windows, field gradients, spin-rotation region size, expected spin-resolved visibility) for a He*/metastable atom or neutron double-slit delayed eraser; clarifies where Bohm trajectories "decide" (locally, at the time of the spin rotation for the same-particle marker). Arrival-time readout links to the Commun. Phys. 2023 proposal.

### (e) Not verified
- Content of Ma–Kofler–Zeilinger "Matter-wave quantum erasure" section (could list a massive delayed eraser I missed — must be checked before claiming novelty in print).
- Dewdney–Hardy–Squires 1993 (not fetched).
- Whether Margalit 2015 grades the which-path continuously (abstract silent).

### D2 addendum (checked after writing the section)
- Ma–Kofler–Zeilinger RMP 2016, Sec. IV "Matter-wave quantum erasure", read via https://ar5iv.arxiv.org/html/1407.2930 (offset 50000–150000): cites Eichmann et al. 1993 (two trapped ions, scattered light as marker), Dürr et al. 1998 (internal-state marker, atom interferometer), Weisz et al. 2014 (electronic), Bramon et al. 2004 (kaon proposal). None is delayed. Massive-particle delayed choice in the review: Manning et al. (single atom, Wheeler type) and NMR "quantum delayed-choice" (Roy 2012, Auccaise 2012). Neutron delayed-choice: proposals only (Miller & Wheeler 1983; Greenberger et al. 1983).
- => As of the 2016 review, NO delayed-choice quantum eraser with massive particles existed. A 2016–2026 search (two queries) found none either. Status: absence supported by the review + searches, not proven.

## D3. Time-dependent Aharonov–Bohm flux (switched on / ramped during passage)

### (a) What has been done (all theory; no full time-dependent wave-packet numerics found; no dedicated experiment found)
- D. Singleton, E. C. Vagenas, "The covariant, time-dependent Aharonov-Bohm Effect", Phys. Lett. B 723, 241 (2013), doi:10.1016/j.physletb.2013.05.014, arXiv:1305.1498. Fetched https://arxiv.org/abs/1305.1498 : infinite solenoid with time-varying flux -> net phase shift vanishes; AB phase cancelled by the phase from the electric field outside the solenoid; notes it "may already have been confirmed experimentally".
- J. Macdougall, D. Singleton, "Stokes' theorem, gauge symmetry and the time-dependent Aharonov-Bohm effect", J. Math. Phys. 55, 042101 (2014), doi:10.1063/1.4869324, arXiv:1312.1405. Fetched https://arxiv.org/abs/1312.1405 : two-slit set-up with time-varying solenoid flux between the slits; electric-field phase cancels the time-dependent part of the magnetic AB phase; non-single-valued gauge functions; proposes an experiment.
- J. Macdougall, D. Singleton, E. C. Vagenas, "Revisiting the Marton, Simpson, and Suddeth experimental confirmation of the Aharonov-Bohm effect", Phys. Lett. A 379, 1689 (2015), doi:10.1016/j.physleta.2015.05.007, arXiv:1505.01510. Fetched https://arxiv.org/abs/1505.01510 : the 1954 electron-interferometer experiment used a time-varying field; its result is argued to agree with cancellation; calls for a new time-dependent AB experiment.
- J. Jing, Y.-F. Zhang, K. Wang, Z.-W. Long, S.-H. Dong, "On the time-dependent Aharonov–Bohm effect", Phys. Lett. B 774, 87 (2017), doi:10.1016/j.physletb.2017.09.041 (search results/INIS record only; conflicting snippets about whether the pattern shifts — NOT verified).
- S. Rai Choudhury, S. Mahajan, "Direct calculation of time varying Aharonov Bohm effect", Phys. Lett. A (2019), doi:10.1016/j.physleta.2019.05.008, arXiv:1903.04138. Fetched https://arxiv.org/abs/1903.04138 : weak time-dependent field; induced E does not enter the action, only alters the path; frequency-dependent AB phase -> static result at low frequency, averages out at high frequency.
- M. Wakamatsu, "On the time-dependent Aharonov-Bohm effect and the 4-dimensional Stokes theorem", arXiv:2406.18046 (2024; v2 says "to appear in Annals of Physics"). Fetched https://arxiv.org/abs/2406.18046 : the Singleton cancellation is only partly correct; a time-dependent AB effect likely exists.
- M. Wakamatsu, "On the role of induced electric field in the time-dependent Aharonov-Bohm effect", arXiv:2511.07775 (Nov 2025). Fetched https://arxiv.org/abs/2511.07775 : induced E outside the solenoid has a "highly nontrivial effect" usable to test existence of the effect (no numerics stated in abstract).
- S. Gao, "Generalized Aharonov-Bohm Effect", Found. Phys. 55, 85 (2025), doi:10.1007/s10701-025-00900-y, arXiv:2601.17659. Fetched https://arxiv.org/abs/2601.17659 : WKB; circular paths, quasistatic: phase proportional to time-averaged enclosed flux; including kinetic contributions total = e*Phi(0) (initial flux); non-circular paths depend on flux history and geometry.
- Related numerics, static flux only: N. Simicevic, "Finite Difference-Time Domain solution of the Dirac equation and the dynamics of the Aharonov-Bohm effect", arXiv:0909.2584 (2009). Fetched https://arxiv.org/abs/0909.2584 : 3-D FDTD Dirac wave packet in AB-type vector potential; abstract does not mention time-dependent flux.

### (b) What remains open (narrow)
- No paper found that solves the full TDSE (non-perturbative, non-WKB) for a wave packet passing a real double slit with a solenoid between the slits whose flux is switched on / ramped at a chosen time relative to passage, including the induced E = -dA/dt outside the solenoid (automatic in H=(p-qA(x,t))^2/2m in the quasistatic limit), and reads out the fringe shift vs switching time (before passage / during / after passage but before detection / after detection). The literature is a live dispute (Singleton et al.: cancellation; Choudhury–Mahajan: frequency-dependent; Wakamatsu 2024–25 and Gao 2025: effect exists, time-averaged or initial flux) based on line/area integrals and WKB.
- Concrete computable question: fringe shift Delta(t_switch, tau_ramp) for a He atom (or electron) packet; does it equal (q/hbar)Phi at passage, at detection, Phi(0), the time average over the packet's transit, or zero? Plus the Bohm-trajectory view of where the canonical vs kinetic momentum kick occurs.
- Caveat: the engine is quasistatic (no retardation, no radiation fields, no solenoid back-action); for neutral atoms AB requires an AC/HMW-type coupling — the clean demonstrator is an electron. The result answers the question within non-relativistic quasistatic QM, which is the regime all the disputants claim to treat.

### (c) Novelty: MEDIUM–HIGH
Active, unresolved theoretical dispute (2013–2026) with no exact wave-packet numerics and no experiment found; an exact TDSE answer for finite packets is directly relevant. Risk: a theorist may say the answer is already fixed by gauge invariance (phase = flux enclosed when the packets close the loop); the numerics must be careful about gauge choice, packet length vs ramp time, and the "switch after passage" case.

### (d) Value
Would adjudicate (within quasistatic QM) between cancellation / time-average / initial-flux claims; would give an experimental design window (ramp time vs transit time) for the "new time-dependent AB experiment" requested by Macdougall–Singleton–Vagenas 2015.

### (e) Not verified
- Jing et al. 2017 conclusion (conflicting snippets).
- Whether any group (e.g. Batelaan, Tonomura successors) attempted a time-dependent AB experiment after 2015 (two searches found none).
- Whether Wakamatsu 2025 contains numerics.

## D4. Scalar (electric) Aharonov–Bohm effect: pulsed potential on one slit channel vs static potential difference

### (a) What has been done
Original and electrostatic (static, with fields) experiments
- Y. Aharonov, D. Bohm, "Significance of Electromagnetic Potentials in the Quantum Theory", Phys. Rev. 115, 485 (1959), doi:10.1103/PhysRev.115.485 (Crossref metadata).
- G. Matteucci, G. Pozzi, "New Diffraction Experiment on the Electrostatic Aharonov-Bohm Effect", PRL 54, 2469 (1985), doi:10.1103/PhysRevLett.54.2469 (Crossref metadata).
- S. A. Hilbert, A. Caprez, H. Batelaan, "Experimental observation of time-delays associated with electric Matteucci–Pozzi phase shifts", New J. Phys. 13, 093025 (2011), doi:10.1088/1367-2630/13/9/093025 (Crossref metadata; content per search snippet).
- A. van Oudenaarden, M. H. Devoret, Yu. V. Nazarov, J. E. Mooij, "Magneto-electric Aharonov–Bohm effect in metal rings", Nature 391, 768 (1998), doi:10.1038/35808 (Crossref metadata) — solid-state rings, not free particles.
- S. Becker, G. Guzzinati, A. Béché, J. Verbeeck, H. Batelaan, "Asymmetry and non-dispersivity in the Aharonov-Bohm effect", Nat. Commun. 10, 1700 (2019), doi:10.1038/s41467-019-09609-9, arXiv:1705.07139. Crossref abstract: free electrons passing a magnetized nanorod; tests Shelankov's quantum "force" vs Zeilinger's dispersionless theorem — MAGNETIC AB, not scalar.

Scalar AB with MASSIVE NEUTRAL particles (magnetic-moment coupling; pulsed/time-dependent, force-free) — DONE
- B. E. Allman, A. Cimmino, A. G. Klein, G. I. Opat, H. Kaiser, S. A. Werner, "Scalar Aharonov-Bohm experiment with neutrons", PRL 68, 2409 (1992), doi:10.1103/PhysRevLett.68.2409; erratum PRL 70, 250 (1993). Abstract fetched https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.68.2409 : pulsed magnetic fields on neutrons in a force-free region; expected phase shifts measured accurately.
- G. Badurek, H. Weinfurter, R. Gähler, A. Kollmar, S. Wehinger, A. Zeilinger, "Nondispersive phase of the Aharonov-Bohm effect", PRL 71, 307 (1993), doi:10.1103/PhysRevLett.71.307 (Crossref metadata).
- J. van der Zouw, ..., A. Zeilinger, "Aharonov–Bohm and gravity experiments with the very-cold-neutron interferometer", NIM A 440, 568 (2000), doi:10.1016/S0168-9002(99)01038-4 (Crossref metadata).
- K. Shinohara, T. Aoki, A. Morinaga, "Scalar Aharonov-Bohm effect for ultracold atoms", PRA 66, 042106 (2002), doi:10.1103/PhysRevA.66.042106. Abstract fetched https://journals.aps.org/pra/abstract/10.1103/PhysRevA.66.042106 : ultracold Na, time-domain atom interferometer, time-dependent magnetic field; 38 fringes of nearly equal amplitude (non-dispersive); phase vs field within 3%.
- A. Morinaga et al., "Scalar Aharonov–Bohm Phase in Ramsey Atom Interferometry under Time-Varying Potential", Atoms 4, 23 (2016), doi:10.3390/atoms4030023 (Crossref metadata).

Gravitational scalar AB
- C. Overstreet, P. Asenbaum, J. Curti, M. Kim, M. A. Kasevich, "Observation of a gravitational Aharonov-Bohm effect", Science 375, 226 (2022), doi:10.1126/science.abl7152 (Crossref metadata + editor summary: Rb wave packets ~25 cm apart, one near a source mass).

Electric (charge) scalar AB in the ORIGINAL pulsed, shielded form — proposals only
- G. Schütz, A. Rembold, A. Pooch, H. Prochel, A. Stibor, "Effective beam separation schemes for the measurement of the electric Aharonov-Bohm effect in an ion interferometer", Ultramicroscopy 158, 65 (2015), doi:10.1016/j.ultramic.2015.06.016, arXiv:1303.7140. Fetched https://arxiv.org/abs/1303.7140 : proposal, H ions, two tubes at different pulsed potentials, delay-line detector allows continuous beam; ~80 s acquisition predicted.
- T. C. Bachlechner, M. Kleban, "Proposal for testing the electric Aharonov-Bohm effect with superconductors", PRB 101, 174504 (2020), doi:10.1103/PhysRevB.101.174504 (Crossref metadata; search snippet: "evidently never been observed").
- R. Y. Chiao, H. Hart, N. A. Inan, M. Scheibner, J. Sharping, D. A. Singleton, M. E. Tobar, "Energy level shift of quantum systems via the electric Aharonov-Bohm effect", PRA 107, 042209 (2023), doi:10.1103/PhysRevA.107.042209, arXiv:2212.03437. Fetched https://arxiv.org/abs/2212.03437 : Faraday cage with time-varying uniform potential -> energy-level shift (sidebands), link to AC Stark effect; no two-slit.
- R. Vieira dos Santos, "Beyond the Lorenz Gauge: Probing a Stueckelberg Scalar in the Electric Aharonov-Bohm Effect", arXiv:2605.08148 (May 2026). Fetched https://arxiv.org/abs/2605.08148 : states the electric AB effect "has never been experimentally tested in its original formulation with shielded, time-dependent potentials"; proposes ps-resolved single-electron interferometry.

Numerics
- No exact TDSE study found of a finite wave packet in a two-slit geometry with a pulsed uniform potential in one channel, quantifying (i) residual force/dispersion when the packet tails overlap the switching edges, (ii) the transition from pulsed AB (phase only) to static potential step (phase + refraction/delay — the Matteucci–Pozzi / Hilbert–Caprez–Batelaan case). Two searches; absence not proven.

### (b) What remains open (narrow)
- The physics of the scalar AB phase itself is established (neutrons 1992–93, cold atoms 2002, gravitational 2022); the CHARGED-particle pulsed version is untested (proposals 2015, 2020, 2026). An engine demonstration is therefore a known effect, not a discovery.
- Narrow open computation: for an electron (or H+ ion as in Schütz et al.) packet in a real double slit with a pulsed potential region behind one slit, map fringe shift and visibility vs pulse timing/duration relative to the packet's transit, packet length and edge sharpness — i.e. the "non-dispersive window" and the leakage into a dispersive (force) contribution and arrival-time delay. This is a design curve for the proposed ion/electron experiments; not found published.

### (c) Novelty: LOW (as physics) / MEDIUM (as quantitative design numerics for the charged-particle experiment)
Scalar AB for massive neutral particles is experimentally done; electric charged version is only proposed; exact wave-packet design numerics not found.

### (d) Value
Directly informs the pending charged-particle electric-AB experiments (Stibor-group ion interferometer, ps electron interferometry): tolerances on pulse timing vs packet length; clean contrast between pulsed (dispersionless, no delay) and static (delay, Hilbert–Caprez–Batelaan) cases in one code. High pedagogical value.

### (e) Not verified
- Content of Matteucci–Pozzi 1985 and Badurek 1993 abstracts (metadata only).
- Search snippet claim (in arXiv:1006.1385v2) that a steady-state electric AB version was observed — not checked.
- Whether any 2024–2026 experiment reported the charged pulsed electric AB (none found; the May 2026 preprint says never tested).

## D5. Time-modulated slit: Floquet sidebands mark the path in energy; time-integrated fringes lost, recovered by time-resolved detection (beats at w)

### (a) What has been done
Diffraction / double slit in time (no spatial which-path marking)
- M. Moshinsky, "Diffraction in Time", Phys. Rev. 88, 625 (1952), doi:10.1103/PhysRev.88.625 (Crossref metadata).
- P. Szriftgiser, D. Guéry-Odelin, M. Arndt, J. Dalibard, "Atomic Wave Diffraction and Interference Using Temporal Slits", PRL 77, 4 (1996), doi:10.1103/PhysRevLett.77.4 (Crossref metadata).
- A. Steane, P. Szriftgiser, P. Desbiolles, J. Dalibard, "Phase Modulation of Atomic de Broglie Waves", PRL 74, 4972 (1995), doi:10.1103/PhysRevLett.74.4972 (Crossref metadata; modulated atom mirror -> energy sidebands, from memory, not verified on a page).
- F. Lindner, M. G. Schätzel, H. Walther, A. Baltuška, E. Goulielmakis, F. Krausz, D. B. Milošević, et al., "Attosecond Double-Slit Experiment", PRL 95, 040401 (2005), doi:10.1103/PhysRevLett.95.040401 (Crossref metadata; search snippet: fringes in the energy domain, visibility depends on which-way information).
- R. Tirole, S. Vezzoli, E. Galiffi, I. Robertson, D. Maurice, B. Tilmann, S. A. Maier, J. B. Pendry, R. Sapienza, "Double-slit time diffraction at optical frequencies", Nat. Phys. 19, 999 (2023), doi:10.1038/s41567-023-01993-w (Crossref metadata).

Energy-marked paths with time-dependent (beat) readout — MASSIVE particles (neutron crystal interferometers) — DONE
- G. Badurek, H. Rauch, D. Tuppinger, "Neutron interferometric double-resonance experiment", PRA 34, 2600 (1986), doi:10.1103/PhysRevA.34.2600. Abstract fetched https://journals.aps.org/pra/abstract/10.1103/PhysRevA.34.2600 : RF spin flips with energy exchange in both beams; coherence preserved; a tiny energy difference 8.6e-17 eV between the interfering beams gives "quantum beating on a macroscopic time scale".
- J. Summhammer, K. A. Hamacher, H. Kaiser, H. Weinfurter, D. L. Jacobson, S. A. Werner, "Multiphoton Exchange Amplitudes Observed by Neutron Interferometry", PRL 75, 3206 (1995), doi:10.1103/PhysRevLett.75.3206 (Crossref metadata; oscillating field in one arm -> multiphoton sidebands — content not verified on a page).
- S. Sponar, J. Klepp, R. Loidl, S. Filipp, G. Badurek, Y. Hasegawa, H. Rauch, "Coherent energy manipulation in single-neutron interferometry", PRA 78, 061604(R) (2008), doi:10.1103/PhysRevA.78.061604, arXiv:0803.3545. Fetched https://arxiv.org/abs/0803.3545 : RF flipper in one arm creates energy superposition, second flipper at w/2 compensates; stationary interference restored.
- H. Geppert-Kleinrath, T. Denkmayr, S. Sponar, H. Lemmel, T. Jenke, Y. Hasegawa, "Multifold paths of neutrons in the three-beam interferometer detected by a tiny energy kick", PRA 97, 052111 (2018), doi:10.1103/PhysRevA.97.052111. Abstract fetched https://journals.aps.org/pra/abstract/10.1103/PhysRevA.97.052111 : paths marked by small energy shifts; which-way information read out from intensity oscillating sinusoidally in time at path-specific frequencies (interference of stationary main component with energy-shifted parts). (Search snippet: amount of marking controlled by spin rotation angle alpha — graded.)

Photons / light
- M. Fernandez-Guasti, C. García-Guerrero, "Time and Space Resolved First Order Optical Interference Between Distinguishable Photon Paths", Front. Phys. 9, 813565 (2022), doi:10.3389/fphy.2021.813565. Fetched https://www.frontiersin.org/articles/10.3389/fphy.2021.813565 : two lasers of slightly different frequency in a Young-equivalent geometry; streak camera resolves fringes in time and space; fringes tilt (move) — time-resolved interference with frequency-labelled paths (classical light; authors' interpretation contested).
- T. Legero, T. Wilk, M. Hennrich, G. Rempe, A. Kuhn, "Quantum Beat of Two Single Photons", PRL 93, 070503 (2004), doi:10.1103/PhysRevLett.93.070503 (Crossref metadata; two-photon interference of frequency-distinguishable photons recovered by time-resolved detection — from memory, not verified on a page).
- Danan, Farfurnik, Bar-Ad, Vaidman, "Asking photons where they have been", PRL 111, 240402 (2013) — mirrors vibrating at different frequencies tag paths; NOT verified (not fetched).

Free electrons (path marked by inelastic light interaction)
- F. J. García de Abajo, C. I. Velasco, "Spectrometer-Free Electron Spectromicroscopy", arXiv:2504.16894 (2025). Fetched https://arxiv.org/abs/2504.16894 : proposal; electron in two-path superposition, one path near laser-illuminated specimen; electron–light (energy-sideband) scattering degrades interference; readout vs laser frequency, no time-resolved recovery.
- J.-W. Henke, H. Jeng, C. Ropers, "Quantum eraser experiments for the demonstration of entanglement between swift electrons and light", PRA 111, 012610 (2025), arXiv:2404.11368. Fetched https://arxiv.org/abs/2404.11368 : proposal (marker photons via cathodoluminescence; energy-filtered electrons).

Theory of oscillating / time-dependent slits
- Search snippets only: "space-and-time-dependent slit" diffraction patterns in space and time; wave packets on an amplitude-modulated barrier with Floquet momentum sidebands (exact papers not identified -> not verified).

### (b) What remains open (narrow)
- The core idea (paths labelled by energy -> time-integrated visibility lost, recovered as beats in time-resolved detection) is established: neutrons (Badurek 1986; Geppert-Kleinrath 2018, with graded marking), photons (Fernandez-Guasti 2022, Legero 2004). This is NOT new.
- Not found: a SPATIAL double slit for matter waves in which ONE SLIT itself is modulated (oscillating barrier height or width, i.e. amplitude + phase modulation, "diffraction in time" inside one channel), computed exactly (non-paraxial, finite thickness), giving (i) the sideband weights vs modulation depth and w, (ii) the time-integrated visibility vs those weights (D^2+V^2 with an energy marker), (iii) the time-resolved space–time fringe pattern (moving fringes at w) and arrival-time spectra, (iv) Bohm trajectories in the modulated slit. Also not found: the case where w is comparable to the inverse transit time through the thick slit (non-adiabatic, sidebands not separable from diffraction in time).
- Physics caution: with a pure phase modulation of one slit the time-integrated fringe visibility drops by |J0(beta)| (textbook FM); the engine result must be compared against this analytic baseline before claiming anything.

### (c) Novelty: LOW–MEDIUM
Concept done with neutrons and light; only the spatial-slit, amplitude-modulated, non-adiabatic exact-numerics version for atoms/electrons appears unpublished.

### (d) Value
A design study for a vibrating-nanomembrane or electrically modulated slit for He/electrons, linking diffraction in time with which-path complementarity; good pedagogical bridge between Moshinsky diffraction in time and Englert duality. Research value modest unless the non-adiabatic regime shows something beyond the J0 baseline.

### (e) Not verified
- Summhammer 1995, Steane 1995, Legero 2004 content (metadata only), Danan 2013 (not fetched).
- Whether any experiment modulated one slit of a material double slit for atoms/electrons (two searches found none).

### D2 cross-reference (found during D5)
- J.-W. Henke, H. Jeng, M. Sivis, C. Ropers, "Observation of quantum entanglement between free electrons and photons", arXiv:2504.13047 (Apr 2025). Fetched https://arxiv.org/abs/2504.13047 : electron in a superposition of two beams passes a nanostructure; transition-radiation photon polarization correlated with the path; tomography violates Peres–Horodecki by >7 sigma. A free-electron path marker (quantum-eraser-inspired per search snippet); abstract does not mention delayed choice. Relevant to D2: the first free-electron path–photon entanglement; a delayed-eraser version for free electrons may follow — check before claiming novelty.

## D6. Tunnelling through the wall between the slits (finite barrier) as a "third path"; signature in fringes and in Sorkin's parameter

### (a) What has been done
Sorkin parameter / higher-order interference
- R. D. Sorkin, "Quantum mechanics as quantum measure theory", Mod. Phys. Lett. A 9, 3119 (1994), doi:10.1142/S021773239400294X (Crossref abstract seen: hierarchy of sum rules; QM satisfies the second).
- U. Sinha, C. Couteau, T. Jennewein, R. Laflamme, G. Weihs, "Ruling Out Multi-Order Interference in Quantum Mechanics", Science 329, 418 (2010), doi:10.1126/science.1190545 (Crossref metadata + editor summary).
- J. P. Cotter, C. Brand, C. Knobloch, Y. Lilach, O. Cheshnovsky, M. Arndt, "In search of multipath interference using large molecules", Sci. Adv. 3, e1602478 (2017), doi:10.1126/sciadv.1602478 (Crossref; teaser "Matter waves pass multipath interference test").

"Nonclassical" (looped) paths make kappa != 0 in standard QM because closing slits changes boundary conditions
- R. Sawant, J. Samuel, A. Sinha, S. Sinha, U. Sinha, "Nonclassical Paths in Quantum Interference Experiments", PRL 113, 120406 (2014), doi:10.1103/PhysRevLett.113.120406, arXiv:1308.2022 (Crossref metadata; search summary of the arXiv abstract: path-integral estimate, looped paths measurable via normalized Sorkin parameter kappa, three-slit proposals).
- A. Sinha, A. H. Vijay, U. Sinha, "On the superposition principle in interference experiments", Sci. Rep. 5, 10304 (2015), arXiv:1412.2198 (search summary only: analytic formula for kappa — not fetched).
- O. S. Magaña-Loaiza, I. De Leon, M. Mirhosseini, R. Fickler, A. Safari, U. Mick, B. McIntyre, P. Banzer, B. Rodenburg, G. Leuchs, R. W. Boyd, "Exotic looped trajectories of photons in three-slit interference", Nat. Commun. 7, 13987 (2016), doi:10.1038/ncomms13987 (Crossref metadata).
- C. Vieira, H. Alexander, G. de Souza, M. Sampaio, I. da Paz, "Exotic looped trajectories in double-slit experiments with matter waves", arXiv:1705.07156 (2017). Fetched https://arxiv.org/abs/1705.07156 : matter-wave double slit; intensity at x=0 vs time of flight; relates Sorkin parameter to looped-path visibility and Gouy phase; neutron estimate |kappa| up to ~0.2.
- J. O. de Almeida, M. Lewenstein, J. Q. Quach, "Significant nonclassical paths with atoms and cavities in the double-slit experiment", PRA 102, 042225 (2020), doi:10.1103/PhysRevA.102.042225, arXiv:2007.05279. Fetched https://arxiv.org/abs/2007.05279 : nonclassical paths "through both slits"; cavity which-way set-up detects a type of nonclassical path with ~1% probability; erase/restore their coherence; exact Born-rule-violation measure.

Finite-barrier slit screens in exact numerics (not analysed for wall tunnelling)
- S. Das, D.-A. Deckert, L. Kellers, S. Krekels, W. Struyve, "Double-slit experiment revisited", Ann. Phys. 479, 170054 (2025), doi:10.1016/j.aop.2025.170054, arXiv:2211.13362. Fetched https://arxiv.org/abs/2211.13362 : Bohmian joint space–time detection distribution for a Gaussian packet through a double-slit potential, incl. one slit closed during flight; He double slit (Kurtsiefer et al. 1997) as illustration. Search snippet (not on the abstract page): the screen is a Gaussian barrier of finite height and thickness; ~25% of trajectories transmitted, rest back-scattered. No wall-tunnelling analysis reported in the abstract.

### (b) What remains open (narrow)
- No paper found that treats tunnelling THROUGH THE INTER-SLIT WALL of finite height V0 and thickness w as an extra path: (i) its amplitude and phase vs V0, w, E; (ii) its signature in the fringe pattern (central-fringe shift/asymmetry, a third "source" between the slits giving a superlattice of fringes at 2x period); (iii) a three-term Sorkin-type kappa defined with the wall as the third "aperture" (wall finite vs infinite while A, B open/closed), compared with the looped-path kappa of Sawant et al.; (iv) Bohm trajectories that pass through the wall and how they share the axis with slit trajectories.
- Physics cautions (important for the plan):
  * For real material plates and thermal/supersonic atoms (He, C60), wall tunnelling is utterly negligible (decay length ~ hbar/sqrt(2 m V0) ~ pm for He with eV barriers). For keV electrons a thin membrane is not a tunnelling barrier but a semi-transparent phase object (over-barrier transmission with mean-inner-potential phase); for neutrons material walls are weak Fermi pseudo-potentials (~100 neV) and slits are made by absorbers. The tunnelling regime is physical mainly for ultracold atoms / BECs with optical (light-sheet) barriers of tunable height, or for low-energy electrons in 2DEG gated slits.
  * Sorkin's kappa needs >= 3 "apertures"; "closing" the wall means changing V0 -> infinity, which also changes the edges of both slits, so kappa != 0 arises from boundary-condition changes as in Sawant et al.; the demo must separate the tunnelling contribution from the generic near-field/looped-path contribution (e.g., by scanning w at fixed slit geometry).

### (c) Novelty: MEDIUM (narrow set-up) / LOW (concept)
Nonclassical-path contributions to kappa are well studied (2014–2020); the specific "tunnelling wall as third path" computation was not found in three searches, but it is a variant of a known theme and is physically relevant only in cold-atom optical-barrier settings.

### (d) Value
A clean, exactly computable model for "how much kappa != 0 comes from a penetrable screen" — useful to the Born-rule-test community as a systematic-error estimate (penetrable/semi-transparent walls in membranes for electrons, light-sheet walls for BECs). Moderate.

### (e) Not verified
- Full content of Sawant 2014 / Sinha 2015 / Magaña-Loaiza 2016 (metadata or search summaries only).
- Whether the Das et al. 2025 screen barrier is low enough for appreciable tunnelling (snippet only).
- Rengaraj et al. (NJP 2018, microwave measurement of nonzero kappa) — recalled, not fetched.

## Cross-cutting prior art relevant to all candidates (engine-level)
- Das, Deckert, Kellers, Krekels, Struyve, Ann. Phys. 479, 170054 (2025), arXiv:2211.13362 (see D6): exact Bohmian space–time detection statistics in a double slit with a time-dependent potential (one slit closed in flight), He atoms. This is the closest existing "engine-type" study; any lfphys demo involving arrival times or switching a slit must cite it and go beyond it (mark/erase, AB flux, modulation).
- Ayatollah Rafsanjani, Kazemi, Bahrampour, Golshani, Commun. Phys. 6, 195 (2023), arXiv:2301.02641 (see D2): interpretations differ in double-slit arrival-time statistics; v2 includes AB analysis.
- Sanz & Borondo 2007/2009, Luis & Sanz 2015 (see D1): Bohmian trajectories with decoherence/mixedness in double slits for matter waves.

## Summary table

| # | Done (closest prior) | Open (narrow) | Novelty |
|---|---|---|---|
| D1 | Graded WWM + reconstructed Bohm trajectories for photons (Xiao et al. Sci. Adv. 2019); matter-wave decoherence trajectories that cross (Sanz–Borondo 2007/2009); graded D/V with atoms (Dürr–Nonn–Rempe 1998) | Crossing fraction vs spin-mark angle, exact Pauli current, thick slits, He/C60/electron | LOW–MEDIUM |
| D2 | Photon delayed erasers (Kim 2000, Walborn 2002, Jacques 2007); massive delayed choice only Wheeler type (Manning 2015); massive erasers not delayed (Dürr 1998, Weisz 2014, Wood 2014); RMP 2016 lists no massive delayed eraser | Spatial-slit massive delayed mark/erase with time-dependent spin rotation; spin-resolved patterns, Bohm re-routing, arrival times | MEDIUM (numerics) / HIGH (as proposal) |
| D3 | Theory dispute: cancellation (Singleton–Vagenas 2013; Macdougall–Singleton 2014; MSV 2015) vs frequency-dependent (Choudhury–Mahajan 2019) vs exists (Wakamatsu 2024/2025; Gao 2025) | Exact TDSE wave packet through double slit with flux switched/ramped at chosen time incl. induced E | MEDIUM–HIGH |
| D4 | Scalar AB done for neutrons (Allman 1992; Badurek 1993) and cold atoms (Shinohara 2002), gravitational (Overstreet 2022); charged pulsed electric AB untested, proposals (Schütz 2015, Bachlechner–Kleban 2020, Chiao 2023, dos Santos 2026) | Design numerics: fringe shift/visibility vs pulse timing, packet length, edge sharpness; pulsed vs static (delay) | LOW (physics) / MEDIUM (design) |
| D5 | Energy-marked paths with time-oscillating readout: neutrons (Badurek 1986; Geppert-Kleinrath 2018), light (Fernandez-Guasti 2022; Legero 2004); diffraction in time (Moshinsky 1952; Szriftgiser 1996; Lindner 2005; Tirole 2023) | Spatial matter-wave double slit with one slit modulated (amplitude+phase), non-adiabatic regime, vs J0 baseline | LOW–MEDIUM |
| D6 | Nonclassical/looped paths give kappa != 0 (Sawant 2014; Magaña-Loaiza 2016; Vieira 2017; de Almeida 2020); finite-barrier screens in Bohm numerics (Das et al. 2025) | Wall tunnelling as third path: amplitude, fringe signature, wall-as-aperture kappa, separated from looped-path kappa; physical mainly for BEC/optical barriers | MEDIUM (narrow) / LOW (concept) |
