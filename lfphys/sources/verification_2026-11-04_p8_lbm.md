# lfphys source verification — 2026-11-04, plan item P8 (batch B7): 2-D flow by the lattice Boltzmann method

Purpose: every quotation and number used by `core.fluids.lbm` (and its tests `tests/test_lbm.py`,
`tests/test_lbm_benchmarks.py`), checked against the source text. Texts fetched on 2026-11-04 with plain HTTP requests
(no contact parameter, e-mail address or personal identifier was sent with any request); PDFs read with
`pdftotext -layout`, scanned pages on renders (`pdftoppm`). Status codes as in `verification_2026-10-23.md`:
VERIFIED (quoted) / DIFFERS (both given) / NOT FOUND / NOT FETCHED (closed text; what replaces it is said).

## 1. The DFG cylinder benchmark — Schäfer & Turek 1996

M. Schäfer, S. Turek (with F. Durst, E. Krause, R. Rannacher), "Benchmark computations of laminar flow around a
cylinder", in: Flow Simulation with High-Performance Computers II, Notes on Numerical Fluid Mechanics 52 (Vieweg 1996),
doi 10.1007/978-3-322-89849-4_39. The authors' PDF (TU Dortmund, `.../lsiii/cms/papers/SchaeferTurek1996.pdf`) is gone
from the live site (404); read from the Wayback Machine copy of that URL (text layer).

* Fluid: "The kinematic viscosity is defined as ν = 10−3 m2 /s, and the fluid density is ρ = 1.0 kg/m3." VERIFIED.
* Geometry (2D cases, Fig. 1 and text): "H = 0.41 m is the channel height and D = 0.1 m is the cylinder diameter";
  channel length "2.2m"; the cylinder 0.15 m above the bottom wall and 0.16 m below the top one, its front 0.15 m from
  the inlet (Fig. 1 labels "0.15m", "0.16m", "0.1m") — centre (0.2, 0.2). VERIFIED.
* "The Reynolds number is defined by Re = U D/ν with the mean velocity U (t) = 2U (0, H/2, t)/3"; "cD = 2Fw/(ρU²D),
  cL = 2Fa/(ρU²D)"; "The Strouhal number is defined as St = Df /U , where f is the frequency of separation."
  VERIFIED (the fractions spread over lines in the text layer).
* "outflow condition can be chosen by the user." VERIFIED (the engine: the anti-bounce-back pressure outlet).
* 2D-1: "U (0, y) = 4Um y(H − y)/H 2 , V = 0 with Um = 0.3 m/s, yielding the Reynolds number Re = 20". VERIFIED.
  Table 3 ("Results for steady test case 2D-1", columns cD, cL, La, ∆P): "lower bound 5.5700 0.0104 0.0842 0.1172",
  "upper bound 5.5900 0.0110 0.0852 0.1176". VERIFIED.
* 2D-2: "with Um = 1.5 m/s, yielding the Reynolds number Re = 100". VERIFIED. The quantities asked for: "maximum drag coefficient cDmax ,
  maximum lift coefficient cLmax , Strouhal number St" (text layer lines 182–183 of the Wayback copy; the same words
  for 3D-2, lines 309–310). VERIFIED (re-fetched 2026-11-04 in the processing of review B7, the
  same file byte for byte as the reviewer's). Table 4 ("Results for time–periodic test case 2D-2", columns cDmax,
  cLmax, St, ∆P): "lower bound 3.2200 0.9900 0.2950 2.4600", "upper bound 3.2400 1.0100 0.3050 2.5000". VERIFIED.

Engine results (tests; re-measured on GPU 0 on 2026-11-04 in the processing of review B7): 2D-1 with interpolated
walls, mean over two acoustic periods after 9 s: cD = 5.57904, cL = 0.010752 at 40 cells per diameter (5.57746,
0.010755 at 80; 5.58927, 0.010483 at 20); staircase walls at 20 cells: cD = 5.63667, cL = 0.011252 (outside: the
negative control). [error in earlier] The test's docstring gave 5.5799 / 0.01078 at 40 and 5.5784 / 0.01078 at 80
(review B7 L17). Settled values (one-period means after 24 s of a 30-s run, Ma 0.1; the start's ringing decays by
≈ 40 % per period, so a one-period mean at 9–15 s still carries up to ±0.007 depending on its phase): 5.5895 /
0.010504 at 20 cells, 5.5791 / 0.010770 at 40 — both inside. 2D-2 (block means of 0.005 s over 9–12 s, interpolated walls): at 20 cells St = 0.2990, cDmax =
3.330, cLmax = 0.979, cLmin = −1.016; at 40 cells St = 0.3009, cDmax = 3.248, cLmax = 0.980, cLmin = −1.016. St is
inside; cDmax and cLmax are outside (3.22–3.24, 0.99–1.01). [error in earlier] The test asserted the lift amplitude
(cLmax − cLmin)/2 = 0.998 against the bounds of cLmax, which the benchmark does not define, and attributed cLmax's
shift to the acoustic wave: the offset (cLmax + cLmin)/2 is −0.0185 at Ma 0.1 and −0.0185 at Ma 0.05 at 20 cells, so
it is not O(Ma²) (review B7 L9). Its cause is open (STATUS V41 p).

## 2. The driven cavity — Ghia, Ghia & Shin 1982

U. Ghia, K. N. Ghia, C. T. Shin, "High-Re solutions for incompressible flow using the Navier-Stokes equations and a
multigrid method", J. Comput. Phys. 48, 387–411 (1982). The paper: NOT FETCHED (paywalled). Its Tables I and II
are taken from two transcriptions found by searching for the numbers, which agree for Re = 100:

* GitHub gist `ivan-pi/3e9326d18a366ffe6a8e5bfda6353219` ("TABLE I / Results for $u$-velocity along Vertical Line
  through Geometric Center of Cavity"), Re = 100 column: y = 1.0000 … 0.0000 → "1.00000 0.84123 0.78871 0.73722 0.68717
  0.23151 0.00332 -0.13641 -0.20581 -0.21090 -0.15662 -0.10150 -0.06434 -0.04775 -0.04192 -0.03717 0.00000" at
  y = 1.0000, 0.9766, 0.9688, 0.9609, 0.9531, 0.8516, 0.7344, 0.6172, 0.5000, 0.4531, 0.2813, 0.1719, 0.1016, 0.0703,
  0.0625, 0.0547, 0.0000.
* Gist `ivan-pi/caa6c6737d36a9140fbcf2ea59c78b3c` ("TABLE II / Results for $v$-Velocity along Horizontal Line through
  Geometric Center of Cavity"; it notes "The velocity for Re = 400 and point (x,v) = (0.9063,-0.23827) is probably
  wrong" — not used), Re = 100: "0.00000 -0.05906 -0.07391 -0.08864 -0.10313 -0.16914 -0.22445 -0.24533 0.05454
  0.17527 0.17507 0.16077 0.12317 0.10890 0.10091 0.09233 0.00000" at x = 1.0000, 0.9688, 0.9609, 0.9531, 0.9453,
  0.9063, 0.8594, 0.8047, 0.5000, 0.2344, 0.2266, 0.1563, 0.0938, 0.0781, 0.0703, 0.0625, 0.0000.
* Second transcription (a project page, sites.google.com/view/sidrg, "u_re100 (u velocity at Re =100)=[1.0000 0.8412
  0.7887 0.7372 0.68717 0.2315 0.0033 -0.1364 -0.2058 -0.2109 -0.1566 -0.1015 -0.0643 -0.04775 -0.0419 -0.0371
  0.0000]" and "v_re100 … =[0.0000 -0.05906 -0.0739 -0.0886 -0.10313 -0.16914 -0.22445 -0.24533 0.05454 0.17527
  0.17507 0.16077 0.12317 0.1089 0.1009 0.0923 0.0000]"): the same numbers, partly rounded. AGREE.

Engine result (test): on 64², 128², 256² nodes the largest differences from the table are 0.0050 / 0.0052 / 0.0051
(u) and 0.0079 / 0.0088 / 0.0089 (v) of the lid speed: independent of the grid, so the difference from Ghia's 129²
multigrid solution itself (and not the compressibility: the profiles change by 2·10⁻⁴ from Ma 0.1 to 0.05, review B7
r10); Re = 125 against the Re = 100 columns: 0.033 (negative control). The test asserts 0.008 (u) and 0.012 (v).

Re = 1000 columns (used for the accuracy statement of review B7 L13; the same two gists, fetched again 2026-11-04
through the GitHub API): u at y = 1.0000 … 0.0000 "1.00000 0.65928 0.57492 0.51117 0.46604 0.33304 0.18719 0.05702
-0.06080 -0.10648 -0.27805 -0.38289 -0.29730 -0.22220 -0.20196 -0.18109 0.00000"; v at x = 1.0000 … 0.0000 "0.00000
-0.21388 -0.27669 -0.33714 -0.39188 -0.51500 -0.42665 -0.31966 0.02526 0.32235 0.33075 0.37095 0.32627 0.30353 0.29012
0.27485 0.00000". VERIFIED (equal to the reviewer's r12 arrays). The cavity at Re 1000 on 64² (cell Reynolds number
15.6, accepted) lies 0.017 (u) / 0.010 (v) of the lid speed off them, on 128² 0.007 / 0.011 (the reviewer's r12,
re-run in the processing).

## 3. TRT, the magic parameter, anti-bounce-back — Ginzburg, Verhaeghe & d'Humières 2008

(a) "Two-relaxation-time lattice Boltzmann scheme: about parametrization, velocity, pressure and mixed boundary
conditions", Commun. Comput. Phys. 3, 427–478 (2008); (b) "Study of simple hydrodynamic solutions with the
two-relaxation-times lattice Boltzmann scheme", Commun. Comput. Phys. 3, 519–581 (2008). Both open access at
global-sci.com (journal page numbers below).

* (a) p. 431, Eq. (2.4): "Λe = −(1/2 + 1/λe), Λo = −(1/2 + 1/λo), Λeo = ΛeΛo" with τ± = −1/λ±, i.e.
  Λeo = (τ+ − 1/2)(τ− − 1/2); "The BGK model [41] is a TRT sub-class with a single relaxation parameter τ = −1/λe =
  −1/λo"; viscosity (b) p. 524, Eq. (2.5): "ν = Λe/3". VERIFIED (the engine's tau+ = 3 nu + 1/2, tau- from Lambda).
* (b) p. 521: "Its particular value, Λeo = 3/16, enables the bounce-back to locate the prescribed slip velocity exactly
  midway the link"; Table 5, p. 540: "BB | Λeo = 3/16". (a) p. 449, Eq. (5.12) "Λeo = 3δq²/4", followed by "When
  δq² = 1/2 the solution reduces to Λeo = 3/16" — a misprint for δq = 1/2 (3 (1/2)²/4 = 3/16; read on a 250-dpi
  render). VERIFIED; viscosity independence (a) p. 448: "This explains why the components of the permeability tensor K
  are viscosity independent for any porous media when BB is applied and Λeo is fixed". VERIFIED.
* Bounce-back slip: (b) Table 4, p. 539 ("Exact solutions for Heff² − Hδ²…"): "BB | Heff² − Hδ² = (16/3)Λeo − 1".
  A parabola of width Heff in the channel H is the exact one shifted by (Heff² − H²) g / (8ν), i.e. the uniform slip
  (16Λ − 3) g / (24ν) in lattice units — the law the engine's test finds to round-off for TRT at six Λ and BGK at four τ
  (`test_bounce_back_slip_is_a_function_of_lambda_only`). VERIFIED (equivalent). (b) p. 522: the parallel-channel
  profiles "obtained with the Stokes and Navier-Stokes equilibrium coincide … including bounce-back".
* Anti-bounce-back ("PAB"): (a) p. 461, Eq. (6.2) with Table 9 (κ1 = −1) and Table 10 ("PAB: α(p) = −2"):
  f_q̄(r_b, t+1) = −f̃_q(r_b, t) + 2 e_q⁺(r_w) [+ an optional correction f^{p.c.(p)}]; e_q⁺ = t*_q [c_s² ρ + (3 j_q² −
  ||j||²)/(2ρ̂)] (Eq. 2.14, p. 433), t*_q = w_q/c_s². With j = ρu: 2 w_q ρ [1 + 9/2 (c_q·u)² − 3/2 u²], the engine's
  outlet rule. VERIFIED (equivalent). Differences: the paper takes ρ̂ = ρ0 in the non-linear term and offers the
  correction term; the engine uses ρ_out throughout and no correction. (a) p. 429: "So far a simple link-wise approach
  is the first-order accurate anti-bounce-back rule."
* Λeo = 1/4: (a) p. 429: "the particular value Λeo = 1/4 has remarkable properties for stability of mass-conservation
  equation" (the engine's dye uses Λ_g = 1/4). VERIFIED.

## 4. Moving walls and momentum exchange — Ladd 1994

A. J. C. Ladd, "Numerical simulations of particulate suspensions via a discretized Boltzmann equation. Part 1.
Theoretical foundation", J. Fluid Mech. 271, 285–309 (1994); read in the preprint arXiv:comp-gas/9306004 (preprint
pages; Greek letters and minus signs read on renders).

* Eq. (3.3), p. 16: "n_i(r + c_i, t + 1) = n_i'(r + c_i, t_+) + 2 a_1^{c_i} ρ u_b · c_i"; Eq. (2.11), p. 9:
  "a_1^1 = 1/6", "a_1^{√2} = 1/12" (= w_i/c_s² of D3Q19): the engine's f_i = f*_-i + 6 w_i ρ0 e_i·u_w (2 w_i/c_s² =
  6 w_i). VERIFIED (same sign convention). Boundary nodes "placed halfway along the links" (p. 15).
* Eq. (3.12), p. 19: "f(r + ½c_i, t + ½) = … = 2[n_i(r, t_+) − n_i'(r + c_i, t_+) − 2 a_1^{c_i} ρ u_b · c_i] c_i";
  "The forces and torques on the solid particle are obtained by summing f(r + ½c_i) and (r + ½c_i) × f(r + ½c_i) over
  all the boundary nodes". VERIFIED (the engine sums e_i (f_in + f_out) per link, the same quantity; torques about
  the obstacle's centre with the link's wall point as lever).

## 5. Not fetched (closed texts) and what replaces them

* Guo, Zheng & Shi, "Discrete lattice effects on the forcing term in the lattice Boltzmann method", Phys. Rev. E 65,
  046308 (2002): NOT FETCHED (APS 401; no open copy found). The forcing term and u = (Σ e f + F/2)/ρ are used as
  commonly stated; their split into the TRT symmetric and antisymmetric parts is the engine's own. Replaced by tests
  of the consequences: every collision adds exactly F to each node's momentum and nothing to its mass (balance to
  round-off), the body-force Poiseuille flow is the exact parabola with TRT 3/16, and the steady drag of a periodic
  array equals the body force on the fluid (1e-8).
* Bouzidi, Firdaouss & Lallemand, "Momentum transfer of a Boltzmann-lattice fluid with boundaries", Phys. Fluids 13,
  3452 (2001): NOT FETCHED (AIP 403; no open copy). The linear interpolation rules are used as commonly stated (module
  docstring). Replaced by the DFG 2D-1 result: inside both ranges with interpolation, outside with staircases.
* Qian, d'Humières & Lallemand, "Lattice BGK models for Navier-Stokes equation", Europhys. Lett. 17, 479 (1992):
  NOT FETCHED (paywalled). The D2Q9 weights 4/9, 1/9, 1/36 and c_s² = 1/3 are the standard ones; replaced by the
  closed-form tests (Poiseuille, Couette's start-up series, Taylor–Green decay at second order).
* Krüger et al., The Lattice Boltzmann Method: Principles and Practice (Springer 2017): NOT FETCHED (subscription);
  cited without section numbers (a preview note links "the anti-bounce-back approach" with a "Sect. 5.3.5", so the
  number 5.3.4 used in a draft was dropped). The anti-bounce-back rule is cited to Ginzburg et al. 2008a (§3).

## 6. Water at 1 atm — NIST WebBook (IAPWS-95, IAPWS 2008)

NIST Chemistry WebBook, SRD 69, "Isobaric Properties for Water" at 0.101325 MPa, 0.01–40 °C (whole degrees and the
triple point), 7 digits, fetched as tab-separated data (`fluid.cgi?Action=Data&ID=C7732185&Type=IsoBar&P=0.101325…`).
The page's references: "Wagner, W. ; Pruss, A. , The IAPWS Formulation 1995 for the Thermodynamic Properties of
Ordinary Water Substance for General and Scientific Use , J. Phys. Chem. Ref. Data , 2002, 31, 2, 387-535" with
"IAPWS R6-95, Revised Release …, 2016"; viscosity "Huber, M.L. ; … New International Formulation for the Viscosity of
H 2 O , J. Phys. Chem. Ref. Data , 2009, 38, 2, 101-125" with the "Release on the IAPWS Formulation 2008 for the
Viscosity of Ordinary Water Substance"; "The uncertainty in density of the equation of state is 0.0001% at 1 atm in
the liquid phase". VERIFIED (grepped in the page).

* 20 °C: "20.00000 0.1013250 998.2072 … 0.001001596" (temperature, pressure, density, …, viscosity). VERIFIED; the
  whole table is `lbm.WATER_1ATM`.
* IAPWS R12-08 itself (iapws.org, fetched): no value at 20 °C; Sect. 2.5: "The formulation reproduces the ISO
  recommended value of the viscosity at 20 oC (293.15 K) and standard atmospheric pressure … within the stated
  uncertainty of 0.17 % at 293.15 K". Its check table (Table 4) starts at 298.15 K ("298.15 | 998 | 889.735100") — at a
  density, not a pressure, so not comparable with the isobar. NOT FOUND (the 20 °C number).
* IAPWS R6-95(2018) (fetched): the density at 20 °C and 0.101325 MPa is not tabulated. NOT FOUND. Both numbers are
  therefore cited to the WebBook, which computes them from these formulations.

## 7. Air — U.S. Standard Atmosphere 1976

NOAA/NASA/USAF, U.S. Standard Atmosphere, 1976 (NASA-TM-X-74335), NASA NTRS 19770009539 (a scan; read on rendered
pages; printed page = PDF page − 16). The NTRS file ends with a reader's erratum note on Table 2's typos.

* p. 19, §1.3.11: "μ = β·T^{3/2}/(T + S) (51)", "In this equation β is a constant equal to 1.458 × 10⁻⁶ kg/(s · m ·
  K^{1/2}) and S is Sutherland's constant, equal to 110.4 K"; "basically from kinetic theory, but with constants derived
  from experiment". VERIFIED (Table 2 prints "S 110 K"; the erratum note: "It should be 110.4 Kelvin").
* p. 3: "The gas constant, R* = 8.31432 × 10³ N·m/(kmol·K)" (Table 2 on p. 2 prints the exponent as −3: the erratum
  note says the p. 3 value is the correct one). VERIFIED.
* p. 9, §1.2.4: "M0 is found to be 28.9644 kg/kmol". VERIFIED. Table 2: "P0 1.013250 × 10⁵ N/m² (or Pa)". VERIFIED.
* Table I (p. 52): sea level "0 0 288.150 15.000 288.150 1.01325 + 3 … 1.2250 + 0"; "−800 −800 293.350 20.200 293.350
  1.1131 + 3 … 1.3219". VERIFIED; the engine's ideal gas with these constants reproduces both densities to the four
  digits printed (test). The tabulated viscosity column was not read.

Values used: dry air at 20 °C and 101325 Pa: ρ = 1.204105 kg/m³, μ = 1.81341 × 10⁻⁵ Pa·s (computed from the
standard's equations). Not fetched: Lemmon et al. (2000, 2004) for air (the modern reference correlations); the
Sutherland expression has not been compared with them.

## 8. Numbers found here (not from a source)

* The bounce-back slip coefficient (16Λ − 3)/24: found numerically, then identified with Ginzburg et al. (b), Table 4
  (§3).
* The acoustic periods (``Flow2D.acoustic_period``: 4 L / c_s between a velocity inlet and an outlet, 2 L / c_s
  between two walls): checked against the measured ringing (1386.3 against 1385.6 steps, 692.83 against 692.82; test).
  The velocity inlet's transverse layer (0.0040 U at cell Re 1, 0.038 U at 10; test) and the plain-channel stability
  edges of the reviewer's r07 / r09 (review B7 L12), reproduced.
* The cell-Reynolds limits (25 closed, 10 with an inlet or outlet; stability edges, not accuracy), the acoustic period and amplitude of the channel,
  the collision's rounding bias (−8e-17 per node and step before the rest population closed the mass), the D2Q5
  numerical diffusion along the flow D − (τ_g− − 1/2)u² (test to 1e-6), the GPU/CPU rates: measurements of this batch,
  recorded in the module (`RE_CELL_MAX_OPEN`, docstring, `RATES`).
