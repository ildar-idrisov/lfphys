# lfphys source verification — 2026-11-04, plan items P1 and P14.8 (batch B8): the Mie series, the rainbow, water

Purpose: every formula, quotation and number used by `core.optics.mie`, `core.optics.mie_debye`, `core.optics.mie_poly`,
`theories.approx.rainbow`, the water and Sun block of `core.data`, their tests (`tests/test_mie.py`,
`tests/test_mie_debye.py`, `tests/test_mie_water.py`, `tests/external/test_ext_mie_miepython.py`) and the visualization
`v17_mie_scattering`, checked against the source text where it could be obtained. Texts fetched on 2026-11-04 and kept
only outside the repository: PDFs converted with `pdftotext -layout`; Wiscombe's scanned report also read from page
images rendered at 200 dpi (its OCR text is unreliable). No contact parameter or personal identifier was sent with
any request. Status codes as in `verification_2026-10-23.md`: VERIFIED (quoted) / DIFFERS (both given) / NOT FOUND /
NOT FETCHED (what replaces it is said).

Licence-clean rule (`../../AGENTS.md` §3 rule 8): no third-party Mie code was read for the implementation. Wiscombe's
report contains the Fortran listings of MIEV0/MIEV1 (Appendices I–III); only its text, its Eq. (50) and its tables of
results were used. miepython was used only in the comparison suite; only its documentation (API pages, "Algorithm"
notebook text) was read, for its conventions.

## 1. The Mie series

* Bohren & Huffman, *Absorption and Scattering of Light by Small Particles* (Wiley, 1983), ch. 4 (Eqs. 4.37–4.53, 4.61,
  4.62, 4.74, 4.76, 4.80, 4.82, 4.88; 3.16). NOT FETCHED (a copyrighted book without a lawful free copy found). The
  formulas used (module docstring of `core.optics.mie`) are the standard textbook ones; each is checked by an
  independent route rather than against the printed text: the coefficients against Arb (python-flint) evaluations of
  B&H's form with j_n, y_n (`test_coefficients_against_arb`, every coefficient within 3.2e-13 of the largest at
  x = 1000) and against Wiscombe's published results (§2); c_n, d_n and the vector spherical harmonics against the
  boundary conditions at r = a (tangential E, H and normal D continuous to <= 4e-11), the far field (E_s -> e^{ikr}/(-ikr)
  (cos φ S2, -sin φ S1), deviation falling as 1/kr), the incident wave's own expansion (equal to e^{ikz} x̂ to 1e-12),
  and the Joule heat of the internal field (= Q_abs of the series to 1e-9). The sign convention exp(-iωt), m = n + iκ
  is the one of `core.optics.interfaces`.
* The accuracy statement (after review B8-mie, M1; tests, not a source): the engine is backward stable in x — on the
  peaks of narrow resonances (m = 1.333, x ≈ 1000, widths Γ = 6e-4 … 1.5e-11 in x) its error stays below the change of
  the exact coefficient under a one-ulp change of x, reaching 6.4e-3 of the largest coefficient at Γ = 1.5e-11 — and
  `mie.coefficient_bound` states |a_n − exact| ≤ u (4 N max|a| + 8 x |da_n/dx|), measured with factors 1 and 4 over 26
  cases including five peaks (`tests/test_mie.py`). [error in earlier] "every coefficient within 2e-11 of the largest,
  x ≤ 2e4" (this record and the module) does not hold on such peaks.
* Fejér's second quadrature rule (`mie.fejer2`, the angular integrals; review B8-mie, M2): J. Waldvogel, "Fast
  construction of the Fejér and Clenshaw-Curtis quadrature rules", BIT Numer. Math. 46, 195–202 (2006); the author's
  copy fetched from people.math.ethz.ch/~waldvoge/Papers/fejer.pdf on 2026-11-04 (pdftotext). Quoted: "Fejér's second
  rule [4] is obtained by omitting the nodes x0 = 1 and xn = −1 and using the interpolating polynomial of degree
  n − 2", the nodes "xk := cos ϑk , ϑk := k π/n" (Eq. 2.1), and Eq. (2.3) "wkf2 = (4/n) sin ϑk Σ_{j=1}^{[n/2]}
  sin(2j − 1)ϑk/(2j − 1)" (as extracted: "wkf 2 = sin ϑk ... 4 ... n ... X sin(2j − 1)ϑk ... 2j − 1"); on accuracy:
  "for n=128 the relative error of the weights of Fejér's second rule is at most 6 eps ... In this range the
  classical algorithm loses about 2 bits of accuracy compared to the DFT algorithm". VERIFIED → `mie.fejer2` (the
  explicit sum, its sine arguments reduced in integers; measured ≤ 48 u at n = 4000). Why not Gauss–Legendre: numpy's
  docstring (2.4.6, grepped in the image by the reviewer): "The results have only been tested up to degree 100,
  higher degrees may be problematic"; measured here, numpy's and scipy's weights near ±1 are off by 1e-8 at n = 1120
  and 8e-7 at n = 3600, also when recomputed from the three-term recurrence at the rounded nodes (the weight formula's
  sensitivity to the node's rounding grows like n³ u).
* BHMIE's printed example (B&H Appendix A). NOT FETCHED (the book). Replaced by Wiscombe's eight test cases (§2), which
  cover x = 10–5000 with absorbing and non-absorbing spheres.
* The Wronskians used: j_n y_n' − j_n' y_n = 1/z² (so ψχ' − χψ' = −1, ψξ' − ξψ' = i, ξ^(2)ξ^(1)' − ξ^(1)ξ^(2)' = 2i):
  standard; checked through c_n, d_n by the boundary conditions and through the Debye sum identity (§3).
* DLMF §10.49 (dlmf.nist.gov/10.49, fetched 2026-11-04): Eq. 10.49.1 "a k ( n + 1 2 ) = ( n + k ) ! / ( 2 k k ! ( n − k ) ! ),
  k = 0 , 1 , … , n" and Eqs. 10.49.6–7 "h n (1) ( z ) = e i z ∑ k = 0 n i k − n − 1 a k ( n + 1 2 ) / z k + 1",
  "h n (2) ( z ) = e − i z ∑ k = 0 n ( − i ) k − n − 1 a k ( n + 1 2 ) / z k + 1" (as extracted from the HTML). VERIFIED →
  `mie._hankel_psi_pair` (the start of D_n where |mx| > N²): ξ^(1)_n = (−i)^(n+1) e^{iz} Σ_k (i/(2z))^k (n+k)!/(k!(n−k)!).
* Lentz, Appl. Opt. 15, 668 (1976) (the continued fraction for J_{n−1/2}/J_{n+1/2}) and Thompson & Barnett, J. Comput.
  Phys. 64, 490 (1986) (the modified Lentz algorithm). NOT FETCHED (paywalled). The fraction is the classical one of the
  recurrence J_{ν−1}/J_ν = 2ν/z − J_{ν+1}/J_ν; its value is checked by the coefficients' references above.
* Mie, Ann. Phys. 330, 377 (1908): cited as the origin; NOT FETCHED.

## 2. Wiscombe's report — the number of terms and the published test results

W. J. Wiscombe, "Mie Scattering Calculations: Advances in Technique and Fast, Vector-Speed Computer Codes",
NCAR/TN-140+STR (June 1979; edited 1996), doi 10.5065/D6ZP4414. The NCAR OpenSky page answers with a bot challenge;
the PDF was fetched from the Internet Archive's copy of NCAR's former library URL
(web.archive.org/web/2016/http://nldr.library.ucar.edu/collections/technotes/asset-000-000-000-290.pdf; 98 pages,
"Title: NCAR/TN-140+STR Mie Scattering Calculations..."). OpenSky's metadata gives its licence as CC BY-NC 4.0.

* Eq. (50), p. 38 (OCR, checked on the page image): "Nmax ≈ x + 4x^1/3 + 1 (0.02 ≤ x ≤ 8); x + 4.05x^1/3 + 2
  (8 < x < 4200); x + 4x^1/3 + 2 (4200 ≤ x ≤ 20,000)". VERIFIED → `mie.n_wiscombe` (the engine adds 16 terms of margin).
* p. 48: "Sample results from MIEV1, rounded to 6 significant digits, are presented in Appendix III. Users should
  reproduce these results before attempting to apply MIEV0 or MIEV1. There are 8 cases: x = 10, 100, 1000, and 5000;
  for each x, m = 1.5 and m = 1.5 - 0.1 i." VERIFIED.
* Appendix III, pp. A22–A29 (read from the page images; "REFRACTIVE INDEX = 1.500 -0.100E+00" for the absorbing cases,
  i.e. his m = n − iκ, the exp(+iωt) convention: his S1, S2 are the complex conjugates of the engine's, his m the
  conjugate of ours — the test reproduces every value with exactly this mapping). VERIFIED values used in
  `tests/test_mie.py::WISCOMBE` (Q_ext, Q_sca, g, S1(0°), S1(90°), S2(90°), S1(180°)):
  x = 10, m = 1.5: "EXTINCTION 2.881999 SCATTERING 2.881999", "ASYMMETRY FACTOR = 0.742913", S1(0) "0.720500E+02
  0.416662E+01", S1(90) "0.785066E-01 0.306855E+01", S2(90) "-0.187329E+01 0.232789E+01", S1(180) "0.432164E+01
  0.486827E+01"; x = 100: 2.094388, 0.818246, S1(0) "0.523597E+04 -0.367988E+03", S1(90) "0.224945E+02 0.396468E+00",
  S2(90) "0.162341E+02 -0.155243E+02", S1(180) "0.407669E+02 0.517546E+02"; x = 1000: 2.013945, 0.827882, S1(0)
  "0.503486E+06 -0.836182E+04", S1(90) "0.425817E+01 -0.156554E+03", S2(90) "-0.157646E+03 -0.174914E+02", S1(180)
  "0.565233E+03 0.150209E+04"; x = 5000: 2.008650, 0.829592, S1(0) "0.125541E+08 -0.672294E+05", S1(90) "0.762792E+03
  0.466846E+03", S2(90) "0.384561E+03 -0.433204E+03", S1(180) "-0.145625E+05 -0.507155E+04"; x = 10, m = 1.5 − 0.1i:
  "2.459791 1.235144 1.224646", 0.922350, S1(0) "0.614948E+02 -0.317799E+01", S1(90) "0.135105E+01 0.417250E+00",
  S2(90) "-0.102255E+01 0.791253E+00", S1(180) "0.149343E+01 0.296366E+00"; x = 100: "2.089822 1.132134 0.957688",
  0.950392, S1(0) "0.522455E+04 -0.261694E+03", S1(90) "0.119224E+01 0.153732E+02", S2(90) "-0.850854E+00
  -0.466332E+01", S1(180) "-0.954952E+01 -0.355581E+01"; x = 1000: "2.019703 1.106932 0.912770", 0.950880, S1(0)
  "0.504926E+06 -0.721499E+04", S1(90) "0.558595E+02 -0.143671E+03", S2(90) "-0.116307E+02 0.460706E+02", S1(180)
  "0.994571E+02 0.221736E+02"; x = 5000: "2.006775 1.099193 0.907582", 0.950650, S1(0) "0.125423E+08 -0.666472E+05",
  S1(90) "0.543810E+03 0.546205E+03", S2(90) "-0.187405E+03 -0.146093E+03", S1(180) "-0.777833E+02 0.503522E+03".
  The engine reproduces all of them within half a unit of the printed digit.
* Table 3, p. 28 ("Values of Q_ext in the small-particle limit, as given by Mie theory and by Eq. (40) ...", column
  "Exact", read from the page image): x = 0.02: 7.67805e-8 (1.5 − 10⁻⁶i), 1.27355e-7 (1.95 − 10⁻⁶i), 3.77659e-7
  (1.95 − 10⁻⁵i); x = 0.04: 1.12179e-7 (1.05 − 10⁻⁶i), 6.70403e-7 (1.5 − 10⁻⁶i), 8.57008e-6 (1.5 − 10⁻⁴i), 7.16259e-6
  (1.95 − 10⁻⁴i); x = 0.08: 3.28478e-7, 9.61292e-6, 2.54547e-5, 3.67336e-5 (same order of m); x = 0.20: 5.25263e-3
  (1.05 − 0.01i), 5.78539e-1 (1.05 − i), 3.90548e-3 (1.95 − 0.01i), 2.58637e-1 (1.95 − i). VERIFIED →
  `tests/test_mie.py::TABLE3`, all reproduced within half a unit.

## 3. The Debye series

* Debye, Phys. Z. 9, 775 (1908); van de Hulst, *Light Scattering by Small Particles* (Wiley 1957), §12.35; Hovenac &
  Lock, J. Opt. Soc. Am. A 9, 781 (1992); Nussenzveig, *Diffraction Effects in Semiclassical Scattering* (Cambridge
  1992). NOT FETCHED (books and a paywalled paper). The formulas of `core.optics.mie_debye` were derived in this batch
  from the boundary condition u'/u (outside) = β u'/u (inside) (β = 1/m for a_n, m for b_n, read off the Mie formulas
  themselves) and the multiple-reflection sum (module docstring). The derivation is checked by the closed-form sum
  against the Mie coefficients of the independent route (within u (1000 N + 32 x|da_n/dx|): ~1e-15 at x = 10, ~1e-12
  at 1000, up to 1e-9 at 2e4 for m = 0.75; `tests/test_mie_debye.py`), the partial sums, the reflection limits, and the
  p = 2 term against Airy (§4).
* Hovenac & Lock's report version, "Assessing the contributions of surface waves and complex rays to far-field Mie
  scattering by use of the Debye series", NASA CR-187191 (NTRS 19920009025), fetched from ntrs.nasa.gov on 2026-11-04
  (review B8-mie found it); Appendix A read from page images (pp. 40–43 of the report): "The time dependence of the
  waves is taken to be e^{-iωt}" (p. 40); (A18) T21 = −(n1/n2) 2i/D, (A19) R22, (A20) α = 1 (TE), n1/n2 (TM),
  (A21) β = n1/n2 (TE), 1 (TM), (A22) D (p. 42); (A25) T12 = −2i/D, (A26) R11, and (A29), whose left side is "the Mie
  far-field partial wave scattering amplitudes a_ℓ (TM amplitude) and b_ℓ (TE amplitude)", = ½[1 − R22 −
  T21T12/(1 − R11)] = ½[1 − R22 − Σ_{p=1}^∞ T21 (R11)^{p−1} T12] (p. 43); on localisation (text, grepped): "When x >> 1, these fractions
  are approximated by the Fresnel coefficients for oblique incidence on a flat interface with either the TE or TM
  polarization." VERIFIED (the printed forms and the time convention). The term-by-term identification of the engine's
  R22, R11, T21T12 with (A18)–(A26) (β_engine = m for b_n, TE; 1/m for a_n, TM) and the Fresnel limits at x = 2000 are
  the reviewer's check (review B8-mie, s03), not re-derived here; the engine's own evidence is the sum identity above.
* The convergence of the series in p (review B8-mie, M5; engine computations): |R11| ≤ 1 for real m; for an absorbing
  m near 1 the tunnelling orders have |R11| > 1 (4.8 for m = 1 + 1e-6 i at x = 100), the series diverges there and the
  closed form is its continuation (`mie_debye.coefficients` flags those orders). D_n p_n = ψ_n'(mx)/ξ_n(mx) is formed
  without D_n, whose downward recurrence loses relative accuracy at its poles (the zeros of ψ_n): [error in earlier]
  single orders missed a_n by up to 5e-9 of the largest coefficient (m = 2.88, x = 6411).

## 4. The rainbow: Descartes and Airy

* Descartes' condition cos² i = (m² − 1)/(p² − 1) and the deviation D_p = (p − 1)π + 2i − 2pr: standard ray optics
  (van de Hulst 1957, ch. 13; NOT FETCHED); checked numerically as the extremum of the deviation and by the ray paths'
  exit directions (`tests/test_mie_debye.py`). Values computed by the engine (not quoted from a source): m = 4/3:
  137.970° (p = 2), 129.022° (p = 3); water at 10 °C and 550 nm in vacuum (n_medium = 1, m = 1.335401): 138.270°,
  128.482°. In air the relative index is smaller by n_air: for an illustrative n_air − 1 = 2.77e-4 (not taken from a
  source; the Ciddor 1996 equations were not obtained — NIST's documentation page gives them only as images) the bows
  move to 138.216° and 128.578° (review B8-mie s11, reproduced). [error in earlier] the angles were quoted without
  saying that the medium is vacuum.
* Airy, Trans. Camb. Phil. Soc. 6, 379 (1838). NOT FETCHED. The intensity |S_j|² = 2π|ε_j|²(b_R/sin θ_R) x^(7/3)
  (2/|h|)^(2/3) Ai²(−z), z = sign(h)(2/|h|)^(1/3) x^(2/3)(θ − θ_R), was derived here from the cubic phase of the rainbow
  wavefront and normalised by the two classical rays (checked: its average far on the bright side equals them within
  1 %); its maxima at the zeros of Ai' (scipy.special.ai_zeros). The Debye p = 2 maximum (m = 1.333, s polarisation)
  lies beyond Descartes' angle by 0.977°, 0.4735°, 0.2131° at x = 1000, 3000, 10⁴ against Airy's 0.9914°, 0.4766°,
  0.2136° (engine computations).

## 5. Water: IAPWS R9-97 and SR6-08

* IAPWS R9-97, "Release on the Refractive Index of Ordinary Water Substance as a Function of Wavelength, Temperature
  and Pressure" (Erlangen, September 1997), fetched from iapws.org/technical-guidance/release/Rindex.download. Its
  terms: "Publication in whole or in part is allowed in all countries provided that attribution is given to the
  International Association for the Properties of Water and Steam". Reference constants "T* = 273.15 K", "ρ* = 1000
  kg ∙ m-3", "λ* = 0.589 µm"; Eq. (1) (layout extracted as "n2 −1 / n2 +2 (1 / ρ ) = a0 + a1 ρ + a 2T + a3 λ 2T +
  a 4 / λ 2 + a5/(λ2 − λUV2) + a6/(λ2 − λIR2) + a 7 ρ 2"); Table 1: "a0 = 0.244 257 733", "a1 = 9.746 344 76 ∙ 10-3",
  "a2 = -3.732 349 96 ∙ 10-3", "a3 = 2.686 784 72 ∙ 10-4", "a4 = 1.589 205 70 ∙ 10-3", "a5 = 2.459 342 59 ∙ 10-3",
  "a6 = 0.900 704 920", "a7 = -1.666 262 19 ∙ 10-2", "λ UV = 0.229 202 0", "λ IR = 5.432 937". VERIFIED →
  `IAPWS97_RINDEX_*`. Range (Sec. 4): "-12 °C ≤ t ≤ 500 °C", "0 kg ∙ m-3 ≤ ρ ≤ 1060 kg ∙ m-3", "0.2 µm ≤ λ ≤ 1.1 µm".
  Uncertainty (Table 2): "0.40 to 0.70 5 to 60 ambient liquid 1.5 ∙ 10-5". Sec. 6: "If the densities are calculated
  from the IAPWS Formulation 1995 [2] to one part in 106, and the coefficients in Table 2 are carried to the number of
  significant digits stated, the formulation should produce the values listed in Table 3 to within one unit in the
  least significant digit." Table 3, 0.1 MPa, 0 °C: "0.226 50 ... 1.394 527", "0.589 00 ... 1.334 344",
  "1.013 98 ... 1.326 135". VERIFIED → `IAPWS97_RINDEX_CHECK_0C_01MPA`; reproduced within 0.4 units with the density of
  SR6-08 (below).
* IAPWS SR6-08(2011), "Revised Supplementary Release on Properties of Liquid Water at 0.1 MPa" (Plzeň, September 2011),
  fetched from iapws.org (LiquidWater.download); same publication terms. "where R = 461.51805 J·kg−1·K−1, TR = 10 K",
  "where T is temperature in K, Ta = 593 K, and Tb = 232 K"; Eq. (2) and Table 1 rows i = 5–10 (a_i, b_i, n_i, m_i)
  as in `core.data`; range "253.15 K ≤ T ≤ 383.15 K"; "a relative uncertainty of 0.0001 % for specific volume (or
  density)" in the stable region; Sec. 2.4: "vatm = v0 + vp0 (patm − p0)... agrees in relative terms within 0.04×10−6
  with the IAPWS Formulation 1995"; Table 8 densities "997.068 360" (260 K), "997.047 013" (298.15 K), "957.009 710"
  (375 K). VERIFIED → `IAPWS08_*`, reproduced within half a unit. Sec. 2.3 (fetched again 2026-11-04, grepped):
  "At some temperatures within this range, the equilibrium phase at 0.1 MPa is a solid (below approximately 273.15 K)
  or a vapor (above approximately 372.76 K); at these conditions Eqs. (1)-(3) describe the properties of the
  metastable liquid phase", and "No uncertainty estimate is given for the metastable regions". VERIFIED →
  `water_index`'s docstring: 100–110 °C at 0.1 MPa is the metastable liquid ([error in earlier] it said "the stable
  range of both"; review B8-mie, M13).
* Absorption of water in the visible: not used (the releases give the real part only); no number is quoted for it.

## 6. The Sun and the colours

* Prša et al., "Nominal values for selected solar and planetary quantities: IAU 2015 Resolution B3", AJ 152, 41
  (2016), arXiv:1605.09788v1: "T⊙N = 5772 K"; "yielding T ⊙ = 5772.0 ± 0.8 K". VERIFIED → `SUN_TEFF_NOMINAL_K`.
  Sunlight as a black body at this temperature is a stated approximation (no lines, no atmosphere).
* The CIE 1931 functions and sRGB: `tools.colour` (verified there, 2026-10-28).

## 7. The comparison library

* miepython 3.3.0 (PyPI; MIT, its LICENSE.txt "Copyright 2017-2021 Scott Prahl ... Permission is hereby granted,
  free of charge"). Documentation pages fetched from miepython.readthedocs.io (API pages of `coefficients`,
  `efficiencies_mx`, `S1_S2`, `i_par`, `normalization_factor`; the notebook "Mie Scattering Algorithms"):
  `efficiencies_mx`: "Complex refractive index of the sphere, defined as m = n - ik"; `coefficients`: "If the
  imaginary part of the refractive index is positive, it is automatically corrected to its conjugate value to ensure a
  valid input."; `S1_S2`: "The normalization is controlled by norm and should be one of ['albedo', 'one', '4pi',
  'qext', 'qsca', 'bohren', or 'wiscombe']". VERIFIED. Measured (not documented): its a_n, b_n equal the engine's,
  its S1, S2 with norm "wiscombe" are their complex conjugates, and it sums Wiscombe's N terms without margin
  (`tests/external/test_ext_mie_miepython.py`). Its coefficients carry an error of about the same size at every order
  — ~3e-13 of the largest at x = 100, ~1e-12 at 1000, ~1.1e-9 at 10⁴, up to 3e-8 near n ≈ x (measured against 40-digit
  references; [error in earlier] "its top orders lose accuracy", review B8-mie, M8).
* numba 0.68.0 (BSD-2-Clause, with third-party notices: MIT, BSD-3-Clause (NetworkX), PSF), llvmlite 0.50.0
  ("BSD-2-Clause AND Apache-2.0 WITH LLVM-exception"): read from the installed dist-info licence files in a throwaway
  container on 2026-11-04.
