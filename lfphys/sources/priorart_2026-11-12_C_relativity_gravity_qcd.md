# Prior-art check C: relativity, strong gravity, QCD (lfphys research demonstrations)

Date of check: 2026-11-12. Method: web search + fetch of arXiv abstract pages, Crossref API
(no mailto), publisher/ADS/project pages. Only abstracts/metadata were read; no full texts
downloaded. "Verified" = the bibliographic data and the stated claim were seen on the fetched page.
"Not verified" = seen only in a search-engine snippet or secondary citation.

Status legend for each claim (per user convention): useful / neutral / weakens / error-in-earlier.

---

## T1. Thomas–Wigner rotation as holonomy

### (a) What has been done

Theory and pedagogy (the area law is classical):

1. P. K. Aravind, "The Wigner angle as an anholonomy in rapidity space", Am. J. Phys. 65, 634–636 (1997),
   DOI 10.1119/1.18620. Verified (metadata) via Crossref:
   https://api.crossref.org/works?query.bibliographic=Aravind+Wigner+angle+anholonomy+rapidity+space
   Content (Wigner angle = area of the velocity-space triangle in the hyperbolic plane) seen only in
   secondary citations (arXiv:1205.1318 snippet; Rhodes & Semon citing it) — content not verified first-hand.
   Status: weakens novelty (area law for planar loops is 1997 textbook-level).
2. J. A. Rhodes, M. D. Semon, "Relativistic velocity space, Wigner rotation, and Thomas precession",
   Am. J. Phys. 72, 943–960 (2004), DOI 10.1119/1.1652040, arXiv:gr-qc/0501070.
   Verified: https://arxiv.org/abs/gr-qc/0501070 and Crossref https://api.crossref.org/works/10.1119/1.1652040
   (abstract: rapidity space gives "a geometric approach to Wigner rotation and Thomas precession").
   Search snippet of the full text (not verified by me first-hand): TWR angle bounded by pi; angle
   proportional to the enclosed rapidity-space area; Thomas precession = sum over a closed planar orbit.
   Status: weakens novelty of planar area law and of "closed loop = holonomy".
3. K. O'Donnell, M. Visser, "Elementary analysis of the special relativistic combination of velocities,
   Wigner rotation, and Thomas precession", Eur. J. Phys. 32, 1033–1047 (2011), DOI 10.1088/0143-0807/32/4/016,
   arXiv:1102.2001. Verified: https://arxiv.org/abs/1102.2001 (the arXiv page journal-ref says "31", the
   DOI says vol. 32). Status: neutral (pedagogy, planar).
4. T. Berry, M. Visser, "Relativistic combination of non-collinear 3-velocities using quaternions",
   arXiv:2002.10659 (2020; journal ref not shown on the page). Verified: https://arxiv.org/abs/2002.10659
   (quaternion "half-velocities", Wigner angle formula, v2 adds composition of three 3-velocities).
   Status: weakens novelty of "non-coplanar composition" as such.
5. V. Palge, C. Pfeifer, "Thomas–Wigner rotation as a holonomy for spin-1/2 particles", arXiv:2310.08121;
   related DOI 10.1103/PhysRevA.109.032206 (Phys. Rev. A 109, 032206 (2024), inferred from DOI).
   Verified: https://arxiv.org/abs/2310.08121 (TWR as holonomy of the mass shell as a Riemannian manifold,
   spin bundle construction). Status: weakens novelty of the "holonomy" framing in general (3-D mass shell,
   i.e. full H^3, not only planes).
6. C. J. McKinstrie, M. V. Kozlov, "How to calculate the Wigner angle", arXiv:2607.21724 (23 Jul 2026).
   Verified: https://arxiv.org/abs/2607.21724 (review of vector/matrix/spinor derivations, 2+1 D; no
   holonomy/area/optimality in abstract). Status: neutral; shows the topic is still active at review level.

Laboratory analogues and proposals:

7. M. Kitano, T. Yabuzaki, "Observation of Lorentz-group Berry phases in polarization optics",
   Phys. Lett. A 142, 321–325 (1989), DOI 10.1016/0375-9601(89)90373-3. Verified (metadata) via Crossref
   https://api.crossref.org/works/10.1016/0375-9601(89)90373-3 . Content (partial polarizers squeeze the
   polarisation-state space; cyclic sequence gives a Lorentz-group geometric phase; measured phase mixes
   geometric and dynamical parts) seen only in a secondary review snippet (arXiv:quant-ph/0402003) — not
   verified first-hand. Status: weakens — an optical experiment on the Lorentz-group (hyperbolic) holonomy
   exists since 1989.
8. R. Y. Chiao, T. F. Jordan, "Lorentz-group Berry phases in squeezed light", Phys. Lett. A 132, 77–81
   (1988), DOI 10.1016/0375-9601(88)90255-1 (Crossref verified, metadata only:
   https://api.crossref.org/works?query.bibliographic=Chiao+Jordan+Lorentz-group+Berry+phases+squeezed+light ).
   Also OSA Annual Meeting 1988 abstract MR17 (Chiao, Kwiat, Vareka, Jordan), DOI 10.1364/oam.1988.mr17.
   Status: weakens (squeezed-light analogue proposed 1988).
9. D. Han, E. E. Hardekopf, Y. S. Kim, "Thomas precession and squeezed states of light", Phys. Rev. A 39,
   1269–1276 (1989), DOI 10.1103/PhysRevA.39.1269 (Crossref verified, metadata:
   https://api.crossref.org/works/10.1103/PhysRevA.39.1269 ). Status: weakens.
10. P. K. Aravind, "Measuring the Wigner angle with a parametric amplifier", in Coherence and Quantum
    Optics VI, pp. 39–42 (1990), DOI 10.1007/978-1-4613-0847-8_9 (Crossref metadata verified). Proposal.
11. D. Han, Y. S. Kim, M. E. Noz, "Wigner rotations and Iwasawa decompositions in polarization optics",
    Phys. Rev. E 60, 1036–1041 (1999), DOI 10.1103/PhysRevE.60.1036, arXiv:quant-ph/0408181.
    Verified: https://arxiv.org/abs/quant-ph/0408181 (rotation + phase-shift + attenuation filters realise
    the 6-parameter Lorentz group on Jones/Stokes vectors; experiments "can be performed in optics labs").
    Proposal. Status: weakens.
12. J. Samuel, S. Sinha, "Thomas rotation and polarised light: a non-Abelian geometric phase in optics",
    arXiv:quant-ph/9705023 (to appear in Pramana per the page). Verified: https://arxiv.org/abs/quant-ph/9705023
    (boost <-> elliptic dichroism analogy, Thomas rotation via Pancharatnam phase on the Poincare sphere).
    Theory. Status: weakens (non-Abelian optical analogue already formulated).
13. J. J. Monzón, L. L. Sánchez-Soto, "A simple optical demonstration of geometric phases from multilayer
    stacks: the Wigner angle as an anholonomy", J. Mod. Opt. 48, 21–34 (2001), DOI 10.1080/09500340117719
    (Crossref metadata verified, no abstract available). Whether it reports a measurement: not verified.
14. V. Palge, J. Dunningham, Y. Hasegawa, C. Pfeifer, "Proposal for an experiment to verify Wigner's
    rotation at non-relativistic speeds with massive spin-1/2 particles", arXiv:1604.03389 (v4, 2 Apr 2025;
    related DOI 10.1016/j.physleta.2025.130490, Phys. Lett. A 2025 inferred from DOI). Verified:
    https://arxiv.org/abs/1604.03389 — a proposal with cold neutrons, no data. Status: useful — shows a
    dedicated direct measurement on massive particles is still regarded as missing.
15. G. Geloni, V. Kocharyan, E. Saldin, "Evidence of Wigner rotation phenomena in the beam splitting
    experiment at the LCLS", arXiv:1607.02928 — WITHDRAWN (replaced by arXiv:1709.09408). Verified:
    https://arxiv.org/abs/1607.02928 . Status: neutral (an indirect, withdrawn claim; do not cite as a
    measurement).

Indirect experimental confirmation of Thomas precession (fine structure factor 1/2; BMT/g-2 spin
precession in storage rings) is standard textbook knowledge; I did not fetch a specific source for it
in this pass (not verified here).

Mathematics needed for the bound:
16. R. Osserman, "The isoperimetric inequality", Bull. AMS 84, 1182–1238 (1978),
    DOI 10.1090/S0002-9904-1978-14553-4 (Crossref verified). Hyperbolic-plane form L^2 >= 4 pi A + A^2
    (curvature -1) is classical; I did not open the text (not verified first-hand which page states it).
17. J. Choe, R. Gulliver, "Isoperimetric inequalities on minimal submanifolds of space forms",
    Manuscripta Math. 77, 169–189 (1992), DOI 10.1007/BF02567052; and "The sharp isoperimetric inequality
    for minimal surfaces with radially connected boundary in hyperbolic space", Invent. Math. 109, 495–503
    (1992), DOI 10.1007/BF01232035 (both Crossref metadata verified; abstracts not accessible — exact
    hypotheses NOT verified). The second title shows that the SHARP inequality in H^3 was proved under a
    boundary hypothesis ("radially connected"), so the general non-planar case may hinge on it.

Searches for "isoperimetric" together with "Thomas precession"/"Wigner rotation", and for rapidity- or
fuel-budget-limited manoeuvres maximising the Wigner angle, returned nothing relevant (two extended
searches, plus one on relativistic rocket / proper acceleration). Absence of hits is weak evidence only.

### (b) What remains open (narrow, computable)

- (ii) Fuel bound, planar: for a closed planar velocity loop with rapidity length L = (1/c) ∫ a dτ (for a
  rocket, L = sum of burn rapidities = (v_e/c) ln(m0/m1) per burn), the Thomas angle obeys
  Theta <= sqrt(L^2 + 4 pi^2) - 2 pi, with equality only for the constant-speed circular loop, where it
  equals 2 pi (gamma - 1) with gamma = sqrt(1 + (L/2pi)^2). This follows in two lines from Aravind's area
  law + the hyperbolic isoperimetric inequality; I found NO paper stating it in "rotation per fuel" form.
  It is elementary, so it is a demonstration / AJP-note, not a research result.
- (i)+(ii) Non-planar loops: does any 3-D manoeuvre with the same rapidity length beat the planar circle?
  Expected answer "no": holonomy angle <= integral of |curvature| over a spanning surface = area of the
  least-area spanning surface <= sqrt(L^2 + 4 pi^2) - 2 pi, IF the sharp isoperimetric inequality holds for
  that minimal disc in H^3 (Choe–Gulliver proved it for "radially connected" boundaries; general status
  not verified). The engine can test it numerically: random and optimised non-planar loops (e.g. Viviani-
  type, saddle, tennis-ball curves on a rapidity sphere), report holonomy axis/angle vs L, and plot against
  the planar bound. Also: for non-planar loops the axis is not fixed by the loop plane — map how the axis
  tilts with the loop's "vector area" (first-order) and where the non-Abelian correction becomes visible.
- (iii) Laboratory: an optical measurement that checks the AREA LAW quantitatively (angle vs hyperbolic
  area for several loop shapes with equal perimeter, i.e. the isoperimetric ordering) — not found. Kitano &
  Yabuzaki 1989 observed a Lorentz-group Berry phase but the content (loop shapes, area dependence) was not
  verified. The engine could supply the design table: sequence of partial polarisers / dichroic elements
  (Han–Kim–Noz mapping) for a circle vs square vs triangle of equal hyperbolic perimeter, with predicted
  phases and required extinction ratios.

### (c) Novelty rating

- Area law, holonomy framing, non-coplanar composition: LOW (Aravind 1997; Rhodes–Semon 2004;
  Berry–Visser 2020; Palge–Pfeifer 2024).
- Fuel/rapidity-budget isoperimetric bound (planar): LOW-to-MEDIUM — not found in print, but a two-line
  corollary of known results; good AJP/EJP-note level, not Q1.
- Non-planar bound + numerical evidence + its link to the open sharp isoperimetric inequality for minimal
  surfaces in H^3: MEDIUM as math-phys curiosity; the physics content is still textbook.
- Optical area-law/isoperimetric test design: MEDIUM-LOW (analogue experiments exist since 1988–1989;
  a shape-resolved test was not found).

### (d) Value

Teaches that a gyroscope's net rotation after a closed manoeuvre is a curvature integral and that the
circle is the most "rotation-efficient" use of delta-v; gives a falsifiable optical design (equal
perimeter, different shapes -> ordered phases). Informs: polarisation-optics / squeezed-light analogue
experiments; neutron Wigner-rotation proposal (Palge et al.) as a source of loop designs.

### (e) Not verified

Aravind 1997 and Kitano–Yabuzaki 1989 contents (metadata only); Choe–Gulliver hypotheses; whether
Monzón & Sánchez-Soto 2001 includes a measurement; whether any spin-qubit/NMR/trapped-ion simulation of
Thomas precession exists (one targeted search found none); indirect g-2 / fine-structure confirmations
(not fetched in this pass).

---

## T2. Non-Kerr shadow tests with photon rings (Johannsen metric, n = 1, 2, Lyapunov exponent)

### (a) What has been done

Metric and early photon-ring work:
1. T. Johannsen, "Regular black hole metric with three constants of motion", Phys. Rev. D 88, 044002 (2013),
   DOI 10.1103/PhysRevD.88.044002. Crossref metadata verified:
   https://api.crossref.org/works?query.bibliographic=Johannsen+Regular+black+hole+metric+with+three+constants+of+motion
2. T. Johannsen, "Photon rings around Kerr and Kerr-like black holes", ApJ 777, 170 (2013),
   DOI 10.1088/0004-637X/777/2/170 (Crossref metadata verified; content not read). Status: weakens —
   the shadow edge ("photon ring" in the 2013 sense = critical curve) of Johannsen-type metrics vs spin/
   inclination was computed already in 2013.

EHT bounds:
3. D. Psaltis et al. (EHT Collaboration), "Gravitational test beyond the first post-Newtonian order with the
   shadow of the M87 black hole", Phys. Rev. Lett. 125, 141104 (2020), DOI 10.1103/PhysRevLett.125.141104,
   arXiv:2010.01055. Verified: https://arxiv.org/abs/2010.01055 (regular parametric non-Kerr metrics;
   shadow size constrains 2PN-and-higher deviation parameters). Exact parametrisation and numbers not on
   the abstract page — not verified.
4. EHT Collaboration, "First Sagittarius A* Event Horizon Telescope Results. VI. Testing the black hole
   metric", ApJL 930, L17 (2022), DOI 10.3847/2041-8213/ac6756, arXiv:2311.09484. Verified:
   https://arxiv.org/abs/2311.09484 (image size within ~10% of Kerr; constraints on parametrically
   non-Kerr metrics and charges; thermal surface excluded). Whether Johannsen is among them: not verified
   on the abstract page.

Photon-ring (subring) theory, Kerr:
5. M. D. Johnson et al., "Universal interferometric signatures of a black hole's photon ring", Sci. Adv. 6,
   eaaz1310 (2020), DOI 10.1126/sciadv.aaz1310, arXiv:1907.04329. Verified: https://arxiv.org/abs/1907.04329
   (self-similar subrings, exponential demagnification, universal long-baseline signatures).
6. S. E. Gralla, A. Lupsasca, D. P. Marrone, "The shape of the black hole photon ring: a precise test of
   strong-field general relativity", Phys. Rev. D 102, 124004 (2020), DOI 10.1103/PhysRevD.102.124004
   (Crossref metadata verified). Companion: Gralla & Lupsasca, "Observable shape of black hole photon rings",
   PRD 102, 124003 (2020) (Crossref). Lensing exponents gamma, delta, tau defined in "Lensing by Kerr black
   holes" arXiv:1910.12873 (seen only in search snippet — not fetched; not verified).
7. H. Paugnat, A. Lupsasca, F. Vincent, M. Wielgus, "Photon ring test of the Kerr hypothesis: variation in
   the ring shape", A&A 668, A11 (2022), DOI 10.1051/0004-6361/202244216, arXiv:2206.02781. Verified:
   https://arxiv.org/abs/2206.02781 (GLM shape test robust at low inclination with right baselines; ring
   width and its angular variation are the main obstacle; new effects at high inclination).
8. S. Hadar, M. D. Johnson, A. Lupsasca, G. N. Wong, "Photon ring autocorrelations", Phys. Rev. D 103,
   104038 (2021), DOI 10.1103/PhysRevD.103.104038 (Crossref metadata verified). Light-curve echoes:
   Gammie, Lupsasca et al. arXiv:2406.04176 (absence of echoes in Sgr A* light curves explained) — seen
   only in a search snippet, not fetched (not verified).

Photon rings beyond Kerr:
9. M. Wielgus, "Photon rings of spherically symmetric black holes and robust tests of non-Kerr metrics",
   Phys. Rev. D 104, 124058 (2021), DOI 10.1103/PhysRevD.104.124058, arXiv:2109.10840 (Crossref verified;
   snippet: Lyapunov exponent controls relative subring flux, Schwarzschild gamma = pi — snippet only).
10. D. Ayzenberg, "Testing gravity with black hole shadow subrings", Class. Quantum Grav. 39, 105009 (2022),
    DOI 10.1088/1361-6382/ac655d, arXiv:2202.02355. Verified: https://arxiv.org/abs/2202.02355 (two
    parametrised non-Kerr metrics, disk illumination, full shadow and individual subrings; Earth VLBI
    struggles, space VLBI could test Kerr). Names of the two metrics: not on the abstract page.
11. S. Staelens, D. R. Mayerson, F. Bacchini, B. Ripperda, L. Küchler, "Black hole photon rings beyond general
    relativity", Phys. Rev. D 107, 124026 (2023), arXiv:2303.02111. Verified: https://arxiv.org/abs/2303.02111
    — JOHANNSEN, Rasheed–Larsen and Manko–Novikov; photon-ring SHAPE and LYAPUNOV EXPONENT; shape nearly
    universal (Kerr-like) at low inclination, measurable shape differences need large deviations AND large
    inclination; Lyapunov exponent varies more clearly. A search snippet (not verified first-hand) attributes
    to this line of work: for Johannsen at theta_0 ~ 17 deg, alpha_22 >~ 2.5 needed for the n=2 shape to
    deviate noticeably from the circlipse. Status: WEAKENS strongly — this is essentially the proposed T2.
12. A. Cárdenas-Avendaño, A. Held, "A lensing-band approach to spacetime constraints", Phys. Rev. D 109,
    064052 (2024), arXiv:2312.06590. Verified: https://arxiv.org/abs/2312.06590 (lensing bands around the
    critical curve; n = 2 first indirect image; parametrised case study, not named on the page).
13. R. K. Walia, P. Kocherlakota, D. O. Chang, K. Salehi, "Spacetime measurements with the photon ring",
    Phys. Rev. D 111, 104074 (2025), arXiv:2411.15119. Verified: https://arxiv.org/abs/2411.15119 —
    Kerr–Newman, Kerr–Sen, Kerr–Bardeen, Kerr–Hayward; gamma (demagnification), tau (time delay), delta
    (rotation) vs spin and inclination; Kerr variation over all spins/inclinations <~20% (gamma), <~10% (tau),
    <~60% (delta) vs <~8% for shadow radius. (A search summary claimed this paper uses Johannsen–Psaltis;
    the fetched abstract does NOT say so — treat that claim as unverified.)
14. K. Salehi, R. K. Walia, D. Chang, P. Kocherlakota, "Influence of observer inclination and spacetime
    structure on photon ring observables", arXiv:2411.15310 (Nov 2024; no journal ref on page). Verified:
    https://arxiv.org/abs/2411.15310 (non-perturbative, non-parametric; Lyapunov exponent, time delay,
    azimuthal shift, shadow size; focus on polar observers / M87*).
15. J. Ben Achour, E. Gourgoulhon, H. Roussille, "Black hole photon ring beyond General Relativity: an
    integrable parametrization", JCAP 10 (2025) 012, DOI 10.1088/1475-7516/2025/10/012, arXiv:2506.09882.
    Verified: https://arxiv.org/abs/2506.09882 ("Kerr off shell" family with Killing tensor, Petrov D;
    closed-form critical curve; the GLM circlipse fits Kerr and modified BHs with high DEGENERACY — shape
    tests need independent M and a). Status: weakens shape-only tests.
16. H.-P. Yan, X.-Q. Li, X.-J. Yue, "Deviations from Kerr: polar critical curves and photon rings in a class
    of separable spacetimes", arXiv:2609.01290 (1 Sep 2026). Verified: https://arxiv.org/abs/2609.01290 —
    exact polar critical radius, Lyapunov exponent, time delay, rotation parameter for a general separable
    class (Johannsen-type metrics belong to such classes, but Johannsen is not named on the page);
    observables probe only local deformation values and derivatives at the critical orbit. POLAR ONLY.

BHEX status (as of 2026-11):
17. A. Lupsasca et al., "The Black Hole Explorer: photon ring science, detection and shape measurement",
    Proc. SPIE 13092, 130926Q (2024), DOI 10.1117/12.3019437, arXiv:2406.09498. Verified:
    https://arxiv.org/abs/2406.09498 (100–300 GHz, ~30,000 km orbit; photon-ring shape test of Kerr, M and a).
18. MIT Haystack news, 16 Apr 2026, https://www.haystack.mit.edu/news/bhex-test-001/ (verified): BHEX still
    in development; Dec 2025 six-day subsystem prototype test nominal; to be proposed as a NASA SMEX in
    mid-2026; no launch date given.
19. K. Akiyama et al., "Black Hole Explorer mission development in Japan", arXiv:2608.00890 (1 Aug 2026).
    Verified: https://arxiv.org/abs/2608.00890 ("mission concept"; ISAS/JAXA working group doing Pre-Phase A).
20. J. R. Farah, D. C. M. Palumbo, M. D. Johnson, D. O. Chang, "Spin inference with the Black Hole Explorer.
    I. Fisher information matrix forecast", arXiv:2608.23672 (24 Aug 2026). Verified:
    https://arxiv.org/abs/2608.23672 (spin sigma well below 0.1 after 30 orbits for M87* and Sgr A*; Kerr only).
21. Phys.org / Universe Today, 15 Jul 2026, https://phys.org/news/2026-07-black-hole-ultimate-space.html
    (verified): BHEX "currently on the drawing board as a NASA Small Explorer mission", "slated for the coming
    decade"; ~5 microarcsec needed to resolve the ring shape.
   => As of Nov 2026 BHEX is a proposed SMEX concept; I found NO announcement of NASA selection (not
   verified either way). A search snippet mentioned an A&A 2026 paper with BHEX precisions
   sigma_rhs ~ 0.1 M, sigma_dPA ~ 1.5 deg (https://www.aanda.org/articles/aa/pdf/forth/aa62651-26.pdf) —
   not fetched, not verified.

### (b) What remains open (narrow)

The core idea "n = 1, 2 ring shape + Lyapunov exponent in the Johannsen metric vs spin and inclination"
is DONE (Staelens et al. 2023; plus Johannsen 2013 for the critical curve). Possible narrow gaps:
- Inclined-observer (not polar) maps of the full triple (gamma, delta, tau) for the JOHANNSEN deviation
  parameters (alpha13, alpha22, alpha52, eps3), jointly with shadow size, at the M87* inclination (~17 deg)
  and Sgr A* plausible inclinations; then a Fisher-style degeneracy check (spin vs alpha13/alpha22) using
  BHEX-like precisions from Farah et al. 2026 / Lupsasca et al. 2024. Walia et al. 2025 did this kind of
  analysis for charge-type metrics; Yan et al. 2026 did polar-only for a separable class; Staelens et al.
  did gamma + shape. A Johannsen inclined (gamma, delta, tau) + Fisher degeneracy table was not found.
- Whether the Ben Achour et al. circlipse degeneracy is broken in the Johannsen family by gamma or delta at
  M87* inclination — a concrete yes/no with numbers.
- Within the engine, a reproducibility benchmark: reproduce Staelens et al. Johannsen gamma and shape to
  stated precision — useful as validation, not novel.

### (c) Novelty rating

LOW for the stated set-up (Johannsen n = 1, 2 shape + Lyapunov exponent: done 2023). MEDIUM-LOW for the
inclined-observer (gamma, delta, tau) + Fisher degeneracy table in Johannsen: crowded field (EHT/BHEX
theory groups, Kocherlakota/Walia, Lupsasca, Wielgus, Mayerson), likely to be done or scooped quickly;
not a Q1-strength stand-alone result for a teaching engine.

### (d) Value

Teaches why the Lyapunov exponent and rotation parameter carry more non-Kerr information than ring shape;
informs BHEX (if selected) target precision for non-Kerr tests. Main value for lfphys: a validated
reproduction of published numbers (benchmark), rather than a new claim.

### (e) Not verified

Exact Johannsen numbers in Staelens et al. (snippet only); which metrics Psaltis 2020 / EHT Sgr A* VI /
Ayzenberg 2022 used; Johannsen 2013 ApJ content; arXiv:1910.12873 content; A&A 2026 BHEX precision
numbers; NASA SMEX selection outcome for BHEX.

---

## T3. QCD running scenarios (alpha_s(M_Z) "what if", quarkonium in potential models, Lambda_QCD variation)

### (a) What has been done

State of the art for running (the engine's 4-loop is one order behind):
1. P. A. Baikov, K. G. Chetyrkin, J. H. Kühn, "Five-loop running of the QCD coupling constant", Phys. Rev.
   Lett. 118, 082002 (2017), DOI 10.1103/PhysRevLett.118.082002 (Crossref metadata verified:
   https://api.crossref.org/works?query.bibliographic=Baikov+Chetyrkin+Kuhn+Five-loop+running+of+the+QCD+coupling+constant ).
   Status: weakens — 5-loop beta function is known since 2017.
2. F. Herren, M. Steinhauser, "Version 3 of RunDec and CRunDec", Comput. Phys. Commun. 224, 333–345 (2018),
   DOI 10.1016/j.cpc.2017.11.014 (Crossref verified). Status: weakens — public, standard tools already do
   multi-loop running with flavour thresholds (decoupling), so an engine reproduction is a validation exercise.

Static potential vs lattice, alpha_s from the static energy:
3. A. Bazavov, N. Brambilla, X. Garcia i Tormo, P. Petreczky, J. Soto, A. Vairo, J. H. Weber, "Determination
   of the QCD coupling from the static energy and the free energy", Phys. Rev. D 100, 114511 (2019),
   DOI 10.1103/PhysRevD.100.114511, arXiv:1907.11747. Verified: https://arxiv.org/abs/1907.11747
   (static energy at three-loop accuracy vs lattice down to r ~ 0.024 fm: alpha_s(M_Z) = 0.11660
   +0.00110/-0.00056; free energy: 0.11638 +0.00095/-0.00087).
4. H. Takaura, T. Kaneko, Y. Kiyo, Y. Sumino, "Determination of alpha_s from static QCD potential with
   renormalon subtraction", Phys. Lett. B (2019), DOI 10.1016/j.physletb.2018.12.060, arXiv:1808.01632.
   Verified: https://arxiv.org/abs/1808.01632 (OPE with renormalon subtraction explains lattice data up to
   Lambda r <~ 0.8; alpha_s(M_Z) = 0.1179 +0.0015/-0.0014).
5. Y. Sumino, "Quarkonium spectroscopy and perturbative QCD: a new perspective", arXiv:hep-ph/0105240 (2001,
   APPI talk). Verified: https://arxiv.org/abs/hep-ph/0105240 (pNRQCD-based bound-state theory reproduces the
   gross bottomonium spectrum; masses dominated by quark self-energies; connection to phenomenological
   potential models). Related: "A connection between the perturbative QCD potential and phenomenological
   potentials", arXiv:hep-ph/0104259 (search snippet only — not fetched, authors not verified).
   Status: weakens — "running-coupling potential vs Cornell vs lattice" is a 2001-era resolved topic.

Varying / anthropic Lambda_QCD and quark masses:
6. C. J. Hogan, "Why the universe is just so", Rev. Mod. Phys. 72, 1149–1161 (2000), DOI
   10.1103/RevModPhys.72.1149 (Crossref verified; content not read).
7. R. L. Jaffe, A. Jenkins, I. Kimchi, "Quark masses: an environmental impact statement", Phys. Rev. D 79,
   065014 (2009), arXiv:0809.1647 (verified via search result listing ADS 2009PhRvD..79f5014J and arXiv;
   abstract-level content: vary quark masses with fixed electron mass and lightest-baryon-multiplet mass;
   "congenial" worlds with stable Z = 1, 6, 8 nuclei). Abstract page itself not fetched — partially verified.
8. E. Epelbaum, H. Krebs, T. A. Lähde, D. Lee, U.-G. Meißner, "Viability of carbon-based life as a function
   of the light quark mass", Phys. Rev. Lett. 110, 112502 (2013), DOI 10.1103/PhysRevLett.110.112502,
   arXiv:1303.4856 (Crossref verified; content from search summary only: lattice EFT, Hoyle state vs m_q,
   ~2–3% window — not verified first-hand).
9. J. MacDonald, D. J. Mullan, "Big bang nucleosynthesis: the strong nuclear force meets the weak anthropic
   principle", Phys. Rev. D 80, 043507 (2009), arXiv:0904.1807 (search summary: substantial hydrogen
   survives unless the strong coupling increases by > ~50%; not fetched — not verified first-hand).
10. V. V. Flambaum, A. J. Mansour, "Constraints on the variation of the QCD interaction scale Lambda_QCD",
    JHEP 11 (2025) 086, DOI 10.1007/JHEP11(2025)086, arXiv:2508.07266. Verified:
    https://arxiv.org/abs/2508.07266 (clocks: dLambda/dt/Lambda = (3.2 +- 3.5)e-17 /yr; Oklo
    |dLambda/Lambda| < 2e-9 over 1.8 Gyr; 229Th nuclear clock ~1e4 more sensitive). Earlier review:
    Flambaum, arXiv:0705.3704 (snippet only).

### (b) What remains open (narrow)

Honest answer: nothing research-grade that a 4-loop running + Cornell-type engine can address.
- Running with thresholds: textbook; 5-loop beta + RunDec exist.
- Cornell (or Richardson/Buchmüller–Tye-type) quarkonium with running coupling vs lattice static energy:
  done for two decades (pNRQCD, renormalon-subtracted potentials, TUMQCD); the phenomenological Cornell
  model has uncontrolled systematics larger than the alpha_s sensitivity being probed.
- "What if alpha_s(M_Z) were different": physically, changing alpha_s(M_Z) at fixed quark masses mostly
  rescales Lambda_QCD, i.e. all hadronic scales; the physical content lives in m_q/Lambda_QCD, which is what
  the anthropic (Jaffe et al., Epelbaum et al.) and varying-constant (Flambaum) literature already uses —
  with nuclear models / lattice EFT, not quarkonium potentials.
- Possible teaching demonstration (not research): sensitivity table d(M(2S)-M(1S))/d alpha_s(M_Z) for
  charmonium/bottomonium in a Cornell + running-coupling model, contrasted with the lattice static energy
  of Bazavov et al. 2019 and the published alpha_s extractions — showing why potential models are NOT
  used to extract alpha_s.

### (c) Novelty rating

LOW — textbook / long-resolved; the engine is one loop behind the state of the art and its potential model
is phenomenological. Not research-grade.

### (d) Value

Pedagogical only: asymptotic freedom, thresholds, why heavy-quarkonium level spacings are nearly
mass-independent (Cornell quirk), why lattice + pNRQCD replaced potential models for alpha_s.

### (e) Not verified

Content of Hogan 2000; Epelbaum et al. 2013 and MacDonald–Mullan 2009 numerical windows (search
summaries only); authorship of hep-ph/0104259; current PDG alpha_s world average (not fetched).

---

## T4. PN binaries: periastron advance vs PN order, breakdown of the truncated series (brief)

### (a) What has been done

1. L. Blanchet, "Post-Newtonian theory for gravitational waves", Living Rev. Relativ. 27, 4 (2024),
   arXiv:1310.1528 (v6, 12 Jul 2024, "matches version published in Living Review in Relativity 27, 4 (2024)").
   Verified: https://arxiv.org/abs/1310.1528 .
2. L. Blanchet, G. Faye, Q. Henry, F. Larrouturou, D. Trestini, "Gravitational-wave flux and quadrupole modes
   from quasicircular nonspinning compact binaries to the fourth post-Newtonian order", Phys. Rev. D 108,
   064041 (2023), DOI 10.1103/PhysRevD.108.064041 (Crossref metadata verified). Status: the engine's
   3.5PN + quadrupole waves is below the 4PN/4.5PN state of the art.
3. R.-M. Memmesheimer, A. Gopakumar, G. Schäfer, "Third post-Newtonian accurate generalized quasi-Keplerian
   parametrization for compact binaries in eccentric orbits", Phys. Rev. D 70, 104011 (2004),
   DOI 10.1103/PhysRevD.70.104011 (Crossref verified). Periastron advance vs PN order for eccentric orbits
   is part of this standard machinery.
4. A. Le Tiec, A. H. Mroué, L. Barack, A. Buonanno, H. P. Pfeiffer, N. Sago, A. Taracchini, "Periastron
   advance in black-hole binaries", Phys. Rev. Lett. 107, 141101 (2011), DOI 10.1103/PhysRevLett.107.141101,
   arXiv:1106.3278 (verified via search listing of the APS accepted manuscript and arXiv; abstract content:
   PN, EOB, self-force vs SpEC NR for mass ratios 1/8–1). Spinning follow-up: arXiv:1309.0541 (Hinderer,
   Mroué et al.; snippet only, not verified).
5. M. Boyle, D. A. Brown, L. E. Kidder, A. H. Mroué, H. P. Pfeiffer, M. A. Scheel et al., "High-accuracy
   comparison of numerical relativity simulations with post-Newtonian expansions", Phys. Rev. D 76, 124038
   (2007), DOI 10.1103/PhysRevD.76.124038 (Crossref verified).
6. N. Yunes, E. Berti, "Accuracy of the post-Newtonian approximation: optimal asymptotic expansion for
   quasi-circular, extreme-mass ratio inspirals", Phys. Rev. D 77, 124006 (2008); Erratum 83, 109901 (2011),
   arXiv:0803.1853. Verified: https://arxiv.org/abs/0803.1853 (region of validity largest at 3PN; beyond
   3PN the series appears to diverge in the EMR limit, likely due to logs). Follow-up: Zhang, Yunes, Berti,
   PRD 84, 024029 (2011), Kerr case (Crossref verified).

### (b) What remains open (narrow)

"Breakdown radius of the truncated PN series" and "periastron advance vs PN order" are studied in depth
(Yunes–Berti; Boyle et al.; Le Tiec et al.). For a 3.5PN engine there is no research gap; at most a
teaching plot: successive-order periastron advance and flux vs x = (M omega)^(2/3) with the 3PN optimum,
compared with the published NR/self-force numbers.

### (c) Novelty: LOW — standard GW-source modelling, the engine is below state of the art (4–4.5PN, EOB, NR).

### (d) Value: pedagogical (asymptotic series, optimal truncation, why EOB/NR are needed near merger).

### (e) Not verified: Le Tiec et al. numbers; the claim that the PN radius of convergence is set by the
light ring (secondary snippet only); eccentric PN vs NR comparisons beyond 2011 not searched.

---

## T5. Terrell–Penrose rotation: experimental demonstration (brief)

### (a) What has been done

1. D. Hornof, V. Helm, E. de Dios Rodriguez, T. Juffmann, P. Haslinger, P. Schattschneider, "A snapshot of
   relativistic motion: visualizing the Terrell-Penrose effect", Commun. Phys. 8, 161 (2025),
   DOI 10.1038/s42005-025-02003-6 (Crossref verified: https://api.crossref.org/works/10.1038/s42005-025-02003-6 ),
   preprint arXiv:2409.04296 "A snapshot of relativistic motion: visualizing the Terrell effect" (6 Sep 2024).
   Verified: https://arxiv.org/abs/2409.04296 — ultrafast pulsed laser + gated intensified camera (gates down
   to 300 ps) give a virtual speed of light < 2 m/s; light reflected from deliberately Lorentz-contracted
   objects (sphere, cube) is used to synthesise snapshots; claimed first experimental visualisation; shows the
   predicted apparent rotation/distortion. Caveat: it is an analogue (virtual c, contracted props), not
   objects physically moving near c.
   Secondary: TU Wien press release https://www.tuwien.at/en/all-news/news/spezielle-relativitaetstheorie-sichtbar-gemacht
   (in search listing; not fetched).

### (b) Open: the 1959 prediction is no longer experimentally open (at analogue level). Remaining narrow
items are engineering/pedagogy (e.g. other shapes, spectral/brightness (Doppler + aberration) effects in the
same set-up) — not searched further.

### (c) Novelty: LOW — demonstrated 2024/2025.

### (d) Value: an lfphys visualisation can reproduce the Hornof et al. sphere/cube frames as a validated
teaching benchmark and cite it.

### (e) Not verified: whether Hornof et al. include Doppler/searchlight brightness effects (not on abstract page).

---

## Summary table

| Candidate | Done (key) | Narrow open item | Novelty |
|---|---|---|---|
| T1 Thomas–Wigner holonomy | Area law (Aravind 1997; Rhodes–Semon 2004), holonomy on mass shell (Palge–Pfeifer 2024), non-coplanar quaternion composition (Berry–Visser 2020); optical Lorentz-group Berry phase observed (Kitano–Yabuzaki 1989); many proposals (Chiao–Jordan 1988, Han–Kim–Noz 1999, Palge et al. 2025 neutrons) | Fuel bound Theta <= sqrt(L^2+4pi^2) - 2pi (circle optimal) not found in print; non-planar extension numerically + link to sharp minimal-surface isoperimetric inequality in H^3; shape-resolved optical area-law test design | low (area law) / low-medium (fuel bound) / medium (non-planar bound as math-phys note) |
| T2 Johannsen photon rings | Johannsen 2013; Staelens et al. 2023 (Johannsen shape + Lyapunov); Walia et al. 2025 (gamma, tau, delta for charged metrics); Ben Achour et al. 2025 (shape degeneracy); Yan et al. 2026 (polar, separable class) | Inclined-observer (gamma, delta, tau) + Fisher degeneracy table for Johannsen parameters at BHEX precision | low / medium-low |
| T3 QCD running + Cornell | 5-loop beta (2017), RunDec 3 (2018), static energy vs lattice (TUMQCD 2019; Takaura et al. 2019); anthropic/varying-constant literature (Jaffe et al. 2009; Epelbaum et al. 2013; Flambaum–Mansour 2025) | none research-grade | low |
| T4 PN breakdown | Blanchet LRR 2024; Yunes–Berti 2008 (3PN optimum); Boyle et al. 2007; Le Tiec et al. 2011 | teaching plot only | low |
| T5 Terrell–Penrose | Hornof et al. Commun. Phys. 8, 161 (2025) | none | low |
