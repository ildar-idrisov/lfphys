# Review B8 — optical vortices (plan P14.7): `core.optics.beams*`, `theories.approx.beams_paraxial`, `v16_optical_vortices`

**Status: awaiting processing.** Internal review (Claude Opus subagent), delivered 2026-11-04. The reviewer did not
write the code under review and does not process this review (`reviews/README.md`).

**Scope.** `lfphys/lfphys/core/optics/beams.py`, `beams_rotation.py`, `beams_generation.py`,
`lfphys/lfphys/theories/approx/beams_paraxial.py`, `lfphys/tests/test_beams.py`, `test_beams_paraxial.py`,
`lfphys/sources/verification_2026-11-04_p14_7_beams.md`, `visualizations/v16_optical_vortices/` (viz.py,
engine/apparatus.py, web/view.js, README.md, tests/), against `AGENTS.md`, `lfphys/LAYERS.md`, `visualizations/RULES.md`.
Not reviewed: FDTD, Mie/v17, charges, slit/v02 (other reviewers).

**Environment.** Every script runs in the project image `light-funnel-viz` (Python 3.11.17, NumPy 2.4.6, SciPy 1.17.1;
`out/s00_env.txt`), CPU only, `engine/` mounted read-only, this folder at `/out`: `./run.sh <name> scripts/<script>`
(containers `lf-b8rb-*`, stopped by name, checked gone). The browser check used a private server on port 8532
(`lf-b8rb-srv`) and Playwright 1.58.2 (`lf-b8rb-pw`), both stopped. The engine's tests pass (70 in
`test_beams*.py`, `out/s00_engine_tests.txt`), and so do v16's (19, `out/s00_v16_tests.txt`). The key-frame browser
check of v16 passes (`out/s10_browser_keyframes.txt`).

## Summary

| severity | count | findings |
|---|---|---|
| error | 2 | O1, O2 |
| should-fix | 6 | O3–O8 |
| nit | 10 | O9–O18 |

The core physics is right, and I reproduced it by independent routes. J_z = l + σ per photon is exact for this
construction. S_z = σ⟨cos θ⟩ and L_z = J − S hold to ≤ 7e-11 by a third route. The rotational Doppler signs and factors
reproduce from my own sampled series. The fork's Fourier coefficients are right. The author's claim of a sign misprint
in Barnett et al. 2017 is correct. The Poynting identity is right.

The problems are in what v16 says about these numbers and in its legal parameter space:
- a check note states the wrong order of the paraxial error;
- worlds whose named LG waist lies almost or entirely beyond q = k are built and titled as that mode, with no notice;
- the spin–orbit "split per photon" is shown as unique, although Barnett's flux split moves the other way;
- the Poynting angular momentum has a simple closed form that the run could check, but shows only "for information";
- there is no cost guard (a legal world needs an ~18 GB matrix);
- the thin-mask generators sit in the core, although the engine places the same boundary condition in `approx`.

## What was verified (status per item)

| item | result | evidence | status |
|---|---|---|---|
| Vector beam construction (`beams.py:20-29`, `_assemble`): the e_σ, e_−σ, ẑ decomposition with orders l, l+2σ, l+σ and the coefficients (1+c)/2, (1−c)/2, −i^σ s/√2 | Re-derived by hand from (θ̂ + iσφ̂)/√2·e^{i(l+σ)φ_k} and ∫e^{inφ'}e^{iqr cos(φ'−φ)}dφ' = 2π i^n J_n e^{inφ}; it agrees. The helicity sign is right: curl E = σkE, H = −iσE, and e_+ rotates from +x to +y under e^{−iωt}. | derivation; the engine's own Maxwell finite-difference tests | [useful] |
| J_z = l + σ per photon (per unit length) | Exact: the field is a Ĵ_z eigenstate, ⟨Ĵ_z⟩ = m⟨E\|E⟩, and W = ½∫\|E\|² for pure helicity. The engine's plane measurement gives it to 1e-10 for the two compact spectra. For the tight beam the window error is 5e-6. | `out/s01_jz_vector_beam.txt` | [useful] |
| S_z = σ⟨cos θ⟩, L_z = l + σ(1 − ⟨cos θ⟩) (density weight \|A\|² q dq) | Route A, independent of the engine: own `quad` radial functions, then plane integrals in the circular basis, ∫(\|F0\|² − \|F2\|²) / ∫(\|F0\|² + \|F2\|² + \|F1\|²) = ⟨c⟩ by Hankel–Parseval. Route B: `moments()`. Route C: the engine's densities on a plane. A, B and C agree to ≤ 7e-11 (l = 2, w0 = 1.2λ) and 3e-16 (l = 3, w0 = 1.5λ). For the tight beam, A and C differ from B by 3e-4: a window error, with the spectrum at 12.6 % of its maximum at q = k. | `s01` | [useful] |
| Barnett & Allen 1994 (text not obtained) | Secondary account, Monteiro et al. 2009, quoted below: for Barnett–Allen's beam the ratio J/W per unit length "was found not to be (ℓ + σ)/ω". That beam is not a J_z eigenstate ("does not coincide with the Barnett-Allen model"). J = l + σ is therefore a property of the engine's construction, not of nonparaxial beams in general (O17). | `out/s12_quotes_grep.txt` | [neutral] |
| Poynting identity ∫(r×P)_z dA = L_z + S_z + ½ d/dz ∫r·S_⊥ dA | Correct: derived by hand by integrating by parts (x∂_x + y∂_y)S_z; numerical residual 1e-12. The closed form of the last term is derived in O4. | `s02` | [useful] |
| Paraxial error (λ/w0)² (scalar) | Own `quad` Rayleigh–Sommerfeld against `PX.lg` at z = z_R for w0 = 1.5, 3, 6λ: 0.104, 0.0251, 0.0062, ratios 4.15 and 4.04. The engine's RS agrees with the own quadrature to 5e-9. | `out/s03_paraxial_scaling.txt` | [useful] |
| Rotational Doppler: co-rotating observer ω − (l+σ)Ω; image rotator ω − 2lΩ_p (scalar), ω − 2(l+σ)Ω_p (mirror-like); on-axis −lΩ; ±l filter beat 2\|l\|Ω | All reproduced with sign, on exact FFT bins, from own rotation, mirror, rough surface and FFT (5 + 3 + 2 cases). The physical sign is consistent with energy: an l > 0 beam scattered onto the axis gives its OAM to a disc turning the same way, so the light loses ℏlΩ ("Doing work against this force", Lavery). | `out/s04_rot_doppler.txt` | [useful] |
| Attributions: Courtial PRL 80 (lΩ, beam rotated at Ω), PRL 81 ((l+σ)), thesis (Dove prism in each arm; Δν = lF, F the beam's rate; Eq. 6.15) | Verified (OpenAlex abstracts; thesis pages 81 and 87 read on the rendered images). | `s12` | [useful] |
| Lavery et al. 2013, Eqs. (1), (3), (4), mode filter, "no dependence upon polarisation" | Verified on the accepted manuscript (page 3 rendered). Fig. 2's caption gives a sign ("positive ℓ … blue-shifted"), so the engine's convention note could say how it maps (O17). | `s12` | [useful] |
| Fork hologram: order m carries m·l; c_m (amplitude 1/2, 1/4; binary sin(mπ/2)/(mπ); blazed δ_m1) | Correct by hand (e^{i(f mod 2π)} = e^{if} exactly). The charges are measured in the run (v16 fork preset: −1, 0, 1). | `s05` | [useful] |
| Barnett, Babiker & Padgett 2017: curvature sign | The author's claim is correct. The published text (PMC5247487) prints Eq. (3.5) with exp(−ikρ²z/2(z_R²+z²)), next to v = u e^{ikz} (3.2) and i∂u/∂z = −(1/2k)∇⊥²u (3.4). With the printed sign the paraxial equation has a residual of 0.46–0.75; with + it is 3e-10–5e-10. The equation is (3.5) in the published version, "Eq. 6" in the accepted one. | `out/s11_barnett2017_sign.txt`; the equation images in the scratch folder | [useful] |
| Time and phase conventions | Consistent throughout:<br>• e^{−iωt};<br>• u e^{ikz} with +kr²/2R and −(N+1)ψ (`beams_paraxial`), as in `theories.approx.gaussian_beam` (q = z − iz_R);<br>• `spectrum()` puts e^{−iωt} at +ω;<br>• v16's sheets are arg ψ = ωt. | reading + `s04` | [useful] |
| v16 default numbers (README check table) | All reproduce (table 1.14e-7, J 4.0000000, S 0.9536057, L 3.0463943, Poynting 4.0479, power 7.7e-8, charge 3, Gouy −2.64376/−2.64159, sheets 3, flow 0.338 w0, ez 0.200, parax 0.281, slice 6.8e-8, beat 30.0001, shift −15). The exception is the flux: 4.0000000488, against 4.000000015 in the README (O18). | `out/s05_v16_presets_lg3_tight.txt` | [useful] |
| v16 tight preset: S = −0.842, L = 0.842, J = 0; paraxial counterpart L = 1, S = −1 | Reproduced. The window error of S (3e-4) is inside the stated tolerance of 4(\|l\|+2)·miss = 4.6e-3. The tolerance is derived: \|J − J_out\| ≲ 2(\|l\|+2), times miss, with a margin of 2. | `s05` | [useful] |
| Dove preset: beat 2\|l\|f, shift −2lf; l0: no beat; lin: J = l, S = 0 | Reproduced (19.9996 / −20; depth 4e-16; 1.0000000 / 0). | `out/s05_v16_presets_rest.txt` | [useful] |
| Radial table: interpolation and its in-run check | Errors 5e-9 … 1.3e-5 of the peak over the presets. The checked points are inside the table. One detector samples just outside it (O14). | `s05`, `s09` | [useful] |
| Layer of `beams_paraxial` (theories/approx) | Agreed: LAYERS.md §1, "paraxial against Rayleigh–Sommerfeld". Its conflicts name the fuller forms. It re-implements `rayleigh`/width of `theories.approx.gaussian_beam` with the same conventions (O12). | reading | [useful] |
| Stepped plate (test docstring "measured 1.26") | The value is grid-converged (1.2589 / 1.2606 on two grids) for the field propagated to z = 6. The sampled mask itself tends to the thin-mask symmetric sum (N/2π)sin(2πl/N) = 0.900 (0.961, then 0.930), derived here. The difference is the evanescent high harmonics; the number is right as stated. | `out/s09_table_range_and_stepped_plate.txt` | [neutral] |

## Findings

### O1 (error) — v16's check «Параксиальная мода против точного поля» states the wrong order of the error

*Location.* `visualizations/v16_optical_vortices/viz.py:382-390`. The note is «наибольшее отличие, доля пика; растёт
как (λ/w0)² = …» and it prints (λ/w0)² next to the value. README check table, row "paraxial mode against the exact
field on z_c".

*Evidence* (`scripts/s03_paraxial_scaling.py`, `out/s03_paraxial_scaling.txt`). The check compares all three
components of the exact vector beam with LG × e_σ at the waist. Its value is the longitudinal field, which is of first
order:

```
w0 =  1.5: all components 2.8030e-01, transverse only 4.7006e-02, max|E_z|/peak 2.8030e-01
w0 =  3.0: all components 1.4015e-01, transverse only 1.1371e-02, max|E_z|/peak 1.4015e-01   ratios: all 2.00, transverse 4.13
w0 =  6.0: all components 7.0075e-02, transverse only 2.8214e-03, max|E_z|/peak 7.0075e-02   ratios: all 2.00, transverse 4.03
```

The shown value (0.2806 for the default world, `s05`) equals max|E_z|/peak. It falls as λ/w0, not (λ/w0)². The
printed comparison number (0.444) therefore misleads.

*Fix.*
- Report the transverse difference (order (λ/w0)², which the note's scaling then describes) and E_z separately (order λ/w0; the check `ez` already shows it).
- Or keep one number and say "dominated by E_z: first order in λ/w0".
- Mark the README row [error in earlier].

### O2 (error) — "exact" worlds whose named LG waist lies mostly or entirely beyond q = k are built and titled as that mode, with no notice

*Location.*
- The exact vector beam keeps propagating waves only: `lfphys/lfphys/core/optics/beams.py:208` (`theta_max = asin(min(1, q_max/k))`).
- v16 builds it from the waist's spectrum: `visualizations/v16_optical_vortices/engine/apparatus.py:47-49, 67-73`.
- The header lists no approximation for an exact beam and gives the title «Оптический вихрь: LG…, точный векторный пучок»: `viz.py:752-763, 777-782`.
- The schema allows w0 = 0.3 µm with λ = 1.6 µm (`viz.py:56-57`).

*Evidence* (`scripts/s08_v16_tight_corners.py`, `out/s08_v16_tight_corners.txt`). The fraction of the named waist's
power at q > k, which the world drops, is:

```
LG_{0,1} w0 = 0.6, lambda = 1.0: 0.007        (the 'tight' preset)
LG_{0,1} w0 = 0.3, lambda = 1.0: 0.470
LG_{0,3} w0 = 0.3, lambda = 1.0: 0.895
LG_{3,6} w0 = 0.3, lambda = 1.6: 1.000
LG_{0,1} w0 = 0.3, lambda = 1.6: 0.846
```

All of these worlds build without an error. `header approximations []`, and every angular-momentum check becomes "for
information". The world titled "LG₃⁶, точный векторный пучок" contains none of LG₃⁶'s waist: what remains is the tail of
its spectrum below k, a different beam.

A hard cut at q = k with a non-zero spectrum there (the `tight` preset: 12.6 % of the maximum, `s05` "edge 0.126") also
gives the r^−3/2 tails. Those tails are why the windows miss energy (STATUS V44 f). The README says "propagating
waves only", but the run does not say how much of the named source that removes.

*Fix.*
- Compute the dropped fraction in the engine (e.g. `VortexBeam.evanescent_fraction()` from the full spectrum; for the spp spectrum, the part beyond k).
- Show it in the header or a check.
- Flag the world «модель: пучок с обрезанным спектром …» above a small threshold, and refuse above, say, 10 %.
- Or rename the parameter as the spectrum's Gaussian width in these worlds.
- State in README and the preset label that w0 names the spectrum's LG width, not the measured waist, when w0 ≲ λ.

### O3 (should-fix) — the spin–orbit "split per photon" is presented as unique; Barnett's flux split for the same beam changes the other way

*Location.*
- Engine: `beams.py:37-41` (per photon, N = W/ω, per unit length).
- v16 panel and help: `web/view.js:72, 86-87, 161` («спин S_z = σ⟨cos θ⟩ по модулю меньше 1 … спин-орбитальное расщепление при фокусировке»).
- Check labels: `viz.py:348-355` («… на фотон»).

*Evidence* (`scripts/s01_jz_vector_beam.py`, `out/s01_jz_vector_beam.txt`). Barnett's gauge-invariant separation of
the angular-momentum flux is used by Monteiro, Maia Neto & Nussenzveig, arXiv:0902.3214, Eqs. (33)–(36), for a focused
LG beam of the same structure (orders l, l+σ, l+2σ). For the engine's beam it is
spin flux / energy flux · ω = σ⟨(1+c²)/2⟩/⟨c⟩. I computed it from my own radial functions and in closed form:

```
l = 2, s = +1, w0 = 1.2:  canonical per unit length S - sigma = -0.0548;  Barnett flux split spin - sigma = +0.0022
l = 3, s = +1, w0 = 1.5:  -0.0464 against +0.0014
l = 1, s = -1, w0 = 0.6:  +0.1582 against -0.0241   (spin flux -1.024: |spin| > 1)
```

Monteiro et al. state the same direction: "we conclude that r is positive and does not depend on the sign of ℓ nor on
the value of σ". They also write: "To our knowledge, a consistent identification of spin and orbital contributions to
the local angular momentum or flux densities of nonparaxial beams is not available" (2009). Bliokh et al. 2010 give the
canonical per-unit-length split that the engine uses: "the energy per unit z-length", Eq. (25).

Both are published definitions. Only J_z = l + σ (and its flux) is definition-independent. STATUS V44 (f) records that
Barnett's split is "not implemented". The v16 text, however, presents the canonical numbers as *the* spin–orbit
conversion "на фотон" and does not say that another standard definition gives the opposite sign of the change.

*Fix.*
- Label S_z and L_z «на единицу длины, канонические плотности (Bliokh et al. 2010)».
- Add one sentence to the help and the README that the split depends on the definition; Barnett's flux split gives |spin| > 1 for the same beam.
- Optionally add the flux split. The closed form and the field route above agree to 2e-4 in a ±12λ window for the tight beam and to 1e-6 for the others.

### O4 (should-fix) — the Poynting angular momentum has a closed form; the docs' "converges or diverges" misleads; the check and the test could be real

*Location.*
- `beams.py:43-45` ("not zero for a beam that converges or diverges").
- `viz.py:360-363`: check `am_poynting`, reference l + σ shown "for information", note «у сходящегося или расходящегося пучка».
- `tests/test_beams.py:164-176`: tests only the identity and |J_P − (l+σ)| > 1e-2.

*Derivation* (this review). For pure helicity S = σP/ω pointwise: Bliokh, Bekshaev & Nori 2013, Eq. (3.50),
"S̄ = σP̄/ω". Then:
- ∫r·S_⊥ dA = (σ/ω) ∫r·P_⊥ dA.
- ∇·P = 0 gives ∫r·P_⊥ dA = ½ d/dz ∫r²P_z dA.
- P_z = (|F0|² − |F2|²)/2.
- The Hankel-space form of ∫r²|F|²dA is quadratic in z, with d²/dz² = ∫tan²θ (|a|²−|b|²) d²k (A real).

Hence, per photon:

    J_Poynting = l + σ + (σ/2) ⟨sin²θ / cos θ⟩     (⟨⟩ over |A|² q dq), independent of z.

*Evidence* (`scripts/s02_poynting_am.py`, `out/s02_poynting_am.txt`):

```
l=2, s=+1, w0=1.2: closed 3.05708595;  z = 0: 3.05708595 (diff -9e-10); z = 0.4: -1e-9; z = z_R: -2.9e-7
l=3, s=+1, w0=1.5: closed 4.04786356;  z = 0: 4.04786356 (diff -6e-15)     [v16 default shows 4.047863607]
l=2, s=-1, w0=1.2: closed 0.94291405;  z = 0: 0.94291405 (diff +9e-10)
```

The extra term is the same at the waist (z = 0), where the beam neither converges nor diverges. It is a property of the
angular spread, constant along z. "Converges or diverges" invites the wrong picture.

*Fix.*
- State the closed form in the docstring.
- Add it as `VortexBeam.moments()["J_poynting"]` (with σ̄ for mixed helicity: check the lin preset, 1.0000000119 against l = 1).
- Make v16's `am_poynting` a real check with that reference and the window tolerance.
- Replace the test's inequality with the closed form; keep the identity test as it is.

### O5 (should-fix) — no cost guard: legal worlds need up to ~18 GB in one matrix

*Location.*
- `visualizations/v16_optical_vortices/engine/apparatus.py:43-84`: the table's r grid of λ/16 out to 1.45·half; `VortexBeam.table(estimate=True)` with nodes ∝ k(r_far + z_max)θ_max, doubled.
- `beams_paraxial.fresnel_table`.
- `viz.py:118-152`: no estimate, no refusal. Compare v03 and v11's `_cost_guard`.

*Evidence* (`scripts/s06_v16_cost.py`, `out/s06_v16_cost.txt`; sizing only, nothing allocated). The largest dense
matrix per world:

```
('spp','exact',  l=6, w0=6, lam=0.4, zspan=3): nr = 8858, nq = 241408  -> ~17.9 GB
('spp','paraxial',l=6, w0=6, lam=0.4, zspan=3): nr = 8858, nq = 43056   -> ~3.2 GB
('mode','exact', l=6, p=3, w0=6, lam=0.4, zspan=3): nr = 5397, nq = 13568 -> ~0.63 GB
defaults: lg3 ~0.010 GB, spp ~0.017 GB
```

A measured build of a modest legal world (`spp`, l = 2, w0 = 6, λ = 1, zspan 1.5; 3.4e7 elements per matrix) takes
45.7 s (`out/s06_v16_cost_run.txt`). The worst corner is ~60 times larger: of order 45 min of Bessel evaluations, and it
exceeds the memory of a worker. For spp the cost is driven by θ_max = π/2 (the q⁻² spectrum has no cut-off) times the
whole z range.

*Fix.* Estimate n_r·n_q (and the time) from the same formulas before building. Refuse with the reason above a budget,
as v03/v11 do, or cap the depth of the region and the table's radius for spp (the light that leaves the window is not
shown anyway).

### O6 (should-fix) — the `spp` preset shows its central claim only "for information" and its label disagrees with what the run shows

*Location.*
- `viz.py:83`: the label «Спиральная фазовая пластинка, l = 2: не одна мода LG, но 2ħ на фотон».
- `viz.py:319` (AM plane at z0 + 2λ), `viz.py:341-345` (`wide = miss > 1e-3`).
- `apparatus.py:62` (am_half).

*Evidence* (`out/s05_v16_presets_rest.txt`, preset spp):

```
[info] am_J 3.0000490 (ref 3)   [info] am_S 0.87288 (ref 0.87190)   [info] am_L 2.12717 (ref 2.12810)   miss 1.26e-3
[info] power 0.0674 (window loses 6.7 % between planes)
```

The default spp world misses 1.26e-3 of the energy, just above the 1e-3 switch, so none of its angular-momentum
comparisons is a check. `test_every_preset_builds_and_passes_its_checks` passes because information checks are skipped.

The label promises "2ħ на фотон", while the world (exact, σ = +1) shows L_z = 2.127ħ and J_z = 3ħ. The 2ħ holds for the
scalar field (the engine's `scalar_oam_per_photon`, `test_beams.py:245`). In the vector world ⟨cos θ⟩ = 0.872, and that
number is set by the wide-angle light of the plate's singular centre (the q⁻² spectrum cut at q = k). It is a property
of the idealised thin plate, not of a real one.

*Fix.*
- Give the spp AM plane a window wide enough for the default preset (or measure the flux ratio, which converges faster), so that the preset's checks are checks.
- Relabel: «l = 2: заряд 2; орбитальный момент скалярного поля 2ħ на фотон; у векторного поля L_z = l + σ(1 − ⟨cos θ⟩)».
- Say in the README that ⟨cos θ⟩ here is set by the singular centre of the ideal plate.

### O7 (should-fix) — thin-mask models sit in the core, while the engine places the same boundary condition in `approx` and has fuller models

*Location.*
- `lfphys/lfphys/core/optics/beams_generation.py:29-40`: layer core; validity «тонкая маска (приближение тонкого транспаранта …)»; conflicts [].
- `beams_rotation.py:120-145, 41-55`: `SpinningSurface`, «тонкий фазовый экран, скалярно»; conflicts [].

*Reasoning.*
- LAYERS.md §1 puts "a simplified form of a law the engine *also* has in fuller form" in `theories/approx`.
- The precedent is exactly this boundary condition: `theories/approx/kirchhoff.py` is "the exact … propagation of Kirchhoff boundary values" ("the field inside a slit = the incident field"). Its layer is approx, and its conflicts name the vector theory.
- A thin transmission mask t(x, y) on z = 0 is the same thin-element (Kirchhoff) assumption.
- The engine now has fuller models of a structured plate: `core.em.fdtd` (B8) and `core.em.slit`.
- Rule 3 (a theory module names a conflict) is then also unmet.

The closed forms of `beams_rotation` (ω − mΩ etc.) are exact consequences of rotational symmetry and belong in the
core. The thin-screen measurable does not.

*Fix.* Either:
- move the mask and screen models (`spiral_phase_plate`, `fork_hologram`, `SpinningSurface`, `on_axis_amplitude`) to `theories.approx` (e.g. `approx.thin_masks`), naming the conflicts with `core.em.fdtd` and `core.em.slit`;
- or record in LAYERS.md why a thin mask counts as an exact boundary value here and not in `kirchhoff.py`.

`beams_paraxial` in approx is right (agreed).

### O8 (should-fix) — fork hologram: the power-fraction reference does not describe the measurement; the sampled binary mask is not the declared one

*Location.*
- `viz.py:464-466`: reference |c_m|²/Σ_{|j|≤40}|c_j|², "information".
- `apparatus.py:389`: the mask sampled point-wise.
- `Fork.orders` `apparatus.py:403-417`: power in a disc of 2.5 w(z).
- README check table: "power fractions 0.190, 0.591, 0.190 against 0.204, 0.503, 0.204".

*Evidence* (`scripts/s07_fork_fractions.py`, `out/s07_fork_fractions.txt`, default fork preset):

```
binary: power behind the sampled mask / incident = 0.5256   (thin binary mask: 0.4975; duty cycle on 9.8 samples per period ≈ 0.526)
        P_0/P_+1 in discs of 1.3, 2.5, 4.0 w(z): 5.79, 3.12, 2.86   (thin mask c0²/c1² = π²/4 = 2.47)
        orders |m| ≥ 3 are evanescent (sin θ_3 = 1.2): propagating-only reference [0.224, 0.552, 0.224]
amplitude: power behind 0.3741 (0.3750); P_0/P_+1 = 4.60 at 2.5 w(z) against 4.00
```

The 0.591 against 0.503 that the README shows without comment has three causes:
- The point-sampled binary mask has a 5 % larger c₀ (10 % in power) than the declared hologram.
- The ±1 orders are vortex beams with wide-angle tails (the singular fork centre) that fall outside 2.5 w(z).
- The reference counts evanescent orders.

The charges are unaffected.

*Fix.*
- Measure each order's power in the angular spectrum: the orders are separated there exactly; each lies around k_x = −mK.
- Use the propagating orders in the reference, and Parseval (mean |t|²) instead of a truncated sum.
- Sample the binary mask by its area fraction per cell (or report the sampled duty cycle in the check).

### O9 (nit) — the paraxial world shows an assigned S_z as if measured

`viz.py:394` sets `"S": sb, "S_ref": sb`. The panel row reads «S_z (спин) −1 ħ (формула −1)» (browser text,
`out/browser/s10_tight_par_text.txt`), the same form as the measured rows. The help below says «S_z = σ задан». *Fix:*
either show «задан моделью» in the value column or compute it from the table's fields with `spin_density` (it is σ
exactly for u·e_σ, so it would then be a real one-line check).

### O10 (nit) — labels

- J, S, L are «на фотон» everywhere (`viz.py:348-350`, `view.js:72`), but they are per unit length (only the Poynting row says «на единицу длины»). See O3.
- The panel's help says «Измерено по полю на плоскости z_c» (`view.js:87`), but spp worlds measure at z0 + 2λ (`viz.py:319`). The check label has the right z.
- The unit «ħω⁻¹·ω» (`view.js:83`) is ħ.
- The detector panel's «сдвиг частоты света» (`view.js:124`) is, for the Dove prism, the turned arm against the arm at rest; the check label is more precise («Сдвиг частоты повёрнутого пучка (по их перекрытию)»).

### O11 (nit) — time model: two clocks on one screen

The optical phase is slowed ×1.2·10¹⁴ (one period per `t_show`, labelled in «Время и фаза»). The rotating element turns
at f in world time (`viz.py:581-591`). On screen, the default world's helices turn at 1/(l·t_show) ≈ 0.83 turn/s and the
disc at 5 turn/s. Their relative rotation is not the Doppler mechanism: the shift −lf is relative to the true ω, which
is not shown.

The README's «The helices therefore turn on screen; in fact the wave front runs along z at c» (`README.md:61`) is
right, since for a helicoid a turn and a translation are the same motion. It does not warn about this comparison.
*Fix:* one line in the time panel and the README: the element turns in real world time, the optical phase is slowed,
so the picture's relative rotation is not the measured shift.

### O12 (nit) — the wrapper re-derives physics the engine has

- `viz.py:445-451`: W = π Σ|a|² ∫|A|² q dq (Parseval), using the engine's private `B._nodes`. It belongs in `VortexBeam`.
- `viz.py:593-601`: re-writes 2|l|f, −lf, −2lf instead of calling the tested `ROT.superposition_beat`, `scattered_on_axis_shift` and `rotated_beam_frequency`.
- `viz.py:418`: writes the Gouy reference inline (`PX.gouy` exists).
- `viz.py:271-279`: computes the paraxial current of the Fresnel field by its own differences.
- `engine_modules()` (`viz.py:739-748`) omits `theories.approx.beams_paraxial` for an exact spp world, which still uses `PX.rayleigh`/`PX.params` for its region and its helix grid.
- `beams_paraxial.rayleigh`/`params` duplicate `theories.approx.gaussian_beam` (same conventions).

### O13 (nit) — the drawn Dove prism is turned 90° from the computed one

`apparatus.py:274-287` draws the prism with its base face normal along x, so reflection off the base mirrors x → −x
(the mirror line is the y axis). The computed rotator at angle α mirrors across the line at α (`beams_rotation.py:104-117`):
the x axis at α = 0. The beat does not depend on the offset. *Fix:* rotate the mesh by 90° (or start α at π/2).

### O14 (nit) — a detector samples the beam outside the radial table

The `DovePrism` square has corners at √2·2.2 w(z_d)·√(max(|l|,1)/2 + p + 1) (`apparatus.py:357`). For l = 6, p = 3 this
is 19.29 µm, while the table ends at r_far = 19.23 µm (`apparatus.py:63`). The bicubic splines are evaluated outside
their data: the error is 5.9e-4 of the peak at a point where |E| is 1.8e-3 of the peak (`out/s09…txt`). *Fix:* take
r_far from the largest radius any consumer samples (the volume, the AM plane, the disc, the prism square).

### O15 (nit) — `VortexBeam.scalar`: unbounded panel count for a spectrum without cut-off as z_min → 0⁺

`beams.py:238-240`: tmax = 46/z_min and npan ∝ tmax·(r_max + 1/k). For the spp spectrum (q_max = ∞), z_min = 1e-4 λ
and r_max = 10λ give ≈ 7.4e5 panels × 16 nodes per evaluation point. That is a memory blow-up rather than an error
message. *Fix:* refuse z_min below a bound tied to the requested accuracy, or cap the panels and return the error
estimate.

### O16 (nit) — the exact model's Poynting flow lines carry no error measure

`viz.py:256-265` traces the lines with RK4 in 220 fixed steps through the table. The paraxial worlds check their
orbital lines against the closed spiral (`flow`). For the exact Poynting lines no error is measured, although
RULES §2.6 asks that numerical errors be measured by the run. *Fix:* step-doubling on one or two lines, reported as an
information check.

### O17 (nit) — the sources file can be sharpened

`lfphys/sources/verification_2026-11-04_p14_7_beams.md`:
- (§1) "The general form for a spectrum … is NOT FOUND as printed". Bliokh et al. 2010, Eq. (22), "S = … σκ … d²k⊥" with κ = k/k, normalised by the energy per unit z-length of their Eq. (A7), gives S_z = σ⟨cos θ⟩ for any spectrum. It can be cited as such.
- (§4) Monteiro, Maia Neto & Nussenzveig, PRA 79, 033830 (2009) (arXiv:0902.3214, open) give the secondary account of Barnett & Allen 1994 needed here: "the ratio between the total angular momentum per unit length and the total energy per unit length was found not to be (ℓ + σ)/ω as in the case of a paraxial beam", and "The nonparaxial focused beam model, as derived here, does not coincide with the Barnett-Allen model". Barnett & Allen is cited in `beams.ABOUT` as the basis for «непараксиальные пучки». The ABOUT could say that J = l + σ is a property of the J_z-eigenstate construction (Bliokh 2010), which Barnett–Allen's beam is not.
- (§6) The Barnett 2017 equation is (3.5) in the published text (PMC5247487); the claim itself is verified (`s11`).
- (§5) Lavery's Fig. 2 caption fixes a sign ("the light scattered from the positive ℓ beam will be blue-shifted"). The engine's convention gives −lΩ for a disc turning in the sense of the beam's OAM. A sentence on how the two map (sense of rotation, reflection geometry), and the physical rule (red shift when the disc turns with the OAM: the light does work on it), would close it.

### O18 (nit) — small inconsistencies

- README check table: "angular-momentum flux … 4.000000015". The default world gives 4.0000000488 (`s05`); it is within tolerance, but the printed number does not reproduce.
- `view.js:57`: the fork panel says «порядок m уходит под углом sin θ = mλ/Λ», while the engine (`beams_generation.order_direction`) and the run put order +1 at negative x (sin θ_m = −mλ/Λ; the check «x = −39.4 мкм»).

## Sources: obtained, quoted (grep in `out/s12_quotes_grep.txt`), and not obtained

Downloaded to the session scratch folder (not here), with no e-mail or identifier sent:
- K. Y. Bliokh et al., arXiv:1006.3876v3: Eqs. (22), (25), (26), (A7) and footnote [28]; quotes "Jz = ℓ + σ̄ (25)", "the energy per unit z-length", "no simple separation into ℓ-dependent orbital and σ-dependent spin component".
- K. Y. Bliokh, A. Y. Bekshaev, F. Nori, arXiv:1208.4523: "assume natural units", Eq. (3.50).
- M. V. Berry, J. Opt. A 11, 094001 (2009), the author's PDF: "there are no cross terms between + and −", "Efull (r , t) = Re E3 (r ) exp(−iωt)".
- P. B. Monteiro, P. A. Maia Neto, H. M. Nussenzveig, arXiv:0902.3214v1: Eqs. (33)–(39) read on the rendered page 8; the three quotes above.
- M. P. J. Lavery et al., Science 341, 537 (2013), accepted manuscript (Glasgow eprints 85025): Eqs. (1), (3), (4) on the rendered page 3; "there is no dependence upon polarisation", "their scattering into a common detection mode gives an intensity modulation", "acting as a mode filter to select only the desired superposition", "Doing work against this force is the energy input required to shift the frequency of the light", and the Fig. 2 caption.
- J. Courtial, PhD thesis, St Andrews 1999 (scanned; read on the rendered pages 81 and 87): "a Mach-Zehnder interferometer with a Dove prism in each arm, one rotating, the other one at rest", "differ by Δν = lF, where F is the rotation frequency of the beam", Eq. (6.15) "Δν = (l + σ)F".
- S. M. Barnett, M. Babiker, M. J. Padgett, Phil. Trans. R. Soc. A 375, 20150444 (2017), PMC5247487: equation images (3.2), (3.4), (3.5) read visually.
- OpenAlex abstracts (no contact parameter):
  - Courtial PRL 80, 3217: "We observe the frequency shift, lΩ, imparted to a mm-wave beam … when the beam is rotated at angular frequency Ω".
  - PRL 81, 4828: "The shift is equal to the total angular momentum per photon multiplied by the angular velocity between the source and observer".
  - Barnett 2002: "can be separated into spin and orbital parts. This separation is gauge invariant and does not rely on the paraxial approximation".
  - Garetz 1981, Allen 1992 and Durnin 1987: abstracts only.

Not obtained:
- the full texts of Barnett & Allen 1994 (no abstract in OpenAlex either), Barnett 2002, Allen et al. 1992, Garetz 1981, Beijersbergen et al. 1993, Durnin 1987 and the typeset PRL 80;
- Siegman's and Saleh–Teich's books.

The LG formulas and conventions were therefore checked through Barnett et al. 2017 and by the paraxial equation itself.

## Scripts and outputs (this folder)

| script | what | output |
|---|---|---|
| `run.sh` | Docker runner (read-only engine, CPU, `lf-b8rb-*`) | — |
| `scripts/s00_env.py` | versions | `out/s00_env.txt`; engine tests `out/s00_engine_tests.txt`; v16 tests `out/s00_v16_tests.txt` |
| `scripts/s01_jz_vector_beam.py` | J, S, L by three routes; Barnett's flux split | `out/s01_jz_vector_beam.txt` |
| `scripts/s02_poynting_am.py` | Poynting AM per unit length, the identity and its closed form at several z | `out/s02_poynting_am.txt` |
| `scripts/s03_paraxial_scaling.py` | (λ/w0)² of the scalar error; the order of v16's `parax` check | `out/s03_paraxial_scaling.txt` |
| `scripts/s04_rot_doppler.py` | own sampled series: observer, image rotator, spinning surface | `out/s04_rot_doppler.txt` |
| `scripts/s05_v16_presets.py` | every v16 preset through `tests/harness.py` | `out/s05_v16_presets_lg3_tight.txt`, `out/s05_v16_presets_rest.txt` |
| `scripts/s06_v16_cost.py` | sizing of the legal parameter corners; one timed build | `out/s06_v16_cost.txt`, `out/s06_v16_cost_run.txt` |
| `scripts/s07_fork_fractions.py` | the fork's order powers against references | `out/s07_fork_fractions.txt` |
| `scripts/s08_v16_tight_corners.py` | tight legal corners: the dropped waist fraction, the checks | `out/s08_v16_tight_corners.txt` |
| `scripts/s09_table_range_and_stepped_plate.py` | detectors against the table's range; the stepped plate | `out/s09_table_range_and_stepped_plate.txt` |
| `scripts/s10_shot.mjs` | browser screenshots and panel texts (lg3, tight_par, dove), private server | `out/browser/`; key frames `out/s10_browser_keyframes.txt` |
| `scripts/s11_barnett2017_sign.py` | Barnett et al. 2017 Eq. (3.5) in their own paraxial equation | `out/s11_barnett2017_sign.txt` |
| — | quotations grepped in the downloaded texts | `out/s12_quotes_grep.txt` |
