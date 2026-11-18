# Magnus lift C_L(S, Re) search for E03 (smooth sphere, Re 1e3-1e4, S 0.3-1)

Started 2026-11-18. Files under src/magnus/<short_name>/. sha256 = first 16 hex.

## Log

### S1. Muto, Tsubokura, Oshima 2012 — OBTAINED
- Citation: M. Muto, M. Tsubokura, N. Oshima, "Negative Magnus lift on a rotating sphere at around the critical Reynolds number", Phys. Fluids 24, 014102 (2012), doi:10.1063/1.3673571
- URL: https://eprints.lib.hokudai.ac.jp/dspace/bitstream/2115/49222/1/PoF24-1_014102.pdf (HUSCAP, hdl 2115/49222)
- File: src/magnus/muto2012/PoF24-1_014102.pdf, sha256 c221ffbf81f4923d; text PoF24-1_014102.txt (pdftotext -layout)
- Access: author-accepted/published PDF in institutional repository; rights: "Copyright 2012 AIP. This article may be downloaded for personal use only." (no CC licence)
- Method: LES (dynamic Smagorinsky), unstructured FV, sphere fixed, rotation imposed by wall velocity. Re = 1.0e4, 2.0e5, 1.14e6; Gamma = 0, 0.2, 1.0 (plus 0.1, 0.5, 0.8 at critical Re only, in Fig. 7).
- Spin definition (txt line 154; checked on rendered page 014102-2): printed "Γ = D_p ω / U_0", but the same sentence calls it "the ratio of the circumferential velocity to the incoming flow velocity" (circumferential velocity would be ω D/2). INCONSISTENT AS PRINTED — formula says ωD/U (=2S), words say ωr/U (=S). Must be resolved (Fig. 7 overlays Tsuji et al. data on the same axis; Tsuji's definition decides).
- C_D = F_D/(ρ U0² A/2), A = projected area (line 231); C_L = F_L/(ρ U0² A/2) (line 344).
- TABLE I (page 014102-9, txt lines 440-461; minus signs are lost in the pdftotext output, signs below checked against the rendered page). Re = 1.0×10^4 column, mean (s.d.):
  - no rotation: C_D 0.046 (0.016) [sic: printed 0.046, Fig.2/validation implies ~0.4 — likely a typo in the paper]; C_Ly −0.004 (0.037); C_Lz 0.005 (0.036)
  - Γ=0.2: C_D 0.474 (0.011); C_Ly −0.002 (0.021); C_Lz 0.167 (0.029)
  - Γ=1.0: C_D 0.661 (0.054); C_Ly 0.064 (0.052); C_Lz 0.301 (0.096)
  - (C_Lz is the Magnus lift component in the table; text line 344 says lift "acting in the y-direction" — another labelling inconsistency.)
- No torque/spin-decay coefficient.

### S2. Zhou, Zhang, Xu 2022 (Water) — OBTAINED, measured, Re 610–3472 (IN TARGET RANGE)
- Citation: S. Zhou, G. Zhang, X. Xu, "Experiments on the Drag and Lift Coefficients of a Spinning Sphere", Water 14(17), 2593 (2022), doi:10.3390/w14172593
- URL: https://mdpi-res.com/d_attachment/water/water-14-02593/article_deploy/water-14-02593.pdf (www.mdpi.com returned HTTP 403 to this client; Semantic Scholar lists OA status GOLD, licence CC BY)
- File: src/magnus/zhou2022/water-14-02593.pdf, sha256 d0ba4eb98acdba87; text water-14-02593.txt. The PDF carries an overlapping "FOR PEER REVIEW" layer, so pdftotext has duplicated/garbled lines on pp. 3-12; tables extract cleanly; Eq. 8 checked on rendered p. 7.
- Licence: CC BY 4.0 (stated on p. 1, txt lines ~49-58).
- Method: MEASUREMENT. Glass spheres (ρs = 2390 kg/m^3, D = 2.5, 4, 6, 8 mm) released from a rolling track ("orbit") above a 0.2×0.2×0.5 m plexiglass water tank (ρ = 1000 kg/m^3); spin comes from rolling on the track (same mechanism as our chute!). High-speed camera 400 fps; u_s and β (angle of velocity to gravity) from the trajectory, Ω from surface marks. Quasi-steady force balance (Eqs. 4–7): C_L = (4D/3)((ρs−ρ)/ρ) g sinβ / u_s^2, C_D = same with cosβ. Assumes zero acceleration, no added mass/history; spin decay during the measurement not reported.
- Spin parameter: Rr = DΩ/u_r (txt line 50) = 2·S. Checked numerically: row 1, 0.0025·38.380/0.262 = 0.3662 → printed 0.366. Re = u_r D/ν (line 52; ν ≈ 1e-6: 0.262·0.0025/1e-6 = 655 → printed 655.000).
- C_L, C_D reference: (π/4)D^2 · ½ρ(u−u_s)^2 (Eqs. 2, 3, txt lines ~497-505).
- TABLE 2 "Experimental results" (p. 7, txt lines 570-596), copied exactly (No., D mm, us m/s, Ω rad/s, Rr, Re, ClΩ, CdΩ); S = Rr/2 added by me in brackets:
  1  2.5 0.262  38.380 0.366  655.000 0.212 0.627  [S 0.183]
  2  2.5 0.244  59.890 0.614  610.000 0.349 0.677  [S 0.307]
  3  4   0.374  13.956 0.149 1496.000 0.132 0.502  [S 0.0745]
  4  4   0.361  20.350 0.225 1444.000 0.098 0.550  [S 0.1125]
  5  4   0.311  65.130 0.838 1244.000 0.364 0.657  [S 0.419]
  6  4   0.315  77.920 0.989 1260.000 0.339 0.648  [S 0.4945]
  7  6   0.417  34.889 0.502 2502.000 0.261 0.570  [S 0.251]
  8  6   0.386 223.290 3.471 2316.000 0.318 0.657  [S 1.7355]
  9  6   0.385  90.250 1.406 2310.000 0.379 0.629  [S 0.703]
  10 6   0.379  90.250 1.429 2274.000 0.378 0.657  [S 0.7145]
  11 6   0.376 185.140 2.954 2256.000 0.331 0.697  [S 1.477]
  12 6   0.376  90.250 1.440 2256.000 0.376 0.674  [S 0.720]
  13 6   0.374  87.220 1.399 2244.000 0.393 0.672  [S 0.6995]
  14 6   0.366 195.380 3.203 2196.000 0.402 0.708  [S 1.6015]
  15 6   0.366 163.280 2.677 2196.000 0.325 0.745  [S 1.3385]
  16 6   0.359 177.930 2.974 2154.000 0.356 0.768  [S 1.487]
  17 6   0.358 167.470 2.807 2148.000 0.329 0.783  [S 1.4035]
  18 6   0.353 186.660 3.173 2118.000 0.371 0.792  [S 1.5865]
  19 6   0.345 115.336 2.006 2070.000 0.449 0.800  [S 1.003]
  20 8   0.434 103.980 1.917 3472.000 0.358 0.682  [S 0.9585]
  21 8   0.428 104.670 1.956 3424.000 0.353 0.709  [S 0.978]
  22 8   0.419  98.640 1.883 3352.000 0.353 0.750  [S 0.9415]
- Fit, Eq. (8) (p. 7, txt line 563; checked on rendered page), valid "0 < Re < 3500 and 0 < Rr < 12":
  C_LΩ = 0.365(1 + e^(2.229−6.5Rr))^(−1) + [Rr − 0.365(1 + e^(2.229−6.5Rr))^(−1)] e^(−0.075(0.5Rr)^0.4 Re^0.71),  R^2 = 0.873
  (Abstract: "when 1 < Rr < 12, the limit value of the lift coefficient is 0.37".)
- Drag with spin (p. 10, txt lines 1006, 1010): Eq. (17) CdΩ = (0.989 + 0.482Rr − 0.093Rr^2) Cd (R^2 = 0.86), 0 < Rr < 2.5, 0 < Re < 3500; Eq. (18) CdΩ = 2.117 Rr^−0.33 Cd (R^2 = 0.823), 2.5 < Rr < 25; non-spinning Cd Eq. (16) Cd = 24/Re + 2.5/√Re + 0.4.
- No torque / spin-decay data.
- My checks: (a) row 7 internal consistency: tan(24.552°) = 0.4568 vs ClΩ/CdΩ = 0.261/0.570 = 0.4579; CdΩ recomputed from Eq. 7 with D=6 mm, u=0.417, β=24.552° → 0.5706 (printed 0.570). Consistent. (b) CAUTION: the near-zero-spin rows have C_D above the standard sphere curve (row 3: 0.502 at Re 1496, S 0.075; Clift–Grace–Weber standard ≈ 0.44; row 4: 0.550 at Re 1444) — +14…+25 %; and spinning rows at Re 2000–3500 have C_D 0.57–0.80 vs standard ≈ 0.39–0.41. Possible non-terminal (accelerating) motion or wall effects; C_L comes from the same balance (C_L = C_D tanβ), so C_L may carry the same bias. Treat as measured but unverified quality; scatter at fixed S is ±5–10 % (rows 9,10,12,13: 0.379,0.378,0.376,0.393 at S ≈ 0.70–0.72).

### NOT OBTAINED so far
- Sareen, Hourigan, Thompson, "Varying Magnus effect on a rotating sphere at intermediate Reynolds numbers", Int. J. Heat Fluid Flow 109, 109501 (2024), doi:10.1016/j.ijheatfluidflow.2024.109501. Crossref licence: Elsevier TDM only (not OA). Open copy flair.monash.edu/publications/pdfs/SaHoTh_IJHFF_2024.pdf: host resolves to private 172.17.100.53 → "No route to host" (curl) / ECONNREFUSED (WebFetch). eng-web77-v02.ocio.monash.edu (same Monash group mirror): connection timeout on 80 and 443 (curl), ECONNREFUSED (WebFetch). Abstract (via search snippets only, NOT verified against text): experiments, Re ≈ 10^3 to 5×10^4, transverse rotation, "considerable effects of Reynolds number and rotation rate on the force coefficients"; shear-layer instability with rotation even at low Re. → MOST RELEVANT MISSING SOURCE (covers Re 2e3–7e3 by its stated range).
- Sareen et al. JFM 837 (2018) "Vortex-induced vibration of a rotating sphere": same Monash hosts unreachable.
- Misfire (kept, irrelevant): arXiv 2407.01748v1 (Vilumbrales-Garcia, Sudarsana, Sareen, "Lift generation on a sphere through asymmetric roughness using active surface morphing"), src/magnus/sareen2024_arxiv/2407.01748v1.pdf sha256 71552d0354df14c5 — non-rotating dimpled sphere, Re 6e4–1.3e5; no spinning-sphere data.
- MDPI www host 403 for Zhou 2022 (but CDN copy obtained, see S2).
- Sareen 2024 IJHFF: OpenAlex lists a green-OA SSRN preprint doi:10.2139/ssrn.4662313 (submittedVersion); papers.ssrn.com returns HTTP 403 to curl and WebFetch. ScienceDirect abstract page 403. Search-snippet summary (unverified): "10^3 < Re ≲ 5×10^4 ... sudden drop in both [lift and drag] coefficients at a critical rotation rate".

### S3. Sareen, Zhao, Lo Jacono, Sheridan, Hourigan, Thompson 2018 — OBTAINED, but no usable fixed-sphere C_L numbers
- Citation: A. Sareen et al., "Vortex-induced vibration of a rotating sphere", J. Fluid Mech. 837, 258–292 (2018), doi:10.1017/jfm.2017.847
- URL: https://researchmgt.monash.edu/ws/files/255070974/255070700_oa.pdf (Monash repository, published version; OpenAlex: bronze OA at Cambridge, "other-oa"); Cambridge direct link returned an HTML page to curl; OATAO (oatao.univ-toulouse.fr) timed out.
- File: src/magnus/sareen2018_jfm/255070700_oa.pdf, sha256 1ceb637b644b3017; text 255070700_oa.txt (very wide left margin; a trimmed copy for reading is out/sareen2018_trim.txt — line numbers below refer to the trimmed copy, same line count as original).
- Method: measurement, water channel, elastically mounted (VIV) rotating sphere, 5000 < Re < 30000, α = |ω|D/(2U) (= S) 0…7.5 (trim lines 31-32, 245).
- C_L: only figures (mean displacement Fig. 11, C_y time traces); no table, no fixed-sphere values. Text (trim lines 932-942): "beyond α = 1.5, there is very slight increase in the time-averaged displacement, suggesting that the magnitude of the Magnus force is limited." Text (trim lines 1562-1565): cites Sareen et al. (2016, Proc. 11th FIV conference, The Hague) — fixed rotating sphere, 0 ≤ α ≤ 6, "a sudden drop in the lift coefficient at α = 0.3 for a Reynolds number of Re = 2.75 × 10^4". (2016 conference paper not found online.)

### UPDATE: Monash/Melbourne/CSIRO copies obtained via the Internet Archive (Wayback, raw "id_" captures)

### S4. Sareen, Hourigan, Thompson 2024 (IJHFF) — OBTAINED (Wayback copy of the FLAIR-hosted published PDF)
- Citation: A. Sareen, K. Hourigan, M.C. Thompson, "Varying Magnus effect on a rotating sphere at intermediate Reynolds numbers", Int. J. Heat Fluid Flow 109, 109501 (2024), doi:10.1016/j.ijheatfluidflow.2024.109501
- URL: https://web.archive.org/web/20250409082430id_/https://flair.monash.edu/publications/pdfs/SaHoTh_IJHFF_2024.pdf
- File: src/magnus/sareen2024_wayback/SaHoTh_IJHFF_2024.pdf, sha256 a49506cfa609145a; text SaHoTh_IJHFF_2024.txt
- Rights printed on p. 1: "© 2024 Elsevier Inc. All rights are reserved, including those for text and data mining, AI training, and similar technologies." Not OA (published version posted on the authors' lab site). Use only for checking, cite, do not redistribute.
- Method: measurement, FLAIR water channel (600 mm wide × 800 mm deep), smooth sphere D = 80 mm on a top support rod with fixed shroud, stepper-driven rotation, ATI Mini40 6-axis load cell; ≥3 repetitions.
- Definitions (txt lines 127-150): Re = ρUD/μ; α = Dω/(2U) (= S); C_D, C_L = F/(½ρU²A), A = πD²/4.
- FORCE DATA ONLY AT Re = 2.75×10^4 and 4.13×10^4 (txt line 216), FIGURES ONLY (Fig. 5, Fig. 8), no table. Re = 3510 (txt lines 258, 271) is dye visualisation only, NO forces. The "10^3 < Re ≲ 5×10^4" in the abstract is the regime discussed, not the force-measurement range.
- Text statements: "even an order of magnitude below the critical Reynolds number, a sudden drop in the force coefficients is still observed with spin ratio (α), with the critical α and the magnitude of the drop in force coefficients dependent on the Reynolds number" (Concluding remarks, ~txt lines 333-336); "Beyond α = 0.5, a sudden increase in the separation angle is observed correlated with a sudden drop in the lift coefficient" (~line 310-311, at Re 2.75e4); "for high spin ratios of α > 2, both ... boundary layers transition to turbulence, beyond which a further increase in coefficients are not observed".
- Fig. 5 (p. 4) also re-plots Poon et al. (2014) C_L(α) at Re = 500 and Re = 1000. VALUES READ OFF THE FIGURE by me (zoomed render, ±0.02, SECOND-BEST, not printed numbers):
  - Poon 2014, Re 1000: α 0.3 → ≈0.29; α 0.5 → ≈0.40; α 0.6 → ≈0.43; α 0.8 → ≈0.47; α 1.0 → ≈0.49; α 1.2 → ≈0.50
  - Poon 2014, Re 500: α 0.2 → ≈0.25; α 0.3 → ≈0.32; α 0.5 → ≈0.43; α 0.6 → ≈0.47; α 0.8 → ≈0.53; α 1.0 → ≈0.56
  - Sareen, Re 2.75e4: α 0.2 → ≈0.15; 0.4 → ≈0.26; 0.6 → ≈0.30; 0.8 → ≈0.26 (dip); 1.0 → ≈0.27; 1.2 → ≈0.35; 1.4 → ≈0.39; 1.8–2.0 → ≈0.42
  - Sareen, Re 4.13e4: α 0.2 → ≈0.15; 0.4 → ≈0.25; 0.6 → ≈0.29; 0.8 → ≈0.19 (dip); 1.0 → ≈0.33; 1.2 → ≈0.39; 1.4 → ≈0.43
- No torque/moment data reported (load cell measures M but not reported).

### S5. Poon, Iaccarino, Ooi, Giacobello 2009 (CFD conf.) — OBTAINED, but no rotating C_L numbers at Re ≥ 1000
- Citation: E.K.W. Poon, G. Iaccarino, A.S.H. Ooi, M. Giacobello, "Numerical studies of high Reynolds number flow past a stationary and rotating sphere", 7th Int. Conf. on CFD in the Minerals and Process Industries, CSIRO, Melbourne, 9-11 Dec 2009, paper 052POO.
- URL: https://web.archive.org/web/20251117032202id_/https://www.cfd.com.au/cfd_conf09/PDFs/052POO.pdf (live www.cfd.com.au has an expired TLS certificate; eng-web77-v02.ocio.monash.edu mirror unreachable)
- File: src/magnus/poon_cfd2009/052POO.pdf, sha256 c627296dee44f3c7; text 052POO.txt. "Copyright © 2009 CSIRO Australia".
- DNS Re 250, 1000; LES Re 10000; Ω* = Ωd/(2U∞) (= S), only Ω* = 1.00 for Re 1000/10000 transverse rotation — "discussed qualitatively" (no C_L, C_D printed for rotating cases at Re 1000/10000).
- Printed tables: Table 1 (Re 250): Ω* = 0.20, α = π/2: CD 0.76, CL 0.27, St 0.18 (CDP); Table 2 (Re 1000, Ω* = 0): CD 0.46, CL 0.01; Table 3 (Re 10000, Ω* = 0): CD 0.39, CL 0.00. (Non-rotating references only.)

### S6. Dobson, Ooi, Poon 2012 (18th AFMC, paper 351) — OBTAINED, out of range
- URL: https://web.archive.org/web/20240629062503id_/https://people.eng.unimelb.edu.au/imarusic/proceedings/18/351%20-%20Poon.pdf (live host returns an Incapsula block page)
- File: src/magnus/poon_afmc18_wayback/351_Poon.pdf, sha256 70b32c91da0d0197. Re = 300, Ω* = 1.50–3.00 only. Not relevant to Re 1e3–1e4.

### S1 addendum: Muto, Tsubokura, Oshima 2011 (Japanese JSME version) — OBTAINED
- 武藤・坪倉・大島, 回転球に作用する負のマグヌス力の数値解析, 日本機械学會論文集 B編 77(775), 781-792 (2011); https://eprints.lib.hokudai.ac.jp/repo/huscap/all/52225/NKRB77-775_781-792.pdf; src/magnus/muto2011_jsme/NKRB77-775_781-792.pdf sha256 e9d637c2774bc1be. © 2011 JSME.
- Eq. (1) on p. 781 (rendered): Γ = D_p ω / U_0 — same formula as the PoF paper, here WITHOUT the "circumferential velocity" wording. Table 1: air, U0 = 3.41 m/s at Re 1.0×10^4, ν = 1.5×10^-5, D = 44.7 mm. Γ = 0, 0.2, 1.0. C_L only in Fig. 6 (no table).
- Also downloaded (not yet relevant): Muto et al., J. Visualization 15(3) 261-268 (2012), https://eprints.lib.hokudai.ac.jp/repo/huscap/all/53053/JoV15-3_261-268.pdf, src/magnus/muto2012_jov/JoV15-3_261-268.pdf sha256 93dbd43db8f53398.
- Muto JoV 2012 (src/magnus/muto2012_jov, line 184-186): same wording as PoF: "ratio of the circumferential velocity to the incoming flow velocity, Γ = Dpω/U0". Lift only in Fig. 4. No new numbers.

### S7. Nguyen, Corey, Chan, Greenhalgh, Graham 2019 — OBTAINED, out of range
- "Experimental determination of the aerodynamic coefficients of spinning bodies", Aeronaut. J. 123(1263), 678-705 (2019). Accepted version: https://spiral.imperial.ac.uk/bitstreams/33f59af4-47a3-40f2-a1e4-9209c37278fe/download ; src/magnus/nguyen2019_spiral/Aerodynamics_of_spinning_bodies.pdf sha256 c2a307b2280b7c46. © Royal Aeronautical Society. Wind tunnel, 100 mm sphere, Re ≈ 5×10^4–3×10^5 (txt lines 534-537, 742). Out of range.

### Cleanup
Removed failed-probe folders (MDPI 403 pages, SSRN 403 page, HZDR record page, empty S2 probe). The Zhou 2022 line refs: Rr definition txt line 50, Re definition line 52, Eq. 8 line 563, Table 2 lines 570-596 (rows at 573-594), Eqs. 6/7 lines 524/530, Eq. 17/18 lines 1006/1010.

### My check of Zhou Eq. 8 (scripts/zhou_eq8.py; my own computation, not printed in the paper)
Eq. 8 as transcribed reproduces Table 2 within ≈0.01–0.05 except row 3 (0.132 vs 0.081) and row 19 (0.449 vs 0.365) → transcription OK. For Re ≥ 1000 the exponential term is negligible, so Eq. 8 reduces to C_L ≈ 0.365/(1 + e^(2.229−6.5Rr)): S 0.3 → 0.307, S 0.4 → 0.347, S 0.5 → 0.360, S ≥ 0.6 → 0.364–0.365 (independent of Re). Eq. 8 is stated valid only for Re < 3500.

## JUDGEMENT
1. Only ONE checkable source has printed C_L numbers inside Re 2e3–7e3 at S 0.3–1: Zhou, Zhang, Xu 2022 (Water, CC BY), Table 2 — measured, free-flying glass spheres spun up on a rolling track, Re 2070–3472 (rows 7, 9–13, 19–22) plus Re 1244–1260 (rows 5–6). Nothing printed between Re 3472 and 10^4.
   - S ≈ 0.70–0.72, Re 2244–2310: C_L 0.379, 0.378, 0.376, 0.393 (C_D 0.629, 0.657, 0.674, 0.672)
   - S ≈ 1.00, Re 2070: C_L 0.449 (C_D 0.800)
   - S ≈ 0.94–0.98, Re 3352–3472: C_L 0.358, 0.353, 0.353 (C_D 0.682, 0.709, 0.750)
   - S 0.251, Re 2502: C_L 0.261 (C_D 0.570)
   - S 0.419 / 0.4945, Re 1244 / 1260: C_L 0.364 / 0.339 (C_D 0.657 / 0.648)
   Caveat: its near-zero-spin C_D is 14–25 % above the standard sphere curve, spinning C_D 0.57–0.80; quasi-steady force balance; C_L shares that balance. No S between 0.3 and 0.4 at Re > 1300.
2. Brackets:
   - Re = 10^3 (Poon et al. 2014 DNS): NO printed numbers obtainable (JFM paywalled, no repository copy). Second-best, figure-read from Sareen 2024 Fig. 5: α=S 0.3 ≈0.29, 0.5 ≈0.40, 0.6 ≈0.43, 0.8 ≈0.47, 1.0 ≈0.49, 1.2 ≈0.50.
   - Re = 10^4 (Muto 2012 LES, Table I, printed): Γ = 0.2 → C_Lz 0.167 (C_D 0.474); Γ = 1.0 → C_Lz 0.301 (C_D 0.661); Γ = 0 → C_D printed 0.046 (evident typo). Γ is printed as D_p ω/U_0 in all three Muto papers but called "ratio of the circumferential velocity" in two; if the formula is literal, Γ = 2S (Γ=1 → S=0.5, Γ=0.2 → S=0.1). Cross-check against Poon Re 1000 and Sareen Re 2.75e4 (both figure-read, α = ωD/2U): C_L at S=0.2 is ≈0.15–0.2, at S=0.1 ≈0.08–0.1, so Muto's 0.167 at Γ=0.2 fits Γ = S better (weak evidence, unresolved).
   - Re = 2.75×10^4 (Sareen 2024, figure only): non-monotonic C_L(α) with a dip at α ≈ 0.6–1.0 (≈0.30 → 0.26 → 0.27). The authors say the drop size shrinks with decreasing Re; whether a dip exists at Re 2e3–7e3 is not measured by anyone found.
3. Trend at S ≈ 1 across sources (mixed quality): Re 1000 ≈0.49 (fig) → Re 2070 0.449 → Re 3350–3470 0.353–0.358 → Re 10^4 0.301 (if Γ=S) → Re 2.75e4 ≈0.27 (fig). C_L at S ≈ 1 falls with Re by ~0.1 between Re 2e3 and 1e4; a constant C_L(S) is a ±15–20 % approximation over the chute range.
4. Torque / spin-decay coefficient: NONE of the obtained sources reports it (Sareen's load cell measures moments but they are not reported). Not found in range.
