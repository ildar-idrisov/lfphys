# lfphys source verification — 2026-11-04, plan item P1 (batch B8: charges and the slit)

Purpose: every formula, number and quotation used by `core.em.charges` and `core.em.slit` (and by v02's vector mode),
checked against the source text. Texts were fetched on 2026-11-04 from: arXiv, public-domain scans (archive.org: Rayleigh's
Scientific Papers IV, Schott 1912; GDZ Göttingen: Sommerfeld 1896; the archive.org DTIC mirror: RADC-TR-79-257; the
UNM Interaction Notes collection), an author's page (Qi et al.), lecture notes (Fitzpatrick), the X-ray Data Booklet
and the PDG review. They were read with `pdftotext` or, where the formulas are images or scans, from rendered pages.
The full texts are kept outside the repository. No contact parameter or personal identifier was sent with any request.

Status codes as in `verification_2026-10-23.md`:

* VERIFIED: quoted from the source.
* DIFFERS: the source and the engine disagree; both are given.
* NOT FETCHED: the text is closed or was unreachable; the entry says what replaces it.

"(mine)" marks the engine author's own algebra or checks, not text from a source.

## 1. Liénard–Wiechert fields, Larmor and Liénard power, angular distributions (`core.em.charges`)

**Source.** R. Fitzpatrick, *Classical Electromagnetism*, graduate lecture notes (UT Austin; PDF of 27 Jun 2014), SI units.
Fetched from https://farside.ph.utexas.edu/teaching/jk1/Electromagnetism.pdf. The PDF's text layer drops "ε" in
"4π ε0", so the formulas were checked against rendered pages 294 and 300.

* Potentials (12.276)–(12.277): "A(x, t) = (µ0 e/4π) u/s", "φ(x, t) = (e/4πε0) 1/s", where "s = r − r·u/c" and r
  runs from the retarded position to the field point. VERIFIED. The engine writes these as φ = q/(4πε0 κR),
  A = φβ/c, κ = 1 − n·β (mine; the same expressions).
* Fields (12.293)–(12.297). VERIFIED:
  * "(4πε0/e) E = (1/s³)(r − r u/c)(1 − u²/c²) + (1/(s³c²)) (r × [(r − r u/c) × u̇])";
  * "B = r × E/(r c)";
  * the split into "E_induction" (12.298) and "E_radiation" (12.303).

  The engine uses the same formula in the variables n, β, κ: (n − β)/(γ²κ³R²) and n × ((n − β) × β̇)/(κ³R) (mine,
  equal term by term since s = κR).
* Uniformly moving charge, from the PRESENT position (12.299): "E = (e/4πε0)(1 − u²/c²) / (r0³(1 − u²/c² +
  u_r²/c²)^{3/2}) r0". VERIFIED. With u_r = u cos ψ this is (1 − β² sin²ψ)^{3/2} (mine). Tested to 1e-10 up to
  β = 0.9999.
* Larmor (12.309): "P = e² u̇²/(6πε0c³)". VERIFIED.
* Liénard (12.327): "P = (e²/(6πε0c³)) γ⁶ (u̇² − (u × u̇)²/c²)". VERIFIED.
* Circular motion (12.332): "P = (e²/(6πε0c³)) γ⁴ u̇²". VERIFIED.
* Retarded versus observer time (12.337)–(12.338). VERIFIED:
  * "This quantity is actually the amount of energy lost by the charge in a retarded time interval dt′" (checked on the
    rendered page 300, re-checked 2026-11-04 in processing review B8: the text layer reads "dt", dropping the prime);
  * the Poynting vector "represents the energy flux per unit actual time, t";
  * "dP(t′)/dΩ = e² r [r × (r_u × u̇)]²/(16π²ε0c³s⁵)".

  The per-observer-time form with κ⁶ follows from his (12.337) with dt/dt′ = s/r. Fitzpatrick does not write it out
  (mine). The engine's tests confirm both forms: the retarded-time pattern integrates to Liénard's P to 1e-10, and the
  observer-time pattern equals the flux R²S·n of the computed fields on a sphere of the light cone to 2e-4 at
  R = 10⁴ m.
* Collinear case (12.343)–(12.344): "∫(1 − µ²)dµ/[1 − (u/c)µ]⁵ = (4/3)γ⁶", "P(t′) = (e²/(6πε0c³))γ⁶u̇²". VERIFIED.
  It is reproduced by the sphere integral (test).
* NOT FETCHED: Jackson, *Classical Electrodynamics* (closed; cited only by chapter) and the Feynman Lectures online
  (the site answered HTTP 403 to scripted requests; no workaround was tried). Fitzpatrick replaces both.

## 2. Synchrotron radiation (`core.em.charges`)

* **X-ray Data Booklet §2.1** (K.-J. Kim; https://xdb.lbl.gov/Section2/Sec_2-1.html; the equations are GIF images,
  transcribed from them).
  * Eq. (1): d²Ṡ_B/(dθ dψ) = (3α/4π²) γ² (Δω/ω)(I/e) y² (1 + X²)² [K²_{2/3}(ξ) + X²/(1 + X²) K²_{1/3}(ξ)].
    VERIFIED.
  * Definitions (text): "ωc = critical frequency, defined as the frequency that divides the emitted power into equal
    halves, = 3γ³c/2ρ". VERIFIED.
  * "The first and second terms in the last bracket of Eq. (1) correspond, respectively, to the intensity of the
    horizontally and vertically polarized radiation." VERIFIED.
  * Eq. (5): G₁(y) = y ∫_y^∞ K_{5/3}. VERIFIED.
  * DIFFERS (slightly): the fraction of the power below ω_c is 0.5000052565 (mpmath, 25 digits; the engine gives the
    same, test `test_synchrotron_spectrum_integrates_to_lienard_power_and_splits_seven_to_one`). "Equal halves" holds
    to 5e-6; the engine's docstring says "nominally" (review B8 C12).
  * The engine turns eq. (1) into power for one charge (mine): ħω × photons per unit ω, I/e = βc/(2πρ), times 2π of
    orbit angle. This gives d²P/(dω dψ) = 3q²γ²β/(16π³ε0ρ) y²(1 + X²)²[…]. Integrated over ψ it equals the
    (F ± G) forms to 1e-9 at γ = 1e5. At γ = 1000 they differ by 1.5e-6 = (3/2)/γ²: the β of the booklet's I/e
    against β⁴ in Liénard's power, both ultrarelativistic.
* **PDG, "Electromagnetic relations"** (H. G. Spieler, rev. 2005, RPP version of 31 May 2024; fetched from
  https://pdg.lbl.gov/2024/reviews/rpp2024-rev-electromag-relations.pdf), §7.3, Gaussian units. All VERIFIED:
  * (7.10) "δE = (4π/3)(e²/R)β³γ⁴";
  * (7.12) "dI = (8π/9) α γ F(ω/ωc) d(ħω)";
  * (7.13) "ωc = 3γ³c/(2R)";
  * (7.14) "F(y) = (9/8π) √3 y ∫_y^∞ K5/3(x) dx";
  * the footnote "earlier editions of Ref. [2] [Jackson] had ωc twice as large as Eq. (7.13)".

  The PDG's F has unit integral. The task's F(x) = x∫K_{5/3} has ∫F = 8π/(9√3), and the engine's
  S = (9√3/8π)F is the PDG's F. ∫F = 8π/(9√3) is checked to 1e-10 and ∫G = 2π/(3√3) to 1e-10 (G's integral is
  Γ(2/3)Γ(4/3), mine).
* The σ:π split, (9√3/16π)(F ± G): derived from ∫G/∫F = 3/4 (mine). The ratio 7:1 is tested, and the two
  polarisation spectra are checked against the booklet's angular form integrated over ψ (above).
* Asymptotes of F (textbook forms, mine): F → (4π/(√3Γ(1/3)))(x/2)^{1/3} and F → √(πx/2)e^{−x}. Tested.
* NOT FETCHED: R. P. Walker, CAS CERN 94-01 (CDS returned an empty page / HTTP 500); Wiedemann, *Particle
  Accelerator Physics* (Springer served a challenge page). The booklet and the PDG replace them.

## 3. Cyclotron harmonics (Schott)

**Source.** G. A. Schott, *Electromagnetic Radiation* (Cambridge 1912, public domain; archive.org
electromagneticr00schouoft). Gaussian units: "we shall use electrostatic units … for electric quantities". The formulas
were read from rendered pages 108–110.

* (128): "s̄_j = (c e² β² j²/(2π ρ² r²)) [cot² θ . {J_j(jβ sin θ)}² + β² {J_j′(jβ sin θ)}²]". VERIFIED.
* "R_j = (2ce²β/ρ²)[jβ² J′_{2j}(2jβ) − j²(1 − β²) ∫_0^β J_{2j}(2jx) dx]". VERIFIED.
* (130): "R = 2ce²β⁴/(3ρ²(1 − β²)²) … agrees with the value of the radiation given by Liénard". VERIFIED.

The SI forms use e² → q²/(4πε0) (mine). They are tested in three ways:

* Σ_m P_m equals Liénard's power to 1e-9 (β = 0.05 and 0.5) and to 1e-6 (β = 0.9, 400 harmonics);
* each P_m equals the integral of the angular form to 1e-9;
* an independent route: the Fourier transform of the engine's Liénard–Wiechert field at r = 10⁶ ρ over one period
  matches eq. (128) to 1e-5 (m = 1, 2, 3).

## 4. Narrow slit in a thick screen, TM (`core.em.slit`)

* **Takakura, PRL 86, 5601 (2001)**, doi:10.1103/PhysRevLett.86.5601: NOT FETCHED. The OpenAlex copy at TU Dortmund
  Eldorado is withdrawn (HTTP 401); arXiv, HAL and CORE have none. Abstract (OpenAlex, re-fetched 2026-11-04): "A
  Fabry-Pérot-like behavior is reported. The resonance peaks, however, have very low magnitude and a systematic shift
  towards longer wavelengths is observed." Replaced by the sources below. The peak height λ/(πw) is therefore not
  attributed to Takakura (his normalisation evidently differs, "very low magnitude"); it is Harrington & Auckland's
  and Holley & Schnitzer's (below). Takakura is cited only for the resonance shift, through Holley & Schnitzer's
  rendering (35) [error in earlier: the engine's test docstring attributed the peak height to Takakura; review B8
  C14].
* **Holley & Schnitzer, arXiv:1812.06753v2** (PEC wall, H along the slit, slit width 2lh, wall thickness l).
  * Results. VERIFIED:
    * (12) the "Fabry–Pérot frequencies Ω̄ = mπ, m = 1, 2, . . .", with (2) the dimensionless frequency Ω = ωl/c;
    * (32) "η ≈ h⁻¹ Ω̄|A|²";
    * (33) "|A|² = (πm)⁻² / [1 + (Ω′ − (2/π)(ln(2mh) + γE − 1))²]";
    * (34) "∆f/fm ≈ (4h/π)(ln h + ln(2m) + γE − 1)";
    * (35) their rendering of Takakura: "(∆f/fm)_{Ref. [4]} = (4h/π)(ln h + ln(πm) − 3/2)".
  * The peak η = 1/(πmh) = λ/(πw) follows from (32)–(33) at resonance, |A|² = (πm)⁻² and Ω̄ = mπ (mine; slit width
    w = 2lh, wall thickness l, λ = 2l/m at the m-th resonance).
  * Engine:
    * the peak at w = 0.02 λ is 15.928 against λ/(πw) = 15.915 (8e-4), and at w = 0.05 λ it is 6.398 against 6.366;
    * the resonant thickness at w = 0.02 λ is 0.4537 λ;
    * H–S (34) gives 0.4503 and Takakura's form (35) gives 0.4415.

    The engine supports Holley & Schnitzer's correction of Takakura's shift (test, within 15 % of the shift).
* **Qi, Miao, Hong, Tentzeris, IEEE TMTT 58, 3657 (2010)** (author copy https://tentzeris.ece.gatech.edu/TMTT10_Qi.pdf;
  the equations are images).
  * (22) "T0(s) = 0.0096 + 0.3183 × s": the peak normalised transmittance of a PEC slit by a modal expansion,
    s = λ/a = 55–260. VERIFIED.
  * Engine at s = 55 and 100: agrees to 5e-3 (test). That tolerance resolves only the slope 1/π (= 0.3183): the
    constant 0.0096 is 5e-4 (s = 55) and 3e-4 (s = 100) of the peak, below it, and the coefficients' last digit (±5e-5
    on the slope) is already 1.6e-4. So this comparison adds nothing beyond Harrington & Auckland and Holley &
    Schnitzer; it is kept as a third published modal computation (review B8 C16). The review measured engine − Qi =
    +0.0024 (s = 55) and −0.0023 (s = 100).
* **Harrington & Auckland**, IEEE TAP 28, 616 (1980). The DOI in the task (10.1109/TAP.1980.1142397) is a different
  paper; the correct DOI is 10.1109/TAP.1980.1142382 [error in earlier: the task's DOI]. Paper NOT FETCHED (closed).
  * The abstract (OpenAlex) says the "transmission width at resonance becomes 1/\pi wavelengths regardless of the
    actual slot width". VERIFIED.
  * The underlying report, Auckland & Harrington, RADC-TR-79-257 (DTIC AD-A078477, archive.org mirror), was obtained.
    Their "TE" = H along the slit. VERIFIED from the report:
    * (8-4) "Z/η0 = −1/(2z⁻¹cos kd + j(1 + z⁻²) sin kd)";
    * (8-7) "Za/η0 = λ0/(w[π − 2j ln(γk0w/8)])", γ = 1.781;
    * (8-8) "T = (4/η0)|Z|² Re{1/Za}";
    * p. 116 (PDF page 132 of the archive.org scan, re-checked 2026-11-04 on the rendered page; the text layer reads
      "l/w7r"): "These peaks approach a value of 1/wπ for small w which can be shown from the equivalent circuit."
      This is the source of the peak height λ/(πw) in the engine's test (review B8 C14).
  * Engine against this circuit at w = 0.02 λ: within 1.5 % at d = 0.1, 0.25 and 0.6 λ (test). The circuit holds for
    k0w ≪ 1.
  * Their Figs. 47–49 were read by eye (±0.1 in T). They give a peak ≈ 6.2 at w = 0.05 λ, against the engine's 6.40
    and the report's own 1/(πw) = 6.37. The reading is too coarse to test; not used.
* Kowarz, Appl. Opt. 34, 3055 (1995): NOT FETCHED (closed). It concerns scalar near-field diffraction and is not
  needed by the engine.

## 5. Narrow slit in a thin screen (`core.em.slit`)

* **Rayleigh, Phil. Mag. 43, 259 (1897)**; Scientific Papers IV, art. 227 (archive.org, public domain). The equations
  were read from rendered pages 293–296. VERIFIED:
  * (46), the Neumann slit: "ψ_m = e^{−ikr}/(γ + log(¼ikb)) · (π/(2ikr))^{½}";
  * (53), the Dirichlet slit: "ψ_p = −(k²b²x/2r)(π/(2ikr))^{½} e^{−ikr}";
  * pp. 295–296: "if R denote the electromotive intensity parallel to z, the condition at the face of the conductor
    is R = 0".

  The transmission per slit width derived from these (mine, also derived independently from the integral equation's
  one-term solution) is `rayleigh_narrow_transmission`:
  * TE: (π²/256)(kw)³;
  * TM: π²/(4kb[(γ + ln(kb/4))² + π²/4]).

  Engine at kw = 0.02: within 1e-3, and the error falls with kw (test).
* **Libelo & Bombardt, NOLTR 70-58 (1970)**, Interaction Note 106 (https://ece-research.unm.edu/summa/notes/In/0106.pdf;
  a scan without a text layer, read from rendered pages; re-checked 2026-11-04 in processing review B8). E along the
  slot, η = kw/2. Their only statement of accuracy (printed p. 29, PDF page 33) is relative to other results, not an
  error bound: "However, the higher order approximation indicates about 3% difference from the other results and this
  is not terribly significant, having as its source the numerical techniques used in the computer program." [error in
  earlier: this file quoted it elided as "accuracy … about 3%", which read as a stated accuracy; review B8 C13 (a)]
  * Table I values used (VERIFIED digits; printed p. 35, PDF page 39, for η ≤ 2.2): η = 0.8 0.2923; 1.0 0.6012;
    1.5 1.2307; 2.0 1.2061; 3.0 1.0001; 3.6 0.9490; 4.8 1.0699; 5.6 1.0363.
  * DIFFERS:
    * the engine agrees within 4 % for η ≥ 1.5;
    * the table lies above the engine by 12 % at η = 0.8 (0.2923 against 0.2606) and by 10 % at η = 1.0 (0.6012
      against 0.5454), more than their stated accuracy.
  * The engine's values are confirmed by an independent route: a piecewise-linear hat basis with the operator in its
    spectral form (the propagating part in the angle, the evanescent part in q = k cosh u), extrapolated in 1/N. It
    gives 0.2605 (η = 0.8), 0.5453 (η = 1.0) and 1.1352 (η = 2.2) against the engine's 0.2606, 0.5454 and 1.1354
    (test at kw = 1.6 and 4.4). The engine also tends to Rayleigh's limit.
  * The table's own normalisation is ½ηΣ|a_n|² (η = 0.80: Σ|a_n|² = 0.7307, T = 0.2923 = ½ · 0.8 · 0.7307; η = 2.00:
    1.2061 and 1.2061), whereas their eq. (130) prints "T(η) = ¼ η Σ_{n=1,3,...} |a_n|²". Their long-wave formulas
    follow the printed ¼, VERIFIED on the rendered p. 29: (131) "σ_t ≈ (ωc/E0²)|A1|² = (ηρ0/2)|a1|²", "|a1|² = π²η²/16",
    (132) "σ_t ≈ ρ0 π²η³/32 = ρ0 π²(2kρ0)³/256". With T = σ_t/(2ρ0) this is T → π²(kw)³/512, half the correct limit
    π²(kw)³/256 (Rayleigh's, derived here from his eq. 53 and independently by the review B8 from the static aperture
    field −ik√(b² − x²): P = π²k³b⁴/16); with the table's ½ the same chain gives the correct limit (mine). So the
    printed (130)–(133) carry a factor ½ error that the table does not (review B8 C13 (b)). Their Fig. 4 puts
    Seshadri's peak at ≈ 1.22–1.23 against the table's 1.26. Both are consistent with the table being a few percent
    high near its peak.
  * **Independent check (review B8, `reviews/archive/2026-11-04_internal_B8-charges-slit/s03_fdfd_thin_slit.py`, reproduced in
    its processing):** a finite-difference frequency-domain solver that uses nothing of the engine (5-point Helmholtz,
    stretched-coordinate PML, the zero-thickness screen between grid rows, exact discrete flux; N = 8, 16, 32, 64 cells
    per half-width, Richardson with the observed order 0.95–1.04). Extrapolated T: TE η = 0.8 0.2608, 1.0 0.5457,
    1.5 1.1824, 2.0 1.1841; TM η = 0.8 1.0143, 1.5 0.9826. Engine − FDFD: −0.09 %, −0.06 %, +0.03 %, +0.02 % (TE), 0.00 %
    (TM), within the FDFD's own spread between its observed-order and first-order extrapolations; the Libelo–Bombardt
    table − FDFD: +12.1 %, +10.2 %, +4.1 %, +1.9 %. The engine's test now takes the FDFD levels as the reference, with
    that spread as the tolerance, and keeps the table as a known-high reference (negative control); review B8 C13 (c).
    These are the first independent values for the thin-screen TM case.
* NOT FETCHED: Morse & Rubenstein, Phys. Rev. 54, 895 (1938) (the Mathieu-function solution; closed); Bouwkamp,
  Rep. Prog. Phys. 17, 35 (1954) (bot check and paywall); Brooker, J. Mod. Opt. 55, 423 (2008) (closed); an MSU thesis
  (access refused). No open exact table for H along a thin slit was found. The engine's thin-screen TM result is
  checked against Rayleigh's limit, by the waveguide modes at t = 0, which converge to the edge basis like 1/M
  (Richardson in 1/M agrees to 1e-3, test), and against the independent FDFD values above (η = 0.8, 1.5).

## 6. Sommerfeld's half-plane (`core.em.slit`)

**Source.** A. Sommerfeld, "Mathematische Theorie der Diffraction", Math. Ann. 47, 317–374 (1896),
doi:10.1007/BF01447273 (GDZ Göttingen scan, no text layer; read from page images).

* (5), p. 359: "u = e^{ikr cos ψ} (e^{iπ/4}/√π) ∫_{−∞}^{T} e^{−iτ²} dτ, T = √(2kr) cos(ψ/2)". VERIFIED.
* §8, pp. 366–367: case (a) electric vibration along the edge, "Z = 0"; case (b) magnetic, "∂Z/∂n = 0";
  "Das Azimuth φ werde von S aus gezählt … 0 < φ < 2π"; (3) "Z = u(φ′) − u(−φ′) im Falle (a), Z = u(φ′) + u(−φ′)
  … (b)". VERIFIED.
* p. 368: time factor "𝒵 = ℜe(e^{2πit/τ} Z)", i.e. e^{+iωt}. VERIFIED.
* Engine (mine, the complex conjugate for e^{−iωt}): U = e^{−ikρ cos ψ} F(−√(2kρ) cos(ψ/2)),
  F(a) = (e^{−iπ/4}/√π)∫_a^∞ e^{iτ²}dτ = ½ erfc(e^{−iπ/4}a).
* Far field, pp. 368–369: "(1/4π) cos[2π(r/λ − t/τ) + π/4] √(λ/r) {±1/cos((φ+φ′)/2) − 1/cos((φ−φ′)/2)}"; "Dabei
  gelten die oberen Zeichen im Falle a), die unteren im Falle b)". VERIFIED. The amplitude (1/4π)√(λ/r) equals
  1/(2√(2πkr)) (mine). This is `half_plane_edge_wave`, Keller's coefficient (Keller 1962 NOT FETCHED).
* Engine tests:
  * the Helmholtz equation, by fourth-order differences, to 1e-7;
  * the boundary conditions, to 1e-12 (TE) and 1e-6 (TM, one-sided differences);
  * the remainder after geometric optics and the edge wave falls by more than 20 per decade of kρ, i.e.
    O((kρ)^{−3/2});
  * the field on the shadow boundary is |u| = 0.5.

## 7. The modal method itself

* The method follows Harrington & Auckland's report (waveguide modes in the slit matched to the half-spaces) and
  Takakura's one-mode model; neither text is reproduced.
* The Galerkin equations, the TE operator after two integrations by parts, the decoupled A ± B systems and the screen's
  optical theorem P_t + P_b = −4π r_s cos θ Re R(q0) are the engine author's own derivation (mine). They are written
  in the module's docstring and tested:
  * the optical theorem to 1e-10, for three unequal slits, oblique incidence, thin and thick screens;
  * reciprocity k_z(q2)T(−q2; q1) = k_z(q1)T(−q1; q2) to 1e-9;
  * the correlation and direct quadratures of the operator agree to 1e-10;
  * the essential field continuity across the apertures and the conductor conditions;
  * Helmholtz by finite differences;
  * the quadrature field against the spectral far field, error O(1/(kr)).
