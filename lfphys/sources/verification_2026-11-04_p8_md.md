# lfphys source verification — 2026-11-04, plan item P8 (batch B7: molecular dynamics)

Purpose: every formula, number and quotation used by `core.md` (`system`, `hard`, `observables`, `cells`, `units`) and
`theories.models.interatomic`, checked against the source text. Texts fetched on 2026-11-04: arXiv PDFs (`pdftotext
-layout`) and one arXiv LaTeX source, NIST web pages (US government works), the CIAAW and OEIS pages, the authors'
supplementary data of Kolafa, Labík & Malijevský (text files only; nothing was compiled or run), Stanford lecture notes,
the Wikipedia article on the DKW inequality (for a statement whose original could not be fetched). No contact
parameter or personal identifier was sent with any request. Status codes as in `verification_2026-10-23.md`:
VERIFIED (quoted) / DIFFERS (both given) / NOT FOUND / NOT FETCHED (closed or unreachable text; what replaces it is
said). "(mine)" marks the engine author's own algebra or checks, not text from a source.

## 1. Lennard-Jones reference values — NIST Standard Reference Simulation Website

Fetched: https://mmlapps.nist.gov/srs/LJ_PURE/index.htm, …/mc.htm, …/md.htm, …/sattmmc_rc25LFS.htm,
https://www.nist.gov/mml/csd-mml/informatics/lammps-md-equation-state-pressure-vs-density-linear-force-shifted-potential.

* Cutoff: "In this work, the cutoff distance is taken to be 3σ, unless noted otherwise." (index). VERIFIED
* Tail corrections: "U_LRC = (1/2) 4πρ ∫_{r_c}^∞ dr r² V_LJ(r)", "p_LRC = −(1/2)(1/3) 4πρ² ∫_{r_c}^∞ dr r² r dV_LJ(r)/dr";
  "the above pressure correction does not account for impulsive effects at r c where the potential energy (and
  therefore the force) changes discontinuously". VERIFIED. Closed forms (mine, `LennardJones.tail`, test against
  quadrature): U/N = (8/3)πρεσ³[(1/3)(σ/r_c)⁹ − (σ/r_c)³], p = (16/3)πρ²εσ³[(2/3)(σ/r_c)⁹ − (σ/r_c)³]; in 2-D
  U/N = πρεσ²[(2/5)(σ/r_c)¹⁰ − (σ/r_c)⁴], p = πρ²εσ²[(12/5)(σ/r_c)¹⁰ − 3(σ/r_c)⁴].
* MC table (mc.htm): METHOD "NVT Monte Carlo"; N "500"; TRUNCATION "3σ + standard long range corrections";
  "Uncertainties were obtained from block averages of 5.0E7 trials and correspond to 67% confidence limits (one
  standard deviation)." "The pressure was calculated using the virial expression." Row used (grepped in context):
  "8.50E-01 7.76E-01 -5.5121E+00 4.55E-04 6.7714E-03 1.77E-03" (T*, ρ*, U*, ±, p*, ±). VERIFIED
* MD table (md.htm): METHOD "NVE molecular dynamics"; INTEGRATOR "Velocity-Verlet"; TIME STEP "0.005 t*"; N "500";
  "Both the potential and force are truncated (no splines)"; row "0.851(1) 0.776 -5.517(1) 0.030(6)". VERIFIED.
  DIFFERS from the MC row at T = 0.85: with ∂U/∂T ≈ 1.2 the MD energy should be −5.511 at T = 0.851; the table gives
  −5.517(1), five of its standard errors away (mine). This engine (five seeds, N = 500, CSVR at T = 0.851, 40 τ each)
  gives U = −5.5120 (SD 0.0023), p = −0.003 (SD 0.017): it agrees with the MC table, not with the MD table. The test
  uses the MC row (`tests/test_md_lj.py`); the difference is an open item (`../../STATUS.md`).
* LAMMPS MD table, linear-force-shifted LJ at 2.5σ: "Canonical Ensemble (fixed N, V, T) Molecular Dynamics using
  default LAMMPS "nvt" ensemble option"; "Number of LJ particles 10000"; "Truncation Linear-force Shifted at 2.5σ";
  "Time Step 0.005τ"; "uncertainty, stated by the standard error, was estimated using block analysis". Row ρ = 0.500
  (grepped in context), T = 1.50 columns: "8.608E-01 1.970E-04 -2.410E+00 6.261E-05" (p, ±, U, ±). VERIFIED. The
  formula of the linear force shift is not on the pages fetched; the engine uses u − u(r_c) − (r − r_c) u′(r_c),
  the usual meaning of the name (Allen & Tildesley §1.6; NOT FETCHED as text).
* Critical points: full LJ "T c * = 1.3120(7), ρ c * = 0.316(1), and p c * = 0.1279(6)"; LFS 2.5σ "T c *=0.937,
  ρ c *=0.320, and p c *=0.0820" (sattmmc page), "kT c /ε=0.931" (LAMMPS page). VERIFIED (both values as printed;
  quoted in the model's `conflicts`).

Not obtained: Thol et al., J. Phys. Chem. Ref. Data 45, 023101 (2016) — author preprint fetched (Paderborn), but its
test values are in the supplement ("See supplemental material at [URL], numerical test values …"), NOT FETCHED;
Thol et al., Int. J. Thermophys. 36, 25 (2015) and Heier et al., Mol. Phys. 116, 2083 (2018) (LJTS 2.5σ) — paywalled
(HTTP 403 / paywall page), NOT FETCHED; Johnson, Zollweg & Gubbins (1993) — NOT FETCHED (no open copy found).

## 2. Hard spheres and hard disks

**Clisby & McCoy**, "Ninth and tenth order virial coefficients for hard spheres in D dimensions", J. Stat. Phys. 122,
15 (2006), arXiv:cond-mat/0503525 (PDF). Eq. (2) "P/(kB T) = Σ_{k=1}^∞ Bk ρ^k with B1 ≡ 1"; Table 3: B2 = "πσ²/2"
(D = 2), "2πσ³/3" (D = 3). Table 1 (B_k/B_2^{k−1}, k = 3…10), grepped lines:

    2   0.782004 · · ·    0.53223180 · · ·      0.33355604(1)     0.1988425(42)    0.1148728(43)     0.0649930(34)   0.0362193(35)    0.0199537(80)
    3   0.625             0.2869495 · · ·       0.110252(1)∗      0.03888198(91)   0.01302354(91)    0.0041832(11)   0.0013094(13)    0.0004035(15)

VERIFIED. "outside of B2 and B3 which are elementary to compute and the original computation of B4 in D = 3 by
Boltzmann and van Laar, the only other analytic computations … are of B4 in D = 2 done … by Rowlinson and Hemmer in
1964". VERIFIED. Use (mine): Z = 1 + Σ (B_k/B_2^{k−1}) (2^{D−1} η)^{k−1}.

**Kolafa & Rottner**, "Simulation-based equation of state of the hard disk fluid and prediction of higher-order
virial coefficients", Mol. Phys. 104, 3435 (2006), arXiv:cond-mat/0608356v1 (LaTeX source; the PDF endpoint returned
HTTP 500).
* "ρ=Nσ²/A"; Table 1 "Molecular dynamics results on the compressibility factor, corrected for the finite size
  effects"; line 153: "0.40 &  2.1514393 & 0.0000052". VERIFIED
* Eq. (Zenscorr): "Z_{μVT} − Z_{NVT} = (ρ/2N) ∂²p/∂ρ² [∂p/∂ρ]^{−1} + O(N^{−2})". VERIFIED
* Eq. (Zvir): "Z_vir(t1,t2) = 1 − ((N−1)/N) (1/(2 E_kin (t2−t1))) Σ_{t∈(t1,t2)} Δv_ij · r_ij"; "the first step
  [MD-NVE → NVT] is already included in formulas (Zvir) and (Zrate)". VERIFIED. The engine's estimator (mine, from
  the virial theorem with impulsive forces): Z = 1 + Σ r_ij·Δp_i / (d N T Δt) with T = 2⟨K⟩/(dN − d), i.e. the same
  (N−1)/N structure (unit masses: Σ r_ij·Δp_i (N−1)/(2 N E Δt)); its sign and factor checked at low density against
  the virial series (`tests/test_md_hard.py`).
* EOS for ρ_max = 0.88 (x = y/(1−y)): "Z = 1+2x+1.12801775x²+0.00181895291x³−0.0526134737x⁴+0.0504951668x⁵
  −0.0325433846x⁶+0.0133946531x⁷+0.00174265604x⁸−0.00944632202x⁹+0.00851111768x¹⁰−0.0035963525x¹¹
  +0.000577345106x¹²−1.06399127·10⁻⁷x¹⁹". VERIFIED; reproduces Table 1 at ρ = 0.40 within 2·10⁻⁵ (test).

**Kolafa, Labík & Malijevský**, PCCP 6, 2335 (2004): the paper is RSC-only (author reprint on request), NOT FETCHED.
The authors' supplementary data (https://old.vscht.cz/fch/software/hsmd/hsmd.zip, text files only):
* readme.txt: "Ensemble correction enscorr/N (see `hseos') should be added to get accurate results." VERIFIED
* zfinal.res, header "# rho   Z(corr.)    stdev       y", line 9: "0.50 3.2693735 0.0000236 0.26179939". VERIFIED
* hseos.c, `zB6_11348` (x = eta/(1−eta)): "1+4*x+6*powi(x,2)+2.36476838*powi(x,3)-0.869855149*powi(x,4)
  +1.1062803*powi(x,5)-1.09504933*powi(x,6)+0.637614043*powi(x,7)-0.227939731*powi(x,10)+0.109894767*powi(x,14)
  -0.00906797261*powi(x,22)". VERIFIED (as code text; equality with the printed paper not checked); reproduces
  zfinal.res at ρ = 0.5 within 4·10⁻⁵ (test). Used for the derivatives of the ensemble correction only.

**Carnahan–Starling**: "Z_CS = (1 + η + η² − η³)/(1 − η)³", η ≡ (π/6)ρσ³ — Robles, López de Haro & Santos, J. Chem.
Phys. 140, 136101 (2014), arXiv:1401.2358v2, Eq. (1). VERIFIED (cited in the test as 0.2 % low at η = 0.262; not
used as a reference). Henderson (disks): "Zs = (1 + η²/8)/(1 − η)²" — López de Haro, Yuste & Santos,
arXiv:0704.0157v1, Table 1. VERIFIED (not used).

## 3. Thermostats

**Bussi, Donadio & Parrinello**, "Canonical sampling through velocity rescaling", J. Chem. Phys. 126, 014101 (2007),
arXiv:0803.4060.
* "K̄ = N_f/(2β), where N_f is the number of degrees of freedom and β is the inverse temperature". VERIFIED
* Eq. (7): "dK = (K̄ − K) dt/τ + 2 √(K K̄/N_f) dW/√τ". VERIFIED
* Eq. (A7): "α² = e^{−Δt/τ} + (K̄/(N_f K))(1 − e^{−Δt/τ})(R_1² + Σ_{i=2}^{N_f} R_i²) + 2e^{−Δt/2τ}
  √((K̄/(N_f K))(1 − e^{−Δt/τ})) R_1". VERIFIED. The engine draws Σ_{i=2}^{N_f} R_i² as χ²(N_f − 1)
  (`Generator.chisquare`): the paper's sentence "can be drawn directly from the Gamma distribution p_{N_f−1}(x) =
  x^{(N_f−1)/2−1} e^{−x}/Γ((N_f−1)/2)" omits the factor 2 between χ² and that Gamma law (mine; a sum of k squared
  unit Gaussians is 2·Gamma(k/2, 1)). Rescaling step "does not change H̃" (Eq. 15) — so the heat counter of a bath
  (ΔK of its steps) closes the effective-energy balance. VERIFIED
* Applied in the engine as two half steps O(Δt/2) at the ends of the step (mine; two exact half updates compose to the
  exact update in distribution).

**Leimkuhler & Matthews**, "Rational construction of stochastic numerical methods for molecular sampling", Appl.
Math. Res. Express 2013, arXiv:1203.5428v2. Appendix: "c1 = e^{−γδt}, … c3 = √(kB T (1 − c1²))"; 'BAOAB': "p_{n+1/2}
= p_n − δt ∇U(x_n)/2; x_{n+1/2} = x_n + δt M^{−1} p_{n+1/2}/2; p̂_{n+1/2} = c1 p_{n+1/2} + c3 M^{1/2} R_{n+1};
x_{n+1} = x_{n+1/2} + δt M^{−1} p̂_{n+1/2}/2; p_{n+1} = p̂_{n+1/2} − δt ∇U(x_{n+1})/2". "For small δt the method is
always eventually second order." VERIFIED. Free-particle diffusion of the scheme (mine, used in the test):
D_BAOAB = (kT h/2m) coth(γh/2) = D (1 + (γh)²/12 + …).

**Velocity Verlet**: Swope, Andersen, Berens & Wilson, J. Chem. Phys. 76, 637 (1982) — NOT FETCHED (closed); the
scheme as in Leimkuhler & Matthews' B, A steps above with γ = 0. Its exact discrete frequency for a linear
oscillator, cos(ω_h h) = 1 − ω²h²/2, and the recursion x_{n+1} + x_{n−1} = (2 − ω²h²) x_n are elementary (mine;
`tests/test_md_bonds.py`).

## 4. The DKW inequality

Massart, "The tight constant in the Dvoretzky–Kiefer–Wolfowitz inequality", Ann. Probab. 18, 1269 (1990): NOT FETCHED
(Project Euclid returned a bot-protection page). Replaced by the Wikipedia article "Dvoretzky–Kiefer–Wolfowitz
inequality" (raw wikitext, https://en.wikipedia.org/w/index.php?title=…&action=raw), which cites it: "In 1990,
Pascal Massart proved the inequality with the sharp constant C = 2"; "ℙ(sup_x |F_n(x) − F(x)| > ε) ≤ 2e^{−2nε²} for
every ε>0"; band "ε = √(ln(2/α)/(2n))". VERIFIED (secondary source; `core.md.observables.dkw_bound`).

## 5. Argon and units

* CIAAW, https://www.ciaaw.org/argon.htm: "A r (Ar) = [39.792, 39.963] since 2017"; "In 1979, the Commission …
  recommended A r (Ar) = 39.948(1)." Abridged table 2024: "18 Ar argon 39.95 ± 0.16". VERIFIED. The engine uses
  39.948 u, the value used with the LJ parameters below (a stated choice).
* σ = 3.405 Å, ε/k_B = 119.8 K: Parejo & Santos, arXiv:2511.14399v2, Table 1: "Ar 6.634 × 10−26 119.8 3.405 × 10−10",
  attributed to "Hirschfelder, J.O.; Curtiss, C.F.; Bird, R.B. Molecular Theory of Gases and Liquids; Wiley: New
  York, NY, USA, 1964". VERIFIED (secondary). Tseng & Caticha, arXiv:cond-mat/0212198v4, Eq. (84): "The generally
  accepted values of the LJ parameters are those given in [15] by fitting B(T) at T = 273 K, ε1 = 0.01034 eV and σ1 =
  3.405 Å" ([15] Michels et al., Physica 15, 627 (1949)). VERIFIED; DIFFERS slightly: 0.01034 eV/k_B = 120.0 K
  (mine). Hirschfelder, Curtiss & Bird, Michels 1949, Rahman 1964: NOT FETCHED.
* Unit conversions: CODATA through `scipy.constants` (k, atomic mass constant, e, ε0, N_A); τ = σ√(m/ε) = 2.156 ps for
  argon (test).

## 6. Coulomb sums (not implemented: refusal in periodic boxes)

Lee & Cai, "Ewald Summation for Coulomb Interactions in a Periodic Supercell", Stanford lecture notes (2009), Eqs.
(27), (28), (38), (39) and "The contribution to the k = 0 term is zero if the supercell is charge neutral" — VERIFIED;
OEIS A085469 (NaCl Madelung constant 1.7475645946331821906…) and A181152 (CsCl 1.76267477307098839…) — VERIFIED.
Kept for the Ewald summation the engine does not have yet (`../../STATUS.md`): its tests would be these constants.

## 7. Derived here (no external source needed; tested)

* LJ walls (`LJWall`): the 12-6 potential integrated over a half-space of wall atoms of density ρ_w: d = 3:
  (2π/3)ρ_w ε σ³ [(2/15)(σ/z)⁹ − (σ/z)³]; d = 2: (3π/8)ρ_w ε σ² [(21/80)(σ/z)¹⁰ − (σ/z)⁴] (derivation in the module).
  Steele, Surf. Sci. 36, 317 (1973), the usual citation of the 9-3 form — NOT FETCHED.
* Thermal (diffuse) wall: emitted normal speed density ∝ v exp(−mv²/2kT) (flux-weighted), mean emitted kinetic energy
  (d+1)kT/2; heat rate between walls T1, T2 for a Knudsen gas N(d+1)k(T2 − T1)/(2L√(πm/2k)(T1^{−1/2} + T2^{−1/2}))
  (renewal-reward; `tests/test_md_thermo.py`).
* Harmonic angle with a fixed vertex: ω² = 2k/(m r0²); in cos θ: k sin²θ0 in place of k.
* Ornstein–Uhlenbeck MSD: 2dD[t − (1 − e^{−γt})/γ], D = kT/(mγ).

## 8. Phase diagrams of the cut models, argon's quantum limit (review B7-md processing, fetched 2026-11-04)

Fetched for the processing of review `reviews/archive/2026-11-04_internal_B7-md` (M2, M3, M16) by a helper of the processing
session: NIST pages, arXiv PDFs and LaTeX sources, an open repository copy of Smit & Frenkel 1991 (OCR of a scan), the
NIST Chemistry WebBook; generic user agent, no contact parameter or personal identifier sent. Quotations grepped.

* NIST SRS, https://mmlapps.nist.gov/srs/LJ_PURE/sattmmc_rc25LFS.htm: "For the Lennard-Jones fluid, linear force
  shifted at 2.5σ, the critical properties are Tc*=0.937, ρc*=0.320, and pc*=0.0820 [7]" ([7] Errington,
  Debenedetti & Torquato, J. Chem. Phys. 118, 2256 (2003)); "V/σ³: 512"; "TRUNCATION: Linear Force Shifted at 2.5σ";
  row T* = 0.75: "3.18771E-02 4.34360E-06 6.93338E-01 8.77657E-05" (ρ_vap, ±, ρ_liq, ±; 95 % limits from 5 runs).
  VERIFIED. Used by the playground's liquid–vapour preset (p03, 3-D at 90 K = 0.751 ε/k) and its test.
* Errington, Debenedetti & Torquato, arXiv:cond-mat/0208389 (the same work), "u_sf(r) = u(r) − u(rc) − (r − rc)
  u′(rc) for r ≤ rc … (rc = 2.5 in this work)" — the engine's linear force shift; Table 1 "Critical and triple point
  parameters of the shifted-force Lennard-Jones potential": "Tc 0.937 1.3120", "Ttr 0.560 0.687", "ρtr,liq 0.815
  0.850" (columns sfLJ, LJ). VERIFIED: 0.75 lies between the force-shifted model's triple point and critical point.
* NIST SRS index: "T c * = 1.3120(7), ρ c * = 0.316(1), and p c * = 0.1279(6)" (full LJ). VERIFIED.
* Smit & Frenkel, J. Chem. Phys. 94, 5663 (1991), open copy pure.uva.nl (OCR of a scan; σ printed as "0", ± as "-t",
  "&"): R_c "= 2.50"; full potential "T, = 0.515 -t 0.002"; truncated and shifted "critical point is T, = 0.459 &
  0.001". VERIFIED (as OCR text). The same numbers restated in arXiv:2110.01986: "$T_c = 0.515 \pm 0.002$ … for the
  full potential; and $T_c = 0.459 \pm 0.001$ … for the truncated and shifted potential at $2.5\sigma$". VERIFIED.
  Shevchenko & Kulinskii, arXiv:2606.08178v3, Table II (the review's source): "Jiang&Gubbins, N=8000 … 0.498 ± 0.002",
  "Smit&Frenkel, N=512 … 0.515 ± 0.002" — no cutoff stated in the table. VERIFIED. No source found for the 2-D
  force-shifted model's critical point (NOT FOUND).
* Li & Pica Ciamarra, arXiv:2010.03876 (Phys. Rev. E 102, 062101; 2-D LJ, "$r_c = 2.5\sigma$, $C$ is a constant
  chosen such that $U(r_c)=0$"): "this result indicates that $T=0.42$ is below the triple point"; "The temperature of
  the critical point is, therefore, in the range $T=[0.42:0.45]$" (the same paper prints "$T\simeq0.496$" elsewhere:
  DIFFERS within itself); "At high temperature, $T = 1.0$, isolated dislocations start growing on decreasing the
  density at $\rho=0.90$, which corresponds to the solid-hexatic transition density"; "… hexatic-fluid coexistence
  region, at $\rho= 0.896$". VERIFIED. Used by the melting preset (ρσ² = 0.85 at 120 K = 1.00 ε/k: fluid).
* Argon, Θ_D: arXiv:1304.2049 "For solid argon, which forms FCC structure below the melting temperature of 84 K, the
  Debye temperature is $\Theta_D$=85 K."; Herrero & Ramírez, arXiv:cond-mat/0606142: "… thermodynamic properties of
  solids at temperatures lower than the Debye temperature $\Theta_D$, where the quantum nature of the atomic nuclei is
  relevant", "($\Theta_D \sim 90$ K for Ar …)". VERIFIED. The Debye heat capacity C_v/(3Nk) at 20 / 40 / 80 K with
  Θ_D = 85 K: 0.47 / 0.81 / 0.95 (mine, `p03_molecules.viz.debye_cv_fraction`).
* NIST Chemistry WebBook, argon, phase change data: "T c 150.86 K" (Angus, Armstrong et al. 1972; Gosman, McCarty
  et al. 1969), "T c 150.65 K" (McCain & Ziegler 1967); "T triple 83.8 K". VERIFIED; the engine's texts say
  150.7–150.9 K.
* Not obtained (paywalled or not found): Ahmed & Sadus 2009/2010, Mastny & de Pablo 2007 (abstract only: "reduced
  triple point temperatureTtr=0.694"), van Meel et al. 2008, Vrabec et al. 2006, Jiang & Gubbins 1995, Barker,
  Henderson & Abraham 1981 — NOT FETCHED.

Hard spheres at ρ = 0.5, N = 500 (`tests/test_md_hard.py`, review B7-md M15): twelve independent runs of the test's
estimator give Z = 3.2649 ± 0.0032 against KLM's corrected 3.2673 (−0.08 %, −0.8 SE). [error in earlier: the "+0.39 %
finite-size effect" recorded in the test and in STATUS V41 (g) is not reproduced]
