# lfphys source verification — 2026-11-04, plan item P14.7 (batch B8): optical vortices

Purpose: every formula, quotation and number used by `core.optics.beams`, `core.optics.beams_rotation`,
`theories.approx.beams_thin_masks` (until review B8-beams, O7: `core.optics.beams_generation` and the rough surface of
`beams_rotation`), `theories.approx.beams_paraxial`, their tests (`tests/test_beams.py`, `tests/test_beams_thin_masks.py`,
`tests/test_beams_paraxial.py`) and the visualization `v16_optical_vortices`, checked against the source text. Texts
fetched on 2026-11-04 from arXiv, open-access publisher pages, authors' pages and university repositories, converted
with `pdftotext` (with and without `-layout`); where `pdftotext` garbled an equation it was read from the rendered page
image (marked [img]). Abstracts of closed papers through the publishers' abstract pages and OpenAlex (no contact
parameter). No e-mail address or personal identifier was sent with any request; no access barrier (captcha, login) was
bypassed. The full texts are kept outside the engine (the session's scratch folder), not here. Status codes as in
`verification_2026-10-23.md`: VERIFIED (quoted) / DIFFERS (both given) / NOT FOUND / NOT FETCHED (what replaces it is
said).

**Where the engine does not depend on a source.** Every formula the engine computes is tested against a second route
(finite differences of Maxwell's and Helmholtz's equations, quadratures, the angular spectrum, overlap integrals,
measured spectra). Where a source could not be obtained, the formula is derived in the module's docstring and its
test is the evidence; the citation is then only an attribution, marked "текст не получен" in `ABOUT["basis"]`.

## 1. Bliokh, Alonso, Ostrovskaya, Aiello — spin–orbit interaction of nonparaxial light

K. Y. Bliokh, M. A. Alonso, E. A. Ostrovskaya, A. Aiello, "Angular momenta and spin-orbit interaction of nonparaxial
light in free space", Phys. Rev. A 82, 063825 (2010), doi 10.1103/PhysRevA.82.063825; text arXiv:1006.3876v3.

* Sec. IV, Eq. (24): "we take non-paraxial vector Bessel-beam solutions which are eigenmodes of Ĵz constructed from
  plane waves with welldefined helicity σ" … "Ẽσℓ = eσ (θ, φ) Ẽℓσ (θ, φ) , Ẽℓσ = Aσ δ (θ − θ0 ) eiℓφ". Basis (Sec. II):
  "e± = e±imφ (eθ ± ieφ ) / √2" … "Hereafter we choose the gauge m = 1". VERIFIED → the engine's construction: the
  plane wave of helicity σ carries e^{i(l+σ)φ_k}(θ̂ + iσφ̂)/√2 (`VortexBeam`, `vector_bessel_beam`), the same as
  Bliokh's with ℓ = l.
* Eq. (25) [img]: "Lz = ℓ + σ̄ ΦB/2π , Sz = σ̄ (1 − ΦB/2π) , Jz = ℓ + σ̄." Eq. (26): "ΦB = ∮ AB · dk = 2π (1 − cos θ0 )".
  "σ̄ = (|A+|² − |A−|²)/(|A+|² + |A−|²) is the averaged helicity". VERIFIED → `bessel_per_photon` and the closed forms of
  `VortexBeam.moments`.
* The general form for a spectrum (S_z = σ⟨cos θ⟩, L_z = l + σ(1 − ⟨cos θ⟩), ⟨⟩ over |A|² q dq): Eq. (22), "S = i (eσ ×
  eσ∗) |Ẽσ|² d2k⊥ = σκ |Ẽσ|² d2k⊥" (integral signs lost in the text layer), with "κ = k/k" (Sec. II) and the
  normalisation of App. A, Eq. (A7): "the energy per unit z-length which is obtained by the 2D integration of the
  time-averaged intesity" [sic], W = ω ∫ |Ẽσ|² d²k⊥ (one photon per unit z-length). Together: S_z = σ⟨κ_z⟩ = σ⟨cos θ⟩
  with the weight |Ẽ|² d²k⊥ (= |A|² q dq dφ in the engine's notation) for any spectrum. VERIFIED (combination of the
  printed Eq. 22 and A7; re-fetched 2026-11-04 by the processing of review B8-beams, O17, and grepped); measured on sampled
  fields (`test_vector_beam_angular_momentum_per_photon`: agreement to 1e-8). [error in earlier: "NOT FOUND as printed"
  — the formula follows from the printed Eqs. 22 and A7.] This is the canonical split **per unit length**; v16 labels
  it so (review O3, O10).
* Eq. (21): "L = ∫ r × πo d²r⊥ , S = ∫ r × πs d²r⊥ ." (per unit length). VERIFIED. For a z-invariant Bessel beam this
  equals the integral of the spin density; for a focused beam the engine finds the difference ½ d/dz ∫ r·S⊥ dA
  (derived), which for one helicity has the closed form (σ/2)⟨sin²θ/cos θ⟩ per photon, the same on every plane
  (derived from Bliokh, Bekshaev & Nori's Eq. 3.50, §3 below; review B8-beams, O4; measured at z = 0, near the waist
  and at z_R in `test_poynting_angular_momentum_closed_form_on_every_plane`); the paper does not discuss it (NOT
  FOUND).
* Footnote [28]: "the Bessel beams cannot be normalized and we calculate the finite ratio … to the infinite norm".
  VERIFIED (why the engine's per-photon tests use beams with a finite spectrum, not Bessel beams).
* The coordinate-space canonical momentum and spin densities are NOT FOUND in this paper (they are in §2 and §3 below).

## 2. Berry — optical currents

M. V. Berry, "Optical currents", J. Opt. A: Pure Appl. Opt. 11, 094001 (2009), doi 10.1088/1464-4258/11/9/094001;
the published PDF on the author's page (publication no. 414).

* Eq. (3.2)–(3.3): "Efull (r , t) = Re E3 (r ) exp(−iωt)" … "P3 (r ) = ½ Re E3∗ (r ) × H3 (r )". Eq. (3.5) [img]:
  "P3 = (c²/2ω) ε0 Im E3∗ × (∇3 × E3 ) = (c²/2ω) ε0 [Im E3∗ · (∇3 ) E3 + ½ ∇3 × Im E3∗ × E3 ] = P3orb + P3sp".
  VERIFIED → the engine's time convention exp(−iωt), `poynting` = Re(E* × H)/2, and the decomposition tested pointwise in
  `test_berry_decomposition_pointwise` (dual-symmetric form, §3).
* Eq. (3.11) and the text after it: the magnetic representation "in which the separate terms are different from
  their electric counterparts"; "restoring the electric–magnetic democracy … simply by averaging the two
  representations". VERIFIED → the engine uses the averaged (dual-symmetric) densities.
* Eq. (3.24): "although the Poynting vector depends quadratically on the field, it separates into the sum of the two
  helicities: there are no cross terms between + and −". VERIFIED (consistent with the incoherent sum over helicities
  in `VortexBeam.moments`).

## 3. Bliokh, Bekshaev, Nori — dual electromagnetism

K. Y. Bliokh, A. Y. Bekshaev, F. Nori, "Dual electromagnetism: helicity, spin, momentum and angular momentum",
New J. Phys. 15, 033026 (2013), doi 10.1088/1367-2630/15/3/033026 (open-access PDF; arXiv:1208.4523v4).

* Sec. 2.1: "assume natural units ε0 = µ0 = c = 1". VERIFIED → the engine's units.
* Eq. (3.40): "W̄ = ¼ (|E|² + |B|²), P̄ = ½ Re(E∗ × B)"; Eq. (3.42): "P̄O = (1/4ω) Im [E∗ · (∇) E + B∗ · (∇) B]";
  Eq. (3.43): "P̄S = (1/8ω) ∇ × Im [E∗ × E + B∗ × B]"; Eq. (3.45): "S̄ = (1/4ω) Im (E∗ × E + B∗ × B)"; p. 19: "P̄S = ½ ∇ ×
  S̄"; Eq. (3.27): "P = PO + PS". VERIFIED [img for the prefactors] → `energy_density`, `poynting`, `orbital_momentum`,
  `spin_density` (with H = B in these units).
* p. 20, Eq. (3.50): "If the field has a well-defined quantum helicity σ = ±1 … the complex electric and magnetic
  amplitudes are related as Ê = iσ B. In this case … H̄ = σ W̄/ω , S̄ = σ P̄/ω" and "in such a pure helicity state, the
  electric and magnetic contributions are equal in all quantities". VERIFIED → the engine's H = −iσE (the same
  relation: E = iσH ⇔ H = −iσE for σ = ±1). Re-read on the rendered page 16 of arXiv:1208.4523v4 (2026-11-04, review
  B8-beams): "H̄ = σ W̄/ω , S̄ = σ P̄/ω (3.50)". Also used for the closed form of the Poynting angular momentum (§1).
* The corrigendum New J. Phys. 18, 089503 (2016): NOT FETCHED (the publisher returned a bot check); its content is not
  known here.

## 4. Barnett & Allen 1994; Barnett 2002; Monteiro, Maia Neto & Nussenzveig 2009 — nonparaxial beams and the split of the angular-momentum flux

* S. M. Barnett, L. Allen, "Orbital angular momentum and nonparaxial light beams", Opt. Commun. 110, 670 (1994), doi
  10.1016/0030-4018(94)90269-0: NOT FETCHED (no legal copy found). Secondary account (Monteiro et al. 2009, below,
  grepped): "They took a general nonparaxial cylindrically symmetric beam containing a phase factor eiℓφ. Besides the
  ambiguity in the identification of spin and orbital contributions, the ratio between the total angular momentum per
  unit length and the total energy per unit length was found not to be (ℓ + σ)/ω as in the case of a paraxial beam",
  and "The nonparaxial focused beam model, as derived here, does not coincide with the Barnett-Allen model". VERIFIED
  (the secondary account). So J_z = l + σ per photon is a property of the engine's construction — the J_z eigenstate of
  Bliokh et al. 2010, each plane wave of helicity σ carrying e^{i(l+σ)φ_k} (§1) — not of every nonparaxial beam with a
  phase e^{ilφ}; `beams.py` and its ABOUT say so (review B8-beams, O17).
* S. M. Barnett, "Optical angular-momentum flux", J. Opt. B: Quantum Semiclass. Opt. 4, S7 (2002), doi
  10.1088/1464-4266/4/2/361: abstract only (OpenAlex): "(ii) The angular-momentum flux for a light beam about its axis
  (or propagation direction) can be separated into spin and orbital parts. This separation is gauge invariant and does
  not rely on the paraxial approximation." VERIFIED at the level of the abstract. The full text returned a bot check:
  NOT FETCHED; its form of the split is taken from Monteiro et al. below.
* P. B. Monteiro, P. A. Maia Neto, H. M. Nussenzveig, "Angular momentum of focused beams: beyond the paraxial
  approximation", Phys. Rev. A 79, 033830 (2009), arXiv:0902.3214v1 (fetched 2026-11-04 for review B8-beams, O3; text
  grepped, Eq. 33 read on the rendered page 8 [img]): "Barnett has shown that the total angular momentum flux … through a
  plane parallel to the xy plane can be separated into two gauge-independent contributions respectively associated to
  the polarization and to the spatial field structure [28]"; Eq. (33): M^spin = (σ/2ω) √(ε/μ0) ∫dρ ρ ∫dφ (|Ex|² +
  |Ey|²) [img], for their focused beam of one helicity (orders ℓ, ℓ + σ, ℓ + 2σ, as in the engine); "we conclude that r
  is positive and does not depend on the sign of ℓ nor on the value of σ" (the spin flux per unit power grows in
  magnitude, |M^spin/F| > 1/ω); "To our knowledge, a consistent identification of spin and orbital contributions to the
  local angular momentum or flux densities of nonparaxial beams is not available". VERIFIED → `VortexBeam.moments()`
  (S_flux = σ̄⟨(1 + cos²θ)/2⟩/⟨cos θ⟩, derived here from Eq. 33 by Hankel–Parseval) and `angular_momentum()` (M_spin =
  −∫Im(E⊥*·H⊥) dA/(2ω): Eq. 33 for each helicity in natural units, no cross terms between helicities — derived here);
  measured in `test_barnett_flux_split_against_the_canonical_split` (agreement 1e-9 near the waist). The canonical split
  per unit length (§1) and this flux split are two published definitions; v16 shows both and says that only J_z = l + σ
  is independent of the definition.

## 5. The rotational Doppler effect

* J. Courtial, K. Dholakia, D. A. Robertson, L. Allen, M. J. Padgett, Phys. Rev. Lett. 80, 3217 (1998), doi
  10.1103/PhysRevLett.80.3217. Full text NOT FETCHED; the APS abstract: "We observe the frequency shift, l Ω , imparted
  to a mm-wave beam with an orbital angular momentum of l ħ per photon, when the beam is rotated at angular frequency
  Ω." VERIFIED. Courtial's PhD thesis (St Andrews, 1999; its §6.3.1 "has been published in ref. [26]" = this paper):
  "uniform rotation of the cylindrical lenses or Dove prism with frequency F/2 causes the transmitted beam to rotate
  with frequency F"; "a Mach-Zehnder interferometer with a Dove prism in each arm, one rotating, the other one at rest";
  "beating between two beams with optical frequencies that differ by Δν = lF, where F is the rotation frequency of the
  beam that has been passed through the rotating Dove prism"; source "an Indium Phosphide Gunn diode oscillating at
  94GHz". VERIFIED → v16's Dove prism: the prism at f turns the beam at 2f; the arms beat at |l|·2f (DIFFERS from the
  task's phrasing "(l + σ)Ω": PRL 80 reports l Ω, Ω the beam's rotation rate).
* J. Courtial et al., Phys. Rev. Lett. 81, 4828 (1998), abstract: "The shift is equal to the total angular momentum per
  photon multiplied by the angular velocity between the source and observer … the shifts due to the spin and orbital
  angular momentum components of the light beam act in an additive way"; thesis §6.4 [img]: "Δν = (l + σ)F (6.15)" with
  a Dove prism and a half-wave plate both turning at F/2. VERIFIED → the engine's mirror-like vector rotator
  (`image_rotator(..., vector=True)`, tested: shift (l_out + σ_out)·2Ω_p).
* M. P. J. Lavery, F. C. Speirits, S. M. Barnett, M. J. Padgett, "Detection of a spinning object using light's orbital
  angular momentum", Science 341, 537 (2013), doi 10.1126/science.1239936; the accepted manuscript (University of
  Glasgow repository; the typeset version not checked). Eq. (1) [img]: "a rotation of angular frequency Ω between the
  source and observer shifts the frequency by Δf = (ℓ + σ) Ω/2π"; Eq. (3) [img]: "the Doppler frequency shift of the
  on-axis scattered light is given as Δf = (ℓλ/2πr) × f0 (Ωr/c) = ℓΩ/2π" and "there is no dependence upon
  polarisation"; Eq. (4) [img]: "their scattering into a common detection mode gives an intensity modulation of
  frequency f_mod = 2|ℓ|Ω/2π"; second configuration: "the SLM and the fibre are now acting as a mode filter" coupling
  "a superposition of ±ℓ into the single-mode fibre". Numbers: "a diode laser at 670 nm", "ℓ = ±18", rotor "driven at
  speeds ranging from 200 – 500 radians per second", "f_mod = 2346 ± 1 Hz"; Fig. 3: "242, 339 and 383 radians per
  second … 1320±20 Hz, 1914±21 Hz and 2124 ± 30 Hz". VERIFIED → `scattered_on_axis_shift` (−lΩ in this engine's sign
  convention), `superposition_beat` (2|l|Ω), v16's disc (illumination by the world's beam l, detection through a ±l
  mode filter: the +l part unshifted, the −l part shifted by −2lΩ, the beat 2|l|Ω; the on-axis part shifted by −lΩ).
  Not used as test values: by Eq. (4) the Fig. 3 beats would be 1386.6, 1942.3, 2194.4 Hz — the reported values are
  1.5–4.8 % lower (arithmetic of this verification, not in the paper; the typeset version was not checked).
  Sign (review B8-beams, O17; the accepted manuscript re-fetched from eprints.gla.ac.uk/85025 on 2026-11-04 and
  grepped): Fig. 2's caption, "For a given input superposition, shown in green, the light scattered from the positive
  ℓ beam will be blue-shifted and that from the negative ℓ beam will be red-shifted", does not state the disc's sense
  of rotation relative to ℓ; the text gives the mechanism, "Doing work against this force is the energy input required
  to shift the frequency of the light". In the engine's conventions (exp(−iωt), Ω > 0 counter-clockwise about +z) the
  light an exp(ilφ) beam scatters onto the axis from a disc turning at Ω is shifted by −lΩ: red when the disc turns in
  the sense of the beam's orbital angular momentum (the light gives lħ per photon to the disc and does work on it),
  blue when it turns against it — the caption's case for the positive ℓ beam. Stated in `beams_rotation`'s docstring.
* B. A. Garetz, "Angular Doppler effect", J. Opt. Soc. Am. 71, 609 (1981): abstract only (an angular Doppler effect
  from the "angular momentum carried by circularly polarized photons"); the printed formula NOT FETCHED.
* I. Bialynicki-Birula, Z. Bialynicka-Birula, "Rotational frequency shift", Phys. Rev. Lett. 78, 2539 (1997): abstract
  only ("scalar product of the angular velocity and the angular momentum of the emitted photon"); the same authors'
  arXiv:1110.2476 gives the shift as MΩ with M the projection of the total angular momentum. The PRL's formula NOT
  FETCHED. The engine's rotating-frame shift ω − mΩ is derived from the rotation property of a J_z eigenstate and
  measured (`test_rotating_observer_measures_omega_minus_m_Omega`).
* Sign convention (all of these): the sources fix the magnitude; the sign depends on the conventions (time factor,
  sense of rotation). The engine states its own (exp(−iωt), Ω > 0 counter-clockwise about +z) and measures every
  shift with its sign from sampled series.

## 6. Modes, converters, Bessel beams, holograms

* L. Allen, M. W. Beijersbergen, R. J. C. Spreeuw, J. P. Woerdman, Phys. Rev. A 45, 8185 (1992): abstract only
  ("well-defined orbital angular momentum"); lħ per photon and the printed LG formula NOT FETCHED. The engine's LG
  formula is checked by the paraxial equation (finite differences), orthonormality, the Fresnel propagation of the
  waist's Hankel spectrum (agreement 2e-16) and the exact propagation.
* M. W. Beijersbergen, L. Allen, H. E. L. O. van der Veen, J. P. Woerdman, "Astigmatic laser mode converters and
  transfer of orbital angular momentum", Opt. Commun. 96, 123 (1993): NOT FETCHED (a copy on a university course page
  exists; not downloaded, its licence for use outside the course being unclear). Secondary (Courtial's thesis, citing
  it): "f = d/√2" and "w0 = sqrt((1 + 1/√2) f λ/π)" for the π/2 converter. The coefficients b(n, m, k) used by the
  engine are the commonly reproduced ones; the engine does not rely on the attribution: in its own conventions it
  measures (overlap integrals, to 1e-10, and the reproduced mode, to 1e-12) that Σ_k i^k b(n,m,k) HG_{N−k,k} =
  (−1)^min(n,m) LG_{min(n,m), m−n} and Σ_k b(n,m,k) HG_{N−k,k} = HG_{n,m} turned by 45°.
* Wikipedia, "Gaussian beam" (revision 1368854400, 2026-08-11): uses the time factor e^{+iωt} with exp(−ikz), the LG
  normalisation "C = sqrt(2p!/(π(p+|l|)!))", exp(−ilφ) and the Gouy phase (N + 1) arctan(z/z_R), N = |l| + 2p. VERIFIED
  (the engine's normalisation; the engine's exp(−iωt) convention is the complex conjugate). The article's own
  sections are inconsistent in the sign of the azimuthal phase (its hypergeometric-Gaussian section uses e^{+imφ}).
  A. E. Siegman, *Lasers* (1986): a book, NOT FETCHED.
* S. M. Barnett, M. Babiker, M. J. Padgett, Phil. Trans. R. Soc. A 375, 20150444 (2017) (accepted version): its LG
  formula (Eq. 6) has e^{iℓφ} and the Gouy factor exp[−i(2p+|ℓ|+1) tan⁻¹(z/zR)] (VERIFIED, the engine's convention),
  but its curvature factor is printed as exp(−ikρ²z/2(z² + zR²)), which contradicts its own v = u e^{ikz} and paraxial
  equation (a finite-difference check gives the residual 3e-8 with + and 0.51 with the printed −). DIFFERS; the engine
  uses + (its test of the paraxial equation fails with the other sign). In the published version (PMC5247487, its
  equation image `rsta20150444-e6.jpg` fetched and read 2026-11-04 for review B8-beams, O17) the same formula is
  Eq. (3.5), with the same printed sign; the substitution and the paraxial equation are its Eqs. (3.2) and (3.4).
  Independently reproduced by the review (`reviews/…_B8-beams/out/s11_barnett2017_sign.txt`: residual 0.46–0.75
  with the printed sign, 3e-10–5e-10 with +).
* J. Durnin, J. Opt. Soc. Am. A 4, 651 (1987); J. Durnin, J. J. Miceli, J. H. Eberly, Phys. Rev. Lett. 58, 1499
  (1987): abstracts only ("exact, nonsingular solutions of the scalar-wave equation for beams that are
  nondiffracting"); the printed J0 form NOT FETCHED. The engine's Bessel beams are checked by Helmholtz's equation
  (finite differences, 1e-7 with a negative control).
* N. R. Heckenberg et al., Opt. Lett. 17, 221 (1992); V. Yu. Bazhenov, M. V. Vasnetsov, M. S. Soskin, JETP Lett. 52,
  429 (1990): NOT FETCHED (an opening paragraph only). The charge m·l of order m is derived from the hologram's Fourier
  series and measured (`test_fork_hologram_order_m_carries_charge_m_l`, three kinds of hologram).
* M. J. Padgett, L. Allen, "The Poynting vector in Laguerre-Gaussian laser modes", Opt. Commun. 121, 36 (1995): NOT
  FETCHED. The spiral of the paraxial flow lines is derived in `beams_paraxial` and tested against traced lines (2e-6
  w0).
* E. Karimi, G. Zito, B. Piccirillo, L. Marrucci, E. Santamato, "Hypergeometric-Gaussian modes", Opt. Lett. 32, 3053
  (2007), arXiv:0712.0782v1: "the HyGG modes with p = −|m| are simply generated by applying the phase factor e^{imφ}
  to a TEM00 laser field at its waist plane" and "the mode HyGG_pm is a superposition of the infinite LG_qm modes with
  same m and any integer q ≥ 0". VERIFIED (the phase is applied by a hologram there, not by a spiral plate) → the
  statement in `beams_thin_masks` (formerly `beams_generation`) that the Gaussian behind the plate is not one LG mode but carries l per photon
  (measured).

## 6a. Numerics noted while processing review B8-beams

* SciPy 1.17.1 (the project image): `scipy.special.ive(0, 1e10)` returns NaN without a warning (also ive(1, 1e10),
  ive(0, 1e12)); the integral of a spiral plate's q^-2 spectrum to infinity reaches such arguments. `gaussian_vortex_
  spectrum` uses the asymptotic series of the difference I_{(n−1)/2} e^{−x} − I_{(n+1)/2} e^{−x} beyond x = 1e6 (tested
  against `ive` where both hold).

## 7. Open

* Barnett 2002 (the split of the flux, the ratios) and Barnett & Allen 1994: the full texts; Beijersbergen et al.
  1993: a licensed copy; Courtial et al. 1998 (PRL 80) and Lavery et al. 2013 in their typeset versions. None of these
  changes what the engine computes (each formula is tested by a second route); they would turn attributions into
  verified quotations.
