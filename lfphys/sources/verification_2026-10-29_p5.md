# lfphys source verification — plan item P5, open quantum systems (2026-10-29)

Purpose: every formula and number used by `core.quantum.open_systems`, `core.quantum.two_level`, `core.quantum.jumps`,
`core.quantum.decoherence` and `theories.alternatives.collapse_baseline`, quoted from source texts fetched on
2026-10-29 (arXiv PDFs and the Steck notes, converted with `pdftotext -layout`; Crossref metadata through
api.crossref.org without any contact parameter). Converted equations are partly garbled; each is given as quoted
fragments plus the reading used, and each reading is checked by a test against an independent route.
Status codes as in `verification_2026-10-23.md`: VERIFIED / NOT FOUND / DIFFERS; in addition DERIVED (not quoted:
derived for the engine, with the check that confirms it).

Sources:

* [CDM] Y. Castin, J. Dalibard, K. Mølmer, "A wave function approach to dissipative processes", AIP Conf. Proc. 275,
  143 (1993) (ICAP-13, Munich 1992); text arXiv:0805.4002v1, https://arxiv.org/pdf/0805.4002 — the conference
  version of the method of Dalibard, Castin & Mølmer, PRL 68, 580 (1992).
* [PK] M. B. Plenio, P. L. Knight, "The quantum-jump approach to dissipative dynamics in quantum optics", Rev. Mod.
  Phys. 70, 101 (1998); text arXiv:quant-ph/9702007v1, https://arxiv.org/pdf/quant-ph/9702007.
* [M] D. Manzano, "A short introduction to the Lindblad master equation", AIP Advances 10, 025106 (2020); text
  arXiv:1906.04478, https://arxiv.org/pdf/1906.04478.
* [S] D. A. Steck, "Quantum and Atom Optics", revision 0.16.11 (28 October 2026),
  https://atomoptics.uoregon.edu/~dsteck/teaching/quantum-optics/quantum-optics-notes.pdf (Open Publication
  License), chapter 5.
* [B] A. Bassi, K. Lochan, S. Satin, T. P. Singh, H. Ulbricht, "Models of wave-function collapse, underlying
  theories, and experimental tests", Rev. Mod. Phys. 85, 471 (2013); text arXiv:1204.4325v3,
  https://arxiv.org/pdf/1204.4325.
* [H] K. Hornberger, "Introduction to decoherence theory", text arXiv:quant-ph/0612118v3,
  https://arxiv.org/pdf/quant-ph/0612118.
* [BCOR] S. Blanes, F. Casas, J. A. Oteo, J. Ros, "The Magnus expansion and some of its applications", Phys. Rep. 470,
  151 (2009); text arXiv:0810.5488v1, https://arxiv.org/pdf/0810.5488.
* [Ma] P. Massart, "The tight constant in the Dvoretzky-Kiefer-Wolfowitz inequality", Ann. Probab. 18, 1269 (1990):
  the abstract only, from https://api.crossref.org/works/10.1214/aop/1176990746.
* [AH] A. H. Al-Mohy, N. J. Higham, "A new scaling and squaring algorithm for the matrix exponential", SIAM J. Matrix
  Anal. Appl. 31, 970 (2009): the abstract only, from https://api.crossref.org/works/10.1137/09074721X; and the
  docstring of `scipy.linalg.expm` (SciPy 1.17.1 in the image lfphys-viz).

---

## 1. The Lindblad form and its jump operators (`open_systems`) — VERIFIED

[CDM] Eq. (2): "Lrelax(ρS) = −1/2 Σm (Cm† Cm ρS + ρS Cm† Cm) + Σm Cm ρS Cm†", with Eq. (1)
"ρ̇S = (i/ħ)[ρS, HS] + Lrelax(ρS)"; "It is assumed here to be local in time ... (Markov approximation)". For
"C1 = √Γ|g⟩⟨e|", Eq. (3): "(ρ̇S)ee = −Γ(ρS)ee", "(ρ̇S)eg = −(Γ/2)(ρS)eg". Reading used: the jump operators carry
the square roots of their rates (`liouvillian(H, c_ops)`; QuTiP uses the same convention, `test_ext_open_qutip.py`).

[M] Eq. (101): "|ρ(t)⟩⟩ = Σi e^{Λi t} |ΛiR⟩⟩⟨⟨ΛiL|ρ(0)⟩⟩" (the eigendecomposition route of `propagate(method="eig")`);
"For any finite system, Evans' Theorem ensures the existence of at least one zero eigenvalue of the Liouvillian
matrix"; "The eigenvector corresponding to this zero eigenvalue would be the steady-state of the system. In exceptional
cases, a Liouvillian can present more than one zero eigenvalues" (the uniqueness check of `steady_state`).
**DIFFERS (typo in the source).** [M] Eq. (93) prints the anticommutator as "{Lk Lk†, ρ}"; its own Eq. (92)
has "Fj† Fi" and [CDM] Eq. (2) has "Cm† Cm". The engine uses L†L; the two routes `liouvillian` and `rhs` and QuTiP's
`liouvillian` agree to 2.2e-16 (tests).

Column stacking, vec(AρB) = (Bᵀ ⊗ A) vec ρ: a convention, checked against QuTiP's `sprepost`, `spre`, `spost` and
`operator_to_vector` exactly (`test_ext_open_qutip.py::test_conventions`).

## 2. Quantum jumps (`jumps`) — VERIFIED; the waiting-time form DERIVED from quoted relations

[CDM] Eq. (4): "H = HS − (iħ/2) Σm Cm† Cm"; Eq. (8): "δpm = δt ⟨φ(t)|Cm† Cm|φ(t)⟩ ≥ 0"; Eq. (10): "with a
probability δpm |φ(t + δt)⟩ = Cm|φ(t)⟩ / ‖Cm|φ(t)⟩‖"; Eq. (11): no jump "with a probability 1 − δp".

[PK] Eq. (66): "|ψA(0)(t)⟩ = e^{−i Heff t/ħ} |ψA(0)⟩"; "In fact the square of the norm of Eq. (66) is just the delay
function", Eq. (67): "P0(t) = ⟨ψA(0)(t)|ψA(0)(t)⟩"; Eq. (30): "I1(τ) ≡ −dP0/dτ" ("the delay function describing the
distribution of delay times before the next emission occurs"); the procedure with "(Dalibard et al., 1992; Dum,
Zoller and Ritsch, 1992)", Eqs. (127)-(129).

DERIVED: the waiting-time scheme (draw r; evolve with exp(−i H_eff t) until ‖ψ‖² = r; jump into channel m with
probability ‖L_m ψ‖²/Σ‖L_k ψ‖²) follows from [PK] (30), (66), (67): P(no jump up to t) = ‖ψ(t)‖². Checked: the jump
times of a pure decay equal −ln(r)/Γ for the generator's own r to round-off; trajectory averages equal the master
equation within 5 standard errors (max |z| = 2.0 over 60 comparisons, N = 4000); jump channels split by their rates
(binomial, z = 5); QuTiP's `mcsolve`, whose source draws a target norm and collapses when the norm falls to it
(`qutip/solver/mcsolve.py`, `target_norm`, `_find_collapse_time`), agrees within the derived statistical tolerances
(54 rows).

## 3. Two-level atom: conventions and Rabi oscillations (`two_level`) — VERIFIED

[S] "Defining the detuning ∆ := ω − ω0"; (5.26) "H̃A = −ħ∆|e⟩⟨e|"; (5.27) "H̃AF = (ħΩ/2)(σ + σ†)"; "σ := |g⟩⟨e| is
the atomic lowering operator"; (5.107) "⟨σx⟩ = ⟨σ⟩ + ⟨σ†⟩ = ρ̃eg + ρ̃ge", "⟨σy⟩ = i⟨σ⟩ − i⟨σ†⟩ = i(ρ̃eg − ρ̃ge)",
"⟨σz⟩ = ρee − ρgg". Equation of motion (before 5.26): "∂t c̃e = i∆c̃e − i(Ω/2)cg".

[S] (5.54) "Ω̃ := sqrt(Ω² + ∆²)"; (5.58) "cg(t) = e^{i∆t/2}[cg(0) cos(Ω̃t/2) − (i/Ω̃)[∆cg(0) + Ωce(0)] sin(Ω̃t/2)]",
"c̃e(t) = e^{i∆t/2}[c̃e(0) cos(Ω̃t/2) + (i/Ω̃)[∆c̃e(0) − Ωcg(0)] sin(Ω̃t/2)]"; (5.60) "Pe(t) = (Ω²/Ω̃²) sin²(Ω̃t/2)".
Checked against the exponential of H for several (Ω, ∆, t) and any initial state (`tests/test_open_systems.py`).

Basis (|e⟩, |g⟩) with σz = diag(1, −1): σx = σ + σ†, σy = i(σ − σ†) are then the Pauli matrices of `core.quantum.qubits`.

## 4. Optical Bloch equations with T1, T2 — VERIFIED

[S] (5.124) "γ⊥ = Γ/2 + γc", "in general γ⊥ ≥ Γ/2"; "the longitudinal relaxation time T1 = 1/Γ and transverse relaxation
time T2 = 1/γ⊥". Hence T2 ≤ 2 T1 (enforced by `two_level.rates`).
[S] (5.127) "∂t⟨σx⟩ = ∆⟨σy⟩ − γ⊥⟨σx⟩", "∂t⟨σy⟩ = −∆⟨σx⟩ − Ω⟨σz⟩ − γ⊥⟨σy⟩", "∂t⟨σz⟩ = Ω⟨σy⟩ − Γ(⟨σz⟩ + 1)";
(5.149) the matrix Q with rows "(−γ⊥, ∆, 0)", "(−∆, −γ⊥, −Ω)", "(0, Ω, −Γ)" and the constant "−(0, 0, Γ)".
[S] (5.177) "∂t ρ̃ = −(i/ħ)[H̃A + H̃AF, ρ̃] + ΓD[σ]ρ̃ + (γc/2)D[σz]ρ̃"; (5.178) "D[c]ρ := cρc† − (1/2)(c†cρ + ρc†c)": the
jump operators √Γ σ and sqrt(γc/2) σz of `collapse_operators`. Checked: the 3-component Bloch solution equals the
4 x 4 Liouvillian solution built from these operators (8 parameter sets, 3 times each).

## 5. Steady state — VERIFIED (Steck's form); the regular form DERIVED

[S] (5.132) "ρee(t → ∞) = (Ω²/(2γ⊥Γ)) / (1 + ∆²/γ⊥² + Ω²/(γ⊥Γ))"; (5.133) "ρ̃eg(t → ∞) = −(iΩ/(2γ⊥))(1 + i∆/γ⊥) /
(1 + ∆²/γ⊥² + Ω²/(γ⊥Γ))"; (5.137) for γ⊥ = Γ/2: "ρee(t → ∞) = (Ω²/Γ²) / (1 + (2∆/Γ)² + 2Ω²/Γ²)".
DERIVED: multiplying numerator and denominator by Γγ⊥², with D = Γ(γ⊥² + ∆²) + Ω²γ⊥: u = Ω∆Γ/D, v = ΩΓγ⊥/D,
w = −Γ(γ⊥² + ∆²)/D (regular at Γ → 0). Checked: equal to (5.132), (5.133), (5.137) written out (tests), to the SVD null
vector of the Liouvillian (2e-16), and to QuTiP's `steadystate` (external rows).

## 6. Torrey's transient solutions

**NOT FOUND (not fetched).** H. C. Torrey, "Transient Nutations in Nuclear Magnetic Resonance", Phys. Rev. 76,
1059-1068 (1949) (metadata from https://api.crossref.org/works/10.1103/PhysRev.76.1059; the text is behind the
publisher's paywall). Replaced by Steck's restatement, which says (footnote 16) "Here we follow H. C. Torrey,
‘‘Transient Nutations in Nuclear Magnetic Resonance,’’ Physical Review 76, 1059 (1949) ... See also L. Allen and J. H.
Eberly, Optical Resonance and Two-Level Atoms (Wiley, 1975), section 3.5, p. 62."

VERIFIED from [S]: (5.153) "f(s) = det(s − Q) = (s + γ⊥)Ω² + (s + Γ)[(s + γ⊥)² + ∆²]"; (5.158) "⟨σα(t)⟩ = Ae^{−ct} +
Be^{−at} cos bt + (C/b)e^{−at} sin bt + D"; §5.5.2.3: "Torrey identified three regimes where the solutions are
reasonably simple: (1) exact resonance (∆ = 0), (2) damping such that γ⊥ = Γ, and (3) strong excitation"; for ∆ = 0,
γ⊥ = Γ/2: (5.161) "s = −3Γ/4 ± iΩΓ", (5.162) "ΩΓ := sqrt(Ω² − (Γ/4)²)", (5.167) "⟨σx(t)⟩ = 0",
(5.171) "⟨σy(t)⟩ = (ΩΓ/(Ω² + Γ²/2)) [1 − e^{−(3Γ/4)t} (cos ΩΓt − ((Ω² − Γ²/4)/(ΓΩΓ)) sin ΩΓt)]" (the prefactor is
the product Ω·Γ, equal to the steady value (5.168) "D = (2Ω/Γ)/(1 + 2Ω²/Γ²)"),
(5.176) "⟨σz(t)⟩ = −1 + (Ω²/(Ω² + Γ²/2)) [1 − e^{−(3Γ/4)t} (cos ΩΓt + (3Γ/(4ΩΓ)) sin ΩΓt)]".

DERIVED (not quoted; the engine's `torrey_resonance` and `torrey_equal_times`):
* Resonance, any T1, T2 ≤ 2T1, any initial Bloch vector: u = u0 e^{−t/T2}; with y = (v − v_ss, w − w_ss),
  dy/dt = M y, M = [[−γ⊥, −Ω], [Ω, −Γ]], κ = (γ⊥ + Γ)/2, δ = (γ⊥ − Γ)/2, N = M + κI = [[−δ, −Ω], [Ω, δ]] with
  N² = (δ² − Ω²) I (Cayley-Hamilton), so e^{Mt} = e^{−κt}[cosh(μt) I + sinh(μt)/μ N], μ² = δ² − Ω²
  (cos/sin when Ω > |δ|, t at μ = 0). Checked: reduces to (5.171) and (5.176) for T2 = 2T1 and a ground-state start
  (2.2e-16); equals the exact 4 x 4 exponential for under-, over- and critically damped cases (2.0e-14).
* T1 = T2 = T, any detuning: Q = A − I/T with A x = p × x, p = (Ω, 0, −∆) (the precession vector of [S] (5.126)
  "℘α = Ωδαx − ∆δαz"), so x(t) = x_ss + e^{−t/T} R(p̂, |p|t)(x0 − x_ss) (Rodrigues). Checked against the exact
  exponential for three parameter sets.
* Torrey's strong-field regime is not implemented; `bloch_solution` (the exact 4 x 4 exponential of [[Q, b], [0, 0]])
  covers every case.

## 7. Fluorescence waiting times — DERIVED from [PK] (30), (66), (67)

With H_eff = H − (iΓ/2)|e⟩⟨e| and a start in |g⟩: c̈g − a ċg + (Ω²/4) cg = 0, a = i∆ − Γ/2; roots
s1,2 = a/2 ± sqrt(a² − Ω²)/2; c_e = −i(Ω/2) e^{s̄τ} sinh(ετ)/ε, c_g = e^{s̄τ}(cosh(ετ) − s̄ sinh(ετ)/ε), s̄ = a/2,
ε = sqrt(a² − Ω²)/2; P0 = |c_e|² + |c_g|², w(τ) = Γ|c_e|²; at ∆ = 0: w = ΓΩ²/(Ω² − Γ²/4) e^{−Γτ/2}
sin²(sqrt(Ω² − Γ²/4) τ/2). Checked: against ‖exp(−iH_eff τ)|g⟩‖² (expm), the integral of w against 1 − P0, the
mean waiting time against 1/(Γ ρee(∞)) (renewal: every emission resets the atom to |g⟩), and sampled jump times
(engine and QuTiP) by the DKW bound, including the exceptional point Ω = Γ/2.

## 8. Lab frame, rotating-wave approximation, Bloch-Siegert shift

DERIVED: H_lab = (ω0/2)σz + (Ω/2)(cos ωt σx + sin ωt σy) becomes −(∆/2)σz + (Ω/2)σx under R = exp(iωtσz/2)
(R σx R† = σx cos ωt − σy sin ωt; i Ṙ R† = −(ω/2)σz); it equals [S] (5.26)+(5.27) up to the constant ∆/2; R σ R† =
e^{−iωt}σ and R σz R† = σz leave the dissipators unchanged. Checked: lab-frame Schrödinger equation by DOP853 (1e-9),
the Magnus integrator against the exact rotating-frame solution (with damping), QuTiP's vern9 `mesolve` (8e-14 from
the exact solution).
VERIFIED, used only in `two_level.ABOUT["validity"]`: [S] (5.556) "∆ωc = Ω²/(4ω0)" ("This is the lowest-order
expression for the Bloch–Siegert shift"), the size of the RWA error for a linear drive. No function uses it.

## 9. Numerical methods and their error statements

* Magnus, VERIFIED: [BCOR] (1) "Y′(t) = A(t)Y(t)"; (252) "A1 = A(tn + (1/2 − √3/6)h), A2 = A(tn + (1/2 + √3/6)h)";
  (254) "Ω[4](h) = (h/2)(A1 + A2) − h²(√3/12)[A1, A2]", "Yn+1 = exp(Ω[4](h))Yn". Checked: the observed order is 4
  (error ratios 15.99, 16.00 per halving).
* Commutator-free Magnus (`evolve(method="cf4")`, review B5 S3), VERIFIED with a DERIVED reading: [BCOR] (293)
  "Ψ2[4] ≡ exp(1/2 α1 + 1/6 α2) exp(1/2 α1 − 1/6 α2)", "are in fact fourth-order (commutator-free) methods requiring
  two and three exponentials"; (295) "Ψ2[4] ≡ exp h(ϱ2,1 A1 + ϱ2,2 A2) exp h(ϱ1,1 A1 + ϱ1,2 A2)" with the
  coefficients garbled in the converted text ("̺1,1 = ̺2,2 = 21 + 723 , ̺1,2 = ̺2,1 = 21 − 723", also in plain
  `pdftotext`); (292) the time-symmetry condition. DERIVED: with α1 = (h/2)(A1 + A2) and α2 = √3 h (A2 − A1), which
  makes their (254) equal to α1 − (1/12)[α1, α2], (293) gives ϱ1,1 = ϱ2,2 = 1/4 + √3/6, ϱ1,2 = ϱ2,1 = 1/4 − √3/6
  (Baker-Campbell-Hausdorff: X + Y = α1, [X, Y]/2 = −[α1, α2]/12). Checked: observed order 4 (error ratios 15.99,
  16.00 per halving). Found here (not in the source): in the stiff regime the scheme drops to first order (each factor
  relaxes to the steady state of its frozen generator; the last acts at t_n + 5h/6): measured 63 375 steps for
  Γ = 1e4 on the review's case.
* Radau IIA (`evolve(method="radau5")`, default since review B5 S3), DERIVED: the 3-stage Radau IIA collocation method
  (Hairer & Wanner, Solving ODEs II, §IV.5 — not fetched). The coefficients in the code are fixed by their defining
  conditions, which the tests check: nodes c = ((4 − √6)/10, (4 + √6)/10, 1) are the zeros of d²/dx²[x²(x − 1)³]
  (the Radau points, to 2.1e-15); the stage matrix satisfies the collocation conditions C(3), Σj aij cj^(k−1) = ci^k/k
  (k = 1, 2, 3, to 3e-17); the weights b = third row satisfy B(5), Σi bi ci^(k−1) = 1/k (k ≤ 5, to 6e-17) and not
  B(6). Checked: observed order 5 (ratios 31.98, 31.98); stiff lab-frame drives with exact solutions (Γ = 1e4, 1e5)
  within the stated error; the review's case against scipy's Radau on the real Bloch equations (≤ 7e-11).
* Hoeffding's inequality (`jumps.Trajectories.interval`, review B5 S5), VERIFIED from a scan: W. Hoeffding,
  "Probability inequalities for sums of bounded random variables", J. Am. Stat. Assoc. 58, 13-30 (1963) (metadata
  https://api.crossref.org/works/10.1080/01621459.1963.10500830; text: a scanned copy,
  https://www.csee.umbc.edu/~lomonaco/f08/643/hwk643/Hoeffding.pdf, no text layer, read from the page images,
  p. 15): "Theorem 1. If X1, X2, ···, Xn are independent and 0 ≤ Xi ≤ 1 for i = 1, ···, n, then for 0 < t < 1 − µ
  Pr{X̄ − µ ≥ t} ≤ {(µ/(µ + t))^(µ+t) ((1 − µ)/(1 − µ − t))^(1−µ−t)}^n (2.1) ≤ e^(−nt²g(µ)) (2.2) ≤ e^(−2nt²) (2.3)";
  "If instead we assume a ≤ Xi ≤ b, the values µ and t in the three upper bounds of the theorem are to be replaced by
  (µ − a)/(b − a) and t/(b − a), respectively"; "Inequality (2.1) remains true for t = 1 − µ if the right-hand side is
  replaced by its limit as t tends to 1 − µ, which is µ^n". Reading used: the right side of (2.1) is
  exp(−n KL(µ + t ‖ µ)); applied to 1 − X it bounds the lower tail; the interval {µ : n KL(m ‖ µ) ≤ ln(2/α)} has
  coverage ≥ 1 − α. Checked: m = 0 gives the upper end 1 − (α/2)^(1/N) exactly; the review's Λ case (4 seeds × 9
  times) and a Bernoulli sample are covered.
* Matrix exponential, partly VERIFIED: [AH] abstract "The scaling and squaring method for the matrix exponential is
  based on the approximation e^A ≈ (r_m(2^{−s}A))^{2^s}, where r_m(x) is the [m/m] Padé approximant", "the backward
  error analysis that underlies the algorithm"; the SciPy docstring "Implements the algorithm given in [1], which is
  essentially a Pade approximation with a variable order that is decided based on the array data", [1] = Al-Mohy &
  Higham 2009. **NOT FOUND in the fetched text:** the size of the backward error (u‖A‖) and the rounding of the Padé
  evaluation; `open_systems.expm_error_bound` takes u‖A‖ and a budget of γ60 per entry, as the qubit comparison of
  `tests/external` does. Measured errors are <= 1e-3 of that bound (against 30-digit mpmath).
* DERIVED (standard facts, not quoted): a completely positive trace-preserving map contracts the trace norm on all
  operators (its dual is unital and positive, Russo-Dye); hence the global error of a linear Lindblad integration is at
  most the sum of the local errors; Wedin's sin-theta bound for the SVD null vector; p(n) = 10n for LAPACK backward
  errors (as quoted in the existing qubit comparison from the LAPACK Users' Guide).
* DKW, VERIFIED: [Ma] abstract "the two-sided inequality P(√n sup_x |F̂n(x) − F(x)| > λ) ≤ 2 exp(−2λ²) holds without
  any restriction on λ". Used: eps = sqrt(ln(2/α)/(2N)) at α = 1e-6.
* Five standard errors: two-sided normal tail erfc(5/√2) = 5.733e-7 (computed).

## 10. Which-path decoherence and GRW (`decoherence`, `collapse_baseline`) — VERIFIED; the double-slit factor DERIVED

[H] (5.170) "∂t ρ̃(X, X′) = −F(X − X′) ρ̃(X, X′)"; (5.171) "F(x) = ∫0^∞ dv ν(v) ngas v ∫ dΩ1dΩ2/4π
(1 − e^{imv(n1−n2)·x/ħ}) |f(mvn2, mvn1)|²"; "in the limit of large distances the localization rate saturates, at a
value given by the average collision rate F(∞) = ⟨σvngas⟩". Reading used: F(d) = Γ(1 − χ(d)) with χ the overlap of
the probe's final states (`localisation_rate`).

[B] (19) "λGRW ≃ 10^−16 sec^−1, rC ≃ 10^−7 m"; (21) "dρ(t)/dt = −(i/ħ)[H, ρ(t)] − T[ρ(t)]"; (22) "⟨x|T[ρ(t)]|y⟩ =
λGRW [1 − e^{−(x−y)²/4rC²}] ⟨x|ρ(t)|y⟩"; "the collapse rate entering the definition of the operator T[·] is NλGRW,
with N the total number of particles making up the object" ("For ordinary matter—and with a good approximation—one
can separate the center-of-mass motion from the internal motion"). Defaults of `collapse_baseline`: λ = 1e-16 1/s per
atomic mass unit, r_C = 1e-7 m (the mass-proportional convention of `collapse.py` and the v02 world).

DERIVED: Gaussian kicks q ~ N(0, 1/(2a²)) give χ(d) = ⟨e^{iqd}⟩ = e^{−d²/(4a²)}, so GRW's T term is a kick stream with
Γ = λ, a = r_C (checked on 200000 kicks of `collapse.grw_kicks`, 5 standard errors); a probe stream at rate Γ with
Kraus operators K_k = diag(⟨k|χ1⟩, ⟨k|χ2⟩) gives dρ12/dt = −Γ(1 − ⟨χ2|χ1⟩)ρ12 (checked with the Lindblad engine,
complex overlap); paths converging linearly at the screen average the kick factor to
1 − (√π a/d) erf(d/(2a)) (checked against `collapse.grw_shift_cf` at the fringe frequency k d/z, 2.3e-15, and against
Gauss-Legendre quadrature). Visibility with one probe: V = 2 sqrt(w1 w2)|⟨χ2|χ1⟩|, D = sqrt(1 − 4 w1 w2 |⟨χ2|χ1⟩|²)
(from the Born rule; checked against `core.quantum.marks.englert`).

**NOT FOUND (not fetched):** W. K. Wootters, W. H. Zurek, Phys. Rev. D 19, 473 (1979); B.-G. Englert, PRL 77, 2154
(1996); E. Joos, H. D. Zeh, Z. Phys. B 59, 223 (1985) — cited as background in `decoherence.ABOUT`; nothing is
quoted from them; the relations used are derived above and checked.

## 11. Other sources not fetched

* Dalibard, Castin, Mølmer, "Wave-function approach to dissipative processes in quantum optics", PRL 68, 580-583
  (1992) (metadata: https://api.crossref.org/works/10.1103/PhysRevLett.68.580). Replaced by [CDM] (same authors, same
  method) and [PK].
* Dum, Zoller, Ritsch, "Monte Carlo simulation of the atomic master equation for spontaneous emission", PRA 45,
  4879-4887 (1992) (metadata: https://api.crossref.org/works/10.1103/PhysRevA.45.4879). Replaced by [PK] Eqs. (30),
  (66), (67), from which the waiting-time form follows (section 2).
* Lindblad, Commun. Math. Phys. 48, 119 (1976); Gorini, Kossakowski, Sudarshan, J. Math. Phys. 17, 821 (1976); Rabi,
  Phys. Rev. 51, 652 (1937); Bloch, Phys. Rev. 70, 460 (1946); Bloch & Siegert, Phys. Rev. 57, 522 (1940); Ghirardi,
  Rimini, Weber, Phys. Rev. D 34, 470 (1986): historical references in the ABOUT passports; their content is used only
  as restated in [CDM], [M], [S] and [B] above.
