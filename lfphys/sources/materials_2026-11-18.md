# Optical materials, their sources and checks — 2026-11-18 (EX2 step E35, second part)

Purpose: the record behind `lfphys.core.optics.materials` and the optical `DATASETS` entries of `lfphys.core.data`
(EX2 design `explore_EX2_2026-11-18_design.md` §3.9; the owner's direction of 2026-11-18, `../../AGENTS.md` §1:
«нужно добавить все до реальных физических явлений»). For each dataset: the source, the file it was taken from (its
sha256, first 16 hex digits), what was compared and how, and the licence. Every file was downloaded into its own
scratch folder, with no e-mail or personal identifier in the requests; numbers were compared by script, not by eye.
Status codes: CHECKED (against the source's own text or table) / TRANSCRIPTION (as the database gives it; the original
not accessible) / DIFFERS (the two sources differ; both given).

## 1. Licences

- **refractiveindex.info database** (M. N. Polyanskiy), `github.com/polyanskiy/refractiveindex.info-database`, branch
  `main`: `LICENSE` (sha256 36ffd9dc085d529a) is CC0 1.0 Universal; the GitHub API reports `cc0-1.0`; every data file
  starts «refractiveindex.info database is in the public domain / copyright and related rights waived via CC0 1.0».
- **SCHOTT data sheets and TIE-29**: product data published by SCHOTT for use with its glasses; the engine records
  facts (constants and measured values, transcribed and cited), not the documents.
- **Code**: none copied. The interpolant (PCHIP) is written from Moler's published description (§4); SciPy and mpmath
  appear only in the tests (`AGENTS.md` rule 8).

## 2. SCHOTT glasses: N-BK7, N-F2, N-SF11 — CHECKED

Sources (media.schott.com):
- «Optical Glass Datasheet SCHOTT N-BK7», «As of 01-Dec-2023» (content 41e799d0bf874807a0bb8e702fbb75b5; PDF modified
  2023-11-28; sha256 b3287ae9ef985527).
- «Optical Glass Datasheet Collection» (content 38cbbe876d324e03b1881d33f3d26635; PDF modified 2025-07-03; sha256
  eb70cd8b1c72051b): the N-F2 and N-SF11 sheets, each «As of 01-Feb-2014».
- «TIE-29 Refractive Index and Dispersion», «Version August 2023» (content aaa572afd854434fb7b3faa4bc46103f; sha256
  9d07414c481e624c).
- Cross-check: the refractiveindex.info files `specs/schott/optical/{N-BK7, N-F2, N-SF11}.yml` (sha256
  87da400af68251be, 85c50ba2f37383a0, 367d46bc83845957; from «SCHOTT Zemax catalog 2017-01-20b») and the SCHOTT data
  sheets PDF of 2017-01-20 the database links (sha256 c94c9c869661c21c; it holds N-BK7HT, not N-BK7: N-BK7HT has the
  same Sellmeier constants but another internal transmittance).

Verified:
- **Sellmeier constants**: the database's B₁–B₃, C₁–C₃ equal the sheets' printed constants to every printed digit (the
  sheets print 9–10 digits, e.g. N-BK7 C₁ «0.006000699» for 0.00600069867; `test_materials.py`).
- **Every printed index** (N-BK7: 20 lines from 312.6 to 2325.4 nm; N-F2 and N-SF11: 17 lines from 404.7 to 2325.4 nm)
  is reproduced to its last digit, |n − printed| ≤ 0.5·10⁻⁵ (largest 4.9·10⁻⁶), at the lines' wavelengths of TIE-29's
  Tab. 1 (e.g. g 435.8343, F 486.1327, d 587.5618, C 656.2725 nm). At the rounded wavelengths the sheets print (435.8
  nm …) the formula misses by up to 2.6·10⁻⁵; at the vacuum wavelengths (×1.00027) by up to 6.8·10⁻⁵. n_F − n_C and ν_d
  as printed. TIE-29, quoted: «The wavelengths used in the equation have to be inserted in µm with the same number of
  digits as listed in Table 1.»; «The achievable precision of this calculation is generally better than 1 · 10⁻⁵ in
  the visible spectral range.»
- **Air, not vacuum.** TIE-29: «The refractive index data given in the data sheets are measured relative to the
  refractive index measured in air. The refractive index of air is very close to 1.»; «The refractive index data are
  exact to five decimal places (for λ > 2 µm: ± 2 · 10⁻⁵).»; «All data apply to room temperature and normal air
  pressure (0.10133 · 10⁶ Pa).»; «The refractive index variation from part to part within a lot is always smaller than
  ± 5 · 10⁻⁵.» So n is relative to air and λ is the wavelength in air (the fit at the air wavelengths above confirms
  it). For a boundary between glass and air in air this is exactly what the Fresnel equations need, with air n = 1.
- **κ** from the sheets' internal transmittance: τᵢ = exp(−4πκd/λ), κ = −λ ln τᵢ/(4πd), d = 25 mm (10 mm where only
  that is printed above 0.000). The database's κ (from the 2017 catalogue) equals this at every wavelength, to its
  5 printed digits, except two N-SF11 entries — **DIFFERS**: at 370 nm the current sheet prints τᵢ(25 mm) = 0.000 (the
  2017 catalogue 0.002; the engine uses τᵢ(10 mm) = 0.080: κ 7.437·10⁻⁶ against the database's 7.319·10⁻⁶) and at
  1970 nm τᵢ(25 mm) = 0.920 (2017: 0.915). The τᵢ tables are in `core/data.py` exactly as printed (script check).
- **dn/dT constants** D₀, D₁, D₂, E₀, E₁, λ_TK as printed, recorded for a later thermal bench (not used).
- At 632.8 nm: N-BK7 1.515089 (printed 1.51509), N-F2 1.616579 (1.61658), N-SF11 1.778602 (1.77860).

## 3. Sellmeier crystals and glass: MgF₂ (Dodge, ordinary ray), fused silica (Malitson)

- Files: `main/MgF2/nk/Dodge-o.yml` (sha256 86f453a855b8eadc: «M. J. Dodge. Refractive properties of magnesium
  fluoride. Appl. Opt. 23, 1980-1985 (1984)», «19 °C. Ordinary ray (o).», range 0.2–7.0 µm) and
  `main/SiO2/nk/Malitson.yml` (c587670f397241ec: «I. H. Malitson … J. Opt. Soc. Am. 55, 1205-1208 (1965)», «Fused
  silica, 20 °C»; the comment «Sellmeier formula is reported in Ref. 1 for the 0.21–3.71 μm wavelength range»; the
  engine keeps 0.21–3.71 µm, not the database's extension to 6.7 µm after Tan 1998).
- **TRANSCRIPTION, cross-checked**: the coefficients agree with a second, independent transcription, Wikipedia's
  «Sellmeier equation» (wikitext fetched 2026-11-18, sha256 cfb32167e4c08f55), which gives Aᵢ and λᵢ²: MgF₂
  0.48755108, 0.39875031, 2.3120353 and 0.001882178, 0.008951888, 566.13559; fused silica 0.6961663, 0.4079426,
  0.8974794 and 0.004679148, 0.01351206, 97.934 (the database's λᵢ squared agree to the printed digits). The papers
  were not accessible (Optica's paywall; the publisher's site answered with bot protection), so whether their λ is in
  air or vacuum and n relative to air or vacuum is not checked: a difference of about 2.7·10⁻⁴ of n and λ, stated in
  the entries' validity.
- At 632.8 nm: MgF₂ 1.376984, fused silica 1.457018 (the design's 1.37698, 1.45702).

## 4. Tabulated films and metals — TRANSCRIPTION

| id | file (refractiveindex.info, `main/…`) | sha256 | rows, range | original |
|---|---|---|---|---|
| `mgf2_film_rodriguez` | `MgF2/nk/Rodriguez-de Marcos.yml` («Numerical data kindly provided by Juan Larruquert»; «44 nm film prepared by evaporation from tungsten boat at 250 °C») | f97bc672a4f3051c | 960, 0.0300–2.0015 µm | L. V. Rodríguez-de Marcos, J. I. Larruquert, J. A. Méndez, J. A. Aznárez, Opt. Mater. Express 7, 989 (2017) |
| `sio2_film_gao` | `SiO2/nk/Gao.yml` («Numerical data kindly provided by F. Lemarchand»; «300-nm monolayer deposited on fused silica using the ion assistance electronic beam deposition technique») | 18803e6bde85b356 | 500, 0.252–1.25 µm | L. Gao, F. Lemarchand, M. Lequime, J. Eur. Opt. Soc. Rapid Publ. 8, 13010 (2013) |
| `ta2o5_film_gao` | `Ta2O5/nk/Gao.yml` («400-nm monolayer deposited on 160-µm BK7 substrate …») | 269efa1797dc91c4 | 726, 0.35–1.8 µm | L. Gao, F. Lemarchand, M. Lequime, Opt. Express 20, 15734 (2012) |
| `au_johnson_christy` | `Au/nk/Johnson.yml` («Room temperature») | 9f4bdab6bd49f7c6 | 49, 0.1879–1.937 µm | P. B. Johnson, R. W. Christy, Phys. Rev. B 6, 4370 (1972) |
| `ag_johnson_christy` | `Ag/nk/Johnson.yml` | 8c79d5e2529e4d3a | 49, 0.1879–1.937 µm | same |
| `al_rakic` | `Al/nk/Rakic.yml` («Optical and electron-energy-loss data for evaporated-aluminum films …») | e93b31fe82155183 | 206, 0.12399 nm–200 µm | A. D. Rakić, Appl. Opt. 34, 4755 (1995) |

The rows are in `core/data.py` with the text of every number identical to the files' (script check). The papers were
not accessible to this check: Johnson and Christy (APS) and Rakić (Optica) behind paywalls; the open-access papers of
Gao et al. and Rodríguez-de Marcos et al. behind bot protection (Optica, JEOS, HAL, DIGITAL.CSIC answered with
challenges; OpenAlex lists them as gold open access). Their values are as the database gives them, which the entries
say. The design's Appendix B sha256 values agree with the files fetched here.

**Interpolation** (`materials.Pchip`): the shape-preserving cubic as described by C. Moler (after Fritsch and Carlson),
*Numerical Computing with MATLAB* (SIAM 2004), ch. 3 «Interpolation» §3.4 (the chapter `interp.pdf` from MathWorks,
sha256 ed0c3af2d789e37a): interior slopes the weighted harmonic mean «(w1 + w2)/dk = w1/δk−1 + w2/δk, w1 = 2hk + hk−1,
w2 = hk + 2hk−1», 0 where the neighbouring slopes differ in sign or one is zero; at the ends Moler's `pchipend`
(«Noncentered, shape-preserving, three-point formula»). It equals SciPy's PchipInterpolator to 10⁻¹³ (tests). n is
interpolated in λ, κ in ln κ (in κ where a table has κ = 0: the Gao films). **Error estimate**: for each interval,
the largest leave-one-out error of the six surrounding nodes, and at least half a unit of the last printed digit of
its two nodes (a printed «0» gets the column's finest precision). Between 0.2 and 2.5 µm this bounds the difference
from a second interpolant (Akima's) at ¼, ½, ¾ of every interval for every table (largest ratio 0.88, aluminium's n);
over the full ranges the one excess is aluminium's L edge near 17 nm (1.8 times the estimate), stated in the module.
At 632.8 nm: gold ±0.016 in n, ±0.038 in κ; silver ±0.010, ±0.019; aluminium ±0.034, ±0.025; the films ±(5–9)·10⁻⁷.

## 5. The group delay (`interfaces.group_delay`)

The design asked for the transfer matrix differentiated in ω «by the complex step». The complex-step derivative needs a
real-valued function; r(ω) and t(ω) are complex-valued, so the engine differentiates the characteristic matrices
exactly instead (forward mode, the product rule through the stack; each layer written through u = q² and δ², so a wave
grazing inside a layer stays regular), with each material's dn/dλ from `materials.dindex` (exact for the formulas and
for the interpolant). The complex step appears in the tests, on the real-valued phase of total internal reflection with
SCHOTT's Sellmeier n(λ). Tests: a lossless slab's closed form (τ_t to 10⁻¹², τ_r to 10⁻⁹), total internal reflection
with dispersion (complex step, 10⁻¹¹), real coatings, a mirror and a Kretschmann film against finite differences
(2·10⁻⁶), and the frustrated-TIR gap (r and t delays equal, as for any symmetric lossless structure; finite
differences; the Hartman saturation).

## 6. The design's numbers (Appendix A.7, §3.1–§3.3, §3.9) recomputed with the module

Confirmed: the indices at 632.8 nm of §3.9 (all to their printed digits); θ_B 56.574°, 58.259°, 60.654° and θ_c
41.302°, 38.213°, 34.211°; the story's R 4.350 % (30°), 7.727 % (θ_B), 5.850 % (inside, 30°), the 200 nm gap's
T 47.09 % (s 36.44 %, p 57.74 %); the λ/4 MgF₂ film (96.64 nm) on N-BK7: 2.79 % at 400 nm, 2.04 % at 550 nm, 2.14 % at
633 nm, 2.28 % at 700 nm (bare 4.40, 4.24, 4.19, 4.17 %); bulk MgF₂ λ/4 1.25 % at 550 nm; Ta₂O₅/SiO₂ (Gao films): 4
pairs 87.9 % at 550 nm, 70.3 % at 632.8 nm, 8 pairs 99.37 %, 75.8 % and 27.4 % at 450 nm.

Corrected **[error in earlier]**: the metals at 632.8 nm were interpolated linearly in the design; with the module's
PCHIP gold is 0.1773 + 3.4384i (linear 0.1838 + 3.4313i), silver 0.0577 + 4.2780i (0.0563 + 4.2760i), aluminium
1.4444 + 7.5408i (1.4482 + 7.5367i), all within the stated interpolation error. The Kretschmann minimum (50 nm of gold
on N-BK7, p light) is then R_p = 0.0038 at 43.773° (the design: 0.0058 at 43.785°). This minimum is sensitive to the
gold's index: within its interpolation error (n ± 0.016, κ ± 0.038) R_p,min ranges from 0 to 0.014 and its angle from
43.71° to 43.84°, so a bench should quote it with that spread.

## 7. u35's detectors (for W35 and E37's `theories.models.photodetector`)

Excelitas Technologies, «SPCM-AQRH Series Single Photon Counting Module», Rev 2023-1 (19 pages),
`excelitas.com/sites/default/files/assets/product/document/27464.pdf`, sha256 0a6a1dae3aa38697, quoted from its
specification table and notes:
- «Photon detection efficiency (PDE) … 650nm 50 [min] 65 [typ] %»; the typical curve (Figure 4) reads about 0.68 at
  632.8 nm (a graph reading); the introduction: «peak photon detection efficiency greater than 70% at 650nm».
- «Dark Count … SPCM-AQRH-W4 100 Counts / second», a maximum (Table 4: «Maximum Dark Count Rates (cps)»; grades
  1500 … 25); «In the dark, the module generates random counts that follow a Poisson distribution.»
- «Dead time (count rate below 5M/c) SPCM-AQRH-1X, SPCM-AQRH-4X 22 ns» (typ); Table 4 of the same revision lists 24 ns
  for -1X and note 8 speaks of «the typical dead time setting of 24ns».
- Figure 1: the actual photon rate = (output count rate × correction factor − dark count)/PDE, correction factor
  = 1/(1 − t_d C_R) (a non-paralysable dead time).
- «Afterpulsing probability 0.5 [typ] 1 [max] %»; «Single photon timing resolution (at 825nm) 350 ps».

So the design's η 0.65, 100 dark counts per second and 22 ns are this module's printed values (η typical at 650 nm;
100 s⁻¹ the maximum of the -x4 grade; 22 ns typical, 24 ns in Table 4).
