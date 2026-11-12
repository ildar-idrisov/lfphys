# lfphys source verification — 2026-11-04, plan item P1 (batch B8): Maxwell's equations by FDTD (Yee)

Purpose: every quotation, formula and number used by `core.em.fdtd` (with `fdtd_geometry`, `fdtd_sources`,
`fdtd_tfsf`, `fdtd_monitors`), `core.optics.cylinder` and their tests (`tests/test_fdtd_grid.py`,
`test_fdtd_boundaries.py`, `test_fdtd_media.py`, `test_fdtd_scattering.py`, `test_fdtd_api.py`,
`test_cylinder_series.py`, and the one-off Meep comparison recorded in `comparison_2026-11-04_meep.md`), checked against the source text. Texts fetched on
2026-11-04 with plain HTTP requests (no contact parameter, e-mail address or personal identifier was sent with any
request); PDFs read with `pdftotext -layout`, web pages as text. The full texts are kept outside the repository.
Status codes as in `verification_2026-10-23.md`: VERIFIED (quoted) / DIFFERS (both given) / NOT FOUND / NOT FETCHED
(closed text; what replaces it is said).

**Revised 2026-11-04 in the processing of review B8-fdtd** (`reviews/archive/2026-11-04_internal_B8-fdtd/`, its
`RESPONSE.md`): §2 (the second CPML paper's author and subject, a second source for σ_max), §3 (the averaging is the
VP-EP scheme and converges linearly in general), §6a (new: the pole schemes and their stability, Bidégaray-Fesquet
2008) and §8 (every number that depended on the flux normalisation re-measured, F5; the Meep comparison redone, F8).
The new quotations were grepped in the reviewer's downloaded copies (session scratchpad, outside the repository) and
the arXiv abstract pages and Crossref metadata fetched on 2026-11-04 with plain requests (no contact parameter, e-mail
address or personal identifier). Withdrawn statements are marked [error in earlier].

## 1. Schneider, *Understanding the Finite-Difference Time-Domain Method* (the author's online edition)

J. B. Schneider, Washington State University, `eecs.wsu.edu/~schneidj/ufdtd/ufdtd.pdf` (the PDF is dated "March 22,
2026"; the book is freely available from the author).

* The Yee grid's dispersion relation, §7.4: "µϵΩ2 = Kx2 . (7.33) This is the FDTD dispersion relation." and the
  form (7.34) sin²(ω∆t/2) = (∆t²/(ϵµ∆x²)) sin²(β̃∆x/2). VERIFIED. For two and three dimensions the book says "(a
  similar dispersion relation holds in two and three dimensions, but there a closed-form solution is not possible)".
  VERIFIED. The engine's form sum_u sin²(k_u dx/2)/dx² = eps mu sin²(omega dt/2)/dt² is the same plane-wave
  substitution per axis; `test_fdtd_grid.py` measures it.
* The magic time step, §7.4: "In one dimension a Courant number of unity is the greatest possible and, since there is
  no dispersion error with this Courant number, the corresponding time step is known as the magic time-step.
  Unfortunately a magic time-step does not exist in higher dimensions." VERIFIED.
* Courant limits: 1-D Sc = c∆t/∆x = 1 (eq. 3.21); "The simulation is run at the Courant limit of 1/√2" (2-D, line
  of ch. 8's example); "For a uniform grid in three dimensions the Courant limit is 1/√3" (§9). VERIFIED (the square
  roots are typeset apart from their arguments in the text layer).
* Analytic reflection of an interface on the grid, §7.6: an interface at an H node, eq. (7.72):
  Γ̃ = (√ϵ1 cos(β̃2∆x/2) − √ϵ2 cos(β̃1∆x/2)) / (√ϵ1 cos(β̃2∆x/2) + √ϵ2 cos(β̃1∆x/2)). VERIFIED. §7.8 "Interface
  Aligned with an Electric-Field Node", eq. (7.90), with "ϵra is the relative permittivity of the node at the
  interface". VERIFIED. The tests' closed forms r_d = (e^{ik1dx} − e^{ik2dx})/(e^{ik2dx} − e^{−ik1dx}) (H node) and
  r_d = (sin k1dx − sin k2dx)/(sin k1dx + sin k2dx) (E node, eps_a the arithmetic mean) were derived independently;
  their moduli equal (7.72) and (7.90) to round-off (checked at n = 2, dx = 0.05, Sc = 0.5, f = 0.5, 1.0, 1.5:
  0.337501, 0.350718, 0.375501 and 0.329152, 0.315719, 0.289789 on both sides). VERIFIED.
* The TF/SF method: §3.10 "Total-Field/Scattered-Field Boundary", §8.5 "The TFSF Boundary for TMz Polarization",
  §9.5 "TFSF Boundary" (table of contents and text). VERIFIED (cited for the method; the engine's incident field — an
  exact discrete plane wave from the dispersion relation — is its own construction, not taken from the book).
* CPML: §11.1 "Arguably the best PML formulation today is the Convolutional-PML (CPML)" — the book's chapter 11
  implements the un-split PML, not CPML's recursive coefficients; those are in §2. VERIFIED (the statement).

## 2. The convolutional PML — Roden & Gedney 2000

J. A. Roden, S. D. Gedney, "Convolution PML (CPML): An efficient FDTD implementation of the CFS-PML for arbitrary
media", Microwave Opt. Technol. Lett. 27(5), 334–339 (2000), doi 10.1002/1098-2760(20001205)27:5<334::AID-MOP14>3.0.CO;2-A.
NOT FETCHED (paywalled). The formulas the engine uses are quoted from two open papers that cite it:

* P. Yang, "libEMM: A fictious wave domain 3D CSEM modelling library bridging sequential and parallel GPU
  implementation", arXiv:2304.00233 (2023): "The
  convolutional PML (CPML) (Roden and Gedney, 2000) uses sx = κx + dx(x)/(αx + iω) (κx ≥ 1) such that ∂x̃ = (1/κx) ∂x
  + ψx", "ψx^{n+1} = bx ψx^n + ax ∂x^{n+1/2}", "bx = e^{−(dx/κx + αx)∆t}, ax = dx/(κx(dx + κxαx)) (bx − 1)". VERIFIED
  (fractions spread over lines in the text layer).
* V. C. Obieke (Oregon State University), "Communication Strategy Selection for Multi-GPU 3D FDTD with
  Convolutional Perfectly Matched Boundary Layers", arXiv:2606.06910 (June 2026; the author from the title page,
  "Victory Obieke ... Oregon State University", and arXiv's citation_author "Obieke, Victory C."; the earlier
  "the authors' names are not legible" [error in earlier], review B8-fdtd F19). The paper's FDTD is acoustic ("we use
  the first-order acoustic pressure–velocity system"); its CPML recursion is the same as for Maxwell's equations:
  "The recursive coefficients are bx = exp[−(σx/κx + αx)∆t] and ax = σx(bx −1)/[κx(σx + κxαx)]";
  "κx(ρ) = 1 + (κmax − 1)ρ3"; "αx(ρ) = αmax(1 − ρ)"; "Outside the CPML layer, σx = 0, κx = 1, and the memory variable
  is zero". VERIFIED. The engine: b = exp(−(σ/κ + α)dt), a = σ(b − 1)/(σκ + κ²α) (the same), grading
  σ = σmax ρ^m, κ = 1 + (κmax − 1)ρ^m, α = αmax(1 − ρ).
* The default σmax = 0.8(m + 1)/(dx η) is the estimate usually attributed to Taflove & Hagness (Computational
  Electrodynamics, 3rd ed., 2005): NOT FETCHED (the book was not obtained). An open secondary source: J. Corbino,
  "Solving Maxwell's Equations with Mimetic Methods", arXiv:2603.19056, eq. (29): "A common estimate for the maximum
  conductivity is [2] σmax = 0.8 (p + 1) / (η ∆x)", its [2] being Taflove & Hagness, 3rd ed. (2005). VERIFIED (the
  fraction typeset over three lines; review B8-fdtd F19). The engine's 1/√(εμ) is η's vacuum case. It is used only as
  a default scale; the reflection it gives is measured (§8), including at grazing incidence (F10).

## 3. Sub-pixel averaging — Farjadpour et al. 2006, Kottke et al. 2008

* A. Farjadpour, D. Roundy, A. Rodriguez, M. Ibanescu, P. Bermel, J. D. Joannopoulos, S. G. Johnson, "Improving
  accuracy by subpixel smoothing in the finite-difference time domain", Opt. Lett. 31, 2972 (2006); the authors' copy
  `math.mit.edu/~stevenj/papers/FarjadpourRo06.pdf`. Eq. (1): "˜⑀−1 = P具⑀−1典 + 共1 − P兲具⑀典−1 , 共1兲 where P is the
  projection matrix Pij = ninj onto the normal. The 具¯典 denotes an average over the voxel" (the text layer's bracket
  glyphs as printed). VERIFIED. "When ˜⑀−1 is not diagonal, we obtain Dy and Dz at the Ex point by simply averaging
  the Dy and Dz components from their four adjacent Yee points". VERIFIED: the engine keeps only the diagonal element.
  The paper names that scheme and its convergence: "We also consider the VP-EP scheme, which is exactly the diagonal
  part of Eq. (1) for s = 1. Both Kaneda and VP-EP are equivalent to Eq. (1) for flat interfaces oriented along the
  grid (xyz) directions, but they do not satisfy the perturbation criterion for diagonal interfaces" and "Previous
  smoothing schemes do not satisfy this criterion and are therefore expected to have only linear convergence in
  general" (the VP-EP's reference mark "7" and the hyphenation as printed). VERIFIED (review B8-fdtd F6). The engine's
  documents called the error "between first and second order" [error in earlier]; measured (§8): second order for
  TM (the diagonal is the full tensor there), first order for TE at ε = 6.
* C. Kottke, A. Farjadpour, S. G. Johnson, "Perturbation theory for anisotropic dielectric interfaces, and
  application to sub-pixel smoothing of discretized numerical methods", Phys. Rev. E 77, 036611 (2008),
  arXiv:0708.1031 (fetched; the title VERIFIED on its first page). Cited for the justification only. (An earlier search
  under the wrong arXiv numbers 0801.1031 and physics/0608198 returned unrelated papers; discarded.)
* Meep's documentation (Materials page, meep.readthedocs.io): "Meep only does subpixel averaging of the nondispersive
  part of ε (and µ)." VERIFIED — the engine likewise staircases dispersive, conducting and PEC bodies.

## 4. Dipole radiation and the 2-D line source

* The time-averaged power of an oscillating dipole: Wikipedia "Dipole" (wikitext fetched 2026-11-04):
  "P = \frac{\mu_0 \omega^4 p_0^2}{12\pi c}". VERIFIED; with mu0 = 1/(eps0 c^2) it is omega^4 p0^2/(12 pi eps0 c^3).
  Jackson, Classical Electrodynamics, 3rd ed., eq. 9.24 (cited in the test's docstring as the textbook form): NOT
  FETCHED (book). In the solver's units with the current moment I l = −i omega p: P = omega² |I l|²/(12 pi).
* The 2-D line source: P' = omega |I|²/8 (and its dual for a magnetic current) is derived in the test's docstring from
  the far field of H_0^(1); the asymptotic form: DLMF 10.17.5 "H_ν^(1)(z) ∼ (2/(πz))^{1/2} e^{iω} Σ i^k a_k(ν)/z^k"
  with 10.17.2 "ω = z − ½νπ − ¼π". VERIFIED (dlmf.nist.gov/10.17).

## 5. The cylinder series (`core.optics.cylinder`)

Bohren & Huffman, *Absorption and Scattering of Light by Small Particles* (1983), ch. 8: NOT FETCHED (book). The
coefficients, efficiencies and the angular pattern are derived in the module from the boundary conditions and the
Hankel asymptotics (DLMF 10.17.5, §4); the tests check them without the book: the boundary conditions at the surface
(to 1e-7 of the field scale at a relative offset of 1e-10), Q_ext = Q_sca for lossless and PEC cylinders (1e-13),
the integral of the pattern equals Q_sca (1e-12), the Rayleigh limit of a thin TM cylinder from the radiation of a line
dipole (residual 1.9e-3, 5.7e-4, 1.6e-4 at x = 0.02, 0.01, 0.005), and the FDTD solver as a second method.

## 6. Meep (comparison only)

* Meep 1.35.0, conda-forge package `pymeep-1.35.0-nompi_py311h17b0aba_100` (uploaded 2026-10-09; md5
  ac2c01bcd96102571b9d2d048d431fc5), licence in the conda record "GPL-2.0-or-later". The repository's licence file:
  `LICENSE` (GitHub's licence API names `LICENSE`, GPL-2.0), first lines "GNU GENERAL PUBLIC LICENSE / Version 2,
  June 1991"; a source header (src/fields.cpp, lines 4–6, read for the licence statement only): "either version 2,
  or (at your option) any later version". VERIFIED. No other part of Meep's code was read.
* The susceptibilities (Meep docs, Materials, "Material Dispersion"): the Lorentzian term σn ωn²/(ωn² − ω² − iωγn),
  "Actually, the numbers that one specifies are fn = ωn/2π and γn/2π"; the Drude form "d²Pn/dt² + γn dPn/dt =
  σn(x) ωn² E", the term "i σn ωn² / (ω (γn − iω))"; "Meep's definition of ω uses a sign convention exp(−iωt)".
  VERIFIED. So `DrudeSusceptibility(frequency=fp, gamma=γ, sigma=1)` gives −fp²/(f² + i γ f), the engine's
  `Drude(fp, γ)`.
* The Python interface (Meep docs, Python User Interface): `is_integrated` is a parameter of the source's time
  dependence ("is_integrated [boolean] — If True, the source is the integral of the ..."). VERIFIED (the first attempt
  passed it to `Source` and failed; corrected).

## 6a. The pole updates and their stability — Bidégaray-Fesquet 2008 (review B8-fdtd F13)

B. Bidégaray-Fesquet, "Stability of FD–TD schemes for Maxwell–Debye and Maxwell–Lorentz equations",
arXiv:math/0506289 (2005); SIAM J. Numer. Anal. 46(5), 2551–2566 (2008), doi 10.1137/060671255 (the journal reference
from arXiv's abstract page and Crossref's record: VERIFIED). Read in the arXiv text.

* Notation: "λ = c∞ k/h is the CFL constant", "q = −λ2 (eiξ − 2 + e−iξ ) = 4λ2 sin2 (ξ/2)", "ε′s = εs /ε∞ ≥ 1 denotes
  the normalized static permittivity", "ω = ω12 k2 /2 > 0 denotes the normalized squared frequency" (k the time step,
  h the cell). VERIFIED.
* The engine's Lorentz/Drude update is her "Lorentz–Young model" (Young, IEEE Trans. Antennas Propag. 43(4), 422–426
  (1995), her [9]: NOT FETCHED), eq. (15): (P^{n+1} − P^n)/k = J^{n+1/2}, (J^{n+1/2} − J^{n−1/2})/k = −(ν/2)(J^{n+1/2}
  + J^{n−1/2}) + ω1²(εs − ε∞)ε0 E^n − ω1² P^n, which is the engine's central difference at t_n. The reviewer's
  `s07b_young_matrix.py` shows the engine's amplification matrix equal to her printed G to 12 digits. VERIFIED.
* Her conditions for it: "there is an extra condition on the time step: ω < 2/(2ε′s − 1)" and "as for the
  Lorentz–Joseph et al. scheme we need a twice smaller k than for raw Maxwell equations: q ≤ 2 instead of q ≤ 4"; in
  2-D "condition q ≤ 2 becomes k ≤ h/(2c∞)". VERIFIED. In the engine's terms: c∞ Δt / dx ≤ 1/√2 (1-D), 1/2 (2-D), and
  ω0 Δt ≤ 2/√(2 εs/ε∞ − 1). Her 3-D case: "is being studied" (no condition stated). These are sufficient: her
  characteristic polynomial (printed after eq. (15)) has all roots on the closed unit disk up to q ≈ 3.9 for small ω
  (computed while processing the review; e.g. ε′s = 2.25, ω = 0.05: max|Z| = 1 at q = 3.5), and the engine admits by
  its computed radius; `test_published_pole_conditions_are_sufficient_for_the_engine` checks that every sampled medium
  satisfying them is admitted. The engine's earlier refusal hint "ω0·Δt < 2 and plasma frequency·Δt < 2·√ε∞" was not
  the published condition [error in earlier]; for a Drude pole (ω0 → 0 at fixed Δε ω0² = ωp²) her condition gives
  ωp Δt ≤ √(2 ε∞) — derived here, not stated by her.
* The engine's Debye trapezoid is her "Debye–Joseph et al. model" (Joseph, Hagness & Taflove, Opt. Lett. 16, 1412
  (1991), her [8]: NOT FETCHED), eq. (10); "the stability condition is q ≤ 4 if εs > ε∞ and q < 4 if εs = ε∞" (the
  vacuum condition). VERIFIED.
* She recommends another Lorentz scheme: "the Kashiwa et al. model seems to overcome others for Lorentz material"
  (stable for q < 4 with no extra condition). VERIFIED. Not adopted (the engine keeps Young's scheme, Meep's form of it
  is compared in `tests/external`; recorded as an option in STATUS).

## 7. Exact references reused from the engine

Fresnel coefficients and the multilayer stack: `core.optics.interfaces` (its own verification,
`verification_2026-10-23.md`, and the tmm comparison). The Mie series: `core.optics.mie` (B8's Mie part, its own
verification and tests); used with its stated conventions (incident x-polarized along +z,
E_theta = e^{ikr}/(−ikr) cos φ S2, E_phi = −e^{ikr}/(−ikr) sin φ S1).

## 8. Measured results (the tests; 2026-11-04, CPU in lfphys-viz unless said; re-measured after review B8-fdtd)

"exact" / "monitor": the incident intensity used — the true one, or the incident wave as the flux monitor measures it (`FDTD.monitor_factor`, Meep's convention); the earlier numbers were all "exact" and attributed to the scheme what was partly the monitor's −(k dx)²/8 [error in earlier, F5].

| what | measured |
|---|---|
| dispersion relation, 2-D, 6 wavevectors (0°–90°), 10.7 and 21 cells per wavelength | omega within 2.2e-15 / 5.7e-15 (relative) of the closed form at every angle; the continuum relation off by 1.8e-3–1.7e-2 / 4.5e-4–4.1e-3 (negative control) |
| 3-D dispersion, (2,1,0) at 16 and 32 cells per unit | closed form to 1e-10; phase-velocity error ratio 3.6–4.4 (second order) |
| magic time step (1-D, c dt = dx), 120 steps | max error 4.7e-15; at c dt = dx/2: 0.36 (negative control) |
| discrete energy in a closed PEC box with dielectric and magnetic bodies | relative drift 3.0e-16 (2-D, 3000 steps), 1.6e-16 (3-D, 1500 steps); with H at one time level 0.20 / 0.36 |
| PEC cavity 1 × 0.6875 × 0.4375, 4 lowest modes, matrix pencil | the grid's exact frequencies to 1.4e-14–5.3e-12; the continuum's to 1.6–4.8e-3 (16 cells) and 0.39–1.2e-3 (32): second order |
| PEC/PMC 2-D box, 4 modes with k_y = (p + ½)π/L_y | grid-exact to 1e-8 (asserted); the PEC/PEC modes absent; the box is now 0.625 high (12.5 cells), because a PEC–PMC length is an odd number of half cells: the 0.6 asked before was silently realised as 0.625 (F9) |
| axis lengths, every pair of PEC/PMC/PML sides (size 0.6, dx 0.05) | exact for (pec, pec), (pmc, pmc), (pml, ·); (pml, pmc) was 0.625 [error in earlier], now 0.6; (pec, pmc) 0.625 (the nearest realisable), flagged in `checks()` |
| CPML, 2-D point source 3 cells from the layer, five probes (normal to ~70°) | TM: 10 cells m = 3 −88…−95 dB, 20 cells −106…−113 dB, m = 4 κ 5 α 0.2 −79…−83 dB; controls: 2 cells −15…−30 dB, un-graded −22…−28 dB. TE: −88…−95, −106…−113, −75…−84; controls −15…−29, −22…−30 dB |
| CPML 3-D (dx = 0.1, 10 cells) | below −70 dB (asserted); a 2-cell layer at least 30 dB worse |
| CPML at grazing incidence (source 3 cells above a long boundary, image-path angles 81.5°, 85.7°, 87.1°; F10) | 10 cells −74.5 / −57.6 / −52.4 dB; 20 cells −114…−136 dB; κ 5 α 0.2 down to −60 dB |
| CPML 1-D, 20 cells, normal incidence (the Meep module's control) | −109 dB at 20 and 40 cells per unit (Meep's PML 1.5 units: −105 / −130 dB) |
| normal-incidence R: dielectric n = 2, conductor, Drude, Debye, Lorentz; TM and TE; interface on an H or E node | monitor-normalised: the grid's exact R (Schneider 7.72 / 7.90 with the scheme's eps) to 2e-6 … 9.6e-5; exact-normalised: low by the monitor factor cos(k dx/2), −0.3 … −2.8 % at 20 cells (to 2e-16 of it). Fresnel with the model's eps (monitor-normalised, the scheme's own error) at 40 cells: n = 2 +0.6…+5.8 % (H node) / −0.6…−5.7 % (E node), conductor +0.4…+4.0 %, Drude +0.12…+0.22 %, Debye +0.6…+4.7 %, Lorentz +0.5…+3.1 %; ratio 3.8–4.6 between 20 and 40 cells. n = 2 at 10 cells per wavelength in the medium: +10.7 % (H node) / −10.3 % (E node) of R; the exact-normalised +9.3 % / −11.4 % stated before contained the monitor's −2.4 % [error in earlier] |
| oblique incidence (Bloch, 24°–42°), s and p; pulse 1.2 ± 0.1 (it was ± 0.12, whose spectrum at the cut-off gave a window tail of 1.3e-6, now refused, F7) | s: the grid's exact R to 4.3e-5 (monitor factor cos(k_x dx/2) cos²(k_y dx/2)); Fresnel (monitor-normalised) s 4.0–16.6 % / 1.0–3.8 %, p 12–22 % / 2.9–4.9 % at 20 / 40 cells, ratio 4.1–4.4 |
| Brewster's angle, p (pulse 1.0 ± 0.025) | R_p = 9.0e-5 (20 cells per wavelength), 5.5e-6 (40): |r_p| second order; s at the same angle 0.15 |
| the flux monitor on the incident wave alone, 2-D TM and TE, 0°, 30°, 45°, 10–40 cells per unit (F5) | measured flux = `incident_intensity("monitor")` × the discrete direction cosine to 5e-11 … 1.6e-9; the closed form TM cos(k_x dx/2) cos²(k_y dx/2), TE cos(k_x dx/2) (−0.04 … −7 %) |
| point dipole, 3-D, f = 0.8–1.2 | P / (omega² |I l|²/(12 pi)) − 1 below 2 % at 20 cells per wavelength, ratio 3–5 to 10 cells |
| line source, 2-D (TM: J; TE: M) | 1.0011–1.0025 (TM) and 1.0018–1.0041 (TE) at 40 cells per wavelength; second order |
| TF/SF leak, 2-D TM/TE at 0°, 30°, 57°; 3-D normal incidence | 2–3e-9 of the incident peak (asserted < 1e-7); with the continuum wavenumber instead of the grid's: > 1e-4 (negative control) |
| TF/SF Bloch slab with two finite faces (F7), pulse 1.2 ± 0.15 | k_par = 2π·0 / 0.3: leak 1.8–2.5e-9; 2π·0.5: window tail 9.5e-7 (accepted), leak 3.4e-7; 2π·0.6: tail 1.8e-5, the same for M = 4096 … 65536 (a precursor of the spectrum cut at the cut-off, not the window's length), now refused; ± 0.08 at 2π·0.6: leak 2.3e-9 |
| hard sources (F2) | 1-D magic step: hard E_z and hard H_z both radiate f(t − \|x − x0\|) to 1.5e-8 (the profile's own jump; hard H_z was 3.8e36 before); 2-D: hard H_z (TE) equals hard E_z (TM) of the half-step-delayed profile to 1e-4 of the peak (86 % before) |
| stability of mixed nodes (F11) | E nodes eps 0.25 next to H nodes mu 0.25 (media eps 0.25 mu 4 and eps 4 mu 0.25): refused at S = 0.5 (NaN after 500 steps before), accepted at S = 0.24 and conserved to 1e-10 over 4000 steps |
| TF/SF with a ramped continuous wave (30°, ramp 6) | during the ramp up to 4e-4 (2.4e-3 for a ramp of 2); afterwards 1.6e-7 … 1.3e-8; amplitude 1 to 1e-7 |
| dielectric cylinder m = 1.5, a = 0.5, x = 1.3–3.1 | Q_sca at 20 / 40 / 80 cells per unit: TM exact +0.11…+0.21 % / +0.03…+0.06 % / +0.007…+0.016 %, monitor +0.39…+1.47 % / +0.10…+0.37 % / +0.024…+0.093 % (ratios 3.3–4.0); TE exact −0.02…+0.89 % / −0.12…+0.29 % / −0.09…+0.11 %, monitor +0.18…+2.13 % / −0.07…+0.60 % / −0.08…+0.19 % (not monotone at f = 0.4); far field at 40 cells within 0.4 / 0.7 % (TM) and 0.6 / 0.9 % (TE) of the pattern's peak. The earlier "0.03–0.3 %" was the exact normalisation, whose smaller numbers come from the monitor's bias cancelling part of the scheme's error [error in earlier] |
| high-contrast cylinder eps = 6, TE, f = 0.5 (GPU 0; F6) | Q_sca +2.62 / +1.44 / +0.77 % (exact), +2.70 / +1.46 / +0.78 % (monitor) at 40 / 80 / 160 cells: ratios 1.83, 1.86 — first order (the VP-EP diagonal); f = 0.6, 0.8 not monotone |
| PEC cylinder (staircase), f = 0.4, 0.7, 1.0 | exact: TM −3.2…−4.6 % / −1.6…−2.0 % / −0.78…−0.90 % at 20 / 40 / 80 cells (first order); TE with the edge rule −0.5…+9.0 % / −1.7…+1.0 % / −0.8…+0.4 %, with the node rule +10…+30 % / +2.8…+6.8 % / +1.6…+3.8 % (the earlier TM −2.7…−4.0 % / −1.5…−1.9 % / −0.8 % and TE −0.3…+6.4 % / −1.2…+1.4 % / −0.7…+0.6 % were not this test's; the original code gives the numbers above [error in earlier]) |
| lossy cylinder (eps 2, sigma 1), 40 cells | sigma_abs −0.6…+0.1 % (exact) / −0.5…+0.3 % (monitor), sigma_sca −0.6…−0.5 % / −0.5…−0.2 % of the series (complex m from eps(f)); the volume integral of the absorbed power within 0.12 % of the flux (asserted 3 % and 2 %) |
| sphere m = 1.5, a = 0.5, x = 1.26–2.51 | Q_sca at 16 cells per unit +1.66 / +0.33 / +1.20 % (exact), +1.97 / +1.03 / +2.47 % (monitor); at 32 (GPU 0) +0.76 / −0.01 / +0.30 % (exact), +0.84 / +0.16 / +0.61 % (monitor); dsigma/dOmega at four directions off by up to 5.9 % / 7.2 % (16) and 1.9 % / 2.0 % (32). The earlier "0.01–0.8 %" and "between first and second order" rested partly on the monitor's bias [error in earlier] |
| GPU = CPU | real fields bit for bit (2-D TM, TE, both; 3-D; PML, Drude + Debye, Lorentz, conductor, PEC, TF/SF, sources, monitors); Bloch (complex) fields within 2.3e-15 |
| Meep 1.35.0, 20 rows, like-normalised (F5, F8; `comparison_2026-11-04_meep.md`, a one-off run outside the repository since 2026-11-10) | slab R (f = 0.6–1.4, 40 cells): engine − Meep 1.6e-7 … 1.1e-6, both within 1.8e-6 of the grid's exact discrete R; Drude R: 1.6e-7 … 6.3e-6 (Meep's Drude update differs at second order: 2.4e-5 / 5.4e-6 from R_d at 20 / 40 cells); cylinder Q_sca: 2e-4 … 6.4e-3, within the coarser-grid bounds (largest diff/tol 0.32); the engine's TE error at f = 0.4 not monotone over 20/40/80 cells (strict xfail). Before the review the engine was exact-normalised: the 1-D rows then differed by 6e-4 … 6e-3, and "the engine nearer the exact value in 13 of 18 rows" was an artefact of the monitor's bias [error in earlier] |
