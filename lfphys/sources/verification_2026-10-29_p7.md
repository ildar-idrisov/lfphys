# lfphys source verification — plan item P7, two-body part (2026-10-29)

Purpose: every formula and number used by `core.gravity.pn_binary`, `core.gravity.gw_quadrupole`,
`theories.approx.peters_mathews` and the PSR B1913+16 constants appended to `core.data`, quoted from source texts
fetched on 2026-10-29 (arXiv PDFs, converted with `pdftotext -layout`; the quotes below are that text, equations in
the converted text are partly garbled, so each is given as quoted fragments plus the reading used, and each reading
is cross-checked against a second source or by a test).
Status codes as in `verification_2026-10-23.md`: VERIFIED / NOT FOUND / DIFFERS.

Sources:

* [WH16] J. M. Weisberg, Y. Huang, "Relativistic Measurements from Timing the Binary Pulsar PSR B1913+16", ApJ 829, 55
  (2016); text arXiv:1606.02744v1 ("Accepted by APJ 2016 Jun 1"). Note: arXiv:1603.02716 is a different paper
  ("General purpose multiplexing device for cryogenic microwave systems", Appl. Phys. Lett. 108, 222602), checked
  through the arXiv API on 2026-10-29.
* [B14] L. Blanchet, "Gravitational Radiation from Post-Newtonian Sources and Inspiralling Compact Binaries", Living
  Rev. Relativ. 17, 2 (2014); text arXiv:1310.1528v3.
* [B24] L. Blanchet, "Post-Newtonian Theory for Gravitational Waves", Living Rev. Relativ. 27, 4 (2024); text
  arXiv:1310.1528v6 (updated 2024-07-12). Used to confirm that the equations of motion did not change between
  editions.
* [K95] L. E. Kidder, "Coalescing binary systems of compact objects to (post)^{5/2}-Newtonian order. V. Spin effects",
  Phys. Rev. D 52, 821 (1995); text arXiv:gr-qc/9506022v1.

---

## 1. PSR B1913+16 (WH16) — VERIFIED

Table 2 "Orbital Parameters" ("Figures in parentheses represent formal TEMPO standard errors in the last quoted
digit"):

    x ≡ a1 sin i (s). . .               2.341776(2)
    e ...............                   0.6171340(4)
    Pb (d) . . . . . . . . . . .        0.322997448918(3)
    hω̇i (deg / yr) . . .               4.226585(4)
    γ (ms) . . . . . . . . . .          0.004307(4)
    Ṗbobs . . . . . . . . . . . .      −2.423(1) ×10−12

**DIFFERS (unit label).** γ is printed under "(ms)" but only γ = 0.004307 **s** gives the paper's own masses through
its Eq. (17): with 0.004307 s the engine obtains m1 = 1.43786, m2 = 1.39050 Msun (paper: 1.438 ± 0.001, 1.390 ±
0.001); with 0.004307 ms, m2 = 0.0021 Msun. The constant is stored in seconds with this note.

Sec. 3.1: "T = G M /c3 = 4.925 490 947 µs." (T_sun). The engine's IAU 2015 nominal G M_sun / c^3 differs by 1.3e-10.

Sec. 4.1: "we find that Ṗbgal = −(0.025 ± 0.004) × 10−12 . Inserting also Ṗbobs from Table 2 into Eq. 15, we calculate
that Ṗbintr = −(2.398 ± 0.004) × 10−12 ." Eq. (15): "Ṗbintr = Ṗbobs − Ṗbgal".

Sec. 4.3: "our measurements of hω̇i and γ, along with the Keplerian elements, leave only the two unknowns m1;hω̇i,γ and
m2;hω̇i,γ in the following two general relativistic equations:" Eq. (16):
"hω̇i = 3 G2/3 c−2 (Pb /2π)−5/3 (1 − e2 )−1 (m1;hω̇i,γ + m2;hω̇i,γ )2/3", Eq. (17):
"γ = G2/3 c−2 e (Pb /2π)1/3 m2;hω̇i,γ (m1;hω̇i,γ + 2m2;hω̇i,γ )× (m1;hω̇i,γ + m2;hω̇i,γ )−4/3";
"Solving simultaneously for the two component masses, we find that m1;hω̇i,γ = 1.438 ± 0.001 M and m2;hω̇i,γ =
1.390 ± 0.001 M"; "(sin i)hω̇i,γ = 0.7327 ± 0.0004".

Sec. 5.1, Eq. (22): "ṖbGR = − 192 π G5/3 / (5 c5) (Pb/2π)−5/3 (1 + 73/24 e2 + 37/96 e4) (1 − e2)−7/2 × m1 m2
(m1 + m2)−1/3" (reading of the garbled layout; identical to B14 Eq. (11) below); "Inserting our measured and derived
values and their uncertainties into Eq. 22 , we find that ṖbGR = (−2.40263 ± 0.00005) × 10−12"; Eq. (23):
"Ṗbintr / ṖbGR = (−2.398 ± 0.004) × 10−12 / (−2.40263 ± 0.00005) × 10−12 = 0.9983±0.0016."

Not printed: the year of ⟨ω̇⟩ in deg/yr. With the Julian year (365.25 d, TEMPO's unit) the engine reproduces
ṖbGR = −2.4026302·10⁻¹² (9e-8 relative to the printed −2.40263); with the tropical year −2.40276·10⁻¹², 2.5 times the
printed uncertainty away. Taken: Julian (`core.data.PULSAR_YEAR_DAYS`).

## 2. Equations of motion in the centre-of-mass frame, harmonic gauge — VERIFIED (two editions and a second paper)

B14 Sec. 7.3, Eq. (219): "dv/dt = − Gm/r2 [ (1 + A) n + B v ] + O(1/c8)", with Eq. (220a) (A) and (220b) (B). The
terms used (fragments as converted; m = total mass, ν = m1 m2/m², ṙ = n·v):

    A = 1/c2 { −3ṙ2ν/2 + v2 + 3νv2 − Gm/r (4 + 2ν) }
      + 1/c4 { 15ṙ4ν/8 − 45ṙ4ν2/8 − 9ṙ2νv2/2 + 6ṙ2ν2v2 + 3νv4 − 4ν2v4
               + Gm/r ( −2ṙ2 − 25ṙ2ν − 2ṙ2ν2 − 13νv2/2 + 2ν2v2 ) + G2m2/r2 ( 9 + 87ν/4 ) }
      + 1/c5 { −24ṙνv2/5 Gm/r − 136ṙν/15 G2m2/r2 }
      + 1/c7 { Gm/r ṙ ( 366/35 νv4 + 12ν2v4 − 114v2νṙ2 − 12ν2v2ṙ2 + 112νṙ4 )
               + G2m2/r2 ṙ ( 692/35 νv2 − 724/15 ν2v2 + 294/5 νṙ2 + 376/5 ν2ṙ2 ) + G3m3/r3 ṙ ( 3956/35 ν + 184/5 ν2 ) }
    B = 1/c2 { −4ṙ + 2ṙν }
      + 1/c4 { 9ṙ3ν/2 + 3ṙ3ν2 − 15ṙνv2/2 − 2ṙν2v2 + Gm/r ( 2ṙ + 41ṙν/2 + 4ṙν2 ) }
      + 1/c5 { 8νv2/5 Gm/r + 24ν/5 G2m2/r2 }
      + 1/c7 { Gm/r ( −626/35 νv4 − 12/5 ν2v4 + 678/5 νv2ṙ2 + 12/5 ν2v2ṙ2 − 120νṙ4 )
               + G2m2/r2 ( 164/21 νv2 + 148/5 ν2v2 − 82/3 νṙ2 − 848/15 ν2ṙ2 ) + G3m3/r3 ( −1060/21 ν − 104/5 ν2 ) }

The 3PN terms (with ln(r/r0'')) are not used. B24 Eqs. (357)-(359) give the same coefficients grouped differently:
"A2.5PN = 8G m ν/(5r) ṙ (−17 Gm/(3r) − 3v2)", "B2.5PN = 8G m ν/(5r) (3 Gm/r + v2)", A3.5PN and B3.5PN (358e), (359e)
expanded term by term equal the 1/c7 lines above (checked by hand, 2026-10-29).

K95 Eq. (2.2b, d) (1PN, 2PN, η = ν), e.g. "aP N = − m/r2 { n̂ [ (1 + 3η)v2 − 2(2 + η) m/r − 3/2 η ṙ2 ] − 2(2 − η)ṙv }";
the engine's 1PN + 2PN acceleration equals K95's to 2e-16 of m/r² (`tests/test_pn_binary.py`). K95 Eq. (2.2f)
"aRR = 8/5 η m2/r3 { ṙn̂ [ 18v2 + 2m/(3r) − 25ṙ2 ] − v [ 6v2 − 2 m/r − 15ṙ2 ] }" is in another gauge than B14's
harmonic 2.5PN term (in the Iyer–Will family: K95 α = 4, β = 5; B14 α = −1, β = 0, derived here by matching the
coefficients); both give the same orbit averages (test).

## 3. Conserved energy and angular momentum to 2PN (K95) — VERIFIED

K95 Eq. (2.7a, b, d) (spin terms dropped): "EN = µ (1/2 v2 − m/r)", "EP N = µ { 3/8 (1 − 3η)v4 + 1/2 (3 + η)v2 m/r +
1/2 η m/r ṙ2 + 1/2 (m/r)2 }", "E2P N = µ { 5/16 (1 − 7η + 13η2 )v6 − 3/8 η(1 − 3η) m/r ṙ4 + 1/8 (21 − 23η − 27η2 ) m/r
v4 + 1/8 (14 − 55η + 4η2 ) (m/r)2 v2 + 1/4 η(1 − 15η) m/r v2 ṙ2 − 1/4 (2 + 15η) (m/r)3 + 1/8 (4 + 69η + 12η2 ) (m/r)2
ṙ2 }"; Eq. (2.9b, d): "LP N = LN { 1/2 v2 (1 − 3η) + (3 + η) m/r }", "L2P N = LN { 3/8 (1 − 7η + 13η2 )v4 − 1/2 η(2 +
5η) m/r ṙ2 + 1/2 (7 − 10η − 9η2 ) m/r v2 + 1/4 (14 − 41η + 4η2 ) (m/r)2 }"; "to (post)2-Newtonian order, Ė = J̇ = 0".
Checked: the residual of dE/dt, dJ/dt along the engine's EOM falls as c⁻⁴ (1PN) and c⁻⁶ (2PN); the circular limit
equals B14 Eqs. (229), (232).

## 4. Gauge-invariant references (B14) — VERIFIED

* Eq. (228) "Ω2 = Gm/r3 { 1 + (−3 + ν)γ + (6 + 41/4 ν + ν2) γ2 + ... }", γ = Gm/(rc2) (harmonic r).
* Eq. (232) "E = −µc2x/2 { 1 + (−3/4 − 1/12 ν) x + (−27/8 + 19/8 ν − 1/24 ν2) x2 + ... }", x = (GmΩ/c3)^(2/3).
* Eq. (345) "ε ≡ −2E/(µc2)", "j ≡ −2E h2/µ3" with h = J/(Gm).
* Eq. (346e) "et = sqrt(1−j) + ε/(8 sqrt(1−j)) [ −8 + 8ν + j(17 − 7ν) ]" (1PN; consistent with Eq. (351)).
* Eq. (348a) "n = ε3/2 c3/(Gm) { 1 + ε/8 (−15 + ν) + ε2/128 [ 555 + 30ν + 11ν2 + 192/j1/2 (−5 + 2ν) ] + ... }";
  Eq. (348b) "K = 1 + 3ε/j + ε2/4 [ 3/j (−5 + 2ν) + 15/j2 (7 − 2ν) ] + ..."; "the functional forms of the mean motion n
  and periastron advance K in terms of the gauge invariant variables ε and j are identical in different coordinate
  systems". Check: their circular limit reproduces Eq. (353) "Kcirc = 1 + 3x + (27/2 − 7ν) x2 + ..." (by hand).
* Eq. (350) "x/ε = 1 + ε (−5/4 + 1/12 ν + 2/j) + ε2 ( 5/2 + 5/24 ν + 1/18 ν2 + 1/j1/2 (−5 + 2ν) + 1/j ( −5 + 7/6 ν +
  1/j (33/2 − 5ν) ) ) + ..." (2PN part read from the converted layout "5/2 + 5/24 ν + 1/18 ν2 + 1/j^1/2 (−5 + 2ν) + 1/j
  (−5 + 7/6 ν + 1/j (33/2 − 5ν))"; added 2026-10-29 for review B5, N6). Check: with Eq. (349) Ω = K n, the reading
  satisfies (K n)^(2/3) = x up to O(ε³) (residual/ε³ → −197.4, −44.0 at j = 0.5, 0.9, ν = 1/4, in 50-digit arithmetic;
  a test checks the slope 3).
* Eq. (231) "γ = x { 1 + (1 − ν/3) x + (1 − 65/12 ν) x2 + ... }" (γ = Gm/(rc²), harmonic r); with Eq. (232) and the
  e = 0 value of Eq. (359b) it gives the 1PN coefficient of Eq. (227a) exactly: (−1247/336 − 35ν/12) − 2(−3/4 − ν/12)
  − 3(1 − ν/3) = −1751/336 − 7ν/4 (test, exact fractions; review B5, S2).
* Eq. (226) "a = −Ω2 x − 32/5 G3m3ν/(c5r4) [ 1 + γ (−743/336 − 11/4 ν) ] v"; Eq. (227a) "ṙ = −64/5 G3m3ν/(r3c5) [ 1 + γ
  (−1751/336 − 7/4 ν) ]". The circular reduction of the 1/c7 terms above reproduces Eq. (226) (by hand: the 1/c7 part
  of B at ṙ = 0, −(6358/105) ν + (32/5) ν², plus the 2.5PN term with Ω²(r), plus B_1PN with the radiative ṙ, gives
  (32/5) ν (−743/336 − 11ν/4); also a test).

## 5. Quadrupole formula and Peters–Mathews (B14) — VERIFIED

* Eq. (2) "hTT ij = 2G/(c4R) Pijab(N) d2Qab/dT2 (T − R/c) + ...", "Pijab = Pia Pjb − 1/2 Pij Pab", "Pij = δij − Ni Nj";
  Eq. (3) "Qij (t) = ∫ d3x ρ (xi xj − 1/3 δij x2)"; Eq. (4) "F ≡ dE/dT = G/c5 { 1/5 d3Qab/dT3 d3Qab/dT3 }"; Eq. (5)
  "Gi ≡ dJi/dT = G/c5 { 2/5 εiab d2Qac/dT2 d3Qbc/dT3 }".
* Eq. (69) "h+ = 1/2 (Pi Pj − Qi Qj) HTT ij", "h× = 1/2 (Pi Qj + Pj Qi) HTT ij"; Sec. 9.4: "P and Q lie along the major
  and minor axis ... P is oriented toward the orbit's ascending node"; Eq. (320) "h+,× = 2Gµx/(c2R) Σ x^(p/2) H+,×p/2";
  Eq. (322a) "H+0 = −(1 + c2i) cos 2ψ − 1/96 s2i (17 + c2i)" (the second term is the non-linear memory, absent from the
  quadrupole formula); Eq. (323a) "H×0 = −2ci sin 2ψ".
* Eq. (8a), (9a): "dE/dt = ∫ d3x vi Fireac = −F + df/dt", "<dE/dt> = −<F>".
* Eq. (10a) "E = − Gm1m2/(2a)", (10b) "J = m1m2 sqrt(Ga(1 − e2)/(m1 + m2))".
* Eq. (11) "<dP/dt> = − 192π/(5c5) (2πG/P)5/3 m1m2/(m1 + m2)1/3 (1 + 73/24 e2 + 37/96 e4)/(1 − e2)7/2"; "Numerically,
  one finds <dP/dt> = −2.4 × 10−12".
* Eq. (12) "<de/dt> = − 608π e/(15c5P) (2πG/P)5/3 m1m2/(m1 + m2)1/3 (1 + 121/304 e2)/(1 − e2)5/2".
* Eq. (13): the converted layout reads "e2 / (1 − e2 )19/6 [ 1 + 121/304 e2 ]145/121 = c0 P 19/9" ("This yields the
  evolution of the eccentricity"; "When e ≪ 1 the latter relation gives approximately e2 ' c0 P 19/9"). Read as
  e² (1 + 121e²/304)^(145/121) / (1 − e²)^(19/6) = c0 P^(19/9), which raised to 6/19 with P ∝ a^(3/2) is Peters'
  a(e) ∝ e^(12/19) (1 + 121e²/304)^(870/2299) / (1 − e²) (145/121 · 6/19 = 870/2299). Checked by integrating
  Eqs. (11)-(12): the relation is constant to 1e-9 along the track (test).
* Eqs. (358), (359a, b): "<Finst> = 32c5/(5G) ν2 x5 { I0 + x I1 + ... }", "I0 = 1/(1 − e2t)7/2 (1 + 73/24 e2t + 37/96
  e4t)", "I1 = 1/(1 − e2t)9/2 { −1247/336 − 35/12 ν + e2t (10475/672 − 1081/36 ν) + e4t (10043/384 − 311/12 ν) + e6t
  (2179/1792 − 851/576 ν) }"; "The Newtonian coefficient I0 is nothing but the Peters & Mathews enhancement function".

Peters' a-forms of da/dt, de/dt, dE/dt, dJ/dt (Peters 1964) are not quoted from Peters' paper (not open access); they
are derived from Eqs. (10)-(12) with Kepler's law (`theories.approx.peters_mathews` docstring) and checked against
quadrature of Eqs. (4), (5) over Kepler ellipses (agreement 1e-14) and against an Arb enclosure of the integral for
e = 0.617134.
