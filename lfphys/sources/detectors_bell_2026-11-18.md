# lfphys sources — 2026-11-18: real detectors and the Bell inequalities without fair sampling (EX2, step E37)

The record of the sources behind `core.quantum.qubits` (the stations' POVMs, Eberhard's states, Werner mixtures),
`theories.models.photodetector` (new), `tools.bell_stats` (slot probabilities, CH, J, accidentals, thresholds) and
`theories.alternatives.local_hidden` (Gisin and Gisin's model), written for the EX2 design
`explore_EX2_2026-11-18_design.md` §4.7. Every file below was downloaded into its own scratch folder by a generic client
(no e-mail address or personal identifier in the requests), converted with `pdftotext` (scanned pages read as images),
and every quotation was found word for word in the text; the hash is the first 16 hex digits of the file's SHA-256.

## 1. Sources and what was verified

| source | file | sha256 (16) | verified |
|---|---|---|---|
| M. Giustina et al., «Significant-loophole-free test of Bell's theorem with entangled photons», PRL 115, 250401 (2015) | `arxiv.org/pdf/1511.03190v2` | f2eea302004982f4 (as the design's Appendix B) | eq. (1) «J ≡ p++ (a1 b1) − p+0 (a1 b2) − p0+ (a2 b1) − p++ (a2 b2) ≤ 0», «+» a detection and «0» none, one detector per side; eq. (2), the Eberhard state (\|V⟩_A\|H⟩_B + r\|H⟩_A\|V⟩_B)/√(1 + r²); r ≈ −2.9, a1 = 94.4°, a2 = 62.4°, b1 = −6.5°, b2 = 25.5°; «system heralding efficiencies of approximately 78.6% in the Alice arm and approximately 76.2% in the Bob arm»; J = 7.27 × 10⁻⁶ measured, «quantum mechanics predicts an optimal J-value of about 4 × 10−5» at 3 500 pairs per second; the pump «pulsed … at 1 MHz repetition rate» (trials of 1 µs); «Our experiment employed locally defined time slots and was thus also not vulnerable to the coincidence-time loophole»; «These inequalities can be violated with system heralding efficiencies larger than 2/3.» |
| L. K. Shalm et al., «A strong loophole-free test of local realism», PRL 115, 250402 (2015) | `arxiv.org/pdf/1511.03189` | e4f16a8d1ea736ca (as Appendix B) | «Eberhard showed that at least 2/3 of the particles must be detected [19] if nonmaximally entangled states are used.»; «These background counts in our system raise the efficiency needed to violate a Bell inequality from 2/3 to 72.5 %.»; the inequality «P (++ \| ab) ≤ P (+0 \| ab0 ) + P (0+ \| a0 b) + P (++ \| a0 b0 )» (= J ≤ 0); system efficiencies 74.7 ± 0.3 % and 75.6 ± 0.3 %; background per window 8.9 × 10⁻⁷ (Alice) and 3.2 × 10⁻⁷ (Bob), «the probability that a single pump pulse downconverts into a photon pair is ≈ 5 × 10−4»; the state 0.961\|HH⟩ + 0.276\|VV⟩ |
| N. Gisin, B. Gisin, «A local hidden variable model of quantum correlation exploiting the detection loophole», Phys. Lett. A 260, 323 (1999) | `arxiv.org/pdf/quant-ph/9905018` | b1caa43414a56288 (as Appendix B) | the model of §2 in full: λ uniform on the sphere, outcome sign((⟨σ⟩ − λ)·a), Alice's outcome only with probability \|λ_A·a\|, mean 1/2 (eq. (3)), the detected pairs' E = −a·b (eqs. (7)–(10)); the symmetric version («both detectors show an effective efficiency of 75%») and the «no outcome at all» with probability 1/9 (each detector then 2/3, independent-looking); «On average the detector efficiency is limited to 75%.»; CHSH (11); CH (15) «N++ (a, b) + N++ (a, b′) + N++ (a′, b) − N++ (a′, b′) ≤ N+· (a) + N·+ (b)»; the threshold (18) and «Hence, quantum mechanics predicts that the CH inequality (15) can be violate, and thus lhv models definitively ruled out, only with detector’s efficiencies higher than 82.8%!» |
| J. F. Clauser, M. A. Horne, «Experimental consequences of objective local theories», Phys. Rev. D 10, 526 (1974) | a scan of the journal pages, `johnclauser.com/_files/ugd/36ef59_941d93aaa6fb442981a62e84f9fc543f.pdf` | 7b83a8c4eff0100a | ineq. (4), read from the page image (p. 528; the scan's text layer is unreadable): −1 ≤ p12(a, b) − p12(a, b′) + p12(a′, b) + p12(a′, b′) − p1(a′) − p2(b) ≤ 0; Gisin and Gisin's (15) is the same with a and a′ exchanged |
| P. H. Eberhard, «Background level and counter efficiencies required for a loophole-free Einstein-Podolsky-Rosen experiment», Phys. Rev. A 47, R747 (1993) | the preprint LBL-32696 (August 1992, submitted to PRL), `escholarship.org/content/qt6bh6m5ng/qt6bh6m5ng.pdf`; **the published version was not read** | ba0ff9ea2f0ab1b0 | a scan with an OCR layer: ineq. (8), n_oe(α1,β2) + n_ou(α1,β2) + n_eo(α2,β1) + n_uo(α2,β1) + n_oo(α2,β2) − n_oo(α1,β1) ≥ 0 (−J ≥ 0, «o» the detected ordinary beam); (7), η > 2(√2 − 1) ≈ 82.8 % at the CHSH optimum; «For η < 2/3 there is none» (the OCR renders 2/3 as «~»); Table 2 (η, the largest background ζ, r, ω, α2 − α1): 70 %: 0.02 %, 0.136, 21.4°; 75 %: 0.31 %, 0.311, 32.0°; 80 %: 1.10 %, 0.465, 37.9°; 85 %: 2.48 %, 0.608, 41.5°; 90 %: 4.50 %, r unreadable, 43.6°; 95 %: unreadable; 100 %: 10.36 %, 1.000, 45.0°; the conclusion's «66.1%» is read as 66.7 % (the table's first row) |
| D. Dehlinger, M. W. Mitchell, Am. J. Phys. 70, 903 (2002) | `arxiv.org/pdf/quant-ph/0205171` | 205531334f0d5625 (as Appendix B) | «Also shown are “accidental” coincidences (NAc. = τ NA NB /T ) assuming a coincidence window of τ = 25 ns.»; «This background is small, nearly constant, and acts to decrease \|S\|.» |
| Excelitas Technologies, «SPCM-AQRH Series, Single Channel Photon Counting Modules», data sheet and operating manual, Rev 2023-1 | `excelitas.com/sites/default/files/assets/product/document/27464.pdf` | 0a6a1dae3aa38697 | Table 1: photon detection efficiency (without FC adaptor) 400 nm 2/5 %, 650 nm 50/65 %, 830 nm 35/45 % (minimum/typical); dark count at most 1500, 1000, 500, 250, 100, 50, 25 counts/s for grades W0–W6; dead time 22 ns (-1X, -4X), 28 ns (-2X, -5X), 42 ns (-3X, -6X); single-photon timing resolution 350 ps typical at 825 nm; afterpulsing 0.5 % typical, 1 % maximum; linearity correction factor 1, 1.02, 1.16, 1.40, 2.35, 3.32 at 0.2, 1, 5, 10, 20, 25 Mc/s. Table 4: dead time 24, 28, 42 ns for -1X/-4X, -2X/-5X, -3X/-6X (24, not 22, for the first option: the revision is inconsistent); note 8: «For the typical dead time setting of 24ns»; note 6: «In the dark, the module generates random counts that follow a Poisson distribution.»; Figure 1 (an image, read): «Correction Factor = 1/(1 − (t_d × C_R))», t_d the module's dead time, C_R the output count rate, «The theoretical value, at low count rate» |
| Excelitas Technologies, «SPCM-NIR, NIR-Optimized Single Photon Counting Module», product brief, Rev 2018-09 | a distributor's copy, `htds.fr/wp-content/uploads/2019/05/Excelitas-SPCM-NIR-Family-datasheet.pdf` (the manufacturer's file was not found) | 8f56a49f68328e5e | Table 2: photon detection efficiency 780 nm 64/70 %, 800 nm 62/68 %, 850 nm 54/58 %, 900 nm 41/45 %; dark count at most 1500 … 100 counts/s for W0–W4; timing resolution 350 ps at 825 nm; dead time 20 ns typical, 40 ns maximum («Other values can be factory set»); afterpulsing 1.0 % typical, 3.0 % maximum |

The timing resolution is printed as one number without its width measure; the engine reads it as the full width at
half maximum (σ = 350 ps / 2.3548 = 148.6 ps), the measure Excelitas's own timing papers use. This reading was not
confirmed in the data sheets themselves.

## 2. The devices in the engine (`photodetector.DEVICES`)

| key | η | dark counts | dead time | jitter σ | for |
|---|---|---|---|---|---|
| `spcm_aqrh_14_650nm` | 0.65 (typical at 650 nm) | 100 s⁻¹ (the grade's maximum) | 22 ns (Table 1) | 148.6 ps | u35 (HeNe, 632.8 nm): the design's illustrative values η 0.65, 100 s⁻¹, 22 ns are exactly this device's [confirmed] |
| `spcm_nir_800_13` | 0.68 (typical at 800 nm) | 250 s⁻¹ (the grade's maximum) | 20 ns (typical) | 148.6 ps | u37 (pairs near 810 nm, as Dehlinger and Mitchell's and Giustina's): the design's illustrative η 0.70, 300 s⁻¹, 50 ns and a jitter of 0.5 ns are not any device's; the real values are 0.68, 250 s⁻¹ (grade W3; 100 s⁻¹ for W4), 20 ns and σ ≈ 0.15 ns |

## 3. The formulas and their tests

| formula | source | test (second method) |
|---|---|---|
| one-detector POVM E₀ = (1 − p_d)(I − ηΠ), E₊ = I − E₀; the two-detector POVM (four outcomes) | Giustina's «+»/«0»; derived | `test_qubits_povm.py`: the limits η = 1, p_d = 0 (projectors); positivity and Σ = I; an enumeration of port × detection × dark clicks to 1e-14 |
| Eberhard's state, Werner's mixture | Giustina eq. (2) | concurrence 2\|r\|/(1 + r²), r ↔ 1/r under X ⊗ X; S = V·2√2 (spins and photons) |
| the slot's outcome probabilities with a Poisson number of independent pairs and dark clicks (inclusion–exclusion over the no-click probabilities exp(−μ(1 − q))) | derived; independent pairs = a slot with many temporal modes | `test_bell_stats.py`: an enumeration over 0 … 40 pairs (1e-13); a time-stream Monte Carlo with settings per slot, dead time and jitter (5σ) |
| J (Giustina eq. (1) = Eberhard (8)); CH (Gisin and Gisin (15) = Clauser and Horne (4)) | as quoted | J = 0.01134 per pair at Giustina's state, angles and efficiencies against a direct formula with the state's amplitudes (1e-15); per slot 3.93 × 10⁻⁵ at 3 500 pairs/s (Giustina: «about 4 × 10−5»); unbiased estimators with covering errors (3 000 runs); CH = J without signalling |
| the thresholds 2/(1 + √2) and → 2/3 | Gisin and Gisin (18); Eberhard (7), Table 2 | a direct search over the four angles (Nelder–Mead from seeded starts): J < 0 at 0.8264, > 0 at 0.8304 for the maximally entangled state; J ≤ 0 at η = 0.66 for every r tried; Eberhard's Table 2: the largest J per pair over the angles, halved, equals the tabulated ζ at 70–100 % (0.0227, 0.3075, 1.0955, 2.4845, 4.4954, 10.3553 % against 0.02, 0.31, 1.10, 2.48, 4.50, 10.36 %) at the tabulated angle a2 − a1 (21.40°, 31.98°, 37.91°, 41.54°, 43.64°, 45.00°) |
| m = n/(1 + n t_d) | the data sheet's Figure 1 | a time-stream Monte Carlo of a non-paralysable detector (5σ); the data sheet's linearity factors at 5–25 Mc/s follow the same form to 2.5 % only with t_d = 28.2 ns (each alone implies 27.6–28.7 ns; the nominal 22 ns gives 2.22 instead of 3.32 at 25 Mc/s) |
| R_acc = w R_A R_B; the share erf(w/(2√2 σ_d)) | Dehlinger and Mitchell; Gaussian jitter (a stated shape) | Monte Carlo of two Poisson streams and of jittered pairs (5σ) |
| Gisin and Gisin's model | §2 of the paper | Monte Carlo against its closed table (both detected (1 − ν)/2, then (1 + ABE)/4; one side alone (1 − ν)/4 each), E = −a·b, 75 % per side, 2/3 with ν = 1/9; CH = (1 − ν)(X − 4)/8 ≤ 0 at 500 random settings; S = 2√2 from coincidences |

## 4. Numbers of the design (§4.3, §4.7, Appendix A.7)

Confirmed by the engine: J per pair 0.01134 at Giustina's set-up; −0.0239 / −0.0060 / +0.0053 / +0.0182 / +0.0852 at
η = 0.60 / 0.70 / 0.75 / 0.80 / 1.00 (Giustina's state and angles); the maximally entangled state's best J −0.0710 at
0.75, −0.0275 at 0.80, 0 at 0.8284, +0.0221 at 0.85, (√2 − 1)/2 at 1; r = −0.05 violates at 0.68; nothing at 0.60.
Refined: the r = −2.9 state violates from η = 0.7246 (the design: «≈ 0.72»). The device values: §2 above.

Shalm et al.'s «from 2/3 to 72.5 %»: with their background per window (8.9 × 10⁻⁷, 3.2 × 10⁻⁷) and pair probability
(5 × 10⁻⁴) in one pulse per trial, the search over r and the angles gives 72.65 % (their trials aggregate several
pulses, which is not modelled); the test brackets it between 72 % and 73.5 %.

The ways of u37's part 4 that depend on the coincidence window (`photodetector.coincidence_rates`, |Φ⁺⟩ at the CHSH
angles, 10⁴ pairs per second, both detectors of each station alike):

| way | set-up | the design | the engine |
|---|---|---|---|
| 16 | the design's devices (η 0.70, 300 s⁻¹, 50 ns, σ 0.5 ns) with 10⁵ s⁻¹ of background, w = 25 ns, not subtracted | accidentals 19 % of the true coincidences, S ≈ 2.37 | 22.0 %, S = 2.319 **[error in earlier]** (subtracted: 2.828) |
| 17 | the same with w = 2 ns | 1.8 %, 16 % of the true lost (erf(1) = 0.843), S ≈ 2.78 | 2.09 %, 0.843, S = 2.771 |
| 18 | w = 0.5 ns, σ 0.5 ns, no background | erf(0.25) = 28 % inside | 0.276 |
| 16–18 with the real SPCM-NIR (0.68, 250 s⁻¹, 20 ns, σ 0.149 ns) | w = 25 / 2 / 0.5 ns | — | 23.2 %, S = 2.295 / 1.86 % with no jitter loss, S = 2.777 / 76.6 % inside (not 28 %) |

With the real jitter a 2 ns window loses nothing and a 0.5 ns window loses 23 %, not 72 %: W37 recomputes ways 17 and
18 for the devices it uses.
