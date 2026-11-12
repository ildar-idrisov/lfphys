# lfphys reference-number verification — 2026-10-23

Purpose: check every reference number used by `lfphys` against a primary or authoritative source text that was actually fetched in this session.
Rules: each value is quoted verbatim from the fetched text with its URL. If a source could not be reached, this is stated; nothing is filled in from memory as "verified".
Status codes: VERIFIED (quoted from the source) / NOT FOUND (source not reachable or value not present in it) / DIFFERS (source differs from the expected value; both given).
Access date for all items: 2026-10-23 unless stated otherwise.

---

## 1. Mercury orbital elements (NASA Mercury Fact Sheet)

Source: D. R. Williams (curator), "Mercury Fact Sheet", NASA Space Science Data Coordinated Archive (NSSDCA), NASA Goddard Space Flight Center, page footer "Last Updated: 11 January 2024, DRW".
URL: https://nssdc.gsfc.nasa.gov/planetary/factsheet/mercuryfact.html — accessed 2026-10-23 (raw HTML downloaded with curl, tags stripped).

Verbatim rows ("Orbital parameters" table; columns Mercury / Earth / Ratio):
- "Semimajor axis (10^6 km)  57.909  149.598  0.387"
- "Sidereal orbit period (days)  87.969  365.256  0.241"
- "Tropical orbit period (days)  87.968  365.242  0.241"
- "Perihelion (10^6 km)  46.000  147.095  0.313"
- "Aphelion (10^6 km)  69.818  152.100  0.459"
- "Orbit inclination (deg)  7.004  0.000"
- "Orbit eccentricity  0.2056  0.0167  12.311"

Verbatim rows ("Mercury Mean Orbital Elements (J2000)"):
- "Semimajor axis (AU)                  0.38709893"
- "Orbital eccentricity                 0.20563069"
- "Orbital inclination (deg)            7.00487"
- "Longitude of perihelion (deg)       77.45645"

Bulk parameter of related use: "GM (x 10^6 km^3/s^2)  0.022032" (Mercury).

Uncertainty: none stated on the page (values are given to the digits shown).
Comparison with expected: 57.909e6 km — matches; 0.2056 — matches (J2000 mean element 0.20563069); 87.969 d — matches.
Status: **VERIFIED**

---

## 2. GR perihelion advance of Mercury, 42.98 arcsec per century

Source: C. M. Will, "The Confrontation between General Relativity and Experiment", Living Reviews in Relativity 17, 4 (2014), DOI 10.12942/lrr-2014-4; arXiv:1403.7377v1 [gr-qc] 28 Mar 2014 (only one arXiv version listed on the abs page).
URLs: https://arxiv.org/abs/1403.7377 (PDF https://arxiv.org/pdf/1403.7377, downloaded, text extracted with pdftotext); Crossref record https://api.crossref.org/works/10.12942/lrr-2014-4 (title "The Confrontation between General Relativity and Experiment", Living Reviews in Relativity, vol 17, issue 1, article-number 4). Accessed 2026-10-23.

Location: Section 4.2 "The perihelion shift of Mercury" (arXiv v1, pp. 44–45), Eq. (65).

Verbatim (arXiv v1 text):
- "The modern value for this discrepancy is 43 arcseconds per century."
- "Substituting standard orbital elements and physical constants for Mercury and the Sun we obtain the rate of perihelion shift ω̃̇, in seconds of arc per century,
  ω̃̇ = 42.″98 [ (1/3)(2 + 2γ − β) + 3 × 10^−4 (J2 / 10^−7) ] .   (65)"
  (pdftotext rendering: "˙ω̃ = 42.′′ 98 1 (2 + 2γ − β) + 3 × 10−4 J2 . (65) / 3 10−7"; the 1/3 and J2/10^−7 are stacked fractions.)
- Context for J2: "the latest inversions of helioseismology data give J2 = (2.2 ± 0.1) × 10^−7 [252, 15]".
- Eq. (64) (per-orbit advance): "∆ω̃ = (6πm/p) [ (1/3)(2 + 2γ − β) + (1/6)(2α1 − α2 + α3 + 2ζ2)η + J2R²/(2mp) ]" with "p ≡ a(1 − e²) is the semi-latus rectum".
- Same section: "Adopting the Cassini bound on γ a priori, these analyses yield a bound on β given by β − 1 = (−4.1 ± 7.8) × 10^−5."

Note: in GR (γ = β = 1) the bracket in Eq. (65) is 1 + 3×10^−4 (J2/10^−7); the pure-PPN part is 42.98″/century; the solar J2 = 2.2×10^−7 term adds about 42.98 × 6.6×10^−4 ≈ 0.03″/century (my arithmetic, not a quoted number).
Uncertainty: none stated for 42.98″ in Will 2014 (it is a computed coefficient, not a measurement).
Status: **VERIFIED** (Will 2014, Sec. 4.2, Eq. 65)

---

## 3. Cassini: γ − 1 = (2.1 ± 2.3) × 10^−5 (Bertotti, Iess & Tortora 2003)

Citation (Crossref, https://api.crossref.org/works/10.1038/nature01997):
"A test of general relativity using radio links with the Cassini spacecraft", Bertotti, B.; Iess, L.; Tortora, P. — Nature, vol 425, issue 6956, pages 374-376, published-print 2003-09. DOI 10.1038/nature01997.

Value, verbatim from the Nature abstract (https://www.nature.com/articles/nature01997, accessed 2026-10-23):
"Here we report a measurement of the frequency shift of radio photons to and from the Cassini spacecraft as they passed near the Sun. Our result, γ = 1 + (2.1 ± 2.3) × 10-5, agrees with the predictions of standard general relativity with a sensitivity that approaches the level at which, theoretically, deviations are expected in some cosmological models".

Same value in Will 2014 (arXiv:1403.7377v1), Sec. 4.1.2 "The time delay of light", p. 43:
"A significant improvement was reported in 2003 from Doppler tracking of the Cassini spacecraft while it was on its way to Saturn [38], with a result γ − 1 = (2.1 ± 2.3) × 10^−5. This was made possible by the ability to do Doppler measurements using both X-band (7175 MHz) and Ka-band (34316 MHz) radar ... with the spacecraft at 8.43 astronomical units from the Sun, the distance of closest approach of the radar signals to the Sun was only 1.6 R⊙."
"From the results of the Cassini experiment, we can conclude that the coefficient ½(1 + γ) must be within at most 0.0012 percent of unity. Scalar-tensor theories must have ω > 40,000 to be compatible with this constraint."
Will 2014 reference [38]: "Bertotti, B., Iess, L. and Tortora, P., “A test of general relativity using radio links with the Cassini spacecraft”, Nature, 425, 374–376 (2003)."
Will 2014 Table 4: "γ−1 | time delay | 2.3 × 10^−5 | Cassini tracking".

Remark (wording only): the observable was the frequency shift (time derivative of the Shapiro delay), not the delay itself; Will files it under the time-delay test. Calling it "the Shapiro-delay result" is standard but strictly it is a Doppler (frequency-shift) measurement.
Uncertainty: ±2.3 × 10^−5 (1σ as stated by authors; the abstract does not specify the confidence level).
Status: **VERIFIED** (citation and value)

---

## 4. VLBI light-deflection bound on γ in Will 2014

Source: Will 2014 (see item 2), Sec. 4.1.1 "The deflection of light", pp. 40–41, and Table 4.

Verbatim:
- "A 1995 VLBI measurement using 3C273 and 3C279 yielded γ − 1 = (−8 ± 34) × 10^−4 [224], while a 2009 measurement using the VLBA targeting the same two quasars plus two other nearby radio sources yielded γ − 1 = (−2 ± 3) × 10^−4 [147]."
- "A 2004 analysis of almost 2 million VLBI observations of 541 radio sources, made by 87 VLBI sites yielded (1 + γ)/2 = 0.99992 ± 0.00023, or equivalently, γ − 1 = (−1.7 ± 4.5) × 10^−4 [335]. A 2009 analysis that incorporated data through 2008 yielded γ − 1 = (−1.6 ± 1.5) × 10^−4 [219]."
- Figure 5 caption: "VLBI light deflection measurements have reached 0.02 percent."
- Table 4 "Current limits on the PPN parameters": "γ−1 | light deflection | 2 × 10^−4 | VLBI".

So the headline VLBI number in Will 2014 is the Table 4 limit |γ − 1| ≲ 2 × 10^−4, whose most recent underlying result in the text is γ − 1 = (−1.6 ± 1.5) × 10^−4 (Lambert & Le Poncin-Lafitte 2009). The most widely cited single VLBI paper is Shapiro et al. 2004, γ − 1 = (−1.7 ± 4.5) × 10^−4.

Citations (Crossref):
- [219] Lambert, S. B.; Le Poncin-Lafitte, C., "Determining the relativistic parameter γ using very long baseline interferometry", Astronomy & Astrophysics 499(1), 331-335 (2009-05). DOI 10.1051/0004-6361/200911714. (Crossref query https://api.crossref.org/works?query.bibliographic=Lambert+Le+Poncin-Lafitte+...)
  Their arXiv abstract (https://export.arxiv.org/abs/0903.1615) does NOT state −1.6 ± 1.5; it says: "We arrive at the conclusion that the relativistic parameter γ cannot be estimated at better than 2×10^{-4}." — this is the origin of the Table 4 entry "2 × 10^−4".
- [335] Shapiro, S. S.; Davis, J. L.; Lebach, D. E.; Gregory, J. S., "Measurement of the Solar Gravitational Deflection of Radio Waves using Geodetic Very-Long-Baseline Interferometry Data, 1979–1999", Physical Review Letters 92(12), 121101 (2004-03-26). DOI 10.1103/PhysRevLett.92.121101. APS abstract (https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.92.121101): "Using a large geodetic VLBI data set, we obtained γ = 0.99983 ± 0.00045 (estimated standard error)."
- [147] Fomalont, E.; Kopeikin, S.; Lanyi, G.; Benson, J., "Progress in Measurements of the Gravitational Bending of Radio Waves Using the VLBA", Astrophysical Journal 699(2), 1395-1402 (2009). DOI 10.1088/0004-637X/699/2/1395.
- [224] Lebach et al., Phys. Rev. Lett. 75, 1439–1442 (1995) — taken from Will's reference list only, not separately checked in Crossref.

Status: **VERIFIED** (values as quoted in Will 2014; Shapiro 2004 value also confirmed in its own abstract; Lambert 2009 abstract gives only "not better than 2×10^-4", the (−1.6 ± 1.5)×10^−4 figure is from Will's text / the paper body, which was not fetched)

---

## 5. Hulse–Taylor pulsar PSR B1913+16: periastron advance and Ṗb(obs)/Ṗb(GR)

Primary source: J. M. Weisberg and Y. Huang, "Relativistic Measurements from Timing the Binary Pulsar PSR B1913+16", The Astrophysical Journal 829(1), 55 (2016-09-20), DOI 10.3847/0004-637X/829/1/55 (Crossref: https://api.crossref.org/works?query.bibliographic=Weisberg+Huang+Relativistic+measurements+...; title, journal, vol 829, issue 1, page 55 confirmed).
Text: arXiv:1606.02744v1 [astro-ph.HE] 3 Jun 2016, "Accepted by APJ 2016 Jun 1", https://arxiv.org/abs/1606.02744 (PDF downloaded, pdftotext). Accessed 2026-10-23.

Verbatim:
- Table 2 "Orbital Parameters" (figures in parentheses = formal TEMPO standard errors in the last digit):
  "⟨ω̇⟩ (deg / yr) . . .  4.226585(4)"
  "Pb (d) . . .  0.322997448918(3)"
  "e . . .  0.6171340(4)"
  "x ≡ a1 sin i (s). . .  2.341776(2)"
  "γ (ms) . . .  0.004307(4)"
  "Ṗb^obs . . .  −2.423(1) ×10^−12"
- Sec. 4.1: "we find that Ṗb^gal = −(0.025 ± 0.004) × 10^−12 . Inserting also Ṗb^obs from Table 2 into Eq. 15, we calculate that Ṗb^intr = −(2.398 ± 0.004) × 10^−12."
- Sec. 5.1: "we find that Ṗb^GR = (−2.40263 ± 0.00005) × 10^−12", and Eq. (23): Ṗb^intr / Ṗb^GR "= 0.9983±0.0016."
- Abstract: "We find that the ratio of observed orbital period decrease due to gravitational wave damping (corrected by a kinematic term) to the general relativistic prediction, is 0.9983 ± 0.0016; thereby confirming the existence and strength of gravitational radiation as predicted by general relativity."
- Abstract: masses "1.438 ± 0.001 M⊙ and 1.390 ± 0.001 M⊙" (pulsar, companion).

Earlier result for comparison: J. M. Weisberg, D. J. Nice, J. H. Taylor, "Timing Measurements of the Relativistic Binary Pulsar PSR B1913+16", ApJ 722(2), 1030-1034 (2010-10-20), DOI 10.1088/0004-637X/722/2/1030 (Crossref). arXiv:1011.0718 abstract (https://export.arxiv.org/api/query?search_query=ti:...): "The system's orbital period has been decreasing at a rate 0.997±0.002 times that predicted as a result of gravitational radiation damping in general relativity." and "m_1=1.4398±0.0002 M⊙ and m_2=1.3886±0.0002 M⊙". (The 2010 ω̇ value was not fetched — only the abstract was read.)

Values: ⟨ω̇⟩ = 4.226585 ± 0.000004 deg/yr; Ṗb^intr/Ṗb^GR = 0.9983 ± 0.0016 (WH2016); 0.997 ± 0.002 (WNT2010).
Status: **VERIFIED**

---

## 6. PDG world average αs(M_Z) and M_Z

IMPORTANT: a newer edition than PDG 2024 is online. The pdg.lbl.gov front page (accessed 2026-10-23) reads: "The Review of Particle Physics (2026) F. Takahashi et al. (Particle Data Group), Int. J. Mod. Phys. A 41, 2630011 (2026)". Both editions were downloaded and are quoted below.

Sources (PDF downloaded, text extracted with pdftotext):
- PDG 2024: S. Navas et al. (Particle Data Group), Phys. Rev. D 110, 030001 (2024). Review "9. Quantum Chromodynamics", "Revised August 2023 by J. Huston (Michigan State U.), K. Rabbertz (KIT) and G. Zanderighi", page footer "31st May, 2024". https://pdg.lbl.gov/2024/reviews/rpp2024-rev-qcd.pdf ; Summary table https://pdg.lbl.gov/2024/tables/rpp2024-sum-gauge-higgs-bosons.pdf (header "Citation: S. Navas et al. (Particle Data Group), Phys. Rev. D 110, 030001 (2024)").
- PDG 2026: F. Takahashi et al. (Particle Data Group), Int. J. Mod. Phys. A 41, 2630011 (2026). Review "9. Quantum Chromodynamics", "Revised August 2025 by J. Huston (Michigan State U.), K. Rabbertz (KIT) and G. Zanderighi". https://pdg.lbl.gov/2026/reviews/rpp2026-rev-qcd.pdf ; https://pdg.lbl.gov/2026/tables/rpp2026-sum-gauge-higgs-bosons.pdf (header "Citation: F. Takahashi et al. (Particle Data Group), Int. J. Mod. Phys. A 41, 2630011 (2026)").
Accessed 2026-10-23.

### αs(m_Z²)
- PDG 2024, Sec. 9.4.8, Eq. (9.25): "This gives our final world average value  αs(m²_Z) = 0.1180 ± 0.0009 (PDG 2023 average) . (9.25)". Components: Eq. (9.24) "αs(m²_Z) = 0.1175 ± 0.0010 (PDG 2023 without lattice)"; Eq. (9.23) "αs(m²_Z) = 0.1184 ± 0.0008 (FLAG 2021 estimate)".
- PDG 2026, Sec. 9.4.8, Eq. (9.25): "This gives our final world average value  αs(m²_Z) = 0.1180 ± 0.0009 (PDG 2025 average) . (9.25)". Components: Eq. (9.24) "αs(m²_Z) = 0.1178 ± 0.0010 (PDG 2025 without lattice)"; Eq. (9.23) "αs(m²_Z) = 0.1183 ± 0.0007 (FLAG 2024 estimate)".
- Value: αs(M_Z) = 0.1180 ± 0.0009 (MS-bar, n_f = 5), unchanged between the 2024 and 2026 editions.

Convention used by PDG (2024 review, Eq. 9.3), useful for item 7: "μ_R² dαs/dμ_R² = β(αs) = −(b0 αs² + b1 αs³ + b2 αs⁴ + · · · ) , (9.3) where b0 = (11C_A − 4n_f T_R)/(12π) = (33 − 2n_f)/(12π) ... the 2-loop coefficient is b1 = (17C_A² − n_f T_R(10C_A + 6C_F))/(24π²) = (153 − 19n_f)/(24π²), and the 3-loop coefficient is b2 = (2857 − 5033/9 n_f + 325/27 n_f²)/(128π³)". (So PDG b_i = β_i/(4π)^{i+1} in the a = αs/(4π) convention of item 7.)

### M_Z
- PDG 2024 summary table: "Z  J = 1 ... Mass m = 91.1880 ± 0.0020 GeV [e]" — matches the expected value.
- PDG 2026 summary table: "Mass m = 91.1879 ± 0.0020 GeV [e]" — central value shifted by −0.1 MeV relative to 2024.
- Footnote [e] (both editions): "The Z-boson mass listed here corresponds to a Breit-Wigner resonance parameter. It lies approximately 34 MeV above the real part of the position of the pole (in the energy-squared plane) in the Z-boson propagator."
- Full width (both editions): "Γ = 2.4955 ± 0.0023 GeV".

Status: αs(M_Z) = 0.1180 ± 0.0009 — **VERIFIED** (PDG 2024 and PDG 2026). M_Z = 91.1880 ± 0.0020 GeV — **VERIFIED for PDG 2024**; the latest edition (PDG 2026) gives 91.1879 ± 0.0020 GeV (**DIFFERS** from the expected value by 0.1 MeV, i.e. 0.05σ; irrelevant numerically, but cite the edition you use).

---

## 7. MS-bar QCD β-function coefficients to four loops (and five-loop β4)

### 7a. Four loops — van Ritbergen, Vermaseren, Larin (1997)
Citation (Crossref, https://api.crossref.org/works?query.bibliographic=van+Ritbergen+Vermaseren+Larin+...): T. van Ritbergen, J.A.M. Vermaseren, S.A. Larin, "The four-loop β-function in quantum chromodynamics", Physics Letters B 400(3-4), 379-384 (1997-05). DOI 10.1016/S0370-2693(97)00370-5.
Text: arXiv:hep-ph/9701390v1 27 Jan 1997, https://arxiv.org/abs/hep-ph/9701390 (PDF downloaded, pdftotext). Accessed 2026-10-23.

Convention, verbatim (Eq. 4): "The definition of the 4-dimensional β-function is:
  ∂a_s/∂ln μ² = β(a_s) = −β0 a_s² − β1 a_s³ − β2 a_s⁴ − β3 a_s⁵ + O(a_s⁶)   (4)
in which a_s = αs/4π = g²/16π², g = g(μ²) is the renormalized strong coupling constant ... μ is the 't Hooft unit of mass, the renormalization point in the MS-scheme."
Also: "Since Z_as does not depend explicitly on μ, the β-function is the same in all MS-like schemes ... That is why the β-function is the same in the MS-scheme [5] and in the MS-bar-scheme [9]."

SU(3) result, verbatim (Eq. 11; "Substitution of these colour factors for N = 3 into eq.(8) yields the following result for QCD"):
  β0 = 11 − (2/3) n_f
  β1 = 102 − (38/3) n_f
  β2 = 2857/2 − (5033/18) n_f + (325/54) n_f²
  β3 = (149753/6 + 3564 ζ3) − (1078361/162 + (6508/27) ζ3) n_f + (50065/162 + (6472/81) ζ3) n_f² + (1093/729) n_f³   (11)
"Here ζ is the Riemann zeta-function (ζ3 = 1.202056903 · · ·)."
Numerical form, verbatim (Eq. 12): "β0 ≈ 11 − 0.66667nf ; β1 ≈ 102 − 12.6667nf ; β2 ≈ 1428.50 − 279.611nf + 6.01852nf² ; β3 ≈ 29243.0 − 6946.30nf + 405.089nf² + 1.49931nf³ (12)". "We note that β3 is positive for all positive values of nf."
General-group form (Eq. 8) is also in the paper: "β0 = 11/3 C_A − 4/3 T_F n_f ; β1 = 34/3 C_A² − 4 C_F T_F n_f − 20/3 C_A T_F n_f ; β2 = 2857/54 C_A³ + 2 C_F² T_F n_f − 205/9 C_F C_A T_F n_f − 1415/27 C_A² T_F n_f + 44/9 C_F T_F² n_f² + 158/27 C_A T_F² n_f²" (β3 with quartic Casimirs d_A^{abcd}, d_F^{abcd}; not transcribed here).

Uncertainty: exact analytic results.
Status: **VERIFIED** (convention a = αs/(4π), d a/d ln μ² = −Σ β_i a^{i+2}; expressions as above).

### 7b. Five loops — Baikov, Chetyrkin, Kühn (2017)
Citation (Crossref, https://api.crossref.org/works?query.bibliographic=Baikov+Chetyrkin+Kuhn+Five-Loop+...): P. A. Baikov, K. G. Chetyrkin, J. H. Kühn, "Five-Loop Running of the QCD Coupling Constant", Physical Review Letters 118(8), 082002 (2017-02-24). DOI 10.1103/PhysRevLett.118.082002.
Text: arXiv:1606.08659v2 [hep-ph] 3 Aug 2016, https://arxiv.org/abs/1606.08659 (PDF downloaded, pdftotext). Accessed 2026-10-23.

CAUTION — DIFFERENT NORMALIZATION: Eq. (1): "β(a_s) = μ² d/dμ² a_s(μ) = −Σ_{i≥0} β_i a_s^{i+2} (1) which describes the running of the quark-gluon coupling a_s ≡ αs/π". Hence β_i^{BCK} = β_i^{vRVL} / 4^{i+1}; e.g. Eq. (2): "β0 = (1/4){11 − (2/3) n_f}, β1 = (1/4²){102 − (38/3) n_f}", Eq. (3) "β2 = (1/4³){2857/2 − (5033/18) n_f + (325/54) n_f²}", Eq. (4) β3 = (1/4⁴){...same as vRVL Eq. 11...}.
Eq. (5), verbatim structure: "β4 = (1/4⁵){ 8157455/16 + (621885/2) ζ3 − (88209/2) ζ4 − 288090 ζ5
  + n_f [ −336460813/1944 − (4811164/81) ζ3 + (33935/6) ζ4 + (1358995/27) ζ5 ]
  + n_f² [ 25960913/1944 + (698531/81) ζ3 − (10526/9) ζ4 − (381760/81) ζ5 ]
  + n_f³ [ −630559/5832 − (48722/243) ζ3 + (1618/27) ζ4 + (460/9) ζ5 ]
  + n_f⁴ [ 1205/2916 − (152/81) ζ3 ] }  (5)"
Numerical form (Eq. 6, a_s = αs/π normalization), verbatim: "β0 ≈ 2.75 − 0.166667 nf , β1 ≈ 6.375 − 0.791667 nf , β2 ≈ 22.3203 − 4.36892 nf + 0.0940394 nf² , β3 ≈ 114.23 − 27.1339 nf + 1.58238 nf² + 0.0058567 nf³ , β4 ≈ 524.56 − 181.8 nf + 17.16 nf² − 0.22586 nf³ − 0.0017993 nf⁴ ."
Table I, row "β4exact" for nf = 0,1,2,3,4,5,6: "525 360 228 127 57 15 0.27" (a_s = αs/π normalization).
Ratios β̄_i = β_i/β0 quoted: "β(nf = 3) = 1 + 1.78 as + 4.47 as² + 20.99 as³ + 56.59 as⁴ ; β(nf = 4) = 1 + 1.54 as + 3.05 as² + 15.07 as³ + 27.33 as⁴ ; β(nf = 5) = 1 + 1.26 as + 1.47 as² + 9.83 as³ + 7.88 as⁴".

My cross-check (computed here from the quoted exact Eq. 5 with ζ3 = 1.2020569, ζ4 = π⁴/90, ζ5 = 1.0369278; not a quoted number):
| n_f | β4 (a_s = αs/π, BCK) | β4 (a = αs/4π, vRVL convention = ×4⁵) | β3 (a = αs/4π) |
|---|---|---|---|
| 3 | 127.32 | 130 378 | 12 090.38 |
| 4 | 56.94 | 58 311 | 8 035.19 |
| 5 | 15.11 | 15 471 | 4 826.16 |
These agree with the paper's Table I (127, 57, 15).
Status: **VERIFIED** (citation, formula, and the n_f = 3, 4, 5 values 127 / 57 / 15 in the a_s = αs/π normalization). Watch the factor 4⁵ = 1024 when combining with vRVL coefficients.

---

## 8. PDG heavy-quark masses: m_c(m_c), m_b(m_b), top

Sources (PDF downloaded, pdftotext; accessed 2026-10-23):
- PDG 2024 Quark Summary Table, https://pdg.lbl.gov/2024/tables/rpp2024-sum-quarks.pdf — "Citation: S. Navas et al. (Particle Data Group), Phys. Rev. D 110, 030001 (2024)".
- PDG 2026 Quark Summary Table, https://pdg.lbl.gov/2026/tables/rpp2026-sum-quarks.pdf — "Citation: F. Takahashi et al. (Particle Data Group), Int. J. Mod. Phys. A 41, 2630011 (2026)".

Scheme statement (identical in both editions), verbatim: "The u-, d-, and s-quark masses are the MS masses at the scale μ = 2 GeV. The c- and b-quark masses are the MS masses renormalized at the MS mass, i.e. m = m(μ = m). The t-quark mass is extracted from event kinematics (see the review “The Top Quark”)." (pdftotext drops the bar over "MS".)

PDG 2024, verbatim:
- "m_c = 1.2730 ± 0.0046 GeV, CL = 90%"
- "m_b = 4.183 ± 0.007 GeV, CL = 90%"
- "m_b − m_c = 3.45 ± 0.05 GeV"
- top: "Mass (direct measurements) m = 172.57 ± 0.29 GeV [a,b] (S = 1.5)"; "Mass (from cross-section measurements) m = 162.5 +2.1 −1.5 GeV [a]" (this is the MS-bar m_t(m_t) from σ(tt̄)); "Mass (Pole from cross-section measurements) m = 172.4 ± 0.7 GeV"; "Full width Γ = 1.42 +0.19 −0.15 GeV (S = 1.4)".
- footnote [a]: "A discussion of the definition of the top quark mass in these measurements can be found in the review “The Top Quark.”"

PDG 2026, verbatim:
- "m_c = 1.2729 ± 0.0045 GeV, CL = 90%"
- "m_b = 4.186 ± 0.006 GeV, CL = 90%"
- top: "Mass (direct measurements) m = 172.60 ± 0.27 GeV [a,b] (S = 1.5)"; "Mass (from cross-section measurements) m = 162.5 +2.1 −1.5 GeV"; "Mass (Pole from cross-section measurements) m = 172.1 ± 0.6 GeV".

Context from the PDG 2024 review "60. Quark Masses" (https://pdg.lbl.gov/2024/reviews/rpp2024-rev-quark-masses.pdf): continuum determinations "m_c(m_c) = (1.280 ± 0.025)GeV, m_b(m_b) = (4.18 ± 0.03) GeV, m_b^{1S} = (4.65 ± 0.03) GeV"; lattice average Eq. (60.23) "m_c(m_c) = (1.275 ± 0.004 ± 0.008[±0.009]) GeV".

No expected values were given for this item. Values (PDG 2024): m_c(m_c) = 1.2730 ± 0.0046 GeV; m_b(m_b) = 4.183 ± 0.007 GeV; m_t(direct) = 172.57 ± 0.29 GeV; m_t(pole, from σ) = 172.4 ± 0.7 GeV.
Status: **VERIFIED** (PDG 2024). Latest edition (PDG 2026) values differ slightly (m_c 1.2729 ± 0.0045, m_b 4.186 ± 0.006, m_t direct 172.60 ± 0.27, pole 172.1 ± 0.6 GeV) — choose and cite one edition consistently.

---

## 9. PDG masses of charmonium and bottomonium states

Sources (accessed 2026-10-23), two independent PDG channels checked against each other:
(a) PDG 2024 Meson Summary Table PDF, https://pdg.lbl.gov/2024/tables/rpp2024-sum-mesons.pdf (Citation: S. Navas et al. (Particle Data Group), Phys. Rev. D 110, 030001 (2024)) — "Mass m = ..." lines quoted below;
(b) PDG official SQLite database for the 2024 edition, https://pdg.lbl.gov/2026/api/pdg-2024-v0.1.4.sqlite (pdginfo: edition "2024", citation "S. Navas et al. (Particle Data Group), Phys. Rev. D 110, 030001 (2024)", data_release_timestamp "2025-04-14"), table pdgdata, rows with in_summary_table = 1.
Also checked: PDG 2026 Meson Summary Table PDF https://pdg.lbl.gov/2026/tables/rpp2026-sum-mesons.pdf and https://pdg.lbl.gov/2026/api/pdg-2026.0.sqlite (citation "F. Takahashi et al. (Particle Data Group), Int. J. Mod. Phys. A 41, 2630011 (2026)").

All values in MeV. "Verbatim PDF" = exact text of the summary-table line; DB = display_value_text / PDG identifier. (S = scale factor.)

| State | PDG ID | PDG 2024, verbatim PDF summary line | PDG 2024 DB display | PDG 2026, verbatim PDF line | 2026 vs 2024 |
|---|---|---|---|---|---|
| η_c(1S) | M026M | "Mass m = 2984.1 ± 0.4 MeV (S = 1.2)" | '2984.1+-0.4' | "Mass m = 2984.09 ± 0.30 MeV (S = 1.2)" | changed (−0.01, smaller error) |
| J/ψ(1S) | M070M | "Mass m = 3096.900 ± 0.006 MeV" | '3096.900+-0.006' | "Mass m = 3096.900 ± 0.006 MeV" | same |
| χ_c0(1P) | M056M | "Mass m = 3414.71 ± 0.30 MeV" | '3414.71+-0.30' | "Mass m = 3415.50 ± 0.19 MeV (S = 1.7)" | **changed by +0.79 MeV** |
| χ_c1(1P) | M055M | "Mass m = 3510.67 ± 0.05 MeV (S = 1.2)" | '3510.67+-0.05' | "Mass m = 3510.67 ± 0.05 MeV (S = 1.2)" | same |
| h_c(1P) | M144M | "Mass m = 3525.37 ± 0.14 MeV (S = 1.2)" | '3525.37+-0.14' | "Mass m = 3525.37 ± 0.14 MeV (S = 1.2)" | same |
| χ_c2(1P) | M057M | "Mass m = 3556.17 ± 0.07 MeV" | '3556.17+-0.07' | "Mass m = 3556.17 ± 0.07 MeV" | same |
| η_c(2S) | M059M | "Mass m = 3637.7 ± 0.9 MeV (S = 1.2)" | '3637.7+-0.9' | "Mass m = 3637.8 ± 0.6 MeV (S = 1.1)" | changed (+0.1) |
| ψ(2S) | M071M | "Mass m = 3686.097 ± 0.011 MeV (S = 1.1)" | '3686.097+-0.011' (fit) | "Mass m = 3686.097 ± 0.011 MeV (S = 1.1)" | same |
| η_b(1S) | M171M | "Mass m = 9398.7 ± 2.0 MeV (S = 1.5)" | '9398.7+-2.0' | "Mass m = 9398.7 ± 2.0 MeV (S = 1.5)" | same |
| Υ(1S) | M049M | "Mass m = 9460.40 ± 0.10 MeV" | '9460.40+-0.10' | "Mass m = 9460.40 ± 0.10 MeV" | same |
| χ_b0(1P) | M076M | "Mass m = 9859.44 ± 0.42 ± 0.31 MeV" | '9859.44+-0.42+-0.31' | "Mass m = 9859.44 ± 0.42 ± 0.31 MeV" | same |
| χ_b1(1P) | M077M | "Mass m = 9892.78 ± 0.26 ± 0.31 MeV" | '9892.78+-0.26+-0.31' | "Mass m = 9892.78 ± 0.26 ± 0.31 MeV" | same |
| h_b(1P) | M204M | "Mass m = 9899.3 ± 0.8 MeV" | '9899.3+-0.8' | "Mass m = 9899.3 ± 0.8 MeV" | same |
| χ_b2(1P) | M078M | "Mass m = 9912.21 ± 0.26 ± 0.31 MeV" | '9912.21+-0.26+-0.31' | "Mass m = 9912.21 ± 0.26 ± 0.31 MeV" | same |
| Υ(2S) | M052M | "Mass m = 10023.4 ± 0.5 MeV" | '10023.4+-0.5' | "Mass m = 10023.4 ± 0.5 MeV" | same |
| Υ(3S) | M048M | "Mass m = 10355.1 ± 0.5 MeV" | '10355.1+-0.5' | "Mass m = 10355.1 ± 0.5 MeV" | same |

Notes, verbatim from the PDG 2024 summary table:
- χ_b0/χ_b1/χ_b2(1P) carry footnote [yyaa]: "Spectroscopic labeling for these states is theoretical, pending experimental information." Their two errors are statistical ± systematic-type components as printed (single-measurement "V" value type in the DB, not a PDG average).
- η_c(2S): "Quantum numbers are quark model predictions."
- ψ(2S): the summary-table value is the PDG fit (DB value_type "FC"); the PDG average ("AC") is '3686.097+-0.010'.

No expected values were given for this item; values for PDG 2024 are as tabulated.
Status: **VERIFIED** (PDG 2024, two channels agree). Latest edition (PDG 2026) differs for η_c(1S), χ_c0(1P) (+0.79 MeV, 2.6σ of the 2024 error) and η_c(2S).

---

## 10. Cornell potential parameters (Eichten, Gottfried, Kinoshita, Lane, Yan)

Citations (Crossref):
- E. Eichten, K. Gottfried, T. Kinoshita, K. D. Lane, T. M. Yan, "Charmonium: Comparison with experiment", Physical Review D 21(1), 203-233 (1980-01-01). DOI 10.1103/PhysRevD.21.203. https://api.crossref.org/works/10.1103/PhysRevD.21.203 — preprint CLNS-425 (INSPIRE 141420).
- E. Eichten, K. Gottfried, T. Kinoshita, K. D. Lane, T.-M. Yan, "Charmonium: The model", Physical Review D 17(11), 3090-3117 (1978-06-01). DOI 10.1103/PhysRevD.17.3090. https://api.crossref.org/works/10.1103/PhysRevD.17.3090 — Erratum Phys. Rev. D 21, 313 (1980) (listed on the APS abstract page); preprint CLNS-375 (INSPIRE 129333).

Full-text access:
- PRD 21, 203 (1980): APS abstract page (https://journals.aps.org/prd/abstract/10.1103/PhysRevD.21.203) was read — the abstract gives NO parameter values ("The parameters of the "naive" model, in which the system is described as a c c̄ pair, are determined from the observed positions of ψ, ψ′, and the P states."). Full text is behind the APS paywall. The KEK scanned preprint (KEKSCAN 79-09-135, https://lib-extopc.kek.jp/preprints/PDF/1979/7909/7909135.pdf) is a 1-page placeholder: "This publication is not inputted, please come and look at the Library." → **the 1980 parameter values could NOT be read in the original paper.**
- PRD 17, 3090 (1978): preprint CLNS-375 (February 1978, "Submitted to Physical Review D"), KEK scan https://lib-extopc.kek.jp/preprints/PDF/1978/7805/7805246.pdf (88 pages, OCR text layer) — read. (Preprint, not the published version; numbers may have changed in print.)

Verbatim from CLNS-375 (1978 preprint; OCR, symbols reconstructed where the OCR garbled them):
- Potential, Eq. (2.1): "V(r) = −κ/r + r/a²  (2.1)  The 1/r behavior of the first term is in accordance with asymptotic freedom. However, the strength κ will be treated as a purely phenomenological parameter ... The linear confinement potential r/a² is inferred from lattice gauge theory and its relation to the dual string model. ... the constant of proportionality 1/a² does not depend on the quark flavor."
- "we have allowed κ to be a free parameter dissociated from the effective coupling constant as determined by the hadronic width of ψ. Instead, the value of κ is determined from the observed data for spin-triplet states".
- Pure linear case (Coulomb term ignored), Eq. (2.15): "Comparison of Eqs. (2.12) and (2.14) with the data yields a = 1.95 GeV^−1, m_c = 1.85 GeV (2.15)".
- Coupled-channel figures (Fig. 3 caption): "The quark masses are m_u = m_d = 0.33 GeV and m_c = 1.65 GeV, while a = 2.07 GeV^−1."
- Same section: "The following analysis, which restores the Coulombic potential, therefore leads to a value of m_c that differs noticeably from the one in (2.15)". The fitted Coulomb+linear set (κ, a, m_c) of the final model is in Part II (= PRD 21, 203), not in this preprint.

Secondary source by one of the original authors (used as the best reachable statement of the 1980 values):
E. J. Eichten and C. Quigg, "Quarkonium Wave Functions at the Origin", FERMILAB-PUB-95/045-T, arXiv:hep-ph/9503356v1 (16 Mar 1995), published Phys. Rev. D 52(3), 1726-1728 (1995-08-01), DOI 10.1103/PhysRevD.52.1726 (Crossref confirmed). https://arxiv.org/abs/hep-ph/9503356 (PDF read). Verbatim:
"a Coulomb-plus-linear potential (the “Cornell potential”) [8], V(r) = −κ/r + r/a² , (6) with m_c = 1.84 GeV/c² m_b = 5.18 GeV/c² (7) κ = 0.52 a = 2.34 GeV^−1 . (8)"
with "[8] E. Eichten, K. Gottfried, T. Kinoshita, K. D. Lane, T.-M. Yan, Phys. Rev. D 17, 3090 (1978); ibid. 21, 313(E) (1980); ibid. 21, 203 (1980)."

Values: V(r) = −κ/r + r/a², κ = 0.52, a = 2.34 GeV^−1 (string tension 1/a² ≈ 0.183 GeV², my arithmetic), m_c = 1.84 GeV (m_b = 5.18 GeV in Eichten–Quigg 1995).
Status: **NOT FOUND in the 1980 original (paywalled, no scan)**; form of the potential **VERIFIED** in the 1978 preprint; κ = 0.52, a = 2.34 GeV^−1, m_c = 1.84 GeV **VERIFIED only via the secondary source** Eichten & Quigg 1995 (co-author of the original). The 1978 preprint values differ (pure linear: a = 1.95 GeV^−1, m_c = 1.85 GeV; coupled-channel figures: a = 2.07 GeV^−1, m_c = 1.65 GeV) — do not mix them.

Addendum to item 10: OSTI record 5729035 (https://www.osti.gov/biblio/5729035, listed by INSPIRE for PRD 21, 203) could not be reached (connection timed out, HTTP code 000), so no OSTI copy was checked.

---

## 11. Loophole-free Bell tests (2015)

Citations (Crossref; accessed 2026-10-23):
- B. Hensen, H. Bernien, A. E. Dréau, A. Reiserer, N. Kalb, M. S. Blok, ... (19 authors), "Loophole-free Bell inequality violation using electron spins separated by 1.3 kilometres", Nature 526(7575), 682-686 (2015-10). DOI 10.1038/nature15759.
- M. Giustina, M. A. M. Versteegh, S. Wengerowsky, J. Handsteiner, A. Hochrainer, K. Phelan, ... (22 authors), "Significant-Loophole-Free Test of Bell’s Theorem with Entangled Photons", Physical Review Letters 115(25), 250401 (2015-12-16). DOI 10.1103/PhysRevLett.115.250401.
- L. K. Shalm, E. Meyer-Scott, B. G. Christensen, P. Bierhorst, M. A. Wayne, M. J. Stevens, ... (34 authors), "Strong Loophole-Free Test of Local Realism", Physical Review Letters 115(25), 250402 (2015-12-16). DOI 10.1103/PhysRevLett.115.250402 (https://api.crossref.org/works/10.1103/PhysRevLett.115.250402).

Hensen et al. CHSH value, verbatim from the Nature abstract (https://www.nature.com/articles/nature15759):
"We performed 245 trials that tested the CHSH–Bell inequality S ≤ 2 and found S = 2.42 ± 0.20 (where S quantifies the correlation between measurement outcomes). A null-hypothesis test yields a probability of at most P = 0.039 that a local-realist model for space-like separated sites could produce data with a violation at least as large as we observe, even when allowing for memory in the devices." Also: "estimated state fidelity of 0.92 ± 0.03".
Same in arXiv:1508.05949v1 abstract (https://export.arxiv.org/api/query?id_list=1508.05949; arXiv title "Experimental loophole-free violation of a Bell inequality using entangled electron spins separated by 1.3 km"): "We perform 245 trials testing the CHSH-Bell inequality S ≤ 2 and find S = 2.42 ± 0.20. A null hypothesis test yields a probability of p = 0.039".

For context (arXiv abstracts, https://export.arxiv.org/api/query?id_list=1511.03190,1511.03189):
- Giustina et al. (arXiv:1511.03190v2): "The purely statistical probability of our results to occur under local realism does not exceed 3.74 × 10^−31, corresponding to an 11.5 standard deviation effect." (They test a CH/Eberhard-type inequality, not CHSH with S.)
- Shalm et al. (arXiv:1511.03189v2): "we compute p-values as small as 5.9×10^−9 for our Bell violation ... our smallest adjusted p-value is 2.3 × 10^−7."

Note: Nature's own editorial summary on the page says "the authors reject local-realist hypotheses by two standard deviations only" — S = 2.42 ± 0.20 is ~2.1σ above 2; the strength of evidence is P = 0.039.
Status: **VERIFIED** (all three titles/citations; S = 2.42 ± 0.20)

---

## 12. Citations checked against Crossref

All via the Crossref REST API (https://api.crossref.org/works?query.bibliographic=..., no mailto/identifier sent), accessed 2026-10-23. "Crossref record" lists title / journal / volume(issue) / pages / issued date / DOI exactly as returned (author lists truncated after six).

| # | Expected | Crossref record | Status |
|---|---|---|---|
| 12.1 | Alväger et al., Phys. Lett. 12, 260 (1964) | T. Alväger, F.J.M. Farley, J. Kjellman, L. Wallin, "Test of the second postulate of special relativity in the GeV region", Physics Letters 12(3), 260-262, 1964-10. DOI 10.1016/0031-9163(64)91095-9 | VERIFIED (citation). The "π⁰-decay photons" detail is not in the Crossref metadata (no abstract), not checked against the text. |
| 12.2 | Brecher, PRL 39, 1051 (1977) | K. Brecher, "Is the Speed of Light Independent of the Velocity of the Source?", Physical Review Letters 39(17), 1051-1054, 1977-10-24. DOI 10.1103/PhysRevLett.39.1051. Note: Crossref also lists an item with the same title, PRL 39(19), 1236 (1977-11-07), DOI 10.1103/PhysRevLett.39.1236.3 (an erratum to this Letter) | VERIFIED (consider citing the erratum too) |
| 12.3 | Michelson & Morley, Am. J. Sci. 34, 333 (1887) | A. A. Michelson, E. W. Morley, "On the relative motion of the Earth and the luminiferous ether", American Journal of Science, vol "s3-34" (3rd series, vol 34), issue 203, 333-345, 1887-11-01. DOI 10.2475/ajs.s3-34.203.333 | VERIFIED (cite as Am. J. Sci. (3rd ser.) 34, 333 (1887)) |
| 12.4 | Bardeen, Press, Teukolsky, ApJ 178, 347 (1972) | J. M. Bardeen, W. H. Press, S. A. Teukolsky, "Rotating Black Holes: Locally Nonrotating Frames, Energy Extraction, and Scalar Synchrotron Radiation", The Astrophysical Journal 178, 347, 1972-12. DOI 10.1086/151796 | VERIFIED |
| 12.5 | Kerr, PRL 11, 237 (1963) | R. P. Kerr, "Gravitational Field of a Spinning Mass as an Example of Algebraically Special Metrics", Physical Review Letters 11(5), 237-238, 1963-09-01. DOI 10.1103/PhysRevLett.11.237 | VERIFIED |
| 12.6 | Englert, PRL 77, 2154 (1996) | B.-G. Englert, "Fringe Visibility and Which-Way Information: An Inequality", Physical Review Letters 77(11), 2154-2157, 1996-09-09. DOI 10.1103/PhysRevLett.77.2154 | VERIFIED |
| 12.7 | Chapman et al., PRL 75, 3783 (1995) | M. S. Chapman, T. D. Hammond, A. Lenef, J. Schmiedmayer, R. A. Rubenstein, E. Smith, ... (7 authors), "Photon Scattering from Atoms in an Atom Interferometer: Coherence Lost and Regained", Physical Review Letters 75(21), 3783-3787, 1995-11-20. DOI 10.1103/PhysRevLett.75.3783 | VERIFIED |
| 12.8 | Sinha et al., Science 329, 418 (2010) | U. Sinha, C. Couteau, T. Jennewein, R. Laflamme, G. Weihs, "Ruling Out Multi-Order Interference in Quantum Mechanics", Science 329(5990), 418-421, 2010-07-23. DOI 10.1126/science.1190545 | VERIFIED |
| 12.9 | Sorkin, Mod. Phys. Lett. A 9, 3119 (1994) | R. D. Sorkin, "Quantum Mechanics as Quantum Measure Theory", Modern Physics Letters A 09(33), 3119-3127, 1994-10-30. DOI 10.1142/S021773239400294X | VERIFIED |
| 12.10 | Ghirardi, Rimini, Weber, PRD 34, 470 (1986) | G. C. Ghirardi, A. Rimini, T. Weber, "Unified dynamics for microscopic and macroscopic systems", Physical Review D 34(2), 470-491, 1986-07-15. DOI 10.1103/PhysRevD.34.470 | VERIFIED |
| 12.11 | Bassi et al., Rev. Mod. Phys. 85, 471 (2013) | A. Bassi, K. Lochan, S. Satin, T. P. Singh, H. Ulbricht, "Models of wave-function collapse, underlying theories, and experimental tests", Reviews of Modern Physics 85(2), 471-527, 2013-04-02. DOI 10.1103/RevModPhys.85.471 | VERIFIED |
| 12.12 | Bohm, Phys. Rev. 85, 166 (1952) | D. Bohm, "A Suggested Interpretation of the Quantum Theory in Terms of "Hidden" Variables. I", Physical Review 85(2), 166-179, 1952-01-15. DOI 10.1103/PhysRev.85.166 (Part II: Phys. Rev. 85, 180-193, DOI 10.1103/PhysRev.85.180) | VERIFIED |
| 12.13 | Kocsis et al., Science 332, 1170 (2011) | S. Kocsis, B. Braverman, S. Ravets, M. J. Stevens, R. P. Mirin, L. K. Shalm, ... (7 authors), "Observing the Average Trajectories of Single Photons in a Two-Slit Interferometer", Science 332(6034), 1170-1173, 2011-06-03. DOI 10.1126/science.1202218 | VERIFIED |
| 12.14 | Brans & Dicke, Phys. Rev. 124, 925 (1961) | C. Brans, R. H. Dicke, "Mach's Principle and a Relativistic Theory of Gravitation", Physical Review 124(3), 925-935, 1961-11-01. DOI 10.1103/PhysRev.124.925 | VERIFIED |
| 12.15 | Bertotti, Iess, Tortora, Nature 425, 374 (2003) | B. Bertotti, L. Iess, P. Tortora, "A test of general relativity using radio links with the Cassini spacecraft", Nature 425(6956), 374-376, 2003-09. DOI 10.1038/nature01997 (see item 3) | VERIFIED |

Other citations confirmed along the way (Crossref): Will, Living Rev. Relativ. 17, 4 (2014), DOI 10.12942/lrr-2014-4; Lambert & Le Poncin-Lafitte, A&A 499, 331 (2009), DOI 10.1051/0004-6361/200911714; Shapiro et al., PRL 92, 121101 (2004), DOI 10.1103/PhysRevLett.92.121101; Fomalont et al., ApJ 699, 1395 (2009), DOI 10.1088/0004-637X/699/2/1395; Weisberg & Huang, ApJ 829, 55 (2016), DOI 10.3847/0004-637X/829/1/55; Weisberg, Nice & Taylor, ApJ 722, 1030 (2010), DOI 10.1088/0004-637X/722/2/1030; van Ritbergen et al., PLB 400, 379 (1997), DOI 10.1016/S0370-2693(97)00370-5; Baikov et al., PRL 118, 082002 (2017), DOI 10.1103/PhysRevLett.118.082002; Eichten et al., PRD 21, 203 (1980), DOI 10.1103/PhysRevD.21.203 and PRD 17, 3090 (1978), DOI 10.1103/PhysRevD.17.3090; Hensen et al., Giustina et al., Shalm et al. (item 11).

---

## Summary

| # | Item | Value as found | Source | Status |
|---|---|---|---|---|
| 1 | Mercury orbit | a = 57.909×10⁶ km = 0.38709893 AU; e = 0.2056 (0.20563069 J2000); P_sid = 87.969 d | NASA NSSDCA Mercury Fact Sheet (upd. 11 Jan 2024) | VERIFIED |
| 2 | GR perihelion advance of Mercury | 42.98″/century × [(2+2γ−β)/3 + 3×10⁻⁴ J2/10⁻⁷], Eq. (65), Sec. 4.2 | Will 2014, LRR 17, 4 (arXiv:1403.7377) | VERIFIED |
| 3 | Cassini γ | γ − 1 = (2.1 ± 2.3)×10⁻⁵ (frequency-shift/Doppler measurement) | Bertotti, Iess, Tortora, Nature 425, 374 (2003) abstract; Will 2014 Sec. 4.1.2 | VERIFIED |
| 4 | VLBI γ bound in Will 2014 | Table 4: 2×10⁻⁴; text: γ−1 = (−1.6 ± 1.5)×10⁻⁴ (Lambert & Le Poncin-Lafitte 2009), (−1.7 ± 4.5)×10⁻⁴ (Shapiro et al. 2004) | Will 2014 Sec. 4.1.1; Shapiro 2004 abstract γ = 0.99983 ± 0.00045 | VERIFIED (the −1.6 ± 1.5 figure only via Will; L&LPL abstract says "not better than 2×10⁻⁴") |
| 5 | PSR B1913+16 | ⟨ω̇⟩ = 4.226585(4) deg/yr; Ṗb,intr/Ṗb,GR = 0.9983 ± 0.0016 (WNT 2010: 0.997 ± 0.002) | Weisberg & Huang, ApJ 829, 55 (2016) | VERIFIED |
| 6 | αs(M_Z), M_Z | αs = 0.1180 ± 0.0009 (PDG 2024 and 2026); M_Z = 91.1880 ± 0.0020 GeV (PDG 2024), 91.1879 ± 0.0020 GeV (PDG 2026) | PDG 2024 PRD 110, 030001; PDG 2026 IJMPA 41, 2630011 | αs VERIFIED; M_Z VERIFIED for 2024, DIFFERS by 0.1 MeV in the latest (2026) edition |
| 7 | QCD β-function | a = αs/4π, da/dlnμ² = −Σβ_i a^{i+2}; β0 = 11 − 2n_f/3, β1 = 102 − 38n_f/3, β2 = 2857/2 − 5033n_f/18 + 325n_f²/54, β3 (with ζ3) as Eq. (11); β4 (BCK, a_s = αs/π normalization!) = 127 / 57 / 15 for n_f = 3/4/5 | van Ritbergen–Vermaseren–Larin PLB 400, 379; Baikov–Chetyrkin–Kühn PRL 118, 082002 | VERIFIED (watch the 4^{i+1} normalization factor between the papers) |
| 8 | Heavy-quark masses | m_c(m_c) = 1.2730 ± 0.0046 GeV; m_b(m_b) = 4.183 ± 0.007 GeV; m_t direct 172.57 ± 0.29 GeV, pole (from σ) 172.4 ± 0.7 GeV (PDG 2024) | PDG 2024 quark summary table | VERIFIED (2024); PDG 2026 slightly different (1.2729 ± 0.0045, 4.186 ± 0.006, 172.60 ± 0.27, 172.1 ± 0.6) |
| 9 | cc̄ and bb̄ masses (16 states) | e.g. J/ψ 3096.900 ± 0.006, ψ(2S) 3686.097 ± 0.011, Υ(1S) 9460.40 ± 0.10 MeV, full table in §9 | PDG 2024 meson summary table + PDG 2024 SQLite | VERIFIED (2024); PDG 2026 changes η_c(1S), χ_c0(1P) (+0.79 MeV), η_c(2S) |
| 10 | Cornell potential | V = −κ/r + r/a²; κ = 0.52, a = 2.34 GeV⁻¹, m_c = 1.84 GeV (m_b = 5.18 GeV) | Potential form: CLNS-375 preprint of PRD 17, 3090; numbers: Eichten & Quigg PRD 52, 1726 (1995), quoting PRD 21, 203 | NOT FOUND in the 1980 original (paywalled, no scan); numbers verified only via the secondary source |
| 11 | Loophole-free Bell tests | Titles/citations as given; Hensen S = 2.42 ± 0.20 (245 trials, P = 0.039) | Crossref; Nature abstract; arXiv:1508.05949 | VERIFIED |
| 12 | 15 citations | all journal/volume/page/year as given (Michelson–Morley vol is "s3-34"; Brecher has an erratum PRL 39, 1236) | Crossref | VERIFIED (all 15) |

Sources not reachable in this session: full text of Eichten et al. PRD 21, 203 (1980) (APS paywall; KEK scan "not inputted"); OSTI 5729035 (timed out); full text of Lambert & Le Poncin-Lafitte 2009 (only the abstract was read).
