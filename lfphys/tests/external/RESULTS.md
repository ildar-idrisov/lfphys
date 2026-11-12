# Comparison of lfphys with third-party libraries (plan item P13)

Generated 2026-11-10 by `tests/external/make_results.py` in the image lfphys-ext (Python 3.11.17). Do not edit by hand; regenerate (README.md).

Each row is one assertion of `tests/external/test_ext_*.py`: the engine's value, the library's value, their difference and the tolerance derived for it (the derivations are in each module's docstring; the key is in the column *basis*). Where an exact reference exists (closed forms or the same equations in 30-50-digit mpmath for the same binary64 inputs), *eng err* and *lib err* are each side's distance to it. *status*: pass, FAIL, or xfail (a known disagreement, recorded with its numbers and asserted to persist).

## Libraries

| library | package | version | licence declared (installed metadata) | licence in the repository |
|---|---|---|---|---|
| CRunDec 3.1 via rundec | `rundec` | 0.7 | License: MIT | MIT (rundec-python LICENSE; CRunDec 3.1 source header: MIT, 'Jan 2019: Changed license from GPLv3 to MIT') |
| KerrGeoPy | `kerrgeopy` | 0.9.3 | classifier: MIT License | MIT (LICENSE) |
| tmm | `tmm` | 0.2.0 | License: MIT | MIT (LICENSE.txt) |
| QuTiP | `qutip` | 5.3.1 | License-Expression: BSD-3-Clause | BSD-3-Clause (LICENSE.txt) |
| QuTiP (open systems) | `qutip` | 5.3.1 | License-Expression: BSD-3-Clause | BSD-3-Clause (LICENSE.txt) |
| Astropy | `astropy` | 8.0.2 | License-Expression: BSD-3-Clause | BSD-3-Clause (LICENSE.rst) |
| Astropy (FLRW cosmology) | `astropy` | 8.0.2 | License-Expression: BSD-3-Clause | BSD-3-Clause (LICENSE.rst) |
| miepython (Mie scattering) | `miepython` | 3.3.0 | License-Expression: MIT | MIT (LICENSE.txt, 2026-11-04) |

Engine side: lfphys from this repository, numpy 2.4.6, scipy 1.17.1, mpmath 1.3.0 (the runtime image's pinned versions). The libraries are used only here, in a separate image that is never distributed (README.md); their audit: `../../sources/dependencies.md`, section "Comparison-only libraries (plan P13)".

Editions of the constants:

* engine: CODATA 2022 via scipy 1.17.1, IAU 2012 B2 (au), IAU 2015 B3 (nominal solar and terrestrial values)
* astropy 8.0.2: physical_constants = codata2022, astronomical_constants = iau2015
* CODATA 2018 -> 2022 shifts (astropy.constants.codata2018 vs codata2022), for scale: m_e: +1.36e-09 relative (+4.43 standard uncertainties of 2022); m_p: +1.35e-09 relative (+4.35 standard uncertainties of 2022); alpha: -6.85e-10 relative (-4.55 standard uncertainties of 2022); u: +1.40e-09 relative (+4.46 standard uncertainties of 2022); G: +0.00e+00 relative (+0.00 standard uncertainties of 2022)

## Summary

| library | comparisons | pass | xfail (known) | FAIL | max diff/tol (passing) | engine closer to exact | library closer | equal |
|---|---|---|---|---|---|---|---|---|
| CRunDec 3.1 via rundec | 216 | 208 | 8 | 0 | 0.060 | 120 | 0 | 96 |
| KerrGeoPy | 1056 | 1056 | 0 | 0 | 0.232 | 562 | 314 | 108 |
| tmm | 476 | 472 | 4 | 0 | 0.077 | 285 | 132 | 59 |
| QuTiP | 110 | 110 | 0 | 0 | 0.111 | 13 | 21 | 27 |
| QuTiP (open systems) | 91 | 91 | 0 | 0 | 0.448 | 41 | 42 | 8 |
| Astropy | 25 | 25 | 0 | 0 | 0.000 | 0 | 0 | 0 |
| Astropy (FLRW cosmology) | 661 | 660 | 1 | 0 | 0.996 | 344 | 57 | 118 |
| miepython (Mie scattering) | 326 | 320 | 6 | 0 | 0.998 | 292 | 20 | 14 |

*engine closer / library closer / equal*: among the rows with an exact reference, which side is nearer to it.

## Known disagreements

* CRunDec 3.1 via rundec: alpha_s with thresholds, 1 loop at mu=4.18299582 GeV: CRunDec AlphasExact over a range \|ln(mu/mu0)\| = 1e-06 < 1e-4 takes its fixed first step of 1e-4 and returns alpha_s at mu0 e^(+-1e-4): measured \|engine - CRunDec\| = 5.91e-06, \|engine - exact\| = 1.8e-14, \|CRunDec - exact\| = 5.91e-06 (tolerance 1.45e-08)
* CRunDec 3.1 via rundec: alpha_s with thresholds, 1 loop at mu=162.500162 GeV: CRunDec AlphasExact over a range \|ln(mu/mu0)\| = 1e-06 < 1e-4 takes its fixed first step of 1e-4 and returns alpha_s at mu0 e^(+-1e-4): measured \|engine - CRunDec\| = 1.31e-06, \|engine - exact\| = 2.13e-16, \|CRunDec - exact\| = 1.31e-06 (tolerance 2.51e-09)
* CRunDec 3.1 via rundec: alpha_s with thresholds, 2 loop at mu=4.18299582 GeV: CRunDec AlphasExact over a range \|ln(mu/mu0)\| = 1e-06 < 1e-4 takes its fixed first step of 1e-4 and returns alpha_s at mu0 e^(+-1e-4): measured \|engine - CRunDec\| = 7.28e-06, \|engine - exact\| = 2.32e-14, \|CRunDec - exact\| = 7.28e-06 (tolerance 1.79e-08)
* CRunDec 3.1 via rundec: alpha_s with thresholds, 2 loop at mu=162.500162 GeV: CRunDec AlphasExact over a range \|ln(mu/mu0)\| = 1e-06 < 1e-4 takes its fixed first step of 1e-4 and returns alpha_s at mu0 e^(+-1e-4): measured \|engine - CRunDec\| = 1.34e-06, \|engine - exact\| = 2.12e-16, \|CRunDec - exact\| = 1.34e-06 (tolerance 2.51e-09)
* CRunDec 3.1 via rundec: alpha_s with thresholds, 3 loop at mu=4.18299582 GeV: CRunDec AlphasExact over a range \|ln(mu/mu0)\| = 1e-06 < 1e-4 takes its fixed first step of 1e-4 and returns alpha_s at mu0 e^(+-1e-4): measured \|engine - CRunDec\| = 7.45e-06, \|engine - exact\| = 2.37e-14, \|CRunDec - exact\| = 7.45e-06 (tolerance 1.82e-08)
* CRunDec 3.1 via rundec: alpha_s with thresholds, 3 loop at mu=162.500162 GeV: CRunDec AlphasExact over a range \|ln(mu/mu0)\| = 1e-06 < 1e-4 takes its fixed first step of 1e-4 and returns alpha_s at mu0 e^(+-1e-4): measured \|engine - CRunDec\| = 1.34e-06, \|engine - exact\| = 2.24e-16, \|CRunDec - exact\| = 1.34e-06 (tolerance 2.51e-09)
* CRunDec 3.1 via rundec: alpha_s with thresholds, 4 loop at mu=4.18299582 GeV: CRunDec AlphasExact over a range \|ln(mu/mu0)\| = 1e-06 < 1e-4 takes its fixed first step of 1e-4 and returns alpha_s at mu0 e^(+-1e-4): measured \|engine - CRunDec\| = 7.51e-06, \|engine - exact\| = 2.4e-14, \|CRunDec - exact\| = 7.51e-06 (tolerance 1.83e-08)
* CRunDec 3.1 via rundec: alpha_s with thresholds, 4 loop at mu=162.500162 GeV: CRunDec AlphasExact over a range \|ln(mu/mu0)\| = 1e-06 < 1e-4 takes its fixed first step of 1e-4 and returns alpha_s at mu0 e^(+-1e-4): measured \|engine - CRunDec\| = 1.34e-06, \|engine - exact\| = 2.01e-16, \|CRunDec - exact\| = 1.34e-06 (tolerance 2.51e-09)
* tmm: stack t (s) at opaque metal 2 um, th0=17.1887 deg: tmm resets an opaque layer's Im(delta) > 35 to 35: measured t engine -2.653e-29+4.151e-31j, tmm 6.143e-16, exact 2.654e-29 (\|engine - exact\| = 1.5e-43, \|tmm - exact\| = 6.1e-16, tolerance 3.3e-41)
* tmm: stack T (s) at opaque metal 2 um, th0=17.1887 deg: tmm resets an opaque layer's Im(delta) > 35 to 35: measured T engine 1.084e-57, tmm 5.81e-31, exact 1.084e-57 (\|engine - exact\| = 1.2e-71, \|tmm - exact\| = 5.8e-31, tolerance 2.1e-69)
* tmm: stack t (p) at opaque metal 2 um, th0=17.1887 deg: tmm resets an opaque layer's Im(delta) > 35 to 35: measured t engine -2.801e-29-8.033e-31j, tmm 6.486e-16, exact 2.802e-29 (\|engine - exact\| = 1.6e-43, \|tmm - exact\| = 6.5e-16, tolerance 3.5e-41)
* tmm: stack T (p) at opaque metal 2 um, th0=17.1887 deg: tmm resets an opaque layer's Im(delta) > 35 to 35: measured T engine 1.208e-57, tmm 6.477e-31, exact 1.208e-57 (\|engine - exact\| = 1.3e-71, \|tmm - exact\| = 6.5e-31, tolerance 2.4e-69)
* Astropy (FLRW cosmology): closed LCDM + radiation: age [Gyr] at z=1000: library-side: Astropy's QUADPACK (QAGI, default epsabs/epsrel 1.49e-8) returns the dimensionless age integral 2.93119e-5 with error estimate 9.4e-9; the integral is 2.889449e-5 (quad at epsrel 1e-13; mpmath): 1.4 % high; engine - exact = 1e-19 Gyr
* miepython (Mie scattering): coefficient a_n at m=1.333, x=100, n=1: miepython's a_1 is 4.20e-13 of the largest coefficient from the exact value (the engine's 1.57e-14), beyond the 16 N u allowance: its coefficients carry an error of that size at every order, ~3e-13 at x = 100, ~1e-12 at 1000, ~1.1e-9 at 1e4 (up to 3e-8 near n ~ x) (measured, test_miepython_coefficient_error_by_order)
* miepython (Mie scattering): coefficient a_n at m=1.333, x=100, n=60: miepython's a_60 is 3.66e-13 of the largest coefficient from the exact value (the engine's 1.24e-14), beyond the 16 N u allowance: its coefficients carry an error of that size at every order, ~3e-13 at x = 100, ~1e-12 at 1000, ~1.1e-9 at 1e4 (up to 3e-8 near n ~ x) (measured, test_miepython_coefficient_error_by_order)
* miepython (Mie scattering): coefficient a_n at m=1.333, x=10000, n=1: miepython's a_1 is 6.98e-10 of the largest coefficient from the exact value (the engine's 3.12e-13), beyond the 16 N u allowance: its coefficients carry an error of that size at every order, ~3e-13 at x = 100, ~1e-12 at 1000, ~1.1e-9 at 1e4 (up to 3e-8 near n ~ x) (measured, test_miepython_coefficient_error_by_order)
* miepython (Mie scattering): coefficient b_n at m=1.333, x=10000, n=1: miepython's b_1 is 1.17e-09 of the largest coefficient from the exact value (the engine's 5.15e-13), beyond the 16 N u allowance: its coefficients carry an error of that size at every order, ~3e-13 at x = 100, ~1e-12 at 1000, ~1.1e-9 at 1e4 (up to 3e-8 near n ~ x) (measured, test_miepython_coefficient_error_by_order)
* miepython (Mie scattering): coefficient a_n at m=1.333, x=10000, n=5044: miepython's a_5044 is 8.24e-10 of the largest coefficient from the exact value (the engine's 3.28e-13), beyond the 16 N u allowance: its coefficients carry an error of that size at every order, ~3e-13 at x = 100, ~1e-12 at 1000, ~1.1e-9 at 1e4 (up to 3e-8 near n ~ x) (measured, test_miepython_coefficient_error_by_order)
* miepython (Mie scattering): coefficient b_n at m=1.333, x=10000, n=5044: miepython's b_5044 is 9.78e-10 of the largest coefficient from the exact value (the engine's 3.88e-13), beyond the 16 N u allowance: its coefficients carry an error of that size at every order, ~3e-13 at x = 100, ~1e-12 at 1000, ~1.1e-9 at 1e4 (up to 3e-8 near n ~ x) (measured, test_miepython_coefficient_error_by_order)

## Tolerance bases

| basis | meaning (details in the module docstrings) |
|---|---|
| 1 roundings | one rounding per side: 2 gamma_1 \|x\| |
| 12 roundings | twelve roundings per side: 2 gamma_12 \|x\| |
| 16 roundings + literal | 2 gamma_16 \|x\| plus Astropy's 11-digit literal for 7/8 (4/11)^(4/3) |
| 16 roundings + literal + Komatsu fit 0.35 % | 2 gamma_16 \|x\|, the literal, and Komatsu's 0.35 % on the massive share |
| 16u x conditioning per side | E, Omega_x(z), rho_crit evaluated algebraically: 16u per side times the conditioning sum\|terms\|/E^2 of the Friedmann sum, plus Astropy's 11-digit literal 0.22710731766 for 7/8 (4/11)^(4/3) (relative 1.05e-12) on the neutrinos' share |
| 16u x conditioning per side + Komatsu fit 0.35 % | E, Omega_x(z), rho_crit evaluated algebraically: 16u per side times the conditioning sum\|terms\|/E^2 of the Friedmann sum, plus Astropy's 11-digit literal 0.22710731766 for 7/8 (4/11)^(4/3) (relative 1.05e-12) on the neutrinos' share; the massive neutrino through Komatsu et al. 2011's fit: 0.35 % of its density (half of its largest share over the range for integrals and E) |
| 2 roundings | two roundings per side: 2 gamma_2 \|x\| |
| 4 roundings | four roundings per side: 2 gamma_4 \|x\| |
| 8 roundings | eight roundings per side: 2 gamma_8 \|x\| |
| DKW two-sample | eps(N_e) + eps(N_q), eps(N) = sqrt(ln(2/alpha)/(2N)) at alpha = 1e-6, plus QuTiP's collapse-time bias in the CDF |
| Komatsu fit 0.35 % + literal | the neutrino density relative to photons: Komatsu's 0.35 % on the massive share, the 11-digit literal, 32u, the engine's Fermi-Dirac quadrature bound (4e-15) twice; the exact value by 30-digit quadrature |
| LAPACK eig + h(x) | LAPACK eigenvalue error p(n) u \|\|rho\|\| (p(n) = 10n) through h(x) = -x log2 x, and the cut-offs |
| LAPACK eig + sqrt | Bauer-Fike with LAPACK's p(n) u \|\|R\|\|, through sqrt (sqrt(dl) at zero eigenvalues) |
| Lueders | products P rho P and the division by p, per side |
| MC z = 5 | 5 sqrt(se_engine^2 + se_qutip^2) of the trajectory means, plus QuTiP's collapse-time and ODE bias |
| TMM rounding | 16u backward error in every input, admittance and phase (mpmath sensitivities) on each side, tmm's absolute error in cos(arcsin x), and the 2x2 product chain (product of moduli) |
| TMM rounding (fluxes) | as TMM rounding; tmm's absorption is a difference of two fluxes |
| TMM rounding + running error | tmm side as TMM rounding, the engine's closed form by its running bound |
| TMM rounding + stated err | the engine's stated err_r/err_t/err_T plus TMM rounding |
| Wedin + LU | engine: Wedin's bound on the SVD null vector; QuTiP direct: cond(A)(10 n u + \|\|E_c\|\|/\|\|A\|\|) for the LAPACK solve, plus its hermitisation |
| brentq + noise | brentq's xtol + rtol\|p\| plus the width of {\|S_exact\| <= running bound of S} (KerrGeoPy), plus the engine's running error bound |
| coefficient budgets + truncation | engine: its tested coefficient bound (mie.coefficient_bound: u (4N + 8s), s the case's largest sensitivity x\|da_n/dx\|/max\|a\| of the exact coefficients, 50 digits) propagated through the row's formula with the moduli of its partial derivatives; miepython: its coefficients' measured distance to the 40-digit reference, propagated the same way, plus the omitted tail beyond its N = Wiscombe's; both: gamma_{8N} times the moduli of the summed terms |
| conditioning + running error | the engine's Newton-polished E, L, Q: \|J^-1\| gamma_16 \|terms\| x 2 + 2u (J the Jacobian of the defining equations); KerrGeoPy's closed form: its running error bound (_common.Fe) |
| contraction 12 | sum \|x\|\|y\| gamma_12 per side |
| contraction 18 | sum \|x\|\|y\| gamma_18 per side |
| contraction 2 | one complex addition per entry, per side |
| contraction 34 | sum \|x\|\|y\| gamma_34 per side (QuTiP and engine contractions) |
| contraction 34 x 4 | four contractions and three additions (CHSH) |
| decoupling | rounding of alpha(1 + c2 a^2 + c3 a^3): 2 gamma_16 alpha (1 + \|c2\| a^2 + \|c3\| a^3) |
| engine bound + closed form 64u | engine: the error bound its integral returns; Astropy's closed forms (flat, no radiation): 64u times the sum of the moduli of the two terms it subtracts (hyp2f1 or asinh; scipy states no bound for hyp2f1, the measured lib err is shown) |
| engine bound + quad 1.49e-8 | engine: the error bound its integral returns (with_error=True); Astropy: QUADPACK's request, scipy.integrate.quad's defaults epsabs = epsrel = 1.49e-8, i.e. 1.49e-8 max(1, \|I\|) of the dimensionless integral times c/H0 or 1/H0 |
| engine bound + quad 1.49e-8 + Komatsu fit 0.35 % | engine: the error bound its integral returns (with_error=True); Astropy: QUADPACK's request, scipy.integrate.quad's defaults epsabs = epsrel = 1.49e-8, i.e. 1.49e-8 max(1, \|I\|) of the dimensionless integral times c/H0 or 1/H0; the massive neutrino through Komatsu et al. 2011's fit: 0.35 % of its density (half of its largest share over the range for integrals and E) |
| engine estimate + Verner control | engine: the error estimate evolve() returns (step doubling); QuTiP vern9: d^{3/2}(atol + rtol) per step times the attempted steps (counted coefficient calls / 16 stages); global <= sum of local errors (CPTP flow contracts the trace norm) |
| expm + diag a posteriori | engine: its stated expm bound plus the construction error carried by trace-norm contraction; QuTiP diag: residuals L U - U Lambda and U Uinv - I in mpmath, the roundings of Uinv rho0, of the k products by exp(lambda dt) and of U y |
| expm/gates | scipy expm (backward error u\|\|A\|\|, Lipschitz 1 on skew-Hermitian) and QuTiP's five gates |
| integrators | both sides' stated error control: CRunDec pi*1e-10 per accepted Runge-Kutta step, the engine's DOP853 atol + rtol\|a\| per step, steps counted, propagated with f(a_end)/f(a_k) |
| one rounding + TMM rounding | the engine's stated single rounding plus tmm's sensitivity terms |
| propagated + closed form 64u | the bounds of D_C (engine + library as in the other bases) carried through sinh/sin and the factors (1+z), log10, plus 2u per extra operation; Astropy: closed form 64u |
| propagated + quad 1.49e-8 | the bounds of D_C (engine + library as in the other bases) carried through sinh/sin and the factors (1+z), log10, plus 2u per extra operation; Astropy: QUADPACK's 1.49e-8 request |
| propagated + quad 1.49e-8 + Komatsu fit 0.35 % | the bounds of D_C (engine + library as in the other bases) carried through sinh/sin and the factors (1+z), log10, plus 2u per extra operation; Astropy: QUADPACK's 1.49e-8 request; the massive neutrino through Komatsu et al. 2011's fit: 0.35 % of its density (half of its largest share over the range for integrals and E) |
| residual | running error bound of the engine's R(r) with KerrGeoPy's E, L carrying their own bounds |
| running error | first-order running error bounds of both sides along their actual operations (_common.Fe) |
| same decimal | both sides parse the same published decimal: 0 |
| sensitivity budget | 256 u per input (p, e, x), per constant (E, L, Q) and on the result, propagated with the engine's sensitivities; plus KerrGeoPy's constants' running bounds propagated the same way |
| stated bound + 16N u | the engine's tested coefficient bound with that order's sensitivity, u (4N + 8s), plus 16 N u of the largest coefficient for the library's recurrences |
| superop rounding | every Liouvillian entry within gamma_k M_ij (k = 3 + 2d + 2(2 + 3 n_c), M the sum of the moduli of its kron terms), per side |

## CRunDec 3.1 via rundec (`test_ext_qcd_rundec.py`)

| quantity | inputs | engine | library | diff | tol | status | basis | eng err | lib err |
|---|---|---|---|---|---|---|---|---|---|
| alpha_s, n_f = 3 fixed, 1 loop | mu=1.5 GeV | 0.385940081704953 | 0.385940079999334 | 1.71e-09 | 8.07e-08 | pass | integrators | 9.67e-14 | 1.71e-09 |
| alpha_s, n_f = 3 fixed, 1 loop | mu=5 GeV | 0.231715353451661 | 0.231715352972993 | 4.79e-10 | 1.82e-08 | pass | integrators | 2.36e-14 | 4.79e-10 |
| alpha_s, n_f = 3 fixed, 1 loop | mu=30 GeV | 0.145303510535021 | 0.145303510469973 | 6.50e-11 | 3.81e-09 | pass | integrators | 2.26e-15 | 6.50e-11 |
| alpha_s, n_f = 3 fixed, 1 loop | mu=300 GeV | 0.0982283883930698 | 0.0982283883684806 | 2.46e-11 | 2.51e-09 | pass | integrators | 3.39e-16 | 2.46e-11 |
| alpha_s, n_f = 3 fixed, 1 loop | mu=3000 GeV | 0.0741918656406947 | 0.074191865492701 | 1.48e-10 | 3.46e-09 | pass | integrators | 6.64e-16 | 1.48e-10 |
| alpha_s, n_f = 3 fixed, 2 loop | mu=1.5 GeV | 0.542721543091295 | 0.54272154004055 | 3.05e-09 | 2.61e-07 | pass | integrators | 2.80e-13 | 3.05e-09 |
| alpha_s, n_f = 3 fixed, 2 loop | mu=5 GeV | 0.255170383698727 | 0.255170383191546 | 5.07e-10 | 2.84e-08 | pass | integrators | 3.61e-14 | 5.07e-10 |
| alpha_s, n_f = 3 fixed, 2 loop | mu=30 GeV | 0.147854501031827 | 0.147854500968423 | 6.34e-11 | 4.51e-09 | pass | integrators | 3.65e-15 | 6.34e-11 |
| alpha_s, n_f = 3 fixed, 2 loop | mu=300 GeV | 0.0972424317296103 | 0.0972424317136124 | 1.60e-11 | 2.51e-09 | pass | integrators | 4.85e-16 | 1.60e-11 |
| alpha_s, n_f = 3 fixed, 2 loop | mu=3000 GeV | 0.0727896619820362 | 0.0727896618990294 | 8.30e-11 | 3.77e-09 | pass | integrators | 7.70e-16 | 8.30e-11 |
| alpha_s, n_f = 3 fixed, 3 loop | mu=1.5 GeV | 0.607022896670349 | 0.607022892715465 | 3.95e-09 | 4.22e-07 | pass | integrators | 4.26e-13 | 3.96e-09 |
| alpha_s, n_f = 3 fixed, 3 loop | mu=5 GeV | 0.25906895590565 | 0.259068955412592 | 4.93e-10 | 2.99e-08 | pass | integrators | 4.06e-14 | 4.93e-10 |
| alpha_s, n_f = 3 fixed, 3 loop | mu=30 GeV | 0.148132660924362 | 0.148132660863289 | 6.11e-11 | 4.54e-09 | pass | integrators | 3.72e-15 | 6.11e-11 |
| alpha_s, n_f = 3 fixed, 3 loop | mu=300 GeV | 0.0971592253309653 | 0.0971592253157829 | 1.52e-11 | 2.51e-09 | pass | integrators | 4.48e-16 | 1.52e-11 |
| alpha_s, n_f = 3 fixed, 3 loop | mu=3000 GeV | 0.0726882521839779 | 0.0726882521146713 | 6.93e-11 | 3.77e-09 | pass | integrators | 7.32e-16 | 6.93e-11 |
| alpha_s, n_f = 3 fixed, 4 loop | mu=1.5 GeV | 0.652764618347461 | 0.65276461326927 | 5.08e-09 | 6.12e-07 | pass | integrators | 5.83e-13 | 5.08e-09 |
| alpha_s, n_f = 3 fixed, 4 loop | mu=5 GeV | 0.260196087179705 | 0.260196086687227 | 4.92e-10 | 3.05e-08 | pass | integrators | 4.18e-14 | 4.93e-10 |
| alpha_s, n_f = 3 fixed, 4 loop | mu=30 GeV | 0.148188184165577 | 0.148188184104934 | 6.06e-11 | 4.55e-09 | pass | integrators | 3.73e-15 | 6.06e-11 |
| alpha_s, n_f = 3 fixed, 4 loop | mu=300 GeV | 0.0971458828780817 | 0.0971458828629983 | 1.51e-11 | 2.51e-09 | pass | integrators | 4.57e-16 | 1.51e-11 |
| alpha_s, n_f = 3 fixed, 4 loop | mu=3000 GeV | 0.0726738877480128 | 0.0726738876809457 | 6.71e-11 | 3.77e-09 | pass | integrators | 7.50e-16 | 6.71e-11 |
| alpha_s, n_f = 4 fixed, 1 loop | mu=1.5 GeV | 0.330372028739755 | 0.330372027549122 | 1.19e-09 | 5.18e-08 | pass | integrators | 6.49e-14 | 1.19e-09 |
| alpha_s, n_f = 4 fixed, 1 loop | mu=5 GeV | 0.216276579045231 | 0.216276578653851 | 3.91e-10 | 1.48e-08 | pass | integrators | 1.87e-14 | 3.91e-10 |
| alpha_s, n_f = 4 fixed, 1 loop | mu=30 GeV | 0.142855021159497 | 0.142855021112036 | 4.75e-11 | 3.68e-09 | pass | integrators | 2.11e-15 | 4.75e-11 |
| alpha_s, n_f = 4 fixed, 1 loop | mu=300 GeV | 0.0994628776499451 | 0.0994628776271826 | 2.28e-11 | 2.51e-09 | pass | integrators | 3.65e-16 | 2.28e-11 |
| alpha_s, n_f = 4 fixed, 1 loop | mu=3000 GeV | 0.0762898673733665 | 0.0762898671853084 | 1.88e-10 | 3.14e-09 | pass | integrators | 7.38e-16 | 1.88e-10 |
| alpha_s, n_f = 4 fixed, 2 loop | mu=1.5 GeV | 0.402180663986694 | 0.402180662440037 | 1.55e-09 | 1.07e-07 | pass | integrators | 1.28e-13 | 1.55e-09 |
| alpha_s, n_f = 4 fixed, 2 loop | mu=5 GeV | 0.231569243455273 | 0.231569243065814 | 3.89e-10 | 2.04e-08 | pass | integrators | 2.69e-14 | 3.89e-10 |
| alpha_s, n_f = 4 fixed, 2 loop | mu=30 GeV | 0.144805642182914 | 0.144805642124189 | 5.87e-11 | 4.31e-09 | pass | integrators | 2.42e-15 | 5.87e-11 |
| alpha_s, n_f = 4 fixed, 2 loop | mu=300 GeV | 0.0986445210454536 | 0.0986445210309484 | 1.45e-11 | 2.51e-09 | pass | integrators | 3.68e-16 | 1.45e-11 |
| alpha_s, n_f = 4 fixed, 2 loop | mu=3000 GeV | 0.075076728857373 | 0.075076728788507 | 6.89e-11 | 3.46e-09 | pass | integrators | 6.83e-16 | 6.89e-11 |
| alpha_s, n_f = 4 fixed, 3 loop | mu=1.5 GeV | 0.416442208497272 | 0.416442206876706 | 1.62e-09 | 1.25e-07 | pass | integrators | 1.48e-13 | 1.62e-09 |
| alpha_s, n_f = 4 fixed, 3 loop | mu=5 GeV | 0.233372419290888 | 0.233372418911596 | 3.79e-10 | 2.10e-08 | pass | integrators | 2.82e-14 | 3.79e-10 |
| alpha_s, n_f = 4 fixed, 3 loop | mu=30 GeV | 0.144970077353776 | 0.144970077296996 | 5.68e-11 | 4.33e-09 | pass | integrators | 2.50e-15 | 5.68e-11 |
| alpha_s, n_f = 4 fixed, 3 loop | mu=300 GeV | 0.0985896058182176 | 0.0985896058044986 | 1.37e-11 | 2.51e-09 | pass | integrators | 3.57e-16 | 1.37e-11 |
| alpha_s, n_f = 4 fixed, 3 loop | mu=3000 GeV | 0.0750062510048854 | 0.075006250939283 | 6.56e-11 | 3.46e-09 | pass | integrators | 6.72e-16 | 6.56e-11 |
| alpha_s, n_f = 4 fixed, 4 loop | mu=1.5 GeV | 0.422829622173506 | 0.422829620488317 | 1.69e-09 | 1.38e-07 | pass | integrators | 1.62e-13 | 1.69e-09 |
| alpha_s, n_f = 4 fixed, 4 loop | mu=5 GeV | 0.233877057661218 | 0.233877057282956 | 3.78e-10 | 2.11e-08 | pass | integrators | 2.87e-14 | 3.78e-10 |
| alpha_s, n_f = 4 fixed, 4 loop | mu=30 GeV | 0.145004176421771 | 0.1450041763654 | 5.64e-11 | 4.34e-09 | pass | integrators | 2.55e-15 | 5.64e-11 |
| alpha_s, n_f = 4 fixed, 4 loop | mu=300 GeV | 0.0985802637101776 | 0.0985802636966003 | 1.36e-11 | 2.51e-09 | pass | integrators | 3.64e-16 | 1.36e-11 |
| alpha_s, n_f = 4 fixed, 4 loop | mu=3000 GeV | 0.0749955927918943 | 0.0749955927263902 | 6.55e-11 | 3.46e-09 | pass | integrators | 6.73e-16 | 6.55e-11 |
| alpha_s, n_f = 5 fixed, 1 loop | mu=1.5 GeV | 0.288791525574291 | 0.288791524704783 | 8.70e-10 | 3.58e-08 | pass | integrators | 4.50e-14 | 8.70e-10 |
| alpha_s, n_f = 5 fixed, 1 loop | mu=5 GeV | 0.20276660718188 | 0.202766606854514 | 3.27e-10 | 1.21e-08 | pass | integrators | 1.48e-14 | 3.27e-10 |
| alpha_s, n_f = 5 fixed, 1 loop | mu=30 GeV | 0.140487682634394 | 0.140487682593502 | 4.09e-11 | 3.56e-09 | pass | integrators | 2.04e-15 | 4.09e-11 |
| alpha_s, n_f = 5 fixed, 1 loop | mu=300 GeV | 0.100728790815724 | 0.100728790794328 | 2.14e-11 | 2.51e-09 | pass | integrators | 3.28e-16 | 2.14e-11 |
| alpha_s, n_f = 5 fixed, 1 loop | mu=3000 GeV | 0.0785099768980663 | 0.0785099767784216 | 1.20e-10 | 3.14e-09 | pass | integrators | 6.37e-16 | 1.20e-10 |
| alpha_s, n_f = 5 fixed, 2 loop | mu=1.5 GeV | 0.323834602566858 | 0.32383460160559 | 9.61e-10 | 5.62e-08 | pass | integrators | 7.15e-14 | 9.61e-10 |
| alpha_s, n_f = 5 fixed, 2 loop | mu=5 GeV | 0.212300369140568 | 0.212300368822758 | 3.18e-10 | 1.48e-08 | pass | integrators | 1.90e-14 | 3.18e-10 |
| alpha_s, n_f = 5 fixed, 2 loop | mu=30 GeV | 0.14188976976487 | 0.141889769726773 | 3.81e-11 | 3.67e-09 | pass | integrators | 2.12e-15 | 3.81e-11 |
| alpha_s, n_f = 5 fixed, 2 loop | mu=300 GeV | 0.100090585097425 | 0.100090585083201 | 1.42e-11 | 2.51e-09 | pass | integrators | 3.51e-16 | 1.42e-11 |
| alpha_s, n_f = 5 fixed, 2 loop | mu=3000 GeV | 0.0775219275532932 | 0.0775219274754634 | 7.78e-11 | 3.46e-09 | pass | integrators | 7.19e-16 | 7.78e-11 |
| alpha_s, n_f = 5 fixed, 3 loop | mu=1.5 GeV | 0.326967533498072 | 0.326967532539891 | 9.58e-10 | 5.81e-08 | pass | integrators | 7.41e-14 | 9.58e-10 |
| alpha_s, n_f = 5 fixed, 3 loop | mu=5 GeV | 0.212909980428061 | 0.212909980114387 | 3.14e-10 | 1.60e-08 | pass | integrators | 1.95e-14 | 3.14e-10 |
| alpha_s, n_f = 5 fixed, 3 loop | mu=30 GeV | 0.141958454007626 | 0.141958453969704 | 3.79e-11 | 3.68e-09 | pass | integrators | 2.16e-15 | 3.79e-11 |
| alpha_s, n_f = 5 fixed, 3 loop | mu=300 GeV | 0.100065000790002 | 0.10006500077625 | 1.38e-11 | 2.51e-09 | pass | integrators | 3.39e-16 | 1.38e-11 |
| alpha_s, n_f = 5 fixed, 3 loop | mu=3000 GeV | 0.0774872553737186 | 0.0774872553017588 | 7.20e-11 | 3.46e-09 | pass | integrators | 7.32e-16 | 7.20e-11 |
| alpha_s, n_f = 5 fixed, 4 loop | mu=1.5 GeV | 0.328467198409137 | 0.32846719744614 | 9.63e-10 | 5.92e-08 | pass | integrators | 7.64e-14 | 9.63e-10 |
| alpha_s, n_f = 5 fixed, 4 loop | mu=5 GeV | 0.213124921420158 | 0.213124921108349 | 3.12e-10 | 1.60e-08 | pass | integrators | 1.96e-14 | 3.12e-10 |
| alpha_s, n_f = 5 fixed, 4 loop | mu=30 GeV | 0.141977424634347 | 0.141977424596435 | 3.79e-11 | 3.68e-09 | pass | integrators | 2.15e-15 | 3.79e-11 |
| alpha_s, n_f = 5 fixed, 4 loop | mu=300 GeV | 0.100059084071637 | 0.100059084058015 | 1.36e-11 | 2.51e-09 | pass | integrators | 3.30e-16 | 1.36e-11 |
| alpha_s, n_f = 5 fixed, 4 loop | mu=3000 GeV | 0.0774800779744486 | 0.0774800779041042 | 7.03e-11 | 3.46e-09 | pass | integrators | 7.21e-16 | 7.03e-11 |
| alpha_s, n_f = 6 fixed, 1 loop | mu=1.5 GeV | 0.256507575571871 | 0.256507574925616 | 6.46e-10 | 2.53e-08 | pass | integrators | 3.30e-14 | 6.46e-10 |
| alpha_s, n_f = 6 fixed, 1 loop | mu=5 GeV | 0.190845234294638 | 0.190845234018796 | 2.76e-10 | 1.07e-08 | pass | integrators | 1.15e-14 | 2.76e-10 |
| alpha_s, n_f = 6 fixed, 1 loop | mu=30 GeV | 0.13819752632427 | 0.138197526285746 | 3.85e-11 | 3.45e-09 | pass | integrators | 1.92e-15 | 3.85e-11 |
| alpha_s, n_f = 6 fixed, 1 loop | mu=300 GeV | 0.10202734320109 | 0.102027343180749 | 2.03e-11 | 2.51e-09 | pass | integrators | 3.69e-16 | 2.03e-11 |
| alpha_s, n_f = 6 fixed, 1 loop | mu=3000 GeV | 0.0808631741078032 | 0.0808631739940558 | 1.14e-10 | 3.14e-09 | pass | integrators | 7.04e-16 | 1.14e-10 |
| alpha_s, n_f = 6 fixed, 2 loop | mu=1.5 GeV | 0.272968022178344 | 0.272968021511854 | 6.66e-10 | 3.34e-08 | pass | integrators | 4.24e-14 | 6.67e-10 |
| alpha_s, n_f = 6 fixed, 2 loop | mu=5 GeV | 0.196230444779174 | 0.196230444528582 | 2.51e-10 | 1.16e-08 | pass | integrators | 1.43e-14 | 2.51e-10 |
| alpha_s, n_f = 6 fixed, 2 loop | mu=30 GeV | 0.139098016092488 | 0.139098016059169 | 3.33e-11 | 3.51e-09 | pass | integrators | 2.01e-15 | 3.33e-11 |
| alpha_s, n_f = 6 fixed, 2 loop | mu=300 GeV | 0.101582813832565 | 0.101582813817761 | 1.48e-11 | 2.51e-09 | pass | integrators | 3.58e-16 | 1.48e-11 |
| alpha_s, n_f = 6 fixed, 2 loop | mu=3000 GeV | 0.0801429443395401 | 0.0801429442498018 | 8.97e-11 | 3.14e-09 | pass | integrators | 6.61e-16 | 8.97e-11 |
| alpha_s, n_f = 6 fixed, 3 loop | mu=1.5 GeV | 0.272640681845127 | 0.272640681176651 | 6.68e-10 | 3.32e-08 | pass | integrators | 4.21e-14 | 6.69e-10 |
| alpha_s, n_f = 6 fixed, 3 loop | mu=5 GeV | 0.196144931840556 | 0.196144931589309 | 2.51e-10 | 1.15e-08 | pass | integrators | 1.42e-14 | 2.51e-10 |
| alpha_s, n_f = 6 fixed, 3 loop | mu=30 GeV | 0.139086420592224 | 0.139086420558776 | 3.34e-11 | 3.51e-09 | pass | integrators | 2.00e-15 | 3.34e-11 |
| alpha_s, n_f = 6 fixed, 3 loop | mu=300 GeV | 0.101587627300035 | 0.101587627285119 | 1.49e-11 | 2.51e-09 | pass | integrators | 3.31e-16 | 1.49e-11 |
| alpha_s, n_f = 6 fixed, 3 loop | mu=3000 GeV | 0.0801498536507725 | 0.0801498535614303 | 8.93e-11 | 3.14e-09 | pass | integrators | 6.41e-16 | 8.93e-11 |
| alpha_s, n_f = 6 fixed, 4 loop | mu=1.5 GeV | 0.27302598762863 | 0.273025986961762 | 6.67e-10 | 3.34e-08 | pass | integrators | 4.28e-14 | 6.67e-10 |
| alpha_s, n_f = 6 fixed, 4 loop | mu=5 GeV | 0.196226108154955 | 0.196226107904192 | 2.51e-10 | 1.16e-08 | pass | integrators | 1.43e-14 | 2.51e-10 |
| alpha_s, n_f = 6 fixed, 4 loop | mu=30 GeV | 0.139095441951403 | 0.139095441918067 | 3.33e-11 | 3.51e-09 | pass | integrators | 1.99e-15 | 3.33e-11 |
| alpha_s, n_f = 6 fixed, 4 loop | mu=300 GeV | 0.101584428418409 | 0.101584428403587 | 1.48e-11 | 2.51e-09 | pass | integrators | 3.61e-16 | 1.48e-11 |
| alpha_s, n_f = 6 fixed, 4 loop | mu=3000 GeV | 0.0801457124376946 | 0.0801457123478548 | 8.98e-11 | 3.14e-09 | pass | integrators | 6.51e-16 | 8.98e-11 |
| alpha_s with thresholds, 1 loop | mu=1.3 GeV | 0.316045994398061 | 0.316045993375464 | 1.02e-09 | 3.99e-08 | pass | integrators | 5.48e-14 | 1.02e-09 |
| alpha_s with thresholds, 1 loop | mu=1.77686 GeV | 0.279443530429531 | 0.279443529672544 | 7.57e-10 | 3.01e-08 | pass | integrators | 3.83e-14 | 7.57e-10 |
| alpha_s with thresholds, 1 loop | mu=2 GeV | 0.267706079476396 | 0.267706078805553 | 6.71e-10 | 2.72e-08 | pass | integrators | 3.36e-14 | 6.71e-10 |
| alpha_s with thresholds, 1 loop | mu=3 GeV | 0.234016398518602 | 0.234016398051783 | 4.67e-10 | 2.00e-08 | pass | integrators | 2.27e-14 | 4.67e-10 |
| alpha_s with thresholds, 1 loop | mu=4.18299582 GeV | 0.212130269229627 | 0.212136177553047 | 5.91e-06 | 1.45e-08 | xfail | integrators | 1.80e-14 | 5.91e-06 |
| alpha_s with thresholds, 1 loop | mu=4.18300418 GeV | 0.212130154640035 | 0.212130154269996 | 3.70e-10 | 1.42e-08 | pass | integrators | 1.80e-14 | 3.70e-10 |
| alpha_s with thresholds, 1 loop | mu=10 GeV | 0.173083796568402 | 0.173083796393387 | 1.75e-10 | 7.44e-09 | pass | integrators | 8.01e-15 | 1.75e-10 |
| alpha_s with thresholds, 1 loop | mu=162.500162 GeV | 0.10893784150117 | 0.10893653260275 | 1.31e-06 | 2.51e-09 | xfail | integrators | 2.13e-16 | 1.31e-06 |
| alpha_s with thresholds, 1 loop | mu=500 GeV | 0.0958616637828821 | 0.0958616637622127 | 2.07e-11 | 4.22e-09 | pass | integrators | 4.24e-16 | 2.07e-11 |
| alpha_s with thresholds, 1 loop | mu=5000 GeV | 0.0769409901808132 | 0.076940990072024 | 1.09e-10 | 4.24e-09 | pass | integrators | 6.37e-16 | 1.09e-10 |
| alpha_s with thresholds, 2 loop | mu=1.3 GeV | 0.369257956096251 | 0.369257954838571 | 1.26e-09 | 6.39e-08 | pass | integrators | 9.53e-14 | 1.26e-09 |
| alpha_s with thresholds, 2 loop | mu=1.77686 GeV | 0.313324282301956 | 0.313324281451789 | 8.50e-10 | 4.30e-08 | pass | integrators | 5.95e-14 | 8.50e-10 |
| alpha_s with thresholds, 2 loop | mu=2 GeV | 0.296566735923638 | 0.296566735181163 | 7.42e-10 | 3.77e-08 | pass | integrators | 5.06e-14 | 7.43e-10 |
| alpha_s with thresholds, 2 loop | mu=3 GeV | 0.251159747634234 | 0.251159747152108 | 4.82e-10 | 2.53e-08 | pass | integrators | 3.13e-14 | 4.82e-10 |
| alpha_s with thresholds, 2 loop | mu=4.18299582 GeV | 0.223534498740789 | 0.223541778441356 | 7.28e-06 | 1.79e-08 | xfail | integrators | 2.32e-14 | 7.28e-06 |
| alpha_s with thresholds, 2 loop | mu=4.18300418 GeV | 0.223534358767543 | 0.223534358405962 | 3.62e-10 | 1.76e-08 | pass | integrators | 2.32e-14 | 3.62e-10 |
| alpha_s with thresholds, 2 loop | mu=10 GeV | 0.177874463522045 | 0.177874463349943 | 1.72e-10 | 8.77e-09 | pass | integrators | 9.40e-15 | 1.72e-10 |
| alpha_s with thresholds, 2 loop | mu=162.500162 GeV | 0.108559247052133 | 0.108557905528627 | 1.34e-06 | 2.51e-09 | xfail | integrators | 2.12e-16 | 1.34e-06 |
| alpha_s with thresholds, 2 loop | mu=500 GeV | 0.0952261833624621 | 0.0952261833467643 | 1.57e-11 | 4.20e-09 | pass | integrators | 4.71e-16 | 1.57e-11 |
| alpha_s with thresholds, 2 loop | mu=5000 GeV | 0.0761555639943178 | 0.0761555639255486 | 6.88e-11 | 4.21e-09 | pass | integrators | 6.72e-16 | 6.88e-11 |
| alpha_s with thresholds, 3 loop | mu=1.3 GeV | 0.377818439345655 | 0.37781843802666 | 1.32e-09 | 6.98e-08 | pass | integrators | 1.04e-13 | 1.32e-09 |
| alpha_s with thresholds, 3 loop | mu=1.77686 GeV | 0.317779163201443 | 0.317779162333585 | 8.68e-10 | 4.51e-08 | pass | integrators | 6.49e-14 | 8.68e-10 |
| alpha_s with thresholds, 3 loop | mu=2 GeV | 0.300110469559571 | 0.30011046880587 | 7.54e-10 | 3.92e-08 | pass | integrators | 5.56e-14 | 7.54e-10 |
| alpha_s with thresholds, 3 loop | mu=3 GeV | 0.252846955391532 | 0.25284695490595 | 4.86e-10 | 2.59e-08 | pass | integrators | 3.25e-14 | 4.86e-10 |
| alpha_s with thresholds, 3 loop | mu=4.18299582 GeV | 0.224466203774213 | 0.224473650250483 | 7.45e-06 | 1.82e-08 | xfail | integrators | 2.37e-14 | 7.45e-06 |
| alpha_s with thresholds, 3 loop | mu=4.18300418 GeV | 0.224291399078731 | 0.224291398716651 | 3.62e-10 | 1.78e-08 | pass | integrators | 2.37e-14 | 3.62e-10 |
| alpha_s with thresholds, 3 loop | mu=10 GeV | 0.178145514516604 | 0.178145514347827 | 1.69e-10 | 8.82e-09 | pass | integrators | 1.00e-14 | 1.69e-10 |
| alpha_s with thresholds, 3 loop | mu=162.500162 GeV | 0.108523582528429 | 0.108522242349686 | 1.34e-06 | 2.51e-09 | xfail | integrators | 2.24e-16 | 1.34e-06 |
| alpha_s with thresholds, 3 loop | mu=500 GeV | 0.0952022853856199 | 0.0952022853698189 | 1.58e-11 | 4.20e-09 | pass | integrators | 4.85e-16 | 1.58e-11 |
| alpha_s with thresholds, 3 loop | mu=5000 GeV | 0.07614352291841 | 0.0761435228486554 | 6.98e-11 | 4.21e-09 | pass | integrators | 6.96e-16 | 6.98e-11 |
| alpha_s with thresholds, 4 loop | mu=1.3 GeV | 0.381752672544161 | 0.381752671183174 | 1.36e-09 | 7.28e-08 | pass | integrators | 1.12e-13 | 1.36e-09 |
| alpha_s with thresholds, 4 loop | mu=1.77686 GeV | 0.319595464098802 | 0.31959546321095 | 8.88e-10 | 4.61e-08 | pass | integrators | 6.76e-14 | 8.88e-10 |
| alpha_s with thresholds, 4 loop | mu=2 GeV | 0.301506864946077 | 0.301506864179522 | 7.67e-10 | 3.99e-08 | pass | integrators | 5.69e-14 | 7.67e-10 |
| alpha_s with thresholds, 4 loop | mu=3 GeV | 0.253459805534335 | 0.25345980504376 | 4.91e-10 | 2.61e-08 | pass | integrators | 3.30e-14 | 4.91e-10 |
| alpha_s with thresholds, 4 loop | mu=4.18299582 GeV | 0.22479507654057 | 0.224802582851388 | 7.51e-06 | 1.83e-08 | xfail | integrators | 2.40e-14 | 7.51e-06 |
| alpha_s with thresholds, 4 loop | mu=4.18300418 GeV | 0.224567666611044 | 0.224567666246274 | 3.65e-10 | 1.79e-08 | pass | integrators | 2.40e-14 | 3.65e-10 |
| alpha_s with thresholds, 4 loop | mu=10 GeV | 0.178230914006553 | 0.17823091383881 | 1.68e-10 | 8.83e-09 | pass | integrators | 1.04e-14 | 1.68e-10 |
| alpha_s with thresholds, 4 loop | mu=162.500162 GeV | 0.108517313853347 | 0.108515973536381 | 1.34e-06 | 2.51e-09 | xfail | integrators | 2.01e-16 | 1.34e-06 |
| alpha_s with thresholds, 4 loop | mu=500 GeV | 0.0951953584858335 | 0.0951953584701032 | 1.57e-11 | 4.20e-09 | pass | integrators | 4.69e-16 | 1.57e-11 |
| alpha_s with thresholds, 4 loop | mu=5000 GeV | 0.0761374773620183 | 0.0761374772930913 | 6.89e-11 | 4.21e-09 | pass | integrators | 6.70e-16 | 6.89e-11 |
| decoupling down, 1 loop | n_l=3, alpha=0.1 | 0.1 | 0.1 | 0.00e+00 | 3.55e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 1 loop | n_l=3, alpha=0.1 | 0.1 | 0.1 | 0.00e+00 | 3.55e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 1 loop | n_l=3, alpha=0.2 | 0.2 | 0.2 | 0.00e+00 | 7.11e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 1 loop | n_l=3, alpha=0.2 | 0.2 | 0.2 | 0.00e+00 | 7.11e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 1 loop | n_l=3, alpha=0.3 | 0.3 | 0.3 | 0.00e+00 | 1.07e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 1 loop | n_l=3, alpha=0.3 | 0.3 | 0.3 | 0.00e+00 | 1.07e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 1 loop | n_l=3, alpha=0.4 | 0.4 | 0.4 | 0.00e+00 | 1.43e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 1 loop | n_l=3, alpha=0.4 | 0.4 | 0.4 | 0.00e+00 | 1.43e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 1 loop | n_l=4, alpha=0.1 | 0.1 | 0.1 | 0.00e+00 | 3.55e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 1 loop | n_l=4, alpha=0.1 | 0.1 | 0.1 | 0.00e+00 | 3.55e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 1 loop | n_l=4, alpha=0.2 | 0.2 | 0.2 | 0.00e+00 | 7.11e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 1 loop | n_l=4, alpha=0.2 | 0.2 | 0.2 | 0.00e+00 | 7.11e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 1 loop | n_l=4, alpha=0.3 | 0.3 | 0.3 | 0.00e+00 | 1.07e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 1 loop | n_l=4, alpha=0.3 | 0.3 | 0.3 | 0.00e+00 | 1.07e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 1 loop | n_l=4, alpha=0.4 | 0.4 | 0.4 | 0.00e+00 | 1.43e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 1 loop | n_l=4, alpha=0.4 | 0.4 | 0.4 | 0.00e+00 | 1.43e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 1 loop | n_l=5, alpha=0.1 | 0.1 | 0.1 | 0.00e+00 | 3.55e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 1 loop | n_l=5, alpha=0.1 | 0.1 | 0.1 | 0.00e+00 | 3.55e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 1 loop | n_l=5, alpha=0.2 | 0.2 | 0.2 | 0.00e+00 | 7.11e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 1 loop | n_l=5, alpha=0.2 | 0.2 | 0.2 | 0.00e+00 | 7.11e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 1 loop | n_l=5, alpha=0.3 | 0.3 | 0.3 | 0.00e+00 | 1.07e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 1 loop | n_l=5, alpha=0.3 | 0.3 | 0.3 | 0.00e+00 | 1.07e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 1 loop | n_l=5, alpha=0.4 | 0.4 | 0.4 | 0.00e+00 | 1.43e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 1 loop | n_l=5, alpha=0.4 | 0.4 | 0.4 | 0.00e+00 | 1.43e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 2 loop | n_l=3, alpha=0.1 | 0.1 | 0.1 | 0.00e+00 | 3.55e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 2 loop | n_l=3, alpha=0.1 | 0.1 | 0.1 | 0.00e+00 | 3.55e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 2 loop | n_l=3, alpha=0.2 | 0.2 | 0.2 | 0.00e+00 | 7.11e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 2 loop | n_l=3, alpha=0.2 | 0.2 | 0.2 | 0.00e+00 | 7.11e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 2 loop | n_l=3, alpha=0.3 | 0.3 | 0.3 | 0.00e+00 | 1.07e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 2 loop | n_l=3, alpha=0.3 | 0.3 | 0.3 | 0.00e+00 | 1.07e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 2 loop | n_l=3, alpha=0.4 | 0.4 | 0.4 | 0.00e+00 | 1.43e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 2 loop | n_l=3, alpha=0.4 | 0.4 | 0.4 | 0.00e+00 | 1.43e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 2 loop | n_l=4, alpha=0.1 | 0.1 | 0.1 | 0.00e+00 | 3.55e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 2 loop | n_l=4, alpha=0.1 | 0.1 | 0.1 | 0.00e+00 | 3.55e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 2 loop | n_l=4, alpha=0.2 | 0.2 | 0.2 | 0.00e+00 | 7.11e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 2 loop | n_l=4, alpha=0.2 | 0.2 | 0.2 | 0.00e+00 | 7.11e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 2 loop | n_l=4, alpha=0.3 | 0.3 | 0.3 | 0.00e+00 | 1.07e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 2 loop | n_l=4, alpha=0.3 | 0.3 | 0.3 | 0.00e+00 | 1.07e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 2 loop | n_l=4, alpha=0.4 | 0.4 | 0.4 | 0.00e+00 | 1.43e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 2 loop | n_l=4, alpha=0.4 | 0.4 | 0.4 | 0.00e+00 | 1.43e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 2 loop | n_l=5, alpha=0.1 | 0.1 | 0.1 | 0.00e+00 | 3.55e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 2 loop | n_l=5, alpha=0.1 | 0.1 | 0.1 | 0.00e+00 | 3.55e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 2 loop | n_l=5, alpha=0.2 | 0.2 | 0.2 | 0.00e+00 | 7.11e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 2 loop | n_l=5, alpha=0.2 | 0.2 | 0.2 | 0.00e+00 | 7.11e-16 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 2 loop | n_l=5, alpha=0.3 | 0.3 | 0.3 | 0.00e+00 | 1.07e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 2 loop | n_l=5, alpha=0.3 | 0.3 | 0.3 | 0.00e+00 | 1.07e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 2 loop | n_l=5, alpha=0.4 | 0.4 | 0.4 | 0.00e+00 | 1.43e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling up, 2 loop | n_l=5, alpha=0.4 | 0.4 | 0.4 | 0.00e+00 | 1.43e-15 | pass | decoupling | 0.00e+00 | 0.00e+00 |
| decoupling down, 3 loop | n_l=3, alpha=0.1 | 0.100015479625279 | 0.100015479625279 | 0.00e+00 | 3.55e-16 | pass | decoupling | 1.56e-17 | 1.56e-17 |
| decoupling up, 3 loop | n_l=3, alpha=0.1 | 0.0999845203747213 | 0.0999845203747213 | 0.00e+00 | 3.55e-16 | pass | decoupling | 1.76e-18 | 1.76e-18 |
| decoupling down, 3 loop | n_l=3, alpha=0.2 | 0.20012383700223 | 0.20012383700223 | 0.00e+00 | 7.11e-16 | pass | decoupling | 1.37e-17 | 1.37e-17 |
| decoupling up, 3 loop | n_l=3, alpha=0.2 | 0.19987616299777 | 0.19987616299777 | 0.00e+00 | 7.11e-16 | pass | decoupling | 1.37e-17 | 1.37e-17 |
| decoupling down, 3 loop | n_l=3, alpha=0.3 | 0.300417949882525 | 0.300417949882525 | 0.00e+00 | 1.07e-15 | pass | decoupling | 5.77e-18 | 5.77e-18 |
| decoupling up, 3 loop | n_l=3, alpha=0.3 | 0.299582050117475 | 0.299582050117475 | 0.00e+00 | 1.07e-15 | pass | decoupling | 5.77e-18 | 5.77e-18 |
| decoupling down, 3 loop | n_l=3, alpha=0.4 | 0.400990696017836 | 0.400990696017836 | 0.00e+00 | 1.43e-15 | pass | decoupling | 1.61e-18 | 1.61e-18 |
| decoupling up, 3 loop | n_l=3, alpha=0.4 | 0.399009303982164 | 0.399009303982164 | 0.00e+00 | 1.43e-15 | pass | decoupling | 1.61e-18 | 1.61e-18 |
| decoupling down, 3 loop | n_l=4, alpha=0.1 | 0.100015479625279 | 0.100015479625279 | 0.00e+00 | 3.55e-16 | pass | decoupling | 1.56e-17 | 1.56e-17 |
| decoupling up, 3 loop | n_l=4, alpha=0.1 | 0.0999845203747213 | 0.0999845203747213 | 0.00e+00 | 3.55e-16 | pass | decoupling | 1.76e-18 | 1.76e-18 |
| decoupling down, 3 loop | n_l=4, alpha=0.2 | 0.20012383700223 | 0.20012383700223 | 0.00e+00 | 7.11e-16 | pass | decoupling | 1.37e-17 | 1.37e-17 |
| decoupling up, 3 loop | n_l=4, alpha=0.2 | 0.19987616299777 | 0.19987616299777 | 0.00e+00 | 7.11e-16 | pass | decoupling | 1.37e-17 | 1.37e-17 |
| decoupling down, 3 loop | n_l=4, alpha=0.3 | 0.300417949882525 | 0.300417949882525 | 0.00e+00 | 1.07e-15 | pass | decoupling | 5.77e-18 | 5.77e-18 |
| decoupling up, 3 loop | n_l=4, alpha=0.3 | 0.299582050117475 | 0.299582050117475 | 0.00e+00 | 1.07e-15 | pass | decoupling | 5.77e-18 | 5.77e-18 |
| decoupling down, 3 loop | n_l=4, alpha=0.4 | 0.400990696017836 | 0.400990696017836 | 0.00e+00 | 1.43e-15 | pass | decoupling | 1.61e-18 | 1.61e-18 |
| decoupling up, 3 loop | n_l=4, alpha=0.4 | 0.399009303982164 | 0.399009303982164 | 0.00e+00 | 1.43e-15 | pass | decoupling | 1.61e-18 | 1.61e-18 |
| decoupling down, 3 loop | n_l=5, alpha=0.1 | 0.100015479625279 | 0.100015479625279 | 0.00e+00 | 3.55e-16 | pass | decoupling | 1.56e-17 | 1.56e-17 |
| decoupling up, 3 loop | n_l=5, alpha=0.1 | 0.0999845203747213 | 0.0999845203747213 | 0.00e+00 | 3.55e-16 | pass | decoupling | 1.76e-18 | 1.76e-18 |
| decoupling down, 3 loop | n_l=5, alpha=0.2 | 0.20012383700223 | 0.20012383700223 | 0.00e+00 | 7.11e-16 | pass | decoupling | 1.37e-17 | 1.37e-17 |
| decoupling up, 3 loop | n_l=5, alpha=0.2 | 0.19987616299777 | 0.19987616299777 | 0.00e+00 | 7.11e-16 | pass | decoupling | 1.37e-17 | 1.37e-17 |
| decoupling down, 3 loop | n_l=5, alpha=0.3 | 0.300417949882525 | 0.300417949882525 | 0.00e+00 | 1.07e-15 | pass | decoupling | 5.77e-18 | 5.77e-18 |
| decoupling up, 3 loop | n_l=5, alpha=0.3 | 0.299582050117475 | 0.299582050117475 | 0.00e+00 | 1.07e-15 | pass | decoupling | 5.77e-18 | 5.77e-18 |
| decoupling down, 3 loop | n_l=5, alpha=0.4 | 0.400990696017836 | 0.400990696017836 | 0.00e+00 | 1.43e-15 | pass | decoupling | 1.61e-18 | 1.61e-18 |
| decoupling up, 3 loop | n_l=5, alpha=0.4 | 0.399009303982164 | 0.399009303982164 | 0.00e+00 | 1.43e-15 | pass | decoupling | 1.61e-18 | 1.61e-18 |
| decoupling down, 4 loop | n_l=3, alpha=0.1 | 0.100017795615098 | 0.100017795615098 | 0.00e+00 | 3.55e-16 | pass | decoupling | 2.46e-17 | 2.46e-17 |
| decoupling up, 4 loop | n_l=3, alpha=0.1 | 0.0999822043849018 | 0.0999822043849018 | 0.00e+00 | 3.55e-16 | pass | decoupling | 3.11e-18 | 3.11e-18 |
| decoupling down, 4 loop | n_l=3, alpha=0.2 | 0.200160892839341 | 0.200160892839341 | 0.00e+00 | 7.11e-16 | pass | decoupling | 8.26e-18 | 8.26e-18 |
| decoupling up, 4 loop | n_l=3, alpha=0.2 | 0.199839107160659 | 0.199839107160659 | 0.00e+00 | 7.11e-16 | pass | decoupling | 8.26e-18 | 8.26e-18 |
| decoupling down, 4 loop | n_l=3, alpha=0.3 | 0.300605545057903 | 0.300605545057903 | 0.00e+00 | 1.07e-15 | pass | decoupling | 1.40e-17 | 1.40e-17 |
| decoupling up, 4 loop | n_l=3, alpha=0.3 | 0.299394454942097 | 0.299394454942097 | 0.00e+00 | 1.07e-15 | pass | decoupling | 1.40e-17 | 1.40e-17 |
| decoupling down, 4 loop | n_l=3, alpha=0.4 | 0.401583589411625 | 0.401583589411625 | 0.00e+00 | 1.43e-15 | pass | decoupling | 3.28e-17 | 3.28e-17 |
| decoupling up, 4 loop | n_l=3, alpha=0.4 | 0.398416410588375 | 0.398416410588375 | 0.00e+00 | 1.43e-15 | pass | decoupling | 2.27e-17 | 2.27e-17 |
| decoupling down, 4 loop | n_l=4, alpha=0.1 | 0.100017522601048 | 0.100017522601048 | 0.00e+00 | 3.55e-16 | pass | decoupling | 6.94e-18 | 6.94e-18 |
| decoupling up, 4 loop | n_l=4, alpha=0.1 | 0.099982477398952 | 0.099982477398952 | 0.00e+00 | 3.55e-16 | pass | decoupling | 6.94e-18 | 6.94e-18 |
| decoupling down, 4 loop | n_l=4, alpha=0.2 | 0.200156524614539 | 0.200156524614539 | 0.00e+00 | 7.11e-16 | pass | decoupling | 1.41e-17 | 1.41e-17 |
| decoupling up, 4 loop | n_l=4, alpha=0.2 | 0.199843475385461 | 0.199843475385461 | 0.00e+00 | 7.11e-16 | pass | decoupling | 1.41e-17 | 1.41e-17 |
| decoupling down, 4 loop | n_l=4, alpha=0.3 | 0.30058343091984 | 0.30058343091984 | 0.00e+00 | 1.07e-15 | pass | decoupling | 2.28e-17 | 2.28e-17 |
| decoupling up, 4 loop | n_l=4, alpha=0.3 | 0.29941656908016 | 0.29941656908016 | 0.00e+00 | 1.07e-15 | pass | decoupling | 2.28e-17 | 2.28e-17 |
| decoupling down, 4 loop | n_l=4, alpha=0.4 | 0.401513697814784 | 0.401513697814784 | 0.00e+00 | 1.43e-15 | pass | decoupling | 4.79e-18 | 4.79e-18 |
| decoupling up, 4 loop | n_l=4, alpha=0.4 | 0.398486302185217 | 0.398486302185217 | 0.00e+00 | 1.43e-15 | pass | decoupling | 4.79e-18 | 4.79e-18 |
| decoupling down, 4 loop | n_l=5, alpha=0.1 | 0.100017249586998 | 0.100017249586998 | 0.00e+00 | 3.55e-16 | pass | decoupling | 3.11e-18 | 3.11e-18 |
| decoupling up, 4 loop | n_l=5, alpha=0.1 | 0.0999827504130021 | 0.0999827504130021 | 0.00e+00 | 3.55e-16 | pass | decoupling | 1.08e-17 | 1.08e-17 |
| decoupling down, 4 loop | n_l=5, alpha=0.2 | 0.200152156389736 | 0.200152156389736 | 0.00e+00 | 7.11e-16 | pass | decoupling | 7.86e-18 | 7.86e-18 |
| decoupling up, 4 loop | n_l=5, alpha=0.2 | 0.199847843610264 | 0.199847843610264 | 0.00e+00 | 7.11e-16 | pass | decoupling | 1.99e-17 | 1.99e-17 |
| decoupling down, 4 loop | n_l=5, alpha=0.3 | 0.300561316781777 | 0.300561316781777 | 0.00e+00 | 1.07e-15 | pass | decoupling | 2.40e-17 | 2.40e-17 |
| decoupling up, 4 loop | n_l=5, alpha=0.3 | 0.299438683218223 | 0.299438683218223 | 0.00e+00 | 1.07e-15 | pass | decoupling | 2.40e-17 | 2.40e-17 |
| decoupling down, 4 loop | n_l=5, alpha=0.4 | 0.401443806217942 | 0.401443806217942 | 0.00e+00 | 1.43e-15 | pass | decoupling | 1.32e-17 | 1.32e-17 |
| decoupling up, 4 loop | n_l=5, alpha=0.4 | 0.398556193782058 | 0.398556193782058 | 0.00e+00 | 1.43e-15 | pass | decoupling | 4.24e-17 | 4.24e-17 |

## KerrGeoPy (`test_ext_kerr_kerrgeopy.py`)

| quantity | inputs | engine | library | diff | tol | status | basis | eng err | lib err |
|---|---|---|---|---|---|---|---|---|---|
| ISCO r_isco (prograde) | chi=0.0 | 6 | 6 | 0.00e+00 | 1.48e-07 | pass | brentq + noise | 0.00e+00 | 0.00e+00 |
| marginally bound r_mb (prograde) | chi=0.0 | 4 | 4 | 0.00e+00 | 1.22e-15 | pass | brentq + noise | 0.00e+00 | 0.00e+00 |
| ISCO r_isco (retrograde) | chi=0.0 | 6 | 6 | 0.00e+00 | 1.48e-07 | pass | brentq + noise | 0.00e+00 | 0.00e+00 |
| marginally bound r_mb (retrograde) | chi=0.0 | 4 | 4 | 0.00e+00 | 1.22e-15 | pass | brentq + noise | 0.00e+00 | 0.00e+00 |
| ISCO r_isco (prograde) | chi=0.1 | 5.66930257120865 | 5.66930257120864 | 1.24e-14 | 2.04e-12 | pass | brentq + noise | 5.45e-15 | 6.98e-15 |
| marginally bound r_mb (prograde) | chi=0.1 | 3.79736659610103 | 3.79736659610103 | 0.00e+00 | 1.01e-12 | pass | brentq + noise | 1.41e-16 | 1.41e-16 |
| ISCO r_isco (retrograde) | chi=0.1 | 6.32289472378945 | 6.32289472378922 | 2.23e-13 | 2.04e-12 | pass | brentq + noise | 4.69e-15 | 2.28e-13 |
| marginally bound r_mb (retrograde) | chi=0.1 | 4.1976176963403 | 4.19761769634028 | 2.04e-14 | 1.01e-12 | pass | brentq + noise | 6.90e-16 | 1.97e-14 |
| ISCO r_isco (prograde) | chi=0.5 | 4.23300252953083 | 4.23300252953083 | 8.88e-16 | 2.02e-12 | pass | brentq + noise | 5.53e-16 | 3.35e-16 |
| marginally bound r_mb (prograde) | chi=0.5 | 2.91421356237309 | 2.91421356237298 | 1.12e-13 | 1.01e-12 | pass | brentq + noise | 1.25e-16 | 1.12e-13 |
| ISCO r_isco (retrograde) | chi=0.5 | 7.55458471451236 | 7.55458471451236 | 8.88e-16 | 2.02e-12 | pass | brentq + noise | 5.29e-16 | 3.59e-16 |
| marginally bound r_mb (retrograde) | chi=0.5 | 4.94948974278318 | 4.94948974278318 | 0.00e+00 | 1.01e-12 | pass | brentq + noise | 2.17e-16 | 2.17e-16 |
| ISCO r_isco (prograde) | chi=0.9 | 2.32088304176189 | 2.32088304176189 | 0.00e+00 | 2.02e-12 | pass | brentq + noise | 7.86e-18 | 7.86e-18 |
| marginally bound r_mb (prograde) | chi=0.9 | 1.73245553203368 | 1.73245553203368 | 8.88e-15 | 1.01e-12 | pass | brentq + noise | 8.62e-17 | 8.97e-15 |
| ISCO r_isco (retrograde) | chi=0.9 | 8.71735227960649 | 8.71735227960649 | 0.00e+00 | 2.02e-12 | pass | brentq + noise | 3.16e-16 | 3.16e-16 |
| marginally bound r_mb (retrograde) | chi=0.9 | 5.65680975041804 | 5.65680975041804 | 0.00e+00 | 1.01e-12 | pass | brentq + noise | 2.67e-16 | 2.67e-16 |
| ISCO r_isco (prograde) | chi=0.99 | 1.45449793805967 | 1.45449793805967 | 0.00e+00 | 2.04e-12 | pass | brentq + noise | 1.55e-16 | 1.55e-16 |
| marginally bound r_mb (prograde) | chi=0.99 | 1.21 | 1.21 | 3.33e-15 | 1.02e-12 | pass | brentq + noise | 8.88e-17 | 3.24e-15 |
| ISCO r_isco (retrograde) | chi=0.99 | 8.97186134254697 | 8.97186134254697 | 1.78e-15 | 2.02e-12 | pass | brentq + noise | 9.79e-16 | 7.97e-16 |
| marginally bound r_mb (retrograde) | chi=0.99 | 5.81134719593318 | 5.81134719593318 | 0.00e+00 | 1.01e-12 | pass | brentq + noise | 3.53e-17 | 3.53e-17 |
| ISCO r_isco (prograde) | chi=0.999 | 1.18176461303357 | 1.18176461303358 | 1.40e-14 | 2.15e-12 | pass | brentq + noise | 4.38e-16 | 1.36e-14 |
| marginally bound r_mb (prograde) | chi=0.999 | 1.06424555320337 | 1.06424555320361 | 2.45e-13 | 1.05e-12 | pass | brentq + noise | 1.71e-16 | 2.45e-13 |
| ISCO r_isco (retrograde) | chi=0.999 | 8.99718736373522 | 8.99718736373522 | 0.00e+00 | 2.02e-12 | pass | brentq + noise | 7.52e-16 | 7.52e-16 |
| marginally bound r_mb (retrograde) | chi=0.999 | 5.82671992955455 | 5.82671992955455 | 0.00e+00 | 1.01e-12 | pass | brentq + noise | 2.96e-16 | 2.96e-16 |
| ISCO r_isco (prograde) | chi=0.9999 | 1.07852643464645 | 1.07852643464642 | 2.73e-14 | 2.64e-12 | pass | brentq + noise | 7.46e-15 | 3.48e-14 |
| marginally bound r_mb (prograde) | chi=0.9999 | 1.0201 | 1.02009999999999 | 1.35e-14 | 1.17e-12 | pass | brentq + noise | 8.88e-18 | 1.35e-14 |
| ISCO r_isco (retrograde) | chi=0.9999 | 8.99971874863766 | 8.99971874863766 | 1.78e-15 | 2.05e-12 | pass | brentq + noise | 1.07e-15 | 7.03e-16 |
| marginally bound r_mb (retrograde) | chi=0.9999 | 5.82825641318417 | 5.82825641318417 | 0.00e+00 | 1.01e-12 | pass | brentq + noise | 2.36e-16 | 2.36e-16 |
| ISCO r_isco (prograde) | chi=0.999999 | 1.01609543819596 | 1.01609543819495 | 1.01e-12 | 1.54e-11 | pass | brentq + noise | 5.99e-14 | 9.50e-13 |
| marginally bound r_mb (prograde) | chi=0.999999 | 1.00200100000003 | 1.00200099999994 | 8.75e-14 | 2.64e-12 | pass | brentq + noise | 8.88e-19 | 8.75e-14 |
| ISCO r_isco (retrograde) | chi=0.999999 | 8.99999718749986 | 8.99999718749986 | 0.00e+00 | 2.61e-12 | pass | brentq + noise | 4.73e-16 | 4.73e-16 |
| marginally bound r_mb (retrograde) | chi=0.999999 | 5.82842541763932 | 5.82842541763932 | 8.88e-16 | 1.01e-12 | pass | brentq + noise | 7.13e-16 | 1.76e-16 |
| ISCO r_isco (prograde) | chi=0.999999999 | 1.00158960683697 | 1.00158960679889 | 3.81e-11 | 1.33e-09 | pass | brentq + noise | 2.65e-13 | 3.78e-11 |
| marginally bound r_mb (prograde) | chi=0.999999999 | 1.00006324655231 | 1.00006324654988 | 2.43e-12 | 5.29e-11 | pass | brentq + noise | 1.74e-16 | 2.43e-12 |
| ISCO r_isco (retrograde) | chi=0.999999999 | 8.9999999971875 | 8.9999999971875 | 0.00e+00 | 6.08e-11 | pass | brentq + noise | 5.34e-16 | 5.34e-16 |
| marginally bound r_mb (retrograde) | chi=0.999999999 | 5.82842712303908 | 5.82842712303908 | 0.00e+00 | 1.01e-12 | pass | brentq + noise | 2.61e-17 | 2.61e-17 |
| ISCO r_isco (prograde) | chi=0.999999999999 | 1.00015876098388 | 1.00015875034304 | 1.06e-08 | 1.33e-07 | pass | brentq + noise | 4.92e-16 | 1.06e-08 |
| marginally bound r_mb (prograde) | chi=0.999999999999 | 1.00000199997888 | 1.00000199993107 | 4.78e-11 | 1.64e-09 | pass | brentq + noise | 1.51e-16 | 4.78e-11 |
| ISCO r_isco (retrograde) | chi=0.999999999999 | 8.99999999999719 | 8.99999999999719 | 0.00e+00 | 5.88e-09 | pass | brentq + noise | 4.65e-16 | 4.65e-16 |
| marginally bound r_mb (retrograde) | chi=0.999999999999 | 5.82842712474448 | 5.82842712474448 | 0.00e+00 | 1.01e-12 | pass | brentq + noise | 2.61e-16 | 2.61e-16 |
| circular orbit E (prograde) | chi=0.0, r=1 r_isco | 0.942809041582181 | 0.942809041582181 | 0.00e+00 | 9.65e-15 | pass | running error | 4.53e-17 | 4.53e-17 |
| circular orbit L (prograde) | chi=0.0, r=1 r_isco | 3.46410161513949 | 3.46410161513949 | 4.44e-16 | 1.64e-13 | pass | running error | 5.88e-16 | 1.44e-16 |
| circular orbit E (prograde) | chi=0.0, r=1.01 r_isco | 0.942820481148675 | 0.942820481148675 | 0.00e+00 | 9.60e-15 | pass | running error | 4.74e-17 | 4.74e-17 |
| circular orbit L (prograde) | chi=0.0, r=1.01 r_isco | 3.46427141987868 | 3.46427141987868 | 2.22e-15 | 1.66e-13 | pass | running error | 7.50e-17 | 2.30e-15 |
| circular orbit E (prograde) | chi=0.0, r=1.5 r_isco | 0.95257934441568 | 0.95257934441568 | 0.00e+00 | 8.57e-15 | pass | running error | 2.02e-18 | 2.02e-18 |
| circular orbit L (prograde) | chi=0.0, r=1.5 r_isco | 3.67423461417477 | 3.67423461417477 | 0.00e+00 | 2.70e-13 | pass | running error | 1.19e-16 | 1.19e-16 |
| circular orbit E (prograde) | chi=0.0, r=3 r_isco | 0.973728991120295 | 0.973728991120295 | 0.00e+00 | 7.99e-15 | pass | running error | 4.62e-18 | 4.62e-18 |
| circular orbit L (prograde) | chi=0.0, r=3 r_isco | 4.6475800154489 | 4.6475800154489 | 2.66e-15 | 7.18e-13 | pass | running error | 1.63e-16 | 2.83e-15 |
| circular orbit E (prograde) | chi=0.0, r=30 r_isco | 0.997234090755008 | 0.997234090755008 | 1.11e-16 | 7.69e-15 | pass | running error | 1.06e-16 | 5.25e-18 |
| circular orbit L (prograde) | chi=0.0, r=30 r_isco | 13.5296285040509 | 13.5296285040509 | 2.31e-14 | 2.19e-11 | pass | running error | 1.39e-15 | 2.17e-14 |
| circular orbit E (prograde) | chi=0.0, r=10000 r_isco | 0.999991666770841 | 0.999991666770841 | 2.22e-16 | 7.66e-15 | pass | running error | 2.37e-17 | 2.46e-16 |
| circular orbit L (prograde) | chi=0.0, r=10000 r_isco | 244.955098232324 | 244.95509823583 | 3.51e-09 | 1.33e-07 | pass | running error | 1.92e-14 | 3.51e-09 |
| circular orbit E (retrograde) | chi=0.0, r=1 r_isco | 0.942809041582181 | 0.942809041582181 | 0.00e+00 | 9.65e-15 | pass | running error | 4.53e-17 | 4.53e-17 |
| circular orbit L (retrograde) | chi=0.0, r=1 r_isco | -3.46410161513949 | -3.46410161513949 | 4.44e-16 | 1.64e-13 | pass | running error | 5.88e-16 | 1.44e-16 |
| circular orbit E (retrograde) | chi=0.0, r=1.01 r_isco | 0.942820481148675 | 0.942820481148675 | 0.00e+00 | 9.60e-15 | pass | running error | 4.74e-17 | 4.74e-17 |
| circular orbit L (retrograde) | chi=0.0, r=1.01 r_isco | -3.46427141987868 | -3.46427141987868 | 2.22e-15 | 1.66e-13 | pass | running error | 7.50e-17 | 2.30e-15 |
| circular orbit E (retrograde) | chi=0.0, r=1.5 r_isco | 0.95257934441568 | 0.95257934441568 | 0.00e+00 | 8.57e-15 | pass | running error | 2.02e-18 | 2.02e-18 |
| circular orbit L (retrograde) | chi=0.0, r=1.5 r_isco | -3.67423461417477 | -3.67423461417477 | 0.00e+00 | 2.70e-13 | pass | running error | 1.19e-16 | 1.19e-16 |
| circular orbit E (retrograde) | chi=0.0, r=3 r_isco | 0.973728991120295 | 0.973728991120295 | 0.00e+00 | 7.99e-15 | pass | running error | 4.62e-18 | 4.62e-18 |
| circular orbit L (retrograde) | chi=0.0, r=3 r_isco | -4.6475800154489 | -4.6475800154489 | 2.66e-15 | 7.18e-13 | pass | running error | 1.63e-16 | 2.83e-15 |
| circular orbit E (retrograde) | chi=0.0, r=30 r_isco | 0.997234090755008 | 0.997234090755008 | 1.11e-16 | 7.69e-15 | pass | running error | 1.06e-16 | 5.25e-18 |
| circular orbit L (retrograde) | chi=0.0, r=30 r_isco | -13.5296285040509 | -13.5296285040509 | 2.31e-14 | 2.19e-11 | pass | running error | 1.39e-15 | 2.17e-14 |
| circular orbit E (retrograde) | chi=0.0, r=10000 r_isco | 0.999991666770841 | 0.999991666770841 | 2.22e-16 | 7.66e-15 | pass | running error | 2.37e-17 | 2.46e-16 |
| circular orbit L (retrograde) | chi=0.0, r=10000 r_isco | -244.955098232324 | -244.95509823583 | 3.51e-09 | 1.33e-07 | pass | running error | 1.92e-14 | 3.51e-09 |
| circular orbit E (prograde) | chi=0.5, r=1 r_isco | 0.917882006660961 | 0.917882006660961 | 1.11e-16 | 1.94e-14 | pass | running error | 1.16e-18 | 1.10e-16 |
| circular orbit L (prograde) | chi=0.5, r=1 r_isco | 2.90286615323708 | 2.90286615323709 | 8.88e-16 | 2.10e-13 | pass | running error | 5.04e-16 | 1.39e-15 |
| circular orbit E (prograde) | chi=0.5, r=1.01 r_isco | 0.917899960922812 | 0.917899960922812 | 1.11e-16 | 1.88e-14 | pass | running error | 3.82e-17 | 7.29e-17 |
| circular orbit L (prograde) | chi=0.5, r=1.01 r_isco | 2.90303305598484 | 2.90303305598484 | 2.66e-15 | 2.06e-13 | pass | running error | 1.44e-16 | 2.52e-15 |
| circular orbit E (prograde) | chi=0.5, r=1.5 r_isco | 0.93247958817787 | 0.93247958817787 | 2.22e-16 | 1.07e-14 | pass | running error | 7.46e-17 | 1.47e-16 |
| circular orbit L (prograde) | chi=0.5, r=1.5 r_isco | 3.09577165951641 | 3.0957716595164 | 2.22e-15 | 2.06e-13 | pass | running error | 9.44e-17 | 2.13e-15 |
| circular orbit E (prograde) | chi=0.5, r=3 r_isco | 0.962852774651725 | 0.962852774651725 | 2.22e-16 | 8.54e-15 | pass | running error | 9.52e-17 | 1.27e-16 |
| circular orbit L (prograde) | chi=0.5, r=3 r_isco | 3.93727820914853 | 3.93727820914852 | 6.66e-15 | 4.57e-13 | pass | running error | 5.69e-16 | 7.23e-15 |
| circular orbit E (prograde) | chi=0.5, r=30 r_isco | 0.996083995852193 | 0.996083995852193 | 1.11e-16 | 7.71e-15 | pass | running error | 1.30e-16 | 1.90e-17 |
| circular orbit L (prograde) | chi=0.5, r=30 r_isco | 11.3926332181233 | 11.3926332181232 | 9.77e-14 | 1.30e-11 | pass | running error | 8.49e-16 | 9.69e-14 |
| circular orbit E (prograde) | chi=0.5, r=10000 r_isco | 0.999988188261312 | 0.999988188261312 | 0.00e+00 | 7.66e-15 | pass | running error | 1.31e-19 | 1.31e-19 |
| circular orbit L (prograde) | chi=0.5, r=10000 r_isco | 205.749874695102 | 205.749874695722 | 6.19e-10 | 7.88e-08 | pass | running error | 1.47e-14 | 6.19e-10 |
| circular orbit E (retrograde) | chi=0.5, r=1 r_isco | 0.954857773047365 | 0.954857773047365 | 1.11e-16 | 9.87e-15 | pass | running error | 6.23e-17 | 1.73e-16 |
| circular orbit L (retrograde) | chi=0.5, r=1 r_isco | -3.8842126320177 | -3.8842126320177 | 4.00e-15 | 2.29e-13 | pass | running error | 7.26e-16 | 4.72e-15 |
| circular orbit E (retrograde) | chi=0.5, r=1.01 r_isco | 0.954866407427762 | 0.954866407427762 | 3.33e-16 | 9.83e-15 | pass | running error | 1.41e-16 | 1.92e-16 |
| circular orbit L (retrograde) | chi=0.5, r=1.01 r_isco | -3.88438939086335 | -3.88438939086335 | 4.88e-15 | 2.32e-13 | pass | running error | 3.09e-16 | 4.58e-15 |
| circular orbit E (retrograde) | chi=0.5, r=1.5 r_isco | 0.962414339933137 | 0.962414339933137 | 1.11e-16 | 8.74e-15 | pass | running error | 8.14e-17 | 2.96e-17 |
| circular orbit L (retrograde) | chi=0.5, r=1.5 r_isco | -4.11031753160017 | -4.11031753160017 | 5.33e-15 | 3.83e-13 | pass | running error | 7.16e-16 | 4.61e-15 |
| circular orbit E (retrograde) | chi=0.5, r=3 r_isco | 0.97910482243811 | 0.97910482243811 | 0.00e+00 | 8.05e-15 | pass | running error | 5.21e-17 | 5.21e-17 |
| circular orbit L (retrograde) | chi=0.5, r=3 r_isco | -5.18855945523801 | -5.18855945523798 | 2.66e-14 | 1.02e-12 | pass | running error | 1.02e-15 | 2.56e-14 |
| circular orbit E (retrograde) | chi=0.5, r=30 r_isco | 0.997801952671535 | 0.997801952671535 | 1.11e-16 | 7.68e-15 | pass | running error | 3.19e-17 | 7.92e-17 |
| circular orbit L (retrograde) | chi=0.5, r=30 r_isco | -15.1618915242423 | -15.161891524243 | 7.51e-13 | 3.10e-11 | pass | running error | 2.68e-15 | 7.49e-13 |
| circular orbit E (retrograde) | chi=0.5, r=10000 r_isco | 0.999993381568536 | 0.999993381568536 | 2.22e-16 | 7.66e-15 | pass | running error | 1.19e-16 | 1.03e-16 |
| circular orbit L (retrograde) | chi=0.5, r=10000 r_isco | -274.861525474671 | -274.861525471474 | 3.20e-09 | 1.88e-07 | pass | running error | 4.17e-14 | 3.20e-09 |
| circular orbit E (prograde) | chi=0.9, r=1 r_isco | 0.844247008005999 | 0.844247008005999 | 1.11e-16 | 1.22e-14 | pass | running error | 3.53e-17 | 1.46e-16 |
| circular orbit L (prograde) | chi=0.9, r=1 r_isco | 2.0997847561259 | 2.0997847561259 | 8.88e-16 | 1.81e-13 | pass | running error | 5.01e-16 | 1.39e-15 |
| circular orbit E (prograde) | chi=0.9, r=1.01 r_isco | 0.844291533406402 | 0.844291533406402 | 2.22e-16 | 1.18e-14 | pass | running error | 6.47e-18 | 2.16e-16 |
| circular orbit L (prograde) | chi=0.9, r=1.01 r_isco | 2.0999838285823 | 2.09998382858229 | 1.33e-15 | 1.68e-13 | pass | running error | 6.82e-16 | 6.50e-16 |
| circular orbit E (prograde) | chi=0.9, r=1.5 r_isco | 0.875202846254368 | 0.875202846254368 | 2.22e-16 | 1.69e-14 | pass | running error | 1.17e-17 | 2.34e-16 |
| circular orbit L (prograde) | chi=0.9, r=1.5 r_isco | 2.28627250250504 | 2.28627250250504 | 4.44e-16 | 1.76e-13 | pass | running error | 5.09e-16 | 9.53e-16 |
| circular orbit E (prograde) | chi=0.9, r=3 r_isco | 0.932631658720136 | 0.932631658720136 | 0.00e+00 | 1.12e-14 | pass | running error | 1.14e-16 | 1.14e-16 |
| circular orbit L (prograde) | chi=0.9, r=3 r_isco | 2.96811454146599 | 2.96811454146599 | 8.88e-16 | 2.52e-13 | pass | running error | 2.40e-16 | 1.13e-15 |
| circular orbit E (prograde) | chi=0.9, r=30 r_isco | 0.992878979827871 | 0.992878979827871 | 1.11e-16 | 7.77e-15 | pass | running error | 1.38e-17 | 1.25e-16 |
| circular orbit L (prograde) | chi=0.9, r=30 r_isco | 8.49130172985571 | 8.49130172985566 | 4.44e-14 | 5.33e-12 | pass | running error | 3.39e-15 | 4.10e-14 |
| circular orbit E (prograde) | chi=0.9, r=10000 r_isco | 0.999978457161172 | 0.999978457161173 | 2.22e-16 | 7.66e-15 | pass | running error | 7.95e-17 | 1.42e-16 |
| circular orbit L (prograde) | chi=0.9, r=10000 r_isco | 152.354177570504 | 152.354177571078 | 5.74e-10 | 3.20e-08 | pass | running error | 1.77e-14 | 5.74e-10 |
| circular orbit E (retrograde) | chi=0.9, r=1 r_isco | 0.961001654354793 | 0.961001654354793 | 1.11e-16 | 1.00e-14 | pass | running error | 1.29e-16 | 1.85e-17 |
| circular orbit L (retrograde) | chi=0.9, r=1 r_isco | -4.16806419633422 | -4.16806419633422 | 2.66e-15 | 2.84e-13 | pass | running error | 7.79e-16 | 3.44e-15 |
| circular orbit E (retrograde) | chi=0.9, r=1.01 r_isco | 0.961008938927137 | 0.961008938927137 | 3.33e-16 | 9.96e-15 | pass | running error | 1.49e-16 | 1.84e-16 |
| circular orbit L (retrograde) | chi=0.9, r=1.01 r_isco | -4.1682470032271 | -4.16824700322711 | 4.44e-15 | 2.87e-13 | pass | running error | 7.44e-18 | 4.43e-15 |
| circular orbit E (retrograde) | chi=0.9, r=1.5 r_isco | 0.967459301074033 | 0.967459301074033 | 1.11e-16 | 8.82e-15 | pass | running error | 1.02e-16 | 2.13e-16 |
| circular orbit L (retrograde) | chi=0.9, r=1.5 r_isco | -4.40591307768884 | -4.40591307768884 | 4.44e-15 | 4.75e-13 | pass | running error | 1.67e-16 | 4.61e-15 |
| circular orbit E (retrograde) | chi=0.9, r=3 r_isco | 0.981876487207238 | 0.981876487207238 | 0.00e+00 | 8.08e-15 | pass | running error | 9.46e-17 | 9.46e-17 |
| circular orbit L (retrograde) | chi=0.9, r=3 r_isco | -5.55713729091552 | -5.55713729091553 | 7.11e-15 | 1.26e-12 | pass | running error | 9.96e-16 | 6.11e-15 |
| circular orbit E (retrograde) | chi=0.9, r=30 r_isco | 0.998094534241825 | 0.998094534241825 | 2.22e-16 | 7.68e-15 | pass | running error | 1.84e-16 | 3.80e-17 |
| circular orbit L (retrograde) | chi=0.9, r=30 r_isco | -16.2757779560242 | -16.275777956024 | 1.39e-13 | 3.84e-11 | pass | running error | 6.47e-15 | 1.32e-13 |
| circular orbit E (retrograde) | chi=0.9, r=10000 r_isco | 0.999994264363227 | 0.999994264363227 | 0.00e+00 | 7.66e-15 | pass | running error | 2.11e-17 | 2.11e-17 |
| circular orbit L (retrograde) | chi=0.9, r=10000 r_isco | -295.256737786321 | -295.256737787551 | 1.23e-09 | 2.33e-07 | pass | running error | 6.67e-14 | 1.23e-09 |
| circular orbit E (prograde) | chi=0.999, r=1 r_isco | 0.660205926527063 | 0.660205926527072 | 9.44e-15 | 2.41e-12 | pass | running error | 5.53e-15 | 3.91e-15 |
| circular orbit L (prograde) | chi=0.999, r=1 r_isco | 1.34183783805845 | 1.34183783805847 | 1.98e-14 | 6.28e-12 | pass | running error | 1.09e-14 | 8.88e-15 |
| circular orbit E (prograde) | chi=0.999, r=1.01 r_isco | 0.660501986146426 | 0.660501986146422 | 3.77e-15 | 1.96e-12 | pass | running error | 9.70e-16 | 2.80e-15 |
| circular orbit L (prograde) | chi=0.999, r=1.01 r_isco | 1.34251770709621 | 1.3425177070962 | 6.88e-15 | 5.20e-12 | pass | running error | 1.89e-15 | 4.99e-15 |
| circular orbit E (prograde) | chi=0.999, r=1.5 r_isco | 0.751351906522403 | 0.751351906522403 | 4.44e-16 | 3.29e-14 | pass | running error | 2.75e-16 | 1.70e-16 |
| circular orbit L (prograde) | chi=0.999, r=1.5 r_isco | 1.59714830127432 | 1.59714830127432 | 2.00e-15 | 4.48e-13 | pass | running error | 4.45e-16 | 1.55e-15 |
| circular orbit E (prograde) | chi=0.999, r=3 r_isco | 0.869844399749559 | 0.869844399749559 | 0.00e+00 | 1.66e-14 | pass | running error | 2.84e-17 | 2.84e-17 |
| circular orbit L (prograde) | chi=0.999, r=3 r_isco | 2.18207063096679 | 2.18207063096679 | 4.44e-16 | 1.81e-13 | pass | running error | 1.77e-16 | 2.68e-16 |
| circular orbit E (prograde) | chi=0.999, r=30 r_isco | 0.986098066384366 | 0.986098066384365 | 1.11e-16 | 7.94e-15 | pass | running error | 7.63e-17 | 3.47e-17 |
| circular orbit L (prograde) | chi=0.999, r=30 r_isco | 6.1377518437558 | 6.1377518437558 | 5.33e-15 | 1.98e-12 | pass | running error | 2.02e-16 | 5.13e-15 |
| circular orbit E (prograde) | chi=0.999, r=10000 r_isco | 0.999957693010559 | 0.999957693010559 | 2.22e-16 | 7.66e-15 | pass | running error | 4.55e-17 | 1.76e-16 |
| circular orbit L (prograde) | chi=0.999, r=10000 r_isco | 108.722545520512 | 108.722545520232 | 2.80e-10 | 1.16e-08 | pass | running error | 1.78e-14 | 2.80e-10 |
| circular orbit E (retrograde) | chi=0.999, r=1 r_isco | 0.96223841610052 | 0.962238416100519 | 2.22e-16 | 1.00e-14 | pass | running error | 1.51e-16 | 3.73e-16 |
| circular orbit L (retrograde) | chi=0.999, r=1 r_isco | -4.23325236871956 | -4.23325236871955 | 8.88e-15 | 2.97e-13 | pass | running error | 9.55e-16 | 9.84e-15 |
| circular orbit E (retrograde) | chi=0.999, r=1.01 r_isco | 0.962245435406372 | 0.962245435406372 | 3.33e-16 | 9.98e-15 | pass | running error | 6.17e-17 | 2.71e-16 |
| circular orbit L (retrograde) | chi=0.999, r=1.01 r_isco | -4.2334366800393 | -4.23343668003929 | 6.22e-15 | 3.01e-13 | pass | running error | 4.94e-17 | 6.17e-15 |
| circular orbit E (retrograde) | chi=0.999, r=1.5 r_isco | 0.96847731075632 | 0.96847731075632 | 1.11e-16 | 8.84e-15 | pass | running error | 1.01e-16 | 9.92e-18 |
| circular orbit L (retrograde) | chi=0.999, r=1.5 r_isco | -4.47388335628026 | -4.47388335628026 | 1.78e-15 | 4.98e-13 | pass | running error | 5.55e-16 | 1.22e-15 |
| circular orbit E (retrograde) | chi=0.999, r=3 r_isco | 0.982436946451063 | 0.982436946451063 | 2.22e-16 | 8.08e-15 | pass | running error | 1.27e-16 | 9.49e-17 |
| circular orbit L (retrograde) | chi=0.999, r=3 r_isco | -5.64206471196474 | -5.64206471196475 | 1.33e-14 | 1.32e-12 | pass | running error | 1.11e-15 | 1.44e-14 |
| circular orbit E (retrograde) | chi=0.999, r=30 r_isco | 0.99815367815397 | 0.99815367815397 | 1.11e-16 | 7.68e-15 | pass | running error | 1.66e-16 | 5.51e-17 |
| circular orbit L (retrograde) | chi=0.999, r=30 r_isco | -16.5326153898857 | -16.5326153898859 | 1.99e-13 | 4.02e-11 | pass | running error | 1.65e-16 | 1.99e-13 |
| circular orbit E (retrograde) | chi=0.999, r=10000 r_isco | 0.999994442754446 | 0.999994442754446 | 2.22e-16 | 7.66e-15 | pass | running error | 1.02e-16 | 1.20e-16 |
| circular orbit L (retrograde) | chi=0.999, r=10000 r_isco | -299.958153320735 | -299.958153316084 | 4.65e-09 | 2.44e-07 | pass | running error | 4.10e-14 | 4.65e-09 |
| circular orbit E (prograde) | chi=0.999999, r=1 r_isco | 0.586424464480687 | 0.586424464481759 | 1.07e-12 | 3.61e-09 | pass | running error | 2.03e-13 | 8.69e-13 |
| circular orbit L (prograde) | chi=0.999999, r=1 r_isco | 1.17306685285766 | 1.17306685285982 | 2.16e-12 | 7.36e-09 | pass | running error | 3.99e-13 | 1.76e-12 |
| circular orbit E (prograde) | chi=0.999999, r=1.01 r_isco | 0.588319202286352 | 0.588319202286357 | 4.11e-15 | 8.15e-10 | pass | running error | 1.71e-13 | 1.67e-13 |
| circular orbit L (prograde) | chi=0.999999, r=1.01 r_isco | 1.17692021816808 | 1.17692021816807 | 7.99e-15 | 1.68e-09 | pass | running error | 3.35e-13 | 3.43e-13 |
| circular orbit E (prograde) | chi=0.999999, r=1.5 r_isco | 0.712881511512607 | 0.712881511512608 | 8.88e-16 | 8.98e-14 | pass | running error | 2.18e-16 | 1.11e-15 |
| circular orbit L (prograde) | chi=0.999999, r=1.5 r_isco | 1.47560210258711 | 1.47560210258712 | 2.89e-15 | 4.92e-13 | pass | running error | 3.12e-16 | 3.20e-15 |
| circular orbit E (prograde) | chi=0.999999, r=3 r_isco | 0.849768708313159 | 0.849768708313159 | 1.11e-16 | 7.24e-15 | pass | running error | 3.39e-17 | 1.45e-16 |
| circular orbit L (prograde) | chi=0.999999, r=3 r_isco | 2.0417301988282 | 2.0417301988282 | 1.78e-15 | 8.08e-14 | pass | running error | 6.86e-17 | 1.84e-15 |
| circular orbit E (prograde) | chi=0.999999, r=30 r_isco | 0.9838621317803 | 0.983862131780299 | 3.33e-16 | 8.01e-15 | pass | running error | 1.56e-17 | 3.17e-16 |
| circular orbit L (prograde) | chi=0.999999, r=30 r_isco | 5.71428878458835 | 5.71428878458829 | 6.31e-14 | 1.59e-12 | pass | running error | 6.28e-16 | 6.24e-14 |
| circular orbit E (prograde) | chi=0.999999, r=10000 r_isco | 0.999950795562031 | 0.999950795562031 | 1.11e-16 | 7.66e-15 | pass | running error | 9.75e-17 | 2.09e-16 |
| circular orbit L (prograde) | chi=0.999999, r=10000 r_isco | 100.816149096952 | 100.81614909673 | 2.22e-10 | 9.27e-09 | pass | running error | 8.82e-15 | 2.22e-10 |
| circular orbit E (retrograde) | chi=0.999999, r=1 r_isco | 0.962250436621313 | 0.962250436621313 | 0.00e+00 | 1.00e-14 | pass | running error | 6.97e-17 | 6.97e-17 |
| circular orbit L (retrograde) | chi=0.999999, r=1 r_isco | -4.23390132453999 | -4.23390132453999 | 1.78e-15 | 2.98e-13 | pass | running error | 2.98e-16 | 1.48e-15 |
| circular orbit E (retrograde) | chi=0.999999, r=1.01 r_isco | 0.962257453359495 | 0.962257453359495 | 0.00e+00 | 9.98e-15 | pass | running error | 5.13e-17 | 5.13e-17 |
| circular orbit L (retrograde) | chi=0.999999, r=1.01 r_isco | -4.23408565102878 | -4.23408565102878 | 8.88e-16 | 3.01e-13 | pass | running error | 8.53e-16 | 3.52e-17 |
| circular orbit E (retrograde) | chi=0.999999, r=1.5 r_isco | 0.968487209214857 | 0.968487209214857 | 2.22e-16 | 8.84e-15 | pass | running error | 1.45e-16 | 7.69e-17 |
| circular orbit L (retrograde) | chi=0.999999, r=1.5 r_isco | -4.47456015227651 | -4.47456015227652 | 7.99e-15 | 4.98e-13 | pass | running error | 8.36e-16 | 7.16e-15 |
| circular orbit E (retrograde) | chi=0.999999, r=3 r_isco | 0.9824423979323 | 0.9824423979323 | 1.11e-16 | 8.08e-15 | pass | running error | 5.83e-17 | 1.69e-16 |
| circular orbit L (retrograde) | chi=0.999999, r=3 r_isco | -5.64291065623108 | -5.64291065623105 | 3.02e-14 | 1.32e-12 | pass | running error | 4.16e-16 | 2.98e-14 |
| circular orbit E (retrograde) | chi=0.999999, r=30 r_isco | 0.998154253401693 | 0.998154253401693 | 1.11e-16 | 7.68e-15 | pass | running error | 3.05e-16 | 1.94e-16 |
| circular orbit L (retrograde) | chi=0.999999, r=30 r_isco | -16.5351740037123 | -16.5351740037128 | 4.83e-13 | 4.02e-11 | pass | running error | 4.52e-15 | 4.88e-13 |
| circular orbit E (retrograde) | chi=0.999999, r=10000 r_isco | 0.999994444489419 | 0.999994444489419 | 1.11e-16 | 7.66e-15 | pass | running error | 1.03e-16 | 7.83e-18 |
| circular orbit L (retrograde) | chi=0.999999, r=10000 r_isco | -300.004986622054 | -300.004986620671 | 1.38e-09 | 2.44e-07 | pass | running error | 1.72e-14 | 1.38e-09 |
| circular orbit E (prograde) | chi=0.999999999, r=1 r_isco | 0.57826584689804 | 0.578265847044907 | 1.47e-10 | 3.76e-06 | pass | running error | 5.41e-11 | 9.28e-11 |
| circular orbit L (prograde) | chi=0.999999999, r=1 r_isco | 1.15653387575437 | 1.15653387604821 | 2.94e-10 | 7.53e-06 | pass | running error | 1.08e-10 | 1.86e-10 |
| circular orbit E (prograde) | chi=0.999999999, r=1.01 r_isco | 0.581774841735166 | 0.58177484173676 | 1.59e-12 | 9.54e-09 | pass | running error | 1.26e-12 | 3.35e-13 |
| circular orbit L (prograde) | chi=0.999999999, r=1.01 r_isco | 1.16358828041711 | 1.16358828042032 | 3.21e-12 | 1.94e-08 | pass | running error | 2.54e-12 | 6.66e-13 |
| circular orbit E (prograde) | chi=0.999999999, r=1.5 r_isco | 0.709039552036552 | 0.709039552036552 | 1.11e-16 | 1.00e-13 | pass | running error | 4.07e-16 | 5.18e-16 |
| circular orbit L (prograde) | chi=0.999999999, r=1.5 r_isco | 1.46460590968807 | 1.46460590968807 | 6.66e-16 | 5.17e-13 | pass | running error | 1.04e-15 | 1.70e-15 |
| circular orbit E (prograde) | chi=0.999999999, r=3 r_isco | 0.84771508579397 | 0.84771508579397 | 2.22e-16 | 7.25e-15 | pass | running error | 1.28e-16 | 9.44e-17 |
| circular orbit L (prograde) | chi=0.999999999, r=3 r_isco | 2.02886350308821 | 2.02886350308821 | 1.33e-15 | 8.10e-14 | pass | running error | 2.86e-16 | 1.05e-15 |
| circular orbit E (prograde) | chi=0.999999999, r=30 r_isco | 0.983631573649998 | 0.983631573649997 | 2.22e-16 | 8.01e-15 | pass | running error | 1.54e-16 | 6.84e-17 |
| circular orbit L (prograde) | chi=0.999999999, r=30 r_isco | 5.67567170803947 | 5.67567170803945 | 2.75e-14 | 1.56e-12 | pass | running error | 5.27e-16 | 2.70e-14 |
| circular orbit E (prograde) | chi=0.999999999, r=10000 r_isco | 0.999950082994836 | 0.999950082994836 | 0.00e+00 | 7.66e-15 | pass | running error | 1.49e-16 | 1.49e-16 |
| circular orbit L (prograde) | chi=0.999999999, r=10000 r_isco | 100.094141640714 | 100.09414164057 | 1.44e-10 | 9.07e-09 | pass | running error | 1.12e-15 | 1.44e-10 |
| circular orbit E (retrograde) | chi=0.999999999, r=1 r_isco | 0.96225044863742 | 0.96225044863742 | 0.00e+00 | 1.00e-14 | pass | running error | 6.22e-17 | 6.22e-17 |
| circular orbit L (retrograde) | chi=0.999999999, r=1 r_isco | -4.23390197340961 | -4.23390197340961 | 8.88e-16 | 2.98e-13 | pass | running error | 1.28e-16 | 7.60e-16 |
| circular orbit E (retrograde) | chi=0.999999999, r=1.01 r_isco | 0.962257465373035 | 0.962257465373035 | 2.22e-16 | 9.98e-15 | pass | running error | 1.57e-16 | 3.79e-16 |
| circular orbit L (retrograde) | chi=0.999999999, r=1.01 r_isco | -4.23408629991357 | -4.23408629991355 | 1.33e-14 | 3.01e-13 | pass | running error | 5.18e-16 | 1.28e-14 |
| circular orbit E (retrograde) | chi=0.999999999, r=1.5 r_isco | 0.96848721910972 | 0.96848721910972 | 1.11e-16 | 8.84e-15 | pass | running error | 4.66e-17 | 6.44e-17 |
| circular orbit L (retrograde) | chi=0.999999999, r=1.5 r_isco | -4.474560828984 | -4.47456082898401 | 4.44e-15 | 4.98e-13 | pass | running error | 2.52e-16 | 4.19e-15 |
| circular orbit E (retrograde) | chi=0.999999999, r=3 r_isco | 0.98244240338182 | 0.98244240338182 | 1.11e-16 | 8.08e-15 | pass | running error | 2.46e-16 | 1.34e-16 |
| circular orbit L (retrograde) | chi=0.999999999, r=3 r_isco | -5.64291150206765 | -5.64291150206762 | 3.02e-14 | 1.32e-12 | pass | running error | 5.52e-16 | 3.07e-14 |
| circular orbit E (retrograde) | chi=0.999999999, r=30 r_isco | 0.998154253976733 | 0.998154253976733 | 1.11e-16 | 7.68e-15 | pass | running error | 1.25e-16 | 1.42e-17 |
| circular orbit L (retrograde) | chi=0.999999999, r=30 r_isco | -16.5351765620034 | -16.5351765620041 | 6.71e-13 | 4.02e-11 | pass | running error | 4.81e-16 | 6.72e-13 |
| circular orbit E (retrograde) | chi=0.999999999, r=10000 r_isco | 0.999994444491153 | 0.999994444491154 | 2.22e-16 | 7.66e-15 | pass | running error | 1.71e-16 | 5.14e-17 |
| circular orbit L (retrograde) | chi=0.999999999, r=10000 r_isco | -300.005033449428 | -300.005033452019 | 2.59e-09 | 2.44e-07 | pass | running error | 2.94e-14 | 2.59e-09 |
| circular orbit E (prograde) | chi=0.999999999999, r=1 r_isco | 0.577441917056211 | 0.577441918805925 | 1.75e-09 | 3.71e-03 | pass | running error | 5.39e-09 | 7.14e-09 |
| circular orbit L (prograde) | chi=0.999999999999, r=1 r_isco | 1.15488385593769 | 1.1548838594368 | 3.50e-09 | 7.42e-03 | pass | running error | 1.08e-08 | 1.43e-08 |
| circular orbit E (prograde) | chi=0.999999999999, r=1.01 r_isco | 0.581224102495596 | 0.58122410249776 | 2.16e-12 | 1.42e-08 | pass | running error | 5.54e-13 | 1.61e-12 |
| circular orbit L (prograde) | chi=0.999999999999, r=1.01 r_isco | 1.16247768120952 | 1.16247768121388 | 4.36e-12 | 2.89e-08 | pass | running error | 1.12e-12 | 3.24e-12 |
| circular orbit E (prograde) | chi=0.999999999999, r=1.5 r_isco | 0.708655103975408 | 0.708655103975407 | 6.66e-16 | 1.01e-13 | pass | running error | 2.12e-16 | 4.54e-16 |
| circular orbit L (prograde) | chi=0.999999999999, r=1.5 r_isco | 1.46351425677048 | 1.46351425677048 | 3.11e-15 | 5.20e-13 | pass | running error | 1.25e-15 | 1.86e-15 |
| circular orbit E (prograde) | chi=0.999999999999, r=3 r_isco | 0.847509438175163 | 0.847509438175162 | 1.11e-16 | 7.25e-15 | pass | running error | 2.16e-17 | 8.94e-17 |
| circular orbit L (prograde) | chi=0.999999999999, r=3 r_isco | 2.02758787728467 | 2.02758787728467 | 1.33e-15 | 8.10e-14 | pass | running error | 2.59e-16 | 1.07e-15 |
| circular orbit E (prograde) | chi=0.999999999999, r=30 r_isco | 0.983608473481307 | 0.983608473481307 | 2.22e-16 | 8.01e-15 | pass | running error | 1.16e-16 | 1.06e-16 |
| circular orbit L (prograde) | chi=0.999999999999, r=30 r_isco | 5.67184788608506 | 5.67184788608503 | 3.20e-14 | 1.56e-12 | pass | running error | 1.09e-15 | 3.31e-14 |
| circular orbit E (prograde) | chi=0.999999999999, r=10000 r_isco | 0.999950011587781 | 0.999950011587781 | 0.00e+00 | 7.66e-15 | pass | running error | 8.67e-17 | 8.67e-17 |
| circular orbit L (prograde) | chi=0.999999999999, r=10000 r_isco | 100.022640891512 | 100.022640891624 | 1.12e-10 | 9.05e-09 | pass | running error | 8.60e-15 | 1.12e-10 |
| circular orbit E (retrograde) | chi=0.999999999999, r=1 r_isco | 0.962250448649436 | 0.962250448649437 | 2.22e-16 | 1.00e-14 | pass | running error | 9.64e-17 | 1.26e-16 |
| circular orbit L (retrograde) | chi=0.999999999999, r=1 r_isco | -4.23390197405848 | -4.23390197405849 | 7.11e-15 | 2.98e-13 | pass | running error | 2.55e-16 | 6.85e-15 |
| circular orbit E (retrograde) | chi=0.999999999999, r=1.01 r_isco | 0.962257465385049 | 0.962257465385049 | 5.55e-16 | 9.98e-15 | pass | running error | 1.92e-16 | 3.63e-16 |
| circular orbit L (retrograde) | chi=0.999999999999, r=1.01 r_isco | -4.23408630056245 | -4.23408630056246 | 7.99e-15 | 3.01e-13 | pass | running error | 3.18e-16 | 8.31e-15 |
| circular orbit E (retrograde) | chi=0.999999999999, r=1.5 r_isco | 0.968487219119615 | 0.968487219119615 | 2.22e-16 | 8.84e-15 | pass | running error | 6.23e-17 | 1.60e-16 |
| circular orbit L (retrograde) | chi=0.999999999999, r=1.5 r_isco | -4.47456082966071 | -4.4745608296607 | 8.88e-15 | 4.98e-13 | pass | running error | 5.55e-16 | 8.33e-15 |
| circular orbit E (retrograde) | chi=0.999999999999, r=3 r_isco | 0.98244240338727 | 0.982442403387269 | 1.11e-16 | 8.08e-15 | pass | running error | 1.55e-17 | 1.27e-16 |
| circular orbit L (retrograde) | chi=0.999999999999, r=3 r_isco | -5.64291150291349 | -5.64291150291347 | 2.04e-14 | 1.32e-12 | pass | running error | 3.85e-16 | 2.08e-14 |
| circular orbit E (retrograde) | chi=0.999999999999, r=30 r_isco | 0.998154253977308 | 0.998154253977308 | 0.00e+00 | 7.68e-15 | pass | running error | 1.53e-16 | 1.53e-16 |
| circular orbit L (retrograde) | chi=0.999999999999, r=30 r_isco | -16.5351765645617 | -16.5351765645605 | 1.19e-12 | 4.02e-11 | pass | running error | 7.29e-17 | 1.19e-12 |
| circular orbit E (retrograde) | chi=0.999999999999, r=10000 r_isco | 0.999994444491155 | 0.999994444491155 | 1.11e-16 | 7.66e-15 | pass | running error | 1.76e-17 | 9.34e-17 |
| circular orbit L (retrograde) | chi=0.999999999999, r=10000 r_isco | -300.005033496255 | -300.005033497089 | 8.34e-10 | 2.44e-07 | pass | running error | 5.88e-15 | 8.34e-10 |
| outer horizon r_+ | chi=0.0 | 2 | 2 | 0.00e+00 | 7.77e-16 | pass | running error | 0.00e+00 | 0.00e+00 |
| inner horizon r_- | chi=0.0 | 0 | 0 | 0.00e+00 | 3.33e-16 | pass | running error | 0.00e+00 | 0.00e+00 |
| outer horizon r_+ | chi=0.1 | 1.99498743710662 | 1.99498743710662 | 0.00e+00 | 7.76e-16 | pass | running error | 1.00e-16 | 1.00e-16 |
| inner horizon r_- | chi=0.1 | 0.00501256289338003 | 0.00501256289338003 | 0.00e+00 | 3.34e-16 | pass | running error | 1.10e-17 | 1.10e-17 |
| outer horizon r_+ | chi=0.5 | 1.86602540378444 | 1.86602540378444 | 0.00e+00 | 7.51e-16 | pass | running error | 5.02e-17 | 5.02e-17 |
| inner horizon r_- | chi=0.5 | 0.133974596215561 | 0.133974596215561 | 0.00e+00 | 3.66e-16 | pass | running error | 5.02e-17 | 5.02e-17 |
| outer horizon r_+ | chi=0.9 | 1.43588989435407 | 1.43588989435407 | 0.00e+00 | 7.73e-16 | pass | running error | 8.94e-17 | 8.94e-17 |
| inner horizon r_- | chi=0.9 | 0.564110105645933 | 0.564110105645933 | 0.00e+00 | 5.80e-16 | pass | running error | 8.94e-17 | 8.94e-17 |
| outer horizon r_+ | chi=0.999 | 1.04471017781222 | 1.04471017781222 | 0.00e+00 | 3.96e-15 | pass | running error | 2.44e-16 | 2.44e-16 |
| inner horizon r_- | chi=0.999 | 0.955289822187784 | 0.955289822187784 | 0.00e+00 | 3.94e-15 | pass | running error | 3.55e-16 | 3.55e-16 |
| outer horizon r_+ | chi=0.999999999 | 1.00004472135892 | 1.00004472135892 | 0.00e+00 | 3.72e-12 | pass | running error | 1.12e-14 | 1.12e-14 |
| inner horizon r_- | chi=0.999999999 | 0.999955278641082 | 0.999955278641082 | 0.00e+00 | 3.72e-12 | pass | running error | 1.12e-14 | 1.12e-14 |
| outer horizon r_+ | chi=1.0 | 1 | 1 | 0.00e+00 | 2.54e-08 | pass | running error | 0.00e+00 | 0.00e+00 |
| inner horizon r_- | chi=1.0 | 1 | 1 | 0.00e+00 | 2.54e-08 | pass | running error | 0.00e+00 | 0.00e+00 |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (prograde) | chi=0.3, p=6.17543, e=0.1 | 6.82121026329696e-13 | 0 | 6.82e-13 | 2.86e-10 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (prograde) | chi=0.3, p=6.17543, e=0.1 | 1.13686837721616e-13 | 0 | 1.14e-13 | 1.52e-10 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (prograde) | chi=0.3, p=20, e=0.1 | -5.82076609134674e-11 | 0 | 5.82e-11 | 2.56e-08 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (prograde) | chi=0.3, p=20, e=0.1 | -7.27595761418343e-11 | 0 | 7.28e-11 | 1.42e-08 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (prograde) | chi=0.3, p=7.00994, e=0.5 | -7.27595761418343e-12 | 0 | 7.28e-12 | 1.46e-09 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (prograde) | chi=0.3, p=7.00994, e=0.5 | -4.54747350886464e-13 | 0 | 4.55e-13 | 6.77e-11 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (prograde) | chi=0.3, p=20, e=0.5 | -4.65661287307739e-10 | 0 | 4.66e-10 | 8.80e-08 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (prograde) | chi=0.3, p=20, e=0.5 | 7.27595761418343e-12 | 0 | 7.28e-12 | 5.14e-09 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (prograde) | chi=0.3, p=7.87611, e=0.9 | 0 | 0 | 0.00e+00 | 1.28e-06 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (prograde) | chi=0.3, p=7.87611, e=0.9 | 1.27045041153906e-11 | 0 | 1.27e-11 | 1.06e-09 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (prograde) | chi=0.3, p=20, e=0.9 | -4.76837158203125e-07 | 0 | 4.77e-07 | 4.86e-05 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (prograde) | chi=0.3, p=20, e=0.9 | 2.3283064365387e-10 | 0 | 2.33e-10 | 5.91e-08 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (retrograde) | chi=0.3, p=8.6153, e=0.1 | 1.81898940354586e-12 | 0 | 1.82e-12 | 1.08e-09 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (retrograde) | chi=0.3, p=8.6153, e=0.1 | -1.36424205265939e-12 | 0 | 1.36e-12 | 5.95e-10 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (retrograde) | chi=0.3, p=20, e=0.1 | -2.91038304567337e-11 | 0 | 2.91e-11 | 2.74e-08 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (retrograde) | chi=0.3, p=20, e=0.1 | -5.82076609134674e-11 | 0 | 5.82e-11 | 1.53e-08 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (retrograde) | chi=0.3, p=9.69133, e=0.5 | 0 | 0 | 0.00e+00 | 5.50e-09 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (retrograde) | chi=0.3, p=9.69133, e=0.5 | 4.54747350886464e-13 | 0 | 4.55e-13 | 3.02e-10 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (retrograde) | chi=0.3, p=20, e=0.5 | -4.65661287307739e-10 | 0 | 4.66e-10 | 9.39e-08 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (retrograde) | chi=0.3, p=20, e=0.5 | -1.09139364212751e-11 | 0 | 1.09e-11 | 5.73e-09 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (retrograde) | chi=0.3, p=10.7354, e=0.9 | -1.49011611938477e-08 | 0 | 1.49e-08 | 4.51e-06 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (retrograde) | chi=0.3, p=10.7354, e=0.9 | 2.20552465179935e-11 | 0 | 2.21e-11 | 4.80e-09 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (retrograde) | chi=0.3, p=20, e=0.9 | -2.38418579101562e-07 | 0 | 2.38e-07 | 5.17e-05 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (retrograde) | chi=0.3, p=20, e=0.9 | -2.40106601268053e-10 | 0 | 2.40e-10 | 6.61e-08 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (prograde) | chi=0.9, p=2.88609, e=0.1 | 7.105427357601e-15 | 0 | 7.11e-15 | 1.05e-11 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (prograde) | chi=0.9, p=2.88609, e=0.1 | 1.4210854715202e-14 | 0 | 1.42e-14 | 5.40e-12 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (prograde) | chi=0.9, p=20, e=0.1 | -2.91038304567337e-11 | 0 | 2.91e-11 | 2.63e-08 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (prograde) | chi=0.9, p=20, e=0.1 | -1.45519152283669e-11 | 0 | 1.46e-11 | 1.46e-08 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (prograde) | chi=0.9, p=3.39988, e=0.5 | 0 | 0 | 0.00e+00 | 7.40e-11 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (prograde) | chi=0.9, p=3.39988, e=0.5 | 1.77635683940025e-14 | 0 | 1.78e-14 | 2.67e-12 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (prograde) | chi=0.9, p=20, e=0.5 | 4.65661287307739e-10 | 0 | 4.66e-10 | 9.02e-08 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (prograde) | chi=0.9, p=20, e=0.5 | 5.45696821063757e-11 | 0 | 5.46e-11 | 5.33e-09 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (prograde) | chi=0.9, p=4.0009, e=0.9 | -9.31322574615479e-10 | 0 | 9.31e-10 | 1.63e-06 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (prograde) | chi=0.9, p=4.0009, e=0.9 | -5.04485342389671e-13 | 0 | 5.04e-13 | 8.73e-10 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (prograde) | chi=0.9, p=20, e=0.9 | -4.76837158203125e-07 | 0 | 4.77e-07 | 5.00e-05 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (prograde) | chi=0.9, p=20, e=0.9 | 3.23780113831162e-10 | 0 | 3.24e-10 | 6.24e-08 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (retrograde) | chi=0.9, p=10.8043, e=0.1 | -3.63797880709171e-12 | 0 | 3.64e-12 | 3.24e-09 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (retrograde) | chi=0.9, p=10.8043, e=0.1 | 0 | 0 | 0.00e+00 | 1.86e-09 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (retrograde) | chi=0.9, p=20, e=0.1 | 2.91038304567337e-11 | 0 | 2.91e-11 | 3.20e-08 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (retrograde) | chi=0.9, p=20, e=0.1 | 1.45519152283669e-11 | 0 | 1.46e-11 | 1.83e-08 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (retrograde) | chi=0.9, p=12.0948, e=0.5 | -1.16415321826935e-10 | 0 | 1.16e-10 | 1.58e-08 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (retrograde) | chi=0.9, p=12.0948, e=0.5 | 0 | 0 | 0.00e+00 | 1.01e-09 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (retrograde) | chi=0.9, p=20, e=0.5 | 4.65661287307739e-10 | 0 | 4.66e-10 | 1.08e-07 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (retrograde) | chi=0.9, p=20, e=0.5 | 6.91215973347425e-11 | 0 | 6.91e-11 | 7.17e-09 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (retrograde) | chi=0.9, p=13.289, e=0.9 | 0 | 0 | 0.00e+00 | 1.23e-05 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (retrograde) | chi=0.9, p=13.289, e=0.9 | -4.91127138957381e-11 | 0 | 4.91e-11 | 1.63e-08 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (retrograde) | chi=0.9, p=20, e=0.9 | 0 | 0 | 0.00e+00 | 5.92e-05 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (retrograde) | chi=0.9, p=20, e=0.9 | 1.68802216649055e-09 | 0 | 1.69e-09 | 8.43e-08 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (prograde) | chi=0.99, p=1.81876, e=0.1 | 2.22044604925031e-14 | 0 | 2.22e-14 | 1.51e-10 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (prograde) | chi=0.99, p=1.81876, e=0.1 | 7.32747196252603e-15 | 0 | 7.33e-15 | 7.45e-11 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (prograde) | chi=0.99, p=20, e=0.1 | 0 | 0 | 0.00e+00 | 2.65e-08 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (prograde) | chi=0.99, p=20, e=0.1 | 0 | 0 | 0.00e+00 | 1.47e-08 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (prograde) | chi=0.99, p=2.26015, e=0.5 | 5.6843418860808e-14 | 0 | 5.68e-14 | 1.06e-08 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (prograde) | chi=0.99, p=2.26015, e=0.5 | 2.64899213675562e-13 | 0 | 2.65e-13 | 2.61e-10 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (prograde) | chi=0.99, p=20, e=0.5 | 4.65661287307739e-10 | 0 | 4.66e-10 | 9.06e-08 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (prograde) | chi=0.99, p=20, e=0.5 | -7.27595761418343e-12 | 0 | 7.28e-12 | 5.37e-09 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (prograde) | chi=0.99, p=2.77243, e=0.9 | -1.16415321826935e-10 | 0 | 1.16e-10 | 7.22e-08 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (prograde) | chi=0.99, p=2.77243, e=0.9 | 2.89768209427166e-14 | 0 | 2.90e-14 | 2.42e-11 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (prograde) | chi=0.99, p=20, e=0.9 | -2.38418579101562e-07 | 0 | 2.38e-07 | 5.02e-05 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (prograde) | chi=0.99, p=20, e=0.9 | 1.15687726065516e-09 | 0 | 1.16e-09 | 6.29e-08 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (retrograde) | chi=0.99, p=11.1194, e=0.1 | -3.63797880709171e-12 | 0 | 3.64e-12 | 3.72e-09 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (retrograde) | chi=0.99, p=11.1194, e=0.1 | 0 | 0 | 0.00e+00 | 2.14e-09 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (retrograde) | chi=0.99, p=20, e=0.1 | -2.91038304567337e-11 | 0 | 2.91e-11 | 3.27e-08 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (retrograde) | chi=0.99, p=20, e=0.1 | -1.45519152283669e-11 | 0 | 1.46e-11 | 1.88e-08 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (retrograde) | chi=0.99, p=12.4405, e=0.5 | -5.82076609134674e-11 | 0 | 5.82e-11 | 1.80e-08 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (retrograde) | chi=0.99, p=12.4405, e=0.5 | -6.3664629124105e-12 | 0 | 6.37e-12 | 1.17e-09 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (retrograde) | chi=0.99, p=20, e=0.5 | 9.31322574615479e-10 | 0 | 9.31e-10 | 1.10e-07 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (retrograde) | chi=0.99, p=20, e=0.5 | 2.5465851649642e-11 | 0 | 2.55e-11 | 7.39e-09 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (retrograde) | chi=0.99, p=13.6558, e=0.9 | 0 | 0 | 0.00e+00 | 1.39e-05 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (retrograde) | chi=0.99, p=13.6558, e=0.9 | -2.5465851649642e-10 | 0 | 2.55e-10 | 1.90e-08 | pass | residual |  |  |
| R(r) at the apoapsis p/(1-e) with KerrGeoPy's E, L (retrograde) | chi=0.99, p=20, e=0.9 | 0 | 0 | 0.00e+00 | 6.03e-05 | pass | residual |  |  |
| R(r) at the periapsis p/(1+e) with KerrGeoPy's E, L (retrograde) | chi=0.99, p=20, e=0.9 | 1.39880285132676e-09 | 0 | 1.40e-09 | 8.71e-08 | pass | residual |  |  |
| generic orbit E | chi=0.3, p=6.81541, e=0.1, x=0.9 | 0.939940875429088 | 0.939940875429087 | 5.55e-16 | 5.65e-14 | pass | conditioning + running error | 4.57e-16 | 9.83e-17 |
| generic orbit L_z | chi=0.3, p=6.81541, e=0.1, x=0.9 | 2.97243702204081 | 2.9724370220408 | 9.33e-15 | 1.10e-12 | pass | conditioning + running error | 9.39e-15 | 6.75e-17 |
| generic orbit Q | chi=0.3, p=6.81541, e=0.1, x=0.9 | 2.07448931783715 | 2.07448931783714 | 1.38e-14 | 1.55e-12 | pass | conditioning + running error | 1.33e-14 | 4.87e-16 |
| generic orbit E | chi=0.3, p=25, e=0.1, x=0.9 | 0.980809569927412 | 0.980809569927412 | 1.11e-16 | 4.76e-14 | pass | conditioning + running error | 1.27e-16 | 1.55e-17 |
| generic orbit L_z | chi=0.3, p=25, e=0.1, x=0.9 | 4.76606237117898 | 4.76606237117895 | 3.11e-14 | 6.50e-12 | pass | conditioning + running error | 2.46e-14 | 6.44e-15 |
| generic orbit Q | chi=0.3, p=25, e=0.1, x=0.9 | 5.3289421139308 | 5.32894211393073 | 7.02e-14 | 1.46e-11 | pass | conditioning + running error | 5.53e-14 | 1.48e-14 |
| generic orbit E | chi=0.3, p=7.45743, e=0.1, x=0.4 | 0.94527984494593 | 0.94527984494593 | 2.22e-16 | 9.22e-14 | pass | conditioning + running error | 1.43e-16 | 3.66e-16 |
| generic orbit L_z | chi=0.3, p=7.45743, e=0.1, x=0.4 | 1.38269760851703 | 1.38269760851702 | 3.11e-15 | 9.38e-13 | pass | conditioning + running error | 2.82e-16 | 3.39e-15 |
| generic orbit Q | chi=0.3, p=7.45743, e=0.1, x=0.4 | 10.0452738708575 | 10.0452738708574 | 4.62e-14 | 1.36e-11 | pass | conditioning + running error | 4.54e-15 | 5.07e-14 |
| generic orbit E | chi=0.3, p=25, e=0.1, x=0.4 | 0.980863735357408 | 0.980863735357408 | 2.22e-16 | 8.03e-14 | pass | conditioning + running error | 2.27e-16 | 5.08e-18 |
| generic orbit L_z | chi=0.3, p=25, e=0.1, x=0.4 | 2.12595429925214 | 2.12595429925213 | 1.42e-14 | 5.09e-12 | pass | conditioning + running error | 1.50e-14 | 8.28e-16 |
| generic orbit Q | chi=0.3, p=25, e=0.1, x=0.4 | 23.7311945519196 | 23.7311945519193 | 3.16e-13 | 1.14e-10 | pass | conditioning + running error | 3.31e-13 | 1.51e-14 |
| generic orbit E | chi=0.3, p=7.85211, e=0.1, x=0.1 | 0.94808281702575 | 0.94808281702575 | 2.22e-16 | 6.68e-13 | pass | conditioning + running error | 1.92e-16 | 2.97e-17 |
| generic orbit L_z | chi=0.3, p=7.85211, e=0.1, x=0.1 | 0.354609176097052 | 0.354609176097052 | 3.89e-16 | 1.91e-12 | pass | conditioning + running error | 1.76e-16 | 2.13e-16 |
| generic orbit Q | chi=0.3, p=7.85211, e=0.1, x=0.1 | 12.4580305918614 | 12.4580305918614 | 2.13e-14 | 1.35e-10 | pass | conditioning + running error | 1.61e-14 | 5.18e-15 |
| generic orbit E | chi=0.3, p=25, e=0.1, x=0.1 | 0.98089727263091 | 0.98089727263091 | 5.55e-16 | 6.14e-13 | pass | conditioning + running error | 4.67e-16 | 8.84e-17 |
| generic orbit L_z | chi=0.3, p=25, e=0.1, x=0.1 | 0.53267642157112 | 0.532676421571111 | 9.21e-15 | 1.02e-11 | pass | conditioning + running error | 6.75e-15 | 2.47e-15 |
| generic orbit Q | chi=0.3, p=25, e=0.1, x=0.1 | 28.0940444318461 | 28.0940444318451 | 9.95e-13 | 1.08e-09 | pass | conditioning + running error | 7.08e-13 | 2.87e-13 |
| generic orbit E | chi=0.3, p=8.52045, e=0.1, x=-0.4 | 0.95219072916429 | 0.95219072916429 | 2.22e-16 | 8.99e-14 | pass | conditioning + running error | 1.23e-16 | 9.88e-17 |
| generic orbit L_z | chi=0.3, p=8.52045, e=0.1, x=-0.4 | -1.47596429789207 | -1.47596429789208 | 1.78e-15 | 1.10e-12 | pass | conditioning + running error | 1.81e-16 | 1.60e-15 |
| generic orbit Q | chi=0.3, p=8.52045, e=0.1, x=-0.4 | 11.4440266562594 | 11.4440266562594 | 2.66e-14 | 1.71e-11 | pass | conditioning + running error | 3.36e-15 | 2.33e-14 |
| generic orbit E | chi=0.3, p=25, e=0.1, x=-0.4 | 0.980954940147465 | 0.980954940147465 | 4.44e-16 | 8.04e-14 | pass | conditioning + running error | 3.72e-16 | 7.20e-17 |
| generic orbit L_z | chi=0.3, p=25, e=0.1, x=-0.4 | -2.13884165555893 | -2.1388416555589 | 2.84e-14 | 5.08e-12 | pass | conditioning + running error | 2.45e-14 | 3.92e-15 |
| generic orbit Q | chi=0.3, p=25, e=0.1, x=-0.4 | 24.019731236507 | 24.0197312365064 | 6.39e-13 | 1.14e-10 | pass | conditioning + running error | 5.49e-13 | 9.04e-14 |
| generic orbit E | chi=0.3, p=9.19724, e=0.1, x=-0.9 | 0.955706671007123 | 0.955706671007124 | 3.33e-16 | 5.38e-14 | pass | conditioning + running error | 2.38e-16 | 9.51e-17 |
| generic orbit L_z | chi=0.3, p=9.19724, e=0.1, x=-0.9 | -3.44484483204361 | -3.44484483204361 | 4.88e-15 | 1.59e-12 | pass | conditioning + running error | 3.00e-15 | 1.88e-15 |
| generic orbit Q | chi=0.3, p=9.19724, e=0.1, x=-0.9 | 2.78508822683919 | 2.78508822683919 | 7.55e-15 | 2.58e-12 | pass | conditioning + running error | 5.07e-15 | 2.48e-15 |
| generic orbit E | chi=0.3, p=25, e=0.1, x=-0.9 | 0.981014877934024 | 0.981014877934024 | 3.33e-16 | 4.79e-14 | pass | conditioning + running error | 3.59e-16 | 2.62e-17 |
| generic orbit L_z | chi=0.3, p=25, e=0.1, x=-0.9 | -4.83131687766506 | -4.83131687766507 | 7.99e-15 | 6.49e-12 | pass | conditioning + running error | 2.00e-14 | 1.20e-14 |
| generic orbit Q | chi=0.3, p=25, e=0.1, x=-0.9 | 5.47583859287206 | 5.47583859287208 | 1.87e-14 | 1.48e-11 | pass | conditioning + running error | 4.62e-14 | 2.75e-14 |
| generic orbit E | chi=0.3, p=7.73003, e=0.5, x=0.9 | 0.956845728861899 | 0.956845728861899 | 1.11e-16 | 1.36e-14 | pass | conditioning + running error | 6.63e-17 | 4.47e-17 |
| generic orbit L_z | chi=0.3, p=7.73003, e=0.5, x=0.9 | 3.12625395388669 | 3.1262539538867 | 4.00e-15 | 8.86e-13 | pass | conditioning + running error | 1.28e-15 | 2.72e-15 |
| generic orbit Q | chi=0.3, p=7.73003, e=0.5, x=0.9 | 2.29398491854483 | 2.29398491854483 | 5.33e-15 | 1.32e-12 | pass | conditioning + running error | 1.74e-15 | 3.59e-15 |
| generic orbit E | chi=0.3, p=25, e=0.5, x=0.9 | 0.985352750710748 | 0.985352750710748 | 1.11e-16 | 1.24e-14 | pass | conditioning + running error | 5.30e-17 | 5.80e-17 |
| generic orbit L_z | chi=0.3, p=25, e=0.5, x=0.9 | 4.78947541884455 | 4.7894754188445 | 5.42e-14 | 5.08e-12 | pass | conditioning + running error | 1.71e-15 | 5.25e-14 |
| generic orbit Q | chi=0.3, p=25, e=0.5, x=0.9 | 5.38126789647637 | 5.38126789647625 | 1.23e-13 | 1.14e-11 | pass | conditioning + running error | 2.79e-15 | 1.20e-13 |
| generic orbit E | chi=0.3, p=8.42992, e=0.5, x=0.4 | 0.960513506689056 | 0.960513506689056 | 1.11e-16 | 2.21e-14 | pass | conditioning + running error | 1.78e-16 | 6.67e-17 |
| generic orbit L_z | chi=0.3, p=8.42992, e=0.5, x=0.4 | 1.4517288545654 | 1.4517288545654 | 4.66e-15 | 8.43e-13 | pass | conditioning + running error | 1.37e-15 | 3.29e-15 |
| generic orbit Q | chi=0.3, p=8.42992, e=0.5, x=0.4 | 11.0703149862254 | 11.0703149862255 | 7.11e-14 | 1.28e-11 | pass | conditioning + running error | 2.09e-14 | 5.02e-14 |
| generic orbit E | chi=0.3, p=25, e=0.5, x=0.4 | 0.985384312040071 | 0.985384312040071 | 2.22e-16 | 2.04e-14 | pass | conditioning + running error | 1.07e-16 | 1.15e-16 |
| generic orbit L_z | chi=0.3, p=25, e=0.5, x=0.4 | 2.13709226662252 | 2.13709226662253 | 1.02e-14 | 4.40e-12 | pass | conditioning + running error | 7.34e-15 | 2.87e-15 |
| generic orbit Q | chi=0.3, p=25, e=0.5, x=0.4 | 23.9798013617767 | 23.979801361777 | 2.27e-13 | 9.86e-11 | pass | conditioning + running error | 1.65e-13 | 6.28e-14 |
| generic orbit E | chi=0.3, p=8.86274, e=0.5, x=0.1 | 0.962468248549342 | 0.962468248549342 | 1.11e-16 | 1.55e-13 | pass | conditioning + running error | 5.29e-17 | 1.64e-16 |
| generic orbit L_z | chi=0.3, p=8.86274, e=0.5, x=0.1 | 0.372014333762133 | 0.372014333762133 | 5.55e-16 | 1.92e-12 | pass | conditioning + running error | 1.04e-16 | 6.59e-16 |
| generic orbit Q | chi=0.3, p=8.86274, e=0.5, x=0.1 | 13.7076344368885 | 13.7076344368885 | 3.38e-14 | 1.42e-10 | pass | conditioning + running error | 3.78e-15 | 3.75e-14 |
| generic orbit E | chi=0.3, p=25, e=0.5, x=0.1 | 0.985403868692744 | 0.985403868692744 | 0.00e+00 | 1.51e-13 | pass | conditioning + running error | 1.11e-16 | 1.11e-16 |
| generic orbit L_z | chi=0.3, p=25, e=0.5, x=0.1 | 0.535574859502972 | 0.535574859502971 | 8.88e-16 | 9.82e-12 | pass | conditioning + running error | 4.90e-16 | 3.98e-16 |
| generic orbit Q | chi=0.3, p=25, e=0.5, x=0.1 | 28.399784631138 | 28.3997846311379 | 1.10e-13 | 1.04e-09 | pass | conditioning + running error | 4.63e-14 | 6.38e-14 |
| generic orbit E | chi=0.3, p=9.59908, e=0.5, x=-0.4 | 0.96536461185403 | 0.96536461185403 | 1.11e-16 | 2.17e-14 | pass | conditioning + running error | 1.04e-16 | 6.90e-18 |
| generic orbit L_z | chi=0.3, p=9.59908, e=0.5, x=-0.4 | -1.54678760594979 | -1.54678760594979 | 3.55e-15 | 1.01e-12 | pass | conditioning + running error | 6.15e-16 | 4.17e-15 |
| generic orbit Q | chi=0.3, p=9.59908, e=0.5, x=-0.4 | 12.5660436442425 | 12.5660436442426 | 5.51e-14 | 1.63e-11 | pass | conditioning + running error | 1.03e-14 | 6.54e-14 |
| generic orbit E | chi=0.3, p=25, e=0.5, x=-0.4 | 0.985437523382338 | 0.985437523382338 | 0.00e+00 | 2.04e-14 | pass | conditioning + running error | 6.60e-18 | 6.60e-18 |
| generic orbit L_z | chi=0.3, p=25, e=0.5, x=-0.4 | -2.15122365903719 | -2.15122365903717 | 1.47e-14 | 4.38e-12 | pass | conditioning + running error | 4.02e-15 | 1.87e-14 |
| generic orbit Q | chi=0.3, p=25, e=0.5, x=-0.4 | 24.2979427781029 | 24.2979427781025 | 3.38e-13 | 9.89e-11 | pass | conditioning + running error | 8.73e-14 | 4.25e-13 |
| generic orbit E | chi=0.3, p=10.3481, e=0.5, x=-0.9 | 0.967869423779683 | 0.967869423779683 | 3.33e-16 | 1.32e-14 | pass | conditioning + running error | 1.14e-16 | 2.19e-16 |
| generic orbit L_z | chi=0.3, p=10.3481, e=0.5, x=-0.9 | -3.60732879032042 | -3.6073287903204 | 1.78e-14 | 1.31e-12 | pass | conditioning + running error | 2.72e-15 | 1.50e-14 |
| generic orbit Q | chi=0.3, p=10.3481, e=0.5, x=-0.9 | 3.05347132356957 | 3.05347132356954 | 3.02e-14 | 2.23e-12 | pass | conditioning + running error | 4.37e-15 | 2.58e-14 |
| generic orbit E | chi=0.3, p=25, e=0.5, x=-0.9 | 0.985472539205856 | 0.985472539205857 | 3.33e-16 | 1.24e-14 | pass | conditioning + running error | 3.01e-16 | 3.21e-17 |
| generic orbit L_z | chi=0.3, p=25, e=0.5, x=-0.9 | -4.86103382630293 | -4.86103382630293 | 0.00e+00 | 5.03e-12 | pass | conditioning + running error | 2.83e-14 | 2.83e-14 |
| generic orbit Q | chi=0.3, p=25, e=0.5, x=-0.9 | 5.54325060492956 | 5.54325060492956 | 8.88e-16 | 1.15e-11 | pass | conditioning + running error | 6.54e-14 | 6.63e-14 |
| generic orbit E | chi=0.3, p=8.43636, e=0.8, x=0.9 | 0.979702261202768 | 0.979702261202768 | 0.00e+00 | 1.11e-14 | pass | conditioning + running error | 7.49e-20 | 7.49e-20 |
| generic orbit L_z | chi=0.3, p=8.43636, e=0.8, x=0.9 | 3.29559015948922 | 3.29559015948923 | 9.77e-15 | 4.69e-12 | pass | conditioning + running error | 1.58e-16 | 9.93e-15 |
| generic orbit Q | chi=0.3, p=8.43636, e=0.8, x=0.9 | 2.54830905709174 | 2.54830905709175 | 1.47e-14 | 7.27e-12 | pass | conditioning + running error | 2.38e-16 | 1.49e-14 |
| generic orbit E | chi=0.3, p=25, e=0.8, x=0.9 | 0.992882386808591 | 0.992882386808591 | 1.11e-16 | 1.03e-14 | pass | conditioning + running error | 2.28e-17 | 8.82e-17 |
| generic orbit L_z | chi=0.3, p=25, e=0.8, x=0.9 | 4.82827109657425 | 4.82827109657447 | 2.23e-13 | 2.54e-11 | pass | conditioning + running error | 4.48e-15 | 2.27e-13 |
| generic orbit Q | chi=0.3, p=25, e=0.8, x=0.9 | 5.46853680124186 | 5.46853680124236 | 5.04e-13 | 5.76e-11 | pass | conditioning + running error | 9.84e-15 | 5.13e-13 |
| generic orbit E | chi=0.3, p=9.16555, e=0.8, x=0.4 | 0.981336504521155 | 0.981336504521154 | 3.33e-16 | 1.79e-14 | pass | conditioning + running error | 3.45e-17 | 2.99e-16 |
| generic orbit L_z | chi=0.3, p=9.16555, e=0.8, x=0.4 | 1.52777882663896 | 1.52777882663893 | 3.46e-14 | 4.60e-12 | pass | conditioning + running error | 3.77e-16 | 3.43e-14 |
| generic orbit Q | chi=0.3, p=9.16555, e=0.8, x=0.4 | 12.2568633384792 | 12.2568633384786 | 5.52e-13 | 7.38e-11 | pass | conditioning + running error | 3.02e-15 | 5.49e-13 |
| generic orbit E | chi=0.3, p=25, e=0.8, x=0.4 | 0.992889842310186 | 0.992889842310186 | 0.00e+00 | 1.69e-14 | pass | conditioning + running error | 6.60e-17 | 6.60e-17 |
| generic orbit L_z | chi=0.3, p=25, e=0.8, x=0.4 | 2.15557085618321 | 2.15557085618318 | 3.46e-14 | 2.26e-11 | pass | conditioning + running error | 7.22e-16 | 3.54e-14 |
| generic orbit Q | chi=0.3, p=25, e=0.8, x=0.4 | 24.3951212430731 | 24.3951212430723 | 7.74e-13 | 5.12e-10 | pass | conditioning + running error | 2.42e-14 | 7.99e-13 |
| generic orbit E | chi=0.3, p=9.61944, e=0.8, x=0.1 | 0.982223283151074 | 0.982223283151074 | 1.11e-16 | 1.24e-13 | pass | conditioning + running error | 5.24e-17 | 5.86e-17 |
| generic orbit L_z | chi=0.3, p=9.61944, e=0.8, x=0.1 | 0.391175300920014 | 0.391175300920012 | 2.50e-15 | 1.08e-11 | pass | conditioning + running error | 4.97e-17 | 2.45e-15 |
| generic orbit Q | chi=0.3, p=9.61944, e=0.8, x=0.1 | 15.1519331432399 | 15.1519331432397 | 2.08e-13 | 8.36e-10 | pass | conditioning + running error | 5.01e-15 | 2.03e-13 |
| generic orbit E | chi=0.3, p=25, e=0.8, x=0.1 | 0.99289446796299 | 0.99289446796299 | 1.11e-16 | 1.23e-13 | pass | conditioning + running error | 6.33e-17 | 4.77e-17 |
| generic orbit L_z | chi=0.3, p=25, e=0.8, x=0.1 | 0.540387115145374 | 0.540387115145415 | 4.16e-14 | 5.18e-11 | pass | conditioning + running error | 4.02e-16 | 4.12e-14 |
| generic orbit Q | chi=0.3, p=25, e=0.8, x=0.1 | 28.9110668945748 | 28.9110668945793 | 4.44e-12 | 5.55e-09 | pass | conditioning + running error | 4.86e-14 | 4.39e-12 |
| generic orbit E | chi=0.3, p=10.3957, e=0.8, x=-0.4 | 0.983554865754667 | 0.983554865754668 | 1.11e-16 | 1.77e-14 | pass | conditioning + running error | 1.09e-16 | 1.88e-18 |
| generic orbit L_z | chi=0.3, p=10.3957, e=0.8, x=-0.4 | -1.62456997538305 | -1.62456997538304 | 1.04e-14 | 5.49e-12 | pass | conditioning + running error | 3.95e-16 | 1.08e-14 |
| generic orbit Q | chi=0.3, p=10.3957, e=0.8, x=-0.4 | 13.8584109846589 | 13.8584109846587 | 1.78e-13 | 9.36e-11 | pass | conditioning + running error | 8.29e-15 | 1.86e-13 |
| generic orbit E | chi=0.3, p=25, e=0.8, x=-0.4 | 0.992902438814105 | 0.992902438814105 | 0.00e+00 | 1.69e-14 | pass | conditioning + running error | 2.53e-17 | 2.53e-17 |
| generic orbit L_z | chi=0.3, p=25, e=0.8, x=-0.4 | -2.17180683341888 | -2.17180683341879 | 8.70e-14 | 2.25e-11 | pass | conditioning + running error | 4.91e-16 | 8.75e-14 |
| generic orbit Q | chi=0.3, p=25, e=0.8, x=-0.4 | 24.7639801817189 | 24.7639801817169 | 1.99e-12 | 5.12e-10 | pass | conditioning + running error | 1.63e-14 | 2.00e-12 |
| generic orbit E | chi=0.3, p=11.1895, e=0.8, x=-0.9 | 0.984721130757474 | 0.984721130757474 | 1.11e-16 | 1.07e-14 | pass | conditioning + running error | 3.72e-17 | 7.39e-17 |
| generic orbit L_z | chi=0.3, p=11.1895, e=0.8, x=-0.9 | -3.78520003372189 | -3.78520003372181 | 8.70e-14 | 6.90e-12 | pass | conditioning + running error | 2.92e-15 | 8.41e-14 |
| generic orbit Q | chi=0.3, p=11.1895, e=0.8, x=-0.9 | 3.36134628137014 | 3.36134628136999 | 1.55e-13 | 1.23e-11 | pass | conditioning + running error | 4.80e-15 | 1.50e-13 |
| generic orbit E | chi=0.3, p=25, e=0.8, x=-0.9 | 0.992910746392035 | 0.992910746392036 | 2.22e-16 | 1.03e-14 | pass | conditioning + running error | 5.88e-17 | 1.63e-16 |
| generic orbit L_z | chi=0.3, p=25, e=0.8, x=-0.9 | -4.91049503234877 | -4.91049503234919 | 4.17e-13 | 2.50e-11 | pass | conditioning + running error | 1.01e-15 | 4.18e-13 |
| generic orbit Q | chi=0.3, p=25, e=0.8, x=-0.9 | 5.65636835593056 | 5.65636835593152 | 9.57e-13 | 5.77e-11 | pass | conditioning + running error | 2.95e-15 | 9.60e-13 |
| generic orbit E | chi=0.7, p=4.82442, e=0.1, x=0.9 | 0.91488443130757 | 0.91488443130757 | 0.00e+00 | 8.00e-14 | pass | conditioning + running error | 1.97e-16 | 1.97e-16 |
| generic orbit L_z | chi=0.7, p=4.82442, e=0.1, x=0.9 | 2.51007555672751 | 2.51007555672751 | 4.44e-16 | 1.01e-12 | pass | conditioning + running error | 2.26e-15 | 1.81e-15 |
| generic orbit Q | chi=0.7, p=4.82442, e=0.1, x=0.9 | 1.49306424732703 | 1.49306424732703 | 4.44e-16 | 1.20e-12 | pass | conditioning + running error | 3.07e-15 | 2.63e-15 |
| generic orbit E | chi=0.7, p=25, e=0.1, x=0.9 | 0.980686193403886 | 0.980686193403886 | 0.00e+00 | 4.79e-14 | pass | conditioning + running error | 3.00e-16 | 3.00e-16 |
| generic orbit L_z | chi=0.7, p=25, e=0.1, x=0.9 | 4.72514609519641 | 4.72514609519641 | 3.55e-15 | 6.56e-12 | pass | conditioning + running error | 3.21e-14 | 3.57e-14 |
| generic orbit Q | chi=0.7, p=25, e=0.1, x=0.9 | 5.24076035169386 | 5.24076035169385 | 8.88e-15 | 1.46e-11 | pass | conditioning + running error | 7.05e-14 | 7.93e-14 |
| generic orbit E | chi=0.7, p=6.31944, e=0.1, x=0.4 | 0.93605443040397 | 0.93605443040397 | 1.11e-16 | 1.01e-13 | pass | conditioning + running error | 1.69e-16 | 5.78e-17 |
| generic orbit L_z | chi=0.7, p=6.31944, e=0.1, x=0.4 | 1.28647153912788 | 1.28647153912788 | 4.44e-16 | 8.19e-13 | pass | conditioning + running error | 6.66e-16 | 2.21e-16 |
| generic orbit Q | chi=0.7, p=6.31944, e=0.1, x=0.4 | 8.73975430590378 | 8.73975430590379 | 7.11e-15 | 1.11e-11 | pass | conditioning + running error | 9.65e-15 | 2.55e-15 |
| generic orbit E | chi=0.7, p=25, e=0.1, x=0.4 | 0.980803852739759 | 0.980803852739759 | 1.11e-16 | 8.06e-14 | pass | conditioning + running error | 3.13e-16 | 2.02e-16 |
| generic orbit L_z | chi=0.7, p=25, e=0.1, x=0.4 | 2.11695702217215 | 2.11695702217215 | 5.77e-15 | 5.11e-12 | pass | conditioning + running error | 1.40e-14 | 8.20e-15 |
| generic orbit Q | chi=0.7, p=25, e=0.1, x=0.4 | 23.5435625241396 | 23.5435625241397 | 1.21e-13 | 1.14e-10 | pass | conditioning + running error | 3.08e-13 | 1.87e-13 |
| generic orbit E | chi=0.7, p=7.29503, e=0.1, x=0.1 | 0.944662704233246 | 0.944662704233245 | 7.77e-16 | 6.85e-13 | pass | conditioning + running error | 3.76e-16 | 4.02e-16 |
| generic orbit L_z | chi=0.7, p=7.29503, e=0.1, x=0.1 | 0.344816912069979 | 0.344816912069978 | 1.28e-15 | 1.77e-12 | pass | conditioning + running error | 6.22e-16 | 6.55e-16 |
| generic orbit Q | chi=0.7, p=7.29503, e=0.1, x=0.1 | 11.8231743453225 | 11.8231743453225 | 9.41e-14 | 1.22e-10 | pass | conditioning + running error | 3.99e-14 | 5.42e-14 |
| generic orbit E | chi=0.7, p=25, e=0.1, x=0.1 | 0.980879903189896 | 0.980879903189895 | 3.33e-16 | 6.15e-13 | pass | conditioning + running error | 4.35e-17 | 2.90e-16 |
| generic orbit L_z | chi=0.7, p=25, e=0.1, x=0.1 | 0.531945578529548 | 0.531945578529542 | 5.77e-15 | 1.03e-11 | pass | conditioning + running error | 1.33e-15 | 4.45e-15 |
| generic orbit Q | chi=0.7, p=25, e=0.1, x=0.1 | 28.0320167291843 | 28.0320167291837 | 6.25e-13 | 1.08e-09 | pass | conditioning + running error | 1.37e-13 | 4.88e-13 |
| generic orbit E | chi=0.7, p=8.95234, e=0.1, x=-0.4 | 0.954792746504733 | 0.954792746504732 | 2.22e-16 | 9.14e-14 | pass | conditioning + running error | 2.63e-16 | 4.85e-16 |
| generic orbit L_z | chi=0.7, p=8.95234, e=0.1, x=-0.4 | -1.51862890771347 | -1.51862890771346 | 1.55e-15 | 1.21e-12 | pass | conditioning + running error | 2.82e-15 | 4.37e-15 |
| generic orbit Q | chi=0.7, p=8.95234, e=0.1, x=-0.4 | 12.1441006624497 | 12.1441006624496 | 2.66e-14 | 1.93e-11 | pass | conditioning + running error | 4.56e-14 | 7.22e-14 |
| generic orbit E | chi=0.7, p=25, e=0.1, x=-0.4 | 0.981016258959814 | 0.981016258959814 | 2.22e-16 | 8.08e-14 | pass | conditioning + running error | 9.82e-18 | 2.12e-16 |
| generic orbit L_z | chi=0.7, p=25, e=0.1, x=-0.4 | -2.14700369866991 | -2.14700369866991 | 4.44e-15 | 5.10e-12 | pass | conditioning + running error | 6.06e-15 | 1.05e-14 |
| generic orbit Q | chi=0.7, p=25, e=0.1, x=-0.4 | 24.2160097132556 | 24.2160097132555 | 9.95e-14 | 1.15e-10 | pass | conditioning + running error | 1.39e-13 | 2.38e-13 |
| generic orbit E | chi=0.7, p=10.6058, e=0.1, x=-0.9 | 0.961692253817911 | 0.96169225381791 | 6.66e-16 | 5.47e-14 | pass | conditioning + running error | 5.07e-16 | 1.59e-16 |
| generic orbit L_z | chi=0.7, p=10.6058, e=0.1, x=-0.9 | -3.69570690719778 | -3.69570690719777 | 1.51e-14 | 1.98e-12 | pass | conditioning + running error | 1.64e-14 | 1.32e-15 |
| generic orbit Q | chi=0.7, p=10.6058, e=0.1, x=-0.9 | 3.21078320968575 | 3.21078320968572 | 2.62e-14 | 3.46e-12 | pass | conditioning + running error | 2.74e-14 | 1.24e-15 |
| generic orbit E | chi=0.7, p=25, e=0.1, x=-0.9 | 0.981165341309092 | 0.981165341309091 | 3.33e-16 | 4.85e-14 | pass | conditioning + running error | 3.85e-17 | 3.72e-16 |
| generic orbit L_z | chi=0.7, p=25, e=0.1, x=-0.9 | -4.87741310801462 | -4.87741310801458 | 3.91e-14 | 6.55e-12 | pass | conditioning + running error | 1.61e-14 | 5.52e-14 |
| generic orbit Q | chi=0.7, p=25, e=0.1, x=-0.9 | 5.58364699783923 | 5.58364699783914 | 9.15e-14 | 1.50e-11 | pass | conditioning + running error | 3.68e-14 | 1.28e-13 |
| generic orbit E | chi=0.7, p=5.52926, e=0.5, x=0.9 | 0.93954866332214 | 0.93954866332214 | 1.11e-16 | 1.70e-14 | pass | conditioning + running error | 6.82e-17 | 4.28e-17 |
| generic orbit L_z | chi=0.7, p=5.52926, e=0.5, x=0.9 | 2.65920239583156 | 2.65920239583155 | 5.33e-15 | 6.86e-13 | pass | conditioning + running error | 5.60e-16 | 4.77e-15 |
| generic orbit Q | chi=0.7, p=5.52926, e=0.5, x=0.9 | 1.66962927756557 | 1.66962927756557 | 6.44e-15 | 8.70e-13 | pass | conditioning + running error | 4.01e-16 | 6.04e-15 |
| generic orbit E | chi=0.7, p=25, e=0.5, x=0.9 | 0.985280961768257 | 0.985280961768257 | 3.33e-16 | 1.25e-14 | pass | conditioning + running error | 1.57e-16 | 1.76e-16 |
| generic orbit L_z | chi=0.7, p=25, e=0.5, x=0.9 | 4.74510727319859 | 4.74510727319855 | 4.09e-14 | 5.15e-12 | pass | conditioning + running error | 2.34e-15 | 3.85e-14 |
| generic orbit Q | chi=0.7, p=25, e=0.5, x=0.9 | 5.28426147342633 | 5.28426147342623 | 9.06e-14 | 1.15e-11 | pass | conditioning + running error | 4.15e-15 | 8.64e-14 |
| generic orbit E | chi=0.7, p=7.13431, e=0.5, x=0.4 | 0.95367427892919 | 0.95367427892919 | 1.11e-16 | 2.35e-14 | pass | conditioning + running error | 4.18e-17 | 6.92e-17 |
| generic orbit L_z | chi=0.7, p=7.13431, e=0.5, x=0.4 | 1.35184750294489 | 1.35184750294489 | 2.22e-16 | 6.96e-13 | pass | conditioning + running error | 3.53e-16 | 5.75e-16 |
| generic orbit Q | chi=0.7, p=7.13431, e=0.5, x=0.4 | 9.63158328406848 | 9.63158328406848 | 0.00e+00 | 9.88e-12 | pass | conditioning + running error | 8.25e-15 | 8.25e-15 |
| generic orbit E | chi=0.7, p=25, e=0.5, x=0.4 | 0.9853494002939 | 0.9853494002939 | 2.22e-16 | 2.05e-14 | pass | conditioning + running error | 1.57e-16 | 6.51e-17 |
| generic orbit L_z | chi=0.7, p=25, e=0.5, x=0.4 | 2.12739425501849 | 2.1273942550185 | 1.33e-14 | 4.43e-12 | pass | conditioning + running error | 6.77e-15 | 2.01e-14 |
| generic orbit Q | chi=0.7, p=25, e=0.5, x=0.4 | 23.7724551883243 | 23.7724551883246 | 2.98e-13 | 9.89e-11 | pass | conditioning + running error | 1.47e-13 | 4.45e-13 |
| generic orbit E | chi=0.7, p=8.20509, e=0.5, x=0.1 | 0.959748905070561 | 0.959748905070561 | 0.00e+00 | 1.58e-13 | pass | conditioning + running error | 4.71e-17 | 4.71e-17 |
| generic orbit L_z | chi=0.7, p=8.20509, e=0.5, x=0.1 | 0.361536250247001 | 0.361536250247001 | 2.78e-16 | 1.72e-12 | pass | conditioning + running error | 5.96e-18 | 2.72e-16 |
| generic orbit Q | chi=0.7, p=8.20509, e=0.5, x=0.1 | 12.9784032412471 | 12.9784032412472 | 1.07e-14 | 1.24e-10 | pass | conditioning + running error | 1.15e-15 | 9.51e-15 |
| generic orbit E | chi=0.7, p=25, e=0.5, x=0.1 | 0.985393710908783 | 0.985393710908783 | 0.00e+00 | 1.51e-13 | pass | conditioning + running error | 3.91e-17 | 3.91e-17 |
| generic orbit L_z | chi=0.7, p=25, e=0.5, x=0.1 | 0.534810774715963 | 0.53481077471596 | 2.66e-15 | 9.85e-12 | pass | conditioning + running error | 3.59e-17 | 2.63e-15 |
| generic orbit Q | chi=0.7, p=25, e=0.5, x=0.1 | 28.3303014391332 | 28.3303014391329 | 3.09e-13 | 1.04e-09 | pass | conditioning + running error | 5.79e-15 | 3.03e-13 |
| generic orbit E | chi=0.7, p=10.0433, e=0.5, x=-0.4 | 0.967053244697723 | 0.967053244697723 | 0.00e+00 | 2.20e-14 | pass | conditioning + running error | 2.33e-17 | 2.33e-17 |
| generic orbit L_z | chi=0.7, p=10.0433, e=0.5, x=-0.4 | -1.58919163638248 | -1.58919163638248 | 4.44e-16 | 1.09e-12 | pass | conditioning + running error | 2.31e-16 | 2.13e-16 |
| generic orbit Q | chi=0.7, p=10.0433, e=0.5, x=-0.4 | 13.2857077818492 | 13.2857077818492 | 5.33e-15 | 1.81e-11 | pass | conditioning + running error | 2.61e-15 | 2.72e-15 |
| generic orbit E | chi=0.7, p=25, e=0.5, x=-0.4 | 0.985473305510223 | 0.985473305510223 | 0.00e+00 | 2.05e-14 | pass | conditioning + running error | 1.07e-16 | 1.07e-16 |
| generic orbit L_z | chi=0.7, p=25, e=0.5, x=-0.4 | -2.16032447578186 | -2.16032447578187 | 9.77e-15 | 4.38e-12 | pass | conditioning + running error | 3.42e-15 | 6.35e-15 |
| generic orbit Q | chi=0.7, p=25, e=0.5, x=-0.4 | 24.513631180551 | 24.5136311805513 | 2.24e-13 | 9.94e-11 | pass | conditioning + running error | 8.15e-14 | 1.42e-13 |
| generic orbit E | chi=0.7, p=11.8894, e=0.5, x=-0.9 | 0.972088047365647 | 0.972088047365647 | 1.11e-16 | 1.34e-14 | pass | conditioning + running error | 1.70e-16 | 5.87e-17 |
| generic orbit L_z | chi=0.7, p=11.8894, e=0.5, x=-0.9 | -3.86373430511944 | -3.86373430511945 | 8.88e-15 | 1.63e-12 | pass | conditioning + running error | 1.56e-15 | 7.32e-15 |
| generic orbit Q | chi=0.7, p=11.8894, e=0.5, x=-0.9 | 3.50685816523806 | 3.50685816523807 | 1.64e-14 | 2.99e-12 | pass | conditioning + running error | 3.90e-15 | 1.25e-14 |
| generic orbit E | chi=0.7, p=25, e=0.5, x=-0.9 | 0.985560547352116 | 0.985560547352115 | 3.33e-16 | 1.25e-14 | pass | conditioning + running error | 7.78e-17 | 2.55e-16 |
| generic orbit L_z | chi=0.7, p=25, e=0.5, x=-0.9 | -4.91204779905555 | -4.91204779905547 | 7.90e-14 | 5.05e-12 | pass | conditioning + running error | 8.58e-15 | 7.05e-14 |
| generic orbit Q | chi=0.7, p=25, e=0.5, x=-0.9 | 5.66237363498696 | 5.66237363498677 | 1.83e-13 | 1.17e-11 | pass | conditioning + running error | 1.94e-14 | 1.64e-13 |
| generic orbit E | chi=0.7, p=6.10252, e=0.8, x=0.9 | 0.971913213319769 | 0.971913213319769 | 0.00e+00 | 1.34e-14 | pass | conditioning + running error | 6.04e-18 | 6.04e-18 |
| generic orbit L_z | chi=0.7, p=6.10252, e=0.8, x=0.9 | 2.82494368097747 | 2.82494368097744 | 3.06e-14 | 3.51e-12 | pass | conditioning + running error | 2.23e-16 | 3.04e-14 |
| generic orbit Q | chi=0.7, p=6.10252, e=0.8, x=0.9 | 1.87708013355447 | 1.87708013355443 | 4.09e-14 | 4.67e-12 | pass | conditioning + running error | 1.60e-16 | 4.07e-14 |
| generic orbit E | chi=0.7, p=25, e=0.8, x=0.9 | 0.992865468276995 | 0.992865468276994 | 2.22e-16 | 1.04e-14 | pass | conditioning + running error | 4.20e-17 | 1.80e-16 |
| generic orbit L_z | chi=0.7, p=25, e=0.8, x=0.9 | 4.77807697950609 | 4.77807697950549 | 6.03e-13 | 2.59e-11 | pass | conditioning + running error | 2.67e-15 | 6.00e-13 |
| generic orbit Q | chi=0.7, p=25, e=0.8, x=0.9 | 5.3565134987699 | 5.35651349876855 | 1.35e-12 | 5.81e-11 | pass | conditioning + running error | 6.05e-15 | 1.35e-12 |
| generic orbit E | chi=0.7, p=7.74675, e=0.8, x=0.4 | 0.977994125737838 | 0.977994125737838 | 0.00e+00 | 1.90e-14 | pass | conditioning + running error | 1.17e-16 | 1.17e-16 |
| generic orbit L_z | chi=0.7, p=7.74675, e=0.8, x=0.4 | 1.42550917432191 | 1.42550917432191 | 4.22e-15 | 3.71e-12 | pass | conditioning + running error | 5.06e-16 | 3.71e-15 |
| generic orbit Q | chi=0.7, p=7.74675, e=0.8, x=0.4 | 10.6863170467918 | 10.6863170467918 | 6.04e-14 | 5.56e-11 | pass | conditioning + running error | 6.06e-15 | 5.43e-14 |
| generic orbit E | chi=0.7, p=25, e=0.8, x=0.4 | 0.99288158804466 | 0.99288158804466 | 0.00e+00 | 1.69e-14 | pass | conditioning + running error | 1.18e-16 | 1.18e-16 |
| generic orbit L_z | chi=0.7, p=25, e=0.8, x=0.4 | 2.14468329809465 | 2.14468329809446 | 1.92e-13 | 2.28e-11 | pass | conditioning + running error | 2.15e-17 | 1.92e-13 |
| generic orbit Q | chi=0.7, p=25, e=0.8, x=0.4 | 24.1540878781256 | 24.1540878781213 | 4.32e-12 | 5.13e-10 | pass | conditioning + running error | 1.57e-15 | 4.32e-12 |
| generic orbit E | chi=0.7, p=8.87003, e=0.8, x=0.1 | 0.980788657155129 | 0.980788657155129 | 1.11e-16 | 1.25e-13 | pass | conditioning + running error | 9.21e-17 | 1.89e-17 |
| generic orbit L_z | chi=0.7, p=8.87003, e=0.8, x=0.1 | 0.380280294473431 | 0.380280294473437 | 6.11e-15 | 9.51e-12 | pass | conditioning + running error | 7.05e-18 | 6.11e-15 |
| generic orbit Q | chi=0.7, p=8.87003, e=0.8, x=0.1 | 14.3351569403241 | 14.3351569403245 | 4.49e-13 | 7.17e-10 | pass | conditioning + running error | 3.21e-16 | 4.49e-13 |
| generic orbit E | chi=0.7, p=25, e=0.8, x=0.1 | 0.992892054165171 | 0.992892054165171 | 0.00e+00 | 1.24e-13 | pass | conditioning + running error | 3.89e-17 | 3.89e-17 |
| generic orbit L_z | chi=0.7, p=25, e=0.8, x=0.1 | 0.539565041433395 | 0.539565041433398 | 2.89e-15 | 5.19e-11 | pass | conditioning + running error | 1.01e-16 | 2.79e-15 |
| generic orbit Q | chi=0.7, p=25, e=0.8, x=0.1 | 28.8287845801581 | 28.8287845801584 | 2.88e-13 | 5.55e-09 | pass | conditioning + running error | 1.48e-14 | 2.73e-13 |
| generic orbit E | chi=0.7, p=10.8227, e=0.8, x=-0.4 | 0.984240742636586 | 0.984240742636586 | 2.22e-16 | 1.79e-14 | pass | conditioning + running error | 1.39e-18 | 2.23e-16 |
| generic orbit L_z | chi=0.7, p=10.8227, e=0.8, x=-0.4 | -1.66729466282101 | -1.66729466282096 | 4.33e-14 | 5.87e-12 | pass | conditioning + running error | 1.67e-16 | 4.31e-14 |
| generic orbit Q | chi=0.7, p=10.8227, e=0.8, x=-0.4 | 14.6071961346008 | 14.6071961346 | 7.53e-13 | 1.03e-10 | pass | conditioning + running error | 7.00e-16 | 7.54e-13 |
| generic orbit E | chi=0.7, p=25, e=0.8, x=-0.4 | 0.992910912554576 | 0.992910912554576 | 1.11e-16 | 1.70e-14 | pass | conditioning + running error | 5.71e-17 | 5.40e-17 |
| generic orbit L_z | chi=0.7, p=25, e=0.8, x=-0.4 | -2.18249113981556 | -2.18249113981548 | 7.99e-14 | 2.24e-11 | pass | conditioning + running error | 1.95e-15 | 7.80e-14 |
| generic orbit Q | chi=0.7, p=25, e=0.8, x=-0.4 | 25.0129698224713 | 25.0129698224695 | 1.84e-12 | 5.14e-10 | pass | conditioning + running error | 4.65e-14 | 1.79e-12 |
| generic orbit E | chi=0.7, p=12.7995, e=0.8, x=-0.9 | 0.986655925954509 | 0.986655925954509 | 0.00e+00 | 1.09e-14 | pass | conditioning + running error | 4.80e-17 | 4.80e-17 |
| generic orbit L_z | chi=0.7, p=12.7995, e=0.8, x=-0.9 | -4.04740358291093 | -4.0474035829109 | 3.38e-14 | 8.60e-12 | pass | conditioning + running error | 1.75e-15 | 3.55e-14 |
| generic orbit Q | chi=0.7, p=12.7995, e=0.8, x=-0.9 | 3.84503647764234 | 3.84503647764227 | 6.53e-14 | 1.64e-11 | pass | conditioning + running error | 3.81e-15 | 6.91e-14 |
| generic orbit E | chi=0.7, p=25, e=0.8, x=-0.9 | 0.992931669636397 | 0.992931669636397 | 0.00e+00 | 1.04e-14 | pass | conditioning + running error | 2.94e-17 | 2.94e-17 |
| generic orbit L_z | chi=0.7, p=25, e=0.8, x=-0.9 | -4.9698504960958 | -4.96985049609566 | 1.43e-13 | 2.50e-11 | pass | conditioning + running error | 8.06e-15 | 1.35e-13 |
| generic orbit Q | chi=0.7, p=25, e=0.8, x=-0.9 | 5.79500116452376 | 5.79500116452343 | 3.33e-13 | 5.84e-11 | pass | conditioning + running error | 1.73e-14 | 3.16e-13 |
| generic orbit E | chi=0.9, p=3.41335, e=0.1, x=0.9 | 0.879933691667057 | 0.879933691667056 | 4.44e-16 | 1.02e-13 | pass | conditioning + running error | 7.40e-17 | 5.18e-16 |
| generic orbit L_z | chi=0.9, p=3.41335, e=0.1, x=0.9 | 2.12456028818023 | 2.12456028818023 | 3.11e-15 | 9.15e-13 | pass | conditioning + running error | 6.61e-16 | 3.77e-15 |
| generic orbit Q | chi=0.9, p=3.41335, e=0.1, x=0.9 | 1.09352016954433 | 1.09352016954433 | 3.33e-15 | 9.39e-13 | pass | conditioning + running error | 3.40e-16 | 3.67e-15 |
| generic orbit E | chi=0.9, p=25, e=0.1, x=0.9 | 0.980628522618333 | 0.980628522618333 | 1.11e-16 | 4.80e-14 | pass | conditioning + running error | 1.16e-16 | 2.27e-16 |
| generic orbit L_z | chi=0.9, p=25, e=0.1, x=0.9 | 4.70546148365851 | 4.7054614836585 | 1.60e-14 | 6.59e-12 | pass | conditioning + running error | 1.88e-14 | 3.48e-14 |
| generic orbit Q | chi=0.9, p=25, e=0.1, x=0.9 | 5.19955895838188 | 5.19955895838185 | 3.55e-14 | 1.46e-11 | pass | conditioning + running error | 4.16e-14 | 7.71e-14 |
| generic orbit E | chi=0.9, p=5.4667, e=0.1, x=0.4 | 0.927295251810181 | 0.927295251810181 | 4.44e-16 | 1.11e-13 | pass | conditioning + running error | 3.01e-16 | 1.43e-16 |
| generic orbit L_z | chi=0.9, p=5.4667, e=0.1, x=0.4 | 1.21516522051167 | 1.21516522051167 | 1.33e-15 | 7.52e-13 | pass | conditioning + running error | 7.23e-16 | 6.10e-16 |
| generic orbit Q | chi=0.9, p=5.4667, e=0.1, x=0.4 | 7.84762923425733 | 7.84762923425735 | 1.78e-14 | 9.68e-12 | pass | conditioning + running error | 1.10e-14 | 6.81e-15 |
| generic orbit E | chi=0.9, p=25, e=0.1, x=0.4 | 0.980774287254482 | 0.980774287254481 | 5.55e-16 | 8.07e-14 | pass | conditioning + running error | 3.93e-16 | 1.62e-16 |
| generic orbit L_z | chi=0.9, p=25, e=0.1, x=0.4 | 2.11234244293976 | 2.11234244293974 | 2.04e-14 | 5.13e-12 | pass | conditioning + running error | 9.20e-15 | 1.12e-14 |
| generic orbit Q | chi=0.9, p=25, e=0.1, x=0.4 | 23.4513614852769 | 23.4513614852765 | 4.55e-13 | 1.14e-10 | pass | conditioning + running error | 2.02e-13 | 2.53e-13 |
| generic orbit E | chi=0.9, p=6.84166, e=0.1, x=0.1 | 0.941651477363038 | 0.941651477363039 | 2.22e-16 | 7.01e-13 | pass | conditioning + running error | 2.35e-16 | 4.57e-16 |
| generic orbit L_z | chi=0.9, p=6.84166, e=0.1, x=0.1 | 0.337173718662885 | 0.337173718662885 | 3.33e-16 | 1.66e-12 | pass | conditioning + running error | 4.61e-16 | 7.94e-16 |
| generic orbit Q | chi=0.9, p=6.84166, e=0.1, x=0.1 | 11.3457747910237 | 11.3457747910237 | 1.60e-14 | 1.13e-10 | pass | conditioning + running error | 2.86e-14 | 4.46e-14 |
| generic orbit E | chi=0.9, p=25, e=0.1, x=0.1 | 0.980870604065227 | 0.980870604065227 | 5.55e-16 | 6.16e-13 | pass | conditioning + running error | 3.19e-16 | 2.36e-16 |
| generic orbit L_z | chi=0.9, p=25, e=0.1, x=0.1 | 0.531522467886089 | 0.531522467886082 | 7.11e-15 | 1.03e-11 | pass | conditioning + running error | 3.61e-15 | 3.49e-15 |
| generic orbit Q | chi=0.9, p=25, e=0.1, x=0.1 | 27.9994835357991 | 27.9994835357983 | 7.60e-13 | 1.08e-09 | pass | conditioning + running error | 3.74e-13 | 3.86e-13 |
| generic orbit E | chi=0.9, p=9.09493, e=0.1, x=-0.4 | 0.955710986770931 | 0.95571098677093 | 2.22e-16 | 9.23e-14 | pass | conditioning + running error | 3.41e-16 | 1.19e-16 |
| generic orbit L_z | chi=0.9, p=9.09493, e=0.1, x=-0.4 | -1.53544625086647 | -1.53544625086646 | 2.66e-15 | 1.25e-12 | pass | conditioning + running error | 4.66e-15 | 2.00e-15 |
| generic orbit Q | chi=0.9, p=9.09493, e=0.1, x=-0.4 | 12.4363086170688 | 12.4363086170687 | 4.62e-14 | 2.02e-11 | pass | conditioning + running error | 7.47e-14 | 2.85e-14 |
| generic orbit E | chi=0.9, p=25, e=0.1, x=-0.4 | 0.981046965183697 | 0.981046965183697 | 0.00e+00 | 8.11e-14 | pass | conditioning + running error | 1.97e-16 | 1.97e-16 |
| generic orbit L_z | chi=0.9, p=25, e=0.1, x=-0.4 | -2.15094940859855 | -2.15094940859856 | 1.33e-15 | 5.11e-12 | pass | conditioning + running error | 1.25e-14 | 1.12e-14 |
| generic orbit Q | chi=0.9, p=25, e=0.1, x=-0.4 | 24.3151095095114 | 24.3151095095115 | 3.55e-14 | 1.15e-10 | pass | conditioning + running error | 2.89e-13 | 2.53e-13 |
| generic orbit E | chi=0.9, p=11.2762, e=0.1, x=-0.9 | 0.964013928930872 | 0.964013928930872 | 3.33e-16 | 5.52e-14 | pass | conditioning + running error | 3.54e-17 | 2.98e-16 |
| generic orbit L_z | chi=0.9, p=11.2762, e=0.1, x=-0.9 | -3.8092805796652 | -3.80928057966519 | 1.07e-14 | 2.19e-12 | pass | conditioning + running error | 6.16e-17 | 1.07e-14 |
| generic orbit Q | chi=0.9, p=11.2762, e=0.1, x=-0.9 | 3.41460254786884 | 3.41460254786882 | 1.87e-14 | 3.93e-12 | pass | conditioning + running error | 1.08e-15 | 1.97e-14 |
| generic orbit E | chi=0.9, p=25, e=0.1, x=-0.9 | 0.981244668331246 | 0.981244668331246 | 2.22e-16 | 4.88e-14 | pass | conditioning + running error | 6.51e-17 | 1.57e-16 |
| generic orbit L_z | chi=0.9, p=25, e=0.1, x=-0.9 | -4.90124002407743 | -4.90124002407741 | 1.95e-14 | 6.58e-12 | pass | conditioning + running error | 8.81e-16 | 2.04e-14 |
| generic orbit Q | chi=0.9, p=25, e=0.1, x=-0.9 | 5.64054494865587 | 5.64054494865583 | 4.62e-14 | 1.52e-11 | pass | conditioning + running error | 2.68e-15 | 4.89e-14 |
| generic orbit E | chi=0.9, p=3.96483, e=0.5, x=0.9 | 0.915827552206663 | 0.915827552206662 | 2.22e-16 | 6.50e-14 | pass | conditioning + running error | 1.50e-16 | 7.24e-17 |
| generic orbit L_z | chi=0.9, p=3.96483, e=0.5, x=0.9 | 2.27534908987275 | 2.27534908987275 | 2.66e-15 | 1.66e-12 | pass | conditioning + running error | 6.78e-16 | 1.99e-15 |
| generic orbit Q | chi=0.9, p=3.96483, e=0.5, x=0.9 | 1.23922599821288 | 1.23922599821288 | 2.66e-15 | 1.80e-12 | pass | conditioning + running error | 1.82e-16 | 2.48e-15 |
| generic orbit E | chi=0.9, p=25, e=0.5, x=0.9 | 0.985247462823319 | 0.985247462823318 | 1.11e-16 | 1.25e-14 | pass | conditioning + running error | 5.11e-17 | 1.62e-16 |
| generic orbit L_z | chi=0.9, p=25, e=0.5, x=0.9 | 4.72392899190415 | 4.72392899190417 | 1.95e-14 | 5.19e-12 | pass | conditioning + running error | 1.28e-14 | 6.74e-15 |
| generic orbit Q | chi=0.9, p=25, e=0.5, x=0.9 | 5.2390085376716 | 5.23900853767165 | 4.35e-14 | 1.15e-11 | pass | conditioning + running error | 2.98e-14 | 1.37e-14 |
| generic orbit E | chi=0.9, p=6.13954, e=0.5, x=0.4 | 0.946822744367795 | 0.946822744367795 | 0.00e+00 | 2.52e-14 | pass | conditioning + running error | 5.74e-17 | 5.74e-17 |
| generic orbit L_z | chi=0.9, p=6.13954, e=0.5, x=0.4 | 1.2763756879222 | 1.2763756879222 | 2.22e-16 | 5.92e-13 | pass | conditioning + running error | 7.91e-16 | 1.01e-15 |
| generic orbit Q | chi=0.9, p=6.13954, e=0.5, x=0.4 | 8.62339776815885 | 8.62339776815885 | 1.78e-15 | 7.95e-12 | pass | conditioning + running error | 1.28e-14 | 1.46e-14 |
| generic orbit E | chi=0.9, p=25, e=0.5, x=0.4 | 0.985332175646108 | 0.985332175646108 | 1.11e-16 | 2.05e-14 | pass | conditioning + running error | 4.77e-17 | 6.33e-17 |
| generic orbit L_z | chi=0.9, p=25, e=0.5, x=0.4 | 2.12247273176493 | 2.12247273176495 | 1.60e-14 | 4.44e-12 | pass | conditioning + running error | 1.29e-15 | 1.73e-14 |
| generic orbit Q | chi=0.9, p=25, e=0.5, x=0.4 | 23.6704887003742 | 23.6704887003745 | 3.59e-13 | 9.90e-11 | pass | conditioning + running error | 2.44e-14 | 3.83e-13 |
| generic orbit E | chi=0.9, p=7.65925, e=0.5, x=0.1 | 0.957236978797364 | 0.957236978797364 | 0.00e+00 | 1.60e-13 | pass | conditioning + running error | 5.89e-17 | 5.89e-17 |
| generic orbit L_z | chi=0.9, p=7.65925, e=0.5, x=0.1 | 0.35318435292643 | 0.35318435292643 | 4.44e-16 | 1.56e-12 | pass | conditioning + running error | 2.69e-16 | 1.75e-16 |
| generic orbit Q | chi=0.9, p=7.65925, e=0.5, x=0.1 | 12.4162964461886 | 12.4162964461886 | 1.95e-14 | 1.10e-10 | pass | conditioning + running error | 1.70e-14 | 2.50e-15 |
| generic orbit E | chi=0.9, p=25, e=0.5, x=0.1 | 0.985388268701154 | 0.985388268701154 | 0.00e+00 | 1.51e-13 | pass | conditioning + running error | 5.62e-17 | 5.62e-17 |
| generic orbit L_z | chi=0.9, p=25, e=0.5, x=0.1 | 0.534377067226301 | 0.534377067226306 | 4.88e-15 | 9.86e-12 | pass | conditioning + running error | 9.09e-16 | 5.79e-15 |
| generic orbit Q | chi=0.9, p=25, e=0.5, x=0.1 | 28.2935892346096 | 28.2935892346101 | 4.97e-13 | 1.04e-09 | pass | conditioning + running error | 9.38e-14 | 5.91e-13 |
| generic orbit E | chi=0.9, p=10.175, e=0.5, x=-0.4 | 0.967592886796007 | 0.967592886796007 | 0.00e+00 | 2.22e-14 | pass | conditioning + running error | 8.84e-18 | 8.84e-18 |
| generic orbit L_z | chi=0.9, p=10.175, e=0.5, x=-0.4 | -1.60544388643291 | -1.60544388643291 | 2.22e-16 | 1.11e-12 | pass | conditioning + running error | 1.62e-16 | 5.96e-17 |
| generic orbit Q | chi=0.9, p=10.175, e=0.5, x=-0.4 | 13.5749979098342 | 13.5749979098342 | 3.55e-15 | 1.88e-11 | pass | conditioning + running error | 5.07e-15 | 1.51e-15 |
| generic orbit E | chi=0.9, p=25, e=0.5, x=-0.4 | 0.985491221145341 | 0.985491221145341 | 0.00e+00 | 2.06e-14 | pass | conditioning + running error | 1.70e-16 | 1.70e-16 |
| generic orbit L_z | chi=0.9, p=25, e=0.5, x=-0.4 | -2.16476743481911 | -2.16476743481914 | 2.89e-14 | 4.39e-12 | pass | conditioning + running error | 8.70e-15 | 3.76e-14 |
| generic orbit Q | chi=0.9, p=25, e=0.5, x=-0.4 | 24.622245064872 | 24.6222450648727 | 6.54e-13 | 9.97e-11 | pass | conditioning + running error | 1.93e-13 | 8.47e-13 |
| generic orbit E | chi=0.9, p=12.6214, e=0.5, x=-0.9 | 0.973729987144844 | 0.973729987144844 | 2.22e-16 | 1.35e-14 | pass | conditioning + running error | 2.15e-16 | 6.69e-18 |
| generic orbit L_z | chi=0.9, p=12.6214, e=0.5, x=-0.9 | -3.97996913738127 | -3.97996913738126 | 1.20e-14 | 1.80e-12 | pass | conditioning + running error | 7.81e-15 | 4.18e-15 |
| generic orbit Q | chi=0.9, p=12.6214, e=0.5, x=-0.9 | 3.72357145895461 | 3.72357145895459 | 2.26e-14 | 3.38e-12 | pass | conditioning + running error | 1.36e-14 | 9.06e-15 |
| generic orbit E | chi=0.9, p=25, e=0.5, x=-0.9 | 0.98560701105508 | 0.98560701105508 | 0.00e+00 | 1.26e-14 | pass | conditioning + running error | 1.04e-16 | 1.04e-16 |
| generic orbit L_z | chi=0.9, p=25, e=0.5, x=-0.9 | -4.93853689714338 | -4.93853689714336 | 1.51e-14 | 5.06e-12 | pass | conditioning + running error | 7.45e-15 | 2.25e-14 |
| generic orbit Q | chi=0.9, p=25, e=0.5, x=-0.9 | 5.72530923103357 | 5.72530923103353 | 3.55e-14 | 1.18e-11 | pass | conditioning + running error | 1.73e-14 | 5.28e-14 |
| generic orbit E | chi=0.9, p=4.43346, e=0.8, x=0.9 | 0.961367288036976 | 0.961367288036976 | 0.00e+00 | 2.21e-14 | pass | conditioning + running error | 3.82e-17 | 3.82e-17 |
| generic orbit L_z | chi=0.9, p=4.43346, e=0.8, x=0.9 | 2.44459070841056 | 2.44459070841056 | 1.33e-15 | 3.62e-12 | pass | conditioning + running error | 5.36e-17 | 1.39e-15 |
| generic orbit Q | chi=0.9, p=4.43346, e=0.8, x=0.9 | 1.41344479954055 | 1.41344479954055 | 1.78e-15 | 4.16e-12 | pass | conditioning + running error | 3.33e-17 | 1.74e-15 |
| generic orbit E | chi=0.9, p=25, e=0.8, x=0.9 | 0.992857596203627 | 0.992857596203627 | 1.11e-16 | 1.04e-14 | pass | conditioning + running error | 4.03e-17 | 7.07e-17 |
| generic orbit L_z | chi=0.9, p=25, e=0.8, x=0.9 | 4.75438090889969 | 4.75438090890018 | 4.90e-13 | 2.62e-11 | pass | conditioning + running error | 2.56e-15 | 4.93e-13 |
| generic orbit Q | chi=0.9, p=25, e=0.8, x=0.9 | 5.30439575011954 | 5.30439575012063 | 1.09e-12 | 5.84e-11 | pass | conditioning + running error | 5.62e-15 | 1.10e-12 |
| generic orbit E | chi=0.9, p=6.62744, e=0.8, x=0.4 | 0.974432390535523 | 0.974432390535523 | 1.11e-16 | 2.02e-14 | pass | conditioning + running error | 3.54e-17 | 7.56e-17 |
| generic orbit L_z | chi=0.9, p=6.62744, e=0.8, x=0.4 | 1.34762342175569 | 1.34762342175567 | 1.20e-14 | 3.05e-12 | pass | conditioning + running error | 4.41e-16 | 1.15e-14 |
| generic orbit Q | chi=0.9, p=6.62744, e=0.8, x=0.4 | 9.56881427971232 | 9.56881427971214 | 1.72e-13 | 4.31e-11 | pass | conditioning + running error | 6.64e-15 | 1.66e-13 |
| generic orbit E | chi=0.9, p=25, e=0.8, x=0.4 | 0.99287752038497 | 0.99287752038497 | 0.00e+00 | 1.70e-14 | pass | conditioning + running error | 7.49e-17 | 7.49e-17 |
| generic orbit L_z | chi=0.9, p=25, e=0.8, x=0.4 | 2.13923936228127 | 2.13923936228139 | 1.22e-13 | 2.29e-11 | pass | conditioning + running error | 2.35e-16 | 1.22e-13 |
| generic orbit Q | chi=0.9, p=25, e=0.8, x=0.4 | 24.0354692617127 | 24.0354692617155 | 2.74e-12 | 5.14e-10 | pass | conditioning + running error | 1.28e-15 | 2.73e-12 |
| generic orbit E | chi=0.9, p=8.23382, e=0.8, x=0.1 | 0.979390189845226 | 0.979390189845226 | 2.22e-16 | 1.26e-13 | pass | conditioning + running error | 5.33e-17 | 1.69e-16 |
| generic orbit L_z | chi=0.9, p=8.23382, e=0.8, x=0.1 | 0.371494810218128 | 0.371494810218122 | 5.83e-15 | 8.44e-12 | pass | conditioning + running error | 3.39e-17 | 5.79e-15 |
| generic orbit Q | chi=0.9, p=8.23382, e=0.8, x=0.1 | 13.6955444029357 | 13.6955444029352 | 4.37e-13 | 6.22e-10 | pass | conditioning + running error | 3.46e-16 | 4.37e-13 |
| generic orbit E | chi=0.9, p=25, e=0.8, x=0.1 | 0.992890759424645 | 0.992890759424646 | 1.11e-16 | 1.24e-13 | pass | conditioning + running error | 1.89e-17 | 1.30e-16 |
| generic orbit L_z | chi=0.9, p=25, e=0.8, x=0.1 | 0.539112041537673 | 0.539112041537666 | 6.66e-15 | 5.20e-11 | pass | conditioning + running error | 5.38e-16 | 6.12e-15 |
| generic orbit Q | chi=0.9, p=25, e=0.8, x=0.1 | 28.7848988107259 | 28.7848988107251 | 7.28e-13 | 5.55e-09 | pass | conditioning + running error | 5.57e-14 | 6.73e-13 |
| generic orbit E | chi=0.9, p=10.9274, e=0.8, x=-0.4 | 0.984419180687935 | 0.984419180687935 | 0.00e+00 | 1.80e-14 | pass | conditioning + running error | 2.87e-17 | 2.87e-17 |
| generic orbit L_z | chi=0.9, p=10.9274, e=0.8, x=-0.4 | -1.68342080302734 | -1.68342080302733 | 7.33e-15 | 5.96e-12 | pass | conditioning + running error | 2.57e-16 | 7.58e-15 |
| generic orbit Q | chi=0.9, p=10.9274, e=0.8, x=-0.4 | 14.8990416040447 | 14.8990416040446 | 1.28e-13 | 1.05e-10 | pass | conditioning + running error | 5.94e-15 | 1.34e-13 |
| generic orbit E | chi=0.9, p=25, e=0.8, x=-0.4 | 0.992915154314341 | 0.992915154314341 | 2.22e-16 | 1.70e-14 | pass | conditioning + running error | 6.42e-17 | 1.58e-16 |
| generic orbit L_z | chi=0.9, p=25, e=0.8, x=-0.4 | -2.1877714499243 | -2.18777144992452 | 2.23e-13 | 2.24e-11 | pass | conditioning + running error | 6.34e-16 | 2.22e-13 |
| generic orbit Q | chi=0.9, p=25, e=0.8, x=-0.4 | 25.1379124701003 | 25.1379124701054 | 5.12e-12 | 5.16e-10 | pass | conditioning + running error | 1.90e-14 | 5.10e-12 |
| generic orbit E | chi=0.9, p=13.5616, e=0.8, x=-0.9 | 0.987411451070673 | 0.987411451070673 | 1.11e-16 | 1.10e-14 | pass | conditioning + running error | 3.38e-17 | 7.72e-17 |
| generic orbit L_z | chi=0.9, p=13.5616, e=0.8, x=-0.9 | -4.16647821498541 | -4.16647821498534 | 7.55e-14 | 9.44e-12 | pass | conditioning + running error | 6.64e-17 | 7.56e-14 |
| generic orbit Q | chi=0.9, p=13.5616, e=0.8, x=-0.9 | 4.07584139872268 | 4.07584139872254 | 1.47e-13 | 1.85e-11 | pass | conditioning + running error | 5.57e-16 | 1.48e-13 |
| generic orbit E | chi=0.9, p=25, e=0.8, x=-0.9 | 0.992942741916728 | 0.992942741916728 | 1.11e-16 | 1.05e-14 | pass | conditioning + running error | 4.66e-17 | 6.44e-17 |
| generic orbit L_z | chi=0.9, p=25, e=0.8, x=-0.9 | -5.00086224092046 | -5.00086224092085 | 3.90e-13 | 2.50e-11 | pass | conditioning + running error | 4.03e-16 | 3.90e-13 |
| generic orbit Q | chi=0.9, p=25, e=0.8, x=-0.9 | 5.86838480475181 | 5.86838480475273 | 9.13e-13 | 5.87e-11 | pass | conditioning + running error | 1.26e-15 | 9.12e-13 |
| generic orbit E | chi=0.99, p=2.19135, e=0.1, x=0.9 | 0.817499307572878 | 0.817499307572878 | 2.22e-16 | 6.03e-14 | pass | conditioning + running error | 3.02e-16 | 8.00e-17 |
| generic orbit L_z | chi=0.99, p=2.19135, e=0.1, x=0.9 | 1.73844889033037 | 1.73844889033037 | 8.88e-16 | 5.71e-13 | pass | conditioning + running error | 1.49e-15 | 6.01e-16 |
| generic orbit Q | chi=0.99, p=2.19135, e=0.1, x=0.9 | 0.770680066308993 | 0.770680066308994 | 5.55e-16 | 4.82e-13 | pass | conditioning + running error | 1.11e-15 | 5.52e-16 |
| generic orbit E | chi=0.99, p=25, e=0.1, x=0.9 | 0.980603440033196 | 0.980603440033196 | 5.55e-16 | 4.80e-14 | pass | conditioning + running error | 2.49e-16 | 3.07e-16 |
| generic orbit L_z | chi=0.99, p=25, e=0.1, x=0.9 | 4.69677125765 | 4.69677125764993 | 7.46e-14 | 6.60e-12 | pass | conditioning + running error | 2.76e-14 | 4.70e-14 |
| generic orbit Q | chi=0.99, p=25, e=0.1, x=0.9 | 5.18164216148418 | 5.18164216148401 | 1.65e-13 | 1.46e-11 | pass | conditioning + running error | 6.05e-14 | 1.05e-13 |
| generic orbit E | chi=0.99, p=4.92858, e=0.1, x=0.4 | 0.920723279474738 | 0.920723279474738 | 1.11e-16 | 1.23e-13 | pass | conditioning + running error | 4.17e-18 | 1.15e-16 |
| generic orbit L_z | chi=0.99, p=4.92858, e=0.1, x=0.4 | 1.1711345811727 | 1.1711345811727 | 1.11e-15 | 7.27e-13 | pass | conditioning + running error | 6.53e-17 | 1.18e-15 |
| generic orbit Q | chi=0.99, p=4.92858, e=0.1, x=0.4 | 7.32603042507908 | 7.32603042507906 | 1.24e-14 | 9.07e-12 | pass | conditioning + running error | 1.86e-15 | 1.43e-14 |
| generic orbit E | chi=0.99, p=25, e=0.1, x=0.4 | 0.980761076472513 | 0.980761076472513 | 2.22e-16 | 8.08e-14 | pass | conditioning + running error | 1.42e-16 | 7.96e-17 |
| generic orbit L_z | chi=0.99, p=25, e=0.1, x=0.4 | 2.11024134881606 | 2.11024134881606 | 2.66e-15 | 5.14e-12 | pass | conditioning + running error | 4.58e-16 | 3.12e-15 |
| generic orbit Q | chi=0.99, p=25, e=0.1, x=0.4 | 23.4102458574696 | 23.4102458574696 | 5.33e-14 | 1.14e-10 | pass | conditioning + running error | 1.68e-14 | 7.00e-14 |
| generic orbit E | chi=0.99, p=6.57602, e=0.1, x=0.1 | 0.93977254126882 | 0.93977254126882 | 0.00e+00 | 7.12e-13 | pass | conditioning + running error | 7.60e-17 | 7.60e-17 |
| generic orbit L_z | chi=0.99, p=6.57602, e=0.1, x=0.1 | 0.332789784158553 | 0.332789784158552 | 1.11e-16 | 1.60e-12 | pass | conditioning + running error | 4.59e-16 | 3.48e-16 |
| generic orbit Q | chi=0.99, p=6.57602, e=0.1, x=0.1 | 11.0775126785898 | 11.0775126785897 | 1.42e-14 | 1.07e-10 | pass | conditioning + running error | 2.89e-14 | 1.47e-14 |
| generic orbit E | chi=0.99, p=25, e=0.1, x=0.1 | 0.980866290788401 | 0.980866290788401 | 1.11e-16 | 6.16e-13 | pass | conditioning + running error | 2.98e-16 | 4.09e-16 |
| generic orbit L_z | chi=0.99, p=25, e=0.1, x=0.1 | 0.531319580606771 | 0.53131958060677 | 1.44e-15 | 1.03e-11 | pass | conditioning + running error | 4.07e-15 | 5.51e-15 |
| generic orbit Q | chi=0.99, p=25, e=0.1, x=0.1 | 27.9845247893811 | 27.9845247893809 | 1.78e-13 | 1.09e-09 | pass | conditioning + running error | 4.26e-13 | 6.04e-13 |
| generic orbit E | chi=0.99, p=9.14286, e=0.1, x=-0.4 | 0.956052344375263 | 0.956052344375263 | 1.11e-16 | 9.28e-14 | pass | conditioning + running error | 2.45e-16 | 1.34e-16 |
| generic orbit L_z | chi=0.99, p=9.14286, e=0.1, x=-0.4 | -1.54209597592341 | -1.54209597592342 | 3.55e-15 | 1.27e-12 | pass | conditioning + running error | 3.83e-15 | 2.74e-16 |
| generic orbit Q | chi=0.99, p=9.14286, e=0.1, x=-0.4 | 12.5555877101799 | 12.5555877101799 | 5.68e-14 | 2.06e-11 | pass | conditioning + running error | 6.22e-14 | 5.39e-15 |
| generic orbit E | chi=0.99, p=25, e=0.1, x=-0.4 | 0.981060779374824 | 0.981060779374824 | 1.11e-16 | 8.12e-14 | pass | conditioning + running error | 2.71e-16 | 1.60e-16 |
| generic orbit L_z | chi=0.99, p=25, e=0.1, x=-0.4 | -2.15269471030493 | -2.15269471030493 | 2.22e-15 | 5.12e-12 | pass | conditioning + running error | 9.63e-15 | 7.41e-15 |
| generic orbit Q | chi=0.99, p=25, e=0.1, x=-0.4 | 24.359885615349 | 24.3598856153491 | 5.33e-14 | 1.16e-10 | pass | conditioning + running error | 2.20e-13 | 1.67e-13 |
| generic orbit E | chi=0.99, p=11.5719, e=0.1, x=-0.9 | 0.964951991542942 | 0.964951991542942 | 3.33e-16 | 5.53e-14 | pass | conditioning + running error | 5.94e-16 | 2.61e-16 |
| generic orbit L_z | chi=0.99, p=11.5719, e=0.1, x=-0.9 | -3.85830536216759 | -3.8583053621676 | 1.11e-14 | 2.28e-12 | pass | conditioning + running error | 1.98e-14 | 8.70e-15 |
| generic orbit Q | chi=0.99, p=11.5719, e=0.1, x=-0.9 | 3.504724281551 | 3.50472428155102 | 2.00e-14 | 4.15e-12 | pass | conditioning + running error | 3.61e-14 | 1.62e-14 |
| generic orbit E | chi=0.99, p=25, e=0.1, x=-0.9 | 0.981281257768561 | 0.981281257768561 | 2.22e-16 | 4.89e-14 | pass | conditioning + running error | 4.50e-16 | 2.28e-16 |
| generic orbit L_z | chi=0.99, p=25, e=0.1, x=-0.9 | -4.91213154373196 | -4.91213154373197 | 7.99e-15 | 6.59e-12 | pass | conditioning + running error | 5.28e-14 | 4.48e-14 |
| generic orbit Q | chi=0.99, p=25, e=0.1, x=-0.9 | 5.66680372578988 | 5.6668037257899 | 1.78e-14 | 1.52e-11 | pass | conditioning + running error | 1.22e-13 | 1.05e-13 |
| generic orbit E | chi=0.99, p=2.62481, e=0.5, x=0.9 | 0.874710175628038 | 0.874710175628039 | 2.22e-16 | 2.28e-14 | pass | conditioning + running error | 6.61e-17 | 1.56e-16 |
| generic orbit L_z | chi=0.99, p=2.62481, e=0.5, x=0.9 | 1.90290882990566 | 1.90290882990566 | 1.33e-15 | 3.35e-13 | pass | conditioning + running error | 1.51e-16 | 1.18e-15 |
| generic orbit Q | chi=0.99, p=2.62481, e=0.5, x=0.9 | 0.893124428474238 | 0.893124428474239 | 9.99e-16 | 3.12e-13 | pass | conditioning + running error | 2.39e-16 | 7.60e-16 |
| generic orbit E | chi=0.99, p=25, e=0.5, x=0.9 | 0.985232905647689 | 0.98523290564769 | 2.22e-16 | 1.25e-14 | pass | conditioning + running error | 1.47e-16 | 7.47e-17 |
| generic orbit L_z | chi=0.99, p=25, e=0.5, x=0.9 | 4.71461780032136 | 4.71461780032135 | 8.88e-15 | 5.21e-12 | pass | conditioning + running error | 5.41e-16 | 9.42e-15 |
| generic orbit Q | chi=0.99, p=25, e=0.5, x=0.9 | 5.21934562698984 | 5.21934562698981 | 2.22e-14 | 1.16e-11 | pass | conditioning + running error | 3.86e-16 | 2.26e-14 |
| generic orbit E | chi=0.99, p=5.49308, e=0.5, x=0.4 | 0.941336293215604 | 0.941336293215604 | 1.11e-16 | 2.69e-14 | pass | conditioning + running error | 1.67e-16 | 5.56e-17 |
| generic orbit L_z | chi=0.99, p=5.49308, e=0.5, x=0.4 | 1.22844037535649 | 1.22844037535649 | 6.66e-16 | 5.31e-13 | pass | conditioning + running error | 6.60e-16 | 5.84e-18 |
| generic orbit Q | chi=0.99, p=5.49308, e=0.5, x=0.4 | 8.01635572567149 | 8.01635572567148 | 8.88e-15 | 6.88e-12 | pass | conditioning + running error | 7.58e-15 | 1.30e-15 |
| generic orbit E | chi=0.99, p=25, e=0.5, x=0.4 | 0.98532448230239 | 0.98532448230239 | 1.11e-16 | 2.05e-14 | pass | conditioning + running error | 1.00e-16 | 1.10e-17 |
| generic orbit L_z | chi=0.99, p=25, e=0.5, x=0.4 | 2.12024354483234 | 2.12024354483233 | 1.07e-14 | 4.45e-12 | pass | conditioning + running error | 3.30e-15 | 1.40e-14 |
| generic orbit Q | chi=0.99, p=25, e=0.5, x=0.4 | 23.6250085458412 | 23.6250085458409 | 2.38e-13 | 9.91e-11 | pass | conditioning + running error | 7.20e-14 | 3.10e-13 |
| generic orbit E | chi=0.99, p=7.33461, e=0.5, x=0.1 | 0.955611206132307 | 0.955611206132307 | 1.11e-16 | 1.61e-13 | pass | conditioning + running error | 2.40e-17 | 1.35e-16 |
| generic orbit L_z | chi=0.99, p=7.33461, e=0.5, x=0.1 | 0.348311403972548 | 0.348311403972549 | 9.44e-16 | 1.47e-12 | pass | conditioning + running error | 6.51e-17 | 8.79e-16 |
| generic orbit Q | chi=0.99, p=7.33461, e=0.5, x=0.1 | 12.094991540988 | 12.094991540988 | 5.51e-14 | 1.02e-10 | pass | conditioning + running error | 4.32e-15 | 5.07e-14 |
| generic orbit E | chi=0.99, p=25, e=0.5, x=0.1 | 0.98538574394567 | 0.98538574394567 | 0.00e+00 | 1.51e-13 | pass | conditioning + running error | 6.04e-18 | 6.04e-18 |
| generic orbit L_z | chi=0.99, p=25, e=0.5, x=0.1 | 0.534170786713081 | 0.534170786713081 | 1.11e-16 | 9.87e-12 | pass | conditioning + running error | 1.14e-16 | 3.37e-18 |
| generic orbit Q | chi=0.99, p=25, e=0.5, x=0.1 | 28.276657671415 | 28.276657671415 | 3.55e-14 | 1.05e-09 | pass | conditioning + running error | 1.25e-14 | 2.30e-14 |
| generic orbit E | chi=0.99, p=10.214, e=0.5, x=-0.4 | 0.967776083129014 | 0.967776083129014 | 1.11e-16 | 2.23e-14 | pass | conditioning + running error | 1.18e-16 | 7.14e-18 |
| generic orbit L_z | chi=0.99, p=10.214, e=0.5, x=-0.4 | -1.61173039425607 | -1.61173039425607 | 3.11e-15 | 1.12e-12 | pass | conditioning + running error | 2.04e-16 | 3.31e-15 |
| generic orbit Q | chi=0.99, p=10.214, e=0.5, x=-0.4 | 13.689997022827 | 13.689997022827 | 5.15e-14 | 1.90e-11 | pass | conditioning + running error | 6.10e-15 | 5.76e-14 |
| generic orbit E | chi=0.99, p=25, e=0.5, x=-0.4 | 0.985499279876062 | 0.985499279876062 | 1.11e-16 | 2.06e-14 | pass | conditioning + running error | 9.33e-17 | 1.78e-17 |
| generic orbit L_z | chi=0.99, p=25, e=0.5, x=-0.4 | -2.16674194337664 | -2.16674194337662 | 1.64e-14 | 4.39e-12 | pass | conditioning + running error | 6.06e-16 | 1.58e-14 |
| generic orbit Q | chi=0.99, p=25, e=0.5, x=-0.4 | 24.6712492173132 | 24.6712492173129 | 3.77e-13 | 9.99e-11 | pass | conditioning + running error | 1.59e-14 | 3.61e-13 |
| generic orbit E | chi=0.99, p=12.944, e=0.5, x=-0.9 | 0.974394355530145 | 0.974394355530145 | 0.00e+00 | 1.35e-14 | pass | conditioning + running error | 7.97e-17 | 7.97e-17 |
| generic orbit L_z | chi=0.99, p=12.944, e=0.5, x=-0.9 | -4.03016735696467 | -4.03016735696467 | 5.33e-15 | 1.87e-12 | pass | conditioning + running error | 2.76e-15 | 8.09e-15 |
| generic orbit Q | chi=0.99, p=12.944, e=0.5, x=-0.9 | 3.81932466240894 | 3.81932466240893 | 1.02e-14 | 3.56e-12 | pass | conditioning + running error | 6.03e-15 | 1.62e-14 |
| generic orbit E | chi=0.99, p=25, e=0.5, x=-0.9 | 0.985628455975354 | 0.985628455975354 | 1.11e-16 | 1.26e-14 | pass | conditioning + running error | 6.16e-17 | 4.94e-17 |
| generic orbit L_z | chi=0.99, p=25, e=0.5, x=-0.9 | -4.95066900855742 | -4.95066900855737 | 4.80e-14 | 5.06e-12 | pass | conditioning + running error | 6.17e-15 | 5.41e-14 |
| generic orbit Q | chi=0.99, p=25, e=0.5, x=-0.9 | 5.7543677387283 | 5.75436773872818 | 1.15e-13 | 1.18e-11 | pass | conditioning + running error | 1.36e-14 | 1.28e-13 |
| generic orbit E | chi=0.99, p=3.00919, e=0.8, x=0.9 | 0.943427004779052 | 0.943427004779052 | 3.33e-16 | 1.51e-13 | pass | conditioning + running error | 6.26e-17 | 2.70e-16 |
| generic orbit L_z | chi=0.99, p=3.00919, e=0.8, x=0.9 | 2.08861184002646 | 2.08861184002644 | 1.95e-14 | 1.37e-11 | pass | conditioning + running error | 2.31e-16 | 1.93e-14 |
| generic orbit Q | chi=0.99, p=3.00919, e=0.8, x=0.9 | 1.04372935768625 | 1.04372935768623 | 1.95e-14 | 1.34e-11 | pass | conditioning + running error | 4.72e-16 | 1.91e-14 |
| generic orbit E | chi=0.99, p=25, e=0.8, x=0.9 | 0.992854180181159 | 0.992854180181159 | 1.11e-16 | 1.05e-14 | pass | conditioning + running error | 6.48e-17 | 4.62e-17 |
| generic orbit L_z | chi=0.99, p=25, e=0.8, x=0.9 | 4.74402351832051 | 4.74402351832037 | 1.38e-13 | 2.63e-11 | pass | conditioning + running error | 2.18e-15 | 1.35e-13 |
| generic orbit Q | chi=0.99, p=25, e=0.8, x=0.9 | 5.28178055370747 | 5.28178055370716 | 3.08e-13 | 5.85e-11 | pass | conditioning + running error | 4.76e-15 | 3.03e-13 |
| generic orbit E | chi=0.99, p=5.87369, e=0.8, x=0.4 | 0.971346641298879 | 0.971346641298879 | 0.00e+00 | 2.13e-14 | pass | conditioning + running error | 6.31e-17 | 6.31e-17 |
| generic orbit L_z | chi=0.99, p=5.87369, e=0.8, x=0.4 | 1.29727014164687 | 1.29727014164687 | 6.66e-15 | 2.63e-12 | pass | conditioning + running error | 1.46e-16 | 6.81e-15 |
| generic orbit Q | chi=0.99, p=5.87369, e=0.8, x=0.4 | 8.88178033219 | 8.88178033219009 | 8.88e-14 | 3.58e-11 | pass | conditioning + running error | 2.66e-15 | 9.15e-14 |
| generic orbit E | chi=0.99, p=25, e=0.8, x=0.4 | 0.992875704822913 | 0.992875704822913 | 1.11e-16 | 1.70e-14 | pass | conditioning + running error | 1.98e-16 | 8.67e-17 |
| generic orbit L_z | chi=0.99, p=25, e=0.8, x=0.4 | 2.1367918310314 | 2.13679183103113 | 2.66e-13 | 2.29e-11 | pass | conditioning + running error | 2.57e-15 | 2.68e-13 |
| generic orbit Q | chi=0.99, p=25, e=0.8, x=0.4 | 23.982555328306 | 23.9825553283 | 5.96e-12 | 5.15e-10 | pass | conditioning + running error | 5.68e-14 | 6.01e-12 |
| generic orbit E | chi=0.99, p=7.84819, e=0.8, x=0.1 | 0.978444265904551 | 0.978444265904551 | 0.00e+00 | 1.27e-13 | pass | conditioning + running error | 4.44e-17 | 4.44e-17 |
| generic orbit L_z | chi=0.99, p=7.84819, e=0.8, x=0.1 | 0.36630735876046 | 0.366307358760458 | 2.55e-15 | 7.81e-12 | pass | conditioning + running error | 4.08e-17 | 2.59e-15 |
| generic orbit Q | chi=0.99, p=7.84819, e=0.8, x=0.1 | 13.3253071924861 | 13.3253071924859 | 1.92e-13 | 5.67e-10 | pass | conditioning + running error | 4.93e-15 | 1.97e-13 |
| generic orbit E | chi=0.99, p=25, e=0.8, x=0.1 | 0.992890158600664 | 0.992890158600664 | 1.11e-16 | 1.24e-13 | pass | conditioning + running error | 5.31e-18 | 1.06e-16 |
| generic orbit L_z | chi=0.99, p=25, e=0.8, x=0.1 | 0.538899306011367 | 0.538899306011391 | 2.45e-14 | 5.20e-11 | pass | conditioning + running error | 9.07e-17 | 2.44e-14 |
| generic orbit Q | chi=0.99, p=25, e=0.8, x=0.1 | 28.7645820354698 | 28.7645820354724 | 2.60e-12 | 5.55e-09 | pass | conditioning + running error | 2.06e-14 | 2.58e-12 |
| generic orbit E | chi=0.99, p=10.9495, e=0.8, x=-0.4 | 0.984465305422147 | 0.984465305422147 | 2.22e-16 | 1.81e-14 | pass | conditioning + running error | 8.25e-18 | 2.14e-16 |
| generic orbit L_z | chi=0.99, p=10.9495, e=0.8, x=-0.4 | -1.68957258592593 | -1.68957258592596 | 2.91e-14 | 5.99e-12 | pass | conditioning + running error | 3.91e-16 | 2.87e-14 |
| generic orbit Q | chi=0.99, p=10.9495, e=0.8, x=-0.4 | 15.0123217468817 | 15.0123217468822 | 5.19e-13 | 1.06e-10 | pass | conditioning + running error | 9.61e-15 | 5.09e-13 |
| generic orbit E | chi=0.99, p=25, e=0.8, x=-0.4 | 0.992917061889502 | 0.992917061889502 | 0.00e+00 | 1.70e-14 | pass | conditioning + running error | 3.37e-18 | 3.37e-18 |
| generic orbit L_z | chi=0.99, p=25, e=0.8, x=-0.4 | -2.19013163548531 | -2.19013163548523 | 8.08e-14 | 2.24e-11 | pass | conditioning + running error | 1.19e-15 | 7.96e-14 |
| generic orbit Q | chi=0.99, p=25, e=0.8, x=-0.4 | 25.194173285673 | 25.1941732856712 | 1.86e-12 | 5.16e-10 | pass | conditioning + running error | 2.37e-14 | 1.84e-12 |
| generic orbit E | chi=0.99, p=13.8969, e=0.8, x=-0.9 | 0.987717579659587 | 0.987717579659587 | 1.11e-16 | 1.10e-14 | pass | conditioning + running error | 6.40e-17 | 4.70e-17 |
| generic orbit L_z | chi=0.99, p=13.8969, e=0.8, x=-0.9 | -4.2179382982785 | -4.21793829827853 | 3.46e-14 | 9.82e-12 | pass | conditioning + running error | 1.78e-15 | 3.29e-14 |
| generic orbit Q | chi=0.99, p=13.8969, e=0.8, x=-0.9 | 4.17774469652574 | 4.17774469652581 | 6.75e-14 | 1.95e-11 | pass | conditioning + running error | 3.47e-15 | 6.40e-14 |
| generic orbit E | chi=0.99, p=25, e=0.8, x=-0.9 | 0.992947857761475 | 0.992947857761475 | 0.00e+00 | 1.05e-14 | pass | conditioning + running error | 4.55e-17 | 4.55e-17 |
| generic orbit L_z | chi=0.99, p=25, e=0.8, x=-0.9 | -5.01510353294315 | -5.01510353294297 | 1.86e-13 | 2.50e-11 | pass | conditioning + running error | 3.94e-15 | 1.90e-13 |
| generic orbit Q | chi=0.99, p=25, e=0.8, x=-0.9 | 5.90229630453399 | 5.90229630453355 | 4.38e-13 | 5.89e-11 | pass | conditioning + running error | 9.65e-15 | 4.48e-13 |
| polar orbit E | chi=0.3, p=7.98486, e=0.1, x=0 (polar) | 0.948957771229885 | 0.948957771229885 | 3.33e-16 | 2.17e-14 | pass | conditioning + running error | 3.88e-16 | 5.51e-17 |
| polar orbit Q | chi=0.3, p=7.98486, e=0.1, x=0 (polar) | 12.7921584009856 | 12.7921584009856 | 4.80e-14 | 3.30e-12 | pass | conditioning + running error | 4.93e-14 | 1.39e-15 |
| polar orbit E | chi=0.3, p=9.00868, e=0.5, x=0 (polar) | 0.963082151386996 | 0.963082151386996 | 1.11e-16 | 5.94e-15 | pass | conditioning + running error | 6.58e-17 | 4.52e-17 |
| polar orbit Q | chi=0.3, p=9.00868, e=0.5, x=0 (polar) | 14.0687591782723 | 14.0687591782723 | 0.00e+00 | 8.63e-13 | pass | conditioning + running error | 3.60e-15 | 3.60e-15 |
| polar orbit E | chi=0.3, p=9.77291, e=0.8, x=0 (polar) | 0.982503843221203 | 0.982503843221203 | 1.11e-16 | 4.99e-15 | pass | conditioning + running error | 5.58e-17 | 5.52e-17 |
| polar orbit Q | chi=0.3, p=9.77291, e=0.8, x=0 (polar) | 15.5433552419201 | 15.5433552419201 | 3.55e-15 | 6.82e-13 | pass | conditioning + running error | 2.38e-15 | 1.17e-15 |
| polar orbit E | chi=0.7, p=7.62507, e=0.1, x=0 (polar) | 0.947044974985142 | 0.947044974985141 | 4.44e-16 | 2.19e-14 | pass | conditioning + running error | 3.42e-16 | 1.02e-16 |
| polar orbit Q | chi=0.7, p=7.62507, e=0.1, x=0 (polar) | 12.4511696484553 | 12.4511696484553 | 3.73e-14 | 3.09e-12 | pass | conditioning + running error | 3.53e-14 | 1.97e-15 |
| polar orbit E | chi=0.7, p=8.56967, e=0.5, x=0 (polar) | 0.961454058832138 | 0.961454058832138 | 0.00e+00 | 5.97e-15 | pass | conditioning + running error | 8.30e-18 | 8.30e-18 |
| polar orbit Q | chi=0.7, p=8.56967, e=0.5, x=0 (polar) | 13.6553388842194 | 13.6553388842194 | 1.78e-15 | 8.04e-13 | pass | conditioning + running error | 4.09e-15 | 2.31e-15 |
| polar orbit E | chi=0.7, p=9.25538, e=0.8, x=0 (polar) | 0.981587077219808 | 0.981587077219808 | 1.11e-16 | 5.01e-15 | pass | conditioning + running error | 1.28e-16 | 1.70e-17 |
| polar orbit Q | chi=0.7, p=9.25538, e=0.8, x=0 (polar) | 15.0655833026114 | 15.0655833026114 | 8.88e-15 | 6.33e-13 | pass | conditioning + running error | 1.30e-14 | 4.14e-15 |
| polar orbit E | chi=0.9, p=7.2979, e=0.1, x=0 (polar) | 0.945197858964374 | 0.945197858964374 | 4.44e-16 | 2.22e-14 | pass | conditioning + running error | 3.47e-16 | 9.67e-17 |
| polar orbit Q | chi=0.9, p=7.2979, e=0.1, x=0 (polar) | 12.1467525799078 | 12.1467525799078 | 5.86e-14 | 2.91e-12 | pass | conditioning + running error | 5.77e-14 | 8.83e-16 |
| polar orbit E | chi=0.9, p=8.16702, e=0.5, x=0 (polar) | 0.959840219420248 | 0.959840219420248 | 2.22e-16 | 6.00e-15 | pass | conditioning + running error | 1.07e-16 | 1.15e-16 |
| polar orbit Q | chi=0.9, p=8.16702, e=0.5, x=0 (polar) | 13.2827266016416 | 13.2827266016416 | 5.33e-15 | 7.53e-13 | pass | conditioning + running error | 7.47e-15 | 2.14e-15 |
| polar orbit E | chi=0.9, p=8.77527, e=0.8, x=0 (polar) | 0.980648870603121 | 0.980648870603121 | 1.11e-16 | 5.02e-15 | pass | conditioning + running error | 3.90e-17 | 7.20e-17 |
| polar orbit Q | chi=0.9, p=8.77527, e=0.8, x=0 (polar) | 14.6318286710539 | 14.6318286710539 | 1.78e-15 | 5.91e-13 | pass | conditioning + running error | 2.50e-15 | 7.22e-16 |
| polar orbit E | chi=0.99, p=7.10431, e=0.1, x=0 (polar) | 0.94405503692363 | 0.94405503692363 | 1.11e-16 | 2.24e-14 | pass | conditioning + running error | 2.35e-16 | 1.23e-16 |
| polar orbit Q | chi=0.99, p=7.10431, e=0.1, x=0 (polar) | 11.9696666762118 | 11.9696666762118 | 2.49e-14 | 2.81e-12 | pass | conditioning + running error | 2.88e-14 | 3.96e-15 |
| polar orbit E | chi=0.99, p=7.92655, e=0.5, x=0 (polar) | 0.958816747547661 | 0.958816747547661 | 1.11e-16 | 6.02e-15 | pass | conditioning + running error | 7.13e-17 | 1.82e-16 |
| polar orbit Q | chi=0.99, p=7.92655, e=0.5, x=0 (polar) | 13.0638112922754 | 13.0638112922754 | 0.00e+00 | 7.23e-13 | pass | conditioning + running error | 3.38e-15 | 3.38e-15 |
| polar orbit E | chi=0.99, p=8.48485, e=0.8, x=0 (polar) | 0.980035047677948 | 0.980035047677948 | 0.00e+00 | 5.03e-15 | pass | conditioning + running error | 7.82e-17 | 7.82e-17 |
| polar orbit Q | chi=0.99, p=8.48485, e=0.8, x=0 (polar) | 14.3748784756147 | 14.3748784756147 | 1.78e-15 | 5.66e-13 | pass | conditioning + running error | 3.86e-15 | 2.09e-15 |
| generic orbit Upsilon_r | chi=0.3, p=6.81541, e=0.1, x=0.9 | 1.65397107333177 | 1.65397107333181 | 4.29e-14 | 7.49e-12 | pass | sensitivity budget | 3.67e-14 | 6.16e-15 |
| generic orbit Upsilon_theta | chi=0.3, p=6.81541, e=0.1, x=0.9 | 3.30414415943025 | 3.30414415943024 | 1.11e-14 | 1.25e-12 | pass | sensitivity budget | 1.08e-14 | 2.94e-16 |
| generic orbit Upsilon_phi | chi=0.3, p=6.81541, e=0.1, x=0.9 | 3.41199761174198 | 3.41199761174197 | 1.07e-14 | 1.26e-12 | pass | sensitivity budget | 1.03e-14 | 3.93e-16 |
| generic orbit Gamma | chi=0.3, p=6.81541, e=0.1, x=0.9 | 61.9015613623044 | 61.9015613623043 | 1.42e-14 | 8.95e-12 | pass | sensitivity budget | 3.04e-15 | 1.73e-14 |
| generic orbit Omega_r | chi=0.3, p=6.81541, e=0.1, x=0.9 | 0.0267193756818382 | 0.0267193756818389 | 6.97e-16 | 1.21e-13 | pass | sensitivity budget | 5.91e-16 | 1.07e-16 |
| generic orbit Omega_theta | chi=0.3, p=6.81541, e=0.1, x=0.9 | 0.0533773960900823 | 0.0533773960900821 | 1.67e-16 | 2.41e-14 | pass | sensitivity budget | 1.78e-16 | 1.10e-17 |
| generic orbit Omega_phi | chi=0.3, p=6.81541, e=0.1, x=0.9 | 0.055119734246635 | 0.0551197342466348 | 1.60e-16 | 2.41e-14 | pass | sensitivity budget | 1.67e-16 | 7.75e-18 |
| generic orbit Upsilon_r | chi=0.3, p=25, e=0.1, x=0.9 | 4.68757551674313 | 4.68757551674315 | 2.22e-14 | 3.42e-11 | pass | sensitivity budget | 3.89e-14 | 1.67e-14 |
| generic orbit Upsilon_theta | chi=0.3, p=25, e=0.1, x=0.9 | 5.29591717726918 | 5.29591717726915 | 3.46e-14 | 5.59e-12 | pass | sensitivity budget | 2.72e-14 | 7.44e-15 |
| generic orbit Upsilon_phi | chi=0.3, p=25, e=0.1, x=0.9 | 5.32047658724693 | 5.3204765872469 | 3.46e-14 | 5.59e-12 | pass | sensitivity budget | 2.62e-14 | 8.45e-15 |
| generic orbit Gamma | chi=0.3, p=25, e=0.1, x=0.9 | 675.455079913184 | 675.455079913184 | 0.00e+00 | 9.91e-11 | pass | sensitivity budget | 1.14e-13 | 1.14e-13 |
| generic orbit Omega_r | chi=0.3, p=25, e=0.1, x=0.9 | 0.00693987750798413 | 0.00693987750798416 | 3.30e-17 | 5.11e-14 | pass | sensitivity budget | 5.85e-17 | 2.55e-17 |
| generic orbit Omega_theta | chi=0.3, p=25, e=0.1, x=0.9 | 0.00784051720796868 | 0.00784051720796862 | 5.03e-17 | 8.79e-15 | pass | sensitivity budget | 3.83e-17 | 1.20e-17 |
| generic orbit Omega_phi | chi=0.3, p=25, e=0.1, x=0.9 | 0.00787687700554531 | 0.00787687700554526 | 5.20e-17 | 8.79e-15 | pass | sensitivity budget | 3.75e-17 | 1.45e-17 |
| generic orbit Upsilon_r | chi=0.3, p=7.85211, e=0.1, x=0.1 | 1.7797807990551 | 1.77978079905507 | 2.38e-14 | 7.11e-11 | pass | sensitivity budget | 1.82e-14 | 5.58e-15 |
| generic orbit Upsilon_theta | chi=0.3, p=7.85211, e=0.1, x=0.1 | 3.54673976185095 | 3.54673976185095 | 2.66e-15 | 1.91e-11 | pass | sensitivity budget | 1.53e-15 | 1.14e-15 |
| generic orbit Upsilon_phi | chi=0.3, p=7.85211, e=0.1, x=0.1 | 3.64345796037886 | 3.64345796037886 | 2.66e-15 | 1.92e-11 | pass | sensitivity budget | 1.06e-15 | 1.60e-15 |
| generic orbit Gamma | chi=0.3, p=7.85211, e=0.1, x=0.1 | 79.0715674162161 | 79.0715674162161 | 1.42e-14 | 2.43e-11 | pass | sensitivity budget | 5.31e-14 | 3.89e-14 |
| generic orbit Omega_r | chi=0.3, p=7.85211, e=0.1, x=0.1 | 0.0225084800670095 | 0.0225084800670092 | 3.05e-16 | 9.03e-13 | pass | sensitivity budget | 2.45e-16 | 6.06e-17 |
| generic orbit Omega_theta | chi=0.3, p=7.85211, e=0.1, x=0.1 | 0.044854805307977 | 0.044854805307977 | 2.08e-17 | 2.52e-13 | pass | sensitivity budget | 1.23e-17 | 3.31e-17 |
| generic orbit Omega_phi | chi=0.3, p=7.85211, e=0.1, x=0.1 | 0.0460779782092906 | 0.0460779782092907 | 2.08e-17 | 2.51e-13 | pass | sensitivity budget | 1.98e-17 | 4.06e-17 |
| generic orbit Upsilon_r | chi=0.3, p=25, e=0.1, x=0.1 | 4.6527895330645 | 4.65278953306473 | 2.27e-13 | 2.62e-10 | pass | sensitivity budget | 1.99e-13 | 2.83e-14 |
| generic orbit Upsilon_theta | chi=0.3, p=25, e=0.1, x=0.1 | 5.32692564475912 | 5.32692564475903 | 9.33e-14 | 1.01e-10 | pass | sensitivity budget | 6.59e-14 | 2.73e-14 |
| generic orbit Upsilon_phi | chi=0.3, p=25, e=0.1, x=0.1 | 5.35241359982307 | 5.35241359982297 | 9.33e-14 | 1.01e-10 | pass | sensitivity budget | 6.56e-14 | 2.77e-14 |
| generic orbit Gamma | chi=0.3, p=25, e=0.1, x=0.1 | 675.625045262559 | 675.625045262559 | 0.00e+00 | 2.44e-10 | pass | sensitivity budget | 7.59e-14 | 7.59e-14 |
| generic orbit Omega_r | chi=0.3, p=25, e=0.1, x=0.1 | 0.00688664454594981 | 0.00688664454595015 | 3.37e-16 | 3.90e-13 | pass | sensitivity budget | 2.93e-16 | 4.31e-17 |
| generic orbit Omega_theta | chi=0.3, p=25, e=0.1, x=0.1 | 0.00788444075913288 | 0.00788444075913275 | 1.37e-16 | 1.51e-13 | pass | sensitivity budget | 9.77e-17 | 3.93e-17 |
| generic orbit Omega_phi | chi=0.3, p=25, e=0.1, x=0.1 | 0.0079221657594754 | 0.00792216575947527 | 1.37e-16 | 1.51e-13 | pass | sensitivity budget | 9.75e-17 | 3.96e-17 |
| generic orbit Upsilon_r | chi=0.3, p=8.52045, e=0.1, x=-0.4 | 1.86009799026402 | 1.860097990264 | 2.55e-14 | 1.43e-11 | pass | sensitivity budget | 1.19e-14 | 1.36e-14 |
| generic orbit Upsilon_theta | chi=0.3, p=8.52045, e=0.1, x=-0.4 | 3.69057081416242 | 3.69057081416242 | 4.44e-15 | 2.60e-12 | pass | sensitivity budget | 6.80e-16 | 3.76e-15 |
| generic orbit Upsilon_phi | chi=0.3, p=8.52045, e=0.1, x=-0.4 | -3.59976894569563 | -3.59976894569563 | 6.22e-15 | 2.62e-12 | pass | sensitivity budget | 2.07e-15 | 4.15e-15 |
| generic orbit Gamma | chi=0.3, p=8.52045, e=0.1, x=-0.4 | 91.253466554156 | 91.2534665541559 | 1.42e-14 | 1.21e-11 | pass | sensitivity budget | 1.82e-14 | 4.02e-15 |
| generic orbit Omega_r | chi=0.3, p=8.52045, e=0.1, x=-0.4 | 0.0203838611343067 | 0.0203838611343065 | 2.74e-16 | 1.56e-13 | pass | sensitivity budget | 1.25e-16 | 1.49e-16 |
| generic orbit Omega_theta | chi=0.3, p=8.52045, e=0.1, x=-0.4 | 0.0404430752444038 | 0.0404430752444039 | 5.55e-17 | 3.10e-14 | pass | sensitivity budget | 1.75e-17 | 3.81e-17 |
| generic orbit Omega_phi | chi=0.3, p=8.52045, e=0.1, x=-0.4 | -0.039448024076535 | -0.0394480240765351 | 7.63e-17 | 3.11e-14 | pass | sensitivity budget | 3.06e-17 | 4.57e-17 |
| generic orbit Upsilon_r | chi=0.3, p=25, e=0.1, x=-0.4 | 4.62947302978266 | 4.62947302978284 | 1.82e-13 | 4.79e-11 | pass | sensitivity budget | 1.47e-13 | 3.47e-14 |
| generic orbit Upsilon_theta | chi=0.3, p=25, e=0.1, x=-0.4 | 5.34728828623465 | 5.34728828623458 | 7.02e-14 | 1.10e-11 | pass | sensitivity budget | 6.07e-14 | 9.43e-15 |
| generic orbit Upsilon_phi | chi=0.3, p=25, e=0.1, x=-0.4 | -5.32121852253027 | -5.3212185225302 | 7.11e-14 | 1.10e-11 | pass | sensitivity budget | 6.12e-14 | 9.87e-15 |
| generic orbit Gamma | chi=0.3, p=25, e=0.1, x=-0.4 | 675.702567280028 | 675.702567280028 | 1.14e-13 | 1.05e-10 | pass | sensitivity budget | 1.36e-13 | 2.25e-14 |
| generic orbit Omega_r | chi=0.3, p=25, e=0.1, x=-0.4 | 0.00685134740336733 | 0.0068513474033676 | 2.71e-16 | 7.13e-14 | pass | sensitivity budget | 2.19e-16 | 5.13e-17 |
| generic orbit Omega_theta | chi=0.3, p=25, e=0.1, x=-0.4 | 0.00791367170286124 | 0.00791367170286114 | 1.02e-16 | 1.68e-14 | pass | sensitivity budget | 8.89e-17 | 1.35e-17 |
| generic orbit Omega_phi | chi=0.3, p=25, e=0.1, x=-0.4 | -0.00787508998811458 | -0.00787508998811448 | 1.04e-16 | 1.68e-14 | pass | sensitivity budget | 8.85e-17 | 1.55e-17 |
| generic orbit Upsilon_r | chi=0.3, p=7.73003, e=0.5, x=0.9 | 1.97244611606684 | 1.97244611606682 | 1.87e-14 | 1.04e-11 | pass | sensitivity budget | 1.39e-14 | 4.70e-15 |
| generic orbit Upsilon_theta | chi=0.3, p=7.73003, e=0.5, x=0.9 | 3.47460541685046 | 3.47460541685047 | 4.88e-15 | 1.30e-12 | pass | sensitivity budget | 1.68e-15 | 3.20e-15 |
| generic orbit Upsilon_phi | chi=0.3, p=7.73003, e=0.5, x=0.9 | 3.57690143668833 | 3.57690143668834 | 4.44e-15 | 1.41e-12 | pass | sensitivity budget | 1.23e-15 | 3.21e-15 |
| generic orbit Gamma | chi=0.3, p=7.73003, e=0.5, x=0.9 | 102.203721511792 | 102.203721511792 | 2.27e-13 | 1.53e-10 | pass | sensitivity budget | 1.72e-13 | 5.53e-14 |
| generic orbit Omega_r | chi=0.3, p=7.73003, e=0.5, x=0.9 | 0.0192991613895319 | 0.0192991613895317 | 1.39e-16 | 7.57e-14 | pass | sensitivity budget | 1.04e-16 | 3.49e-17 |
| generic orbit Omega_theta | chi=0.3, p=7.73003, e=0.5, x=0.9 | 0.0339968580933678 | 0.0339968580933679 | 1.18e-16 | 6.11e-14 | pass | sensitivity budget | 7.11e-17 | 4.69e-17 |
| generic orbit Omega_phi | chi=0.3, p=7.73003, e=0.5, x=0.9 | 0.0349977611752195 | 0.0349977611752196 | 1.25e-16 | 6.37e-14 | pass | sensitivity budget | 7.34e-17 | 5.15e-17 |
| generic orbit Upsilon_r | chi=0.3, p=25, e=0.5, x=0.9 | 4.70871365366242 | 4.7087136536625 | 7.28e-14 | 4.16e-11 | pass | sensitivity budget | 4.88e-14 | 2.40e-14 |
| generic orbit Upsilon_theta | chi=0.3, p=25, e=0.5, x=0.9 | 5.3218618902209 | 5.32186189022084 | 6.04e-14 | 5.83e-12 | pass | sensitivity budget | 2.36e-15 | 5.80e-14 |
| generic orbit Upsilon_phi | chi=0.3, p=25, e=0.5, x=0.9 | 5.34693540215434 | 5.34693540215428 | 6.04e-14 | 5.85e-12 | pass | sensitivity budget | 2.11e-15 | 5.83e-14 |
| generic orbit Gamma | chi=0.3, p=25, e=0.5, x=0.9 | 998.021391793395 | 998.021391793398 | 3.30e-12 | 1.79e-09 | pass | sensitivity budget | 2.56e-12 | 7.32e-13 |
| generic orbit Omega_r | chi=0.3, p=25, e=0.5, x=0.9 | 0.00471804882378433 | 0.00471804882378438 | 5.72e-17 | 3.42e-14 | pass | sensitivity budget | 3.69e-17 | 2.03e-17 |
| generic orbit Omega_theta | chi=0.3, p=25, e=0.5, x=0.9 | 0.00533241264564257 | 0.00533241264564249 | 7.81e-17 | 1.49e-14 | pass | sensitivity budget | 1.63e-17 | 6.18e-17 |
| generic orbit Omega_phi | chi=0.3, p=25, e=0.5, x=0.9 | 0.00535753586658715 | 0.00535753586658707 | 7.89e-17 | 1.50e-14 | pass | sensitivity budget | 1.63e-17 | 6.26e-17 |
| generic orbit Upsilon_r | chi=0.3, p=8.86274, e=0.5, x=0.1 | 2.11615989826026 | 2.11615989826029 | 2.26e-14 | 4.10e-11 | pass | sensitivity budget | 9.20e-15 | 3.18e-14 |
| generic orbit Upsilon_theta | chi=0.3, p=8.86274, e=0.5, x=0.1 | 3.72059320198205 | 3.72059320198206 | 4.88e-15 | 1.95e-11 | pass | sensitivity budget | 3.39e-16 | 5.22e-15 |
| generic orbit Upsilon_phi | chi=0.3, p=8.86274, e=0.5, x=0.1 | 3.81238806051732 | 3.81238806051732 | 4.44e-15 | 1.99e-11 | pass | sensitivity budget | 1.20e-15 | 3.24e-15 |
| generic orbit Gamma | chi=0.3, p=8.86274, e=0.5, x=0.1 | 131.029842649727 | 131.029842649727 | 3.13e-13 | 6.97e-10 | pass | sensitivity budget | 1.57e-13 | 4.70e-13 |
| generic orbit Omega_r | chi=0.3, p=8.86274, e=0.5, x=0.1 | 0.0161502132298003 | 0.0161502132298004 | 1.32e-16 | 2.29e-13 | pass | sensitivity budget | 5.16e-17 | 1.83e-16 |
| generic orbit Omega_theta | chi=0.3, p=8.86274, e=0.5, x=0.1 | 0.0283950062576818 | 0.0283950062576818 | 3.12e-17 | 2.97e-13 | pass | sensitivity budget | 2.98e-17 | 6.10e-17 |
| generic orbit Omega_phi | chi=0.3, p=8.86274, e=0.5, x=0.1 | 0.0290955707754967 | 0.0290955707754967 | 3.47e-17 | 3.04e-13 | pass | sensitivity budget | 4.42e-17 | 7.89e-17 |
| generic orbit Upsilon_r | chi=0.3, p=25, e=0.5, x=0.1 | 4.67585700026751 | 4.67585700026751 | 0.00e+00 | 1.33e-10 | pass | sensitivity budget | 5.75e-14 | 5.75e-14 |
| generic orbit Upsilon_theta | chi=0.3, p=25, e=0.5, x=0.1 | 5.35587155341884 | 5.35587155341883 | 9.77e-15 | 9.84e-11 | pass | sensitivity budget | 4.22e-15 | 5.55e-15 |
| generic orbit Upsilon_phi | chi=0.3, p=25, e=0.5, x=0.1 | 5.38193508859844 | 5.38193508859843 | 1.07e-14 | 9.85e-11 | pass | sensitivity budget | 2.18e-15 | 8.48e-15 |
| generic orbit Gamma | chi=0.3, p=25, e=0.5, x=0.1 | 996.865994416342 | 996.865994416342 | 3.41e-13 | 5.52e-09 | pass | sensitivity budget | 2.52e-12 | 2.17e-12 |
| generic orbit Omega_r | chi=0.3, p=25, e=0.5, x=0.1 | 0.00469055723282566 | 0.00469055723282566 | 1.73e-18 | 1.08e-13 | pass | sensitivity budget | 4.56e-17 | 4.73e-17 |
| generic orbit Omega_theta | chi=0.3, p=25, e=0.5, x=0.1 | 0.00537270965547848 | 0.00537270965547847 | 1.13e-17 | 1.28e-13 | pass | sensitivity budget | 1.78e-17 | 6.55e-18 |
| generic orbit Omega_phi | chi=0.3, p=25, e=0.5, x=0.1 | 0.00539885513072349 | 0.00539885513072347 | 1.21e-17 | 1.28e-13 | pass | sensitivity budget | 1.54e-17 | 3.31e-18 |
| generic orbit Upsilon_r | chi=0.3, p=9.59908, e=0.5, x=-0.4 | 2.20846378555727 | 2.2084637855573 | 2.62e-14 | 1.63e-11 | pass | sensitivity budget | 3.01e-14 | 3.94e-15 |
| generic orbit Upsilon_theta | chi=0.3, p=9.59908, e=0.5, x=-0.4 | 3.86742841056924 | 3.86742841056925 | 8.88e-15 | 2.76e-12 | pass | sensitivity budget | 1.13e-15 | 1.00e-14 |
| generic orbit Upsilon_phi | chi=0.3, p=9.59908, e=0.5, x=-0.4 | -3.78129193236935 | -3.78129193236936 | 9.77e-15 | 2.88e-12 | pass | sensitivity budget | 2.91e-16 | 1.01e-14 |
| generic orbit Gamma | chi=0.3, p=9.59908, e=0.5, x=-0.4 | 151.72638557386 | 151.726385573861 | 4.55e-13 | 3.20e-10 | pass | sensitivity budget | 5.26e-13 | 7.08e-14 |
| generic orbit Omega_r | chi=0.3, p=9.59908, e=0.5, x=-0.4 | 0.0145555684148437 | 0.0145555684148438 | 1.28e-16 | 7.85e-14 | pass | sensitivity budget | 1.47e-16 | 1.91e-17 |
| generic orbit Omega_theta | chi=0.3, p=9.59908, e=0.5, x=-0.4 | 0.0254894914680913 | 0.0254894914680913 | 1.73e-17 | 7.01e-14 | pass | sensitivity budget | 9.46e-17 | 7.73e-17 |
| generic orbit Omega_phi | chi=0.3, p=9.59908, e=0.5, x=-0.4 | -0.0249217821809155 | -0.0249217821809155 | 1.04e-17 | 6.80e-14 | pass | sensitivity budget | 8.97e-17 | 7.93e-17 |
| generic orbit Upsilon_r | chi=0.3, p=25, e=0.5, x=-0.4 | 4.65371844248806 | 4.65371844248806 | 0.00e+00 | 4.75e-11 | pass | sensitivity budget | 2.08e-14 | 2.08e-14 |
| generic orbit Upsilon_theta | chi=0.3, p=25, e=0.5, x=-0.4 | 5.3781994600657 | 5.37819946006567 | 3.64e-14 | 1.10e-11 | pass | sensitivity budget | 1.07e-14 | 4.71e-14 |
| generic orbit Upsilon_phi | chi=0.3, p=25, e=0.5, x=-0.4 | -5.35151149884695 | -5.35151149884692 | 3.73e-14 | 1.11e-11 | pass | sensitivity budget | 1.16e-14 | 4.89e-14 |
| generic orbit Gamma | chi=0.3, p=25, e=0.5, x=-0.4 | 996.020940955112 | 996.020940955112 | 1.14e-13 | 2.08e-09 | pass | sensitivity budget | 1.03e-12 | 9.21e-13 |
| generic orbit Omega_r | chi=0.3, p=25, e=0.5, x=-0.4 | 0.00467230983921431 | 0.00467230983921431 | 0.00e+00 | 3.88e-14 | pass | sensitivity budget | 1.62e-17 | 1.62e-17 |
| generic orbit Omega_theta | chi=0.3, p=25, e=0.5, x=-0.4 | 0.00539968512600588 | 0.00539968512600585 | 3.73e-17 | 2.19e-14 | pass | sensitivity budget | 5.01e-18 | 4.23e-17 |
| generic orbit Omega_phi | chi=0.3, p=25, e=0.5, x=-0.4 | -0.00537289054757749 | -0.00537289054757745 | 3.82e-17 | 2.18e-14 | pass | sensitivity budget | 5.77e-18 | 4.39e-17 |
| generic orbit Upsilon_r | chi=0.3, p=8.43636, e=0.8, x=0.9 | 2.20342751171611 | 2.20342751171612 | 8.88e-16 | 4.78e-11 | pass | sensitivity budget | 1.86e-14 | 1.95e-14 |
| generic orbit Upsilon_theta | chi=0.3, p=8.43636, e=0.8, x=0.9 | 3.66221372396704 | 3.66221372396705 | 1.11e-14 | 5.58e-12 | pass | sensitivity budget | 2.37e-16 | 1.09e-14 |
| generic orbit Upsilon_phi | chi=0.3, p=8.43636, e=0.8, x=0.9 | 3.76650237801811 | 3.76650237801812 | 1.15e-14 | 6.48e-12 | pass | sensitivity budget | 6.76e-16 | 1.09e-14 |
| generic orbit Gamma | chi=0.3, p=8.43636, e=0.8, x=0.9 | 301.416561180188 | 301.416561180188 | 3.98e-13 | 4.41e-09 | pass | sensitivity budget | 2.09e-12 | 2.49e-12 |
| generic orbit Omega_r | chi=0.3, p=8.43636, e=0.8, x=0.9 | 0.00731024036333192 | 0.00731024036333191 | 6.07e-18 | 5.46e-14 | pass | sensitivity budget | 1.06e-17 | 4.52e-18 |
| generic orbit Omega_theta | chi=0.3, p=8.43636, e=0.8, x=0.9 | 0.0121500083128404 | 0.0121500083128404 | 2.08e-17 | 1.95e-13 | pass | sensitivity budget | 8.43e-17 | 6.35e-17 |
| generic orbit Omega_phi | chi=0.3, p=8.43636, e=0.8, x=0.9 | 0.0124960034155737 | 0.0124960034155737 | 2.08e-17 | 2.03e-13 | pass | sensitivity budget | 8.87e-17 | 6.79e-17 |
| generic orbit Upsilon_r | chi=0.3, p=25, e=0.8, x=0.9 | 4.74375355658532 | 4.74375355658504 | 2.77e-13 | 1.56e-10 | pass | sensitivity budget | 2.95e-14 | 2.48e-13 |
| generic orbit Upsilon_theta | chi=0.3, p=25, e=0.8, x=0.9 | 5.36485334001633 | 5.36485334001658 | 2.50e-13 | 2.86e-11 | pass | sensitivity budget | 4.41e-15 | 2.54e-13 |
| generic orbit Upsilon_phi | chi=0.3, p=25, e=0.8, x=0.9 | 5.39077603084512 | 5.39077603084537 | 2.50e-13 | 2.88e-11 | pass | sensitivity budget | 3.55e-15 | 2.54e-13 |
| generic orbit Gamma | chi=0.3, p=25, e=0.8, x=0.9 | 2875.15972631566 | 2875.15972631557 | 9.69e-11 | 5.42e-08 | pass | sensitivity budget | 1.08e-11 | 8.61e-11 |
| generic orbit Omega_r | chi=0.3, p=25, e=0.8, x=0.9 | 0.00164990957308106 | 0.00164990957308102 | 4.10e-17 | 2.39e-14 | pass | sensitivity budget | 4.15e-18 | 3.68e-17 |
| generic orbit Omega_theta | chi=0.3, p=25, e=0.8, x=0.9 | 0.00186593227879241 | 0.00186593227879256 | 1.50e-16 | 4.50e-14 | pass | sensitivity budget | 5.58e-18 | 1.44e-16 |
| generic orbit Omega_phi | chi=0.3, p=25, e=0.8, x=0.9 | 0.0018749483660002 | 0.00187494836600035 | 1.50e-16 | 4.52e-14 | pass | sensitivity budget | 5.78e-18 | 1.44e-16 |
| generic orbit Upsilon_r | chi=0.3, p=9.61944, e=0.8, x=0.1 | 2.35569865619768 | 2.35569865619757 | 1.03e-13 | 1.63e-10 | pass | sensitivity budget | 6.91e-14 | 3.39e-14 |
| generic orbit Upsilon_theta | chi=0.3, p=9.61944, e=0.8, x=0.1 | 3.91195770496441 | 3.91195770496439 | 2.53e-14 | 1.08e-10 | pass | sensitivity budget | 2.59e-17 | 2.53e-14 |
| generic orbit Upsilon_phi | chi=0.3, p=9.61944, e=0.8, x=0.1 | 4.00559579514924 | 4.00559579514922 | 2.31e-14 | 1.11e-10 | pass | sensitivity budget | 3.65e-15 | 2.67e-14 |
| generic orbit Gamma | chi=0.3, p=9.61944, e=0.8, x=0.1 | 387.953098180953 | 387.953098180941 | 1.22e-11 | 1.80e-08 | pass | sensitivity budget | 7.67e-12 | 4.49e-12 |
| generic orbit Omega_r | chi=0.3, p=9.61944, e=0.8, x=0.1 | 0.00607212229324409 | 0.00607212229324401 | 7.46e-17 | 1.40e-13 | pass | sensitivity budget | 5.77e-17 | 1.69e-17 |
| generic orbit Omega_theta | chi=0.3, p=9.61944, e=0.8, x=0.1 | 0.0100835841324813 | 0.0100835841324815 | 2.52e-16 | 7.44e-13 | pass | sensitivity budget | 2.00e-16 | 5.20e-17 |
| generic orbit Omega_phi | chi=0.3, p=9.61944, e=0.8, x=0.1 | 0.0103249485928346 | 0.0103249485928348 | 2.64e-16 | 7.62e-13 | pass | sensitivity budget | 2.13e-16 | 5.10e-17 |
| generic orbit Upsilon_r | chi=0.3, p=25, e=0.8, x=0.1 | 4.71417387022899 | 4.71417387022871 | 2.79e-13 | 4.41e-10 | pass | sensitivity budget | 9.76e-14 | 1.81e-13 |
| generic orbit Upsilon_theta | chi=0.3, p=25, e=0.8, x=0.1 | 5.40393070038461 | 5.40393070038503 | 4.14e-13 | 5.19e-10 | pass | sensitivity budget | 3.12e-15 | 4.11e-13 |
| generic orbit Upsilon_phi | chi=0.3, p=25, e=0.8, x=0.1 | 5.43094632165699 | 5.4309463216574 | 4.15e-13 | 5.19e-10 | pass | sensitivity budget | 6.62e-15 | 4.08e-13 |
| generic orbit Gamma | chi=0.3, p=25, e=0.8, x=0.1 | 2865.19511673082 | 2865.19511673073 | 9.50e-11 | 1.53e-07 | pass | sensitivity budget | 3.36e-11 | 6.14e-11 |
| generic orbit Omega_r | chi=0.3, p=25, e=0.8, x=0.1 | 0.00164532385340927 | 0.00164532385340923 | 4.27e-17 | 6.65e-14 | pass | sensitivity budget | 1.47e-17 | 2.80e-17 |
| generic orbit Omega_theta | chi=0.3, p=25, e=0.8, x=0.1 | 0.0018860602786977 | 0.0018860602786979 | 2.07e-16 | 2.82e-13 | pass | sensitivity budget | 2.33e-17 | 1.84e-16 |
| generic orbit Omega_phi | chi=0.3, p=25, e=0.8, x=0.1 | 0.00189548917277706 | 0.00189548917277727 | 2.08e-16 | 2.83e-13 | pass | sensitivity budget | 2.46e-17 | 1.83e-16 |
| generic orbit Upsilon_r | chi=0.3, p=10.3957, e=0.8, x=-0.4 | 2.45425055515958 | 2.45425055515946 | 1.17e-13 | 7.20e-11 | pass | sensitivity budget | 1.08e-13 | 9.03e-15 |
| generic orbit Upsilon_theta | chi=0.3, p=10.3957, e=0.8, x=-0.4 | 4.06163455410321 | 4.06163455410319 | 2.58e-14 | 1.40e-11 | pass | sensitivity budget | 9.00e-16 | 2.67e-14 |
| generic orbit Upsilon_phi | chi=0.3, p=10.3957, e=0.8, x=-0.4 | -3.97383507146036 | -3.97383507146033 | 2.84e-14 | 1.50e-11 | pass | sensitivity budget | 1.85e-15 | 2.66e-14 |
| generic orbit Gamma | chi=0.3, p=10.3957, e=0.8, x=-0.4 | 451.015979081066 | 451.015979081052 | 1.44e-11 | 8.97e-09 | pass | sensitivity budget | 1.28e-11 | 1.54e-12 |
| generic orbit Omega_r | chi=0.3, p=10.3957, e=0.8, x=-0.4 | 0.0054416044419536 | 0.00544160444195351 | 8.59e-17 | 5.36e-14 | pass | sensitivity budget | 8.43e-17 | 1.53e-18 |
| generic orbit Omega_theta | chi=0.3, p=10.3957, e=0.8, x=-0.4 | 0.00900552251469825 | 0.00900552251469848 | 2.31e-16 | 2.09e-13 | pass | sensitivity budget | 2.59e-16 | 2.84e-17 |
| generic orbit Omega_phi | chi=0.3, p=10.3957, e=0.8, x=-0.4 | -0.00881085206683132 | -0.00881085206683154 | 2.19e-16 | 2.03e-13 | pass | sensitivity budget | 2.47e-16 | 2.85e-17 |
| generic orbit Upsilon_r | chi=0.3, p=25, e=0.8, x=-0.4 | 4.69404439130945 | 4.69404439130946 | 1.78e-15 | 1.76e-10 | pass | sensitivity budget | 4.99e-15 | 3.21e-15 |
| generic orbit Upsilon_theta | chi=0.3, p=25, e=0.8, x=-0.4 | 5.42958507739659 | 5.42958507739637 | 2.18e-13 | 5.64e-11 | pass | sensitivity budget | 1.35e-15 | 2.19e-13 |
| generic orbit Upsilon_phi | chi=0.3, p=25, e=0.8, x=-0.4 | -5.4018735657187 | -5.40187356571848 | 2.18e-13 | 5.67e-11 | pass | sensitivity budget | 8.60e-16 | 2.19e-13 |
| generic orbit Gamma | chi=0.3, p=25, e=0.8, x=-0.4 | 2858.25270578536 | 2858.25270578536 | 4.55e-13 | 6.19e-08 | pass | sensitivity budget | 2.78e-12 | 2.33e-12 |
| generic orbit Omega_r | chi=0.3, p=25, e=0.8, x=-0.4 | 0.00164227759911092 | 0.00164227759911092 | 4.34e-19 | 2.66e-14 | pass | sensitivity budget | 2.29e-19 | 2.05e-19 |
| generic orbit Omega_theta | chi=0.3, p=25, e=0.8, x=-0.4 | 0.0018996168765647 | 0.00189961687656463 | 7.65e-17 | 6.07e-14 | pass | sensitivity budget | 1.46e-18 | 7.51e-17 |
| generic orbit Omega_phi | chi=0.3, p=25, e=0.8, x=-0.4 | -0.0018899216135735 | -0.00188992161357343 | 7.68e-17 | 6.04e-14 | pass | sensitivity budget | 1.61e-18 | 7.52e-17 |
| generic orbit Upsilon_r | chi=0.9, p=3.41335, e=0.1, x=0.9 | 1.09436336513044 | 1.09436336513045 | 1.29e-14 | 4.06e-12 | pass | sensitivity budget | 2.50e-15 | 1.54e-14 |
| generic orbit Upsilon_theta | chi=0.9, p=3.41335, e=0.1, x=0.9 | 2.3954082527974 | 2.3954082527974 | 3.11e-15 | 1.21e-12 | pass | sensitivity budget | 9.08e-16 | 4.02e-15 |
| generic orbit Upsilon_phi | chi=0.9, p=3.41335, e=0.1, x=0.9 | 3.02008375501899 | 3.02008375501899 | 2.66e-15 | 1.28e-12 | pass | sensitivity budget | 1.82e-15 | 4.48e-15 |
| generic orbit Gamma | chi=0.9, p=3.41335, e=0.1, x=0.9 | 21.4110534331832 | 21.4110534331832 | 1.78e-14 | 6.04e-12 | pass | sensitivity budget | 5.86e-15 | 1.19e-14 |
| generic orbit Omega_r | chi=0.9, p=3.41335, e=0.1, x=0.9 | 0.0511120748236691 | 0.0511120748236698 | 6.45e-16 | 1.97e-13 | pass | sensitivity budget | 1.05e-16 | 7.50e-16 |
| generic orbit Omega_theta | chi=0.9, p=3.41335, e=0.1, x=0.9 | 0.111877178779301 | 0.111877178779301 | 5.55e-17 | 7.85e-14 | pass | sensitivity budget | 6.96e-17 | 1.25e-16 |
| generic orbit Omega_phi | chi=0.9, p=3.41335, e=0.1, x=0.9 | 0.141052553273181 | 0.141052553273181 | 0.00e+00 | 7.22e-14 | pass | sensitivity budget | 1.22e-16 | 1.22e-16 |
| generic orbit Upsilon_r | chi=0.9, p=25, e=0.1, x=0.9 | 4.75991109645287 | 4.75991109645292 | 4.62e-14 | 3.39e-11 | pass | sensitivity budget | 4.78e-14 | 9.40e-14 |
| generic orbit Upsilon_theta | chi=0.9, p=25, e=0.1, x=0.9 | 5.23097957049503 | 5.23097957049501 | 1.60e-14 | 5.71e-12 | pass | sensitivity budget | 2.18e-14 | 3.77e-14 |
| generic orbit Upsilon_phi | chi=0.9, p=25, e=0.1, x=0.9 | 5.2983304543924 | 5.2983304543924 | 7.11e-15 | 5.71e-12 | pass | sensitivity budget | 3.08e-14 | 3.79e-14 |
| generic orbit Gamma | chi=0.9, p=25, e=0.1, x=0.9 | 675.223801450798 | 675.223801450798 | 0.00e+00 | 1.02e-10 | pass | sensitivity budget | 1.97e-13 | 1.97e-13 |
| generic orbit Omega_r | chi=0.9, p=25, e=0.1, x=0.9 | 0.00704938286568934 | 0.00704938286568941 | 6.85e-17 | 5.07e-14 | pass | sensitivity budget | 7.31e-17 | 1.42e-16 |
| generic orbit Omega_theta | chi=0.9, p=25, e=0.1, x=0.9 | 0.00774703077595258 | 0.00774703077595256 | 2.34e-17 | 8.98e-15 | pass | sensitivity budget | 2.99e-17 | 5.33e-17 |
| generic orbit Omega_phi | chi=0.9, p=25, e=0.1, x=0.9 | 0.00784677679164792 | 0.00784677679164791 | 1.04e-17 | 8.96e-15 | pass | sensitivity budget | 4.27e-17 | 5.31e-17 |
| generic orbit Upsilon_r | chi=0.9, p=6.84166, e=0.1, x=0.1 | 1.59491864824135 | 1.59491864824133 | 2.02e-14 | 6.32e-11 | pass | sensitivity budget | 2.14e-14 | 4.16e-14 |
| generic orbit Upsilon_theta | chi=0.9, p=6.84166, e=0.1, x=0.1 | 3.37859233477387 | 3.37859233477387 | 4.00e-15 | 1.68e-11 | pass | sensitivity budget | 2.95e-15 | 6.95e-15 |
| generic orbit Upsilon_phi | chi=0.9, p=6.84166, e=0.1, x=0.1 | 3.71275819736866 | 3.71275819736864 | 1.47e-14 | 1.72e-11 | pass | sensitivity budget | 2.05e-14 | 5.82e-15 |
| generic orbit Gamma | chi=0.9, p=6.84166, e=0.1, x=0.1 | 62.8925197561479 | 62.8925197561479 | 2.13e-14 | 2.39e-11 | pass | sensitivity budget | 3.39e-14 | 1.25e-14 |
| generic orbit Omega_r | chi=0.9, p=6.84166, e=0.1, x=0.1 | 0.0253594331158189 | 0.0253594331158186 | 3.12e-16 | 1.01e-12 | pass | sensitivity budget | 3.53e-16 | 6.65e-16 |
| generic orbit Omega_theta | chi=0.9, p=6.84166, e=0.1, x=0.1 | 0.0537200981591074 | 0.0537200981591075 | 8.33e-17 | 2.81e-13 | pass | sensitivity budget | 1.77e-17 | 1.01e-16 |
| generic orbit Omega_phi | chi=0.9, p=6.84166, e=0.1, x=0.1 | 0.0590333828532243 | 0.0590333828532241 | 2.15e-16 | 2.76e-13 | pass | sensitivity budget | 2.94e-16 | 7.86e-17 |
| generic orbit Upsilon_r | chi=0.9, p=25, e=0.1, x=0.1 | 4.66698084868735 | 4.66698084868757 | 2.27e-13 | 2.62e-10 | pass | sensitivity budget | 1.33e-13 | 9.40e-14 |
| generic orbit Upsilon_theta | chi=0.9, p=25, e=0.1, x=0.1 | 5.31668227356959 | 5.31668227356952 | 7.19e-14 | 1.01e-10 | pass | sensitivity budget | 3.52e-14 | 3.67e-14 |
| generic orbit Upsilon_phi | chi=0.9, p=25, e=0.1, x=0.1 | 5.39235136686882 | 5.39235136686874 | 7.11e-14 | 1.01e-10 | pass | sensitivity budget | 3.31e-14 | 3.79e-14 |
| generic orbit Gamma | chi=0.9, p=25, e=0.1, x=0.1 | 675.944759514498 | 675.944759514498 | 2.27e-13 | 2.50e-10 | pass | sensitivity budget | 9.22e-14 | 1.35e-13 |
| generic orbit Omega_r | chi=0.9, p=25, e=0.1, x=0.1 | 0.00690438202677899 | 0.00690438202677932 | 3.38e-16 | 3.90e-13 | pass | sensitivity budget | 1.98e-16 | 1.40e-16 |
| generic orbit Omega_theta | chi=0.9, p=25, e=0.1, x=0.1 | 0.00786555735321971 | 0.0078655573532196 | 1.04e-16 | 1.52e-13 | pass | sensitivity budget | 5.11e-17 | 5.30e-17 |
| generic orbit Omega_phi | chi=0.9, p=25, e=0.1, x=0.1 | 0.0079775030295995 | 0.0079775030295994 | 1.02e-16 | 1.52e-13 | pass | sensitivity budget | 4.77e-17 | 5.47e-17 |
| generic orbit Upsilon_r | chi=0.9, p=9.09493, e=0.1, x=-0.4 | 1.89563904979243 | 1.89563904979246 | 2.24e-14 | 1.63e-11 | pass | sensitivity budget | 4.13e-14 | 1.88e-14 |
| generic orbit Upsilon_theta | chi=0.9, p=9.09493, e=0.1, x=-0.4 | 3.84390951146052 | 3.84390951146051 | 7.11e-15 | 2.92e-12 | pass | sensitivity budget | 1.10e-14 | 3.93e-15 |
| generic orbit Upsilon_phi | chi=0.9, p=9.09493, e=0.1, x=-0.4 | -3.58040936144491 | -3.5804093614449 | 6.66e-15 | 2.94e-12 | pass | sensitivity budget | 1.03e-14 | 3.63e-15 |
| generic orbit Gamma | chi=0.9, p=9.09493, e=0.1, x=-0.4 | 102.84955280168 | 102.849552801679 | 1.42e-14 | 1.26e-11 | pass | sensitivity budget | 6.82e-15 | 2.10e-14 |
| generic orbit Omega_r | chi=0.9, p=9.09493, e=0.1, x=-0.4 | 0.0184311841729416 | 0.0184311841729418 | 2.19e-16 | 1.58e-13 | pass | sensitivity budget | 3.99e-16 | 1.81e-16 |
| generic orbit Omega_theta | chi=0.9, p=9.09493, e=0.1, x=-0.4 | 0.0373741003898439 | 0.0373741003898438 | 6.25e-17 | 3.01e-14 | pass | sensitivity budget | 1.11e-16 | 4.86e-17 |
| generic orbit Omega_phi | chi=0.9, p=9.09493, e=0.1, x=-0.4 | -0.0348121043204618 | -0.0348121043204617 | 5.55e-17 | 3.00e-14 | pass | sensitivity budget | 1.00e-16 | 4.45e-17 |
| generic orbit Upsilon_r | chi=0.9, p=25, e=0.1, x=-0.4 | 4.59519173201758 | 4.59519173201758 | 1.78e-15 | 4.84e-11 | pass | sensitivity budget | 7.67e-14 | 7.49e-14 |
| generic orbit Upsilon_theta | chi=0.9, p=25, e=0.1, x=-0.4 | 5.37901323535675 | 5.37901323535676 | 3.55e-15 | 1.10e-11 | pass | sensitivity budget | 3.23e-14 | 2.87e-14 |
| generic orbit Upsilon_phi | chi=0.9, p=25, e=0.1, x=-0.4 | -5.29810771694485 | -5.29810771694486 | 3.55e-15 | 1.10e-11 | pass | sensitivity budget | 3.22e-14 | 2.86e-14 |
| generic orbit Gamma | chi=0.9, p=25, e=0.1, x=-0.4 | 676.137624134523 | 676.137624134523 | 2.27e-13 | 1.04e-10 | pass | sensitivity budget | 2.83e-13 | 5.56e-14 |
| generic orbit Omega_r | chi=0.9, p=25, e=0.1, x=-0.4 | 0.00679623728660208 | 0.00679623728660208 | 0.00e+00 | 7.21e-14 | pass | sensitivity budget | 1.11e-16 | 1.11e-16 |
| generic orbit Omega_theta | chi=0.9, p=25, e=0.1, x=-0.4 | 0.0079555005421301 | 0.00795550054213011 | 8.67e-18 | 1.69e-14 | pass | sensitivity budget | 5.17e-17 | 4.30e-17 |
| generic orbit Omega_phi | chi=0.9, p=25, e=0.1, x=-0.4 | -0.00783584218335224 | -0.00783584218335225 | 6.94e-18 | 1.69e-14 | pass | sensitivity budget | 5.01e-17 | 4.31e-17 |
| generic orbit Upsilon_r | chi=0.9, p=3.96483, e=0.5, x=0.9 | 1.33680664959118 | 1.33680664959119 | 1.07e-14 | 7.15e-12 | pass | sensitivity budget | 7.99e-15 | 2.67e-15 |
| generic orbit Upsilon_theta | chi=0.9, p=3.96483, e=0.5, x=0.9 | 2.55143572852597 | 2.55143572852596 | 2.66e-15 | 2.14e-12 | pass | sensitivity budget | 6.49e-16 | 2.02e-15 |
| generic orbit Upsilon_phi | chi=0.9, p=3.96483, e=0.5, x=0.9 | 3.14738275728481 | 3.14738275728481 | 3.11e-15 | 2.72e-12 | pass | sensitivity budget | 2.82e-16 | 2.83e-15 |
| generic orbit Gamma | chi=0.9, p=3.96483, e=0.5, x=0.9 | 33.1175790333325 | 33.1175790333326 | 4.97e-14 | 4.28e-11 | pass | sensitivity budget | 4.32e-14 | 6.54e-15 |
| generic orbit Omega_r | chi=0.9, p=3.96483, e=0.5, x=0.9 | 0.0403654702007565 | 0.0403654702007568 | 2.64e-16 | 1.73e-13 | pass | sensitivity budget | 1.92e-16 | 7.18e-17 |
| generic orbit Omega_theta | chi=0.9, p=3.96483, e=0.5, x=0.9 | 0.0770417344201993 | 0.0770417344201991 | 1.94e-16 | 1.55e-13 | pass | sensitivity budget | 1.19e-16 | 7.55e-17 |
| generic orbit Omega_phi | chi=0.9, p=3.96483, e=0.5, x=0.9 | 0.0950366194979713 | 0.095036619497971 | 2.36e-16 | 1.96e-13 | pass | sensitivity budget | 1.36e-16 | 9.98e-17 |
| generic orbit Upsilon_r | chi=0.9, p=25, e=0.5, x=0.9 | 4.77705343171153 | 4.7770534317116 | 7.28e-14 | 4.10e-11 | pass | sensitivity budget | 2.42e-14 | 9.71e-14 |
| generic orbit Upsilon_theta | chi=0.9, p=25, e=0.5, x=0.9 | 5.2508547312112 | 5.25085473121122 | 2.22e-14 | 5.95e-12 | pass | sensitivity budget | 1.46e-14 | 7.63e-15 |
| generic orbit Upsilon_phi | chi=0.9, p=25, e=0.5, x=0.9 | 5.31936090184508 | 5.31936090184511 | 3.29e-14 | 6.01e-12 | pass | sensitivity budget | 2.48e-14 | 8.10e-15 |
| generic orbit Gamma | chi=0.9, p=25, e=0.5, x=0.9 | 1000.54602060298 | 1000.54602060298 | 3.30e-12 | 1.70e-09 | pass | sensitivity budget | 2.18e-13 | 3.52e-12 |
| generic orbit Omega_r | chi=0.9, p=25, e=0.5, x=0.9 | 0.00477444648556259 | 0.00477444648556265 | 5.72e-17 | 3.38e-14 | pass | sensitivity budget | 2.31e-17 | 8.03e-17 |
| generic orbit Omega_theta | chi=0.9, p=25, e=0.5, x=0.9 | 0.00524798922097234 | 0.00524798922097235 | 5.20e-18 | 1.44e-14 | pass | sensitivity budget | 1.56e-17 | 1.04e-17 |
| generic orbit Omega_phi | chi=0.9, p=25, e=0.5, x=0.9 | 0.00531645800623881 | 0.00531645800623882 | 1.56e-17 | 1.46e-14 | pass | sensitivity budget | 2.58e-17 | 1.02e-17 |
| generic orbit Upsilon_r | chi=0.9, p=7.65925, e=0.5, x=0.1 | 1.89661389101452 | 1.89661389101451 | 6.66e-16 | 3.56e-11 | pass | sensitivity budget | 8.55e-15 | 7.88e-15 |
| generic orbit Upsilon_theta | chi=0.9, p=7.65925, e=0.5, x=0.1 | 3.53668225315746 | 3.53668225315747 | 4.00e-15 | 1.60e-11 | pass | sensitivity budget | 2.95e-15 | 1.04e-15 |
| generic orbit Upsilon_phi | chi=0.9, p=7.65925, e=0.5, x=0.1 | 3.85863840754561 | 3.85863840754564 | 2.53e-14 | 1.72e-11 | pass | sensitivity budget | 2.58e-14 | 4.75e-16 |
| generic orbit Gamma | chi=0.9, p=7.65925, e=0.5, x=0.1 | 100.659821538656 | 100.659821538656 | 1.28e-13 | 5.20e-10 | pass | sensitivity budget | 1.86e-13 | 5.85e-14 |
| generic orbit Omega_r | chi=0.9, p=7.65925, e=0.5, x=0.1 | 0.0188418165462985 | 0.0188418165462986 | 1.73e-17 | 2.59e-13 | pass | sensitivity budget | 5.14e-17 | 6.88e-17 |
| generic orbit Omega_theta | chi=0.9, p=7.65925, e=0.5, x=0.1 | 0.0351349942717638 | 0.0351349942717639 | 8.33e-17 | 3.28e-13 | pass | sensitivity budget | 9.59e-17 | 1.27e-17 |
| generic orbit Omega_phi | chi=0.9, p=7.65925, e=0.5, x=0.1 | 0.0383334517045987 | 0.038333451704599 | 2.98e-16 | 3.56e-13 | pass | sensitivity budget | 3.27e-16 | 2.90e-17 |
| generic orbit Upsilon_r | chi=0.9, p=25, e=0.5, x=0.1 | 4.69008122657195 | 4.69008122657195 | 8.88e-16 | 1.32e-10 | pass | sensitivity budget | 2.21e-14 | 2.12e-14 |
| generic orbit Upsilon_theta | chi=0.9, p=25, e=0.5, x=0.1 | 5.34488070455189 | 5.34488070455194 | 4.80e-14 | 9.88e-11 | pass | sensitivity budget | 8.45e-15 | 5.64e-14 |
| generic orbit Upsilon_phi | chi=0.9, p=25, e=0.5, x=0.1 | 5.4221668638328 | 5.42216686383284 | 4.80e-14 | 9.90e-11 | pass | sensitivity budget | 5.16e-15 | 5.31e-14 |
| generic orbit Gamma | chi=0.9, p=25, e=0.5, x=0.1 | 997.957487417811 | 997.957487417812 | 1.14e-13 | 5.47e-09 | pass | sensitivity budget | 6.64e-13 | 5.51e-13 |
| generic orbit Omega_r | chi=0.9, p=25, e=0.5, x=0.1 | 0.00469968038288626 | 0.00469968038288626 | 8.67e-19 | 1.08e-13 | pass | sensitivity budget | 1.92e-17 | 1.83e-17 |
| generic orbit Omega_theta | chi=0.9, p=25, e=0.5, x=0.1 | 0.00535582003436001 | 0.00535582003436006 | 4.77e-17 | 1.28e-13 | pass | sensitivity budget | 1.21e-17 | 5.98e-17 |
| generic orbit Omega_phi | chi=0.9, p=25, e=0.5, x=0.1 | 0.00543326437468044 | 0.00543326437468049 | 4.77e-17 | 1.28e-13 | pass | sensitivity budget | 8.67e-18 | 5.64e-17 |
| generic orbit Upsilon_r | chi=0.9, p=10.175, e=0.5, x=-0.4 | 2.24560074345525 | 2.24560074345525 | 4.44e-16 | 1.82e-11 | pass | sensitivity budget | 3.71e-15 | 3.26e-15 |
| generic orbit Upsilon_theta | chi=0.9, p=10.175, e=0.5, x=-0.4 | 4.01733846581309 | 4.01733846581309 | 8.88e-16 | 3.04e-12 | pass | sensitivity budget | 1.05e-15 | 1.65e-16 |
| generic orbit Upsilon_phi | chi=0.9, p=10.175, e=0.5, x=-0.4 | -3.76585650123881 | -3.76585650123881 | 4.44e-15 | 3.41e-12 | pass | sensitivity budget | 4.76e-15 | 3.16e-16 |
| generic orbit Gamma | chi=0.9, p=10.175, e=0.5, x=-0.4 | 169.080684107509 | 169.080684107509 | 5.68e-14 | 3.97e-10 | pass | sensitivity budget | 5.91e-14 | 1.16e-13 |
| generic orbit Omega_r | chi=0.9, p=10.175, e=0.5, x=-0.4 | 0.013281237625153 | 0.013281237625153 | 8.67e-18 | 7.84e-14 | pass | sensitivity budget | 1.81e-17 | 9.39e-18 |
| generic orbit Omega_theta | chi=0.9, p=10.175, e=0.5, x=-0.4 | 0.0237598900608817 | 0.0237598900608817 | 0.00e+00 | 7.16e-14 | pass | sensitivity budget | 1.60e-17 | 1.60e-17 |
| generic orbit Omega_phi | chi=0.9, p=10.175, e=0.5, x=-0.4 | -0.0222725411901238 | -0.0222725411901238 | 1.73e-17 | 6.57e-14 | pass | sensitivity budget | 3.52e-17 | 1.79e-17 |
| generic orbit Upsilon_r | chi=0.9, p=25, e=0.5, x=-0.4 | 4.62184226693689 | 4.62184226693689 | 8.88e-16 | 4.80e-11 | pass | sensitivity budget | 1.20e-13 | 1.19e-13 |
| generic orbit Upsilon_theta | chi=0.9, p=25, e=0.5, x=-0.4 | 5.41316867622223 | 5.4131686762223 | 7.37e-14 | 1.10e-11 | pass | sensitivity budget | 1.87e-14 | 9.24e-14 |
| generic orbit Upsilon_phi | chi=0.9, p=25, e=0.5, x=-0.4 | -5.33025200220921 | -5.33025200220928 | 7.19e-14 | 1.11e-11 | pass | sensitivity budget | 1.85e-14 | 9.04e-14 |
| generic orbit Gamma | chi=0.9, p=25, e=0.5, x=-0.4 | 995.28005643734 | 995.280056437339 | 2.27e-13 | 2.14e-09 | pass | sensitivity budget | 4.75e-12 | 4.98e-12 |
| generic orbit Omega_r | chi=0.9, p=25, e=0.5, x=-0.4 | 0.00464376055467346 | 0.00464376055467346 | 1.73e-18 | 3.91e-14 | pass | sensitivity budget | 9.81e-17 | 9.64e-17 |
| generic orbit Omega_theta | chi=0.9, p=25, e=0.5, x=-0.4 | 0.00543883969261774 | 0.00543883969261782 | 7.55e-17 | 2.23e-14 | pass | sensitivity budget | 4.50e-17 | 1.20e-16 |
| generic orbit Omega_phi | chi=0.9, p=25, e=0.5, x=-0.4 | -0.00535552980061627 | -0.00535552980061634 | 7.37e-17 | 2.20e-14 | pass | sensitivity budget | 4.42e-17 | 1.18e-16 |
| generic orbit Upsilon_r | chi=0.9, p=4.43346, e=0.8, x=0.9 | 1.52843744663388 | 1.52843744663388 | 2.22e-16 | 2.29e-11 | pass | sensitivity budget | 5.17e-15 | 5.40e-15 |
| generic orbit Upsilon_theta | chi=0.9, p=4.43346, e=0.8, x=0.9 | 2.72641719346582 | 2.72641719346582 | 1.78e-15 | 4.34e-12 | pass | sensitivity budget | 1.24e-16 | 1.65e-15 |
| generic orbit Upsilon_phi | chi=0.9, p=4.43346, e=0.8, x=0.9 | 3.34160088324531 | 3.34160088324531 | 4.44e-16 | 7.72e-12 | pass | sensitivity budget | 1.84e-15 | 2.28e-15 |
| generic orbit Gamma | chi=0.9, p=4.43346, e=0.8, x=0.9 | 89.3791951266928 | 89.3791951266927 | 4.26e-14 | 8.63e-10 | pass | sensitivity budget | 1.92e-13 | 1.49e-13 |
| generic orbit Omega_r | chi=0.9, p=4.43346, e=0.8, x=0.9 | 0.0171005953283352 | 0.0171005953283352 | 1.04e-17 | 9.91e-14 | pass | sensitivity budget | 2.18e-17 | 3.22e-17 |
| generic orbit Omega_theta | chi=0.9, p=4.43346, e=0.8, x=0.9 | 0.0305039353912417 | 0.0305039353912416 | 6.94e-18 | 3.37e-13 | pass | sensitivity budget | 6.33e-17 | 7.02e-17 |
| generic orbit Omega_phi | chi=0.9, p=4.43346, e=0.8, x=0.9 | 0.0373867864720494 | 0.0373867864720495 | 1.39e-17 | 4.40e-13 | pass | sensitivity budget | 1.03e-16 | 8.91e-17 |
| generic orbit Upsilon_r | chi=0.9, p=25, e=0.8, x=0.9 | 4.80533135770195 | 4.80533135770168 | 2.68e-13 | 1.53e-10 | pass | sensitivity budget | 6.71e-14 | 2.01e-13 |
| generic orbit Upsilon_theta | chi=0.9, p=25, e=0.8, x=0.9 | 5.28363294169014 | 5.28363294169069 | 5.45e-13 | 2.94e-11 | pass | sensitivity budget | 1.86e-15 | 5.47e-13 |
| generic orbit Upsilon_phi | chi=0.9, p=25, e=0.8, x=0.9 | 5.3540395621789 | 5.35403956217945 | 5.52e-13 | 3.00e-11 | pass | sensitivity budget | 2.73e-15 | 5.49e-13 |
| generic orbit Gamma | chi=0.9, p=25, e=0.8, x=0.9 | 2896.0337067783 | 2896.03370677821 | 9.19e-11 | 5.21e-08 | pass | sensitivity budget | 2.50e-11 | 6.68e-11 |
| generic orbit Omega_r | chi=0.9, p=25, e=0.8, x=0.9 | 0.00165928018947253 | 0.00165928018947249 | 3.99e-17 | 2.37e-14 | pass | sensitivity budget | 8.84e-18 | 3.11e-17 |
| generic orbit Omega_theta | chi=0.9, p=25, e=0.8, x=0.9 | 0.0018244376539277 | 0.00182443765392794 | 2.46e-16 | 4.28e-14 | pass | sensitivity budget | 1.51e-17 | 2.31e-16 |
| generic orbit Omega_phi | chi=0.9, p=25, e=0.8, x=0.9 | 0.00184874904931097 | 0.00184874904931121 | 2.49e-16 | 4.35e-14 | pass | sensitivity budget | 1.70e-17 | 2.32e-16 |
| generic orbit Upsilon_r | chi=0.9, p=8.23382, e=0.8, x=0.1 | 2.10894380434206 | 2.10894380434223 | 1.71e-13 | 1.41e-10 | pass | sensitivity budget | 3.20e-14 | 1.39e-13 |
| generic orbit Upsilon_theta | chi=0.9, p=8.23382, e=0.8, x=0.1 | 3.71719239168884 | 3.71719239168878 | 5.82e-14 | 8.48e-11 | pass | sensitivity budget | 1.66e-15 | 5.98e-14 |
| generic orbit Upsilon_phi | chi=0.9, p=8.23382, e=0.8, x=0.1 | 4.05260389785444 | 4.05260389785437 | 6.93e-14 | 9.31e-11 | pass | sensitivity budget | 6.24e-17 | 6.93e-14 |
| generic orbit Gamma | chi=0.9, p=8.23382, e=0.8, x=0.1 | 283.827331145336 | 283.827331145352 | 1.52e-11 | 1.29e-08 | pass | sensitivity budget | 2.63e-12 | 1.26e-11 |
| generic orbit Omega_r | chi=0.9, p=8.23382, e=0.8, x=0.1 | 0.00743037605234061 | 0.00743037605234081 | 2.06e-16 | 1.63e-13 | pass | sensitivity budget | 4.44e-17 | 1.61e-16 |
| generic orbit Omega_theta | chi=0.9, p=8.23382, e=0.8, x=0.1 | 0.013096668233777 | 0.0130966682337761 | 9.06e-16 | 8.54e-13 | pass | sensitivity budget | 1.16e-16 | 7.90e-16 |
| generic orbit Omega_phi | chi=0.9, p=8.23382, e=0.8, x=0.1 | 0.0142784131517598 | 0.0142784131517587 | 1.01e-15 | 9.34e-13 | pass | sensitivity budget | 1.32e-16 | 8.76e-16 |
| generic orbit Upsilon_r | chi=0.9, p=25, e=0.8, x=0.1 | 4.72841827361498 | 4.72841827361471 | 2.77e-13 | 4.40e-10 | pass | sensitivity budget | 1.03e-14 | 2.87e-13 |
| generic orbit Upsilon_theta | chi=0.9, p=25, e=0.8, x=0.1 | 5.39165784454206 | 5.39165784454199 | 6.66e-14 | 5.20e-10 | pass | sensitivity budget | 2.62e-15 | 6.40e-14 |
| generic orbit Upsilon_phi | chi=0.9, p=25, e=0.8, x=0.1 | 5.47161426295885 | 5.47161426295879 | 6.66e-14 | 5.23e-10 | pass | sensitivity budget | 6.17e-16 | 6.60e-14 |
| generic orbit Gamma | chi=0.9, p=25, e=0.8, x=0.1 | 2871.23359907961 | 2871.23359907952 | 9.50e-11 | 1.52e-07 | pass | sensitivity budget | 2.82e-12 | 9.79e-11 |
| generic orbit Omega_r | chi=0.9, p=25, e=0.8, x=0.1 | 0.00164682465234828 | 0.00164682465234824 | 4.21e-17 | 6.65e-14 | pass | sensitivity budget | 2.01e-18 | 4.41e-17 |
| generic orbit Omega_theta | chi=0.9, p=25, e=0.8, x=0.1 | 0.00187781929212252 | 0.00187781929212255 | 3.90e-17 | 2.80e-13 | pass | sensitivity budget | 2.78e-18 | 4.18e-17 |
| generic orbit Omega_phi | chi=0.9, p=25, e=0.8, x=0.1 | 0.00190566670183604 | 0.00190566670183608 | 3.99e-17 | 2.82e-13 | pass | sensitivity budget | 2.14e-18 | 4.20e-17 |
| generic orbit Upsilon_r | chi=0.9, p=10.9274, e=0.8, x=-0.4 | 2.48705977831275 | 2.48705977831275 | 4.44e-16 | 8.00e-11 | pass | sensitivity budget | 6.08e-14 | 6.03e-14 |
| generic orbit Upsilon_theta | chi=0.9, p=10.9274, e=0.8, x=-0.4 | 4.21027711060509 | 4.21027711060507 | 1.60e-14 | 1.52e-11 | pass | sensitivity budget | 2.63e-15 | 1.86e-14 |
| generic orbit Upsilon_phi | chi=0.9, p=10.9274, e=0.8, x=-0.4 | -3.95175849189332 | -3.9517584918933 | 2.00e-14 | 1.85e-11 | pass | sensitivity budget | 1.24e-15 | 2.12e-14 |
| generic orbit Gamma | chi=0.9, p=10.9274, e=0.8, x=-0.4 | 494.167486120442 | 494.167486120442 | 1.14e-13 | 1.08e-08 | pass | sensitivity budget | 7.56e-12 | 7.68e-12 |
| generic orbit Omega_r | chi=0.9, p=10.9274, e=0.8, x=-0.4 | 0.0050328276306438 | 0.0050328276306438 | 1.73e-18 | 5.34e-14 | pass | sensitivity budget | 4.60e-17 | 4.43e-17 |
| generic orbit Omega_theta | chi=0.9, p=10.9274, e=0.8, x=-0.4 | 0.00851993955259722 | 0.00851993955259719 | 2.95e-17 | 2.15e-13 | pass | sensitivity budget | 1.25e-16 | 9.53e-17 |
| generic orbit Omega_phi | chi=0.9, p=10.9274, e=0.8, x=-0.4 | -0.00799679987632811 | -0.00799679987632807 | 3.82e-17 | 1.97e-13 | pass | sensitivity budget | 1.20e-16 | 8.19e-17 |
| generic orbit Upsilon_r | chi=0.9, p=25, e=0.8, x=-0.4 | 4.66624322435336 | 4.66624322435279 | 5.71e-13 | 1.78e-10 | pass | sensitivity budget | 2.36e-13 | 3.35e-13 |
| generic orbit Upsilon_theta | chi=0.9, p=25, e=0.8, x=-0.4 | 5.47003496625965 | 5.47003496626021 | 5.57e-13 | 5.64e-11 | pass | sensitivity budget | 2.72e-15 | 5.54e-13 |
| generic orbit Upsilon_phi | chi=0.9, p=25, e=0.8, x=-0.4 | -5.38378804739677 | -5.38378804739733 | 5.55e-13 | 5.73e-11 | pass | sensitivity budget | 1.68e-16 | 5.55e-13 |
| generic orbit Gamma | chi=0.9, p=25, e=0.8, x=-0.4 | 2849.63623970103 | 2849.63623970082 | 2.02e-10 | 6.32e-08 | pass | sensitivity budget | 8.37e-11 | 1.18e-10 |
| generic orbit Omega_r | chi=0.9, p=25, e=0.8, x=-0.4 | 0.0016374873253447 | 0.00163748732534461 | 8.46e-17 | 2.68e-14 | pass | sensitivity budget | 3.48e-17 | 4.98e-17 |
| generic orbit Omega_theta | chi=0.9, p=25, e=0.8, x=-0.4 | 0.00191955551731527 | 0.0019195555173156 | 3.32e-16 | 6.21e-14 | pass | sensitivity budget | 5.74e-17 | 2.74e-16 |
| generic orbit Omega_phi | chi=0.9, p=25, e=0.8, x=-0.4 | -0.00188928957752222 | -0.00188928957752255 | 3.29e-16 | 6.11e-14 | pass | sensitivity budget | 5.56e-17 | 2.73e-16 |
| generic orbit Upsilon_r | chi=0.99, p=2.19135, e=0.1, x=0.9 | 0.765217975704764 | 0.76521797570476 | 3.33e-15 | 1.66e-12 | pass | sensitivity budget | 4.74e-15 | 1.41e-15 |
| generic orbit Upsilon_theta | chi=0.99, p=2.19135, e=0.1, x=0.9 | 2.00629959663994 | 2.00629959663994 | 1.33e-15 | 8.40e-13 | pass | sensitivity budget | 1.86e-15 | 5.23e-16 |
| generic orbit Upsilon_phi | chi=0.99, p=2.19135, e=0.1, x=0.9 | 3.26785598870438 | 3.26785598870439 | 5.33e-15 | 8.78e-13 | pass | sensitivity budget | 4.36e-15 | 9.69e-16 |
| generic orbit Gamma | chi=0.99, p=2.19135, e=0.1, x=0.9 | 13.4886792049181 | 13.4886792049181 | 8.88e-15 | 5.23e-12 | pass | sensitivity budget | 7.97e-15 | 9.13e-16 |
| generic orbit Omega_r | chi=0.99, p=2.19135, e=0.1, x=0.9 | 0.0567303858353868 | 0.0567303858353865 | 2.84e-16 | 1.39e-13 | pass | sensitivity budget | 3.87e-16 | 1.02e-16 |
| generic orbit Omega_theta | chi=0.99, p=2.19135, e=0.1, x=0.9 | 0.148739514533671 | 0.148739514533671 | 0.00e+00 | 1.05e-13 | pass | sensitivity budget | 5.10e-17 | 5.10e-17 |
| generic orbit Omega_phi | chi=0.99, p=2.19135, e=0.1, x=0.9 | 0.242266565840849 | 0.242266565840849 | 2.50e-16 | 8.54e-14 | pass | sensitivity budget | 1.88e-16 | 6.15e-17 |
| generic orbit Upsilon_r | chi=0.99, p=25, e=0.1, x=0.9 | 4.76990332570444 | 4.76990332570466 | 2.22e-13 | 3.39e-11 | pass | sensitivity budget | 1.08e-13 | 1.14e-13 |
| generic orbit Upsilon_theta | chi=0.99, p=25, e=0.1, x=0.9 | 5.22189847624636 | 5.22189847624627 | 8.35e-14 | 5.73e-12 | pass | sensitivity budget | 3.04e-14 | 5.31e-14 |
| generic orbit Upsilon_phi | chi=0.99, p=25, e=0.1, x=0.9 | 5.29493690413392 | 5.29493690413384 | 8.26e-14 | 5.73e-12 | pass | sensitivity budget | 2.59e-14 | 5.67e-14 |
| generic orbit Gamma | chi=0.99, p=25, e=0.1, x=0.9 | 675.195414321891 | 675.195414321891 | 3.41e-13 | 1.02e-10 | pass | sensitivity budget | 8.67e-14 | 2.54e-13 |
| generic orbit Omega_r | chi=0.99, p=25, e=0.1, x=0.9 | 0.00706447825996408 | 0.00706447825996441 | 3.32e-16 | 5.07e-14 | pass | sensitivity budget | 1.61e-16 | 1.71e-16 |
| generic orbit Omega_theta | chi=0.99, p=25, e=0.1, x=0.9 | 0.00773390690381211 | 0.00773390690381199 | 1.20e-16 | 9.01e-15 | pass | sensitivity budget | 4.38e-17 | 7.59e-17 |
| generic orbit Omega_phi | chi=0.99, p=25, e=0.1, x=0.9 | 0.00784208066556806 | 0.00784208066556794 | 1.18e-16 | 8.99e-15 | pass | sensitivity budget | 3.75e-17 | 8.05e-17 |
| generic orbit Upsilon_r | chi=0.99, p=6.57602, e=0.1, x=0.1 | 1.53955903439084 | 1.53955903439084 | 2.22e-16 | 6.15e-11 | pass | sensitivity budget | 6.85e-15 | 7.07e-15 |
| generic orbit Upsilon_theta | chi=0.99, p=6.57602, e=0.1, x=0.1 | 3.33655806135191 | 3.3365580613519 | 2.22e-15 | 1.63e-11 | pass | sensitivity budget | 4.14e-15 | 1.92e-15 |
| generic orbit Upsilon_phi | chi=0.99, p=6.57602, e=0.1, x=0.1 | 3.72028718648043 | 3.72028718648044 | 1.87e-14 | 1.67e-11 | pass | sensitivity budget | 1.75e-14 | 1.16e-15 |
| generic orbit Gamma | chi=0.99, p=6.57602, e=0.1, x=0.1 | 58.9876117706916 | 58.9876117706916 | 1.42e-14 | 2.34e-11 | pass | sensitivity budget | 1.95e-14 | 5.32e-15 |
| generic orbit Omega_r | chi=0.99, p=6.57602, e=0.1, x=0.1 | 0.0260997010758076 | 0.0260997010758076 | 3.47e-18 | 1.05e-12 | pass | sensitivity budget | 1.26e-16 | 1.22e-16 |
| generic orbit Omega_theta | chi=0.99, p=6.57602, e=0.1, x=0.1 | 0.0565637082294913 | 0.0565637082294913 | 2.78e-17 | 2.90e-13 | pass | sensitivity budget | 5.18e-17 | 2.41e-17 |
| generic orbit Omega_phi | chi=0.99, p=6.57602, e=0.1, x=0.1 | 0.0630689576133828 | 0.0630689576133831 | 3.33e-16 | 2.83e-13 | pass | sensitivity budget | 3.22e-16 | 1.13e-17 |
| generic orbit Upsilon_r | chi=0.99, p=25, e=0.1, x=0.1 | 4.66952868588821 | 4.66952868588826 | 4.62e-14 | 2.62e-10 | pass | sensitivity budget | 1.15e-13 | 1.62e-13 |
| generic orbit Upsilon_theta | chi=0.99, p=25, e=0.1, x=0.1 | 5.31496043845157 | 5.31496043845155 | 1.69e-14 | 1.01e-10 | pass | sensitivity budget | 4.03e-14 | 5.72e-14 |
| generic orbit Upsilon_phi | chi=0.99, p=25, e=0.1, x=0.1 | 5.39805631592634 | 5.39805631592635 | 1.33e-14 | 1.02e-10 | pass | sensitivity budget | 6.78e-14 | 5.45e-14 |
| generic orbit Gamma | chi=0.99, p=25, e=0.1, x=0.1 | 676.023197092002 | 676.023197092002 | 1.14e-13 | 2.51e-10 | pass | sensitivity budget | 1.25e-13 | 1.17e-14 |
| generic orbit Omega_r | chi=0.99, p=25, e=0.1, x=0.1 | 0.00690734978618304 | 0.00690734978618311 | 6.94e-17 | 3.90e-13 | pass | sensitivity budget | 1.69e-16 | 2.39e-16 |
| generic orbit Omega_theta | chi=0.99, p=25, e=0.1, x=0.1 | 0.00786209772285114 | 0.00786209772285111 | 2.26e-17 | 1.52e-13 | pass | sensitivity budget | 6.15e-17 | 8.40e-17 |
| generic orbit Omega_phi | chi=0.99, p=25, e=0.1, x=0.1 | 0.00798501640054181 | 0.00798501640054183 | 2.08e-17 | 1.52e-13 | pass | sensitivity budget | 1.02e-16 | 8.11e-17 |
| generic orbit Upsilon_r | chi=0.99, p=9.14286, e=0.1, x=-0.4 | 1.89385908194316 | 1.89385908194315 | 1.44e-14 | 1.66e-11 | pass | sensitivity budget | 3.02e-14 | 1.58e-14 |
| generic orbit Upsilon_theta | chi=0.99, p=9.14286, e=0.1, x=-0.4 | 3.86156838323412 | 3.86156838323413 | 1.02e-14 | 2.96e-12 | pass | sensitivity budget | 1.02e-14 | 2.73e-17 |
| generic orbit Upsilon_phi | chi=0.99, p=9.14286, e=0.1, x=-0.4 | -3.57182209081815 | -3.57182209081816 | 1.07e-14 | 2.98e-12 | pass | sensitivity budget | 9.50e-15 | 1.16e-15 |
| generic orbit Gamma | chi=0.99, p=9.14286, e=0.1, x=-0.4 | 103.907060732697 | 103.907060732697 | 8.53e-14 | 1.26e-11 | pass | sensitivity budget | 4.94e-14 | 3.59e-14 |
| generic orbit Omega_r | chi=0.99, p=9.14286, e=0.1, x=-0.4 | 0.0182264715081794 | 0.0182264715081792 | 1.25e-16 | 1.59e-13 | pass | sensitivity budget | 2.83e-16 | 1.58e-16 |
| generic orbit Omega_theta | chi=0.99, p=9.14286, e=0.1, x=-0.4 | 0.0371636764239543 | 0.0371636764239544 | 1.32e-16 | 3.01e-14 | pass | sensitivity budget | 1.17e-16 | 1.44e-17 |
| generic orbit Omega_phi | chi=0.99, p=9.14286, e=0.1, x=-0.4 | -0.0343751624348872 | -0.0343751624348873 | 1.32e-16 | 3.00e-14 | pass | sensitivity budget | 1.08e-16 | 2.41e-17 |
| generic orbit Upsilon_r | chi=0.99, p=25, e=0.1, x=-0.4 | 4.59029472806103 | 4.59029472806099 | 4.71e-14 | 4.85e-11 | pass | sensitivity budget | 1.01e-13 | 5.38e-14 |
| generic orbit Upsilon_theta | chi=0.99, p=25, e=0.1, x=-0.4 | 5.3837176781308 | 5.38371767813081 | 7.99e-15 | 1.10e-11 | pass | sensitivity budget | 2.56e-14 | 1.76e-14 |
| generic orbit Upsilon_phi | chi=0.99, p=25, e=0.1, x=-0.4 | -5.29428634043115 | -5.29428634043116 | 7.11e-15 | 1.10e-11 | pass | sensitivity budget | 2.62e-14 | 1.91e-14 |
| generic orbit Gamma | chi=0.99, p=25, e=0.1, x=-0.4 | 676.228809062893 | 676.228809062892 | 9.09e-13 | 1.04e-10 | pass | sensitivity budget | 6.85e-13 | 2.24e-13 |
| generic orbit Omega_r | chi=0.99, p=25, e=0.1, x=-0.4 | 0.00678807922191631 | 0.00678807922191625 | 5.98e-17 | 7.22e-14 | pass | sensitivity budget | 1.42e-16 | 8.23e-17 |
| generic orbit Omega_theta | chi=0.99, p=25, e=0.1, x=-0.4 | 0.00796138467627765 | 0.00796138467627767 | 2.26e-17 | 1.69e-14 | pass | sensitivity budget | 4.56e-17 | 2.30e-17 |
| generic orbit Omega_phi | chi=0.99, p=25, e=0.1, x=-0.4 | -0.00782913456137411 | -0.00782913456137413 | 2.26e-17 | 1.69e-14 | pass | sensitivity budget | 4.74e-17 | 2.48e-17 |
| generic orbit Upsilon_r | chi=0.99, p=2.62481, e=0.5, x=0.9 | 0.981585929991716 | 0.981585929991707 | 9.44e-15 | 2.72e-12 | pass | sensitivity budget | 3.14e-15 | 6.30e-15 |
| generic orbit Upsilon_theta | chi=0.99, p=2.62481, e=0.5, x=0.9 | 2.16304109915218 | 2.16304109915219 | 2.22e-15 | 6.48e-13 | pass | sensitivity budget | 6.03e-16 | 1.62e-15 |
| generic orbit Upsilon_phi | chi=0.99, p=2.62481, e=0.5, x=0.9 | 3.36889428803993 | 3.36889428803993 | 4.88e-15 | 1.54e-12 | pass | sensitivity budget | 2.55e-15 | 2.33e-15 |
| generic orbit Gamma | chi=0.99, p=2.62481, e=0.5, x=0.9 | 19.1114543249425 | 19.1114543249424 | 2.84e-14 | 1.02e-11 | pass | sensitivity budget | 6.44e-15 | 2.20e-14 |
| generic orbit Omega_r | chi=0.99, p=2.62481, e=0.5, x=0.9 | 0.0513611320887622 | 0.0513611320887618 | 4.16e-16 | 1.27e-13 | pass | sensitivity budget | 1.44e-16 | 2.73e-16 |
| generic orbit Omega_theta | chi=0.99, p=2.62481, e=0.5, x=0.9 | 0.113180350504733 | 0.113180350504733 | 2.91e-16 | 8.06e-14 | pass | sensitivity budget | 7.11e-17 | 2.20e-16 |
| generic orbit Omega_phi | chi=0.99, p=2.62481, e=0.5, x=0.9 | 0.176276186561227 | 0.176276186561228 | 5.27e-16 | 1.57e-13 | pass | sensitivity budget | 2.02e-16 | 3.25e-16 |
| generic orbit Upsilon_r | chi=0.99, p=25, e=0.5, x=0.9 | 4.78647393292854 | 4.78647393292839 | 1.41e-13 | 4.09e-11 | pass | sensitivity budget | 1.05e-13 | 3.64e-14 |
| generic orbit Upsilon_theta | chi=0.99, p=25, e=0.5, x=0.9 | 5.24094556648926 | 5.24094556648925 | 1.15e-14 | 5.97e-12 | pass | sensitivity budget | 2.05e-16 | 1.13e-14 |
| generic orbit Upsilon_phi | chi=0.99, p=25, e=0.5, x=0.9 | 5.31519672082933 | 5.31519672082932 | 1.15e-14 | 6.03e-12 | pass | sensitivity budget | 1.60e-15 | 1.31e-14 |
| generic orbit Gamma | chi=0.99, p=25, e=0.5, x=0.9 | 1000.89290303598 | 1000.89290303597 | 5.00e-12 | 1.69e-09 | pass | sensitivity budget | 3.70e-12 | 1.30e-12 |
| generic orbit Omega_r | chi=0.99, p=25, e=0.5, x=0.9 | 0.00478220388855778 | 0.00478220388855766 | 1.17e-16 | 3.37e-14 | pass | sensitivity budget | 8.71e-17 | 3.00e-17 |
| generic orbit Omega_theta | chi=0.99, p=25, e=0.5, x=0.9 | 0.00523627008503313 | 0.00523627008503315 | 1.39e-17 | 1.44e-14 | pass | sensitivity budget | 1.88e-17 | 4.95e-18 |
| generic orbit Omega_phi | chi=0.99, p=25, e=0.5, x=0.9 | 0.00531045499943791 | 0.00531045499943792 | 1.47e-17 | 1.45e-14 | pass | sensitivity budget | 2.12e-17 | 6.47e-18 |
| generic orbit Upsilon_r | chi=0.99, p=7.33461, e=0.5, x=0.1 | 1.82946501865206 | 1.82946501865205 | 1.64e-14 | 3.43e-11 | pass | sensitivity budget | 2.66e-15 | 1.91e-14 |
| generic orbit Upsilon_theta | chi=0.99, p=7.33461, e=0.5, x=0.1 | 3.48926841369632 | 3.48926841369632 | 8.44e-15 | 1.50e-11 | pass | sensitivity budget | 1.84e-15 | 6.59e-15 |
| generic orbit Upsilon_phi | chi=0.99, p=7.33461, e=0.5, x=0.1 | 3.86135681657846 | 3.86135681657845 | 9.77e-15 | 1.64e-11 | pass | sensitivity budget | 1.75e-14 | 7.78e-15 |
| generic orbit Gamma | chi=0.99, p=7.33461, e=0.5, x=0.1 | 93.1609834009646 | 93.1609834009644 | 2.27e-13 | 4.82e-10 | pass | sensitivity budget | 1.09e-14 | 2.38e-13 |
| generic orbit Omega_r | chi=0.99, p=7.33461, e=0.5, x=0.1 | 0.0196376739689195 | 0.0196376739689194 | 1.28e-16 | 2.70e-13 | pass | sensitivity budget | 2.77e-17 | 1.56e-16 |
| generic orbit Omega_theta | chi=0.99, p=7.33461, e=0.5, x=0.1 | 0.0374541818507702 | 0.0374541818507704 | 1.80e-16 | 3.40e-13 | pass | sensitivity budget | 1.58e-17 | 1.65e-16 |
| generic orbit Omega_phi | chi=0.99, p=7.33461, e=0.5, x=0.1 | 0.0414482187243472 | 0.0414482187243472 | 0.00e+00 | 3.74e-13 | pass | sensitivity budget | 1.92e-16 | 1.92e-16 |
| generic orbit Upsilon_r | chi=0.99, p=25, e=0.5, x=0.1 | 4.69267466535247 | 4.69267466535247 | 0.00e+00 | 1.32e-10 | pass | sensitivity budget | 5.92e-16 | 5.92e-16 |
| generic orbit Upsilon_theta | chi=0.99, p=25, e=0.5, x=0.1 | 5.34305168343218 | 5.34305168343217 | 8.88e-16 | 9.89e-11 | pass | sensitivity budget | 8.40e-16 | 1.73e-15 |
| generic orbit Upsilon_phi | chi=0.99, p=25, e=0.5, x=0.1 | 5.4279029012177 | 5.4279029012177 | 1.78e-15 | 9.91e-11 | pass | sensitivity budget | 4.35e-15 | 2.57e-15 |
| generic orbit Gamma | chi=0.99, p=25, e=0.5, x=0.1 | 998.185910625138 | 998.185910625137 | 6.82e-13 | 5.46e-09 | pass | sensitivity budget | 1.16e-13 | 5.66e-13 |
| generic orbit Omega_r | chi=0.99, p=25, e=0.5, x=0.1 | 0.004701203067887 | 0.004701203067887 | 3.47e-18 | 1.08e-13 | pass | sensitivity budget | 2.58e-19 | 3.21e-18 |
| generic orbit Omega_theta | chi=0.99, p=25, e=0.5, x=0.1 | 0.00535276207223358 | 0.00535276207223358 | 2.60e-18 | 1.28e-13 | pass | sensitivity budget | 1.36e-18 | 1.25e-18 |
| generic orbit Omega_phi | chi=0.99, p=25, e=0.5, x=0.1 | 0.00543776749745781 | 0.00543776749745781 | 5.20e-18 | 1.28e-13 | pass | sensitivity budget | 5.03e-18 | 1.76e-19 |
| generic orbit Upsilon_r | chi=0.99, p=10.214, e=0.5, x=-0.4 | 2.24253230111388 | 2.24253230111385 | 2.89e-14 | 1.84e-11 | pass | sensitivity budget | 3.64e-14 | 7.54e-15 |
| generic orbit Upsilon_theta | chi=0.99, p=10.214, e=0.5, x=-0.4 | 4.03379446768044 | 4.03379446768044 | 6.22e-15 | 3.06e-12 | pass | sensitivity budget | 1.85e-15 | 8.07e-15 |
| generic orbit Upsilon_phi | chi=0.99, p=10.214, e=0.5, x=-0.4 | -3.75683882273204 | -3.75683882273203 | 7.55e-15 | 3.47e-12 | pass | sensitivity budget | 9.43e-17 | 7.46e-15 |
| generic orbit Gamma | chi=0.99, p=10.214, e=0.5, x=-0.4 | 170.295151366427 | 170.295151366426 | 7.39e-13 | 4.06e-10 | pass | sensitivity budget | 8.54e-13 | 1.15e-13 |
| generic orbit Omega_r | chi=0.99, p=10.214, e=0.5, x=-0.4 | 0.0131685035253211 | 0.013168503525321 | 1.13e-16 | 7.86e-14 | pass | sensitivity budget | 1.48e-16 | 3.56e-17 |
| generic orbit Omega_theta | chi=0.99, p=10.214, e=0.5, x=-0.4 | 0.0236870776138592 | 0.0236870776138592 | 6.59e-17 | 7.22e-14 | pass | sensitivity budget | 1.31e-16 | 6.49e-17 |
| generic orbit Omega_phi | chi=0.99, p=10.214, e=0.5, x=-0.4 | -0.0220607503653959 | -0.0220607503653959 | 4.86e-17 | 6.56e-14 | pass | sensitivity budget | 1.08e-16 | 5.98e-17 |
| generic orbit Upsilon_r | chi=0.99, p=25, e=0.5, x=-0.4 | 4.61735485390226 | 4.61735485390234 | 7.82e-14 | 4.81e-11 | pass | sensitivity budget | 4.82e-14 | 2.99e-14 |
| generic orbit Upsilon_theta | chi=0.99, p=25, e=0.5, x=-0.4 | 5.41836519015206 | 5.41836519015202 | 4.09e-14 | 1.11e-11 | pass | sensitivity budget | 1.89e-15 | 3.90e-14 |
| generic orbit Upsilon_phi | chi=0.99, p=25, e=0.5, x=-0.4 | -5.32670056292058 | -5.32670056292054 | 3.82e-14 | 1.11e-11 | pass | sensitivity budget | 1.86e-15 | 4.01e-14 |
| generic orbit Gamma | chi=0.99, p=25, e=0.5, x=-0.4 | 995.220475195208 | 995.220475195211 | 3.41e-12 | 2.14e-09 | pass | sensitivity budget | 2.15e-12 | 1.26e-12 |
| generic orbit Omega_r | chi=0.99, p=25, e=0.5, x=-0.4 | 0.00463952960071143 | 0.00463952960071149 | 6.33e-17 | 3.92e-14 | pass | sensitivity budget | 3.88e-17 | 2.45e-17 |
| generic orbit Omega_theta | chi=0.99, p=25, e=0.5, x=-0.4 | 0.00544438677177464 | 0.00544438677177458 | 5.98e-17 | 2.24e-14 | pass | sensitivity budget | 1.37e-17 | 4.61e-17 |
| generic orbit Omega_phi | chi=0.99, p=25, e=0.5, x=-0.4 | -0.00535228192715365 | -0.00535228192715359 | 5.64e-17 | 2.21e-14 | pass | sensitivity budget | 9.51e-18 | 4.69e-17 |
| generic orbit Upsilon_r | chi=0.99, p=3.00919, e=0.8, x=0.9 | 1.162329720316 | 1.16232972031607 | 6.99e-14 | 4.22e-11 | pass | sensitivity budget | 1.55e-14 | 5.44e-14 |
| generic orbit Upsilon_theta | chi=0.99, p=3.00919, e=0.8, x=0.9 | 2.34159524093586 | 2.34159524093584 | 2.18e-14 | 1.54e-11 | pass | sensitivity budget | 1.58e-16 | 2.16e-14 |
| generic orbit Upsilon_phi | chi=0.99, p=3.00919, e=0.8, x=0.9 | 3.5999995523158 | 3.59999955231576 | 4.35e-14 | 2.51e-11 | pass | sensitivity budget | 5.82e-15 | 3.77e-14 |
| generic orbit Gamma | chi=0.99, p=3.00919, e=0.8, x=0.9 | 45.0807294620667 | 45.0807294620683 | 1.54e-12 | 9.76e-10 | pass | sensitivity budget | 3.70e-13 | 1.17e-12 |
| generic orbit Omega_r | chi=0.99, p=3.00919, e=0.8, x=0.9 | 0.0257832944183843 | 0.025783294418385 | 6.70e-16 | 4.36e-13 | pass | sensitivity budget | 1.32e-16 | 5.37e-16 |
| generic orbit Omega_theta | chi=0.99, p=3.00919, e=0.8, x=0.9 | 0.0519422659943025 | 0.0519422659943002 | 2.26e-15 | 1.37e-12 | pass | sensitivity budget | 4.27e-16 | 1.83e-15 |
| generic orbit Omega_phi | chi=0.99, p=3.00919, e=0.8, x=0.9 | 0.0798567280359788 | 0.0798567280359751 | 3.69e-15 | 2.20e-12 | pass | sensitivity budget | 7.81e-16 | 2.91e-15 |
| generic orbit Upsilon_r | chi=0.99, p=25, e=0.8, x=0.9 | 4.81378839939915 | 4.81378839939943 | 2.73e-13 | 1.53e-10 | pass | sensitivity budget | 9.83e-14 | 1.74e-13 |
| generic orbit Upsilon_theta | chi=0.99, p=25, e=0.8, x=0.9 | 5.27233525705649 | 5.27233525705634 | 1.53e-13 | 2.95e-11 | pass | sensitivity budget | 2.01e-15 | 1.51e-13 |
| generic orbit Upsilon_phi | chi=0.99, p=25, e=0.8, x=0.9 | 5.34858001567047 | 5.34858001567032 | 1.47e-13 | 3.02e-11 | pass | sensitivity budget | 9.25e-16 | 1.46e-13 |
| generic orbit Gamma | chi=0.99, p=25, e=0.8, x=0.9 | 2898.88536854419 | 2898.88536854428 | 9.14e-11 | 5.18e-08 | pass | sensitivity budget | 3.20e-11 | 5.94e-11 |
| generic orbit Omega_r | chi=0.99, p=25, e=0.8, x=0.9 | 0.00166056528196444 | 0.00166056528196448 | 4.16e-17 | 2.37e-14 | pass | sensitivity budget | 1.55e-17 | 2.61e-17 |
| generic orbit Omega_theta | chi=0.99, p=25, e=0.8, x=0.9 | 0.00181874568558889 | 0.00181874568558878 | 1.10e-16 | 4.25e-14 | pass | sensitivity budget | 2.08e-17 | 8.92e-17 |
| generic orbit Omega_phi | chi=0.99, p=25, e=0.8, x=0.9 | 0.00184504709075699 | 0.00184504709075688 | 1.09e-16 | 4.32e-14 | pass | sensitivity budget | 2.07e-17 | 8.80e-17 |
| generic orbit Upsilon_r | chi=0.99, p=7.84819, e=0.8, x=0.1 | 2.03100982340549 | 2.03100982340549 | 1.78e-15 | 1.36e-10 | pass | sensitivity budget | 4.22e-14 | 4.04e-14 |
| generic orbit Upsilon_theta | chi=0.99, p=7.84819, e=0.8, x=0.1 | 3.66595202198124 | 3.66595202198122 | 2.84e-14 | 7.85e-11 | pass | sensitivity budget | 2.82e-16 | 2.87e-14 |
| generic orbit Upsilon_phi | chi=0.99, p=7.84819, e=0.8, x=0.1 | 4.05727977878878 | 4.05727977878877 | 6.22e-15 | 8.80e-11 | pass | sensitivity budget | 2.59e-14 | 3.21e-14 |
| generic orbit Gamma | chi=0.99, p=7.84819, e=0.8, x=0.1 | 257.446647565093 | 257.446647565093 | 1.14e-13 | 1.17e-08 | pass | sensitivity budget | 3.44e-12 | 3.56e-12 |
| generic orbit Omega_r | chi=0.99, p=7.84819, e=0.8, x=0.1 | 0.00788905135341477 | 0.00788905135341476 | 1.04e-17 | 1.72e-13 | pass | sensitivity budget | 5.81e-17 | 4.77e-17 |
| generic orbit Omega_theta | chi=0.99, p=7.84819, e=0.8, x=0.1 | 0.0142396572519141 | 0.014239657251914 | 1.16e-16 | 8.99e-13 | pass | sensitivity budget | 1.92e-16 | 3.08e-16 |
| generic orbit Omega_phi | chi=0.99, p=7.84819, e=0.8, x=0.1 | 0.0157596916377128 | 0.0157596916377127 | 3.12e-17 | 9.99e-13 | pass | sensitivity budget | 3.10e-16 | 3.41e-16 |
| generic orbit Upsilon_r | chi=0.99, p=25, e=0.8, x=0.1 | 4.73108094954934 | 4.73108094954906 | 2.75e-13 | 4.40e-10 | pass | sensitivity budget | 2.64e-14 | 3.02e-13 |
| generic orbit Upsilon_theta | chi=0.99, p=25, e=0.8, x=0.1 | 5.38964364419083 | 5.38964364419108 | 2.44e-13 | 5.21e-10 | pass | sensitivity budget | 2.21e-15 | 2.42e-13 |
| generic orbit Upsilon_phi | chi=0.99, p=25, e=0.8, x=0.1 | 5.47739239908723 | 5.47739239908744 | 2.11e-13 | 5.23e-10 | pass | sensitivity budget | 3.00e-14 | 2.41e-13 |
| generic orbit Gamma | chi=0.99, p=25, e=0.8, x=0.1 | 2872.41637490915 | 2872.41637490906 | 9.32e-11 | 1.52e-07 | pass | sensitivity budget | 9.02e-12 | 1.02e-10 |
| generic orbit Omega_r | chi=0.99, p=25, e=0.8, x=0.1 | 0.00164707352000769 | 0.00164707352000764 | 4.23e-17 | 6.65e-14 | pass | sensitivity budget | 4.10e-18 | 4.64e-17 |
| generic orbit Omega_theta | chi=0.99, p=25, e=0.8, x=0.1 | 0.001876344840278 | 0.00187634484027815 | 1.46e-16 | 2.80e-13 | pass | sensitivity budget | 5.08e-18 | 1.51e-16 |
| generic orbit Omega_phi | chi=0.99, p=25, e=0.8, x=0.1 | 0.00190689359903836 | 0.0019068935990385 | 1.36e-16 | 2.82e-13 | pass | sensitivity budget | 1.64e-17 | 1.52e-16 |
| generic orbit Upsilon_r | chi=0.99, p=10.9495, e=0.8, x=-0.4 | 2.4818634870125 | 2.48186348701224 | 2.57e-13 | 8.08e-11 | pass | sensitivity budget | 1.85e-14 | 2.39e-13 |
| generic orbit Upsilon_theta | chi=0.99, p=10.9495, e=0.8, x=-0.4 | 4.22600498067728 | 4.22600498067736 | 7.46e-14 | 1.53e-11 | pass | sensitivity budget | 3.14e-15 | 7.15e-14 |
| generic orbit Upsilon_phi | chi=0.99, p=10.9495, e=0.8, x=-0.4 | -3.94066638657317 | -3.94066638657324 | 6.26e-14 | 1.89e-11 | pass | sensitivity budget | 1.11e-15 | 6.15e-14 |
| generic orbit Gamma | chi=0.99, p=10.9495, e=0.8, x=-0.4 | 495.417281207194 | 495.417281207159 | 3.50e-11 | 1.10e-08 | pass | sensitivity budget | 2.69e-12 | 3.23e-11 |
| generic orbit Omega_r | chi=0.99, p=10.9495, e=0.8, x=-0.4 | 0.00500964254005207 | 0.00500964254005191 | 1.65e-16 | 5.37e-14 | pass | sensitivity budget | 1.00e-17 | 1.55e-16 |
| generic orbit Omega_theta | chi=0.99, p=10.9495, e=0.8, x=-0.4 | 0.0085301929120835 | 0.00853019291208426 | 7.53e-16 | 2.18e-13 | pass | sensitivity budget | 5.22e-17 | 7.01e-16 |
| generic orbit Omega_phi | chi=0.99, p=10.9495, e=0.8, x=-0.4 | -0.00795423683439316 | -0.00795423683439385 | 6.89e-16 | 1.97e-13 | pass | sensitivity budget | 4.55e-17 | 6.43e-16 |
| generic orbit Upsilon_r | chi=0.99, p=25, e=0.8, x=-0.4 | 4.66244785953355 | 4.66244785953355 | 0.00e+00 | 1.78e-10 | pass | sensitivity budget | 5.58e-14 | 5.58e-14 |
| generic orbit Upsilon_theta | chi=0.99, p=25, e=0.8, x=-0.4 | 5.47606175958107 | 5.47606175958086 | 2.01e-13 | 5.64e-11 | pass | sensitivity budget | 1.17e-15 | 2.00e-13 |
| generic orbit Upsilon_phi | chi=0.99, p=25, e=0.8, x=-0.4 | -5.38069947851597 | -5.38069947851577 | 1.99e-13 | 5.74e-11 | pass | sensitivity budget | 7.62e-16 | 1.98e-13 |
| generic orbit Gamma | chi=0.99, p=25, e=0.8, x=-0.4 | 2848.5570456436 | 2848.5570456436 | 9.09e-13 | 6.34e-08 | pass | sensitivity budget | 1.86e-11 | 1.77e-11 |
| generic orbit Omega_r | chi=0.99, p=25, e=0.8, x=-0.4 | 0.00163677531635324 | 0.00163677531635324 | 4.34e-19 | 2.68e-14 | pass | sensitivity budget | 8.95e-18 | 9.38e-18 |
| generic orbit Omega_theta | chi=0.99, p=25, e=0.8, x=-0.4 | 0.00192239848872109 | 0.00192239848872102 | 7.09e-17 | 6.23e-14 | pass | sensitivity budget | 1.28e-17 | 5.81e-17 |
| generic orbit Omega_phi | chi=0.99, p=25, e=0.8, x=-0.4 | -0.00188892108962496 | -0.00188892108962489 | 7.05e-17 | 6.11e-14 | pass | sensitivity budget | 1.25e-17 | 5.80e-17 |

## tmm (`test_ext_optics_tmm.py`)

| quantity | inputs | engine | library | diff | tol | status | basis | eng err | lib err |
|---|---|---|---|---|---|---|---|---|---|
| fresnel r (s) | air/glass, th0=0 deg | -0.2 | -0.2 | 0.00e+00 | 1.25e-14 | pass | TMM rounding | 1.11e-17 | 1.11e-17 |
| fresnel t (s) | air/glass, th0=0 deg | 0.8 | 0.8 | 0.00e+00 | 1.27e-14 | pass | TMM rounding | 4.44e-17 | 4.44e-17 |
| fresnel R (s) | air/glass, th0=0 deg | 0.04 | 0.04 | 0.00e+00 | 3.60e-15 | pass | TMM rounding | 7.77e-18 | 7.77e-18 |
| fresnel T (s) | air/glass, th0=0 deg | 0.96 | 0.96 | 0.00e+00 | 8.27e-15 | pass | TMM rounding | 1.87e-16 | 1.87e-16 |
| fresnel r (p) | air/glass, th0=0 deg | 0.2 | 0.2 | 0.00e+00 | 1.25e-14 | pass | TMM rounding | 1.11e-17 | 1.11e-17 |
| fresnel t (p) | air/glass, th0=0 deg | 0.8 | 0.8 | 0.00e+00 | 1.27e-14 | pass | TMM rounding | 4.44e-17 | 4.44e-17 |
| fresnel R (p) | air/glass, th0=0 deg | 0.04 | 0.04 | 0.00e+00 | 3.60e-15 | pass | TMM rounding | 7.77e-18 | 7.77e-18 |
| fresnel T (p) | air/glass, th0=0 deg | 0.96 | 0.96 | 0.00e+00 | 8.27e-15 | pass | TMM rounding | 1.87e-16 | 1.87e-16 |
| fresnel r (s) | air/glass, th0=30 deg | -0.240408205773457 | -0.240408205773457 | 2.78e-17 | 1.58e-14 | pass | TMM rounding | 8.88e-17 | 6.10e-17 |
| fresnel t (s) | air/glass, th0=30 deg | 0.759591794226543 | 0.759591794226543 | 1.11e-16 | 1.58e-14 | pass | TMM rounding | 6.10e-17 | 1.72e-16 |
| fresnel R (s) | air/glass, th0=30 deg | 0.057796105403213 | 0.0577961054032131 | 1.39e-17 | 5.41e-15 | pass | TMM rounding | 4.30e-17 | 2.91e-17 |
| fresnel T (s) | air/glass, th0=30 deg | 0.942203894596787 | 0.942203894596787 | 3.33e-16 | 9.72e-15 | pass | TMM rounding | 2.64e-17 | 3.07e-16 |
| fresnel r (p) | air/glass, th0=30 deg | 0.158899800341064 | 0.158899800341064 | 0.00e+00 | 1.50e-14 | pass | TMM rounding | 5.86e-18 | 5.86e-18 |
| fresnel t (p) | air/glass, th0=30 deg | 0.772599866894043 | 0.772599866894043 | 0.00e+00 | 1.43e-14 | pass | TMM rounding | 5.16e-17 | 5.16e-17 |
| fresnel R (p) | air/glass, th0=30 deg | 0.02524914654843 | 0.02524914654843 | 0.00e+00 | 3.29e-15 | pass | TMM rounding | 3.35e-18 | 3.35e-18 |
| fresnel T (p) | air/glass, th0=30 deg | 0.97475085345157 | 0.97475085345157 | 0.00e+00 | 8.28e-15 | pass | TMM rounding | 2.57e-16 | 2.57e-16 |
| fresnel r (s) | air/glass, th0=56.3099 deg | -0.384615384615385 | -0.384615384615385 | 5.55e-17 | 2.41e-14 | pass | TMM rounding | 2.85e-17 | 8.40e-17 |
| fresnel t (s) | air/glass, th0=56.3099 deg | 0.615384615384615 | 0.615384615384615 | 2.22e-16 | 2.30e-14 | pass | TMM rounding | 2.70e-17 | 1.95e-16 |
| fresnel R (s) | air/glass, th0=56.3099 deg | 0.14792899408284 | 0.14792899408284 | 5.55e-17 | 1.38e-14 | pass | TMM rounding | 1.16e-17 | 6.71e-17 |
| fresnel T (s) | air/glass, th0=56.3099 deg | 0.85207100591716 | 0.852071005917159 | 6.66e-16 | 1.64e-14 | pass | TMM rounding | 1.27e-16 | 5.39e-16 |
| fresnel r (p) | air/glass, th0=56.3099 deg | 0 | -6.6716100708112e-17 | 6.67e-17 | 2.29e-14 | pass | TMM rounding | 8.37e-18 | 7.51e-17 |
| fresnel t (p) | air/glass, th0=56.3099 deg | 0.666666666666667 | 0.666666666666667 | 1.11e-16 | 1.85e-14 | pass | TMM rounding | 4.26e-17 | 1.54e-16 |
| fresnel R (p) | air/glass, th0=56.3099 deg | 0 | 4.45103809369495e-33 | 4.45e-33 | 2.64e-31 | pass | TMM rounding | 7.00e-35 | 4.38e-33 |
| fresnel T (p) | air/glass, th0=56.3099 deg | 1 | 1 | 4.44e-16 | 5.77e-15 | pass | TMM rounding | 7.00e-35 | 4.44e-16 |
| fresnel r (s) | air/glass, th0=70 deg | -0.547352425712472 | -0.547352425712471 | 3.33e-16 | 3.45e-14 | pass | TMM rounding | 3.45e-18 | 3.37e-16 |
| fresnel t (s) | air/glass, th0=70 deg | 0.452647574287528 | 0.452647574287528 | 1.11e-16 | 3.22e-14 | pass | TMM rounding | 5.21e-17 | 5.90e-17 |
| fresnel R (s) | air/glass, th0=70 deg | 0.299594677933327 | 0.299594677933327 | 3.89e-16 | 2.99e-14 | pass | TMM rounding | 5.33e-18 | 3.83e-16 |
| fresnel T (s) | air/glass, th0=70 deg | 0.700405322066673 | 0.700405322066673 | 2.22e-16 | 2.99e-14 | pass | TMM rounding | 5.33e-18 | 2.17e-16 |
| fresnel r (p) | air/glass, th0=70 deg | -0.20613197908525 | -0.20613197908525 | 2.78e-16 | 3.99e-14 | pass | TMM rounding | 3.05e-17 | 2.47e-16 |
| fresnel t (p) | air/glass, th0=70 deg | 0.5292453472765 | 0.5292453472765 | 2.22e-16 | 2.73e-14 | pass | TMM rounding | 2.03e-17 | 2.02e-16 |
| fresnel R (p) | air/glass, th0=70 deg | 0.0424903928016021 | 0.042490392801602 | 1.11e-16 | 1.24e-14 | pass | TMM rounding | 1.02e-17 | 1.01e-16 |
| fresnel T (p) | air/glass, th0=70 deg | 0.957509607198398 | 0.957509607198399 | 7.77e-16 | 1.70e-14 | pass | TMM rounding | 3.83e-17 | 8.15e-16 |
| fresnel r (s) | air/glass, th0=89 deg | -0.969263721231228 | -0.969263721231231 | 3.11e-15 | 3.85e-13 | pass | TMM rounding | 6.79e-17 | 3.04e-15 |
| fresnel t (s) | air/glass, th0=89 deg | 0.0307362787687722 | 0.0307362787687691 | 3.08e-15 | 3.79e-13 | pass | TMM rounding | 1.99e-18 | 3.08e-15 |
| fresnel R (s) | air/glass, th0=89 deg | 0.939472161295007 | 0.939472161295013 | 6.11e-15 | 7.30e-13 | pass | TMM rounding | 1.63e-16 | 5.94e-15 |
| fresnel T (s) | air/glass, th0=89 deg | 0.0605278387049927 | 0.0605278387049806 | 1.21e-14 | 7.19e-13 | pass | TMM rounding | 3.44e-18 | 1.21e-14 |
| fresnel r (p) | air/glass, th0=89 deg | -0.932146843724405 | -0.932146843724412 | 6.77e-15 | 8.26e-13 | pass | TMM rounding | 6.80e-17 | 6.70e-15 |
| fresnel t (p) | air/glass, th0=89 deg | 0.0452354375170634 | 0.045235437517059 | 4.45e-15 | 5.47e-13 | pass | TMM rounding | 9.34e-19 | 4.45e-15 |
| fresnel R (p) | air/glass, th0=89 deg | 0.86889773826537 | 0.868897738265383 | 1.27e-14 | 1.51e-12 | pass | TMM rounding | 1.23e-16 | 1.25e-14 |
| fresnel T (p) | air/glass, th0=89 deg | 0.13110226173463 | 0.131102261734604 | 2.58e-14 | 1.50e-12 | pass | TMM rounding | 1.56e-17 | 2.58e-14 |
| fresnel r (s) | air/glass, th0=89.9 deg | -0.996882731774177 | -0.996882731774171 | 6.44e-15 | 3.66e-12 | pass | TMM rounding | 1.29e-16 | 6.57e-15 |
| fresnel t (s) | air/glass, th0=89.9 deg | 0.00311726822582268 | 0.00311726822582902 | 6.34e-15 | 3.66e-12 | pass | TMM rounding | 1.76e-19 | 6.34e-15 |
| fresnel R (s) | air/glass, th0=89.9 deg | 0.993775180909546 | 0.993775180909533 | 1.28e-14 | 7.28e-12 | pass | TMM rounding | 2.73e-16 | 1.30e-14 |
| fresnel T (s) | air/glass, th0=89.9 deg | 0.00622481909045364 | 0.00622481909047894 | 2.53e-14 | 7.27e-12 | pass | TMM rounding | 2.84e-19 | 2.53e-14 |
| fresnel r (p) | air/glass, th0=89.9 deg | -0.992999784959349 | -0.992999784959335 | 1.42e-14 | 8.20e-12 | pass | TMM rounding | 1.26e-16 | 1.43e-14 |
| fresnel t (p) | air/glass, th0=89.9 deg | 0.00466681002710063 | 0.0046668100271101 | 9.47e-15 | 5.46e-12 | pass | TMM rounding | 2.99e-20 | 9.47e-15 |
| fresnel R (p) | air/glass, th0=89.9 deg | 0.986048572929313 | 0.986048572929285 | 2.82e-14 | 1.62e-11 | pass | TMM rounding | 2.18e-16 | 2.84e-14 |
| fresnel T (p) | air/glass, th0=89.9 deg | 0.0139514270706865 | 0.0139514270707431 | 5.66e-14 | 1.62e-11 | pass | TMM rounding | 6.15e-19 | 5.66e-14 |
| fresnel r (s) | air/glass, th0=89.999 deg | -0.999968779088581 | -0.999968779087423 | 1.16e-12 | 3.64e-10 | pass | TMM rounding | 6.23e-17 | 1.16e-12 |
| fresnel t (s) | air/glass, th0=89.999 deg | 3.12209114190011e-05 | 3.12209125772161e-05 | 1.16e-12 | 3.64e-10 | pass | TMM rounding | 2.58e-21 | 1.16e-12 |
| fresnel R (s) | air/glass, th0=89.999 deg | 0.999937559151907 | 0.999937559149591 | 2.32e-12 | 7.28e-10 | pass | TMM rounding | 9.93e-17 | 2.32e-12 |
| fresnel T (s) | air/glass, th0=89.999 deg | 6.24408480926924e-05 | 6.24408527254801e-05 | 4.63e-12 | 7.28e-10 | pass | TMM rounding | 2.98e-21 | 4.63e-12 |
| fresnel r (p) | air/glass, th0=89.999 deg | -0.999929754320016 | -0.99992975431741 | 2.61e-12 | 8.19e-10 | pass | TMM rounding | 1.95e-17 | 2.61e-12 |
| fresnel t (p) | air/glass, th0=89.999 deg | 4.68304533226049e-05 | 4.68304550598595e-05 | 1.74e-12 | 5.46e-10 | pass | TMM rounding | 7.06e-26 | 1.74e-12 |
| fresnel R (p) | air/glass, th0=89.999 deg | 0.999859513574488 | 0.999859513569276 | 5.21e-12 | 1.64e-09 | pass | TMM rounding | 8.46e-17 | 5.21e-12 |
| fresnel T (p) | air/glass, th0=89.999 deg | 0.000140486425512258 | 0.00014048643593542 | 1.04e-11 | 1.64e-09 | pass | TMM rounding | 2.21e-20 | 1.04e-11 |
| fresnel r (s) | glass/air, th0=0 deg | 0.2 | 0.2 | 0.00e+00 | 1.25e-14 | pass | TMM rounding | 1.11e-17 | 1.11e-17 |
| fresnel t (s) | glass/air, th0=0 deg | 1.2 | 1.2 | 2.22e-16 | 1.40e-14 | pass | TMM rounding | 4.44e-17 | 1.78e-16 |
| fresnel R (s) | glass/air, th0=0 deg | 0.04 | 0.04 | 0.00e+00 | 3.60e-15 | pass | TMM rounding | 7.77e-18 | 7.77e-18 |
| fresnel T (s) | glass/air, th0=0 deg | 0.96 | 0.96 | 2.22e-16 | 8.27e-15 | pass | TMM rounding | 3.55e-17 | 1.87e-16 |
| fresnel r (p) | glass/air, th0=0 deg | -0.2 | -0.2 | 0.00e+00 | 1.25e-14 | pass | TMM rounding | 1.11e-17 | 1.11e-17 |
| fresnel t (p) | glass/air, th0=0 deg | 1.2 | 1.2 | 2.22e-16 | 1.40e-14 | pass | TMM rounding | 4.44e-17 | 1.78e-16 |
| fresnel R (p) | glass/air, th0=0 deg | 0.04 | 0.04 | 0.00e+00 | 3.60e-15 | pass | TMM rounding | 7.77e-18 | 7.77e-18 |
| fresnel T (p) | glass/air, th0=0 deg | 0.96 | 0.96 | 2.22e-16 | 8.27e-15 | pass | TMM rounding | 3.55e-17 | 1.87e-16 |
| fresnel r (s) | glass/air, th0=30 deg | 0.325227291513248 | 0.325227291513248 | 0.00e+00 | 2.40e-14 | pass | TMM rounding | 3.76e-17 | 3.76e-17 |
| fresnel t (s) | glass/air, th0=30 deg | 1.32522729151325 | 1.32522729151325 | 0.00e+00 | 2.53e-14 | pass | TMM rounding | 3.76e-17 | 3.76e-17 |
| fresnel R (s) | glass/air, th0=30 deg | 0.105772791145043 | 0.105772791145043 | 0.00e+00 | 1.20e-14 | pass | TMM rounding | 3.06e-17 | 3.06e-17 |
| fresnel T (s) | glass/air, th0=30 deg | 0.894227208854957 | 0.894227208854957 | 0.00e+00 | 1.54e-14 | pass | TMM rounding | 1.55e-16 | 1.55e-16 |
| fresnel r (p) | glass/air, th0=30 deg | -0.067878888070656 | -0.067878888070656 | 0.00e+00 | 1.82e-14 | pass | TMM rounding | 1.68e-18 | 1.68e-18 |
| fresnel t (p) | glass/air, th0=30 deg | 1.39818166789402 | 1.39818166789402 | 2.22e-16 | 3.78e-14 | pass | TMM rounding | 1.78e-16 | 4.42e-17 |
| fresnel R (p) | glass/air, th0=30 deg | 0.00460754344570865 | 0.00460754344570865 | 0.00e+00 | 1.63e-15 | pass | TMM rounding | 3.17e-19 | 3.17e-19 |
| fresnel T (p) | glass/air, th0=30 deg | 0.995392456554291 | 0.995392456554292 | 2.22e-16 | 7.16e-15 | pass | TMM rounding | 3.35e-17 | 1.89e-16 |
| fresnel r (s) | glass/air, th0=41.8103 deg | 0.999646670877049 | 0.99964667087827 | 1.22e-12 | 1.23e-10 | pass | TMM rounding | 2.96e-14 | 1.25e-12 |
| fresnel t (s) | glass/air, th0=41.8103 deg | 1.99964667087705 | 1.99964667087827 | 1.22e-12 | 1.23e-10 | pass | TMM rounding | 2.96e-14 | 1.25e-12 |
| fresnel R (s) | glass/air, th0=41.8103 deg | 0.999293466595567 | 0.999293466598008 | 2.44e-12 | 2.45e-10 | pass | TMM rounding | 5.93e-14 | 2.50e-12 |
| fresnel T (s) | glass/air, th0=41.8103 deg | 0.000706533404433529 | 0.000706533401992396 | 2.44e-12 | 2.45e-10 | pass | TMM rounding | 5.89e-14 | 2.50e-12 |
| fresnel r (p) | glass/air, th0=41.8103 deg | 0.999205184992915 | 0.999205184995661 | 2.75e-12 | 2.76e-10 | pass | TMM rounding | 6.63e-14 | 2.81e-12 |
| fresnel t (p) | glass/air, th0=41.8103 deg | 2.99880777748937 | 2.99880777749349 | 4.12e-12 | 4.14e-10 | pass | TMM rounding | 9.90e-14 | 4.22e-12 |
| fresnel R (p) | glass/air, th0=41.8103 deg | 0.998411001716726 | 0.998411001722214 | 5.49e-12 | 5.52e-10 | pass | TMM rounding | 1.32e-13 | 5.62e-12 |
| fresnel T (p) | glass/air, th0=41.8103 deg | 0.00158899828327378 | 0.00158899827778608 | 5.49e-12 | 5.52e-10 | pass | TMM rounding | 1.32e-13 | 5.62e-12 |
| fresnel r (s) | glass/air, th0=41.8103 deg | 0.999999937557-0.000353391555218j | 0.999999937557-0.000353391554931j | 2.87e-13 | 1.23e-10 | pass | TMM rounding | 3.21e-13 | 3.43e-14 |
| fresnel t (s) | glass/air, th0=41.8103 deg | 1.99999993756-0.000353391555218j | 1.99999993756-0.000353391554931j | 2.87e-13 | 1.23e-10 | pass | TMM rounding | 3.21e-13 | 3.43e-14 |
| fresnel R (s) | glass/air, th0=41.8103 deg | 1 | 1 | 0.00e+00 | 2.74e-14 | pass | TMM rounding | 2.22e-16 | 2.22e-16 |
| fresnel T (s) | glass/air, th0=41.8103 deg | 0 | 2.19071480160646e-16 | 2.19e-16 | 1.63e-14 | pass | TMM rounding | 0.00e+00 | 2.19e-16 |
| fresnel r (p) | glass/air, th0=41.8103 deg | 0.999999683883-0.000795130898389j | 0.999999683883-0.000795130897744j | 6.45e-13 | 2.76e-10 | pass | TMM rounding | 7.22e-13 | 7.71e-14 |
| fresnel t (p) | glass/air, th0=41.8103 deg | 2.99999952583-0.00119269634758j | 2.99999952583-0.00119269634662j | 9.68e-13 | 4.14e-10 | pass | TMM rounding | 1.08e-12 | 1.16e-13 |
| fresnel R (p) | glass/air, th0=41.8103 deg | 1 | 1 | 2.22e-16 | 4.79e-14 | pass | TMM rounding | 0.00e+00 | 2.22e-16 |
| fresnel T (p) | glass/air, th0=41.8103 deg | 0 | 4.92910767842163e-16 | 4.93e-16 | 3.68e-14 | pass | TMM rounding | 0.00e+00 | 4.93e-16 |
| fresnel r (s) | glass/air, th0=45 deg | 0.8-0.6j | 0.8-0.6j | 1.11e-16 | 1.08e-13 | pass | TMM rounding | 4.16e-16 | 3.56e-16 |
| fresnel t (s) | glass/air, th0=45 deg | 1.8-0.6j | 1.8-0.6j | 2.48e-16 | 1.08e-13 | pass | TMM rounding | 4.95e-16 | 4.58e-16 |
| fresnel R (s) | glass/air, th0=45 deg | 1 | 1 | 2.22e-16 | 4.15e-14 | pass | TMM rounding | 0.00e+00 | 2.22e-16 |
| fresnel T (s) | glass/air, th0=45 deg | 0 | 2.20436423846524e-16 | 2.20e-16 | 2.09e-14 | pass | TMM rounding | 0.00e+00 | 2.20e-16 |
| fresnel r (p) | glass/air, th0=45 deg | 0.28-0.96j | 0.28-0.96j | 6.87e-16 | 1.82e-13 | pass | TMM rounding | 6.91e-16 | 8.98e-16 |
| fresnel t (p) | glass/air, th0=45 deg | 1.92-1.44j | 1.92-1.44j | 1.11e-15 | 2.70e-13 | pass | TMM rounding | 1.28e-15 | 1.02e-15 |
| fresnel R (p) | glass/air, th0=45 deg | 1 | 0.999999999999999 | 1.55e-15 | 5.97e-14 | pass | TMM rounding | 4.44e-16 | 1.11e-15 |
| fresnel T (p) | glass/air, th0=45 deg | 0 | 3.52698278154438e-16 | 3.53e-16 | 3.35e-14 | pass | TMM rounding | 0.00e+00 | 3.53e-16 |
| fresnel r (s) | glass/air, th0=60 deg | -0.1-0.994987437107j | -0.1-0.994987437107j | 5.34e-16 | 9.00e-14 | pass | TMM rounding | 7.14e-17 | 4.87e-16 |
| fresnel t (s) | glass/air, th0=60 deg | 0.9-0.994987437107j | 0.9-0.994987437107j | 4.44e-16 | 8.80e-14 | pass | TMM rounding | 1.11e-16 | 3.37e-16 |
| fresnel R (s) | glass/air, th0=60 deg | 1 | 1 | 4.44e-16 | 5.52e-14 | pass | TMM rounding | 0.00e+00 | 4.44e-16 |
| fresnel T (s) | glass/air, th0=60 deg | 0 | 1.90903542970483e-16 | 1.91e-16 | 2.23e-14 | pass | TMM rounding | 0.00e+00 | 1.91e-16 |
| fresnel r (p) | glass/air, th0=60 deg | -0.721739130435-0.692165173639j | -0.721739130435-0.692165173639j | 4.00e-16 | 7.42e-14 | pass | TMM rounding | 1.32e-16 | 3.74e-16 |
| fresnel t (p) | glass/air, th0=60 deg | 0.417391304348-1.03824776046j | 0.417391304348-1.03824776046j | 4.97e-16 | 8.94e-14 | pass | TMM rounding | 1.18e-16 | 3.78e-16 |
| fresnel R (p) | glass/air, th0=60 deg | 1 | 1 | 2.22e-16 | 4.18e-14 | pass | TMM rounding | 2.22e-16 | 0.00e+00 |
| fresnel T (p) | glass/air, th0=60 deg | 0 | 1.32802464675119e-16 | 1.33e-16 | 1.55e-14 | pass | TMM rounding | 0.00e+00 | 1.33e-16 |
| fresnel r (s) | glass/air, th0=89.9 deg | -0.999989033784-0.00468319460376j | -0.999989033784-0.00468319460377j | 9.53e-15 | 5.51e-12 | pass | TMM rounding | 9.10e-17 | 9.53e-15 |
| fresnel t (s) | glass/air, th0=89.9 deg | 1.09662159773e-05-0.00468319460376j | 1.09662159774e-05-0.00468319460377j | 9.53e-15 | 5.50e-12 | pass | TMM rounding | 2.56e-19 | 9.53e-15 |
| fresnel R (s) | glass/air, th0=89.9 deg | 1 | 1 | 2.22e-16 | 3.57e-14 | pass | TMM rounding | 2.22e-16 | 0.00e+00 |
| fresnel T (s) | glass/air, th0=89.9 deg | 0 | 7.69466714869837e-19 | 7.69e-19 | 9.67e-17 | pass | TMM rounding | 0.00e+00 | 7.69e-19 |
| fresnel r (p) | glass/air, th0=89.9 deg | -0.999997833824-0.00208142898223j | -0.999997833824-0.00208142898224j | 4.26e-15 | 2.45e-12 | pass | TMM rounding | 1.27e-16 | 4.25e-15 |
| fresnel t (p) | glass/air, th0=89.9 deg | 3.2492634753e-06-0.00312214347335j | 3.24926347532e-06-0.00312214347336j | 6.35e-15 | 3.67e-12 | pass | TMM rounding | 3.41e-19 | 6.35e-15 |
| fresnel R (p) | glass/air, th0=89.9 deg | 1 | 0.999999999999999 | 1.11e-15 | 2.21e-14 | pass | TMM rounding | 4.44e-16 | 6.66e-16 |
| fresnel T (p) | glass/air, th0=89.9 deg | 0 | 3.41986711358872e-19 | 3.42e-19 | 4.30e-17 | pass | TMM rounding | 0.00e+00 | 3.42e-19 |
| fresnel r (s) | air/metal, th0=0 deg | -0.805352798054-0.535279805353j | -0.805352798054-0.535279805353j | 1.11e-16 | 1.78e-14 | pass | TMM rounding | 7.59e-17 | 1.87e-16 |
| fresnel t (s) | air/metal, th0=0 deg | 0.194647201946-0.535279805353j | 0.194647201946-0.535279805353j | 0.00e+00 | 1.35e-14 | pass | TMM rounding | 1.15e-17 | 1.15e-17 |
| fresnel R (s) | air/metal, th0=0 deg | 0.935117599351176 | 0.935117599351176 | 0.00e+00 | 2.02e-14 | pass | TMM rounding | 2.07e-16 | 2.07e-16 |
| fresnel T (s) | air/metal, th0=0 deg | 0.064882400648824 | 0.064882400648824 | 0.00e+00 | 5.40e-15 | pass | TMM rounding | 9.75e-19 | 9.75e-19 |
| fresnel r (p) | air/metal, th0=0 deg | 0.805352798054+0.535279805353j | 0.805352798054+0.535279805353j | 1.11e-16 | 1.78e-14 | pass | TMM rounding | 7.59e-17 | 1.87e-16 |
| fresnel t (p) | air/metal, th0=0 deg | 0.194647201946-0.535279805353j | 0.194647201946-0.535279805353j | 0.00e+00 | 1.35e-14 | pass | TMM rounding | 1.15e-17 | 1.15e-17 |
| fresnel R (p) | air/metal, th0=0 deg | 0.935117599351176 | 0.935117599351176 | 0.00e+00 | 2.02e-14 | pass | TMM rounding | 2.07e-16 | 2.07e-16 |
| fresnel T (p) | air/metal, th0=0 deg | 0.064882400648824 | 0.064882400648824 | 0.00e+00 | 5.40e-15 | pass | TMM rounding | 9.75e-19 | 9.75e-19 |
| fresnel r (s) | air/metal, th0=45 deg | -0.895388252632-0.391087395491j | -0.895388252632-0.391087395491j | 0.00e+00 | 1.99e-14 | pass | TMM rounding | 7.23e-17 | 7.23e-17 |
| fresnel t (s) | air/metal, th0=45 deg | 0.104611747368-0.391087395491j | 0.104611747368-0.391087395491j | 5.55e-17 | 1.51e-14 | pass | TMM rounding | 4.25e-17 | 1.49e-17 |
| fresnel R (s) | air/metal, th0=45 deg | 0.954669473863016 | 0.954669473863016 | 0.00e+00 | 2.10e-14 | pass | TMM rounding | 1.38e-16 | 1.38e-16 |
| fresnel T (s) | air/metal, th0=45 deg | 0.0453305261369835 | 0.0453305261369835 | 1.39e-17 | 4.75e-15 | pass | TMM rounding | 5.82e-18 | 8.06e-18 |
| fresnel r (p) | air/metal, th0=45 deg | 0.648770772039+0.70035011935j | 0.648770772039+0.70035011935j | 2.48e-16 | 3.14e-14 | pass | TMM rounding | 6.15e-17 | 2.49e-16 |
| fresnel t (p) | air/metal, th0=45 deg | 0.24162026974-0.484983853967j | 0.24162026974-0.484983853967j | 6.21e-17 | 1.53e-14 | pass | TMM rounding | 4.56e-17 | 2.40e-17 |
| fresnel R (p) | air/metal, th0=45 deg | 0.911393804325889 | 0.911393804325888 | 6.66e-16 | 2.81e-14 | pass | TMM rounding | 1.35e-16 | 5.31e-16 |
| fresnel T (p) | air/metal, th0=45 deg | 0.0886061956741112 | 0.0886061956741112 | 1.39e-17 | 8.47e-15 | pass | TMM rounding | 3.73e-18 | 1.01e-17 |
| fresnel r (s) | air/metal, th0=80 deg | -0.989418289054-0.0997376644021j | -0.989418289054-0.0997376644021j | 1.78e-16 | 2.72e-14 | pass | TMM rounding | 7.59e-17 | 1.25e-16 |
| fresnel t (s) | air/metal, th0=80 deg | 0.0105817109457-0.0997376644021j | 0.0105817109457-0.0997376644021j | 1.41e-16 | 2.16e-14 | pass | TMM rounding | 2.01e-17 | 1.21e-16 |
| fresnel R (s) | air/metal, th0=80 deg | 0.988896152415518 | 0.988896152415517 | 2.22e-16 | 1.96e-14 | pass | TMM rounding | 2.21e-16 | 1.14e-18 |
| fresnel T (s) | air/metal, th0=80 deg | 0.0111038475844826 | 0.0111038475844826 | 3.12e-17 | 2.99e-15 | pass | TMM rounding | 4.07e-18 | 2.72e-17 |
| fresnel r (p) | air/metal, th0=80 deg | -0.507036753933+0.798863585515j | -0.507036753933+0.798863585515j | 1.02e-15 | 1.78e-13 | pass | TMM rounding | 1.97e-16 | 9.05e-16 |
| fresnel t (p) | air/metal, th0=80 deg | 0.250214316689-0.134218297797j | 0.250214316689-0.134218297797j | 3.55e-16 | 5.04e-14 | pass | TMM rounding | 4.78e-17 | 3.08e-16 |
| fresnel R (p) | air/metal, th0=80 deg | 0.895269298100318 | 0.895269298100318 | 2.22e-16 | 6.99e-14 | pass | TMM rounding | 2.29e-16 | 6.68e-18 |
| fresnel T (p) | air/metal, th0=80 deg | 0.104730701899682 | 0.104730701899682 | 2.36e-16 | 1.93e-14 | pass | TMM rounding | 2.11e-17 | 2.15e-16 |
| fresnel r (s) | air/metal, th0=89.99 deg | -0.999994390569-0.000100934213242j | -0.999994390569-0.000100934213066j | 1.75e-13 | 1.18e-11 | pass | TMM rounding | 7.78e-17 | 1.75e-13 |
| fresnel t (s) | air/metal, th0=89.99 deg | 5.6094306062e-06-0.000100934213242j | 5.60943059646e-06-0.000100934213066j | 1.75e-13 | 1.18e-11 | pass | TMM rounding | 1.29e-21 | 1.75e-13 |
| fresnel R (s) | air/metal, th0=89.99 deg | 0.999988791357969 | 0.999988791357988 | 1.89e-14 | 1.32e-12 | pass | TMM rounding | 2.09e-16 | 1.91e-14 |
| fresnel T (s) | air/metal, th0=89.99 deg | 1.12086420312886e-05 | 1.12086419923878e-05 | 3.89e-14 | 1.31e-12 | pass | TMM rounding | 1.78e-21 | 3.89e-14 |
| fresnel r (p) | air/metal, th0=89.99 deg | -0.999926968207+0.00110245991522j | -0.999926968207+0.00110245991331j | 1.92e-12 | 1.29e-10 | pass | TMM rounding | 9.38e-17 | 1.92e-12 |
| fresnel t (p) | air/metal, th0=89.99 deg | 0.000334192504923-1.87675514203e-06j | 0.000334192504343-1.87675513845e-06j | 5.80e-13 | 3.90e-11 | pass | TMM rounding | 4.27e-20 | 5.80e-13 |
| fresnel R (p) | air/metal, th0=89.99 deg | 0.999855157165601 | 0.999855157165852 | 2.51e-13 | 1.70e-11 | pass | TMM rounding | 1.78e-16 | 2.51e-13 |
| fresnel T (p) | air/metal, th0=89.99 deg | 0.000144842834399262 | 0.000144842833896586 | 5.03e-13 | 1.69e-11 | pass | TMM rounding | 4.29e-20 | 5.03e-13 |
| stack r (s) | AR MgF2 on glass, th0=0 deg | -0.118787451533-2.33137901023e-17j | -0.118787451533-2.33137901023e-17j | 1.25e-16 | 2.73e-14 | pass | TMM rounding | 1.25e-16 | 1.83e-17 |
| stack t (s) | AR MgF2 on glass, th0=0 deg | 2.32733147723e-16+0.810715544589j | 2.32733147723e-16+0.810715544589j | 1.11e-16 | 3.79e-14 | pass | TMM rounding | 1.89e-16 | 1.91e-16 |
| stack R (s) | AR MgF2 on glass, th0=0 deg | 0.0141104586417784 | 0.0141104586417784 | 2.95e-17 | 4.48e-15 | pass | TMM rounding | 2.98e-17 | 3.54e-19 |
| stack T (s) | AR MgF2 on glass, th0=0 deg | 0.985889541358221 | 0.985889541358222 | 4.44e-16 | 2.77e-14 | pass | TMM rounding | 3.19e-16 | 1.25e-16 |
| stack r (p) | AR MgF2 on glass, th0=0 deg | 0.118787451533+2.33137901023e-17j | 0.118787451533+2.33137901023e-17j | 4.16e-17 | 2.73e-14 | pass | TMM rounding | 4.68e-17 | 1.83e-17 |
| stack t (p) | AR MgF2 on glass, th0=0 deg | 2.32733147723e-16+0.810715544589j | 2.32733147723e-16+0.810715544589j | 1.11e-16 | 3.79e-14 | pass | TMM rounding | 1.89e-16 | 1.91e-16 |
| stack R (p) | AR MgF2 on glass, th0=0 deg | 0.0141104586417784 | 0.0141104586417784 | 1.04e-17 | 4.48e-15 | pass | TMM rounding | 1.01e-17 | 3.54e-19 |
| stack T (p) | AR MgF2 on glass, th0=0 deg | 0.985889541358221 | 0.985889541358222 | 4.44e-16 | 2.77e-14 | pass | TMM rounding | 3.19e-16 | 1.25e-16 |
| stack r (s) | AR MgF2 on glass, th0=45 deg | -0.205690178117-0.0226482778126j | -0.205690178117-0.0226482778126j | 1.04e-17 | 3.98e-14 | pass | TMM rounding | 2.93e-17 | 3.56e-17 |
| stack t (s) | AR MgF2 on glass, th0=45 deg | 0.161613628542+0.696788720551j | 0.161613628542+0.696788720551j | 1.57e-16 | 4.42e-14 | pass | TMM rounding | 1.49e-16 | 1.15e-16 |
| stack R (s) | AR MgF2 on glass, th0=45 deg | 0.0428213938615978 | 0.0428213938615978 | 0.00e+00 | 1.26e-14 | pass | TMM rounding | 1.19e-17 | 1.19e-17 |
| stack T (s) | AR MgF2 on glass, th0=45 deg | 0.957178606138403 | 0.957178606138402 | 2.22e-16 | 3.73e-14 | pass | TMM rounding | 3.35e-16 | 1.13e-16 |
| stack r (p) | AR MgF2 on glass, th0=45 deg | 0.0382547505155+0.0121714160219j | 0.0382547505155+0.0121714160219j | 1.48e-16 | 3.32e-14 | pass | TMM rounding | 5.40e-17 | 9.38e-17 |
| stack t (p) | AR MgF2 on glass, th0=45 deg | 0.161313443235+0.712487920479j | 0.161313443235+0.712487920479j | 2.37e-16 | 4.26e-14 | pass | TMM rounding | 1.94e-16 | 7.75e-17 |
| stack R (p) | AR MgF2 on glass, th0=45 deg | 0.00161156930498136 | 0.00161156930498137 | 1.06e-17 | 1.98e-15 | pass | TMM rounding | 3.72e-18 | 6.91e-18 |
| stack T (p) | AR MgF2 on glass, th0=45 deg | 0.998388430695019 | 0.998388430695019 | 1.11e-16 | 2.99e-14 | pass | TMM rounding | 6.88e-17 | 4.23e-17 |
| stack r (s) | Bragg (2.3/1.38)^10 on 1.52, th0=0 deg | -0.999951893809+1.24235675192e-17j | -0.999951893809+3.14079972807e-16j | 4.49e-16 | 2.17e-13 | pass | TMM rounding | 2.09e-16 | 4.79e-16 |
| stack t (s) | Bragg (2.3/1.38)^10 on 1.52, th0=0 deg | 0.00795588442122-2.1574707563e-18j | 0.00795588442122-4.86102729431e-18j | 1.24e-17 | 3.13e-15 | pass | TMM rounding | 1.48e-17 | 6.07e-18 |
| stack R (s) | Bragg (2.3/1.38)^10 on 1.52, th0=0 deg | 0.999903789932676 | 0.999903789932675 | 6.66e-16 | 3.37e-13 | pass | TMM rounding | 3.21e-16 | 3.45e-16 |
| stack T (s) | Bragg (2.3/1.38)^10 on 1.52, th0=0 deg | 9.62100673242856e-05 | 9.62100673242859e-05 | 3.25e-19 | 4.74e-17 | pass | TMM rounding | 3.81e-19 | 5.56e-20 |
| stack r (p) | Bragg (2.3/1.38)^10 on 1.52, th0=0 deg | 0.999951893809-1.24235675192e-17j | 0.999951893809-3.14079972807e-16j | 4.49e-16 | 2.17e-13 | pass | TMM rounding | 2.09e-16 | 4.79e-16 |
| stack t (p) | Bragg (2.3/1.38)^10 on 1.52, th0=0 deg | 0.00795588442122-2.1574707563e-18j | 0.00795588442122-4.86102729431e-18j | 2.70e-18 | 3.13e-15 | pass | TMM rounding | 3.75e-18 | 6.07e-18 |
| stack R (p) | Bragg (2.3/1.38)^10 on 1.52, th0=0 deg | 0.999903789932676 | 0.999903789932675 | 6.66e-16 | 3.37e-13 | pass | TMM rounding | 3.21e-16 | 3.45e-16 |
| stack T (p) | Bragg (2.3/1.38)^10 on 1.52, th0=0 deg | 9.62100673242859e-05 | 9.62100673242859e-05 | 1.36e-20 | 4.74e-17 | pass | TMM rounding | 6.91e-20 | 5.56e-20 |
| stack r (s) | Bragg (2.3/1.38)^10 on 1.52, th0=20 deg | -0.998247367804+0.0586179653723j | -0.998247367804+0.0586179653723j | 2.91e-16 | 2.33e-13 | pass | TMM rounding | 3.41e-16 | 6.24e-16 |
| stack t (s) | Bragg (2.3/1.38)^10 on 1.52, th0=20 deg | 0.00643735411295-0.000719209518306j | 0.00643735411295-0.000719209518306j | 3.53e-18 | 2.90e-15 | pass | TMM rounding | 4.21e-18 | 6.88e-18 |
| stack R (s) | Bragg (2.3/1.38)^10 on 1.52, th0=20 deg | 0.999933873191862 | 0.999933873191862 | 0.00e+00 | 3.69e-13 | pass | TMM rounding | 1.56e-16 | 1.56e-16 |
| stack T (s) | Bragg (2.3/1.38)^10 on 1.52, th0=20 deg | 6.61268081375121e-05 | 6.61268081375121e-05 | 5.42e-20 | 4.04e-17 | pass | TMM rounding | 5.65e-21 | 5.99e-20 |
| stack r (p) | Bragg (2.3/1.38)^10 on 1.52, th0=20 deg | 0.997481681-0.0697718736543j | 0.997481681-0.0697718736543j | 3.25e-16 | 2.46e-13 | pass | TMM rounding | 4.26e-16 | 7.01e-16 |
| stack t (p) | Bragg (2.3/1.38)^10 on 1.52, th0=20 deg | 0.0100682343978-0.00123826997758j | 0.0100682343978-0.00123826997758j | 1.40e-17 | 4.62e-15 | pass | TMM rounding | 7.83e-18 | 1.58e-17 |
| stack R (p) | Bragg (2.3/1.38)^10 on 1.52, th0=20 deg | 0.999837818284748 | 0.999837818284748 | 2.22e-16 | 3.76e-13 | pass | TMM rounding | 3.20e-16 | 9.80e-17 |
| stack T (p) | Bragg (2.3/1.38)^10 on 1.52, th0=20 deg | 0.000162181715251632 | 0.000162181715251632 | 4.61e-19 | 1.01e-16 | pass | TMM rounding | 9.91e-20 | 3.62e-19 |
| stack r (s) | Bragg (2.3/1.38)^10 on 1.52, th0=60 deg | -0.976793723053+0.214068111044j | -0.976793723053+0.214068111044j | 1.57e-16 | 1.16e-12 | pass | TMM rounding | 2.10e-16 | 3.20e-16 |
| stack t (s) | Bragg (2.3/1.38)^10 on 1.52, th0=60 deg | 0.00360530766897-0.00256153872627j | 0.00360530766897-0.00256153872627j | 1.02e-17 | 5.65e-15 | pass | TMM rounding | 5.41e-18 | 1.55e-17 |
| stack R (s) | Bragg (2.3/1.38)^10 on 1.52, th0=60 deg | 0.9999511335613 | 0.9999511335613 | 2.22e-16 | 2.22e-12 | pass | TMM rounding | 2.88e-16 | 6.61e-17 |
| stack T (s) | Bragg (2.3/1.38)^10 on 1.52, th0=60 deg | 4.88664387003453e-05 | 4.88664387003456e-05 | 2.30e-19 | 1.03e-16 | pass | TMM rounding | 1.21e-19 | 3.51e-19 |
| stack r (p) | Bragg (2.3/1.38)^10 on 1.52, th0=60 deg | 0.0601614637+0.0154336836554j | 0.0601614637+0.0154336836554j | 1.83e-15 | 5.24e-12 | pass | TMM rounding | 1.01e-15 | 2.76e-15 |
| stack t (p) | Bragg (2.3/1.38)^10 on 1.52, th0=60 deg | -0.625440062937+0.0868891295608j | -0.625440062937+0.0868891295608j | 2.56e-15 | 3.32e-12 | pass | TMM rounding | 7.70e-16 | 2.93e-15 |
| stack R (p) | Bragg (2.3/1.38)^10 on 1.52, th0=60 deg | 0.00385760030569578 | 0.00385760030569601 | 2.25e-16 | 6.05e-13 | pass | TMM rounding | 1.17e-16 | 3.42e-16 |
| stack T (p) | Bragg (2.3/1.38)^10 on 1.52, th0=60 deg | 0.996142399694303 | 0.996142399694306 | 3.00e-15 | 7.87e-12 | pass | TMM rounding | 1.71e-15 | 1.29e-15 |
| stack r (s) | Bragg (2.3/1.38)^10 on 1.52, th0=89.9 deg | -0.999999021003+0.00111680328766j | -0.999999021003+0.00111680328766j | 3.14e-15 | 6.28e-12 | pass | TMM rounding | 9.53e-16 | 2.19e-15 |
| stack t (s) | Bragg (2.3/1.38)^10 on 1.52, th0=89.9 deg | 2.53444619615e-05-2.10072288606e-05j | 2.53444619616e-05-2.10072288606e-05j | 9.70e-17 | 3.88e-14 | pass | TMM rounding | 2.99e-17 | 6.71e-17 |
| stack R (s) | Bragg (2.3/1.38)^10 on 1.52, th0=89.9 deg | 0.999999289257152 | 0.999999289257152 | 2.22e-16 | 9.95e-12 | pass | TMM rounding | 2.32e-16 | 1.04e-17 |
| stack T (s) | Bragg (2.3/1.38)^10 on 1.52, th0=89.9 deg | 7.10742848140986e-07 | 7.10742848144528e-07 | 3.54e-18 | 8.38e-16 | pass | TMM rounding | 6.44e-19 | 2.90e-18 |
| stack r (p) | Bragg (2.3/1.38)^10 on 1.52, th0=89.9 deg | -0.994140515585-0.000979578251359j | -0.994140515585-0.000979578251362j | 1.73e-14 | 1.28e-11 | pass | TMM rounding | 5.27e-15 | 1.21e-14 |
| stack t (p) | Bragg (2.3/1.38)^10 on 1.52, th0=89.9 deg | 0.00410924249049+0.00096323860445j | 0.0041092424905+0.000963238604453j | 1.24e-14 | 4.96e-12 | pass | TMM rounding | 3.83e-15 | 8.56e-15 |
| stack R (p) | Bragg (2.3/1.38)^10 on 1.52, th0=89.9 deg | 0.988316324301645 | 0.988316324301611 | 3.40e-14 | 2.53e-11 | pass | TMM rounding | 1.03e-14 | 2.37e-14 |
| stack T (p) | Bragg (2.3/1.38)^10 on 1.52, th0=89.9 deg | 0.0116836756983552 | 0.0116836756984131 | 5.79e-14 | 1.37e-11 | pass | TMM rounding | 1.06e-14 | 4.74e-14 |
| stack r (s) | Kretschmann 50 nm metal, th0=40 deg | -0.739930317195-0.599161993705j | -0.739930317195-0.599161993705j | 1.57e-16 | 3.76e-14 | pass | TMM rounding | 7.82e-17 | 1.25e-16 |
| stack t (s) | Kretschmann 50 nm metal, th0=40 deg | 0.123389642605-0.192272526552j | 0.123389642605-0.192272526552j | 1.00e-16 | 1.92e-14 | pass | TMM rounding | 3.27e-17 | 1.33e-16 |
| stack R (s) | Kretschmann 50 nm metal, th0=40 deg | 0.906491969005739 | 0.906491969005739 | 0.00e+00 | 4.64e-14 | pass | TMM rounding | 1.76e-16 | 1.76e-16 |
| stack T (s) | Kretschmann 50 nm metal, th0=40 deg | 0.0120480874056627 | 0.0120480874056627 | 1.04e-17 | 3.55e-15 | pass | TMM rounding | 7.69e-18 | 2.72e-18 |
| stack r (p) | Kretschmann 50 nm metal, th0=40 deg | 0.420452781154+0.791998785463j | 0.420452781154+0.791998785463j | 3.14e-16 | 4.47e-14 | pass | TMM rounding | 2.37e-16 | 9.71e-17 |
| stack t (p) | Kretschmann 50 nm metal, th0=40 deg | 0.648995530273-0.0260392405812j | 0.648995530273-0.0260392405812j | 2.28e-16 | 1.23e-13 | pass | TMM rounding | 3.10e-16 | 4.81e-16 |
| stack R (p) | Kretschmann 50 nm metal, th0=40 deg | 0.804042617355752 | 0.804042617355752 | 2.22e-16 | 5.75e-14 | pass | TMM rounding | 2.30e-16 | 7.86e-18 |
| stack T (p) | Kretschmann 50 nm metal, th0=40 deg | 0.097382690083064 | 0.097382690083064 | 4.16e-17 | 1.25e-14 | pass | TMM rounding | 7.60e-18 | 4.92e-17 |
| stack r (s) | Kretschmann 50 nm metal, th0=43 deg | -0.767341050677-0.57884419239j | -0.767341050677-0.57884419239j | 1.11e-16 | 3.74e-14 | pass | TMM rounding | 1.48e-16 | 2.57e-16 |
| stack t (s) | Kretschmann 50 nm metal, th0=43 deg | 0.0929235346612-0.183523887744j | 0.0929235346612-0.183523887744j | 2.55e-16 | 1.84e-14 | pass | TMM rounding | 3.93e-17 | 2.45e-16 |
| stack R (s) | Kretschmann 50 nm metal, th0=43 deg | 0.923872887117774 | 0.923872887117774 | 2.22e-16 | 4.36e-14 | pass | TMM rounding | 2.22e-16 | 4.44e-16 |
| stack T (s) | Kretschmann 50 nm metal, th0=43 deg | 0 | 2.41623563590295e-18 | 2.42e-18 | 2.11e-16 | pass | TMM rounding | 0.00e+00 | 2.42e-18 |
| stack r (p) | Kretschmann 50 nm metal, th0=43 deg | 0.621113950361+0.728239014776j | 0.621113950361+0.728239014776j | 1.29e-15 | 3.01e-13 | pass | TMM rounding | 2.48e-15 | 1.23e-15 |
| stack t (p) | Kretschmann 50 nm metal, th0=43 deg | 2.36595654988+0.92985514002j | 2.36595654988+0.92985514002j | 8.19e-15 | 2.00e-12 | pass | TMM rounding | 1.97e-14 | 1.19e-14 |
| stack R (p) | Kretschmann 50 nm metal, th0=43 deg | 0.916114601975235 | 0.916114601975234 | 8.88e-16 | 1.92e-13 | pass | TMM rounding | 6.36e-16 | 2.52e-16 |
| stack T (p) | Kretschmann 50 nm metal, th0=43 deg | 0 | 3.69002475771025e-16 | 3.69e-16 | 3.22e-14 | pass | TMM rounding | 0.00e+00 | 3.69e-16 |
| stack r (s) | Kretschmann 50 nm metal, th0=44 deg | -0.775396446193-0.569886130406j | -0.775396446193-0.569886130406j | 3.14e-16 | 3.71e-14 | pass | TMM rounding | 1.04e-16 | 2.20e-16 |
| stack t (s) | Kretschmann 50 nm metal, th0=44 deg | 0.0878975589303-0.176938147957j | 0.0878975589303-0.176938147957j | 1.39e-16 | 1.69e-14 | pass | TMM rounding | 2.68e-17 | 1.12e-16 |
| stack R (s) | Kretschmann 50 nm metal, th0=44 deg | 0.926009850397263 | 0.926009850397263 | 0.00e+00 | 4.33e-14 | pass | TMM rounding | 1.64e-16 | 1.64e-16 |
| stack T (s) | Kretschmann 50 nm metal, th0=44 deg | 0 | 2.30808055312407e-18 | 2.31e-18 | 2.12e-16 | pass | TMM rounding | 0.00e+00 | 2.31e-18 |
| stack r (p) | Kretschmann 50 nm metal, th0=44 deg | 0.680628714666+0.217715871854j | 0.680628714666+0.217715871854j | 2.05e-15 | 1.16e-12 | pass | TMM rounding | 5.37e-16 | 1.70e-15 |
| stack t (p) | Kretschmann 50 nm metal, th0=44 deg | 5.65873914123-1.41309054657j | 5.65873914123-1.41309054657j | 1.63e-14 | 8.54e-12 | pass | TMM rounding | 3.48e-15 | 1.32e-14 |
| stack R (p) | Kretschmann 50 nm metal, th0=44 deg | 0.510655648084835 | 0.510655648084832 | 2.66e-15 | 1.22e-12 | pass | TMM rounding | 2.34e-16 | 2.43e-15 |
| stack T (p) | Kretschmann 50 nm metal, th0=44 deg | 0 | 2.01154047916184e-15 | 2.01e-15 | 1.84e-13 | pass | TMM rounding | 0.00e+00 | 2.01e-15 |
| stack r (s) | Kretschmann 50 nm metal, th0=45 deg | -0.783136603165-0.560926951935j | -0.783136603165-0.560926951935j | 1.11e-16 | 3.70e-14 | pass | TMM rounding | 9.65e-17 | 4.67e-17 |
| stack t (s) | Kretschmann 50 nm metal, th0=45 deg | 0.0835543230945-0.171283378942j | 0.0835543230945-0.171283378942j | 6.94e-17 | 1.60e-14 | pass | TMM rounding | 2.99e-17 | 3.96e-17 |
| stack R (s) | Kretschmann 50 nm metal, th0=45 deg | 0.927941984624891 | 0.927941984624891 | 0.00e+00 | 4.31e-14 | pass | TMM rounding | 8.30e-17 | 8.30e-17 |
| stack T (s) | Kretschmann 50 nm metal, th0=45 deg | 0 | 2.22391699884156e-18 | 2.22e-18 | 2.11e-16 | pass | TMM rounding | 0.00e+00 | 2.22e-18 |
| stack r (p) | Kretschmann 50 nm metal, th0=45 deg | -0.168012018594+0.388340932371j | -0.168012018594+0.388340932371j | 6.47e-16 | 8.90e-13 | pass | TMM rounding | 2.28e-15 | 2.80e-15 |
| stack t (p) | Kretschmann 50 nm metal, th0=45 deg | 0.25446739498-5.19465802129j | 0.25446739498-5.19465802129j | 9.78e-15 | 6.32e-12 | pass | TMM rounding | 2.28e-14 | 2.43e-14 |
| stack R (p) | Kretschmann 50 nm metal, th0=45 deg | 0.179036718146958 | 0.179036718146957 | 4.72e-16 | 6.58e-13 | pass | TMM rounding | 1.92e-15 | 2.39e-15 |
| stack T (p) | Kretschmann 50 nm metal, th0=45 deg | 0 | 1.65628737833705e-15 | 1.66e-15 | 1.57e-13 | pass | TMM rounding | 0.00e+00 | 1.66e-15 |
| stack r (s) | Kretschmann 50 nm metal, th0=50 deg | -0.819878704613-0.51415328068j | -0.819878704613-0.51415328068j | 1.11e-16 | 3.68e-14 | pass | TMM rounding | 1.08e-16 | 1.01e-16 |
| stack t (s) | Kretschmann 50 nm metal, th0=50 deg | 0.0660005904454-0.147997925691j | 0.0660005904454-0.147997925691j | 3.93e-17 | 1.38e-14 | pass | TMM rounding | 2.87e-17 | 2.22e-17 |
| stack R (s) | Kretschmann 50 nm metal, th0=50 deg | 0.936554686311205 | 0.936554686311205 | 2.22e-16 | 4.26e-14 | pass | TMM rounding | 2.20e-16 | 2.45e-18 |
| stack T (s) | Kretschmann 50 nm metal, th0=50 deg | 0 | 1.91625447540957e-18 | 1.92e-18 | 2.03e-16 | pass | TMM rounding | 0.00e+00 | 1.92e-18 |
| stack r (p) | Kretschmann 50 nm metal, th0=50 deg | 0.0685789534136+0.872441491488j | 0.0685789534136+0.872441491488j | 4.02e-16 | 9.35e-14 | pass | TMM rounding | 1.87e-16 | 2.79e-16 |
| stack t (p) | Kretschmann 50 nm metal, th0=50 deg | -0.598532884817-0.871410400186j | -0.598532884817-0.871410400186j | 4.97e-16 | 2.79e-13 | pass | TMM rounding | 8.57e-16 | 3.74e-16 |
| stack R (p) | Kretschmann 50 nm metal, th0=50 deg | 0.765857228921286 | 0.765857228921286 | 0.00e+00 | 1.14e-13 | pass | TMM rounding | 1.64e-16 | 1.64e-16 |
| stack T (p) | Kretschmann 50 nm metal, th0=50 deg | 0 | 8.15554193381976e-17 | 8.16e-17 | 8.63e-15 | pass | TMM rounding | 0.00e+00 | 8.16e-17 |
| stack r (s) | Kretschmann 50 nm metal, th0=70 deg | -0.942198175834-0.28355883931j | -0.942198175834-0.28355883931j | 2.00e-16 | 3.86e-14 | pass | TMM rounding | 1.18e-16 | 3.17e-16 |
| stack t (s) | Kretschmann 50 nm metal, th0=70 deg | 0.0207129355586-0.0723321016182j | 0.0207129355586-0.0723321016182j | 4.65e-17 | 9.69e-15 | pass | TMM rounding | 5.52e-17 | 1.02e-16 |
| stack R (s) | Kretschmann 50 nm metal, th0=70 deg | 0.968143017895273 | 0.968143017895273 | 0.00e+00 | 4.05e-14 | pass | TMM rounding | 1.51e-16 | 1.51e-16 |
| stack T (s) | Kretschmann 50 nm metal, th0=70 deg | 0 | 9.52368381567672e-19 | 9.52e-19 | 1.16e-16 | pass | TMM rounding | 0.00e+00 | 9.52e-19 |
| stack r (p) | Kretschmann 50 nm metal, th0=70 deg | -0.407481161046+0.82189471208j | -0.407481161046+0.82189471208j | 5.55e-17 | 9.92e-14 | pass | TMM rounding | 7.65e-16 | 8.15e-16 |
| stack t (p) | Kretschmann 50 nm metal, th0=70 deg | -0.10790442066-0.244778393728j | -0.10790442066-0.244778393728j | 1.95e-16 | 4.45e-14 | pass | TMM rounding | 2.57e-16 | 4.20e-16 |
| stack R (p) | Kretschmann 50 nm metal, th0=70 deg | 0.841551814353052 | 0.841551814353052 | 0.00e+00 | 7.87e-14 | pass | TMM rounding | 1.33e-16 | 1.33e-16 |
| stack T (p) | Kretschmann 50 nm metal, th0=70 deg | 0 | 1.20388295043647e-17 | 1.20e-17 | 1.47e-15 | pass | TMM rounding | 0.00e+00 | 1.20e-17 |
| stack r (s) | FTIR gap 100 nm, th0=60 deg | -0.0460435553294-0.676990062192j | -0.0460435553294-0.676990062192j | 1.62e-16 | 8.25e-14 | pass | TMM rounding | 3.14e-16 | 2.48e-16 |
| stack t (s) | FTIR gap 100 nm, th0=60 deg | 0.732857489666-0.0498432196549j | 0.732857489666-0.0498432196549j | 2.33e-16 | 7.75e-14 | pass | TMM rounding | 3.37e-16 | 3.16e-16 |
| stack R (s) | FTIR gap 100 nm, th0=60 deg | 0.460435553294212 | 0.460435553294212 | 1.67e-16 | 7.18e-14 | pass | TMM rounding | 2.64e-17 | 1.93e-16 |
| stack T (s) | FTIR gap 100 nm, th0=60 deg | 0.539564446705789 | 0.539564446705788 | 2.22e-16 | 5.69e-14 | pass | TMM rounding | 8.46e-17 | 1.37e-16 |
| stack r (p) | FTIR gap 100 nm, th0=60 deg | -0.460557500851-0.652693363639j | -0.460557500851-0.652693363639j | 3.33e-16 | 1.01e-13 | pass | TMM rounding | 3.88e-16 | 4.16e-16 |
| stack t (p) | FTIR gap 100 nm, th0=60 deg | 0.491517042311-0.346827274864j | 0.491517042311-0.346827274864j | 2.22e-16 | 8.69e-14 | pass | TMM rounding | 3.28e-16 | 4.32e-16 |
| stack R (p) | FTIR gap 100 nm, th0=60 deg | 0.638121838528838 | 0.638121838528838 | 4.44e-16 | 1.06e-13 | pass | TMM rounding | 1.76e-16 | 6.20e-16 |
| stack T (p) | FTIR gap 100 nm, th0=60 deg | 0.361878161471162 | 0.361878161471163 | 1.11e-16 | 7.29e-14 | pass | TMM rounding | 2.31e-16 | 1.20e-16 |
| stack r (s) | FTIR gap 1 um, th0=60 deg | -0.099999971881-0.99498729863j | -0.099999971881-0.99498729863j | 3.33e-16 | 1.02e-13 | pass | TMM rounding | 7.31e-16 | 3.98e-16 |
| stack t (s) | FTIR gap 1 um, th0=60 deg | 0.000527615156674-5.30273109054e-05j | 0.000527615156674-5.30273109054e-05j | 2.79e-19 | 2.82e-16 | pass | TMM rounding | 7.03e-19 | 9.36e-19 |
| stack R (s) | FTIR gap 1 um, th0=60 deg | 0.999999718810351 | 0.999999718810351 | 0.00e+00 | 7.96e-14 | pass | TMM rounding | 1.33e-16 | 1.33e-16 |
| stack T (s) | FTIR gap 1 um, th0=60 deg | 2.81189649253601e-07 | 2.81189649253601e-07 | 5.29e-23 | 2.35e-19 | pass | TMM rounding | 6.54e-22 | 7.07e-22 |
| stack r (p) | FTIR gap 1 um, th0=60 deg | -0.721739032223-0.69216517775j | -0.721739032223-0.69216517775j | 1.11e-16 | 8.50e-14 | pass | TMM rounding | 3.52e-16 | 4.12e-16 |
| stack t (p) | FTIR gap 1 um, th0=60 deg | 0.000255329867124-0.000266239240459j | 0.000255329867124-0.000266239240459j | 4.23e-19 | 2.10e-16 | pass | TMM rounding | 5.42e-19 | 7.13e-19 |
| stack R (p) | FTIR gap 1 um, th0=60 deg | 0.999999863923326 | 0.999999863923326 | 2.22e-16 | 6.33e-14 | pass | TMM rounding | 2.77e-16 | 5.48e-17 |
| stack T (p) | FTIR gap 1 um, th0=60 deg | 1.36076674205703e-07 | 1.36076674205703e-07 | 7.94e-23 | 1.26e-19 | pass | TMM rounding | 4.47e-22 | 3.68e-22 |
| stack r (s) | FTIR gap 5 um, th0=60 deg | -0.1-0.994987437107j | -0.1-0.994987437107j | 3.34e-16 | 1.02e-13 | pass | TMM rounding | 6.18e-16 | 3.37e-16 |
| stack t (s) | FTIR gap 5 um, th0=60 deg | 2.66026990624e-18-2.67367185457e-19j | 2.66026990624e-18-2.67367185457e-19j | 2.13e-32 | 6.46e-30 | pass | TMM rounding | 7.39e-33 | 2.84e-32 |
| stack R (s) | FTIR gap 5 um, th0=60 deg | 1 | 1 | 4.44e-16 | 7.96e-14 | pass | TMM rounding | 4.44e-16 | 7.15e-36 |
| stack T (s) | FTIR gap 5 um, th0=60 deg | 7.14852118590485e-36 | 7.14852118590476e-36 | 9.76e-50 | 2.77e-47 | pass | TMM rounding | 4.06e-50 | 1.38e-49 |
| stack r (p) | FTIR gap 5 um, th0=60 deg | -0.721739130435-0.692165173639j | -0.721739130435-0.692165173639j | 2.48e-16 | 8.50e-14 | pass | TMM rounding | 4.50e-16 | 2.20e-16 |
| stack t (p) | FTIR gap 5 um, th0=60 deg | 1.28738959546e-18-1.3423955474e-18j | 1.28738959546e-18-1.3423955474e-18j | 1.50e-32 | 4.57e-30 | pass | TMM rounding | 5.98e-33 | 2.06e-32 |
| stack R (p) | FTIR gap 5 um, th0=60 deg | 1 | 1 | 0.00e+00 | 6.33e-14 | pass | TMM rounding | 3.46e-36 | 3.46e-36 |
| stack T (p) | FTIR gap 5 um, th0=60 deg | 3.45939777616568e-36 | 3.45939777616563e-36 | 4.74e-50 | 1.37e-47 | pass | TMM rounding | 2.21e-50 | 6.95e-50 |
| stack r (s) | FTIR gap 20 um, th0=60 deg | -0.1-0.994987437107j | -0.1-0.994987437107j | 2.99e-16 | 1.02e-13 | pass | TMM rounding | 6.18e-16 | 3.20e-16 |
| stack t (s) | FTIR gap 20 um, th0=60 deg | 6.45219130623e-72-6.48469625405e-73j | 6.45219130623e-72-6.48469625405e-73j | 2.11e-85 | 6.16e-83 | pass | TMM rounding | 7.25e-86 | 2.78e-85 |
| stack R (s) | FTIR gap 20 um, th0=60 deg | 1 | 1 | 0.00e+00 | 7.96e-14 | pass | TMM rounding | 4.44e-16 | 4.44e-16 |
| stack T (s) | FTIR gap 20 um, th0=60 deg | 4.20512855072444e-143 | 4.2051285507242e-143 | 2.39e-156 | 6.42e-154 | pass | TMM rounding | 9.45e-157 | 3.33e-156 |
| stack r (p) | FTIR gap 20 um, th0=60 deg | -0.721739130435-0.692165173639j | -0.721739130435-0.692165173639j | 2.48e-16 | 8.50e-14 | pass | TMM rounding | 4.50e-16 | 2.20e-16 |
| stack t (p) | FTIR gap 20 um, th0=60 deg | 3.12242150169e-72-3.25583237254e-72j | 3.12242150169e-72-3.25583237254e-72j | 1.46e-85 | 4.30e-83 | pass | TMM rounding | 5.33e-86 | 1.95e-85 |
| stack R (p) | FTIR gap 20 um, th0=60 deg | 1 | 1 | 0.00e+00 | 6.33e-14 | pass | TMM rounding | 0.00e+00 | 0.00e+00 |
| stack T (p) | FTIR gap 20 um, th0=60 deg | 2.03499604723149e-143 | 2.03499604723137e-143 | 1.15e-156 | 3.13e-154 | pass | TMM rounding | 4.75e-157 | 1.63e-156 |
| stack r (s) | absorbing 4 layers, th0=0 deg | 0.162601385557-0.52363169855j | 0.162601385557-0.52363169855j | 2.22e-16 | 1.75e-13 | pass | TMM rounding | 6.04e-16 | 7.01e-16 |
| stack t (s) | absorbing 4 layers, th0=0 deg | 0.492456081549-0.206069682645j | 0.492456081549-0.206069682645j | 2.78e-17 | 9.80e-14 | pass | TMM rounding | 3.40e-16 | 3.13e-16 |
| stack R (s) | absorbing 4 layers, th0=0 deg | 0.300629366311125 | 0.300629366311125 | 2.22e-16 | 1.13e-13 | pass | TMM rounding | 3.02e-17 | 1.92e-16 |
| stack T (s) | absorbing 4 layers, th0=0 deg | 0.427466559540229 | 0.427466559540229 | 0.00e+00 | 9.35e-14 | pass | TMM rounding | 8.27e-17 | 8.27e-17 |
| stack r (p) | absorbing 4 layers, th0=0 deg | -0.162601385557+0.52363169855j | -0.162601385557+0.52363169855j | 2.62e-16 | 1.75e-13 | pass | TMM rounding | 4.72e-16 | 7.01e-16 |
| stack t (p) | absorbing 4 layers, th0=0 deg | 0.492456081549-0.206069682645j | 0.492456081549-0.206069682645j | 1.24e-16 | 9.80e-14 | pass | TMM rounding | 2.46e-16 | 3.13e-16 |
| stack R (p) | absorbing 4 layers, th0=0 deg | 0.300629366311125 | 0.300629366311125 | 1.11e-16 | 1.13e-13 | pass | TMM rounding | 8.08e-17 | 1.92e-16 |
| stack T (p) | absorbing 4 layers, th0=0 deg | 0.427466559540229 | 0.427466559540229 | 0.00e+00 | 9.35e-14 | pass | TMM rounding | 8.27e-17 | 8.27e-17 |
| stack r (s) | absorbing 4 layers, th0=40 deg | -0.339484382552-0.516946370952j | -0.339484382552-0.516946370952j | 2.78e-16 | 1.55e-13 | pass | TMM rounding | 1.54e-16 | 4.07e-16 |
| stack t (s) | absorbing 4 layers, th0=40 deg | 0.229993623374-0.296263739379j | 0.229993623374-0.296263739379j | 1.57e-16 | 6.73e-14 | pass | TMM rounding | 9.20e-17 | 2.47e-16 |
| stack R (s) | absorbing 4 layers, th0=40 deg | 0.382483196436471 | 0.382483196436471 | 1.11e-16 | 1.17e-13 | pass | TMM rounding | 2.91e-17 | 1.40e-16 |
| stack T (s) | absorbing 4 layers, th0=40 deg | 0.248873726353623 | 0.248873726353623 | 5.55e-17 | 5.71e-14 | pass | TMM rounding | 8.81e-17 | 3.26e-17 |
| stack r (p) | absorbing 4 layers, th0=40 deg | 0.114334868531+0.496117773694j | 0.114334868531+0.496117773694j | 2.56e-16 | 1.55e-13 | pass | TMM rounding | 2.40e-16 | 2.68e-16 |
| stack t (p) | absorbing 4 layers, th0=40 deg | 0.351295973438-0.313912380294j | 0.351295973438-0.313912380294j | 1.76e-16 | 8.39e-14 | pass | TMM rounding | 1.65e-16 | 2.45e-16 |
| stack R (p) | absorbing 4 layers, th0=40 deg | 0.259205307537493 | 0.259205307537493 | 1.11e-16 | 9.29e-14 | pass | TMM rounding | 2.70e-16 | 1.59e-16 |
| stack T (p) | absorbing 4 layers, th0=40 deg | 0.392676272361336 | 0.392676272361336 | 2.78e-16 | 7.36e-14 | pass | TMM rounding | 4.49e-16 | 1.71e-16 |
| stack r (s) | absorbing 4 layers, th0=85 deg | -0.931438667662-0.0364784648371j | -0.931438667662-0.0364784648371j | 2.33e-16 | 1.17e-13 | pass | TMM rounding | 2.32e-16 | 2.56e-17 |
| stack t (s) | absorbing 4 layers, th0=85 deg | 0.00024167375658-0.043062804697j | 0.00024167375658-0.043062804697j | 6.39e-17 | 3.15e-14 | pass | TMM rounding | 7.56e-17 | 1.18e-17 |
| stack R (s) | absorbing 4 layers, th0=85 deg | 0.868908670013265 | 0.868908670013265 | 4.44e-16 | 1.89e-13 | pass | TMM rounding | 4.18e-16 | 2.63e-17 |
| stack T (s) | absorbing 4 layers, th0=85 deg | 0.0238612334262984 | 0.0238612334262984 | 3.47e-17 | 1.72e-14 | pass | TMM rounding | 4.85e-17 | 1.38e-17 |
| stack r (p) | absorbing 4 layers, th0=85 deg | -0.539007206871+0.0864913689331j | -0.539007206871+0.0864913689331j | 5.88e-16 | 3.59e-13 | pass | TMM rounding | 4.90e-16 | 1.26e-16 |
| stack t (p) | absorbing 4 layers, th0=85 deg | 0.0619154898657-0.159373414649j | 0.0619154898657-0.159373414649j | 2.65e-16 | 1.23e-13 | pass | TMM rounding | 2.73e-16 | 4.69e-17 |
| stack R (p) | absorbing 4 layers, th0=85 deg | 0.298009525958367 | 0.298009525958367 | 6.11e-16 | 3.33e-13 | pass | TMM rounding | 4.13e-16 | 1.98e-16 |
| stack T (p) | absorbing 4 layers, th0=85 deg | 0.376143976552523 | 0.376143976552523 | 5.55e-16 | 1.95e-13 | pass | TMM rounding | 4.80e-16 | 7.52e-17 |
| stack r (s) | absorbing 4 layers, th0=89.99 deg | -0.999858459327-7.63756417163e-05j | -0.999858459327-7.63756417038e-05j | 2.61e-14 | 1.88e-11 | pass | TMM rounding | 2.53e-13 | 2.79e-13 |
| stack t (s) | absorbing 4 layers, th0=89.99 deg | -1.54971821447e-06-8.91532237739e-05j | -1.54971821422e-06-8.91532237593e-05j | 1.46e-14 | 1.04e-11 | pass | TMM rounding | 1.40e-13 | 1.55e-13 |
| stack R (s) | absorbing 4 layers, th0=89.99 deg | 0.999716944521533 | 0.999716944521579 | 4.60e-14 | 3.31e-11 | pass | TMM rounding | 4.45e-13 | 4.91e-13 |
| stack T (s) | absorbing 4 layers, th0=89.99 deg | 5.09310882277144e-05 | 5.09310881310111e-05 | 9.67e-14 | 5.94e-12 | pass | TMM rounding | 8.00e-14 | 1.77e-13 |
| stack r (p) | absorbing 4 layers, th0=89.99 deg | -0.998809129147+0.000274317243447j | -0.998809129147+0.000274317243402j | 2.00e-13 | 1.43e-10 | pass | TMM rounding | 1.92e-12 | 2.12e-12 |
| stack t (p) | absorbing 4 layers, th0=89.99 deg | 0.000176958869847-0.000410092760703j | 0.000176958869818-0.000410092760636j | 7.29e-14 | 5.21e-11 | pass | TMM rounding | 7.02e-13 | 7.75e-13 |
| stack R (p) | absorbing 4 layers, th0=89.99 deg | 0.997619751716983 | 0.997619751717372 | 3.89e-13 | 2.78e-10 | pass | TMM rounding | 3.74e-12 | 4.13e-12 |
| stack T (p) | absorbing 4 layers, th0=89.99 deg | 0.00127790890475022 | 0.00127790890232406 | 2.43e-12 | 1.49e-10 | pass | TMM rounding | 2.01e-12 | 4.43e-12 |
| stack r (s) | opaque metal 2 um, th0=17.1887 deg | -0.820799701123-0.514246146159j | -0.820799701123-0.514246146159j | 1.57e-16 | 2.86e-14 | pass | TMM rounding | 1.66e-16 | 2.09e-17 |
| stack t (s) | opaque metal 2 um, th0=17.1887 deg | -2.65323176197e-29+4.15101565198e-31j | -6.14272361968e-16+9.61037111668e-18j | 6.14e-16 | 3.29e-41 | xfail | TMM rounding | 1.50e-43 | 6.14e-16 |
| stack R (s) | opaque metal 2 um, th0=17.1887 deg | 0.938161248204209 | 0.938161248204209 | 2.22e-16 | 4.03e-14 | pass | TMM rounding | 1.71e-16 | 5.14e-17 |
| stack T (s) | opaque metal 2 um, th0=17.1887 deg | 1.08391494993463e-57 | 5.80987491301165e-31 | 5.81e-31 | 2.14e-69 | xfail | TMM rounding | 1.21e-71 | 5.81e-31 |
| stack r (p) | opaque metal 2 um, th0=17.1887 deg | 0.788695952476+0.556724343981j | 0.788695952476+0.556724343981j | 4.00e-16 | 2.98e-14 | pass | TMM rounding | 9.96e-17 | 3.02e-16 |
| stack t (p) | opaque metal 2 um, th0=17.1887 deg | -2.80054411309e-29-8.03336700332e-31j | -6.48377903432e-16-1.85987345486e-17j | 6.49e-16 | 3.47e-41 | xfail | TMM rounding | 1.57e-43 | 6.49e-16 |
| stack R (p) | opaque metal 2 um, th0=17.1887 deg | 0.931983300633068 | 0.931983300633067 | 8.88e-16 | 4.11e-14 | pass | TMM rounding | 2.64e-16 | 6.24e-16 |
| stack T (p) | opaque metal 2 um, th0=17.1887 deg | 1.20831615345951e-57 | 6.47667578290572e-31 | 6.48e-31 | 2.38e-69 | xfail | TMM rounding | 1.30e-71 | 6.48e-31 |
| single_film (Airy sum) r (s) | AR film, th0=0 deg | -0.12228907841-0.016495898025j | -0.12228907841-0.016495898025j | 4.39e-17 | 2.51e-14 | pass | TMM rounding + stated err | 1.97e-17 | 2.91e-17 |
| single_film (Airy sum) t (s) | AR film, th0=0 deg | 0.168246430763+0.792596145358j | 0.168246430763+0.792596145358j | 3.55e-16 | 3.45e-14 | pass | TMM rounding + stated err | 1.03e-16 | 2.92e-16 |
| single_film (Airy sum) r (p) | AR film, th0=0 deg | 0.12228907841+0.016495898025j | 0.12228907841+0.016495898025j | 4.39e-17 | 2.51e-14 | pass | TMM rounding + stated err | 1.97e-17 | 2.91e-17 |
| single_film (Airy sum) t (p) | AR film, th0=0 deg | 0.168246430763+0.792596145358j | 0.168246430763+0.792596145358j | 3.55e-16 | 3.45e-14 | pass | TMM rounding + stated err | 1.03e-16 | 2.92e-16 |
| single_film (Airy sum) r (s) | AR film, th0=60 deg | -0.335687590633-0.049420137014j | -0.335687590633-0.0494201370139j | 1.19e-16 | 4.46e-14 | pass | TMM rounding + stated err | 5.72e-17 | 1.27e-16 |
| single_film (Airy sum) t (s) | AR film, th0=60 deg | 0.303390042346+0.518846562976j | 0.303390042346+0.518846562976j | 1.24e-16 | 4.38e-14 | pass | TMM rounding + stated err | 6.89e-17 | 9.23e-17 |
| single_film (Airy sum) r (p) | AR film, th0=60 deg | -0.0697024315392+0.0151607002097j | -0.0697024315392+0.0151607002097j | 1.84e-17 | 3.70e-14 | pass | TMM rounding + stated err | 2.83e-18 | 2.11e-17 |
| single_film (Airy sum) t (p) | AR film, th0=60 deg | 0.309820575962+0.556940051783j | 0.309820575962+0.556940051783j | 5.55e-17 | 4.06e-14 | pass | TMM rounding + stated err | 4.79e-17 | 2.43e-17 |
| single_film (Airy sum) r (s) | free-standing n=2.3, th0=0 deg | -0.677875497402-0.0530999880113j | -0.677875497402-0.0530999880113j | 3.59e-15 | 4.24e-13 | pass | TMM rounding + stated err | 3.16e-15 | 4.35e-16 |
| single_film (Airy sum) t (s) | free-standing n=2.3, th0=0 deg | -0.0572627361908+0.731017223011j | -0.0572627361908+0.731017223011j | 3.84e-15 | 4.54e-13 | pass | TMM rounding + stated err | 3.39e-15 | 4.73e-16 |
| single_film (Airy sum) r (p) | free-standing n=2.3, th0=0 deg | 0.677875497402+0.0530999880113j | 0.677875497402+0.0530999880113j | 3.59e-15 | 4.24e-13 | pass | TMM rounding + stated err | 3.16e-15 | 4.35e-16 |
| single_film (Airy sum) t (p) | free-standing n=2.3, th0=0 deg | -0.0572627361908+0.731017223011j | -0.0572627361908+0.731017223011j | 3.84e-15 | 4.54e-13 | pass | TMM rounding + stated err | 3.39e-15 | 4.73e-16 |
| single_film (Airy sum) r (s) | free-standing n=2.3, th0=45 deg | -0.40965419567-0.405460576605j | -0.40965419567-0.405460576605j | 2.83e-16 | 8.58e-13 | pass | TMM rounding + stated err | 2.53e-15 | 2.81e-15 |
| single_film (Airy sum) t (s) | free-standing n=2.3, th0=45 deg | 0.574853926357-0.580799555906j | 0.574853926357-0.580799555906j | 1.11e-16 | 9.57e-13 | pass | TMM rounding + stated err | 2.78e-15 | 2.82e-15 |
| single_film (Airy sum) r (p) | free-standing n=2.3, th0=45 deg | 0.154325978813+0.227582371312j | 0.154325978813+0.227582371312j | 1.00e-16 | 4.84e-13 | pass | TMM rounding + stated err | 1.39e-15 | 1.49e-15 |
| single_film (Airy sum) t (p) | free-standing n=2.3, th0=45 deg | 0.795748561406-0.539605396148j | 0.795748561406-0.539605396148j | 1.11e-16 | 9.45e-13 | pass | TMM rounding + stated err | 2.76e-15 | 2.84e-15 |
| single_film (Airy sum) r (s) | free-standing n=2.3, th0=80 deg | -0.867525302534+0.320778482105j | -0.867525302534+0.320778482105j | 2.22e-16 | 8.44e-13 | pass | TMM rounding + stated err | 5.17e-15 | 5.02e-15 |
| single_film (Airy sum) t (s) | free-standing n=2.3, th0=80 deg | -0.131835061867-0.356539663072j | -0.131835061867-0.356539663072j | 1.76e-16 | 7.77e-13 | pass | TMM rounding + stated err | 4.90e-15 | 5.06e-15 |
| single_film (Airy sum) r (p) | free-standing n=2.3, th0=80 deg | -0.181190236747+0.298572043161j | -0.181190236747+0.298572043161j | 7.85e-17 | 8.97e-13 | pass | TMM rounding + stated err | 5.10e-15 | 5.17e-15 |
| single_film (Airy sum) t (p) | free-standing n=2.3, th0=80 deg | -0.801063288684-0.486130065593j | -0.801063288684-0.486130065593j | 4.00e-16 | 1.17e-12 | pass | TMM rounding + stated err | 6.92e-15 | 6.99e-15 |
| single_film (Airy sum) r (s) | metal film, th0=0 deg | -0.664652394119-0.511815437842j | -0.664652394119-0.511815437842j | 1.57e-16 | 2.68e-14 | pass | TMM rounding + stated err | 7.95e-17 | 2.30e-16 |
| single_film (Airy sum) t (s) | metal film, th0=0 deg | 0.307422154107-0.218706813117j | 0.307422154107-0.218706813117j | 1.14e-16 | 1.80e-14 | pass | TMM rounding + stated err | 9.63e-17 | 2.23e-17 |
| single_film (Airy sum) r (p) | metal film, th0=0 deg | 0.664652394119+0.511815437842j | 0.664652394119+0.511815437842j | 1.57e-16 | 2.68e-14 | pass | TMM rounding + stated err | 7.95e-17 | 2.30e-16 |
| single_film (Airy sum) t (p) | metal film, th0=0 deg | 0.307422154107-0.218706813117j | 0.307422154107-0.218706813117j | 1.14e-16 | 1.80e-14 | pass | TMM rounding + stated err | 9.63e-17 | 2.23e-17 |
| single_film (Airy sum) r (s) | metal film, th0=60 deg | -0.87114643031-0.304203193049j | -0.87114643031-0.304203193049j | 5.55e-17 | 3.09e-14 | pass | TMM rounding + stated err | 1.36e-16 | 1.46e-16 |
| single_film (Airy sum) t (s) | metal film, th0=60 deg | 0.132459026528-0.153427359713j | 0.132459026528-0.153427359713j | 6.21e-17 | 1.70e-14 | pass | TMM rounding + stated err | 2.81e-17 | 6.00e-17 |
| single_film (Airy sum) r (p) | metal film, th0=60 deg | 0.279859400021+0.706103565693j | 0.279859400021+0.706103565693j | 1.11e-16 | 5.39e-14 | pass | TMM rounding + stated err | 4.38e-17 | 9.50e-17 |
| single_film (Airy sum) t (p) | metal film, th0=60 deg | 0.339254072439-0.112718250808j | 0.339254072439-0.112718250808j | 4.16e-17 | 2.28e-14 | pass | TMM rounding + stated err | 4.49e-17 | 6.51e-17 |
| single_film (Airy sum) r (s) | Kretschmann, th0=44 deg | -0.775396446193-0.569886130406j | -0.775396446193-0.569886130406j | 1.57e-16 | 3.25e-14 | pass | TMM rounding + stated err | 7.02e-17 | 2.20e-16 |
| single_film (Airy sum) t (s) | Kretschmann, th0=44 deg | 0.0878975589303-0.176938147957j | 0.0878975589303-0.176938147957j | 1.18e-16 | 1.67e-14 | pass | TMM rounding + stated err | 1.64e-17 | 1.12e-16 |
| single_film (Airy sum) r (p) | Kretschmann, th0=44 deg | 0.680628714666+0.217715871854j | 0.680628714666+0.217715871854j | 1.89e-15 | 1.09e-12 | pass | TMM rounding + stated err | 2.89e-16 | 1.70e-15 |
| single_film (Airy sum) t (p) | Kretschmann, th0=44 deg | 5.65873914123-1.41309054657j | 5.65873914123-1.41309054657j | 1.55e-14 | 8.37e-12 | pass | TMM rounding + stated err | 2.74e-15 | 1.32e-14 |
| single_film (Airy sum) r (s) | gap beyond TIR, th0=60 deg | -0.0972009833891-0.981102340594j | -0.0972009833891-0.981102340594j | 2.00e-16 | 9.27e-14 | pass | TMM rounding + stated err | 6.27e-16 | 4.53e-16 |
| single_film (Airy sum) t (s) | gap beyond TIR, th0=60 deg | 0.166487533894-0.0164944586787j | 0.166487533894-0.0164944586787j | 1.04e-17 | 3.49e-14 | pass | TMM rounding + stated err | 1.22e-16 | 1.30e-16 |
| single_film (Airy sum) r (p) | gap beyond TIR, th0=60 deg | -0.711819646444-0.692509153424j | -0.711819646444-0.692509153424j | 3.14e-16 | 7.96e-14 | pass | TMM rounding + stated err | 4.14e-16 | 4.08e-16 |
| single_film (Airy sum) t (p) | gap beyond TIR, th0=60 deg | 0.0817494940269-0.0840290639445j | 0.0817494940269-0.0840290639445j | 9.81e-17 | 2.83e-14 | pass | TMM rounding + stated err | 1.26e-16 | 1.01e-16 |
| airy T (s) | 1.0/2.3/1.0, d=1700 nm, lam=450, th0=25 deg | 0.933745706123413 | 0.933745706123412 | 5.55e-16 | 9.36e-13 | pass | TMM rounding + stated err | 3.20e-15 | 2.65e-15 |
| airy T (p) | 1.0/2.3/1.0, d=1700 nm, lam=450, th0=25 deg | 0.957837844415807 | 0.957837844415807 | 3.33e-16 | 7.70e-13 | pass | TMM rounding + stated err | 2.46e-15 | 2.12e-15 |
| airy T (s) | 1.0/2.3/1.0, d=1700 nm, lam=633, th0=25 deg | 0.827736360340027 | 0.827736360340027 | 1.11e-16 | 6.60e-13 | pass | TMM rounding + stated err | 1.10e-15 | 9.86e-16 |
| airy T (p) | 1.0/2.3/1.0, d=1700 nm, lam=633, th0=25 deg | 0.885656308565572 | 0.885656308565571 | 5.55e-16 | 5.68e-13 | pass | TMM rounding + stated err | 1.09e-15 | 5.34e-16 |
| airy T (s) | 1.0/2.3/1.0, d=1700 nm, lam=1064, th0=25 deg | 0.684707724254464 | 0.684707724254464 | 2.22e-16 | 3.18e-13 | pass | TMM rounding + stated err | 2.08e-15 | 1.86e-15 |
| airy T (p) | 1.0/2.3/1.0, d=1700 nm, lam=1064, th0=25 deg | 0.777808997265868 | 0.777808997265868 | 1.11e-16 | 3.02e-13 | pass | TMM rounding + stated err | 2.04e-15 | 1.93e-15 |
| airy T (s) | 1.0/2.3/1.0, d=1700 nm, lam=1550, th0=25 deg | 0.982459395193839 | 0.982459395193838 | 2.22e-16 | 2.52e-13 | pass | TMM rounding + stated err | 4.87e-16 | 7.09e-16 |
| airy T (p) | 1.0/2.3/1.0, d=1700 nm, lam=1550, th0=25 deg | 0.989045523256442 | 0.989045523256442 | 3.33e-16 | 2.11e-13 | pass | TMM rounding + stated err | 2.54e-17 | 3.08e-16 |
| airy T (s) | 1.0/2.3/1.52, d=1700 nm, lam=450, th0=25 deg | 0.918674717381737 | 0.918674717381737 | 0.00e+00 | 6.32e-13 | pass | TMM rounding + stated err | 1.49e-15 | 1.49e-15 |
| airy T (p) | 1.0/2.3/1.52, d=1700 nm, lam=450, th0=25 deg | 0.948520894637532 | 0.948520894637533 | 5.55e-16 | 5.88e-13 | pass | TMM rounding + stated err | 9.14e-16 | 1.47e-15 |
| airy T (s) | 1.0/2.3/1.52, d=1700 nm, lam=633, th0=25 deg | 0.871340318612553 | 0.871340318612553 | 2.22e-16 | 4.72e-13 | pass | TMM rounding + stated err | 6.39e-16 | 4.17e-16 |
| airy T (p) | 1.0/2.3/1.52, d=1700 nm, lam=633, th0=25 deg | 0.912679604514223 | 0.912679604514223 | 6.66e-16 | 4.40e-13 | pass | TMM rounding + stated err | 3.73e-16 | 1.04e-15 |
| airy T (s) | 1.0/2.3/1.52, d=1700 nm, lam=1064, th0=25 deg | 0.795888523545619 | 0.795888523545619 | 3.33e-16 | 2.67e-13 | pass | TMM rounding + stated err | 1.32e-15 | 9.89e-16 |
| airy T (p) | 1.0/2.3/1.52, d=1700 nm, lam=1064, th0=25 deg | 0.853350676398857 | 0.853350676398858 | 6.66e-16 | 2.57e-13 | pass | TMM rounding + stated err | 1.00e-15 | 1.67e-15 |
| airy T (s) | 1.0/2.3/1.52, d=1700 nm, lam=1550, th0=25 deg | 0.938411050032186 | 0.938411050032186 | 3.33e-16 | 1.79e-13 | pass | TMM rounding + stated err | 1.15e-16 | 4.48e-16 |
| airy T (p) | 1.0/2.3/1.52, d=1700 nm, lam=1550, th0=25 deg | 0.963164569418718 | 0.963164569418718 | 4.44e-16 | 1.69e-13 | pass | TMM rounding + stated err | 2.68e-16 | 1.76e-16 |
| airy T (s) | 1.33/1.6/1.0, d=1700 nm, lam=450, th0=25 deg | 0.882175610171385 | 0.882175610171385 | 1.11e-16 | 3.53e-13 | pass | TMM rounding + stated err | 2.52e-16 | 3.63e-16 |
| airy T (p) | 1.33/1.6/1.0, d=1700 nm, lam=450, th0=25 deg | 0.954534391715162 | 0.954534391715162 | 0.00e+00 | 3.44e-13 | pass | TMM rounding + stated err | 6.24e-16 | 6.24e-16 |
| airy T (s) | 1.33/1.6/1.0, d=1700 nm, lam=633, th0=25 deg | 0.962669759274672 | 0.962669759274673 | 5.55e-16 | 2.61e-13 | pass | TMM rounding + stated err | 6.98e-17 | 6.25e-16 |
| airy T (p) | 1.33/1.6/1.0, d=1700 nm, lam=633, th0=25 deg | 0.989569707085847 | 0.989569707085846 | 3.33e-16 | 2.48e-13 | pass | TMM rounding + stated err | 6.33e-16 | 3.00e-16 |
| airy T (s) | 1.33/1.6/1.0, d=1700 nm, lam=1064, th0=25 deg | 0.91827739306646 | 0.918277393066461 | 1.11e-16 | 1.70e-13 | pass | TMM rounding + stated err | 1.61e-16 | 5.03e-17 |
| airy T (p) | 1.33/1.6/1.0, d=1700 nm, lam=1064, th0=25 deg | 0.970693202688619 | 0.970693202688618 | 7.77e-16 | 1.58e-13 | pass | TMM rounding + stated err | 5.07e-16 | 2.71e-16 |
| airy T (s) | 1.33/1.6/1.0, d=1700 nm, lam=1550, th0=25 deg | 0.892620253900059 | 0.892620253900059 | 2.22e-16 | 1.20e-13 | pass | TMM rounding + stated err | 1.96e-16 | 4.18e-16 |
| airy T (p) | 1.33/1.6/1.0, d=1700 nm, lam=1550, th0=25 deg | 0.959287176919471 | 0.95928717691947 | 4.44e-16 | 1.13e-13 | pass | TMM rounding + stated err | 6.07e-16 | 1.63e-16 |
| airy T (s) | 1.0/1.45/3.5, d=1700 nm, lam=450, th0=25 deg | 0.940058857126878 | 0.940058857126877 | 2.22e-16 | 3.62e-13 | pass | TMM rounding + stated err | 2.94e-16 | 5.16e-16 |
| airy T (p) | 1.0/1.45/3.5, d=1700 nm, lam=450, th0=25 deg | 0.932698322623139 | 0.932698322623139 | 1.11e-16 | 3.32e-13 | pass | TMM rounding + stated err | 1.93e-16 | 8.21e-17 |
| airy T (s) | 1.0/1.45/3.5, d=1700 nm, lam=633, th0=25 deg | 0.931836847728408 | 0.931836847728409 | 3.33e-16 | 2.87e-13 | pass | TMM rounding + stated err | 2.96e-16 | 3.69e-17 |
| airy T (p) | 1.0/1.45/3.5, d=1700 nm, lam=633, th0=25 deg | 0.927314870199218 | 0.927314870199218 | 2.22e-16 | 2.57e-13 | pass | TMM rounding + stated err | 1.53e-16 | 3.75e-16 |
| airy T (s) | 1.0/1.45/3.5, d=1700 nm, lam=1064, th0=25 deg | 0.923784840566841 | 0.923784840566841 | 1.11e-16 | 1.85e-13 | pass | TMM rounding + stated err | 3.24e-16 | 2.13e-16 |
| airy T (p) | 1.0/1.45/3.5, d=1700 nm, lam=1064, th0=25 deg | 0.922011324237843 | 0.922011324237843 | 1.11e-16 | 1.65e-13 | pass | TMM rounding + stated err | 1.29e-16 | 2.40e-16 |
| airy T (s) | 1.0/1.45/3.5, d=1700 nm, lam=1550, th0=25 deg | 0.659889951706491 | 0.659889951706492 | 1.11e-16 | 6.82e-14 | pass | TMM rounding + stated err | 2.29e-16 | 1.18e-16 |
| airy T (p) | 1.0/1.45/3.5, d=1700 nm, lam=1550, th0=25 deg | 0.729042500180569 | 0.729042500180569 | 2.22e-16 | 7.43e-14 | pass | TMM rounding + stated err | 2.01e-16 | 4.23e-16 |
| quarter_wave_R R (s) | quarter-wave 1.0/1.38/1.5, th0=0 deg | 0.0141104586417784 | 0.0141104586417784 | 5.20e-18 | 2.04e-15 | pass | TMM rounding + running error | 5.56e-18 | 3.54e-19 |
| quarter_wave_R R (s) | quarter-wave 1.0/1.22474/1.5, th0=0 deg | 5.47820073070147e-33 | 1.10868324830005e-32 | 5.61e-33 | 1.69e-30 | pass | TMM rounding + running error | 2.75e-33 | 2.86e-33 |
| quarter_wave_R R (s) | quarter-wave 1.0/2/1.5, th0=0 deg | 0.206611570247934 | 0.206611570247934 | 5.55e-17 | 9.07e-15 | pass | TMM rounding + running error | 2.20e-17 | 3.35e-17 |
| quarter_wave_R R (s) | quarter-wave 1.33/1.6/1.52, th0=0 deg | 0.013809430294877 | 0.0138094302948769 | 3.47e-18 | 1.92e-15 | pass | TMM rounding + running error | 9.12e-19 | 2.56e-18 |
| quarter_wave_stack_R R (s) | (2.3/1.38)^1 on 1.52, th0=0 deg | 0.380715255771843 | 0.380715255771842 | 1.67e-16 | 1.99e-14 | pass | TMM rounding + running error | 1.53e-16 | 1.36e-17 |
| quarter_wave_stack_R R (s) | (2.3/1.38)^5 on 1.52, th0=0 deg | 0.984213695272784 | 0.984213695272784 | 2.22e-16 | 1.13e-13 | pass | TMM rounding + running error | 8.99e-17 | 1.32e-16 |
| quarter_wave_stack_R R (s) | (2.3/1.38)^15 on 1.52, th0=0 deg | 0.999999418226696 | 0.999999418226696 | 0.00e+00 | 3.00e-13 | pass | TMM rounding + running error | 3.47e-17 | 3.47e-17 |
| ftir_T T (s) | FTIR gap 100 nm, th0=45 deg | 0.737255265713891 | 0.73725526571389 | 1.11e-16 | 3.23e-14 | pass | TMM rounding + running error | 1.75e-17 | 9.35e-17 |
| ftir_T T (p) | FTIR gap 100 nm, th0=45 deg | 0.877799865834103 | 0.877799865834103 | 1.11e-16 | 3.42e-14 | pass | TMM rounding + running error | 1.27e-16 | 2.38e-16 |
| ftir_T T (s) | FTIR gap 300 nm, th0=60 deg | 0.0279901661091892 | 0.0279901661091891 | 2.08e-17 | 5.60e-15 | pass | TMM rounding + running error | 4.70e-19 | 2.03e-17 |
| ftir_T T (p) | FTIR gap 300 nm, th0=60 deg | 0.0137438633610422 | 0.0137438633610422 | 1.04e-17 | 3.52e-15 | pass | TMM rounding + running error | 7.94e-19 | 9.61e-18 |
| ftir_T T (s) | FTIR gap 1000 nm, th0=60 deg | 2.81189649253601e-07 | 2.81189649253601e-07 | 0.00e+00 | 1.50e-19 | pass | TMM rounding + running error | 7.07e-22 | 7.07e-22 |
| ftir_T T (p) | FTIR gap 1000 nm, th0=60 deg | 1.36076674205703e-07 | 1.36076674205703e-07 | 5.29e-23 | 7.97e-20 | pass | TMM rounding + running error | 3.15e-22 | 3.68e-22 |
| ftir_T T (s) | FTIR gap 300 nm, th0=41.8103 deg | 0.265177915502342 | 0.265177915894324 | 3.92e-10 | 5.85e-01 | pass | TMM rounding + running error | 7.14e-17 | 3.92e-10 |
| ftir_T T (p) | FTIR gap 300 nm, th0=41.8103 deg | 0.646258464852598 | 0.646258465814433 | 9.62e-10 | 6.86e-01 | pass | TMM rounding + running error | 1.50e-16 | 9.62e-10 |
| evanescent_length 1/kappa | glass/air, th0 = th_c + 1e-09 rad | 2130499.08714835 | 2130499.12456089 | 3.74e-02 | 6.46e+00 | pass | one rounding + TMM rounding | 1.74e-10 | 3.74e-02 |
| evanescent_length 1/kappa | glass/air, th0 = th_c + 1e-06 rad | 67372.2910737885 | 67372.2910760103 | 2.22e-06 | 2.04e-04 | pass | one rounding + TMM rounding | 1.63e-12 | 2.22e-06 |
| evanescent_length 1/kappa | glass/air, th0 = th_c + 0.001 rad | 2130.3806504268 | 2130.38065042664 | 1.67e-10 | 6.68e-09 | pass | one rounding + TMM rounding | 1.32e-13 | 1.67e-10 |
| evanescent_length 1/kappa | glass/air, th0 = th_c + 0.1 rad | 212.573234248912 | 212.573234248912 | 8.53e-14 | 1.02e-11 | pass | one rounding + TMM rounding | 8.31e-15 | 9.36e-14 |
| evanescent_length 1/kappa | glass/air, th0 = th_c + 0.5 rad | 100.833075410518 | 100.833075410518 | 2.84e-14 | 2.00e-12 | pass | one rounding + TMM rounding | 6.07e-16 | 2.90e-14 |
| absorption in layer 1 (s) | absorbing 4 layers, th0=0 deg | 0.0169552106325491 | 0.0169552106325487 | 3.75e-16 | 7.10e-14 | pass | TMM rounding (fluxes) | 1.04e-17 | 3.85e-16 |
| absorption in layer 2 (s) | absorbing 4 layers, th0=0 deg | 0.242207011807042 | 0.242207011807042 | 2.78e-17 | 8.49e-14 | pass | TMM rounding (fluxes) | 1.11e-16 | 1.39e-16 |
| absorption in layer 3 (s) | absorbing 4 layers, th0=0 deg | 0 | -0 | 0.00e+00 | 5.04e-14 | pass | TMM rounding (fluxes) | 1.15e-41 | 1.15e-41 |
| absorption in layer 4 (s) | absorbing 4 layers, th0=0 deg | 0.0127418517090554 | 0.0127418517090552 | 1.96e-16 | 4.26e-14 | pass | TMM rounding (fluxes) | 1.73e-18 | 1.98e-16 |
| \|E\|^2 (s) | absorbing 4 layers, th0=0 deg, layer 0, depth -100 nm | 2.34789276341058 | 2.34789276341058 | 8.88e-16 | 3.59e-13 | pass | TMM rounding | 4.44e-16 | 1.33e-15 |
| \|E\|^2 (s) | absorbing 4 layers, th0=0 deg, layer 1, depth 0 nm | 1.6258321374251 | 1.6258321374251 | 0.00e+00 | 3.25e-13 | pass | TMM rounding | 4.44e-16 | 4.44e-16 |
| \|E\|^2 (s) | absorbing 4 layers, th0=0 deg, layer 1, depth 36 nm | 0.912904014822811 | 0.912904014822811 | 0.00e+00 | 2.26e-13 | pass | TMM rounding | 2.22e-16 | 2.22e-16 |
| \|E\|^2 (s) | absorbing 4 layers, th0=0 deg, layer 1, depth 119.88 nm | 0.216029256651077 | 0.216029256651078 | 3.05e-16 | 6.47e-14 | pass | TMM rounding | 1.94e-16 | 5.00e-16 |
| \|E\|^2 (s) | absorbing 4 layers, th0=0 deg, layer 2, depth 0 nm | 0.21719002243533 | 0.21719002243533 | 2.78e-17 | 6.17e-14 | pass | TMM rounding | 1.39e-16 | 1.11e-16 |
| \|E\|^2 (s) | absorbing 4 layers, th0=0 deg, layer 2, depth 10.5 nm | 0.337603956520313 | 0.337603956520313 | 2.22e-16 | 8.23e-14 | pass | TMM rounding | 3.33e-16 | 1.11e-16 |
| \|E\|^2 (s) | absorbing 4 layers, th0=0 deg, layer 2, depth 34.965 nm | 0.690695841091938 | 0.690695841091938 | 4.44e-16 | 1.36e-13 | pass | TMM rounding | 6.66e-16 | 2.22e-16 |
| \|E\|^2 (s) | absorbing 4 layers, th0=0 deg, layer 3, depth 0 nm | 0.691196603074408 | 0.691196603074408 | 2.22e-16 | 1.34e-13 | pass | TMM rounding | 3.33e-16 | 1.11e-16 |
| \|E\|^2 (s) | absorbing 4 layers, th0=0 deg, layer 3, depth 60 nm | 1.35872990470784 | 1.35872990470784 | 8.88e-16 | 2.29e-13 | pass | TMM rounding | 1.11e-15 | 2.22e-16 |
| \|E\|^2 (s) | absorbing 4 layers, th0=0 deg, layer 3, depth 199.8 nm | 0.13773417184728 | 0.13773417184728 | 8.33e-17 | 4.06e-14 | pass | TMM rounding | 1.11e-16 | 2.78e-17 |
| \|E\|^2 (s) | absorbing 4 layers, th0=0 deg, layer 4, depth 0 nm | 0.136501856307884 | 0.136501856307884 | 1.67e-16 | 3.59e-14 | pass | TMM rounding | 1.39e-16 | 2.78e-17 |
| \|E\|^2 (s) | absorbing 4 layers, th0=0 deg, layer 4, depth 24 nm | 0.05470166572596 | 0.05470166572596 | 6.94e-18 | 1.26e-14 | pass | TMM rounding | 6.94e-18 | 0.00e+00 |
| \|E\|^2 (s) | absorbing 4 layers, th0=0 deg, layer 4, depth 79.92 nm | 0.284976581369974 | 0.284976581369974 | 5.55e-17 | 6.39e-14 | pass | TMM rounding | 0.00e+00 | 5.55e-17 |
| absorption in layer 1 (s) | absorbing 4 layers, th0=40 deg | 0.00950198019004767 | 0.00950198019004711 | 5.60e-16 | 5.98e-14 | pass | TMM rounding (fluxes) | 1.04e-17 | 5.71e-16 |
| absorption in layer 2 (s) | absorbing 4 layers, th0=40 deg | 0.351201297263815 | 0.351201297263815 | 1.67e-16 | 7.88e-14 | pass | TMM rounding (fluxes) | 0.00e+00 | 1.67e-16 |
| absorption in layer 3 (s) | absorbing 4 layers, th0=40 deg | 0 | 1.11022302462516e-16 | 1.11e-16 | 3.43e-14 | pass | TMM rounding (fluxes) | 5.74e-42 | 1.11e-16 |
| absorption in layer 4 (s) | absorbing 4 layers, th0=40 deg | 0.00793979975604331 | 0.00793979975604331 | 1.73e-18 | 2.49e-14 | pass | TMM rounding (fluxes) | 5.20e-18 | 3.47e-18 |
| \|E\|^2 (s) | absorbing 4 layers, th0=40 deg, layer 0, depth -100 nm | 2.10340256131299 | 2.10340256131299 | 0.00e+00 | 3.28e-13 | pass | TMM rounding | 4.44e-16 | 4.44e-16 |
| \|E\|^2 (s) | absorbing 4 layers, th0=40 deg, layer 1, depth 0 nm | 0.70351443133308 | 0.70351443133308 | 3.33e-16 | 1.77e-13 | pass | TMM rounding | 5.55e-16 | 2.22e-16 |
| \|E\|^2 (s) | absorbing 4 layers, th0=40 deg, layer 1, depth 36 nm | 0.296318667416733 | 0.296318667416733 | 5.55e-17 | 9.34e-14 | pass | TMM rounding | 2.22e-16 | 1.67e-16 |
| \|E\|^2 (s) | absorbing 4 layers, th0=40 deg, layer 1, depth 119.88 nm | 0.319220761438952 | 0.319220761438952 | 3.89e-16 | 7.18e-14 | pass | TMM rounding | 5.55e-17 | 4.44e-16 |
| \|E\|^2 (s) | absorbing 4 layers, th0=40 deg, layer 2, depth 0 nm | 0.320365810385092 | 0.320365810385092 | 3.89e-16 | 6.94e-14 | pass | TMM rounding | 0.00e+00 | 3.89e-16 |
| \|E\|^2 (s) | absorbing 4 layers, th0=40 deg, layer 2, depth 10.5 nm | 0.423956601870677 | 0.423956601870678 | 5.55e-16 | 8.24e-14 | pass | TMM rounding | 2.22e-16 | 3.33e-16 |
| \|E\|^2 (s) | absorbing 4 layers, th0=40 deg, layer 2, depth 34.965 nm | 0.643089928393834 | 0.643089928393834 | 1.11e-16 | 1.05e-13 | pass | TMM rounding | 1.11e-16 | 2.22e-16 |
| \|E\|^2 (s) | absorbing 4 layers, th0=40 deg, layer 3, depth 0 nm | 0.643336627649802 | 0.643336627649802 | 3.33e-16 | 1.05e-13 | pass | TMM rounding | 1.11e-16 | 2.22e-16 |
| \|E\|^2 (s) | absorbing 4 layers, th0=40 deg, layer 3, depth 60 nm | 0.862198033140231 | 0.862198033140231 | 6.66e-16 | 1.54e-13 | pass | TMM rounding | 5.55e-16 | 1.11e-16 |
| \|E\|^2 (s) | absorbing 4 layers, th0=40 deg, layer 3, depth 199.8 nm | 0.0610632983419718 | 0.0610632983419718 | 6.94e-18 | 1.98e-14 | pass | TMM rounding | 3.47e-17 | 4.16e-17 |
| \|E\|^2 (s) | absorbing 4 layers, th0=40 deg, layer 4, depth 0 nm | 0.0604611630583248 | 0.0604611630583248 | 1.39e-17 | 1.76e-14 | pass | TMM rounding | 3.47e-17 | 4.86e-17 |
| \|E\|^2 (s) | absorbing 4 layers, th0=40 deg, layer 4, depth 24 nm | 0.0231890445010296 | 0.0231890445010297 | 3.47e-17 | 5.84e-15 | pass | TMM rounding | 2.08e-17 | 1.39e-17 |
| \|E\|^2 (s) | absorbing 4 layers, th0=40 deg, layer 4, depth 79.92 nm | 0.14066871475114 | 0.14066871475114 | 1.67e-16 | 3.30e-14 | pass | TMM rounding | 1.11e-16 | 5.55e-17 |
| absorption in layer 1 (s) | absorbing 4 layers, th0=85 deg | 0.0021905976483532 | 0.00219059764835319 | 4.77e-18 | 1.32e-14 | pass | TMM rounding (fluxes) | 3.90e-18 | 8.67e-18 |
| absorption in layer 2 (s) | absorbing 4 layers, th0=85 deg | 0.104165561156914 | 0.104165561156914 | 2.22e-16 | 7.22e-14 | pass | TMM rounding (fluxes) | 1.94e-16 | 2.78e-17 |
| absorption in layer 3 (s) | absorbing 4 layers, th0=85 deg | 0 | 3.46944695195361e-18 | 3.47e-18 | 4.12e-15 | pass | TMM rounding (fluxes) | 0.00e+00 | 3.47e-18 |
| absorption in layer 4 (s) | absorbing 4 layers, th0=85 deg | 0.000873937755169323 | 0.000873937755169342 | 1.85e-17 | 3.09e-15 | pass | TMM rounding (fluxes) | 1.73e-18 | 1.68e-17 |
| \|E\|^2 (s) | absorbing 4 layers, th0=85 deg, layer 0, depth -100 nm | 0.0334186632154931 | 0.0334186632154932 | 1.46e-16 | 4.31e-14 | pass | TMM rounding | 1.53e-16 | 6.94e-18 |
| \|E\|^2 (s) | absorbing 4 layers, th0=85 deg, layer 1, depth 0 nm | 0.00603133468880244 | 0.00603133468880246 | 2.17e-17 | 8.31e-15 | pass | TMM rounding | 2.34e-17 | 1.73e-18 |
| \|E\|^2 (s) | absorbing 4 layers, th0=85 deg, layer 1, depth 36 nm | 0.00432006699206307 | 0.00432006699206309 | 1.73e-17 | 5.90e-15 | pass | TMM rounding | 1.65e-17 | 8.67e-19 |
| \|E\|^2 (s) | absorbing 4 layers, th0=85 deg, layer 1, depth 119.88 nm | 0.0140221266041242 | 0.0140221266041243 | 4.68e-17 | 1.79e-14 | pass | TMM rounding | 4.68e-17 | 0.00e+00 |
| \|E\|^2 (s) | absorbing 4 layers, th0=85 deg, layer 2, depth 0 nm | 0.0140442889248185 | 0.0140442889248186 | 4.86e-17 | 1.78e-14 | pass | TMM rounding | 4.51e-17 | 3.47e-18 |
| \|E\|^2 (s) | absorbing 4 layers, th0=85 deg, layer 2, depth 10.5 nm | 0.0158171968286815 | 0.0158171968286816 | 5.55e-17 | 1.99e-14 | pass | TMM rounding | 5.55e-17 | 0.00e+00 |
| \|E\|^2 (s) | absorbing 4 layers, th0=85 deg, layer 2, depth 34.965 nm | 0.0180030813460795 | 0.0180030813460796 | 7.29e-17 | 2.23e-14 | pass | TMM rounding | 6.59e-17 | 6.94e-18 |
| \|E\|^2 (s) | absorbing 4 layers, th0=85 deg, layer 3, depth 0 nm | 0.018003787075013 | 0.018003787075013 | 6.59e-17 | 2.23e-14 | pass | TMM rounding | 6.59e-17 | 0.00e+00 |
| \|E\|^2 (s) | absorbing 4 layers, th0=85 deg, layer 3, depth 60 nm | 0.0157169483747845 | 0.0157169483747845 | 6.94e-17 | 1.95e-14 | pass | TMM rounding | 6.25e-17 | 6.94e-18 |
| \|E\|^2 (s) | absorbing 4 layers, th0=85 deg, layer 3, depth 199.8 nm | 0.000666501930070175 | 0.00066650193007018 | 4.23e-18 | 9.39e-16 | pass | TMM rounding | 3.69e-18 | 5.42e-19 |
| \|E\|^2 (s) | absorbing 4 layers, th0=85 deg, layer 4, depth 0 nm | 0.000658766346943145 | 0.000658766346943149 | 3.58e-18 | 9.03e-16 | pass | TMM rounding | 3.79e-18 | 2.17e-19 |
| \|E\|^2 (s) | absorbing 4 layers, th0=85 deg, layer 4, depth 24 nm | 0.000232824065984865 | 0.000232824065984866 | 8.67e-19 | 3.11e-16 | pass | TMM rounding | 8.13e-19 | 5.42e-20 |
| \|E\|^2 (s) | absorbing 4 layers, th0=85 deg, layer 4, depth 79.92 nm | 0.00185445623379958 | 0.00185445623379959 | 7.16e-18 | 2.38e-15 | pass | TMM rounding | 7.59e-18 | 4.34e-19 |
| absorption in layer 1 (s) | metal film 30 nm, th0=0 deg | 0.082770576168342 | 0.0827705761683424 | 3.47e-16 | 1.10e-14 | pass | TMM rounding (fluxes) | 0.00e+00 | 3.47e-16 |
| \|E\|^2 (s) | metal film 30 nm, th0=0 deg, layer 0, depth -100 nm | 3.17594885513718 | 3.17594885513718 | 1.78e-15 | 9.68e-14 | pass | TMM rounding | 4.44e-16 | 1.33e-15 |
| \|E\|^2 (s) | metal film 30 nm, th0=0 deg, layer 1, depth 0 nm | 0.374413059183051 | 0.37441305918305 | 1.11e-16 | 1.97e-14 | pass | TMM rounding | 5.55e-17 | 5.55e-17 |
| \|E\|^2 (s) | metal film 30 nm, th0=0 deg, layer 1, depth 9 nm | 0.238876635338652 | 0.238876635338652 | 1.11e-16 | 1.47e-14 | pass | TMM rounding | 1.39e-16 | 2.78e-17 |
| \|E\|^2 (s) | metal film 30 nm, th0=0 deg, layer 1, depth 29.97 nm | 0.142341216291856 | 0.142341216291856 | 8.33e-17 | 1.12e-14 | pass | TMM rounding | 5.55e-17 | 2.78e-17 |
| absorption in layer 1 (s) | metal film 30 nm, th0=60 deg | 0.0479261747714434 | 0.0479261747714436 | 2.43e-16 | 8.23e-15 | pass | TMM rounding (fluxes) | 2.78e-17 | 2.15e-16 |
| \|E\|^2 (s) | metal film 30 nm, th0=60 deg, layer 0, depth -100 nm | 1.4087651528904 | 1.4087651528904 | 0.00e+00 | 1.06e-13 | pass | TMM rounding | 4.44e-16 | 4.44e-16 |
| \|E\|^2 (s) | metal film 30 nm, th0=60 deg, layer 1, depth 0 nm | 0.109142825083165 | 0.109142825083166 | 1.25e-16 | 1.16e-14 | pass | TMM rounding | 2.78e-17 | 9.71e-17 |
| \|E\|^2 (s) | metal film 30 nm, th0=60 deg, layer 1, depth 9 nm | 0.0691421919255005 | 0.0691421919255005 | 5.55e-17 | 8.05e-15 | pass | TMM rounding | 1.39e-17 | 4.16e-17 |
| \|E\|^2 (s) | metal film 30 nm, th0=60 deg, layer 1, depth 29.97 nm | 0.0410853961439828 | 0.0410853961439828 | 3.47e-17 | 5.53e-15 | pass | TMM rounding | 2.08e-17 | 1.39e-17 |
| absorption in layer 1 (s) | Kretschmann 50 nm, th0=44 deg | 0.0739901496027366 | 0.0739901496027366 | 4.16e-17 | 9.58e-15 | pass | TMM rounding (fluxes) | 0.00e+00 | 4.16e-17 |
| \|E\|^2 (s) | Kretschmann 50 nm, th0=44 deg, layer 0, depth -100 nm | 3.72331354129088 | 3.72331354129088 | 0.00e+00 | 1.12e-13 | pass | TMM rounding | 4.44e-16 | 4.44e-16 |
| \|E\|^2 (s) | Kretschmann 50 nm, th0=44 deg, layer 1, depth 0 nm | 0.375216958011807 | 0.375216958011807 | 0.00e+00 | 2.64e-14 | pass | TMM rounding | 5.55e-17 | 5.55e-17 |
| \|E\|^2 (s) | Kretschmann 50 nm, th0=44 deg, layer 1, depth 15 nm | 0.146980984557929 | 0.146980984557929 | 8.33e-17 | 1.26e-14 | pass | TMM rounding | 0.00e+00 | 8.33e-17 |
| \|E\|^2 (s) | Kretschmann 50 nm, th0=44 deg, layer 1, depth 49.95 nm | 0.0390445494469133 | 0.0390445494469133 | 2.08e-17 | 5.29e-15 | pass | TMM rounding | 1.39e-17 | 3.47e-17 |
| absorption in layer 1 (s) | weak absorber 500 nm, th0=0 deg | 0.388521129565719 | 0.38852112956572 | 7.77e-16 | 4.09e-14 | pass | TMM rounding (fluxes) | 5.55e-17 | 7.22e-16 |
| \|E\|^2 (s) | weak absorber 500 nm, th0=0 deg, layer 0, depth -100 nm | 1.06691791560419 | 1.06691791560419 | 0.00e+00 | 3.98e-14 | pass | TMM rounding | 0.00e+00 | 0.00e+00 |
| \|E\|^2 (s) | weak absorber 500 nm, th0=0 deg, layer 1, depth 0 nm | 1.01424287350945 | 1.01424287350945 | 6.66e-16 | 4.06e-14 | pass | TMM rounding | 0.00e+00 | 6.66e-16 |
| \|E\|^2 (s) | weak absorber 500 nm, th0=0 deg, layer 1, depth 150 nm | 0.84380881024527 | 0.84380881024527 | 0.00e+00 | 3.84e-14 | pass | TMM rounding | 3.33e-16 | 3.33e-16 |
| \|E\|^2 (s) | weak absorber 500 nm, th0=0 deg, layer 1, depth 499.5 nm | 0.609954836931706 | 0.609954836931706 | 2.22e-16 | 4.31e-14 | pass | TMM rounding | 3.33e-16 | 1.11e-16 |
| absorption in layer 1 (s) | weak absorber 500 nm, th0=70 deg | 0.665723675810707 | 0.665723675810707 | 1.11e-16 | 4.66e-14 | pass | TMM rounding (fluxes) | 1.11e-16 | 0.00e+00 |
| \|E\|^2 (s) | weak absorber 500 nm, th0=70 deg, layer 0, depth -100 nm | 1.25150190144364 | 1.25150190144364 | 4.44e-16 | 1.31e-13 | pass | TMM rounding | 6.66e-16 | 1.11e-15 |
| \|E\|^2 (s) | weak absorber 500 nm, th0=70 deg, layer 1, depth 0 nm | 0.932630469146541 | 0.932630469146541 | 2.22e-16 | 1.18e-13 | pass | TMM rounding | 7.77e-16 | 9.99e-16 |
| \|E\|^2 (s) | weak absorber 500 nm, th0=70 deg, layer 1, depth 150 nm | 0.539926537054245 | 0.539926537054245 | 5.55e-16 | 7.79e-14 | pass | TMM rounding | 2.22e-16 | 7.77e-16 |
| \|E\|^2 (s) | weak absorber 500 nm, th0=70 deg, layer 1, depth 499.5 nm | 0.276636467920453 | 0.276636467920453 | 5.55e-17 | 5.85e-14 | pass | TMM rounding | 1.11e-16 | 1.67e-16 |

## QuTiP (`test_ext_qubits_qutip.py`)

| quantity | inputs | engine | library | diff | tol | status | basis | eng err | lib err |
|---|---|---|---|---|---|---|---|---|---|
| singlet E(a,b) | z,z | -1 | -1 | 4.44e-16 | 7.55e-15 | pass | contraction 34 | 2.22e-16 | 2.22e-16 |
| singlet E(a,b) | z,x | 0 | 0 | 0.00e+00 | 0.00e+00 | pass | contraction 34 | 0.00e+00 | 0.00e+00 |
| singlet E(a,b) | z,45deg | -0.707106781186547 | -0.707106781186548 | 2.22e-16 | 5.34e-15 | pass | contraction 34 | 1.74e-16 | 4.83e-17 |
| singlet E(a,b) | z,135deg | 0.707106781186547 | 0.707106781186548 | 2.22e-16 | 5.34e-15 | pass | contraction 34 | 1.74e-16 | 4.83e-17 |
| singlet E(a,b) | z,-z | 1 | 1 | 4.44e-16 | 7.55e-15 | pass | contraction 34 | 2.22e-16 | 2.22e-16 |
| singlet E(a,b) | oblique | -0.161919178143782 | -0.161919178143782 | 5.55e-17 | 6.81e-15 | pass | contraction 34 | 2.41e-17 | 3.15e-17 |
| singlet E(a,b) | oblique y | -0.7999996000003 | -0.7999996000003 | 3.33e-16 | 7.55e-15 | pass | contraction 34 | 2.33e-16 | 9.98e-17 |
| singlet E(a,b) | nearly parallel | -1 | -1 | 4.44e-16 | 7.55e-15 | pass | contraction 34 | 1.72e-16 | 2.72e-16 |
| singlet E(a,b) | unnormalised | 0 | 0 | 0.00e+00 | 4.53e-15 | pass | contraction 34 | 0.00e+00 | 0.00e+00 |
| CHSH S (singlet) | optimal angles | -2.82842712474619 | -2.82842712474619 | 8.88e-16 | 2.40e-14 | pass | contraction 34 x 4 | 2.51e-16 | 6.37e-16 |
| Phi+ polarizer E(alpha,beta) | 0,0 | 1 | 1 | 4.44e-16 | 9.33e-15 | pass | contraction 34 | 2.22e-16 | 2.22e-16 |
| Phi+ polarizer E(alpha,beta) | 0,0.392699082 | 0.707106781186547 | 0.707106781186548 | 1.11e-16 | 7.74e-15 | pass | contraction 34 | 8.43e-17 | 2.67e-17 |
| Phi+ polarizer E(alpha,beta) | 0,0.785398163 | 6.12323399573676e-17 | 0 | 6.12e-17 | 2.13e-15 | pass | contraction 34 | 1.08e-32 | 6.12e-17 |
| Phi+ polarizer E(alpha,beta) | 0.392699,1.17809725 | 0 | 1.57009245868378e-16 | 1.57e-16 | 1.11e-14 | pass | contraction 34 | 6.12e-17 | 9.58e-17 |
| Phi+ polarizer E(alpha,beta) | 0.3,1.9 | -0.998294775794753 | -0.998294775794753 | 2.22e-16 | 1.16e-14 | pass | contraction 34 | 1.96e-16 | 2.60e-17 |
| Phi+ polarizer E(alpha,beta) | 1,1.0000001 | 0.99999999999998 | 0.99999999999998 | 4.44e-16 | 1.11e-14 | pass | contraction 34 | 2.06e-16 | 2.38e-16 |
| Bloch r_x | \|0> | 0 | 0 | 0.00e+00 | 0.00e+00 | pass | contraction 12 |  |  |
| Bloch r_y | \|0> | 0 | 0 | 0.00e+00 | 0.00e+00 | pass | contraction 12 |  |  |
| Bloch r_z | \|0> | 1 | 1 | 0.00e+00 | 2.66e-15 | pass | contraction 12 |  |  |
| Born P(+n) | \|0>; n=z | 1 | 1 | 0.00e+00 | 2.66e-15 | pass | contraction 12 |  |  |
| Lueders state max\|entry diff\| | \|0>; n=z | 0 | 0 | 0.00e+00 | 7.33e-15 | pass | Lueders |  |  |
| Born P(+n) | \|0>; n=x | 0.5 | 0.5 | 0.00e+00 | 1.33e-15 | pass | contraction 12 |  |  |
| Lueders state max\|entry diff\| | \|0>; n=x | 0 | 0 | 0.00e+00 | 3.66e-15 | pass | Lueders |  |  |
| Born P(+n) | \|0>; n=oblique | 0.905792067552021 | 0.905792067552021 | 0.00e+00 | 2.41e-15 | pass | contraction 12 |  |  |
| Lueders state max\|entry diff\| | \|0>; n=oblique | 0 | 0 | 0.00e+00 | 6.64e-15 | pass | Lueders |  |  |
| Born P(+n) | \|0>; n=-z | 0 | 0 | 0.00e+00 | 0.00e+00 | pass | contraction 12 |  |  |
| Bloch r_x | \|+i> | 0 | 0 | 0.00e+00 | 2.66e-15 | pass | contraction 12 |  |  |
| Bloch r_y | \|+i> | 1 | 1 | 0.00e+00 | 2.66e-15 | pass | contraction 12 |  |  |
| Bloch r_z | \|+i> | 0 | 0 | 0.00e+00 | 2.66e-15 | pass | contraction 12 |  |  |
| Born P(+n) | \|+i>; n=z | 0.5 | 0.5 | 0.00e+00 | 1.33e-15 | pass | contraction 12 |  |  |
| Lueders state max\|entry diff\| | \|+i>; n=z | 0 | 0 | 0.00e+00 | 7.33e-15 | pass | Lueders |  |  |
| Born P(+n) | \|+i>; n=x | 0.5 | 0.5 | 0.00e+00 | 2.66e-15 | pass | contraction 12 |  |  |
| Lueders state max\|entry diff\| | \|+i>; n=x | 0 | 0 | 0.00e+00 | 7.22e-15 | pass | Lueders |  |  |
| Born P(+n) | \|+i>; n=oblique | 0.249511069412333 | 0.249511069412333 | 0.00e+00 | 2.11e-15 | pass | contraction 12 |  |  |
| Lueders state max\|entry diff\| | \|+i>; n=oblique | 0 | 0 | 0.00e+00 | 2.06e-14 | pass | Lueders |  |  |
| Born P(+n) | \|+i>; n=-z | 0.5 | 0.5 | 0.00e+00 | 1.33e-15 | pass | contraction 12 |  |  |
| Lueders state max\|entry diff\| | \|+i>; n=-z | 0 | 0 | 0.00e+00 | 7.33e-15 | pass | Lueders |  |  |
| Bloch r_x | tilted pure | 0.548664201625441 | 0.548664201625441 | 0.00e+00 | 1.91e-15 | pass | contraction 12 |  |  |
| Bloch r_y | tilted pure | 0.462133481805161 | 0.462133481805161 | 0.00e+00 | 1.91e-15 | pass | contraction 12 |  |  |
| Bloch r_z | tilted pure | 0.696706709347165 | 0.696706709347165 | 0.00e+00 | 2.66e-15 | pass | contraction 12 |  |  |
| Born P(+n) | tilted pure; n=z | 0.848353354673583 | 0.848353354673583 | 0.00e+00 | 2.26e-15 | pass | contraction 12 |  |  |
| Lueders state max\|entry diff\| | tilted pure; n=z | 0 | 0 | 0.00e+00 | 7.33e-15 | pass | Lueders |  |  |
| Born P(+n) | tilted pure; n=x | 0.774332100812721 | 0.774332100812721 | 0.00e+00 | 2.29e-15 | pass | contraction 12 |  |  |
| Lueders state max\|entry diff\| | tilted pure; n=x | 0 | 0 | 0.00e+00 | 4.05e-15 | pass | Lueders |  |  |
| Born P(+n) | tilted pure; n=oblique | 0.749419319887357 | 0.749419319887357 | 1.11e-16 | 2.64e-15 | pass | contraction 12 |  |  |
| Lueders state max\|entry diff\| | tilted pure; n=oblique | 2.77555756156289e-17 | 0 | 2.78e-17 | 8.72e-15 | pass | Lueders |  |  |
| Born P(+n) | tilted pure; n=-z | 0.151646645326417 | 0.151646645326417 | 0.00e+00 | 4.04e-16 | pass | contraction 12 |  |  |
| Lueders state max\|entry diff\| | tilted pure; n=-z | 0 | 0 | 0.00e+00 | 7.33e-15 | pass | Lueders |  |  |
| Bloch r_x | mixed r=(0.2,-0.3,0.5) | 0.2 | 0.2 | 0.00e+00 | 9.61e-16 | pass | contraction 12 |  |  |
| Bloch r_y | mixed r=(0.2,-0.3,0.5) | -0.3 | -0.3 | 0.00e+00 | 9.61e-16 | pass | contraction 12 |  |  |
| Bloch r_z | mixed r=(0.2,-0.3,0.5) | 0.5 | 0.5 | 0.00e+00 | 2.66e-15 | pass | contraction 12 |  |  |
| Born P(+n) | mixed r=(0.2,-0.3,0.5); n=z | 0.75 | 0.75 | 0.00e+00 | 2.00e-15 | pass | contraction 12 |  |  |
| Lueders state max\|entry diff\| | mixed r=(0.2,-0.3,0.5); n=z | 0 | 0 | 0.00e+00 | 7.33e-15 | pass | Lueders |  |  |
| Born P(+n) | mixed r=(0.2,-0.3,0.5); n=x | 0.6 | 0.6 | 0.00e+00 | 1.81e-15 | pass | contraction 12 |  |  |
| Lueders state max\|entry diff\| | mixed r=(0.2,-0.3,0.5); n=x | 0 | 0 | 0.00e+00 | 4.14e-15 | pass | Lueders |  |  |
| Born P(+n) | mixed r=(0.2,-0.3,0.5); n=oblique | 0.808101384622831 | 0.808101384622831 | 0.00e+00 | 2.15e-15 | pass | contraction 12 |  |  |
| Lueders state max\|entry diff\| | mixed r=(0.2,-0.3,0.5); n=oblique | 0 | 0 | 0.00e+00 | 6.64e-15 | pass | Lueders |  |  |
| Born P(+n) | mixed r=(0.2,-0.3,0.5); n=-z | 0.25 | 0.25 | 0.00e+00 | 6.66e-16 | pass | contraction 12 |  |  |
| Lueders state max\|entry diff\| | mixed r=(0.2,-0.3,0.5); n=-z | 0 | 0 | 0.00e+00 | 7.33e-15 | pass | Lueders |  |  |
| Born P(A: +n) singlet | z | 0.5 | 0.5 | 2.22e-16 | 2.00e-15 | pass | contraction 18 |  |  |
| Born P(A: +n) singlet | x | 0.5 | 0.5 | 2.22e-16 | 2.00e-15 | pass | contraction 18 |  |  |
| Born P(A: +n) singlet | oblique | 0.5 | 0.5 | 2.22e-16 | 2.00e-15 | pass | contraction 18 |  |  |
| Born P(A: +n) singlet | -z | 0.5 | 0.5 | 2.22e-16 | 2.00e-15 | pass | contraction 18 |  |  |
| partial trace max\|entry diff\| | keep 0 | 0 | 0 | 0.00e+00 | 3.01e-16 | pass | contraction 2 |  |  |
| partial trace max\|entry diff\| | keep 1 | 0 | 0 | 0.00e+00 | 2.82e-16 | pass | contraction 2 |  |  |
| concurrence | singlet | 0.999999999999999 | 1 | 4.44e-16 | 6.58e-07 | pass | LAPACK eig + sqrt | 6.66e-16 | 2.22e-16 |
| entropy of rho_A (bits) | singlet | 1 | 1 | 0.00e+00 | 8.66e-15 | pass | LAPACK eig + h(x) | 0.00e+00 | 0.00e+00 |
| concurrence | Phi+ | 0.999999999999999 | 1 | 4.44e-16 | 6.58e-07 | pass | LAPACK eig + sqrt | 6.66e-16 | 2.22e-16 |
| entropy of rho_A (bits) | Phi+ | 1 | 1 | 0.00e+00 | 8.66e-15 | pass | LAPACK eig + h(x) | 0.00e+00 | 0.00e+00 |
| concurrence | product \|0+> | 0 | 0 | 0.00e+00 | 0.00e+00 | pass | LAPACK eig + sqrt | 0.00e+00 | 0.00e+00 |
| entropy of rho_A (bits) | product \|0+> | 3.20342650381492e-16 | 8.85070426512343e-16 | 5.65e-16 | 4.87e-13 | pass | LAPACK eig + h(x) | 3.20e-16 | 8.85e-16 |
| concurrence | cos t\|00>+sin t\|11>, t=0.1 | 0.198669330795061 | 0.198669330795061 | 0.00e+00 | 9.26e-07 | pass | LAPACK eig + sqrt | 9.94e-18 | 9.94e-18 |
| entropy of rho_A (bits) | cos t\|00>+sin t\|11>, t=0.1 | 0.0805723709370555 | 0.0805723709370555 | 0.00e+00 | 1.17e-13 | pass | LAPACK eig + h(x) | 1.63e-16 | 1.63e-16 |
| concurrence | cos t\|00>+sin t\|11>, t=0.4 | 0.717356085595696 | 0.717356085595696 | 0.00e+00 | 8.59e-07 | pass | LAPACK eig + sqrt | 5.30e-09 | 5.30e-09 |
| entropy of rho_A (bits) | cos t\|00>+sin t\|11>, t=0.4 | 0.613945740849939 | 0.613945740849939 | 0.00e+00 | 3.80e-14 | pass | LAPACK eig + h(x) | 1.15e-16 | 1.15e-16 |
| concurrence | cos t\|00>+sin t\|11>, t=0.0001 | 0.000199999997979647 | 0.000199999997979647 | 0.00e+00 | 9.31e-07 | pass | LAPACK eig + sqrt | 6.87e-13 | 6.87e-13 |
| entropy of rho_A (bits) | cos t\|00>+sin t\|11>, t=0.0001 | 2.80181197002307e-07 | 2.80181197002307e-07 | 0.00e+00 | 4.72e-13 | pass | LAPACK eig + h(x) | 3.96e-17 | 3.96e-17 |
| concurrence | Werner p=0.2 | 0 | 0 | 0.00e+00 | 4.82e-14 | pass | LAPACK eig + sqrt | 0.00e+00 | 0.00e+00 |
| entropy of rho_A (bits) | Werner p=0.2 | 1 | 1 | 0.00e+00 | 8.88e-15 | pass | LAPACK eig + h(x) | 0.00e+00 | 0.00e+00 |
| concurrence | Werner p=0.3333 | 0 | 0 | 0.00e+00 | 8.35e-14 | pass | LAPACK eig + sqrt | 0.00e+00 | 0.00e+00 |
| entropy of rho_A (bits) | Werner p=0.3333 | 1 | 1 | 0.00e+00 | 8.88e-15 | pass | LAPACK eig + h(x) | 0.00e+00 | 0.00e+00 |
| concurrence | Werner p=0.5 | 0.25 | 0.25 | 1.67e-16 | 1.71e-13 | pass | LAPACK eig + sqrt | 5.55e-17 | 1.11e-16 |
| entropy of rho_A (bits) | Werner p=0.5 | 1 | 1 | 0.00e+00 | 8.66e-15 | pass | LAPACK eig + h(x) | 0.00e+00 | 0.00e+00 |
| concurrence | Werner p=0.9 | 0.849999999999998 | 0.849999999999999 | 4.44e-16 | 1.86e-12 | pass | LAPACK eig + sqrt | 1.61e-15 | 1.17e-15 |
| entropy of rho_A (bits) | Werner p=0.9 | 1 | 1 | 0.00e+00 | 8.66e-15 | pass | LAPACK eig + h(x) | 0.00e+00 | 0.00e+00 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=0.3; n=z | 0 | 0 | 0.00e+00 | 1.07e-14 | pass | expm/gates | 4.56e-17 | 4.56e-17 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=0.3; n=x | 9.15044653021757e-18 | 0 | 9.15e-18 | 1.07e-14 | pass | expm/gates | 4.56e-17 | 4.65e-17 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=0.3; n=y | 9.15044653021757e-18 | 0 | 9.15e-18 | 1.07e-14 | pass | expm/gates | 4.56e-17 | 4.65e-17 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=0.3; n=oblique | 1.77722398948334e-16 | 0 | 1.78e-16 | 1.79e-14 | pass | expm/gates | 5.52e-17 | 1.56e-16 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=0.3; n=near -z | 1.14439169963056e-16 | 0 | 1.14e-16 | 1.79e-14 | pass | expm/gates | 5.64e-17 | 1.57e-16 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=2; n=z | 0 | 0 | 0.00e+00 | 1.18e-14 | pass | expm/gates | 4.76e-17 | 4.76e-17 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=2; n=x | 1.22396085451394e-16 | 0 | 1.22e-16 | 1.18e-14 | pass | expm/gates | 1.09e-16 | 7.02e-17 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=2; n=y | 1.22396085451394e-16 | 0 | 1.22e-16 | 1.18e-14 | pass | expm/gates | 1.09e-16 | 7.02e-17 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=2; n=oblique | 2.22044604925031e-16 | 0 | 2.22e-16 | 1.93e-14 | pass | expm/gates | 1.52e-16 | 1.62e-16 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=2; n=near -z | 2.22044604925031e-16 | 0 | 2.22e-16 | 1.93e-14 | pass | expm/gates | 1.35e-16 | 1.07e-16 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=3.14159; n=z | 0 | 0 | 0.00e+00 | 1.24e-14 | pass | expm/gates | 2.40e-33 | 2.40e-33 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=3.14159; n=x | 8.65956056235493e-17 | 0 | 8.66e-17 | 1.24e-14 | pass | expm/gates | 6.12e-17 | 6.12e-17 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=3.14159; n=y | 8.65956056235493e-17 | 0 | 8.66e-17 | 1.24e-14 | pass | expm/gates | 6.12e-17 | 6.12e-17 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=3.14159; n=oblique | 1.24126707662364e-16 | 0 | 1.24e-16 | 2.03e-14 | pass | expm/gates | 9.37e-17 | 8.06e-17 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=3.14159; n=near -z | 1.38777878078145e-16 | 0 | 1.39e-16 | 2.03e-14 | pass | expm/gates | 1.83e-16 | 7.33e-17 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=10; n=z | 0 | 0 | 0.00e+00 | 1.66e-14 | pass | expm/gates | 2.35e-17 | 2.35e-17 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=10; n=x | 2.29676976365171e-16 | 0 | 2.30e-16 | 1.66e-14 | pass | expm/gates | 2.40e-16 | 6.15e-17 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=10; n=y | 2.29676976365171e-16 | 0 | 2.30e-16 | 1.66e-14 | pass | expm/gates | 2.40e-16 | 6.15e-17 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=10; n=oblique | 7.0216669371534e-16 | 0 | 7.02e-16 | 3.54e-14 | pass | expm/gates | 7.40e-16 | 1.23e-16 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=10; n=near -z | 6.86635019778336e-16 | 0 | 6.87e-16 | 3.54e-14 | pass | expm/gates | 5.84e-16 | 1.16e-16 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=1000; n=z | 0 | 0 | 0.00e+00 | 1.82e-12 | pass | expm/gates | 5.11e-17 | 5.11e-17 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=1000; n=x | 2.27595720048157e-15 | 0 | 2.28e-15 | 1.82e-12 | pass | expm/gates | 2.26e-15 | 5.65e-17 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=1000; n=y | 1.55457612552944e-15 | 0 | 1.55e-15 | 1.82e-12 | pass | expm/gates | 1.60e-15 | 5.65e-17 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=1000; n=oblique | 3.29338355245821e-14 | 0 | 3.29e-14 | 3.25e-12 | pass | expm/gates | 3.29e-14 | 1.08e-16 |
| U = exp(-i w t n.sigma/2) max\|entry diff\| | w t=1000; n=near -z | 4.809601597309e-14 | 0 | 4.81e-14 | 2.05e-12 | pass | expm/gates | 4.81e-14 | 1.69e-16 |

## QuTiP (open systems) (`test_ext_open_qutip.py`)

| quantity | inputs | engine | library | diff | tol | status | basis | eng err | lib err |
|---|---|---|---|---|---|---|---|---|---|
| Liouvillian max\|entry diff\| | OBE Omega=1.3 Delta=0.7 T1=2 T2=1.5 | 1.11022302462516e-16 | 0 | 1.11e-16 | 1.18e-14 | pass | superop rounding | 1.11e-16 | 0.00e+00 |
| Liouvillian max\|entry diff\| | OBE Omega=5 Delta=-2 T2=2T1 | 0 | 0 | 0.00e+00 | 1.89e-14 | pass | superop rounding | 0.00e+00 | 0.00e+00 |
| Liouvillian max\|entry diff\| | Lambda O1=1.1 O2=0.7 Delta=0.4 | 0 | 0 | 0.00e+00 | 1.28e-14 | pass | superop rounding | 0.00e+00 | 0.00e+00 |
| Liouvillian max\|entry diff\| | oscillator N=4 driven, nth=0.3 | 2.22044604925031e-16 | 0 | 2.22e-16 | 4.77e-14 | pass | superop rounding | 2.22e-16 | 2.22e-16 |
| Liouvillian max\|entry diff\| | two qubits, collective decay | 2.22044604925031e-16 | 0 | 2.22e-16 | 1.20e-14 | pass | superop rounding | 1.11e-16 | 2.22e-16 |
| rho(t) max\|entry diff\| (constant L) | OBE Omega=1.3 Delta=0.7 T1=2 T2=1.5; t=0 | 1.1148909509417e-16 | 0 | 1.11e-16 | 8.23e-14 | pass | expm + diag a posteriori | 0.00e+00 | 1.11e-16 |
| rho(t) max\|entry diff\| (constant L) | OBE Omega=1.3 Delta=0.7 T1=2 T2=1.5; t=0.5 | 3.20168114105716e-16 | 0 | 3.20e-16 | 1.05e-13 | pass | expm + diag a posteriori | 1.39e-17 | 3.20e-16 |
| rho(t) max\|entry diff\| (constant L) | OBE Omega=1.3 Delta=0.7 T1=2 T2=1.5; t=2 | 6.19576312663508e-16 | 0 | 6.20e-16 | 1.73e-13 | pass | expm + diag a posteriori | 1.24e-16 | 6.05e-16 |
| rho(t) max\|entry diff\| (constant L) | OBE Omega=1.3 Delta=0.7 T1=2 T2=1.5; t=6 | 4.22510959593162e-16 | 0 | 4.23e-16 | 5.96e-13 | pass | expm + diag a posteriori | 1.70e-16 | 5.53e-16 |
| rho(t) max\|entry diff\| (constant L) | OBE Omega=5 Delta=-2 T2=2T1; t=0 | 4.44305997370834e-16 | 0 | 4.44e-16 | 8.34e-14 | pass | expm + diag a posteriori | 0.00e+00 | 4.44e-16 |
| rho(t) max\|entry diff\| (constant L) | OBE Omega=5 Delta=-2 T2=2T1; t=0.5 | 9.57064408256085e-16 | 0 | 9.57e-16 | 1.37e-13 | pass | expm + diag a posteriori | 1.67e-16 | 8.78e-16 |
| rho(t) max\|entry diff\| (constant L) | OBE Omega=5 Delta=-2 T2=2T1; t=2 | 1.1866928732136e-15 | 0 | 1.19e-15 | 5.36e-13 | pass | expm + diag a posteriori | 1.11e-16 | 1.13e-15 |
| rho(t) max\|entry diff\| (constant L) | OBE Omega=5 Delta=-2 T2=2T1; t=6 | 5.58419063729596e-16 | 0 | 5.58e-16 | 1.28e-12 | pass | expm + diag a posteriori | 3.97e-16 | 5.54e-16 |
| rho(t) max\|entry diff\| (constant L) | Lambda O1=1.1 O2=0.7 Delta=0.4; t=0 | 2.83626622906298e-16 | 0 | 2.84e-16 | 3.69e-13 | pass | expm + diag a posteriori | 0.00e+00 | 2.84e-16 |
| rho(t) max\|entry diff\| (constant L) | Lambda O1=1.1 O2=0.7 Delta=0.4; t=0.5 | 4.71966742449081e-16 | 0 | 4.72e-16 | 4.26e-13 | pass | expm + diag a posteriori | 5.55e-17 | 4.79e-16 |
| rho(t) max\|entry diff\| (constant L) | Lambda O1=1.1 O2=0.7 Delta=0.4; t=2 | 9.47355980655874e-16 | 0 | 9.47e-16 | 9.52e-13 | pass | expm + diag a posteriori | 1.12e-16 | 1.00e-15 |
| rho(t) max\|entry diff\| (constant L) | Lambda O1=1.1 O2=0.7 Delta=0.4; t=6 | 7.44616791464118e-16 | 0 | 7.45e-16 | 3.55e-12 | pass | expm + diag a posteriori | 1.11e-16 | 7.41e-16 |
| rho(t) max\|entry diff\| (constant L) | oscillator N=4 driven, nth=0.3; t=0 | 9.72838122060418e-17 | 0 | 9.73e-17 | 1.09e-12 | pass | expm + diag a posteriori | 0.00e+00 | 9.73e-17 |
| rho(t) max\|entry diff\| (constant L) | oscillator N=4 driven, nth=0.3; t=0.5 | 7.17840228520914e-16 | 0 | 7.18e-16 | 1.43e-12 | pass | expm + diag a posteriori | 1.43e-17 | 7.29e-16 |
| rho(t) max\|entry diff\| (constant L) | oscillator N=4 driven, nth=0.3; t=2 | 1.53937136636162e-15 | 0 | 1.54e-15 | 5.70e-12 | pass | expm + diag a posteriori | 5.57e-17 | 1.59e-15 |
| rho(t) max\|entry diff\| (constant L) | oscillator N=4 driven, nth=0.3; t=6 | 1.37315137874598e-15 | 0 | 1.37e-15 | 1.27e-11 | pass | expm + diag a posteriori | 3.39e-16 | 1.65e-15 |
| rho(t) max\|entry diff\| (constant L) | two qubits, collective decay; t=0 | 1.94567624412084e-16 | 0 | 1.95e-16 | 1.11e-12 | pass | expm + diag a posteriori | 0.00e+00 | 1.95e-16 |
| rho(t) max\|entry diff\| (constant L) | two qubits, collective decay; t=0.5 | 3.5108334685767e-16 | 0 | 3.51e-16 | 1.25e-12 | pass | expm + diag a posteriori | 1.11e-16 | 3.47e-16 |
| rho(t) max\|entry diff\| (constant L) | two qubits, collective decay; t=2 | 3.70065643813413e-16 | 0 | 3.70e-16 | 2.78e-12 | pass | expm + diag a posteriori | 1.72e-16 | 3.96e-16 |
| rho(t) max\|entry diff\| (constant L) | two qubits, collective decay; t=6 | 7.44259855094618e-16 | 0 | 7.44e-16 | 6.13e-12 | pass | expm + diag a posteriori | 2.35e-16 | 6.13e-16 |
| rho(t) max\|entry diff\| (lab-frame circular drive) | w0=8 w=7.2 Omega=1.5 T1=2 T2=1; t=0 | 0 | 0 | 0.00e+00 | 1.99e-09 | pass | engine estimate + Verner control | 0.00e+00 | 0.00e+00 |
| rho(t) max\|entry diff\| (lab-frame circular drive) | w0=8 w=7.2 Omega=1.5 T1=2 T2=1; t=1 | 2.65455726258152e-12 | 0 | 2.65e-12 | 2.00e-09 | pass | engine estimate + Verner control | 2.70e-12 | 6.08e-14 |
| rho(t) max\|entry diff\| (lab-frame circular drive) | w0=8 w=7.2 Omega=1.5 T1=2 T2=1; t=2 | 3.92803719084137e-12 | 0 | 3.93e-12 | 2.01e-09 | pass | engine estimate + Verner control | 4.01e-12 | 8.50e-14 |
| rho(t) max\|entry diff\| (lab-frame circular drive) | w0=8 w=7.2 Omega=1.5 T1=2 T2=1; t=3 | 3.8863584129719e-12 | 0 | 3.89e-12 | 2.02e-09 | pass | engine estimate + Verner control | 3.93e-12 | 4.82e-14 |
| rho(t) max\|entry diff\| (lab-frame circular drive) | w0=8 w=7.2 Omega=1.5 T1=2 T2=1; t=4 | 3.14440397643669e-12 | 0 | 3.14e-12 | 2.03e-09 | pass | engine estimate + Verner control | 3.21e-12 | 6.34e-14 |
| rho(t) max\|entry diff\| (lab-frame circular drive) | w0=8 w=7.2 Omega=1.5 T1=2 T2=1; t=5 | 3.75306355345313e-12 | 0 | 3.75e-12 | 2.05e-09 | pass | engine estimate + Verner control | 3.83e-12 | 7.99e-14 |
| rho(t) max\|entry diff\| (lab-frame circular drive) | w0=8 w=7.2 Omega=1.5 T1=2 T2=1; t=6 | 3.78023459428494e-12 | 0 | 3.78e-12 | 2.06e-09 | pass | engine estimate + Verner control | 3.86e-12 | 7.53e-14 |
| steady state max\|entry diff\| | OBE Omega=1.3 Delta=0.7 T1=2 T2=1.5 | 1.11022302462516e-16 | 0 | 1.11e-16 | 8.18e-14 | pass | Wedin + LU | 1.14e-16 | 6.21e-17 |
| steady state max\|entry diff\| | OBE Omega=5 Delta=-2 T1=1 T2=2 | 3.89568068015994e-16 | 0 | 3.90e-16 | 2.22e-13 | pass | Wedin + LU | 5.00e-16 | 1.11e-16 |
| steady state max\|entry diff\| | OBE Omega=0.2 Delta=0 T1=1 T2=2 | 1.11022302462516e-16 | 0 | 1.11e-16 | 7.86e-14 | pass | Wedin + LU | 1.11e-16 | 2.78e-17 |
| steady state max\|entry diff\| | Lambda dark state O1=1.1 O2=0.7 | 6.66133814775094e-16 | 0 | 6.66e-16 | 4.66e-13 | pass | Wedin + LU | 5.55e-16 | 1.11e-16 |
| steady state max\|entry diff\| | thermal oscillator N=5 nth=0.4 | 2.22044604925031e-16 | 0 | 2.22e-16 | 2.42e-12 | pass | Wedin + LU | 1.11e-16 | 1.11e-16 |
| trajectory mean <P_e> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=0 | 0 | 0 | 0.00e+00 | 1.81e-03 | pass | MC z = 5 | 0.00e+00 | 0.00e+00 |
| trajectory mean <P_e> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=0.5 | 0.169155512370185 | 0.168895133048108 | 2.60e-04 | 7.62e-03 | pass | MC z = 5 | 6.83e-05 | 1.92e-04 |
| trajectory mean <P_e> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=1 | 0.392407369919839 | 0.393826785117493 | 1.42e-03 | 2.62e-02 | pass | MC z = 5 | 5.99e-04 | 8.20e-04 |
| trajectory mean <P_e> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=1.5 | 0.453535659163454 | 0.462013040355716 | 8.48e-03 | 3.95e-02 | pass | MC z = 5 | 4.55e-03 | 3.92e-03 |
| trajectory mean <P_e> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=2 | 0.401693153125056 | 0.402547428618464 | 8.54e-04 | 3.32e-02 | pass | MC z = 5 | 3.99e-03 | 3.13e-03 |
| trajectory mean <P_e> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=2.5 | 0.353058386685226 | 0.346982232526513 | 6.08e-03 | 3.14e-02 | pass | MC z = 5 | 6.10e-03 | 2.65e-05 |
| trajectory mean <P_e> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=3 | 0.337609309537383 | 0.33546981256271 | 2.14e-03 | 3.73e-02 | pass | MC z = 5 | 5.41e-03 | 3.27e-03 |
| trajectory mean <P_e> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=3.5 | 0.34884705913317 | 0.346906353338162 | 1.94e-03 | 3.46e-02 | pass | MC z = 5 | 2.12e-03 | 1.81e-04 |
| trajectory mean <P_e> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=4 | 0.359692517237883 | 0.364398405190412 | 4.71e-03 | 3.34e-02 | pass | MC z = 5 | 1.57e-03 | 3.14e-03 |
| trajectory mean <P_e> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=4.5 | 0.359206570635269 | 0.36497002190305 | 5.76e-03 | 3.44e-02 | pass | MC z = 5 | 4.82e-03 | 9.44e-04 |
| trajectory mean <P_e> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=5 | 0.359192562075066 | 0.355169038467297 | 4.02e-03 | 3.33e-02 | pass | MC z = 5 | 5.39e-04 | 4.56e-03 |
| trajectory mean <P_e> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=5.5 | 0.360908776509074 | 0.348374659358764 | 1.25e-02 | 3.34e-02 | pass | MC z = 5 | 4.95e-03 | 7.59e-03 |
| trajectory mean <P_e> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=6 | 0.346373315449688 | 0.352563690872201 | 6.19e-03 | 3.39e-02 | pass | MC z = 5 | 9.01e-03 | 2.82e-03 |
| trajectory mean <P_e> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=6.5 | 0.348949148635968 | 0.352634350108283 | 3.69e-03 | 3.39e-02 | pass | MC z = 5 | 7.59e-03 | 3.90e-03 |
| trajectory mean <P_e> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=7 | 0.361188443352442 | 0.354588370980637 | 6.60e-03 | 3.40e-02 | pass | MC z = 5 | 3.74e-03 | 2.86e-03 |
| trajectory mean <P_e> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=7.5 | 0.356914278382258 | 0.354522907453309 | 2.39e-03 | 3.39e-02 | pass | MC z = 5 | 6.10e-04 | 3.00e-03 |
| trajectory mean <P_e> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=8 | 0.352202205179401 | 0.3582365347567 | 6.03e-03 | 3.34e-02 | pass | MC z = 5 | 4.99e-03 | 1.04e-03 |
| trajectory mean <sigma_x> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=0 | 0 | 0 | 0.00e+00 | 1.81e-03 | pass | MC z = 5 | 0.00e+00 | 0.00e+00 |
| trajectory mean <sigma_x> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=0.5 | 0.139611977015507 | 0.139163077243052 | 4.49e-04 | 1.01e-02 | pass | MC z = 5 | 5.62e-04 | 1.13e-04 |
| trajectory mean <sigma_x> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=1 | 0.336573390878689 | 0.335498871333682 | 1.07e-03 | 3.54e-02 | pass | MC z = 5 | 3.42e-03 | 2.35e-03 |
| trajectory mean <sigma_x> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=1.5 | 0.398123271364948 | 0.410492891547204 | 1.24e-02 | 5.98e-02 | pass | MC z = 5 | 4.80e-03 | 7.57e-03 |
| trajectory mean <sigma_x> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=2 | 0.371189067911772 | 0.383037218663686 | 1.18e-02 | 6.38e-02 | pass | MC z = 5 | 1.09e-03 | 1.08e-02 |
| trajectory mean <sigma_x> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=2.5 | 0.341840636854779 | 0.332682294114828 | 9.16e-03 | 5.66e-02 | pass | MC z = 5 | 1.26e-02 | 3.40e-03 |
| trajectory mean <sigma_x> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=3 | 0.318096295740199 | 0.320681658406708 | 2.59e-03 | 5.52e-02 | pass | MC z = 5 | 4.57e-05 | 2.54e-03 |
| trajectory mean <sigma_x> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=3.5 | 0.322523941217804 | 0.339556504584141 | 1.70e-02 | 5.54e-02 | pass | MC z = 5 | 7.87e-03 | 9.17e-03 |
| trajectory mean <sigma_x> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=4 | 0.341600225092205 | 0.353254564802821 | 1.17e-02 | 5.77e-02 | pass | MC z = 5 | 1.73e-03 | 9.93e-03 |
| trajectory mean <sigma_x> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=4.5 | 0.341588514850246 | 0.363169257403235 | 2.16e-02 | 6.04e-02 | pass | MC z = 5 | 5.27e-03 | 1.63e-02 |
| trajectory mean <sigma_x> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=5 | 0.346239225538612 | 0.342866844038637 | 3.37e-03 | 6.10e-02 | pass | MC z = 5 | 2.04e-03 | 1.33e-03 |
| trajectory mean <sigma_x> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=5.5 | 0.35744629481026 | 0.330648649030731 | 2.68e-02 | 5.99e-02 | pass | MC z = 5 | 1.60e-02 | 1.08e-02 |
| trajectory mean <sigma_x> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=6 | 0.334469885701357 | 0.33235788776679 | 2.11e-03 | 6.02e-02 | pass | MC z = 5 | 6.58e-03 | 8.69e-03 |
| trajectory mean <sigma_x> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=6.5 | 0.346978277310294 | 0.330196548307283 | 1.68e-02 | 5.91e-02 | pass | MC z = 5 | 4.94e-03 | 1.18e-02 |
| trajectory mean <sigma_x> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=7 | 0.349896484850542 | 0.336245601081513 | 1.37e-02 | 5.93e-02 | pass | MC z = 5 | 7.01e-03 | 6.64e-03 |
| trajectory mean <sigma_x> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=7.5 | 0.339472998365789 | 0.342884949581163 | 3.41e-03 | 6.00e-02 | pass | MC z = 5 | 3.57e-03 | 1.55e-04 |
| trajectory mean <sigma_x> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=8 | 0.339933098459522 | 0.356284310251689 | 1.64e-02 | 5.99e-02 | pass | MC z = 5 | 2.90e-03 | 1.35e-02 |
| trajectory mean <sigma_y> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=0 | 0 | 0 | 0.00e+00 | 1.81e-03 | pass | MC z = 5 | 0.00e+00 | 0.00e+00 |
| trajectory mean <sigma_y> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=0.5 | 0.687892825105326 | 0.687616372104492 | 2.76e-04 | 3.27e-02 | pass | MC z = 5 | 1.99e-03 | 1.71e-03 |
| trajectory mean <sigma_y> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=1 | 0.709122935695051 | 0.702109779166215 | 7.01e-03 | 4.88e-02 | pass | MC z = 5 | 8.31e-03 | 1.30e-03 |
| trajectory mean <sigma_y> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=1.5 | 0.428774419176786 | 0.43123108197448 | 2.46e-03 | 4.29e-02 | pass | MC z = 5 | 3.35e-03 | 8.94e-04 |
| trajectory mean <sigma_y> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=2 | 0.273689968906828 | 0.255963388695796 | 1.77e-02 | 7.04e-02 | pass | MC z = 5 | 1.00e-02 | 7.70e-03 |
| trajectory mean <sigma_y> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=2.5 | 0.278059685310191 | 0.271590078397414 | 6.47e-03 | 7.60e-02 | pass | MC z = 5 | 7.57e-03 | 1.10e-03 |
| trajectory mean <sigma_y> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=3 | 0.332861364570239 | 0.341940685613362 | 9.08e-03 | 6.00e-02 | pass | MC z = 5 | 9.82e-03 | 7.43e-04 |
| trajectory mean <sigma_y> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=3.5 | 0.376300791011516 | 0.373597624132021 | 2.70e-03 | 6.33e-02 | pass | MC z = 5 | 7.18e-03 | 9.88e-03 |
| trajectory mean <sigma_y> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=4 | 0.367745849645797 | 0.375853792694924 | 8.11e-03 | 6.47e-02 | pass | MC z = 5 | 1.11e-02 | 3.03e-03 |
| trajectory mean <sigma_y> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=4.5 | 0.35391046677506 | 0.345370213681501 | 8.54e-03 | 6.19e-02 | pass | MC z = 5 | 5.68e-03 | 1.42e-02 |
| trajectory mean <sigma_y> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=5 | 0.360159862406117 | 0.343991033137543 | 1.62e-02 | 6.34e-02 | pass | MC z = 5 | 1.04e-02 | 5.79e-03 |
| trajectory mean <sigma_y> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=5.5 | 0.351374016764871 | 0.359157436915896 | 7.78e-03 | 6.36e-02 | pass | MC z = 5 | 2.82e-04 | 7.50e-03 |
| trajectory mean <sigma_y> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=6 | 0.349778964473766 | 0.358660255537397 | 8.88e-03 | 6.26e-02 | pass | MC z = 5 | 6.97e-03 | 1.91e-03 |
| trajectory mean <sigma_y> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=6.5 | 0.365354125424555 | 0.35779019288567 | 7.56e-03 | 6.27e-02 | pass | MC z = 5 | 6.29e-03 | 1.27e-03 |
| trajectory mean <sigma_y> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=7 | 0.3679615304641 | 0.365643028696145 | 2.32e-03 | 6.24e-02 | pass | MC z = 5 | 9.56e-03 | 7.25e-03 |
| trajectory mean <sigma_y> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=7.5 | 0.349185209647054 | 0.36391359595082 | 1.47e-02 | 6.27e-02 | pass | MC z = 5 | 7.87e-03 | 6.85e-03 |
| trajectory mean <sigma_y> | Omega=2 Delta=0.8 T1=1 T2=1.2; N=3000; t=8 | 0.357101536170642 | 0.367201665624757 | 1.01e-02 | 6.26e-02 | pass | MC z = 5 | 5.83e-04 | 1.07e-02 |
| waiting-time CDF sup\|F_engine - F_qutip\| | Omega=1 Delta=0 Gamma=1; N=4000 | 0.01525 | 0 | 1.52e-02 | 8.52e-02 | pass | DKW two-sample | 1.84e-02 | 1.64e-02 |
| waiting-time CDF sup\|F_engine - F_qutip\| | Omega=3 Delta=1 Gamma=1; N=4000 | 0.0132500000000001 | 0 | 1.33e-02 | 8.52e-02 | pass | DKW two-sample | 1.46e-02 | 1.56e-02 |
| waiting-time CDF sup\|F_engine - F_qutip\| | Omega=0.5 Delta=0 Gamma=1; exceptional point; N=4000 | 0.013 | 0 | 1.30e-02 | 8.52e-02 | pass | DKW two-sample | 1.33e-02 | 8.75e-03 |

## Astropy (`test_ext_constants_astropy.py`)

| quantity | inputs | engine | library | diff | tol | status | basis | eng err | lib err |
|---|---|---|---|---|---|---|---|---|---|
| constants.C | SI | 299792458 | 299792458 | 0.00e+00 | 0.00e+00 | pass | same decimal |  |  |
| constants.G | SI | 6.6743e-11 | 6.6743e-11 | 0.00e+00 | 0.00e+00 | pass | same decimal |  |  |
| constants.AU | SI | 149597870700 | 149597870700 | 0.00e+00 | 0.00e+00 | pass | same decimal |  |  |
| constants.DAY | SI | 86400 | 86400 | 0.00e+00 | 0.00e+00 | pass | same decimal |  |  |
| constants.YEAR_JULIAN | SI | 31557600 | 31557600 | 0.00e+00 | 0.00e+00 | pass | same decimal |  |  |
| constants.LIGHT_YEAR | SI | 9.4607304725808e+15 | 9.4607304725808e+15 | 0.00e+00 | 4.20e+00 | pass | 2 roundings |  |  |
| constants.GM_SUN | SI | 1.3271244e+20 | 1.3271244e+20 | 0.00e+00 | 0.00e+00 | pass | same decimal |  |  |
| constants.R_SUN | SI | 695700000 | 695700000 | 0.00e+00 | 0.00e+00 | pass | same decimal |  |  |
| constants.GM_EARTH | SI | 398600400000000 | 398600400000000 | 0.00e+00 | 0.00e+00 | pass | same decimal |  |  |
| constants.R_EARTH | SI | 6378100 | 6378100 | 0.00e+00 | 0.00e+00 | pass | same decimal |  |  |
| constants.M_SUN = GM_SUN/G | SI | 1.98840987069805e+30 | 1.98840987069805e+30 | 0.00e+00 | 4.42e+14 | pass | 1 roundings |  |  |
| particles.H | SI | 6.62607015e-34 | 6.62607015e-34 | 0.00e+00 | 0.00e+00 | pass | same decimal |  |  |
| particles.HBAR = h/(2 pi) | SI | 1.05457181764616e-34 | 1.05457181764616e-34 | 0.00e+00 | 2.34e-50 | pass | 1 roundings |  |  |
| particles.C | SI | 299792458 | 299792458 | 0.00e+00 | 0.00e+00 | pass | same decimal |  |  |
| particles.E_CHARGE | SI | 1.602176634e-19 | 1.602176634e-19 | 0.00e+00 | 0.00e+00 | pass | same decimal |  |  |
| particles.EV | SI | 1.602176634e-19 | 1.602176634e-19 | 0.00e+00 | 0.00e+00 | pass | same decimal |  |  |
| particles.U (atomic mass constant) | SI | 1.66053906892e-27 | 1.66053906892e-27 | 0.00e+00 | 0.00e+00 | pass | same decimal |  |  |
| particles: m_e | SI | 9.1093837139e-31 | 9.1093837139e-31 | 0.00e+00 | 0.00e+00 | pass | same decimal |  |  |
| particles: m_n | SI | 1.67492750056e-27 | 1.67492750056e-27 | 0.00e+00 | 0.00e+00 | pass | same decimal |  |  |
| hydrogen: m_p (default nucleus) | SI | 1.67262192595e-27 | 1.67262192595e-27 | 0.00e+00 | 0.00e+00 | pass | same decimal |  |  |
| hydrogen.ALPHA | SI | 0.0072973525643 | 0.0072973525643 | 0.00e+00 | 0.00e+00 | pass | same decimal |  |  |
| hydrogen.ME_C2 = m_e c^2 | SI | 8.18710578796845e-14 | 8.18710578796845e-14 | 0.00e+00 | 3.64e-29 | pass | 2 roundings |  |  |
| compton.LAMBDA_C = h/(m_e c) | SI | 2.42631023538032e-12 | 2.42631023538032e-12 | 0.00e+00 | 1.08e-27 | pass | 2 roundings |  |  |
| radiation.H | SI | 6.62607015e-34 | 6.62607015e-34 | 0.00e+00 | 0.00e+00 | pass | same decimal |  |  |
| radiation.K (Boltzmann) | SI | 1.380649e-23 | 1.380649e-23 | 0.00e+00 | 0.00e+00 | pass | same decimal |  |  |

## Astropy (FLRW cosmology) (`test_ext_flrw_astropy.py`)

| quantity | inputs | engine | library | diff | tol | status | basis | eng err | lib err |
|---|---|---|---|---|---|---|---|---|---|
| flat LCDM, no radiation: D_C [Mpc] | z=0.001 | 4.28178557284689 | 4.28178557284571 | 1.18e-12 | 2.01e-10 | pass | engine bound + closed form 64u | 0.00e+00 | 1.18e-12 |
| flat LCDM, no radiation: D_M [Mpc] | z=0.001 | 4.28178557284689 | 4.28178557284571 | 1.18e-12 | 2.01e-10 | pass | propagated + closed form 64u | 0.00e+00 | 1.18e-12 |
| flat LCDM, no radiation: D_A [Mpc] | z=0.001 | 4.27750806478211 | 4.27750806478093 | 1.18e-12 | 2.01e-10 | pass | propagated + closed form 64u | 8.88e-16 | 1.18e-12 |
| flat LCDM, no radiation: D_L [Mpc] | z=0.001 | 4.28606735841974 | 4.28606735841856 | 1.18e-12 | 2.01e-10 | pass | propagated + closed form 64u | 0.00e+00 | 1.18e-12 |
| flat LCDM, no radiation: distance modulus | z=0.001 | 28.1602949599408 | 28.1602949599402 | 6.00e-13 | 1.02e-10 | pass | propagated + closed form 64u | 0.00e+00 | 6.00e-13 |
| flat LCDM, no radiation: lookback time [Gyr] | z=0.001 | 0.0139583392427133 | 0.0139583392427127 | 5.79e-16 | 1.91e-13 | pass | engine bound + closed form 64u | 1.73e-18 | 5.81e-16 |
| flat LCDM, no radiation: age [Gyr] | z=0.001 | 13.4530256078192 | 13.4530256078192 | 5.33e-15 | 1.43e-11 | pass | engine bound + closed form 64u | 1.78e-15 | 3.55e-15 |
| flat LCDM, no radiation: H [km/s/Mpc] | z=0.001 | 70.0315244120103 | 70.0315244120103 | 0.00e+00 | 2.49e-13 | pass | 16u x conditioning per side | 1.42e-14 | 1.42e-14 |
| flat LCDM, no radiation: Omega_m(z) | z=0.001 | 0.300630062586427 | 0.300630062586427 | 5.55e-17 | 1.07e-15 | pass | 16u x conditioning per side | 1.11e-16 | 5.55e-17 |
| flat LCDM, no radiation: Omega_de(z) | z=0.001 | 0.699369937413573 | 0.699369937413573 | 0.00e+00 | 4.97e-15 | pass | 16u x conditioning per side | 1.11e-16 | 1.11e-16 |
| flat LCDM, no radiation: rho_crit(z) [kg/m^3] | z=0.001 | 9.21216569575089e-27 | 9.21216569575088e-27 | 4.30e-42 | 4.91e-41 | pass | 16u x conditioning per side | 1.43e-42 | 5.74e-42 |
| flat LCDM, no radiation: D_C [Mpc] | z=0.1 | 418.454487627707 | 418.454487627702 | 5.51e-12 | 2.00e-10 | pass | engine bound + closed form 64u | 0.00e+00 | 5.51e-12 |
| flat LCDM, no radiation: D_M [Mpc] | z=0.1 | 418.454487627707 | 418.454487627702 | 5.51e-12 | 2.00e-10 | pass | propagated + closed form 64u | 0.00e+00 | 5.51e-12 |
| flat LCDM, no radiation: D_A [Mpc] | z=0.1 | 380.413170570643 | 380.413170570638 | 5.06e-12 | 1.82e-10 | pass | propagated + closed form 64u | 0.00e+00 | 5.06e-12 |
| flat LCDM, no radiation: D_L [Mpc] | z=0.1 | 460.299936390478 | 460.299936390472 | 6.08e-12 | 2.21e-10 | pass | propagated + closed form 64u | 0.00e+00 | 6.08e-12 |
| flat LCDM, no radiation: distance modulus | z=0.1 | 38.3152045743909 | 38.3152045743909 | 2.84e-14 | 1.08e-12 | pass | propagated + closed form 64u | 0.00e+00 | 2.84e-14 |
| flat LCDM, no radiation: lookback time [Gyr] | z=0.1 | 1.30129755754484 | 1.30129755754484 | 1.33e-15 | 1.88e-13 | pass | engine bound + closed form 64u | 2.22e-16 | 1.11e-15 |
| flat LCDM, no radiation: age [Gyr] | z=0.1 | 12.165686389517 | 12.165686389517 | 5.33e-15 | 1.34e-11 | pass | engine bound + closed form 64u | 0.00e+00 | 5.33e-15 |
| flat LCDM, no radiation: H [km/s/Mpc] | z=0.1 | 73.393255820954 | 73.393255820954 | 0.00e+00 | 2.61e-13 | pass | 16u x conditioning per side | 0.00e+00 | 0.00e+00 |
| flat LCDM, no radiation: Omega_m(z) | z=0.1 | 0.363231147093605 | 0.363231147093605 | 0.00e+00 | 1.29e-15 | pass | 16u x conditioning per side | 5.55e-17 | 5.55e-17 |
| flat LCDM, no radiation: Omega_de(z) | z=0.1 | 0.636768852906395 | 0.636768852906395 | 0.00e+00 | 4.52e-15 | pass | 16u x conditioning per side | 0.00e+00 | 0.00e+00 |
| flat LCDM, no radiation: rho_crit(z) [kg/m^3] | z=0.1 | 1.01178186035237e-26 | 1.01178186035237e-26 | 2.87e-42 | 5.39e-41 | pass | 16u x conditioning per side | 0.00e+00 | 2.87e-42 |
| flat LCDM, no radiation: D_C [Mpc] | z=0.5 | 1888.62539593341 | 1888.62539593342 | 1.11e-11 | 1.96e-10 | pass | engine bound + closed form 64u | 0.00e+00 | 1.11e-11 |
| flat LCDM, no radiation: D_M [Mpc] | z=0.5 | 1888.62539593341 | 1888.62539593342 | 1.11e-11 | 1.98e-10 | pass | propagated + closed form 64u | 0.00e+00 | 1.11e-11 |
| flat LCDM, no radiation: D_A [Mpc] | z=0.5 | 1259.08359728894 | 1259.08359728894 | 7.50e-12 | 1.33e-10 | pass | propagated + closed form 64u | 0.00e+00 | 7.50e-12 |
| flat LCDM, no radiation: D_L [Mpc] | z=0.5 | 2832.93809390011 | 2832.93809390013 | 1.68e-11 | 2.98e-10 | pass | propagated + closed form 64u | 4.55e-13 | 1.64e-11 |
| flat LCDM, no radiation: distance modulus | z=0.5 | 42.2611854215409 | 42.2611854215409 | 1.42e-14 | 2.67e-13 | pass | propagated + closed form 64u | 0.00e+00 | 1.42e-14 |
| flat LCDM, no radiation: lookback time [Gyr] | z=0.5 | 5.04063792931009 | 5.04063792931009 | 2.66e-15 | 1.78e-13 | pass | engine bound + closed form 64u | 1.78e-15 | 4.44e-15 |
| flat LCDM, no radiation: age [Gyr] | z=0.5 | 8.42634601775178 | 8.42634601775178 | 3.55e-15 | 8.98e-12 | pass | engine bound + closed form 64u | 3.55e-15 | 0.00e+00 |
| flat LCDM, no radiation: H [km/s/Mpc] | z=0.5 | 91.6037662981168 | 91.6037662981168 | 0.00e+00 | 3.25e-13 | pass | 16u x conditioning per side | 1.42e-14 | 1.42e-14 |
| flat LCDM, no radiation: Omega_m(z) | z=0.5 | 0.591240875912409 | 0.591240875912409 | 1.11e-16 | 2.10e-15 | pass | 16u x conditioning per side | 0.00e+00 | 1.11e-16 |
| flat LCDM, no radiation: Omega_de(z) | z=0.5 | 0.408759124087591 | 0.408759124087591 | 0.00e+00 | 2.90e-15 | pass | 16u x conditioning per side | 5.55e-17 | 5.55e-17 |
| flat LCDM, no radiation: rho_crit(z) [kg/m^3] | z=0.5 | 1.57616340930904e-26 | 1.57616340930904e-26 | 5.74e-42 | 8.40e-41 | pass | 16u x conditioning per side | 2.87e-42 | 2.87e-42 |
| flat LCDM, no radiation: D_C [Mpc] | z=1 | 3303.82880588747 | 3303.82880588747 | 0.00e+00 | 1.93e-10 | pass | engine bound + closed form 64u | 0.00e+00 | 0.00e+00 |
| flat LCDM, no radiation: D_M [Mpc] | z=1 | 3303.82880588747 | 3303.82880588747 | 0.00e+00 | 1.96e-10 | pass | propagated + closed form 64u | 0.00e+00 | 0.00e+00 |
| flat LCDM, no radiation: D_A [Mpc] | z=1 | 1651.91440294373 | 1651.91440294373 | 0.00e+00 | 9.85e-11 | pass | propagated + closed form 64u | 0.00e+00 | 0.00e+00 |
| flat LCDM, no radiation: D_L [Mpc] | z=1 | 6607.65761177494 | 6607.65761177494 | 0.00e+00 | 3.94e-10 | pass | propagated + closed form 64u | 0.00e+00 | 0.00e+00 |
| flat LCDM, no radiation: distance modulus | z=1 | 44.1002376555437 | 44.1002376555437 | 0.00e+00 | 1.70e-13 | pass | propagated + closed form 64u | 0.00e+00 | 0.00e+00 |
| flat LCDM, no radiation: lookback time [Gyr] | z=1 | 7.71533700361359 | 7.71533700361359 | 2.66e-15 | 1.70e-13 | pass | engine bound + closed form 64u | 0.00e+00 | 2.66e-15 |
| flat LCDM, no radiation: age [Gyr] | z=1 | 5.75164694344828 | 5.75164694344828 | 1.78e-15 | 6.12e-12 | pass | engine bound + closed form 64u | 8.88e-16 | 8.88e-16 |
| flat LCDM, no radiation: H [km/s/Mpc] | z=1 | 123.247718031613 | 123.247718031613 | 0.00e+00 | 4.38e-13 | pass | 16u x conditioning per side | 1.42e-14 | 1.42e-14 |
| flat LCDM, no radiation: Omega_m(z) | z=1 | 0.774193548387097 | 0.774193548387097 | 1.11e-16 | 2.75e-15 | pass | 16u x conditioning per side | 1.11e-16 | 0.00e+00 |
| flat LCDM, no radiation: Omega_de(z) | z=1 | 0.225806451612903 | 0.225806451612903 | 5.55e-17 | 1.60e-15 | pass | 16u x conditioning per side | 2.78e-17 | 2.78e-17 |
| flat LCDM, no radiation: rho_crit(z) [kg/m^3] | z=1 | 2.85320091612148e-26 | 2.85320091612148e-26 | 1.72e-41 | 1.52e-40 | pass | 16u x conditioning per side | 0.00e+00 | 1.72e-41 |
| flat LCDM, no radiation: D_C [Mpc] | z=2 | 5179.86207440937 | 5179.86207440937 | 9.09e-13 | 1.87e-10 | pass | engine bound + closed form 64u | 9.09e-13 | 0.00e+00 |
| flat LCDM, no radiation: D_M [Mpc] | z=2 | 5179.86207440937 | 5179.86207440937 | 9.09e-13 | 1.92e-10 | pass | propagated + closed form 64u | 9.09e-13 | 0.00e+00 |
| flat LCDM, no radiation: D_A [Mpc] | z=2 | 1726.62069146979 | 1726.62069146979 | 4.55e-13 | 6.47e-11 | pass | propagated + closed form 64u | 2.27e-13 | 2.27e-13 |
| flat LCDM, no radiation: D_L [Mpc] | z=2 | 15539.5862232281 | 15539.5862232281 | 1.82e-12 | 5.82e-10 | pass | propagated + closed form 64u | 1.82e-12 | 0.00e+00 |
| flat LCDM, no radiation: distance modulus | z=2 | 45.9571972527102 | 45.9571972527102 | 0.00e+00 | 1.23e-13 | pass | propagated + closed form 64u | 0.00e+00 | 0.00e+00 |
| flat LCDM, no radiation: lookback time [Gyr] | z=2 | 10.2403568869975 | 10.2403568869975 | 1.78e-15 | 1.64e-13 | pass | engine bound + closed form 64u | 0.00e+00 | 1.78e-15 |
| flat LCDM, no radiation: age [Gyr] | z=2 | 3.22662706006434 | 3.22662706006434 | 0.00e+00 | 3.43e-12 | pass | engine bound + closed form 64u | 8.88e-16 | 8.88e-16 |
| flat LCDM, no radiation: H [km/s/Mpc] | z=2 | 207.653557638679 | 207.653557638679 | 2.84e-14 | 7.38e-13 | pass | 16u x conditioning per side | 0.00e+00 | 2.84e-14 |
| flat LCDM, no radiation: Omega_m(z) | z=2 | 0.920454545454546 | 0.920454545454546 | 1.11e-16 | 3.27e-15 | pass | 16u x conditioning per side | 1.11e-16 | 2.22e-16 |
| flat LCDM, no radiation: Omega_de(z) | z=2 | 0.0795454545454545 | 0.0795454545454546 | 2.78e-17 | 5.65e-16 | pass | 16u x conditioning per side | 1.39e-17 | 1.39e-17 |
| flat LCDM, no radiation: rho_crit(z) [kg/m^3] | z=2 | 8.09940905221582e-26 | 8.09940905221581e-26 | 6.89e-41 | 4.32e-40 | pass | 16u x conditioning per side | 1.15e-41 | 5.74e-41 |
| flat LCDM, no radiation: D_C [Mpc] | z=5 | 7775.37049546286 | 7775.37049546287 | 1.82e-12 | 1.82e-10 | pass | engine bound + closed form 64u | 9.09e-13 | 9.09e-13 |
| flat LCDM, no radiation: D_M [Mpc] | z=5 | 7775.37049546286 | 7775.37049546287 | 1.82e-12 | 1.88e-10 | pass | propagated + closed form 64u | 9.09e-13 | 9.09e-13 |
| flat LCDM, no radiation: D_A [Mpc] | z=5 | 1295.89508257714 | 1295.89508257714 | 2.27e-13 | 3.20e-11 | pass | propagated + closed form 64u | 2.27e-13 | 0.00e+00 |
| flat LCDM, no radiation: D_L [Mpc] | z=5 | 46652.2229727772 | 46652.2229727772 | 7.28e-12 | 1.15e-09 | pass | propagated + closed form 64u | 7.28e-12 | 0.00e+00 |
| flat LCDM, no radiation: distance modulus | z=5 | 48.3443617132753 | 48.3443617132753 | 7.11e-15 | 9.75e-14 | pass | propagated + closed form 64u | 7.11e-15 | 0.00e+00 |
| flat LCDM, no radiation: lookback time [Gyr] | z=5 | 12.3122260363045 | 12.3122260363045 | 1.78e-15 | 1.63e-13 | pass | engine bound + closed form 64u | 3.55e-15 | 5.33e-15 |
| flat LCDM, no radiation: age [Gyr] | z=5 | 1.15475791075741 | 1.15475791075741 | 2.22e-16 | 1.23e-12 | pass | engine bound + closed form 64u | 2.22e-16 | 0.00e+00 |
| flat LCDM, no radiation: H [km/s/Mpc] | z=5 | 566.524491968353 | 566.524491968353 | 0.00e+00 | 2.01e-12 | pass | 16u x conditioning per side | 1.14e-13 | 1.14e-13 |
| flat LCDM, no radiation: Omega_m(z) | z=5 | 0.989312977099237 | 0.989312977099237 | 1.11e-16 | 3.51e-15 | pass | 16u x conditioning per side | 0.00e+00 | 1.11e-16 |
| flat LCDM, no radiation: Omega_de(z) | z=5 | 0.0106870229007634 | 0.0106870229007634 | 3.47e-18 | 7.59e-17 | pass | 16u x conditioning per side | 3.47e-18 | 0.00e+00 |
| flat LCDM, no radiation: rho_crit(z) [kg/m^3] | z=5 | 6.028537419547e-25 | 6.028537419547e-25 | 2.76e-40 | 3.21e-39 | pass | 16u x conditioning per side | 1.84e-40 | 9.18e-41 |
| flat LCDM, no radiation: D_C [Mpc] | z=10 | 9440.24962640023 | 9440.24962640023 | 1.82e-12 | 6.46e-10 | pass | engine bound + closed form 64u | 0.00e+00 | 1.82e-12 |
| flat LCDM, no radiation: D_M [Mpc] | z=10 | 9440.24962640023 | 9440.24962640023 | 1.82e-12 | 6.55e-10 | pass | propagated + closed form 64u | 0.00e+00 | 1.82e-12 |
| flat LCDM, no radiation: D_A [Mpc] | z=10 | 858.20451149093 | 858.20451149093 | 2.27e-13 | 5.99e-11 | pass | propagated + closed form 64u | 1.14e-13 | 1.14e-13 |
| flat LCDM, no radiation: D_L [Mpc] | z=10 | 103842.745890403 | 103842.745890403 | 2.91e-11 | 7.25e-09 | pass | propagated + closed form 64u | 1.46e-11 | 1.46e-11 |
| flat LCDM, no radiation: distance modulus | z=10 | 50.0818808177978 | 50.0818808177978 | 0.00e+00 | 1.97e-13 | pass | propagated + closed form 64u | 0.00e+00 | 0.00e+00 |
| flat LCDM, no radiation: lookback time [Gyr] | z=10 | 13.0010967089075 | 13.0010967089075 | 3.55e-15 | 1.61e-13 | pass | engine bound + closed form 64u | 0.00e+00 | 3.55e-15 |
| flat LCDM, no radiation: age [Gyr] | z=10 | 0.465887238154356 | 0.465887238154356 | 5.55e-17 | 4.96e-13 | pass | engine bound + closed form 64u | 5.55e-17 | 0.00e+00 |
| flat LCDM, no radiation: H [km/s/Mpc] | z=10 | 1400 | 1400 | 0.00e+00 | 4.97e-12 | pass | 16u x conditioning per side | 0.00e+00 | 0.00e+00 |
| flat LCDM, no radiation: Omega_m(z) | z=10 | 0.99825 | 0.99825 | 1.11e-16 | 3.55e-15 | pass | 16u x conditioning per side | 1.11e-16 | 2.22e-16 |
| flat LCDM, no radiation: Omega_de(z) | z=10 | 0.00175 | 0.00175 | 0.00e+00 | 1.24e-17 | pass | 16u x conditioning per side | 2.17e-19 | 2.17e-19 |
| flat LCDM, no radiation: rho_crit(z) [kg/m^3] | z=10 | 3.68154956918901e-24 | 3.68154956918901e-24 | 1.47e-39 | 1.96e-38 | pass | 16u x conditioning per side | 0.00e+00 | 1.47e-39 |
| flat LCDM, no radiation: D_C [Mpc] | z=100 | 12598.7338386548 | 12598.7338386548 | 0.00e+00 | 2.46e-10 | pass | engine bound + closed form 64u | 1.82e-12 | 1.82e-12 |
| flat LCDM, no radiation: D_M [Mpc] | z=100 | 12598.7338386548 | 12598.7338386548 | 0.00e+00 | 2.57e-10 | pass | propagated + closed form 64u | 1.82e-12 | 1.82e-12 |
| flat LCDM, no radiation: D_A [Mpc] | z=100 | 124.739938996582 | 124.739938996582 | 1.42e-14 | 2.60e-12 | pass | propagated + closed form 64u | 2.84e-14 | 1.42e-14 |
| flat LCDM, no radiation: D_L [Mpc] | z=100 | 1272472.11770413 | 1272472.11770413 | 0.00e+00 | 2.65e-08 | pass | propagated + closed form 64u | 2.33e-10 | 2.33e-10 |
| flat LCDM, no radiation: distance modulus | z=100 | 55.523241374455 | 55.523241374455 | 0.00e+00 | 9.55e-14 | pass | propagated + closed form 64u | 0.00e+00 | 0.00e+00 |
| flat LCDM, no radiation: lookback time [Gyr] | z=100 | 13.4502339618823 | 13.4502339618823 | 1.78e-15 | 9.82e-13 | pass | engine bound + closed form 64u | 3.55e-15 | 5.33e-15 |
| flat LCDM, no radiation: age [Gyr] | z=100 | 0.0167499851795682 | 0.0167499851795682 | 3.47e-18 | 1.78e-14 | pass | engine bound + closed form 64u | 0.00e+00 | 3.47e-18 |
| flat LCDM, no radiation: H [km/s/Mpc] | z=100 | 38917.1671630914 | 38917.1671630914 | 0.00e+00 | 1.38e-10 | pass | 16u x conditioning per side | 0.00e+00 | 0.00e+00 |
| flat LCDM, no radiation: Omega_m(z) | z=100 | 0.999997735294784 | 0.999997735294784 | 2.22e-16 | 3.55e-15 | pass | 16u x conditioning per side | 0.00e+00 | 2.22e-16 |
| flat LCDM, no radiation: Omega_de(z) | z=100 | 2.26470521626317e-06 | 2.26470521626317e-06 | 4.24e-22 | 1.61e-20 | pass | 16u x conditioning per side | 4.24e-22 | 8.47e-22 |
| flat LCDM, no radiation: rho_crit(z) [kg/m^3] | z=100 | 2.8448345947255e-21 | 2.8448345947255e-21 | 1.13e-36 | 1.52e-35 | pass | 16u x conditioning per side | 0.00e+00 | 1.13e-36 |
| flat LCDM, no radiation: D_C [Mpc] | z=1000 | 13660.529296916 | 13660.529296916 | 1.82e-12 | 1.71e-10 | pass | engine bound + closed form 64u | 1.82e-12 | 3.64e-12 |
| flat LCDM, no radiation: D_M [Mpc] | z=1000 | 13660.529296916 | 13660.529296916 | 1.82e-12 | 1.84e-10 | pass | propagated + closed form 64u | 1.82e-12 | 3.64e-12 |
| flat LCDM, no radiation: D_A [Mpc] | z=1000 | 13.6468824145015 | 13.6468824145015 | 1.78e-15 | 1.90e-13 | pass | propagated + closed form 64u | 1.78e-15 | 3.55e-15 |
| flat LCDM, no radiation: D_L [Mpc] | z=1000 | 13674189.826213 | 13674189.826213 | 1.86e-09 | 1.90e-07 | pass | propagated + closed form 64u | 0.00e+00 | 1.86e-09 |
| flat LCDM, no radiation: distance modulus | z=1000 | 60.6795080225856 | 60.6795080225856 | 0.00e+00 | 8.50e-14 | pass | propagated + closed form 64u | 0.00e+00 | 0.00e+00 |
| flat LCDM, no radiation: lookback time [Gyr] | z=1000 | 13.4664471062366 | 13.4664471062366 | 3.55e-15 | 1.61e-13 | pass | engine bound + closed form 64u | 0.00e+00 | 3.55e-15 |
| flat LCDM, no radiation: age [Gyr] | z=1000 | 0.000536840825270842 | 0.000536840825270842 | 0.00e+00 | 5.71e-16 | pass | engine bound + closed form 64u | 1.08e-19 | 1.08e-19 |
| flat LCDM, no radiation: H [km/s/Mpc] | z=1000 | 1214254.67464614 | 1214254.67464614 | 0.00e+00 | 4.31e-09 | pass | 16u x conditioning per side | 0.00e+00 | 0.00e+00 |
| flat LCDM, no radiation: Omega_m(z) | z=1000 | 0.999999997673653 | 0.999999997673653 | 1.11e-16 | 3.55e-15 | pass | 16u x conditioning per side | 1.11e-16 | 0.00e+00 |
| flat LCDM, no radiation: Omega_de(z) | z=1000 | 2.32634730462306e-09 | 2.32634730462306e-09 | 4.14e-25 | 1.65e-23 | pass | 16u x conditioning per side | 0.00e+00 | 4.14e-25 |
| flat LCDM, no radiation: rho_crit(z) [kg/m^3] | z=1000 | 2.76945395611284e-18 | 2.76945395611284e-18 | 1.16e-33 | 1.48e-32 | pass | 16u x conditioning per side | 0.00e+00 | 1.16e-33 |
| flat LCDM, no radiation: rho_crit0 [kg/m^3] | today | 9.20387392297252e-27 | 9.20387392297252e-27 | 4.30e-42 | 2.45e-41 | pass | 12 roundings |  |  |
| flat LCDM, no radiation: hubble distance [Mpc] | today | 4282.7494 | 4282.7494 | 9.09e-13 | 3.80e-12 | pass | 4 roundings |  |  |
| flat LCDM, no radiation: hubble time [Gyr] | today | 13.9684603097256 | 13.9684603097256 | 1.78e-15 | 2.48e-14 | pass | 8 roundings |  |  |
| flat LCDM, no radiation: D_A(z1, z2) [Mpc] | z1=0.5, z2=2 | 1097.07889282532 | 1097.07889282532 | 3.64e-12 | 2.61e-09 | pass | propagated + closed form 64u |  |  |
| flat LCDM, no radiation: D_A(z1, z2) [Mpc] | z1=1, z2=1100 | 9.42750381839655 | 9.42750381839655 | 0.00e+00 | 1.66e-11 | pass | propagated + closed form 64u |  |  |
| flat LCDM + radiation: D_C [Mpc] | z=0.001 | 4.42983735462504 | 4.42983735462504 | 8.88e-16 | 6.60e-05 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 8.88e-16 |
| flat LCDM + radiation: D_M [Mpc] | z=0.001 | 4.42983735462504 | 4.42983735462504 | 8.88e-16 | 6.60e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 8.88e-16 |
| flat LCDM + radiation: D_A [Mpc] | z=0.001 | 4.42541194268235 | 4.42541194268235 | 8.88e-16 | 6.60e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 8.88e-16 |
| flat LCDM + radiation: D_L [Mpc] | z=0.001 | 4.43426719197966 | 4.43426719197966 | 8.88e-16 | 6.61e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 8.88e-16 |
| flat LCDM + radiation: distance modulus | z=0.001 | 28.234109292456 | 28.234109292456 | 0.00e+00 | 3.24e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| flat LCDM + radiation: lookback time [Gyr] | z=0.001 | 0.0144409783276978 | 0.0144409783276978 | 0.00e+00 | 2.15e-07 | pass | engine bound + quad 1.49e-8 | 1.73e-18 | 1.73e-18 |
| flat LCDM + radiation: age [Gyr] | z=0.001 | 13.7896807558276 | 13.7896807558276 | 6.57e-14 | 2.15e-07 | pass | engine bound + quad 1.49e-8 | 1.78e-15 | 6.39e-14 |
| flat LCDM + radiation: H [km/s/Mpc] | z=0.001 | 67.6914620163465 | 67.6914620163465 | 1.42e-14 | 2.43e-13 | pass | 16u x conditioning per side | 1.42e-14 | 0.00e+00 |
| flat LCDM + radiation: Omega_m(z) | z=0.001 | 0.310282664068051 | 0.310282664068051 | 0.00e+00 | 1.13e-15 | pass | 16u x conditioning per side | 1.11e-16 | 1.11e-16 |
| flat LCDM + radiation: Omega_de(z) | z=0.001 | 0.689625665486949 | 0.689625665486949 | 0.00e+00 | 4.95e-15 | pass | 16u x conditioning per side | 1.11e-16 | 1.11e-16 |
| flat LCDM + radiation: rho_crit(z) [kg/m^3] | z=0.001 | 8.60681304274655e-27 | 8.60681304274655e-27 | 1.43e-42 | 4.65e-41 | pass | 16u x conditioning per side | 1.43e-42 | 2.87e-42 |
| flat LCDM + radiation: D_C [Mpc] | z=0.1 | 432.611334398472 | 432.611334398472 | 5.68e-14 | 6.60e-05 | pass | engine bound + quad 1.49e-8 | 5.68e-14 | 1.14e-13 |
| flat LCDM + radiation: D_M [Mpc] | z=0.1 | 432.611334398472 | 432.611334398472 | 5.68e-14 | 6.60e-05 | pass | propagated + quad 1.49e-8 | 5.68e-14 | 1.14e-13 |
| flat LCDM + radiation: D_A [Mpc] | z=0.1 | 393.283031271338 | 393.283031271338 | 5.68e-14 | 6.00e-05 | pass | propagated + quad 1.49e-8 | 5.68e-14 | 1.14e-13 |
| flat LCDM + radiation: D_L [Mpc] | z=0.1 | 475.872467838319 | 475.872467838319 | 5.68e-14 | 7.26e-05 | pass | propagated + quad 1.49e-8 | 5.68e-14 | 1.14e-13 |
| flat LCDM + radiation: distance modulus | z=0.1 | 38.3874528945361 | 38.3874528945361 | 0.00e+00 | 3.31e-07 | pass | propagated + quad 1.49e-8 | 7.11e-15 | 7.11e-15 |
| flat LCDM + radiation: lookback time [Gyr] | z=0.1 | 1.34533780136671 | 1.34533780136671 | 2.22e-16 | 2.15e-07 | pass | engine bound + quad 1.49e-8 | 2.22e-16 | 0.00e+00 |
| flat LCDM + radiation: age [Gyr] | z=0.1 | 12.4587839327886 | 12.4587839327886 | 6.04e-14 | 2.15e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 6.04e-14 |
| flat LCDM + radiation: H [km/s/Mpc] | z=0.1 | 71.0440867746465 | 71.0440867746465 | 1.42e-14 | 2.56e-13 | pass | 16u x conditioning per side | 0.00e+00 | 1.42e-14 |
| flat LCDM + radiation: Omega_m(z) | z=0.1 | 0.373805124580633 | 0.373805124580633 | 0.00e+00 | 1.37e-15 | pass | 16u x conditioning per side | 5.55e-17 | 5.55e-17 |
| flat LCDM + radiation: Omega_de(z) | z=0.1 | 0.626073515386174 | 0.626073515386174 | 0.00e+00 | 4.51e-15 | pass | 16u x conditioning per side | 0.00e+00 | 0.00e+00 |
| flat LCDM + radiation: rho_crit(z) [kg/m^3] | z=0.1 | 9.48048276513459e-27 | 9.48048276513459e-27 | 2.87e-42 | 5.15e-41 | pass | 16u x conditioning per side | 0.00e+00 | 2.87e-42 |
| flat LCDM + radiation: D_C [Mpc] | z=0.5 | 1947.36046566774 | 1947.36046566774 | 2.27e-13 | 6.60e-05 | pass | engine bound + quad 1.49e-8 | 2.27e-13 | 4.55e-13 |
| flat LCDM + radiation: D_M [Mpc] | z=0.5 | 1947.36046566774 | 1947.36046566774 | 2.27e-13 | 6.60e-05 | pass | propagated + quad 1.49e-8 | 2.27e-13 | 4.55e-13 |
| flat LCDM + radiation: D_A [Mpc] | z=0.5 | 1298.24031044516 | 1298.24031044516 | 2.27e-13 | 4.40e-05 | pass | propagated + quad 1.49e-8 | 2.27e-13 | 4.55e-13 |
| flat LCDM + radiation: D_L [Mpc] | z=0.5 | 2921.04069850161 | 2921.04069850161 | 4.55e-13 | 9.90e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 4.55e-13 |
| flat LCDM + radiation: distance modulus | z=0.5 | 42.3276880399371 | 42.3276880399371 | 0.00e+00 | 7.36e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| flat LCDM + radiation: lookback time [Gyr] | z=0.5 | 5.19858888400289 | 5.19858888400289 | 8.88e-16 | 2.15e-07 | pass | engine bound + quad 1.49e-8 | 1.78e-15 | 8.88e-16 |
| flat LCDM + radiation: age [Gyr] | z=0.5 | 8.60553285015244 | 8.60553285015238 | 6.04e-14 | 2.15e-07 | pass | engine bound + quad 1.49e-8 | 1.78e-15 | 5.86e-14 |
| flat LCDM + radiation: H [km/s/Mpc] | z=0.5 | 89.1411113304763 | 89.1411113304763 | 1.42e-14 | 3.27e-13 | pass | 16u x conditioning per side | 1.42e-14 | 0.00e+00 |
| flat LCDM + radiation: Omega_m(z) | z=0.5 | 0.602061361509041 | 0.60206136150904 | 1.11e-16 | 2.28e-15 | pass | 16u x conditioning per side | 0.00e+00 | 1.11e-16 |
| flat LCDM + radiation: Omega_de(z) | z=0.5 | 0.397672093966168 | 0.397672093966169 | 1.11e-16 | 2.92e-15 | pass | 16u x conditioning per side | 1.11e-16 | 0.00e+00 |
| flat LCDM + radiation: rho_crit(z) [kg/m^3] | z=0.5 | 1.49255611907e-26 | 1.49255611907e-26 | 1.43e-41 | 8.30e-41 | pass | 16u x conditioning per side | 2.87e-42 | 1.15e-41 |
| flat LCDM + radiation: D_C [Mpc] | z=1 | 3398.42724588796 | 3398.42724588796 | 4.55e-13 | 6.60e-05 | pass | engine bound + quad 1.49e-8 | 9.09e-13 | 4.55e-13 |
| flat LCDM + radiation: D_M [Mpc] | z=1 | 3398.42724588796 | 3398.42724588796 | 4.55e-13 | 6.60e-05 | pass | propagated + quad 1.49e-8 | 9.09e-13 | 4.55e-13 |
| flat LCDM + radiation: D_A [Mpc] | z=1 | 1699.21362294398 | 1699.21362294398 | 2.27e-13 | 3.30e-05 | pass | propagated + quad 1.49e-8 | 4.55e-13 | 2.27e-13 |
| flat LCDM + radiation: D_L [Mpc] | z=1 | 6796.85449177592 | 6796.85449177592 | 9.09e-13 | 1.32e-04 | pass | propagated + quad 1.49e-8 | 1.82e-12 | 9.09e-13 |
| flat LCDM + radiation: distance modulus | z=1 | 44.161539862856 | 44.161539862856 | 0.00e+00 | 4.22e-08 | pass | propagated + quad 1.49e-8 | 7.11e-15 | 7.11e-15 |
| flat LCDM + radiation: lookback time [Gyr] | z=1 | 7.94134762427222 | 7.94134762427222 | 0.00e+00 | 2.15e-07 | pass | engine bound + quad 1.49e-8 | 8.88e-16 | 8.88e-16 |
| flat LCDM + radiation: age [Gyr] | z=1 | 5.86277410988312 | 5.86277410988305 | 6.31e-14 | 2.15e-07 | pass | engine bound + quad 1.49e-8 | 8.88e-16 | 6.22e-14 |
| flat LCDM + radiation: H [km/s/Mpc] | z=1 | 120.443560035764 | 120.443560035764 | 1.42e-14 | 4.52e-13 | pass | 16u x conditioning per side | 0.00e+00 | 1.42e-14 |
| flat LCDM + radiation: Omega_m(z) | z=1 | 0.781710394738744 | 0.781710394738745 | 3.33e-16 | 3.09e-15 | pass | 16u x conditioning per side | 1.11e-16 | 2.22e-16 |
| flat LCDM + radiation: Omega_de(z) | z=1 | 0.217828166967175 | 0.217828166967175 | 1.39e-16 | 1.63e-15 | pass | 16u x conditioning per side | 2.78e-17 | 1.11e-16 |
| flat LCDM + radiation: rho_crit(z) [kg/m^3] | z=1 | 2.72484465850565e-26 | 2.72484465850565e-26 | 2.30e-41 | 1.56e-40 | pass | 16u x conditioning per side | 0.00e+00 | 2.30e-41 |
| flat LCDM + radiation: D_C [Mpc] | z=2 | 5314.43833589558 | 5314.43833589558 | 9.09e-13 | 7.92e-05 | pass | engine bound + quad 1.49e-8 | 9.09e-13 | 0.00e+00 |
| flat LCDM + radiation: D_M [Mpc] | z=2 | 5314.43833589558 | 5314.43833589558 | 9.09e-13 | 7.92e-05 | pass | propagated + quad 1.49e-8 | 9.09e-13 | 0.00e+00 |
| flat LCDM + radiation: D_A [Mpc] | z=2 | 1771.47944529853 | 1771.47944529853 | 2.27e-13 | 2.64e-05 | pass | propagated + quad 1.49e-8 | 4.55e-13 | 2.27e-13 |
| flat LCDM + radiation: D_L [Mpc] | z=2 | 15943.3150076867 | 15943.3150076867 | 1.82e-12 | 2.38e-04 | pass | propagated + quad 1.49e-8 | 1.82e-12 | 0.00e+00 |
| flat LCDM + radiation: distance modulus | z=2 | 46.012893134818 | 46.012893134818 | 0.00e+00 | 3.24e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| flat LCDM + radiation: lookback time [Gyr] | z=2 | 10.5204748347098 | 10.5204748347098 | 1.78e-15 | 2.15e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 1.78e-15 |
| flat LCDM + radiation: age [Gyr] | z=2 | 3.28364689944556 | 3.2836468994455 | 6.13e-14 | 2.15e-07 | pass | engine bound + quad 1.49e-8 | 1.78e-15 | 6.31e-14 |
| flat LCDM + radiation: H [km/s/Mpc] | z=2 | 203.632868716734 | 203.632868716734 | 5.68e-14 | 7.95e-13 | pass | 16u x conditioning per side | 0.00e+00 | 5.68e-14 |
| flat LCDM + radiation: Omega_m(z) | z=2 | 0.922977412050118 | 0.922977412050118 | 4.44e-16 | 3.93e-15 | pass | 16u x conditioning per side | 0.00e+00 | 4.44e-16 |
| flat LCDM + radiation: Omega_de(z) | z=2 | 0.0762053470790481 | 0.0762053470790481 | 6.94e-17 | 5.95e-16 | pass | 16u x conditioning per side | 2.78e-17 | 4.16e-17 |
| flat LCDM + radiation: rho_crit(z) [kg/m^3] | z=2 | 7.78879619322375e-26 | 7.78879619322374e-26 | 9.18e-41 | 4.70e-40 | pass | 16u x conditioning per side | 1.15e-41 | 8.04e-41 |
| flat LCDM + radiation: D_C [Mpc] | z=5 | 7958.11758890213 | 7958.11758890213 | 9.09e-13 | 1.19e-04 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 9.09e-13 |
| flat LCDM + radiation: D_M [Mpc] | z=5 | 7958.11758890213 | 7958.11758890213 | 9.09e-13 | 1.19e-04 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 9.09e-13 |
| flat LCDM + radiation: D_A [Mpc] | z=5 | 1326.35293148369 | 1326.35293148369 | 2.27e-13 | 1.98e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 2.27e-13 |
| flat LCDM + radiation: D_L [Mpc] | z=5 | 47748.7055334128 | 47748.7055334128 | 0.00e+00 | 7.11e-04 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| flat LCDM + radiation: distance modulus | z=5 | 48.394808011817 | 48.394808011817 | 0.00e+00 | 3.24e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| flat LCDM + radiation: lookback time [Gyr] | z=5 | 12.63103113409 | 12.63103113409 | 1.78e-15 | 2.15e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 1.78e-15 |
| flat LCDM + radiation: age [Gyr] | z=5 | 1.17309060006531 | 1.17309060006524 | 6.35e-14 | 2.15e-07 | pass | engine bound + quad 1.49e-8 | 2.22e-16 | 6.37e-14 |
| flat LCDM + radiation: H [km/s/Mpc] | z=5 | 556.670607363994 | 556.670607363993 | 1.14e-13 | 2.40e-12 | pass | 16u x conditioning per side | 1.14e-13 | 2.27e-13 |
| flat LCDM + radiation: Omega_m(z) | z=5 | 0.9880529907174 | 0.988052990717401 | 7.77e-16 | 5.00e-15 | pass | 16u x conditioning per side | 0.00e+00 | 7.77e-16 |
| flat LCDM + radiation: Omega_de(z) | z=5 | 0.0101972865352774 | 0.0101972865352774 | 1.39e-17 | 8.78e-17 | pass | 16u x conditioning per side | 3.47e-18 | 1.04e-17 |
| flat LCDM + radiation: rho_crit(z) [kg/m^3] | z=5 | 5.82064567058315e-25 | 5.82064567058315e-25 | 6.43e-40 | 3.98e-39 | pass | 16u x conditioning per side | 9.18e-41 | 5.51e-40 |
| flat LCDM + radiation: D_C [Mpc] | z=10 | 9651.72225020802 | 9651.72225020802 | 1.82e-12 | 1.44e-04 | pass | engine bound + quad 1.49e-8 | 1.82e-12 | 3.64e-12 |
| flat LCDM + radiation: D_M [Mpc] | z=10 | 9651.72225020802 | 9651.72225020802 | 1.82e-12 | 1.44e-04 | pass | propagated + quad 1.49e-8 | 1.82e-12 | 3.64e-12 |
| flat LCDM + radiation: D_A [Mpc] | z=10 | 877.429295473456 | 877.429295473456 | 1.14e-13 | 1.31e-05 | pass | propagated + quad 1.49e-8 | 1.14e-13 | 2.27e-13 |
| flat LCDM + radiation: D_L [Mpc] | z=10 | 106168.944752288 | 106168.944752288 | 1.46e-11 | 1.58e-03 | pass | propagated + quad 1.49e-8 | 1.46e-11 | 2.91e-11 |
| flat LCDM + radiation: distance modulus | z=10 | 50.1299875039218 | 50.1299875039218 | 0.00e+00 | 3.24e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| flat LCDM + radiation: lookback time [Gyr] | z=10 | 13.3318195748193 | 13.3318195748193 | 1.78e-15 | 2.15e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 1.78e-15 |
| flat LCDM + radiation: age [Gyr] | z=10 | 0.472302159335996 | 0.472302159335931 | 6.48e-14 | 2.15e-07 | pass | engine bound + quad 1.49e-8 | 5.55e-17 | 6.48e-14 |
| flat LCDM + radiation: H [km/s/Mpc] | z=10 | 1376.9451028965 | 1376.9451028965 | 1.14e-12 | 6.81e-12 | pass | 16u x conditioning per side | 0.00e+00 | 1.14e-12 |
| flat LCDM + radiation: Omega_m(z) | z=10 | 0.995102623928206 | 0.995102623928207 | 9.99e-16 | 6.30e-15 | pass | 16u x conditioning per side | 1.11e-16 | 1.11e-15 |
| flat LCDM + radiation: Omega_de(z) | z=10 | 0.00166666360883008 | 0.00166666360883009 | 1.95e-18 | 1.65e-17 | pass | 16u x conditioning per side | 2.17e-19 | 2.17e-18 |
| flat LCDM + radiation: rho_crit(z) [kg/m^3] | z=10 | 3.56129403730862e-24 | 3.56129403730861e-24 | 7.35e-39 | 2.89e-38 | pass | 16u x conditioning per side | 0.00e+00 | 7.35e-39 |
| flat LCDM + radiation: D_C [Mpc] | z=100 | 12852.5387083305 | 12852.5387083305 | 9.09e-12 | 1.92e-04 | pass | engine bound + quad 1.49e-8 | 1.82e-12 | 7.28e-12 |
| flat LCDM + radiation: D_M [Mpc] | z=100 | 12852.5387083305 | 12852.5387083305 | 9.09e-12 | 1.92e-04 | pass | propagated + quad 1.49e-8 | 1.82e-12 | 7.28e-12 |
| flat LCDM + radiation: D_A [Mpc] | z=100 | 127.252858498321 | 127.252858498322 | 9.95e-14 | 1.90e-06 | pass | propagated + quad 1.49e-8 | 1.42e-14 | 8.53e-14 |
| flat LCDM + radiation: D_L [Mpc] | z=100 | 1298106.40954138 | 1298106.40954138 | 9.31e-10 | 1.93e-02 | pass | propagated + quad 1.49e-8 | 2.33e-10 | 6.98e-10 |
| flat LCDM + radiation: distance modulus | z=100 | 55.5665514714993 | 55.5665514714993 | 0.00e+00 | 3.24e-08 | pass | propagated + quad 1.49e-8 | 7.11e-15 | 7.11e-15 |
| flat LCDM + radiation: lookback time [Gyr] | z=100 | 13.7876684293028 | 13.7876684293028 | 3.55e-15 | 2.15e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 3.55e-15 |
| flat LCDM + radiation: age [Gyr] | z=100 | 0.0164533048525185 | 0.0164533048524324 | 8.61e-14 | 2.15e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 8.61e-14 |
| flat LCDM + radiation: H [km/s/Mpc] | z=100 | 38781.31774178 | 38781.3177417798 | 2.47e-10 | 6.21e-10 | pass | 16u x conditioning per side | 0.00e+00 | 2.47e-10 |
| flat LCDM + radiation: Omega_m(z) | z=100 | 0.971051057020357 | 0.971051057020369 | 1.23e-14 | 2.76e-14 | pass | 16u x conditioning per side | 1.11e-16 | 1.22e-14 |
| flat LCDM + radiation: Omega_de(z) | z=100 | 2.10104851557227e-06 | 2.1010485155723e-06 | 2.67e-20 | 6.73e-20 | pass | 16u x conditioning per side | 0.00e+00 | 2.67e-20 |
| flat LCDM + radiation: rho_crit(z) [kg/m^3] | z=100 | 2.82500814632982e-21 | 2.82500814632978e-21 | 3.72e-35 | 8.54e-35 | pass | 16u x conditioning per side | 3.76e-37 | 3.69e-35 |
| flat LCDM + radiation: D_C [Mpc] | z=1000 | 13887.7130680185 | 13887.7130680185 | 3.46e-11 | 2.07e-04 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 3.46e-11 |
| flat LCDM + radiation: D_M [Mpc] | z=1000 | 13887.7130680185 | 13887.7130680185 | 3.46e-11 | 2.07e-04 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 3.46e-11 |
| flat LCDM + radiation: D_A [Mpc] | z=1000 | 13.8738392287897 | 13.8738392287897 | 3.55e-14 | 2.07e-07 | pass | propagated + quad 1.49e-8 | 1.78e-15 | 3.38e-14 |
| flat LCDM + radiation: D_L [Mpc] | z=1000 | 13901600.7810865 | 13901600.7810865 | 3.54e-08 | 2.07e-01 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 3.54e-08 |
| flat LCDM + radiation: distance modulus | z=1000 | 60.7153240625525 | 60.7153240625525 | 7.11e-15 | 3.24e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 7.11e-15 |
| flat LCDM + radiation: lookback time [Gyr] | z=1000 | 13.803691587006 | 13.803691587006 | 2.49e-14 | 2.15e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 2.49e-14 |
| flat LCDM + radiation: age [Gyr] | z=1000 | 0.000430147149352185 | 0.000430146939934315 | 2.09e-10 | 2.15e-07 | pass | engine bound + quad 1.49e-8 | 1.63e-19 | 2.09e-10 |
| flat LCDM + radiation: H [km/s/Mpc] | z=1000 | 1357130.43685871 | 1357130.43685864 | 6.64e-08 | 1.38e-07 | pass | 16u x conditioning per side | 0.00e+00 | 6.64e-08 |
| flat LCDM + radiation: Omega_m(z) | z=1000 | 0.771937463688801 | 0.771937463688877 | 7.56e-14 | 1.54e-13 | pass | 16u x conditioning per side | 0.00e+00 | 7.56e-14 |
| flat LCDM + radiation: Omega_de(z) | z=1000 | 1.71568685188916e-09 | 1.71568685188933e-09 | 1.68e-22 | 3.49e-22 | pass | 16u x conditioning per side | 0.00e+00 | 1.68e-22 |
| flat LCDM + radiation: rho_crit(z) [kg/m^3] | z=1000 | 3.45953526763361e-18 | 3.45953526763327e-18 | 3.40e-31 | 6.97e-31 | pass | 16u x conditioning per side | 0.00e+00 | 3.40e-31 |
| flat LCDM + radiation: Omega_gamma0 | today | 5.40201513713935e-05 | 5.40201513713935e-05 | 4.74e-20 | 1.44e-19 | pass | 12 roundings |  |  |
| flat LCDM + radiation: Omega_nu0 | today | 3.73694601298394e-05 | 3.73694601298001e-05 | 3.93e-17 | 3.95e-17 | pass | 16 roundings + literal |  |  |
| flat LCDM + radiation: T_nu0 [K] (engine / (N_eff/3)^(1/4)) | today | 1.94536883917508 | 1.94536883917508 | 0.00e+00 | 3.47e-15 | pass | 8 roundings |  |  |
| flat LCDM + radiation: rho_crit0 [kg/m^3] | today | 8.5988142566229e-27 | 8.59881425662289e-27 | 4.30e-42 | 2.29e-41 | pass | 12 roundings |  |  |
| flat LCDM + radiation: hubble distance [Mpc] | today | 4430.8669524091 | 4430.8669524091 | 0.00e+00 | 3.94e-12 | pass | 4 roundings |  |  |
| flat LCDM + radiation: hubble time [Gyr] | today | 14.4515551534258 | 14.4515551534258 | 0.00e+00 | 2.57e-14 | pass | 8 roundings |  |  |
| flat LCDM + radiation: D_A(z1, z2) [Mpc] | z1=0.5, z2=2 | 1122.35929007595 | 1122.35929007595 | 2.27e-13 | 4.84e-05 | pass | propagated + quad 1.49e-8 |  |  |
| flat LCDM + radiation: D_A(z1, z2) [Mpc] | z1=1, z2=1100 | 9.54562630500727 | 9.54562630500723 | 4.62e-14 | 2.48e-07 | pass | propagated + quad 1.49e-8 |  |  |
| open LCDM + radiation: D_C [Mpc] | z=0.001 | 4.28157139522891 | 4.28157139522891 | 8.88e-16 | 6.38e-05 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 8.88e-16 |
| open LCDM + radiation: D_M [Mpc] | z=0.001 | 4.28157146648828 | 4.28157146648828 | 8.88e-16 | 6.38e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 8.88e-16 |
| open LCDM + radiation: D_A [Mpc] | z=0.001 | 4.27729417231597 | 4.27729417231597 | 0.00e+00 | 6.37e-05 | pass | propagated + quad 1.49e-8 | 8.88e-16 | 8.88e-16 |
| open LCDM + radiation: D_L [Mpc] | z=0.001 | 4.28585303795477 | 4.28585303795477 | 8.88e-16 | 6.39e-05 | pass | propagated + quad 1.49e-8 | 8.88e-16 | 0.00e+00 |
| open LCDM + radiation: distance modulus | z=0.001 | 28.1601863749435 | 28.1601863749435 | 0.00e+00 | 3.24e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| open LCDM + radiation: lookback time [Gyr] | z=0.001 | 0.0139576411540675 | 0.0139576411540675 | 1.73e-18 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 3.47e-18 | 1.73e-18 |
| open LCDM + radiation: age [Gyr] | z=0.001 | 13.0431229451524 | 13.0431229451523 | 8.88e-14 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 3.55e-15 | 8.53e-14 |
| open LCDM + radiation: H [km/s/Mpc] | z=0.001 | 70.0385303979464 | 70.0385303979464 | 0.00e+00 | 3.01e-13 | pass | 16u x conditioning per side | 1.42e-14 | 1.42e-14 |
| open LCDM + radiation: Omega_m(z) | z=0.001 | 0.300569921271756 | 0.300569921271756 | 0.00e+00 | 1.30e-15 | pass | 16u x conditioning per side | 5.55e-17 | 5.55e-17 |
| open LCDM + radiation: Omega_de(z) | z=0.001 | 0.599340023852542 | 0.599340023852542 | 1.11e-16 | 4.73e-15 | pass | 16u x conditioning per side | 1.11e-16 | 0.00e+00 |
| open LCDM + radiation: Omega_k(z) | z=0.001 | 0.100004425440727 | 0.100004425440727 | 2.78e-17 | 4.34e-16 | pass | 16u x conditioning per side | 1.39e-17 | 1.39e-17 |
| open LCDM + radiation: rho_crit(z) [kg/m^3] | z=0.001 | 9.21400896653982e-27 | 9.21400896653981e-27 | 5.74e-42 | 5.63e-41 | pass | 16u x conditioning per side | 1.43e-42 | 7.17e-42 |
| open LCDM + radiation: D_C [Mpc] | z=0.1 | 416.456161197222 | 416.456161197223 | 5.68e-14 | 6.38e-05 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 5.68e-14 |
| open LCDM + radiation: D_M [Mpc] | z=0.1 | 416.521739601895 | 416.521739601895 | 1.14e-13 | 6.38e-05 | pass | propagated + quad 1.49e-8 | 5.68e-14 | 5.68e-14 |
| open LCDM + radiation: D_A [Mpc] | z=0.1 | 378.656126910814 | 378.656126910814 | 5.68e-14 | 5.80e-05 | pass | propagated + quad 1.49e-8 | 5.68e-14 | 0.00e+00 |
| open LCDM + radiation: D_L [Mpc] | z=0.1 | 458.173913562085 | 458.173913562085 | 1.14e-13 | 7.02e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 1.14e-13 |
| open LCDM + radiation: distance modulus | z=0.1 | 38.3051517935538 | 38.3051517935538 | 0.00e+00 | 3.33e-07 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| open LCDM + radiation: lookback time [Gyr] | z=0.1 | 1.29518068671185 | 1.29518068671185 | 0.00e+00 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| open LCDM + radiation: age [Gyr] | z=0.1 | 11.7618998995946 | 11.7618998995945 | 8.53e-14 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 8.53e-14 |
| open LCDM + radiation: H [km/s/Mpc] | z=0.1 | 74.0916750241636 | 74.0916750241636 | 0.00e+00 | 3.24e-13 | pass | 16u x conditioning per side | 1.42e-14 | 1.42e-14 |
| open LCDM + radiation: Omega_m(z) | z=0.1 | 0.356415484595635 | 0.356415484595635 | 5.55e-17 | 1.57e-15 | pass | 16u x conditioning per side | 5.55e-17 | 1.11e-16 |
| open LCDM + radiation: Omega_de(z) | z=0.1 | 0.535560457694418 | 0.535560457694418 | 1.11e-16 | 4.27e-15 | pass | 16u x conditioning per side | 0.00e+00 | 1.11e-16 |
| open LCDM + radiation: Omega_k(z) | z=0.1 | 0.107912476071996 | 0.107912476071996 | 5.55e-17 | 4.76e-16 | pass | 16u x conditioning per side | 1.39e-17 | 6.94e-17 |
| open LCDM + radiation: rho_crit(z) [kg/m^3] | z=0.1 | 1.03112996384331e-26 | 1.03112996384331e-26 | 2.87e-42 | 6.38e-41 | pass | 16u x conditioning per side | 0.00e+00 | 2.87e-42 |
| open LCDM + radiation: D_C [Mpc] | z=0.5 | 1852.50912905059 | 1852.5091290506 | 6.82e-13 | 6.38e-05 | pass | engine bound + quad 1.49e-8 | 2.27e-13 | 4.55e-13 |
| open LCDM + radiation: D_M [Mpc] | z=0.5 | 1858.28635636621 | 1858.28635636621 | 6.82e-13 | 6.44e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 6.82e-13 |
| open LCDM + radiation: D_A [Mpc] | z=0.5 | 1238.8575709108 | 1238.85757091081 | 4.55e-13 | 4.29e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 4.55e-13 |
| open LCDM + radiation: D_L [Mpc] | z=0.5 | 2787.42953454931 | 2787.42953454931 | 9.09e-13 | 9.66e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 9.09e-13 |
| open LCDM + radiation: distance modulus | z=0.5 | 42.2260194867507 | 42.2260194867507 | 0.00e+00 | 7.53e-08 | pass | propagated + quad 1.49e-8 | 7.11e-15 | 7.11e-15 |
| open LCDM + radiation: lookback time [Gyr] | z=0.5 | 4.95019258855725 | 4.95019258855725 | 0.00e+00 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| open LCDM + radiation: age [Gyr] | z=0.5 | 8.10688799774922 | 8.10688799774913 | 8.53e-14 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 8.53e-14 |
| open LCDM + radiation: H [km/s/Mpc] | z=0.5 | 94.8942920643368 | 94.8942920643368 | 0.00e+00 | 4.29e-13 | pass | 16u x conditioning per side | 1.42e-14 | 1.42e-14 |
| open LCDM + radiation: Omega_m(z) | z=0.5 | 0.550948406777866 | 0.550948406777866 | 1.11e-16 | 2.55e-15 | pass | 16u x conditioning per side | 0.00e+00 | 1.11e-16 |
| open LCDM + radiation: Omega_de(z) | z=0.5 | 0.326487944757254 | 0.326487944757254 | 0.00e+00 | 2.67e-15 | pass | 16u x conditioning per side | 5.55e-17 | 5.55e-17 |
| open LCDM + radiation: Omega_k(z) | z=0.5 | 0.122328443939243 | 0.122328443939243 | 2.78e-17 | 5.66e-16 | pass | 16u x conditioning per side | 0.00e+00 | 2.78e-17 |
| open LCDM + radiation: rho_crit(z) [kg/m^3] | z=0.5 | 1.69143285149147e-26 | 1.69143285149147e-26 | 2.87e-42 | 1.08e-40 | pass | 16u x conditioning per side | 0.00e+00 | 2.87e-42 |
| open LCDM + radiation: D_C [Mpc] | z=1 | 3209.58922043273 | 3209.58922043273 | 1.82e-12 | 6.38e-05 | pass | engine bound + quad 1.49e-8 | 9.09e-13 | 9.09e-13 |
| open LCDM + radiation: D_M [Mpc] | z=1 | 3239.69149177282 | 3239.69149177282 | 1.36e-12 | 6.56e-05 | pass | propagated + quad 1.49e-8 | 4.55e-13 | 9.09e-13 |
| open LCDM + radiation: D_A [Mpc] | z=1 | 1619.84574588641 | 1619.84574588641 | 6.82e-13 | 3.28e-05 | pass | propagated + quad 1.49e-8 | 2.27e-13 | 4.55e-13 |
| open LCDM + radiation: D_L [Mpc] | z=1 | 6479.38298354564 | 6479.38298354564 | 2.73e-12 | 1.31e-04 | pass | propagated + quad 1.49e-8 | 9.09e-13 | 1.82e-12 |
| open LCDM + radiation: distance modulus | z=1 | 44.0576682549703 | 44.0576682549703 | 0.00e+00 | 4.40e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| open LCDM + radiation: lookback time [Gyr] | z=1 | 7.51571905771772 | 7.51571905771772 | 8.88e-16 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 8.88e-16 |
| open LCDM + radiation: age [Gyr] | z=1 | 5.54136152858875 | 5.54136152858866 | 8.44e-14 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 8.88e-16 | 8.35e-14 |
| open LCDM + radiation: H [km/s/Mpc] | z=1 | 129.093068920338 | 129.093068920338 | 0.00e+00 | 5.89e-13 | pass | 16u x conditioning per side | 0.00e+00 | 0.00e+00 |
| open LCDM + radiation: Omega_m(z) | z=1 | 0.705669701398322 | 0.705669701398323 | 3.33e-16 | 3.34e-15 | pass | 16u x conditioning per side | 1.11e-16 | 2.22e-16 |
| open LCDM + radiation: Omega_de(z) | z=1 | 0.176417425349581 | 0.176417425349581 | 8.33e-17 | 1.46e-15 | pass | 16u x conditioning per side | 2.78e-17 | 5.55e-17 |
| open LCDM + radiation: Omega_k(z) | z=1 | 0.117511198115595 | 0.117511198115595 | 8.33e-17 | 5.56e-16 | pass | 16u x conditioning per side | 0.00e+00 | 8.33e-17 |
| open LCDM + radiation: rho_crit(z) [kg/m^3] | z=1 | 3.1302601445638e-26 | 3.1302601445638e-26 | 1.15e-41 | 2.04e-40 | pass | 16u x conditioning per side | 0.00e+00 | 1.15e-41 |
| open LCDM + radiation: D_C [Mpc] | z=2 | 5000.68513925119 | 5000.68513925119 | 2.73e-12 | 7.45e-05 | pass | engine bound + quad 1.49e-8 | 9.09e-13 | 1.82e-12 |
| open LCDM + radiation: D_M [Mpc] | z=2 | 5114.99363265101 | 5114.99363265102 | 3.64e-12 | 7.96e-05 | pass | propagated + quad 1.49e-8 | 1.82e-12 | 1.82e-12 |
| open LCDM + radiation: D_A [Mpc] | z=2 | 1704.99787755034 | 1704.99787755034 | 1.36e-12 | 2.65e-05 | pass | propagated + quad 1.49e-8 | 6.82e-13 | 6.82e-13 |
| open LCDM + radiation: D_L [Mpc] | z=2 | 15344.980897953 | 15344.9808979531 | 1.09e-11 | 2.39e-04 | pass | propagated + quad 1.49e-8 | 5.46e-12 | 5.46e-12 |
| open LCDM + radiation: distance modulus | z=2 | 45.929831760705 | 45.929831760705 | 0.00e+00 | 3.38e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| open LCDM + radiation: lookback time [Gyr] | z=2 | 9.92620491173462 | 9.92620491173462 | 1.78e-15 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 1.78e-15 |
| open LCDM + radiation: age [Gyr] | z=2 | 3.13087567457185 | 3.13087567457176 | 8.17e-14 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 1.33e-15 | 8.30e-14 |
| open LCDM + radiation: H [km/s/Mpc] | z=2 | 216.956499463893 | 216.956499463893 | 5.68e-14 | 9.82e-13 | pass | 16u x conditioning per side | 5.68e-14 | 0.00e+00 |
| open LCDM + radiation: Omega_m(z) | z=2 | 0.843210039774204 | 0.843210039774204 | 1.11e-16 | 4.08e-15 | pass | 16u x conditioning per side | 0.00e+00 | 1.11e-16 |
| open LCDM + radiation: Omega_de(z) | z=2 | 0.0624600029462373 | 0.0624600029462373 | 1.39e-17 | 5.24e-16 | pass | 16u x conditioning per side | 6.94e-18 | 6.94e-18 |
| open LCDM + radiation: Omega_k(z) | z=2 | 0.0936100103118307 | 0.0936100103118307 | 4.16e-17 | 4.53e-16 | pass | 16u x conditioning per side | 0.00e+00 | 4.16e-17 |
| open LCDM + radiation: rho_crit(z) [kg/m^3] | z=2 | 8.84137703057247e-26 | 8.84137703057246e-26 | 6.89e-41 | 5.85e-40 | pass | 16u x conditioning per side | 2.30e-41 | 4.59e-41 |
| open LCDM + radiation: D_C [Mpc] | z=5 | 7505.03578598131 | 7505.03578598131 | 9.09e-13 | 1.12e-04 | pass | engine bound + quad 1.49e-8 | 9.09e-13 | 1.82e-12 |
| open LCDM + radiation: D_M [Mpc] | z=5 | 7894.75418230619 | 7894.7541823062 | 2.73e-12 | 1.29e-04 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 2.73e-12 |
| open LCDM + radiation: D_A [Mpc] | z=5 | 1315.7923637177 | 1315.7923637177 | 6.82e-13 | 2.16e-05 | pass | propagated + quad 1.49e-8 | 2.27e-13 | 4.55e-13 |
| open LCDM + radiation: D_L [Mpc] | z=5 | 47368.5250938372 | 47368.5250938372 | 1.46e-11 | 7.77e-04 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 1.46e-11 |
| open LCDM + radiation: distance modulus | z=5 | 48.3774493119045 | 48.3774493119045 | 0.00e+00 | 3.56e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| open LCDM + radiation: lookback time [Gyr] | z=5 | 11.9233447551772 | 11.9233447551772 | 1.78e-15 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 1.78e-15 | 0.00e+00 |
| open LCDM + radiation: age [Gyr] | z=5 | 1.13373583112926 | 1.13373583112918 | 8.48e-14 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 8.48e-14 |
| open LCDM + radiation: H [km/s/Mpc] | z=5 | 581.916786614252 | 581.916786614252 | 2.27e-13 | 2.68e-12 | pass | 16u x conditioning per side | 0.00e+00 | 2.27e-13 |
| open LCDM + radiation: Omega_m(z) | z=5 | 0.937668474725347 | 0.937668474725348 | 6.66e-16 | 4.97e-15 | pass | 16u x conditioning per side | 1.11e-16 | 5.55e-16 |
| open LCDM + radiation: Omega_de(z) | z=5 | 0.00868211550671617 | 0.00868211550671618 | 8.67e-18 | 7.69e-17 | pass | 16u x conditioning per side | 1.73e-18 | 6.94e-18 |
| open LCDM + radiation: Omega_k(z) | z=5 | 0.0520482154195073 | 0.0520482154195074 | 6.25e-17 | 2.76e-16 | pass | 16u x conditioning per side | 1.39e-17 | 4.86e-17 |
| open LCDM + radiation: rho_crit(z) [kg/m^3] | z=5 | 6.36057461975902e-25 | 6.36057461975901e-25 | 8.27e-40 | 4.50e-39 | pass | 16u x conditioning per side | 9.18e-41 | 7.35e-40 |
| open LCDM + radiation: D_C [Mpc] | z=10 | 9134.80468221691 | 9134.80468221691 | 3.64e-12 | 1.36e-04 | pass | engine bound + quad 1.49e-8 | 1.82e-12 | 1.82e-12 |
| open LCDM + radiation: D_M [Mpc] | z=10 | 9842.74280717966 | 9842.74280717966 | 3.64e-12 | 1.68e-04 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 3.64e-12 |
| open LCDM + radiation: D_A [Mpc] | z=10 | 894.794800652696 | 894.794800652697 | 3.41e-13 | 1.53e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 3.41e-13 |
| open LCDM + radiation: D_L [Mpc] | z=10 | 108270.170878976 | 108270.170878976 | 2.91e-11 | 1.85e-03 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 2.91e-11 |
| open LCDM + radiation: distance modulus | z=10 | 50.1725441110566 | 50.1725441110566 | 0.00e+00 | 3.71e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| open LCDM + radiation: lookback time [Gyr] | z=10 | 12.5973329480497 | 12.5973329480497 | 0.00e+00 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 1.78e-15 | 1.78e-15 |
| open LCDM + radiation: age [Gyr] | z=10 | 0.459747638256765 | 0.459747638256679 | 8.60e-14 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 8.60e-14 |
| open LCDM + radiation: H [km/s/Mpc] | z=10 | 1422.98093323766 | 1422.98093323766 | 6.82e-13 | 7.20e-12 | pass | 16u x conditioning per side | 0.00e+00 | 6.82e-13 |
| open LCDM + radiation: Omega_m(z) | z=10 | 0.966267179331403 | 0.966267179331405 | 1.11e-15 | 6.15e-15 | pass | 16u x conditioning per side | 0.00e+00 | 1.11e-15 |
| open LCDM + radiation: Omega_de(z) | z=10 | 0.00145194166691421 | 0.00145194166691421 | 1.30e-18 | 1.44e-17 | pass | 16u x conditioning per side | 2.17e-19 | 1.52e-18 |
| open LCDM + radiation: Omega_k(z) | z=10 | 0.0292558231545566 | 0.0292558231545567 | 4.16e-17 | 1.86e-16 | pass | 16u x conditioning per side | 0.00e+00 | 4.16e-17 |
| open LCDM + radiation: rho_crit(z) [kg/m^3] | z=10 | 3.80340648637768e-24 | 3.80340648637768e-24 | 5.14e-39 | 3.10e-38 | pass | 16u x conditioning per side | 7.35e-40 | 4.41e-39 |
| open LCDM + radiation: D_C [Mpc] | z=100 | 12256.1589647207 | 12256.1589647207 | 1.09e-11 | 1.83e-04 | pass | engine bound + quad 1.49e-8 | 1.82e-12 | 9.09e-12 |
| open LCDM + radiation: D_M [Mpc] | z=100 | 13997.34964044 | 13997.34964044 | 1.64e-11 | 2.63e-04 | pass | propagated + quad 1.49e-8 | 3.64e-12 | 1.27e-11 |
| open LCDM + radiation: D_A [Mpc] | z=100 | 138.587620202376 | 138.587620202376 | 1.71e-13 | 2.60e-06 | pass | propagated + quad 1.49e-8 | 2.84e-14 | 1.42e-13 |
| open LCDM + radiation: D_L [Mpc] | z=100 | 1413732.31368444 | 1413732.31368444 | 1.63e-09 | 2.65e-02 | pass | propagated + quad 1.49e-8 | 4.66e-10 | 1.16e-09 |
| open LCDM + radiation: distance modulus | z=100 | 55.7518359239123 | 55.7518359239123 | 0.00e+00 | 4.07e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| open LCDM + radiation: lookback time [Gyr] | z=100 | 13.0409204533805 | 13.0409204533805 | 5.33e-15 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 5.33e-15 |
| open LCDM + radiation: age [Gyr] | z=100 | 0.0161601329259708 | 0.0161601329258587 | 1.12e-13 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 1.12e-13 |
| open LCDM + radiation: H [km/s/Mpc] | z=100 | 39535.7485136746 | 39535.7485136743 | 2.33e-10 | 6.15e-10 | pass | 16u x conditioning per side | 0.00e+00 | 2.33e-10 |
| open LCDM + radiation: Omega_m(z) | z=100 | 0.968950352485001 | 0.968950352485013 | 1.13e-14 | 2.67e-14 | pass | 16u x conditioning per side | 2.22e-16 | 1.15e-14 |
| open LCDM + radiation: Omega_de(z) | z=100 | 1.88090733190592e-06 | 1.88090733190594e-06 | 2.16e-20 | 5.85e-20 | pass | 16u x conditioning per side | 6.35e-22 | 2.22e-20 |
| open LCDM + radiation: Omega_k(z) | z=100 | 0.00319512556539746 | 0.00319512556539749 | 3.86e-17 | 8.80e-17 | pass | 16u x conditioning per side | 8.67e-19 | 3.95e-17 |
| open LCDM + radiation: rho_crit(z) [kg/m^3] | z=100 | 2.93598959401564e-21 | 2.93598959401561e-21 | 3.65e-35 | 8.61e-35 | pass | 16u x conditioning per side | 0.00e+00 | 3.65e-35 |
| open LCDM + radiation: D_C [Mpc] | z=1000 | 13273.400793205 | 13273.400793205 | 2.55e-11 | 1.98e-04 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 2.55e-11 |
| open LCDM + radiation: D_M [Mpc] | z=1000 | 15500.7843065667 | 15500.7843065667 | 4.18e-11 | 3.01e-04 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 4.18e-11 |
| open LCDM + radiation: D_A [Mpc] | z=1000 | 15.4852990075591 | 15.4852990075592 | 4.26e-14 | 3.00e-07 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 4.26e-14 |
| open LCDM + radiation: D_L [Mpc] | z=1000 | 15516285.0908732 | 15516285.0908733 | 4.10e-08 | 3.01e-01 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 4.10e-08 |
| open LCDM + radiation: distance modulus | z=1000 | 60.9539387528921 | 60.9539387528921 | 7.11e-15 | 4.21e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 7.11e-15 |
| open LCDM + radiation: lookback time [Gyr] | z=1000 | 13.0566555537236 | 13.0566555537236 | 8.88e-15 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 8.88e-15 |
| open LCDM + radiation: age [Gyr] | z=1000 | 0.00042503258288028 | 0.000425032388264881 | 1.95e-10 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 1.63e-19 | 1.95e-10 |
| open LCDM + radiation: H [km/s/Mpc] | z=1000 | 1376572.27970907 | 1376572.279709 | 6.54e-08 | 1.36e-07 | pass | 16u x conditioning per side | 2.33e-10 | 6.52e-08 |
| open LCDM + radiation: Omega_m(z) | z=1000 | 0.778075118432581 | 0.778075118432655 | 7.41e-14 | 1.51e-13 | pass | 16u x conditioning per side | 1.11e-16 | 7.39e-14 |
| open LCDM + radiation: Omega_de(z) | z=1000 | 1.5514911075178e-09 | 1.55149110751794e-09 | 1.48e-22 | 3.07e-22 | pass | 16u x conditioning per side | 2.07e-25 | 1.48e-22 |
| open LCDM + radiation: Omega_k(z) | z=1000 | 0.000258878050203249 | 0.000258878050203274 | 2.47e-17 | 5.03e-17 | pass | 16u x conditioning per side | 0.00e+00 | 2.47e-17 |
| open LCDM + radiation: rho_crit(z) [kg/m^3] | z=1000 | 3.55936577852424e-18 | 3.5593657785239e-18 | 3.40e-31 | 6.98e-31 | pass | 16u x conditioning per side | 0.00e+00 | 3.40e-31 |
| open LCDM + radiation: Omega_gamma0 | today | 5.04688842594712e-05 | 5.04688842594712e-05 | 4.07e-20 | 1.34e-19 | pass | 12 roundings |  |  |
| open LCDM + radiation: Omega_nu0 | today | 3.49128040231764e-05 | 3.49128040231397e-05 | 3.67e-17 | 3.69e-17 | pass | 16 roundings + literal |  |  |
| open LCDM + radiation: T_nu0 [K] (engine / (N_eff/3)^(1/4)) | today | 1.94536883917508 | 1.94536883917508 | 0.00e+00 | 3.47e-15 | pass | 8 roundings |  |  |
| open LCDM + radiation: rho_crit0 [kg/m^3] | today | 9.20387392297252e-27 | 9.20387392297252e-27 | 4.30e-42 | 2.45e-41 | pass | 12 roundings |  |  |
| open LCDM + radiation: hubble distance [Mpc] | today | 4282.7494 | 4282.7494 | 9.09e-13 | 3.80e-12 | pass | 4 roundings |  |  |
| open LCDM + radiation: hubble time [Gyr] | today | 13.9684603097256 | 13.9684603097256 | 1.78e-15 | 2.48e-14 | pass | 8 roundings |  |  |
| open LCDM + radiation: D_A(z1, z2) [Mpc] | z1=0.5, z2=2 | 1058.86005223775 | 1058.86005223775 | 4.55e-13 | 1.05e-04 | pass | propagated + quad 1.49e-8 |  |  |
| open LCDM + radiation: D_A(z1, z2) [Mpc] | z1=1, z2=1100 | 10.0282052331625 | 10.0282052331625 | 3.02e-14 | 1.50e-06 | pass | propagated + quad 1.49e-8 |  |  |
| closed LCDM + radiation: D_C [Mpc] | z=0.001 | 4.28183884170858 | 4.28183884170858 | 8.88e-16 | 6.38e-05 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 8.88e-16 |
| closed LCDM + radiation: D_M [Mpc] | z=0.001 | 4.28183877031404 | 4.28183877031404 | 8.88e-16 | 6.38e-05 | pass | propagated + quad 1.49e-8 | 8.88e-16 | 0.00e+00 |
| closed LCDM + radiation: D_A [Mpc] | z=0.001 | 4.27756120910493 | 4.27756120910493 | 8.88e-16 | 6.37e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 8.88e-16 |
| closed LCDM + radiation: D_L [Mpc] | z=0.001 | 4.28612060908435 | 4.28612060908435 | 8.88e-16 | 6.39e-05 | pass | propagated + quad 1.49e-8 | 8.88e-16 | 0.00e+00 |
| closed LCDM + radiation: distance modulus | z=0.001 | 28.160321938432 | 28.160321938432 | 0.00e+00 | 3.24e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| closed LCDM + radiation: lookback time [Gyr] | z=0.001 | 0.0139585128667858 | 0.0139585128667858 | 1.73e-18 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 1.73e-18 | 3.47e-18 |
| closed LCDM + radiation: age [Gyr] | z=0.001 | 13.2630999480822 | 13.2630999480819 | 2.63e-13 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 1.78e-15 | 2.61e-13 |
| closed LCDM + radiation: H [km/s/Mpc] | z=0.001 | 70.029782918049 | 70.029782918049 | 0.00e+00 | 3.01e-13 | pass | 16u x conditioning per side | 1.42e-14 | 1.42e-14 |
| closed LCDM + radiation: Omega_m(z) | z=0.001 | 0.350752517327074 | 0.350752517327074 | 5.55e-17 | 1.52e-15 | pass | 16u x conditioning per side | 1.11e-16 | 5.55e-17 |
| closed LCDM + radiation: Omega_de(z) | z=0.001 | 0.749362201688412 | 0.749362201688412 | 0.00e+00 | 5.91e-15 | pass | 16u x conditioning per side | 1.11e-16 | 1.11e-16 |
| closed LCDM + radiation: Omega_k(z) | z=0.001 | -0.100200369843888 | -0.100200369843888 | 5.55e-17 | 4.35e-16 | pass | 16u x conditioning per side | 1.39e-17 | 6.94e-17 |
| closed LCDM + radiation: rho_crit(z) [kg/m^3] | z=0.001 | 9.21170753832557e-27 | 9.21170753832557e-27 | 4.30e-42 | 5.63e-41 | pass | 16u x conditioning per side | 1.43e-42 | 5.74e-42 |
| closed LCDM + radiation: D_C [Mpc] | z=0.1 | 418.906770547322 | 418.906770547322 | 5.68e-14 | 6.38e-05 | pass | engine bound + quad 1.49e-8 | 5.68e-14 | 0.00e+00 |
| closed LCDM + radiation: D_M [Mpc] | z=0.1 | 418.839919930368 | 418.839919930368 | 5.68e-14 | 6.38e-05 | pass | propagated + quad 1.49e-8 | 5.68e-14 | 0.00e+00 |
| closed LCDM + radiation: D_A [Mpc] | z=0.1 | 380.763563573062 | 380.763563573062 | 5.68e-14 | 5.80e-05 | pass | propagated + quad 1.49e-8 | 5.68e-14 | 0.00e+00 |
| closed LCDM + radiation: D_L [Mpc] | z=0.1 | 460.723911923405 | 460.723911923405 | 5.68e-14 | 7.02e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 5.68e-14 |
| closed LCDM + radiation: distance modulus | z=0.1 | 38.317203765267 | 38.317203765267 | 0.00e+00 | 3.31e-07 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| closed LCDM + radiation: lookback time [Gyr] | z=0.1 | 1.3026831368897 | 1.3026831368897 | 0.00e+00 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 2.22e-16 | 2.22e-16 |
| closed LCDM + radiation: age [Gyr] | z=0.1 | 11.9743753240592 | 11.974375324059 | 2.59e-13 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 2.59e-13 |
| closed LCDM + radiation: H [km/s/Mpc] | z=0.1 | 73.2452818131398 | 73.2452818131398 | 0.00e+00 | 3.21e-13 | pass | 16u x conditioning per side | 0.00e+00 | 0.00e+00 |
| closed LCDM + radiation: Omega_m(z) | z=0.1 | 0.425483645179806 | 0.425483645179806 | 5.55e-17 | 1.89e-15 | pass | 16u x conditioning per side | 0.00e+00 | 5.55e-17 |
| closed LCDM + radiation: Omega_de(z) | z=0.1 | 0.68501177178245 | 0.68501177178245 | 0.00e+00 | 5.47e-15 | pass | 16u x conditioning per side | 1.11e-16 | 1.11e-16 |
| closed LCDM + radiation: Omega_k(z) | z=0.1 | -0.110609592285565 | -0.110609592285565 | 5.55e-17 | 4.91e-16 | pass | 16u x conditioning per side | 0.00e+00 | 5.55e-17 |
| closed LCDM + radiation: rho_crit(z) [kg/m^3] | z=0.1 | 1.00770610470934e-26 | 1.00770610470934e-26 | 4.30e-42 | 6.26e-41 | pass | 16u x conditioning per side | 1.43e-42 | 2.87e-42 |
| closed LCDM + radiation: D_C [Mpc] | z=0.5 | 1893.29145727213 | 1893.29145727213 | 0.00e+00 | 6.38e-05 | pass | engine bound + quad 1.49e-8 | 2.27e-13 | 2.27e-13 |
| closed LCDM + radiation: D_M [Mpc] | z=0.5 | 1887.12548229421 | 1887.12548229421 | 2.27e-13 | 6.32e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 2.27e-13 |
| closed LCDM + radiation: D_A [Mpc] | z=0.5 | 1258.0836548628 | 1258.08365486281 | 2.27e-13 | 4.21e-05 | pass | propagated + quad 1.49e-8 | 2.27e-13 | 0.00e+00 |
| closed LCDM + radiation: D_L [Mpc] | z=0.5 | 2830.68822344131 | 2830.68822344131 | 0.00e+00 | 9.48e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| closed LCDM + radiation: distance modulus | z=0.5 | 42.2594601905283 | 42.2594601905283 | 0.00e+00 | 7.27e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| closed LCDM + radiation: lookback time [Gyr] | z=0.5 | 5.05275972464093 | 5.05275972464093 | 8.88e-16 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 8.88e-16 |
| closed LCDM + radiation: age [Gyr] | z=0.5 | 8.22429873630801 | 8.22429873630775 | 2.58e-13 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 1.78e-15 | 2.59e-13 |
| closed LCDM + radiation: H [km/s/Mpc] | z=0.5 | 91.4428874565521 | 91.4428874565521 | 0.00e+00 | 4.21e-13 | pass | 16u x conditioning per side | 0.00e+00 | 0.00e+00 |
| closed LCDM + radiation: Omega_m(z) | z=0.5 | 0.69221027129405 | 0.69221027129405 | 1.11e-16 | 3.26e-15 | pass | 16u x conditioning per side | 0.00e+00 | 1.11e-16 |
| closed LCDM + radiation: Omega_de(z) | z=0.5 | 0.439498584948603 | 0.439498584948603 | 1.11e-16 | 3.63e-15 | pass | 16u x conditioning per side | 1.11e-16 | 0.00e+00 |
| closed LCDM + radiation: Omega_k(z) | z=0.5 | -0.131962150878123 | -0.131962150878123 | 5.55e-17 | 6.21e-16 | pass | 16u x conditioning per side | 0.00e+00 | 5.55e-17 |
| closed LCDM + radiation: rho_crit(z) [kg/m^3] | z=0.5 | 1.57063200625245e-26 | 1.57063200625245e-26 | 5.74e-42 | 1.02e-40 | pass | 16u x conditioning per side | 0.00e+00 | 5.74e-42 |
| closed LCDM + radiation: D_C [Mpc] | z=1 | 3304.85512237367 | 3304.85512237367 | 1.36e-12 | 6.38e-05 | pass | engine bound + quad 1.49e-8 | 4.55e-13 | 9.09e-13 |
| closed LCDM + radiation: D_M [Mpc] | z=1 | 3272.12579279686 | 3272.12579279686 | 1.36e-12 | 6.19e-05 | pass | propagated + quad 1.49e-8 | 9.09e-13 | 4.55e-13 |
| closed LCDM + radiation: D_A [Mpc] | z=1 | 1636.06289639843 | 1636.06289639843 | 6.82e-13 | 3.10e-05 | pass | propagated + quad 1.49e-8 | 4.55e-13 | 2.27e-13 |
| closed LCDM + radiation: D_L [Mpc] | z=1 | 6544.25158559371 | 6544.25158559372 | 2.73e-12 | 1.24e-04 | pass | propagated + quad 1.49e-8 | 1.82e-12 | 9.09e-13 |
| closed LCDM + radiation: distance modulus | z=1 | 44.0792999344707 | 44.0792999344707 | 7.11e-15 | 4.11e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 7.11e-15 |
| closed LCDM + radiation: lookback time [Gyr] | z=1 | 7.72121568358588 | 7.72121568358588 | 1.78e-15 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 1.78e-15 |
| closed LCDM + radiation: age [Gyr] | z=1 | 5.55584277736306 | 5.5558427773628 | 2.59e-13 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 8.88e-16 | 2.58e-13 |
| closed LCDM + radiation: H [km/s/Mpc] | z=1 | 124.257878797568 | 124.257878797568 | 1.42e-14 | 5.77e-13 | pass | 16u x conditioning per side | 0.00e+00 | 1.42e-14 |
| closed LCDM + radiation: Omega_m(z) | z=1 | 0.888599859722295 | 0.888599859722295 | 2.22e-16 | 4.29e-15 | pass | 16u x conditioning per side | 0.00e+00 | 2.22e-16 |
| closed LCDM + radiation: Omega_de(z) | z=1 | 0.238017819568472 | 0.238017819568472 | 5.55e-17 | 1.99e-15 | pass | 16u x conditioning per side | 0.00e+00 | 5.55e-17 |
| closed LCDM + radiation: Omega_k(z) | z=1 | -0.127051223040658 | -0.127051223040658 | 2.78e-17 | 6.13e-16 | pass | 16u x conditioning per side | 0.00e+00 | 2.78e-17 |
| closed LCDM + radiation: rho_crit(z) [kg/m^3] | z=1 | 2.90016329648949e-26 | 2.90016329648948e-26 | 1.72e-41 | 1.92e-40 | pass | 16u x conditioning per side | 0.00e+00 | 1.72e-41 |
| closed LCDM + radiation: D_C [Mpc] | z=2 | 5147.76892522347 | 5147.76892522347 | 2.73e-12 | 7.67e-05 | pass | engine bound + quad 1.49e-8 | 1.82e-12 | 9.09e-13 |
| closed LCDM + radiation: D_M [Mpc] | z=2 | 5024.60294921302 | 5024.60294921302 | 2.73e-12 | 7.12e-05 | pass | propagated + quad 1.49e-8 | 9.09e-13 | 1.82e-12 |
| closed LCDM + radiation: D_A [Mpc] | z=2 | 1674.86764973767 | 1674.86764973767 | 9.09e-13 | 2.37e-05 | pass | propagated + quad 1.49e-8 | 2.27e-13 | 6.82e-13 |
| closed LCDM + radiation: D_L [Mpc] | z=2 | 15073.8088476391 | 15073.8088476391 | 9.09e-12 | 2.14e-04 | pass | propagated + quad 1.49e-8 | 3.64e-12 | 5.46e-12 |
| closed LCDM + radiation: distance modulus | z=2 | 45.8911150182115 | 45.8911150182115 | 0.00e+00 | 3.08e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| closed LCDM + radiation: lookback time [Gyr] | z=2 | 10.2033205310239 | 10.2033205310239 | 1.78e-15 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 3.55e-15 | 1.78e-15 |
| closed LCDM + radiation: age [Gyr] | z=2 | 3.07373792992505 | 3.07373792992479 | 2.60e-13 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 8.88e-16 | 2.61e-13 |
| closed LCDM + radiation: H [km/s/Mpc] | z=2 | 213.541852243597 | 213.541852243597 | 2.84e-14 | 9.74e-13 | pass | 16u x conditioning per side | 2.84e-14 | 0.00e+00 |
| closed LCDM + radiation: Omega_m(z) | z=2 | 1.01545779483172 | 1.01545779483172 | 4.44e-16 | 4.96e-15 | pass | 16u x conditioning per side | 0.00e+00 | 4.44e-16 |
| closed LCDM + radiation: Omega_de(z) | z=2 | 0.0805918884787081 | 0.0805918884787082 | 5.55e-17 | 6.80e-16 | pass | 16u x conditioning per side | 2.78e-17 | 2.78e-17 |
| closed LCDM + radiation: Omega_k(z) | z=2 | -0.0967928390324521 | -0.0967928390324521 | 0.00e+00 | 4.72e-16 | pass | 16u x conditioning per side | 0.00e+00 | 0.00e+00 |
| closed LCDM + radiation: rho_crit(z) [kg/m^3] | z=2 | 8.56526081288329e-26 | 8.56526081288328e-26 | 6.89e-41 | 5.70e-40 | pass | 16u x conditioning per side | 1.15e-41 | 5.74e-41 |
| closed LCDM + radiation: D_C [Mpc] | z=5 | 7638.58558446977 | 7638.58558446978 | 3.64e-12 | 1.14e-04 | pass | engine bound + quad 1.49e-8 | 9.09e-13 | 2.73e-12 |
| closed LCDM + radiation: D_M [Mpc] | z=5 | 7239.65558352813 | 7239.65558352814 | 2.73e-12 | 9.62e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 2.73e-12 |
| closed LCDM + radiation: D_A [Mpc] | z=5 | 1206.60926392136 | 1206.60926392136 | 4.55e-13 | 1.60e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 4.55e-13 |
| closed LCDM + radiation: D_L [Mpc] | z=5 | 43437.9335011688 | 43437.9335011688 | 1.46e-11 | 5.77e-04 | pass | propagated + quad 1.49e-8 | 7.28e-12 | 2.18e-11 |
| closed LCDM + radiation: distance modulus | z=5 | 48.1893457806034 | 48.1893457806034 | 0.00e+00 | 2.88e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| closed LCDM + radiation: lookback time [Gyr] | z=5 | 12.1944822667857 | 12.1944822667858 | 1.78e-15 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 1.78e-15 |
| closed LCDM + radiation: age [Gyr] | z=5 | 1.08257619416319 | 1.08257619416292 | 2.62e-13 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 2.22e-16 | 2.62e-13 |
| closed LCDM + radiation: H [km/s/Mpc] | z=5 | 597.496566135285 | 597.496566135285 | 2.27e-13 | 2.72e-12 | pass | 16u x conditioning per side | 0.00e+00 | 2.27e-13 |
| closed LCDM + radiation: Omega_m(z) | z=5 | 1.03764081977279 | 1.03764081977279 | 6.66e-16 | 5.41e-15 | pass | 16u x conditioning per side | 0.00e+00 | 6.66e-16 |
| closed LCDM + radiation: Omega_de(z) | z=5 | 0.0102940557517142 | 0.0102940557517142 | 1.04e-17 | 9.02e-17 | pass | 16u x conditioning per side | 3.47e-18 | 6.94e-18 |
| closed LCDM + radiation: Omega_k(z) | z=5 | -0.0494536559534774 | -0.0494536559534774 | 2.08e-17 | 2.58e-16 | pass | 16u x conditioning per side | 6.94e-18 | 1.39e-17 |
| closed LCDM + radiation: rho_crit(z) [kg/m^3] | z=5 | 6.70571989187049e-25 | 6.70571989187048e-25 | 8.27e-40 | 4.69e-39 | pass | 16u x conditioning per side | 9.18e-41 | 7.35e-40 |
| closed LCDM + radiation: D_C [Mpc] | z=10 | 9207.30762346889 | 9207.30762346889 | 3.64e-12 | 1.37e-04 | pass | engine bound + quad 1.49e-8 | 1.82e-12 | 1.82e-12 |
| closed LCDM + radiation: D_M [Mpc] | z=10 | 8513.68751457481 | 8513.68751457482 | 3.64e-12 | 1.07e-04 | pass | propagated + quad 1.49e-8 | 1.82e-12 | 1.82e-12 |
| closed LCDM + radiation: D_A [Mpc] | z=10 | 773.971592234074 | 773.971592234074 | 3.41e-13 | 9.70e-06 | pass | propagated + quad 1.49e-8 | 1.14e-13 | 2.27e-13 |
| closed LCDM + radiation: D_L [Mpc] | z=10 | 93650.5626603229 | 93650.562660323 | 4.37e-11 | 1.17e-03 | pass | propagated + quad 1.49e-8 | 1.46e-11 | 2.91e-11 |
| closed LCDM + radiation: distance modulus | z=10 | 49.8575519549812 | 49.8575519549812 | 0.00e+00 | 2.72e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| closed LCDM + radiation: lookback time [Gyr] | z=10 | 12.8439540848203 | 12.8439540848203 | 1.78e-15 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 1.78e-15 |
| closed LCDM + radiation: age [Gyr] | z=10 | 0.433104376128631 | 0.433104376128365 | 2.66e-13 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 5.55e-17 | 2.66e-13 |
| closed LCDM + radiation: H [km/s/Mpc] | z=10 | 1494.36432517574 | 1494.36432517574 | 6.82e-13 | 7.35e-12 | pass | 16u x conditioning per side | 0.00e+00 | 6.82e-13 |
| closed LCDM + radiation: Omega_m(z) | z=10 | 1.02218427964882 | 1.02218427964882 | 1.11e-15 | 6.24e-15 | pass | 16u x conditioning per side | 0.00e+00 | 1.11e-15 |
| closed LCDM + radiation: Omega_de(z) | z=10 | 0.00164567609689088 | 0.00164567609689088 | 1.95e-18 | 1.59e-17 | pass | 16u x conditioning per side | 0.00e+00 | 1.95e-18 |
| closed LCDM + radiation: Omega_k(z) | z=10 | -0.0265729100738739 | -0.0265729100738739 | 1.73e-17 | 1.62e-16 | pass | 16u x conditioning per side | 3.47e-18 | 2.08e-17 |
| closed LCDM + radiation: rho_crit(z) [kg/m^3] | z=10 | 4.19457112810402e-24 | 4.19457112810401e-24 | 5.88e-39 | 3.30e-38 | pass | 16u x conditioning per side | 0.00e+00 | 5.88e-39 |
| closed LCDM + radiation: D_C [Mpc] | z=100 | 12138.0450155875 | 12138.0450155875 | 9.09e-12 | 1.81e-04 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 9.09e-12 |
| closed LCDM + radiation: D_M [Mpc] | z=100 | 10575.8091691418 | 10575.8091691418 | 5.46e-12 | 1.13e-04 | pass | propagated + quad 1.49e-8 | 1.82e-12 | 7.28e-12 |
| closed LCDM + radiation: D_A [Mpc] | z=100 | 104.710981872691 | 104.710981872691 | 4.26e-14 | 1.12e-06 | pass | propagated + quad 1.49e-8 | 1.42e-14 | 5.68e-14 |
| closed LCDM + radiation: D_L [Mpc] | z=100 | 1068156.72608332 | 1068156.72608332 | 4.66e-10 | 1.14e-02 | pass | propagated + quad 1.49e-8 | 2.33e-10 | 6.98e-10 |
| closed LCDM + radiation: distance modulus | z=100 | 55.1431748977298 | 55.1431748977298 | 0.00e+00 | 2.32e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| closed LCDM + radiation: lookback time [Gyr] | z=100 | 13.262002247806 | 13.262002247806 | 5.33e-15 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 1.78e-15 | 3.55e-15 |
| closed LCDM + radiation: age [Gyr] | z=100 | 0.0150562131429184 | 0.0150562131425904 | 3.28e-13 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 1.73e-18 | 3.28e-13 |
| closed LCDM + radiation: H [km/s/Mpc] | z=100 | 42491.2098031642 | 42491.209803164 | 2.26e-10 | 5.93e-10 | pass | 16u x conditioning per side | 7.28e-12 | 2.18e-10 |
| closed LCDM + radiation: Omega_m(z) | z=100 | 0.97865597706233 | 0.97865597706234 | 9.88e-15 | 2.38e-14 | pass | 16u x conditioning per side | 1.11e-16 | 9.99e-15 |
| closed LCDM + radiation: Omega_de(z) | z=100 | 2.03544396331543e-06 | 2.03544396331545e-06 | 2.08e-20 | 5.67e-20 | pass | 16u x conditioning per side | 0.00e+00 | 2.08e-20 |
| closed LCDM + radiation: Omega_k(z) | z=100 | -0.00277083895348805 | -0.00277083895348808 | 2.73e-17 | 6.74e-17 | pass | 16u x conditioning per side | 0.00e+00 | 2.73e-17 |
| closed LCDM + radiation: rho_crit(z) [kg/m^3] | z=100 | 3.39135125635471e-21 | 3.39135125635467e-21 | 3.69e-35 | 8.85e-35 | pass | 16u x conditioning per side | 0.00e+00 | 3.69e-35 |
| closed LCDM + radiation: D_C [Mpc] | z=1000 | 13086.5040648501 | 13086.5040648501 | 3.64e-11 | 1.95e-04 | pass | engine bound + quad 1.49e-8 | 1.82e-12 | 3.46e-11 |
| closed LCDM + radiation: D_M [Mpc] | z=1000 | 11141.4538691766 | 11141.4538691767 | 2.00e-11 | 1.11e-04 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 2.00e-11 |
| closed LCDM + radiation: D_A [Mpc] | z=1000 | 11.130323545631 | 11.130323545631 | 2.13e-14 | 1.11e-07 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 2.13e-14 |
| closed LCDM + radiation: D_L [Mpc] | z=1000 | 11152595.3230458 | 11152595.3230458 | 2.05e-08 | 1.11e-01 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 2.05e-08 |
| closed LCDM + radiation: distance modulus | z=1000 | 60.2368797195754 | 60.2368797195754 | 7.11e-15 | 2.16e-08 | pass | propagated + quad 1.49e-8 | 7.11e-15 | 0.00e+00 |
| closed LCDM + radiation: lookback time [Gyr] | z=1000 | 13.2766548494574 | 13.2766548494575 | 5.86e-14 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 5.86e-14 |
| closed LCDM + radiation: age [Gyr] | z=1000 | 0.000403611491540025 | 0.00040944270561754 | 5.83e-06 | 2.08e-07 | xfail | engine bound + quad 1.49e-8 | 1.08e-19 | 5.83e-06 |
| closed LCDM + radiation: H [km/s/Mpc] | z=1000 | 1462773.05699258 | 1462773.05699252 | 6.15e-08 | 1.29e-07 | pass | 16u x conditioning per side | 2.33e-10 | 6.17e-08 |
| closed LCDM + radiation: Omega_m(z) | z=1000 | 0.803919294314181 | 0.803919294314249 | 6.79e-14 | 1.39e-13 | pass | 16u x conditioning per side | 0.00e+00 | 6.79e-14 |
| closed LCDM + radiation: Omega_de(z) | z=1000 | 1.71752646839969e-09 | 1.71752646839983e-09 | 1.45e-22 | 3.02e-22 | pass | 16u x conditioning per side | 0.00e+00 | 1.45e-22 |
| closed LCDM + radiation: Omega_k(z) | z=1000 | -0.000229657683510803 | -0.000229657683510822 | 1.93e-17 | 3.96e-17 | pass | 16u x conditioning per side | 0.00e+00 | 1.93e-17 |
| closed LCDM + radiation: rho_crit(z) [kg/m^3] | z=1000 | 4.01909698000824e-18 | 4.0190969800079e-18 | 3.41e-31 | 7.00e-31 | pass | 16u x conditioning per side | 0.00e+00 | 3.41e-31 |
| closed LCDM + radiation: Omega_gamma0 | today | 5.04688842594712e-05 | 5.04688842594712e-05 | 4.07e-20 | 1.34e-19 | pass | 12 roundings |  |  |
| closed LCDM + radiation: Omega_nu0 | today | 3.49128040231764e-05 | 3.49128040231397e-05 | 3.67e-17 | 3.69e-17 | pass | 16 roundings + literal |  |  |
| closed LCDM + radiation: T_nu0 [K] (engine / (N_eff/3)^(1/4)) | today | 1.94536883917508 | 1.94536883917508 | 0.00e+00 | 3.47e-15 | pass | 8 roundings |  |  |
| closed LCDM + radiation: rho_crit0 [kg/m^3] | today | 9.20387392297252e-27 | 9.20387392297252e-27 | 4.30e-42 | 2.45e-41 | pass | 12 roundings |  |  |
| closed LCDM + radiation: hubble distance [Mpc] | today | 4282.7494 | 4282.7494 | 9.09e-13 | 3.80e-12 | pass | 4 roundings |  |  |
| closed LCDM + radiation: hubble time [Gyr] | today | 13.9684603097256 | 13.9684603097256 | 1.78e-15 | 2.48e-14 | pass | 8 roundings |  |  |
| flat w0wa + radiation: D_C [Mpc] | z=0.001 | 4.2815605189713 | 4.2815605189713 | 8.88e-16 | 6.38e-05 | pass | engine bound + quad 1.49e-8 | 8.88e-16 | 0.00e+00 |
| flat w0wa + radiation: D_M [Mpc] | z=0.001 | 4.2815605189713 | 4.2815605189713 | 8.88e-16 | 6.38e-05 | pass | propagated + quad 1.49e-8 | 8.88e-16 | 0.00e+00 |
| flat w0wa + radiation: D_A [Mpc] | z=0.001 | 4.27728323573557 | 4.27728323573557 | 0.00e+00 | 6.37e-05 | pass | propagated + quad 1.49e-8 | 8.88e-16 | 8.88e-16 |
| flat w0wa + radiation: D_L [Mpc] | z=0.001 | 4.28584207949027 | 4.28584207949028 | 8.88e-16 | 6.39e-05 | pass | propagated + quad 1.49e-8 | 8.88e-16 | 0.00e+00 |
| flat w0wa + radiation: distance modulus | z=0.001 | 28.1601808227154 | 28.1601808227154 | 0.00e+00 | 3.24e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| flat w0wa + radiation: lookback time [Gyr] | z=0.001 | 0.0139576057040948 | 0.0139576057040948 | 3.47e-18 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 3.47e-18 |
| flat w0wa + radiation: age [Gyr] | z=0.001 | 13.1078092102762 | 13.1078092102761 | 8.35e-14 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 8.35e-14 |
| flat w0wa + radiation: H [km/s/Mpc] | z=0.001 | 70.0388865549864 | 70.0388865549864 | 0.00e+00 | 2.51e-13 | pass | 16u x conditioning per side | 1.42e-14 | 1.42e-14 |
| flat w0wa + radiation: Omega_m(z) | z=0.001 | 0.300566864403592 | 0.300566864403592 | 0.00e+00 | 1.09e-15 | pass | 16u x conditioning per side | 5.55e-17 | 5.55e-17 |
| flat w0wa + radiation: Omega_de(z) | z=0.001 | 0.699347507032305 | 0.699347507032305 | 1.11e-16 | 5.02e-15 | pass | 16u x conditioning per side | 0.00e+00 | 1.11e-16 |
| flat w0wa + radiation: rho_crit(z) [kg/m^3] | z=0.001 | 9.2141026761732e-27 | 9.2141026761732e-27 | 4.30e-42 | 4.98e-41 | pass | 16u x conditioning per side | 1.43e-42 | 5.74e-42 |
| flat w0wa + radiation: D_C [Mpc] | z=0.1 | 416.343583111148 | 416.343583111148 | 5.68e-14 | 6.38e-05 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 5.68e-14 |
| flat w0wa + radiation: D_M [Mpc] | z=0.1 | 416.343583111148 | 416.343583111148 | 5.68e-14 | 6.38e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 5.68e-14 |
| flat w0wa + radiation: D_A [Mpc] | z=0.1 | 378.49416646468 | 378.49416646468 | 0.00e+00 | 5.80e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| flat w0wa + radiation: D_L [Mpc] | z=0.1 | 457.977941422263 | 457.977941422263 | 5.68e-14 | 7.02e-05 | pass | propagated + quad 1.49e-8 | 5.68e-14 | 1.14e-13 |
| flat w0wa + radiation: distance modulus | z=0.1 | 38.3042228032366 | 38.3042228032366 | 0.00e+00 | 3.33e-07 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| flat w0wa + radiation: lookback time [Gyr] | z=0.1 | 1.29483625295925 | 1.29483625295925 | 2.22e-16 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 2.22e-16 | 0.00e+00 |
| flat w0wa + radiation: age [Gyr] | z=0.1 | 11.8269305630211 | 11.826930563021 | 8.70e-14 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 1.78e-15 | 8.53e-14 |
| flat w0wa + radiation: H [km/s/Mpc] | z=0.1 | 74.1321328600839 | 74.1321328600839 | 0.00e+00 | 2.67e-13 | pass | 16u x conditioning per side | 0.00e+00 | 0.00e+00 |
| flat w0wa + radiation: Omega_m(z) | z=0.1 | 0.356026561093382 | 0.356026561093382 | 0.00e+00 | 1.30e-15 | pass | 16u x conditioning per side | 0.00e+00 | 0.00e+00 |
| flat w0wa + radiation: Omega_de(z) | z=0.1 | 0.643861979027466 | 0.643861979027466 | 1.11e-16 | 4.64e-15 | pass | 16u x conditioning per side | 0.00e+00 | 1.11e-16 |
| flat w0wa + radiation: rho_crit(z) [kg/m^3] | z=0.1 | 1.03225637046754e-26 | 1.03225637046753e-26 | 5.74e-42 | 5.60e-41 | pass | 16u x conditioning per side | 0.00e+00 | 5.74e-42 |
| flat w0wa + radiation: D_C [Mpc] | z=0.5 | 1851.26482974061 | 1851.26482974061 | 6.82e-13 | 6.38e-05 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 6.82e-13 |
| flat w0wa + radiation: D_M [Mpc] | z=0.5 | 1851.26482974061 | 1851.26482974061 | 6.82e-13 | 6.38e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 6.82e-13 |
| flat w0wa + radiation: D_A [Mpc] | z=0.5 | 1234.17655316041 | 1234.17655316041 | 4.55e-13 | 4.25e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 4.55e-13 |
| flat w0wa + radiation: D_L [Mpc] | z=0.5 | 2776.89724461092 | 2776.89724461092 | 9.09e-13 | 9.57e-05 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 9.09e-13 |
| flat w0wa + radiation: distance modulus | z=0.5 | 42.2177990477896 | 42.2177990477896 | 0.00e+00 | 7.49e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| flat w0wa + radiation: lookback time [Gyr] | z=0.5 | 4.94693972898229 | 4.94693972898229 | 8.88e-16 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 8.88e-16 | 1.78e-15 |
| flat w0wa + radiation: age [Gyr] | z=0.5 | 8.17482708699802 | 8.17482708699793 | 8.17e-14 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 8.17e-14 |
| flat w0wa + radiation: H [km/s/Mpc] | z=0.5 | 94.9097662381526 | 94.9097662381526 | 1.42e-14 | 3.47e-13 | pass | 16u x conditioning per side | 0.00e+00 | 1.42e-14 |
| flat w0wa + radiation: Omega_m(z) | z=0.5 | 0.5507687671739 | 0.5507687671739 | 0.00e+00 | 2.07e-15 | pass | 16u x conditioning per side | 0.00e+00 | 0.00e+00 |
| flat w0wa + radiation: Omega_de(z) | z=0.5 | 0.448996104990126 | 0.448996104990127 | 1.67e-16 | 3.28e-15 | pass | 16u x conditioning per side | 1.11e-16 | 5.55e-17 |
| flat w0wa + radiation: rho_crit(z) [kg/m^3] | z=0.5 | 1.6919845318802e-26 | 1.6919845318802e-26 | 8.61e-42 | 9.36e-41 | pass | 16u x conditioning per side | 2.87e-42 | 5.74e-42 |
| flat w0wa + radiation: D_C [Mpc] | z=1 | 3211.08320272457 | 3211.08320272457 | 1.36e-12 | 6.38e-05 | pass | engine bound + quad 1.49e-8 | 4.55e-13 | 9.09e-13 |
| flat w0wa + radiation: D_M [Mpc] | z=1 | 3211.08320272457 | 3211.08320272457 | 1.36e-12 | 6.38e-05 | pass | propagated + quad 1.49e-8 | 4.55e-13 | 9.09e-13 |
| flat w0wa + radiation: D_A [Mpc] | z=1 | 1605.54160136229 | 1605.54160136229 | 6.82e-13 | 3.19e-05 | pass | propagated + quad 1.49e-8 | 2.27e-13 | 4.55e-13 |
| flat w0wa + radiation: D_L [Mpc] | z=1 | 6422.16640544914 | 6422.16640544914 | 2.73e-12 | 1.28e-04 | pass | propagated + quad 1.49e-8 | 9.09e-13 | 1.82e-12 |
| flat w0wa + radiation: distance modulus | z=1 | 44.0384077721381 | 44.0384077721381 | 0.00e+00 | 4.32e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| flat w0wa + radiation: lookback time [Gyr] | z=1 | 7.5173384938192 | 7.5173384938192 | 1.78e-15 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 1.78e-15 |
| flat w0wa + radiation: age [Gyr] | z=1 | 5.60442832216111 | 5.60442832216103 | 8.44e-14 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 8.88e-16 | 8.35e-14 |
| flat w0wa + radiation: H [km/s/Mpc] | z=1 | 128.482688909602 | 128.482688909602 | 0.00e+00 | 4.79e-13 | pass | 16u x conditioning per side | 0.00e+00 | 0.00e+00 |
| flat w0wa + radiation: Omega_m(z) | z=1 | 0.712390448071258 | 0.712390448071258 | 0.00e+00 | 2.78e-15 | pass | 16u x conditioning per side | 0.00e+00 | 0.00e+00 |
| flat w0wa + radiation: Omega_de(z) | z=1 | 0.28720405126759 | 0.28720405126759 | 5.55e-17 | 2.14e-15 | pass | 16u x conditioning per side | 0.00e+00 | 5.55e-17 |
| flat w0wa + radiation: rho_crit(z) [kg/m^3] | z=1 | 3.10072902787216e-26 | 3.10072902787216e-26 | 1.72e-41 | 1.76e-40 | pass | 16u x conditioning per side | 0.00e+00 | 1.72e-41 |
| flat w0wa + radiation: D_C [Mpc] | z=2 | 5018.05604229129 | 5018.05604229129 | 1.82e-12 | 7.48e-05 | pass | engine bound + quad 1.49e-8 | 9.09e-13 | 9.09e-13 |
| flat w0wa + radiation: D_M [Mpc] | z=2 | 5018.05604229129 | 5018.05604229129 | 1.82e-12 | 7.48e-05 | pass | propagated + quad 1.49e-8 | 9.09e-13 | 9.09e-13 |
| flat w0wa + radiation: D_A [Mpc] | z=2 | 1672.68534743043 | 1672.68534743043 | 6.82e-13 | 2.49e-05 | pass | propagated + quad 1.49e-8 | 4.55e-13 | 2.27e-13 |
| flat w0wa + radiation: D_L [Mpc] | z=2 | 15054.1681268739 | 15054.1681268739 | 5.46e-12 | 2.24e-04 | pass | propagated + quad 1.49e-8 | 1.82e-12 | 3.64e-12 |
| flat w0wa + radiation: distance modulus | z=2 | 45.8882838099081 | 45.8882838099081 | 0.00e+00 | 3.24e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| flat w0wa + radiation: lookback time [Gyr] | z=2 | 9.94854249613476 | 9.94854249613476 | 1.78e-15 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 1.78e-15 | 0.00e+00 |
| flat w0wa + radiation: age [Gyr] | z=2 | 3.17322431984554 | 3.17322431984546 | 8.22e-14 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 1.33e-15 | 8.35e-14 |
| flat w0wa + radiation: H [km/s/Mpc] | z=2 | 214.250067083078 | 214.250067083077 | 5.68e-14 | 8.29e-13 | pass | 16u x conditioning per side | 2.84e-14 | 2.84e-14 |
| flat w0wa + radiation: Omega_m(z) | z=2 | 0.864647650592246 | 0.864647650592246 | 1.11e-16 | 3.62e-15 | pass | 16u x conditioning per side | 0.00e+00 | 1.11e-16 |
| flat w0wa + radiation: Omega_de(z) | z=2 | 0.134614098645982 | 0.134614098645982 | 5.55e-17 | 1.04e-15 | pass | 16u x conditioning per side | 2.78e-17 | 2.78e-17 |
| flat w0wa + radiation: rho_crit(z) [kg/m^3] | z=2 | 8.62216866315579e-26 | 8.62216866315579e-26 | 6.89e-41 | 5.14e-40 | pass | 16u x conditioning per side | 2.30e-41 | 4.59e-41 |
| flat w0wa + radiation: D_C [Mpc] | z=5 | 7559.99492792483 | 7559.99492792481 | 2.09e-11 | 1.13e-04 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 2.09e-11 |
| flat w0wa + radiation: D_M [Mpc] | z=5 | 7559.99492792483 | 7559.99492792481 | 2.09e-11 | 1.13e-04 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 2.09e-11 |
| flat w0wa + radiation: D_A [Mpc] | z=5 | 1259.99915465414 | 1259.99915465414 | 3.41e-12 | 1.88e-05 | pass | propagated + quad 1.49e-8 | 2.27e-13 | 3.64e-12 |
| flat w0wa + radiation: D_L [Mpc] | z=5 | 45359.969567549 | 45359.9695675489 | 1.24e-10 | 6.76e-04 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 1.24e-10 |
| flat w0wa + radiation: distance modulus | z=5 | 48.2833637725625 | 48.2833637725625 | 0.00e+00 | 3.24e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| flat w0wa + radiation: lookback time [Gyr] | z=5 | 11.9753460921546 | 11.9753460921542 | 4.69e-13 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 4.69e-13 |
| flat w0wa + radiation: age [Gyr] | z=5 | 1.14642072382566 | 1.14642072382558 | 8.44e-14 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 2.22e-16 | 8.46e-14 |
| flat w0wa + radiation: H [km/s/Mpc] | z=5 | 573.145451060751 | 573.145451060751 | 2.27e-13 | 2.44e-12 | pass | 16u x conditioning per side | 0.00e+00 | 2.27e-13 |
| flat w0wa + radiation: Omega_m(z) | z=5 | 0.966587971160834 | 0.966587971160835 | 6.66e-16 | 4.81e-15 | pass | 16u x conditioning per side | 1.11e-16 | 5.55e-16 |
| flat w0wa + radiation: Omega_de(z) | z=5 | 0.0317614505821377 | 0.0317614505821378 | 2.78e-17 | 2.71e-16 | pass | 16u x conditioning per side | 1.39e-17 | 1.39e-17 |
| flat w0wa + radiation: rho_crit(z) [kg/m^3] | z=5 | 6.17027159454874e-25 | 6.17027159454874e-25 | 8.27e-40 | 4.16e-39 | pass | 16u x conditioning per side | 9.18e-41 | 7.35e-40 |
| flat w0wa + radiation: D_C [Mpc] | z=10 | 9211.86210905441 | 9211.86210905439 | 2.00e-11 | 1.37e-04 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 2.00e-11 |
| flat w0wa + radiation: D_M [Mpc] | z=10 | 9211.86210905441 | 9211.86210905439 | 2.00e-11 | 1.37e-04 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 2.00e-11 |
| flat w0wa + radiation: D_A [Mpc] | z=10 | 837.442009914037 | 837.442009914035 | 1.82e-12 | 1.25e-05 | pass | propagated + quad 1.49e-8 | 1.14e-13 | 1.71e-12 |
| flat w0wa + radiation: D_L [Mpc] | z=10 | 101330.483199598 | 101330.483199598 | 2.18e-10 | 1.51e-03 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 2.18e-10 |
| flat w0wa + radiation: distance modulus | z=10 | 50.0287005680592 | 50.0287005680592 | 7.11e-15 | 3.24e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 7.11e-15 |
| flat w0wa + radiation: lookback time [Gyr] | z=10 | 12.6586085759288 | 12.6586085759284 | 4.69e-13 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 4.69e-13 |
| flat w0wa + radiation: age [Gyr] | z=10 | 0.463158240051465 | 0.463158240051379 | 8.62e-14 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 5.55e-17 | 8.61e-14 |
| flat w0wa + radiation: H [km/s/Mpc] | z=10 | 1407.08864578374 | 1407.08864578374 | 1.14e-12 | 6.87e-12 | pass | 16u x conditioning per side | 2.27e-13 | 9.09e-13 |
| flat w0wa + radiation: Omega_m(z) | z=10 | 0.988217346697785 | 0.988217346697786 | 1.22e-15 | 6.14e-15 | pass | 16u x conditioning per side | 1.11e-16 | 1.11e-15 |
| flat w0wa + radiation: Omega_de(z) | z=10 | 0.00868887890233594 | 0.00868887890233595 | 1.04e-17 | 8.49e-17 | pass | 16u x conditioning per side | 1.73e-18 | 8.67e-18 |
| flat w0wa + radiation: rho_crit(z) [kg/m^3] | z=10 | 3.71892566926053e-24 | 3.71892566926053e-24 | 5.88e-39 | 2.97e-38 | pass | 16u x conditioning per side | 0.00e+00 | 5.88e-39 |
| flat w0wa + radiation: D_C [Mpc] | z=100 | 12352.2327102215 | 12352.2327102215 | 1.46e-11 | 1.84e-04 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 1.46e-11 |
| flat w0wa + radiation: D_M [Mpc] | z=100 | 12352.2327102215 | 12352.2327102215 | 1.46e-11 | 1.84e-04 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 1.46e-11 |
| flat w0wa + radiation: D_A [Mpc] | z=100 | 122.29933376457 | 122.29933376457 | 1.42e-13 | 1.82e-06 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 1.42e-13 |
| flat w0wa + radiation: D_L [Mpc] | z=100 | 1247575.50373237 | 1247575.50373238 | 1.40e-09 | 1.86e-02 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 1.40e-09 |
| flat w0wa + radiation: distance modulus | z=100 | 55.4803341937699 | 55.4803341937699 | 0.00e+00 | 3.24e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| flat w0wa + radiation: lookback time [Gyr] | z=100 | 13.1055914914457 | 13.1055914914457 | 1.78e-15 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 1.78e-15 | 0.00e+00 |
| flat w0wa + radiation: age [Gyr] | z=100 | 0.0161753245346196 | 0.0161753245345074 | 1.12e-13 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 1.12e-13 |
| flat w0wa + radiation: H [km/s/Mpc] | z=100 | 39474.0267646673 | 39474.0267646671 | 2.33e-10 | 6.15e-10 | pass | 16u x conditioning per side | 0.00e+00 | 2.33e-10 |
| flat w0wa + radiation: Omega_m(z) | z=100 | 0.97198283086512 | 0.971982830865131 | 1.17e-14 | 2.68e-14 | pass | 16u x conditioning per side | 0.00e+00 | 1.17e-14 |
| flat w0wa + radiation: Omega_de(z) | z=100 | 7.73589909399664e-05 | 7.73589909399673e-05 | 9.49e-19 | 2.41e-18 | pass | 16u x conditioning per side | 4.07e-20 | 9.08e-19 |
| flat w0wa + radiation: rho_crit(z) [kg/m^3] | z=100 | 2.92682963286676e-21 | 2.92682963286673e-21 | 3.61e-35 | 8.60e-35 | pass | 16u x conditioning per side | 3.76e-37 | 3.57e-35 |
| flat w0wa + radiation: D_C [Mpc] | z=1000 | 13370.222229854 | 13370.222229854 | 2.73e-11 | 1.99e-04 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 2.73e-11 |
| flat w0wa + radiation: D_M [Mpc] | z=1000 | 13370.222229854 | 13370.222229854 | 2.73e-11 | 1.99e-04 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 2.73e-11 |
| flat w0wa + radiation: D_A [Mpc] | z=1000 | 13.3568653644895 | 13.3568653644895 | 2.66e-14 | 1.99e-07 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 2.66e-14 |
| flat w0wa + radiation: D_L [Mpc] | z=1000 | 13383592.4520838 | 13383592.4520838 | 2.79e-08 | 1.99e-01 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 2.79e-08 |
| flat w0wa + radiation: distance modulus | z=1000 | 60.6328635166 | 60.6328635166 | 0.00e+00 | 3.24e-08 | pass | propagated + quad 1.49e-8 | 0.00e+00 | 0.00e+00 |
| flat w0wa + radiation: lookback time [Gyr] | z=1000 | 13.1213417520667 | 13.1213417520666 | 1.42e-14 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 0.00e+00 | 1.42e-14 |
| flat w0wa + radiation: age [Gyr] | z=1000 | 0.000425063913647349 | 0.000425063719062036 | 1.95e-10 | 2.08e-07 | pass | engine bound + quad 1.49e-8 | 1.08e-19 | 1.95e-10 |
| flat w0wa + radiation: H [km/s/Mpc] | z=1000 | 1376394.42813013 | 1376394.42813007 | 6.54e-08 | 1.36e-07 | pass | 16u x conditioning per side | 0.00e+00 | 6.54e-08 |
| flat w0wa + radiation: Omega_m(z) | z=1000 | 0.778276210250539 | 0.778276210250613 | 7.41e-14 | 1.51e-13 | pass | 16u x conditioning per side | 0.00e+00 | 7.41e-14 |
| flat w0wa + radiation: Omega_de(z) | z=1000 | 4.98688817155676e-07 | 4.98688817155723e-07 | 4.75e-20 | 9.87e-20 | pass | 16u x conditioning per side | 4.24e-22 | 4.71e-20 |
| flat w0wa + radiation: rho_crit(z) [kg/m^3] | z=1000 | 3.55844610588649e-18 | 3.55844610588615e-18 | 3.41e-31 | 6.98e-31 | pass | 16u x conditioning per side | 7.70e-34 | 3.40e-31 |
| flat w0wa + radiation: Omega_gamma0 | today | 5.04688842594712e-05 | 5.04688842594712e-05 | 4.07e-20 | 1.34e-19 | pass | 12 roundings |  |  |
| flat w0wa + radiation: Omega_nu0 | today | 3.49128040231764e-05 | 3.49128040231397e-05 | 3.67e-17 | 3.69e-17 | pass | 16 roundings + literal |  |  |
| flat w0wa + radiation: T_nu0 [K] (engine / (N_eff/3)^(1/4)) | today | 1.94536883917508 | 1.94536883917508 | 0.00e+00 | 3.47e-15 | pass | 8 roundings |  |  |
| flat w0wa + radiation: rho_crit0 [kg/m^3] | today | 9.20387392297252e-27 | 9.20387392297252e-27 | 4.30e-42 | 2.45e-41 | pass | 12 roundings |  |  |
| flat w0wa + radiation: hubble distance [Mpc] | today | 4282.7494 | 4282.7494 | 9.09e-13 | 3.80e-12 | pass | 4 roundings |  |  |
| flat w0wa + radiation: hubble time [Gyr] | today | 13.9684603097256 | 13.9684603097256 | 1.78e-15 | 2.48e-14 | pass | 8 roundings |  |  |
| flat w0wa + radiation: D_A(z1, z2) [Mpc] | z1=0.5, z2=2 | 1055.59707085022 | 1055.59707085022 | 4.55e-13 | 4.62e-05 | pass | propagated + quad 1.49e-8 |  |  |
| flat w0wa + radiation: D_A(z1, z2) [Mpc] | z1=1, z2=1100 | 9.24550829463233 | 9.24550829463235 | 2.13e-14 | 2.39e-07 | pass | propagated + quad 1.49e-8 |  |  |
| Planck 2018, m_nu = 0.06 eV: D_C [Mpc] | z=0.001 | 4.42983270932935 | 4.42983270933198 | 2.63e-12 | 7.70e-05 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_M [Mpc] | z=0.001 | 4.42983270932935 | 4.42983270933198 | 2.63e-12 | 7.70e-05 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_A [Mpc] | z=0.001 | 4.42540730202732 | 4.42540730202995 | 2.63e-12 | 7.69e-05 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_L [Mpc] | z=0.001 | 4.43426254203868 | 4.43426254204131 | 2.63e-12 | 7.71e-05 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: distance modulus | z=0.001 | 28.2341070153664 | 28.2341070153677 | 1.29e-12 | 3.77e-05 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: lookback time [Gyr] | z=0.001 | 0.0144409631868624 | 0.0144409631868709 | 8.58e-15 | 2.51e-07 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: age [Gyr] | z=0.001 | 13.7726816653535 | 13.7726753462722 | 6.32e-06 | 3.27e-03 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: H [km/s/Mpc] | z=0.001 | 67.6916039981943 | 67.6916039981166 | 7.78e-11 | 1.68e-04 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: Omega_m(z) | z=0.001 | 0.310281362445481 | 0.310281362446194 | 7.13e-13 | 1.54e-06 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: Omega_de(z) | z=0.001 | 0.688221741894499 | 0.688221776810646 | 3.49e-08 | 3.41e-06 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: rho_crit(z) [kg/m^3] | z=0.001 | 8.60684914811242e-27 | 8.60684914809264e-27 | 1.98e-38 | 4.27e-32 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_C [Mpc] | z=0.1 | 432.566295783505 | 432.566295636756 | 1.47e-07 | 1.35e-03 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_M [Mpc] | z=0.1 | 432.566295783505 | 432.566295636756 | 1.47e-07 | 1.35e-03 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_A [Mpc] | z=0.1 | 393.242087075913 | 393.242086942505 | 1.33e-07 | 1.23e-03 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_L [Mpc] | z=0.1 | 475.822925361855 | 475.822925200431 | 1.61e-07 | 1.49e-03 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: distance modulus | z=0.1 | 38.3872268135409 | 38.3872268128042 | 7.37e-10 | 6.79e-06 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: lookback time [Gyr] | z=0.1 | 1.34519998093593 | 1.34519998049122 | 4.45e-10 | 4.22e-06 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: age [Gyr] | z=0.1 | 12.4419226476044 | 12.4419163289679 | 6.32e-06 | 2.96e-03 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: H [km/s/Mpc] | z=0.1 | 71.0589874689585 | 71.0589875477419 | 7.88e-08 | 2.12e-04 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: Omega_m(z) | z=0.1 | 0.373648371097454 | 0.373648370268924 | 8.29e-10 | 2.23e-06 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: Omega_de(z) | z=0.1 | 0.62453958305882 | 0.624539613357832 | 3.03e-08 | 3.73e-06 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: rho_crit(z) [kg/m^3] | z=0.1 | 9.4844600304209e-27 | 9.4844600514518e-27 | 2.10e-35 | 5.67e-32 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_C [Mpc] | z=0.5 | 1946.42903038422 | 1946.4290111441 | 1.92e-05 | 9.34e-03 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_M [Mpc] | z=0.5 | 1946.42903038422 | 1946.4290111441 | 1.92e-05 | 9.34e-03 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_A [Mpc] | z=0.5 | 1297.61935358948 | 1297.61934076274 | 1.28e-05 | 6.23e-03 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_L [Mpc] | z=0.5 | 2919.64354557633 | 2919.64351671616 | 2.89e-05 | 1.40e-02 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: distance modulus | z=0.5 | 42.32664916197 | 42.3266491405054 | 2.15e-08 | 1.04e-05 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: lookback time [Gyr] | z=0.5 | 5.19627037883186 | 5.19627033285389 | 4.60e-08 | 2.50e-05 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: age [Gyr] | z=0.5 | 8.59085224970848 | 8.59084597660523 | 6.27e-06 | 2.04e-03 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: H [km/s/Mpc] | z=0.5 | 89.2260598485898 | 89.2260627496132 | 2.90e-06 | 4.29e-04 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: Omega_m(z) | z=0.5 | 0.600915510747732 | 0.60091547167238 | 3.91e-08 | 5.78e-06 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: Omega_de(z) | z=0.5 | 0.396108870449882 | 0.396108864787583 | 5.66e-09 | 3.81e-06 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: rho_crit(z) [kg/m^3] | z=0.5 | 1.49540218733541e-26 | 1.49540228457599e-26 | 9.72e-34 | 1.44e-31 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_C [Mpc] | z=1 | 3395.67126679908 | 3395.67114379964 | 1.23e-04 | 2.11e-02 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_M [Mpc] | z=1 | 3395.67126679908 | 3395.67114379964 | 1.23e-04 | 2.11e-02 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_A [Mpc] | z=1 | 1697.83563339954 | 1697.83557189982 | 6.15e-05 | 1.05e-02 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_L [Mpc] | z=1 | 6791.34253359815 | 6791.34228759927 | 2.46e-04 | 4.21e-02 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: distance modulus | z=1 | 44.1597781772196 | 44.1597780985636 | 7.87e-08 | 1.35e-05 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: lookback time [Gyr] | z=1 | 7.93561845836041 | 7.93561822210958 | 2.36e-07 | 4.93e-05 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: age [Gyr] | z=1 | 5.85150417017993 | 5.85149808734954 | 6.08e-06 | 1.39e-03 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: H [km/s/Mpc] | z=1 | 120.628110188847 | 120.628124986593 | 1.48e-05 | 7.52e-04 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: Omega_m(z) | z=1 | 0.779320331316051 | 0.779320140113815 | 1.91e-07 | 9.71e-06 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: Omega_de(z) | z=1 | 0.216720977386421 | 0.216720935209635 | 4.22e-08 | 2.70e-06 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: rho_crit(z) [kg/m^3] | z=1 | 2.73320136535535e-26 | 2.73320203593241e-26 | 6.71e-33 | 3.41e-31 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_C [Mpc] | z=2 | 5308.27177539189 | 5308.27119821702 | 5.77e-04 | 3.90e-02 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_M [Mpc] | z=2 | 5308.27177539189 | 5308.27119821702 | 5.77e-04 | 3.90e-02 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_A [Mpc] | z=2 | 1769.42392513063 | 1769.42373273901 | 1.92e-04 | 1.30e-02 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_L [Mpc] | z=2 | 15924.8153261757 | 15924.8135946511 | 1.73e-03 | 1.17e-01 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: distance modulus | z=2 | 46.0103720234709 | 46.010371787364 | 2.36e-07 | 1.59e-05 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: lookback time [Gyr] | z=2 | 10.510192874589 | 10.5101920495894 | 8.25e-07 | 7.72e-05 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: age [Gyr] | z=2 | 3.27692975395133 | 3.27692425986968 | 5.49e-06 | 7.79e-04 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: H [km/s/Mpc] | z=2 | 204.034922713769 | 204.035001864427 | 7.92e-05 | 1.50e-03 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: Omega_m(z) | z=2 | 0.919343513140706 | 0.919342799864755 | 7.13e-07 | 1.35e-05 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: Omega_de(z) | z=2 | 0.0757511068595273 | 0.0757510519307295 | 5.49e-08 | 1.11e-06 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: rho_crit(z) [kg/m^3] | z=2 | 7.8195830510061e-26 | 7.81958911786226e-26 | 6.07e-32 | 1.15e-30 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_C [Mpc] | z=5 | 7946.45306135065 | 7946.45037988162 | 2.68e-03 | 6.27e-02 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_M [Mpc] | z=5 | 7946.45306135065 | 7946.45037988162 | 2.68e-03 | 6.27e-02 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_A [Mpc] | z=5 | 1324.40884355844 | 1324.40839664694 | 4.47e-04 | 1.05e-02 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_L [Mpc] | z=5 | 47678.7183681039 | 47678.7022792897 | 1.61e-02 | 3.76e-01 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: distance modulus | z=5 | 48.3916228639943 | 48.3916221312476 | 7.33e-07 | 1.71e-05 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: lookback time [Gyr] | z=5 | 12.6163780567668 | 12.6163756697085 | 2.39e-06 | 9.96e-05 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: age [Gyr] | z=5 | 1.17074457177349 | 1.17074063975056 | 3.93e-06 | 2.79e-04 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: H [km/s/Mpc] | z=5 | 557.855975833342 | 557.856764112726 | 7.88e-04 | 4.40e-03 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: Omega_m(z) | z=5 | 0.983858493987532 | 0.983855713507418 | 2.78e-06 | 1.55e-05 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: Omega_de(z) | z=5 | 0.0101333681109708 | 0.0101333399871638 | 2.81e-08 | 1.60e-07 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: rho_crit(z) [kg/m^3] | z=5 | 5.84546090507082e-25 | 5.84547742496045e-25 | 1.65e-30 | 9.21e-30 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_C [Mpc] | z=10 | 9636.49843915457 | 9636.49200765481 | 6.43e-03 | 7.69e-02 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_M [Mpc] | z=10 | 9636.49843915457 | 9636.49200765481 | 6.43e-03 | 7.69e-02 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_A [Mpc] | z=10 | 876.045312650415 | 876.044727968619 | 5.85e-04 | 6.99e-03 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_L [Mpc] | z=10 | 106001.4828307 | 106001.412084203 | 7.07e-02 | 8.46e-01 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: distance modulus | z=10 | 50.1265597027713 | 50.1265582535075 | 1.45e-06 | 1.73e-05 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: lookback time [Gyr] | z=10 | 13.3156914599884 | 13.3156875860342 | 3.87e-06 | 1.06e-04 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: age [Gyr] | z=10 | 0.471431168551956 | 0.471428723424894 | 2.45e-06 | 1.12e-04 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: H [km/s/Mpc] | z=10 | 1379.78583321288 | 1379.79040282064 | 4.57e-03 | 1.10e-02 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: Omega_m(z) | z=10 | 0.99100936804866 | 0.991002803984167 | 6.56e-06 | 1.58e-05 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: Omega_de(z) | z=10 | 0.00165643590445914 | 0.0016564250168985 | 1.09e-08 | 2.64e-08 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: rho_crit(z) [kg/m^3] | z=10 | 3.57600357308799e-24 | 3.5760272593157e-24 | 2.37e-29 | 5.70e-29 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_C [Mpc] | z=100 | 12831.704660498 | 12831.6804482667 | 2.42e-02 | 1.37e-01 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_M [Mpc] | z=100 | 12831.704660498 | 12831.6804482667 | 2.42e-02 | 1.37e-01 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_A [Mpc] | z=100 | 127.04658079701 | 127.046341071948 | 2.40e-04 | 1.35e-03 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_L [Mpc] | z=100 | 1296002.17071029 | 1295999.72527494 | 2.45e+00 | 1.38e+01 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: distance modulus | z=100 | 55.5630286447358 | 55.5630245473658 | 4.10e-06 | 2.31e-05 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: lookback time [Gyr] | z=100 | 13.7706816986706 | 13.7706753881301 | 6.31e-06 | 1.47e-04 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: age [Gyr] | z=100 | 0.0164409298697551 | 0.0164409213289553 | 8.54e-09 | 4.12e-06 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: H [km/s/Mpc] | z=100 | 38823.6780941702 | 38823.643601048 | 3.45e-02 | 4.16e-01 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: Omega_m(z) | z=100 | 0.968933193573126 | 0.968934915284064 | 1.72e-06 | 2.07e-05 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: Omega_de(z) | z=100 | 2.09220696704205e-06 | 2.09221079085498e-06 | 3.82e-12 | 4.48e-11 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: rho_crit(z) [kg/m^3] | z=100 | 2.83118295954803e-21 | 2.83117792878839e-21 | 5.03e-27 | 6.06e-26 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_C [Mpc] | z=1000 | 13866.2405136119 | 13866.2125647739 | 2.79e-02 | 7.54e-01 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_M [Mpc] | z=1000 | 13866.2405136119 | 13866.2125647739 | 2.79e-02 | 7.54e-01 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_A [Mpc] | z=1000 | 13.8523881254864 | 13.8523602045693 | 2.79e-05 | 7.54e-04 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_L [Mpc] | z=1000 | 13880106.7541255 | 13880078.7773386 | 2.80e+01 | 7.55e+02 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: distance modulus | z=1000 | 60.7119640318007 | 60.7119596549697 | 4.38e-06 | 1.18e-04 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: lookback time [Gyr] | z=1000 | 13.7866925159095 | 13.7866862032479 | 6.31e-06 | 7.50e-04 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: age [Gyr] | z=1000 | 0.000430112630837036 | 0.000430106001880722 | 6.63e-09 | 3.18e-07 | pass | engine bound + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: H [km/s/Mpc] | z=1000 | 1357319.80872035 | 1357344.30347771 | 2.45e+01 | 7.45e+01 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: Omega_m(z) | z=1000 | 0.771722078875335 | 0.771694225994601 | 2.79e-05 | 8.47e-05 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: Omega_de(z) | z=1000 | 1.71172354406349e-09 | 1.71166185162223e-09 | 6.17e-14 | 1.88e-13 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: rho_crit(z) [kg/m^3] | z=1000 | 3.46050081129071e-18 | 3.46062571168925e-18 | 1.25e-22 | 3.80e-22 | pass | 16u x conditioning per side + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: Omega_gamma0 | today | 5.40201513713935e-05 | 5.40201513713935e-05 | 4.74e-20 | 1.44e-19 | pass | 12 roundings |  |  |
| Planck 2018, m_nu = 0.06 eV: Omega_nu0 | today | 0.00143970925127499 | 0.00143967430408452 | 3.49e-08 | 4.95e-06 | pass | 16 roundings + literal + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: T_nu0 [K] (engine / (N_eff/3)^(1/4)) | today | 1.94536883917508 | 1.94536883917508 | 0.00e+00 | 3.47e-15 | pass | 8 roundings |  |  |
| Planck 2018, m_nu = 0.06 eV: rho_crit0 [kg/m^3] | today | 8.5988142566229e-27 | 8.59881425662289e-27 | 4.30e-42 | 2.29e-41 | pass | 12 roundings |  |  |
| Planck 2018, m_nu = 0.06 eV: hubble distance [Mpc] | today | 4430.8669524091 | 4430.8669524091 | 0.00e+00 | 3.94e-12 | pass | 4 roundings |  |  |
| Planck 2018, m_nu = 0.06 eV: hubble time [Gyr] | today | 14.4515551534258 | 14.4515551534258 | 0.00e+00 | 2.57e-14 | pass | 8 roundings |  |  |
| Planck 2018, m_nu = 0.06 eV: D_A(z1, z2) [Mpc] | z1=0.5, z2=2 | 1120.61424833589 | 1120.61406235764 | 1.86e-04 | 1.78e-02 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: D_A(z1, z2) [Mpc] | z1=1, z2=1100 | 9.52862423961921 | 9.52859863206837 | 2.56e-05 | 9.05e-04 | pass | propagated + quad 1.49e-8 + Komatsu fit 0.35 % |  |  |
| Planck 2018, m_nu = 0.06 eV: nu density / photon density | z=0 | 26.6513368571825 | 26.6506899284052 | 6.47e-04 | 9.17e-02 | pass | Komatsu fit 0.35 % + literal | 3.55e-15 | 6.47e-04 |
| Planck 2018, m_nu = 0.06 eV: nu density / photon density | z=10 | 2.85642911929744 | 2.85991189322799 | 3.48e-03 | 8.38e-03 | pass | Komatsu fit 0.35 % + literal | 0.00e+00 | 3.48e-03 |
| Planck 2018, m_nu = 0.06 eV: nu density / photon density | z=35 | 1.23328674408989 | 1.2358841525662 | 2.60e-03 | 2.70e-03 | pass | Komatsu fit 0.35 % + literal | 2.22e-16 | 2.60e-03 |
| Planck 2018, m_nu = 0.06 eV: nu density / photon density | z=100 | 0.819514155164213 | 0.819410078411262 | 1.04e-04 | 1.25e-03 | pass | Komatsu fit 0.35 % + literal | 0.00e+00 | 1.04e-04 |
| Planck 2018, m_nu = 0.06 eV: nu density / photon density | z=140 | 0.766939185008934 | 0.76665167754132 | 2.88e-04 | 1.07e-03 | pass | Komatsu fit 0.35 % + literal | 0.00e+00 | 2.88e-04 |
| Planck 2018, m_nu = 0.06 eV: nu density / photon density | z=1000 | 0.693839227557893 | 0.694107041479911 | 2.68e-04 | 8.14e-04 | pass | Komatsu fit 0.35 % + literal | 1.11e-16 | 2.68e-04 |

## miepython (Mie scattering) (`test_ext_mie_miepython.py`)

| quantity | inputs | engine | library | diff | tol | status | basis | eng err | lib err |
|---|---|---|---|---|---|---|---|---|---|
| efficiencies Qext | m=1.333, x=0.1 | 1.12747447744073e-05 | 1.12747447744073e-05 | 0.00e+00 | 2.96e-14 | pass | coefficient budgets + truncation | 3.39e-21 | 3.39e-21 |
| efficiencies Qsca | m=1.333, x=0.1 | 1.12747447744073e-05 | 1.12747447744073e-05 | 3.39e-21 | 3.67e-19 | pass | coefficient budgets + truncation | 6.78e-21 | 3.39e-21 |
| efficiencies Qback | m=1.333, x=0.1 | 1.6837163147824e-05 | 1.68371631502093e-05 | 2.39e-15 | 2.40e-15 | pass | coefficient budgets + truncation | 3.39e-21 | 2.39e-15 |
| efficiencies g | m=1.333, x=0.1 | 0.0018344211378938 | 0.00183442113789379 | 1.17e-17 | 4.29e-10 | pass | coefficient budgets + truncation | 2.58e-16 | 2.46e-16 |
| amplitude S1 (conj of miepython's) | m=1.333, x=0.1, theta=0 deg | 2.8186861936e-08-0.000206077836636j | 2.8186861936e-08-0.000206077836622j | 1.45e-14 | 1.46e-14 | pass | coefficient budgets + truncation | 1.36e-19 | 1.45e-14 |
| amplitude S2 (conj of miepython's) | m=1.333, x=0.1, theta=0 deg | 2.8186861936e-08-0.000206077836636j | 2.8186861936e-08-0.000206077836622j | 1.45e-14 | 1.46e-14 | pass | coefficient budgets + truncation | 1.36e-19 | 1.45e-14 |
| amplitude S1 (conj of miepython's) | m=1.333, x=0.1, theta=30 deg | 2.81868538673e-08-0.000206016640955j | 2.81868538673e-08-0.000206016640948j | 7.08e-15 | 7.12e-15 | pass | coefficient budgets + truncation | 1.36e-19 | 7.08e-15 |
| amplitude S2 (conj of miepython's) | m=1.333, x=0.1, theta=30 deg | 2.44105387687e-08-0.000178431016179j | 2.44105387687e-08-0.000178431016185j | 5.45e-15 | 5.49e-15 | pass | coefficient budgets + truncation | 1.36e-19 | 5.45e-15 |
| amplitude S1 (conj of miepython's) | m=1.333, x=0.1, theta=90 deg | 2.81868017102e-08-0.00020562135953j | 2.81868017102e-08-0.00020562135953j | 2.87e-18 | 2.45e-17 | pass | coefficient budgets + truncation | 5.42e-20 | 2.82e-18 |
| amplitude S2 (conj of miepython's) | m=1.333, x=0.1, theta=90 deg | 2.90673558069e-14-6.14326769084e-08j | 2.90673558069e-14-6.14326660049e-08j | 1.09e-14 | 1.09e-14 | pass | coefficient budgets + truncation | 5.32e-20 | 1.09e-14 |
| amplitude S1 (conj of miepython's) | m=1.333, x=0.1, theta=137.9 deg | 2.8186757024e-08-0.000205283102575j | 2.8186757024e-08-0.000205283102578j | 2.31e-15 | 2.34e-15 | pass | coefficient budgets + truncation | 2.71e-20 | 2.31e-15 |
| amplitude S2 (conj of miepython's) | m=1.333, x=0.1, theta=137.9 deg | -2.09138796823e-08+0.000152287510947j | -2.09138796823e-08+0.000152287510935j | 1.23e-14 | 1.23e-14 | pass | coefficient budgets + truncation | 2.71e-20 | 1.23e-14 |
| amplitude S1 (conj of miepython's) | m=1.333, x=0.1, theta=170 deg | 2.81867423993e-08-0.000205172479709j | 2.81867423993e-08-0.000205172479722j | 1.36e-14 | 1.36e-14 | pass | coefficient budgets + truncation | 2.71e-20 | 1.36e-14 |
| amplitude S2 (conj of miepython's) | m=1.333, x=0.1, theta=170 deg | -2.77585215705e-08+0.000202053598128j | -2.77585215705e-08+0.00020205359814j | 1.14e-14 | 1.15e-14 | pass | coefficient budgets + truncation | 1.32e-23 | 1.14e-14 |
| amplitude S1 (conj of miepython's) | m=1.333, x=0.1, theta=180 deg | 2.81867414843e-08-0.000205165560158j | 2.81867414843e-08-0.000205165560173j | 1.45e-14 | 1.46e-14 | pass | coefficient budgets + truncation | 2.71e-20 | 1.45e-14 |
| amplitude S2 (conj of miepython's) | m=1.333, x=0.1, theta=180 deg | -2.81867414843e-08+0.000205165560158j | -2.81867414843e-08+0.000205165560173j | 1.45e-14 | 1.46e-14 | pass | coefficient budgets + truncation | 2.71e-20 | 1.45e-14 |
| coefficient a_n | m=1.333, x=0.1, n=1 | 1.87912011401e-08-0.000137081000824j | 1.87912011401e-08-0.000137081000824j | 0.00e+00 | 2.19e-18 | pass | stated bound + 16N u | 2.71e-20 | 2.71e-20 |
| coefficient b_n | m=1.333, x=0.1, n=1 | 2.97644005887e-14-1.72523623277e-07j | 2.97644005887e-14-1.72523623277e-07j | 0.00e+00 | 2.19e-18 | pass | stated bound + 16N u | 3.54e-20 | 3.54e-20 |
| coefficient a_n | m=1.333, x=0.1, n=3 | 4.46287822626e-22-2.11255253811e-11j | 4.46287822626e-22-2.11255253811e-11j | 9.69e-27 | 1.83e-18 | pass | stated bound + 16N u | 9.69e-27 | 1.94e-26 |
| coefficient b_n | m=1.333, x=0.1, n=3 | 6.1215509083e-29-7.82403406709e-15j | 6.1215509083e-29-7.82403406709e-15j | 0.00e+00 | 1.83e-18 | pass | stated bound + 16N u | 5.90e-28 | 5.90e-28 |
| efficiencies Qext | m=1.333, x=1 | 0.0956523519956125 | 0.0956523519956124 | 8.33e-17 | 7.73e-13 | pass | coefficient budgets + truncation | 2.78e-17 | 5.55e-17 |
| efficiencies Qsca | m=1.333, x=1 | 0.0956523519956125 | 0.0956523519956124 | 8.33e-17 | 4.62e-15 | pass | coefficient budgets + truncation | 2.78e-17 | 5.55e-17 |
| efficiencies Qback | m=1.333, x=1 | 0.0861355075988746 | 0.0861355075989146 | 4.00e-14 | 2.66e-13 | pass | coefficient budgets + truncation | 1.11e-16 | 3.99e-14 |
| efficiencies g | m=1.333, x=1 | 0.184734896450387 | 0.184734896450387 | 4.16e-16 | 6.81e-13 | pass | coefficient budgets + truncation | 5.00e-16 | 8.33e-17 |
| amplitude S1 (conj of miepython's) | m=1.333, x=1, theta=0 deg | 0.0239130879989-0.230270450455j | 0.0239130879989-0.230270450455j | 3.55e-14 | 2.29e-13 | pass | coefficient budgets + truncation | 1.39e-16 | 3.53e-14 |
| amplitude S2 (conj of miepython's) | m=1.333, x=1, theta=0 deg | 0.0239130879989-0.230270450455j | 0.0239130879989-0.230270450455j | 3.55e-14 | 2.29e-13 | pass | coefficient budgets + truncation | 1.39e-16 | 3.53e-14 |
| amplitude S1 (conj of miepython's) | m=1.333, x=1, theta=30 deg | 0.0238410080664-0.223744882513j | 0.0238410080664-0.223744882513j | 3.61e-15 | 7.51e-14 | pass | coefficient budgets + truncation | 1.11e-16 | 3.72e-15 |
| amplitude S2 (conj of miepython's) | m=1.333, x=1, theta=30 deg | 0.0207169760158-0.195614930878j | 0.0207169760158-0.195614930878j | 2.04e-14 | 9.13e-14 | pass | coefficient budgets + truncation | 1.11e-16 | 2.05e-14 |
| amplitude S1 (conj of miepython's) | m=1.333, x=1, theta=90 deg | 0.0233761296896-0.184476232543j | 0.0233761296896-0.184476232543j | 2.78e-16 | 4.12e-14 | pass | coefficient budgets + truncation | 2.80e-17 | 2.50e-16 |
| amplitude S2 (conj of miepython's) | m=1.333, x=1, theta=90 deg | 0.000279597556327-0.00683577281524j | 0.000279597556327-0.00683577281522j | 1.92e-14 | 5.75e-14 | pass | coefficient budgets + truncation | 1.22e-16 | 1.90e-14 |
| amplitude S1 (conj of miepython's) | m=1.333, x=1, theta=137.9 deg | 0.0229792904932-0.15459148421j | 0.0229792904932-0.15459148421j | 3.03e-15 | 6.82e-14 | pass | coefficient budgets + truncation | 8.33e-17 | 3.11e-15 |
| amplitude S2 (conj of miepython's) | m=1.333, x=1, theta=137.9 deg | -0.0169246502545+0.111828335404j | -0.0169246502545+0.111828335404j | 1.77e-14 | 8.18e-14 | pass | coefficient budgets + truncation | 1.11e-16 | 1.76e-14 |
| amplitude S1 (conj of miepython's) | m=1.333, x=1, theta=170 deg | 0.0228497042856-0.145512580375j | 0.0228497042856-0.145512580375j | 2.62e-14 | 1.46e-13 | pass | coefficient budgets + truncation | 8.33e-17 | 2.61e-14 |
| amplitude S2 (conj of miepython's) | m=1.333, x=1, theta=170 deg | -0.0224941566791+0.143113219026j | -0.0224941566791+0.143113219026j | 1.03e-14 | 1.30e-13 | pass | coefficient budgets + truncation | 1.11e-16 | 1.02e-14 |
| amplitude S1 (conj of miepython's) | m=1.333, x=1, theta=180 deg | 0.0228416017634-0.144955641934j | 0.0228416017634-0.144955641934j | 3.45e-14 | 2.28e-13 | pass | coefficient budgets + truncation | 8.33e-17 | 3.44e-14 |
| amplitude S2 (conj of miepython's) | m=1.333, x=1, theta=180 deg | -0.0228416017634+0.144955641934j | -0.0228416017634+0.144955641934j | 3.45e-14 | 2.28e-13 | pass | coefficient budgets + truncation | 8.33e-17 | 3.44e-14 |
| coefficient a_n | m=1.333, x=1, n=1 | 0.0155844591306-0.123861147113j | 0.0155844591306-0.123861147113j | 5.65e-17 | 3.07e-15 | pass | stated bound + 16N u | 0.00e+00 | 5.65e-17 |
| coefficient b_n | m=1.333, x=1, n=1 | 0.000271780154728-0.0164835157135j | 0.000271780154728-0.0164835157135j | 7.29e-17 | 3.07e-15 | pass | stated bound + 16N u | 7.29e-17 | 0.00e+00 |
| coefficient a_n | m=1.333, x=1, n=3 | 3.70205585884e-08-0.00019240726914j | 3.70205585884e-08-0.00019240726914j | 1.63e-19 | 2.77e-15 | pass | stated bound + 16N u | 1.08e-19 | 5.42e-20 |
| coefficient b_n | m=1.333, x=1, n=3 | 5.33388369628e-11-7.30334423124e-06j | 5.33388369628e-11-7.30334423124e-06j | 1.27e-19 | 2.77e-15 | pass | stated bound + 16N u | 3.22e-20 | 9.49e-20 |
| coefficient a_n | m=1.333, x=1, n=7 | 1.10169204953e-24-1.04961519117e-12j | 1.10169204953e-24-1.04961519117e-12j | 0.00e+00 | 2.77e-15 | pass | stated bound + 16N u | 6.06e-28 | 6.06e-28 |
| coefficient b_n | m=1.333, x=1, n=7 | 1.12572959086e-28-1.06100404847e-14j | 1.12572959086e-28-1.06100404847e-14j | 0.00e+00 | 2.77e-15 | pass | stated bound + 16N u | 3.12e-28 | 3.12e-28 |
| efficiencies Qext | m=1.333, x=10 | 2.15765960806197 | 2.15765960806197 | 0.00e+00 | 1.16e-12 | pass | coefficient budgets + truncation | 4.44e-16 | 4.44e-16 |
| efficiencies Qsca | m=1.333, x=10 | 2.15765960806197 | 2.15765960806197 | 0.00e+00 | 2.96e-13 | pass | coefficient budgets + truncation | 4.44e-16 | 4.44e-16 |
| efficiencies Qback | m=1.333, x=10 | 0.542415905458389 | 0.542415905666113 | 2.08e-10 | 2.26e-10 | pass | coefficient budgets + truncation | 1.22e-15 | 2.08e-10 |
| efficiencies g | m=1.333, x=10 | 0.705899508335843 | 0.705899508335843 | 2.22e-16 | 2.33e-13 | pass | coefficient budgets + truncation | 2.22e-16 | 0.00e+00 |
| amplitude S1 (conj of miepython's) | m=1.333, x=10, theta=0 deg | 53.9414902015+22.6683552177j | 53.9414902015+22.6683552188j | 1.12e-09 | 1.15e-09 | pass | coefficient budgets + truncation | 1.46e-14 | 1.12e-09 |
| amplitude S2 (conj of miepython's) | m=1.333, x=10, theta=0 deg | 53.9414902015+22.6683552177j | 53.9414902015+22.6683552188j | 1.12e-09 | 1.15e-09 | pass | coefficient budgets + truncation | 1.46e-14 | 1.12e-09 |
| amplitude S1 (conj of miepython's) | m=1.333, x=10, theta=30 deg | -9.90252441579-9.87710664219j | -9.90252441579-9.87710664226j | 6.95e-11 | 7.58e-11 | pass | coefficient budgets + truncation | 8.88e-15 | 6.95e-11 |
| amplitude S2 (conj of miepython's) | m=1.333, x=10, theta=30 deg | -9.4835256083-12.1228504871j | -9.4835256083-12.1228504873j | 1.96e-10 | 2.03e-10 | pass | coefficient budgets + truncation | 3.97e-15 | 1.96e-10 |
| amplitude S1 (conj of miepython's) | m=1.333, x=10, theta=90 deg | -1.40411406906+0.350246344334j | -1.40411406906+0.350246344346j | 1.18e-11 | 1.51e-11 | pass | coefficient budgets + truncation | 4.48e-16 | 1.18e-11 |
| amplitude S2 (conj of miepython's) | m=1.333, x=10, theta=90 deg | -2.63115650711+2.75414702656j | -2.63115650711+2.75414702654j | 1.57e-11 | 1.90e-11 | pass | coefficient budgets + truncation | 5.20e-15 | 1.57e-11 |
| amplitude S1 (conj of miepython's) | m=1.333, x=10, theta=137.9 deg | 3.05321479986+1.04440197014j | 3.05321479986+1.0444019702j | 6.26e-11 | 6.81e-11 | pass | coefficient budgets + truncation | 1.99e-15 | 6.26e-11 |
| amplitude S2 (conj of miepython's) | m=1.333, x=10, theta=137.9 deg | 0.660951866857-3.61866772662j | 0.660951866857-3.61866772634j | 2.84e-10 | 2.90e-10 | pass | coefficient budgets + truncation | 3.18e-15 | 2.84e-10 |
| amplitude S1 (conj of miepython's) | m=1.333, x=10, theta=170 deg | -4.01990331056+1.43244236564j | -4.01990331056+1.43244236578j | 1.32e-10 | 1.44e-10 | pass | coefficient budgets + truncation | 3.72e-15 | 1.32e-10 |
| amplitude S2 (conj of miepython's) | m=1.333, x=10, theta=170 deg | -3.03235130768-0.81852199052j | -3.03235130768-0.818521989813j | 7.07e-10 | 7.20e-10 | pass | coefficient budgets + truncation | 8.59e-15 | 7.07e-10 |
| amplitude S1 (conj of miepython's) | m=1.333, x=10, theta=180 deg | 0.612122964694+3.63121234749j | 0.612122964694+3.6312123482j | 7.15e-10 | 7.44e-10 | pass | coefficient budgets + truncation | 2.81e-15 | 7.15e-10 |
| amplitude S2 (conj of miepython's) | m=1.333, x=10, theta=180 deg | -0.612122964694-3.63121234749j | -0.612122964694-3.6312123482j | 7.15e-10 | 7.44e-10 | pass | coefficient budgets + truncation | 2.81e-15 | 7.15e-10 |
| coefficient a_n | m=1.333, x=10, n=1 | 0.000493903396159-0.0222184485416j | 0.000493903396159-0.0222184485416j | 0.00e+00 | 5.30e-14 | pass | stated bound + 16N u | 3.44e-16 | 3.44e-16 |
| coefficient b_n | m=1.333, x=10, n=1 | 0.0898357078926-0.28594624229j | 0.0898357078926-0.28594624229j | 6.21e-17 | 5.30e-14 | pass | stated bound + 16N u | 2.55e-16 | 1.93e-16 |
| coefficient a_n | m=1.333, x=10, n=10 | 0.89175003226-0.310695851636j | 0.89175003226-0.310695851636j | 1.16e-15 | 6.63e-14 | pass | stated bound + 16N u | 5.12e-16 | 6.47e-16 |
| coefficient b_n | m=1.333, x=10, n=10 | 0.947943119515+0.222141760322j | 0.947943119515+0.222141760322j | 5.55e-16 | 6.63e-14 | pass | stated bound + 16N u | 2.95e-16 | 2.73e-16 |
| coefficient a_n | m=1.333, x=10, n=20 | 4.49717006887e-19-6.70609429465e-10j | 4.49717006887e-19-6.70609429465e-10j | 9.31e-25 | 5.02e-14 | pass | stated bound + 16N u | 1.03e-25 | 1.03e-24 |
| coefficient b_n | m=1.333, x=10, n=20 | 1.46780115582e-20-1.21152843789e-10j | 1.46780115582e-20-1.21152843789e-10j | 1.55e-25 | 5.02e-14 | pass | stated bound + 16N u | 1.55e-25 | 0.00e+00 |
| efficiencies Qext | m=1.333, x=100 | 2.11996783888142 | 2.11996783888137 | 5.33e-14 | 1.01e-11 | pass | coefficient budgets + truncation | 2.22e-15 | 5.55e-14 |
| efficiencies Qsca | m=1.333, x=100 | 2.11996783888142 | 2.11996783888137 | 5.28e-14 | 7.34e-12 | pass | coefficient budgets + truncation | 2.66e-15 | 5.55e-14 |
| efficiencies Qback | m=1.333, x=100 | 0.247237123451522 | 0.247237123360661 | 9.09e-11 | 5.05e-09 | pass | coefficient budgets + truncation | 1.38e-14 | 9.09e-11 |
| efficiencies g | m=1.333, x=100 | 0.875782209165125 | 0.875782209165148 | 2.35e-14 | 6.48e-12 | pass | coefficient budgets + truncation | 4.44e-16 | 2.40e-14 |
| amplitude S1 (conj of miepython's) | m=1.333, x=100, theta=0 deg | 5299.9195972+57.4913452404j | 5299.9195972+57.4913456608j | 4.20e-07 | 4.45e-07 | pass | coefficient budgets + truncation | 4.63e-12 | 4.20e-07 |
| amplitude S2 (conj of miepython's) | m=1.333, x=100, theta=0 deg | 5299.9195972+57.4913452404j | 5299.9195972+57.4913456608j | 4.20e-07 | 4.45e-07 | pass | coefficient budgets + truncation | 4.63e-12 | 4.20e-07 |
| amplitude S1 (conj of miepython's) | m=1.333, x=100, theta=30 deg | -62.6724400172-10.4949045825j | -62.6724400172-10.4949045622j | 2.04e-08 | 2.24e-08 | pass | coefficient budgets + truncation | 1.65e-12 | 2.04e-08 |
| amplitude S2 (conj of miepython's) | m=1.333, x=100, theta=30 deg | -80.0184880863-24.7618888082j | -80.0184880863-24.7618887488j | 5.94e-08 | 6.15e-08 | pass | coefficient budgets + truncation | 2.31e-12 | 5.94e-08 |
| amplitude S1 (conj of miepython's) | m=1.333, x=100, theta=90 deg | -5.81542585432-10.0985451366j | -5.81542585432-10.0985451375j | 9.33e-10 | 2.12e-09 | pass | coefficient budgets + truncation | 1.44e-13 | 9.33e-10 |
| amplitude S2 (conj of miepython's) | m=1.333, x=100, theta=90 deg | -6.58115722999+3.42914828189j | -6.58115722999+3.4291482714j | 1.05e-08 | 1.17e-08 | pass | coefficient budgets + truncation | 5.92e-14 | 1.05e-08 |
| amplitude S1 (conj of miepython's) | m=1.333, x=100, theta=137.9 deg | -20.3352918731-36.2783527487j | -20.3352918732-36.2783527607j | 1.20e-08 | 1.38e-08 | pass | coefficient budgets + truncation | 1.31e-12 | 1.20e-08 |
| amplitude S2 (conj of miepython's) | m=1.333, x=100, theta=137.9 deg | -10.6010425182-2.30867634871j | -10.6010425182-2.30867638221j | 3.35e-08 | 3.54e-08 | pass | coefficient budgets + truncation | 9.93e-13 | 3.35e-08 |
| amplitude S1 (conj of miepython's) | m=1.333, x=100, theta=170 deg | 0.652907408479+6.44264387035j | 0.652907408493+6.44264389417j | 2.38e-08 | 2.78e-08 | pass | coefficient budgets + truncation | 7.24e-13 | 2.38e-08 |
| amplitude S2 (conj of miepython's) | m=1.333, x=100, theta=170 deg | -15.6030300301+8.92777270879j | -15.6030300301+8.92777272234j | 1.36e-08 | 1.75e-08 | pass | coefficient budgets + truncation | 2.90e-13 | 1.36e-08 |
| amplitude S1 (conj of miepython's) | m=1.333, x=100, theta=180 deg | -24.7759998933-2.05976647125j | -24.7759998933-2.05976641627j | 5.50e-08 | 8.01e-08 | pass | coefficient budgets + truncation | 1.17e-12 | 5.50e-08 |
| amplitude S2 (conj of miepython's) | m=1.333, x=100, theta=180 deg | 24.7759998933+2.05976647125j | 24.7759998933+2.05976641627j | 5.50e-08 | 8.01e-08 | pass | coefficient budgets + truncation | 1.17e-12 | 5.50e-08 |
| coefficient a_n | m=1.333, x=100, n=1 | 0.941677064066+0.234353090609j | 0.941677064066+0.234353090608j | 4.04e-13 | 3.37e-13 | xfail | stated bound + 16N u | 1.57e-14 | 4.20e-13 |
| coefficient b_n | m=1.333, x=100, n=1 | 0.874398783859+0.331399382384j | 0.87439878386+0.331399382384j | 2.40e-13 | 3.37e-13 | pass | stated bound + 16N u | 9.40e-15 | 2.49e-13 |
| coefficient a_n | m=1.333, x=100, n=60 | 0.000121029111689-0.0110006574187j | 0.000121029111681-0.0110006574183j | 3.54e-13 | 3.22e-13 | xfail | stated bound + 16N u | 1.24e-14 | 3.66e-13 |
| coefficient b_n | m=1.333, x=100, n=60 | 0.0363790421292-0.187231427445j | 0.0363790421291-0.187231427444j | 2.26e-13 | 3.22e-13 | pass | stated bound + 16N u | 8.11e-15 | 2.34e-13 |
| coefficient a_n | m=1.333, x=100, n=120 | 1.77113798307e-16-1.33084108107e-08j | 1.77113798307e-16-1.33084108107e-08j | 4.16e-21 | 2.74e-13 | pass | stated bound + 16N u | 3.31e-23 | 4.19e-21 |
| coefficient b_n | m=1.333, x=100, n=120 | 1.41129777356e-16-1.18798054427e-08j | 1.41129777356e-16-1.18798054427e-08j | 6.69e-21 | 2.74e-13 | pass | stated bound + 16N u | 6.78e-23 | 6.75e-21 |
| efficiencies Qext | m=1.333, x=1000 | 2.02281143322015 | 2.02281143322038 | 2.29e-13 | 1.20e-09 | pass | coefficient budgets + truncation | 4.44e-15 | 2.25e-13 |
| efficiencies Qsca | m=1.333, x=1000 | 2.02281143322015 | 2.02281143322038 | 2.29e-13 | 1.37e-09 | pass | coefficient budgets + truncation | 4.44e-15 | 2.25e-13 |
| efficiencies Qback | m=1.333, x=1000 | 3.49447622422868 | 3.4944762255087 | 1.28e-09 | 5.35e-06 | pass | coefficient budgets + truncation | 7.26e-12 | 1.29e-09 |
| efficiencies g | m=1.333, x=1000 | 0.88009449871184 | 0.880094498711746 | 9.47e-14 | 1.28e-09 | pass | coefficient budgets + truncation | 2.11e-15 | 9.68e-14 |
| amplitude S1 (conj of miepython's) | m=1.333, x=1000, theta=0 deg | 505702.858305+8720.42087046j | 505702.858305+8720.4207999j | 7.06e-05 | 3.70e-04 | pass | coefficient budgets + truncation | 5.40e-09 | 7.06e-05 |
| amplitude S2 (conj of miepython's) | m=1.333, x=1000, theta=0 deg | 505702.858305+8720.42087046j | 505702.858305+8720.4207999j | 7.06e-05 | 3.70e-04 | pass | coefficient budgets + truncation | 5.40e-09 | 7.06e-05 |
| amplitude S1 (conj of miepython's) | m=1.333, x=1000, theta=30 deg | 311.371930824+857.371457117j | 311.371930819+857.371455797j | 1.32e-06 | 9.97e-06 | pass | coefficient budgets + truncation | 2.10e-10 | 1.32e-06 |
| amplitude S2 (conj of miepython's) | m=1.333, x=1000, theta=30 deg | 317.027761847+973.805207872j | 317.027761845+973.805206007j | 1.87e-06 | 1.05e-05 | pass | coefficient budgets + truncation | 6.36e-11 | 1.87e-06 |
| amplitude S1 (conj of miepython's) | m=1.333, x=1000, theta=90 deg | 7.64685246466+136.787293164j | 7.64685246199+136.787292127j | 1.04e-06 | 5.93e-06 | pass | coefficient budgets + truncation | 1.47e-10 | 1.04e-06 |
| amplitude S2 (conj of miepython's) | m=1.333, x=1000, theta=90 deg | 4.04090838681-12.7319388362j | 4.04090838681-12.7319394777j | 6.42e-07 | 5.55e-06 | pass | coefficient budgets + truncation | 3.82e-12 | 6.42e-07 |
| amplitude S1 (conj of miepython's) | m=1.333, x=1000, theta=137.9 deg | 519.773602722+165.824718651j | 519.773602718+165.824718982j | 3.31e-07 | 7.97e-06 | pass | coefficient budgets + truncation | 1.36e-10 | 3.31e-07 |
| amplitude S2 (conj of miepython's) | m=1.333, x=1000, theta=137.9 deg | 114.612689661-98.1679609811j | 114.612689661-98.1679604072j | 5.74e-07 | 8.21e-06 | pass | coefficient budgets + truncation | 1.58e-11 | 5.74e-07 |
| amplitude S1 (conj of miepython's) | m=1.333, x=1000, theta=170 deg | 229.816426953+106.232172842j | 229.816426959+106.232174939j | 2.10e-06 | 1.72e-05 | pass | coefficient budgets + truncation | 3.39e-10 | 2.10e-06 |
| amplitude S2 (conj of miepython's) | m=1.333, x=1000, theta=170 deg | -191.555946303-196.778973855j | -191.555946303-196.778971962j | 1.89e-06 | 1.70e-05 | pass | coefficient budgets + truncation | 2.69e-11 | 1.89e-06 |
| amplitude S1 (conj of miepython's) | m=1.333, x=1000, theta=180 deg | 933.492334068+47.0225296323j | 933.492334113+47.0225321461j | 2.51e-06 | 3.01e-04 | pass | coefficient budgets + truncation | 2.79e-09 | 2.52e-06 |
| amplitude S2 (conj of miepython's) | m=1.333, x=1000, theta=180 deg | -933.492334068-47.0225296323j | -933.492334113-47.0225321461j | 2.51e-06 | 3.01e-04 | pass | coefficient budgets + truncation | 2.79e-09 | 2.52e-06 |
| coefficient a_n | m=1.333, x=1000, n=1 | 0.0219806185428+0.146620158748j | 0.0219806185425+0.146620158747j | 9.95e-13 | 2.69e-12 | pass | stated bound + 16N u | 2.65e-14 | 1.02e-12 |
| coefficient b_n | m=1.333, x=1000, n=1 | 0.0137267652594-0.116354377549j | 0.0137267652596-0.11635437755j | 8.26e-13 | 2.69e-12 | pass | stated bound + 16N u | 1.83e-14 | 8.44e-13 |
| coefficient a_n | m=1.333, x=1000, n=521 | 0.997891219946+0.0458730105904j | 0.997891219946+0.0458730105912j | 8.47e-13 | 2.67e-12 | pass | stated bound + 16N u | 2.93e-14 | 8.77e-13 |
| coefficient b_n | m=1.333, x=1000, n=521 | 0.897342937935+0.303510444092j | 0.897342937935+0.303510444093j | 9.25e-13 | 2.67e-12 | pass | stated bound + 16N u | 3.26e-14 | 9.57e-13 |
| coefficient a_n | m=1.333, x=1000, n=1042 | 1.67574166762e-16-1.29450441004e-08j | 1.67574166763e-16-1.29450441005e-08j | 5.23e-20 | 2.32e-12 | pass | stated bound + 16N u | 9.02e-22 | 5.32e-20 |
| coefficient b_n | m=1.333, x=1000, n=1042 | 1.21692655521e-17-3.48844744149e-09j | 1.21692655525e-17-3.48844744155e-09j | 5.91e-20 | 2.32e-12 | pass | stated bound + 16N u | 1.08e-21 | 6.01e-20 |
| efficiencies Qext | m=1.333, x=10000 | 2.00493832246981 | 2.00493832245681 | 1.30e-11 | 1.25e-07 | pass | coefficient budgets + truncation | 1.91e-14 | 1.30e-11 |
| efficiencies Qsca | m=1.333, x=10000 | 2.00493832246981 | 2.00493832245681 | 1.30e-11 | 1.56e-07 | pass | coefficient budgets + truncation | 1.91e-14 | 1.30e-11 |
| efficiencies Qback | m=1.333, x=10000 | 1.26558917353672 | 1.26559803466132 | 8.86e-06 | 4.34e-03 | pass | coefficient budgets + truncation | 4.70e-11 | 8.86e-06 |
| efficiencies g | m=1.333, x=10000 | 0.883540371573564 | 0.88354037158318 | 9.62e-12 | 1.47e-07 | pass | coefficient budgets + truncation | 2.00e-15 | 9.62e-12 |
| amplitude S1 (conj of miepython's) | m=1.333, x=10000, theta=0 deg | 50123458.0617+199310.985128j | 50123458.0614+199311.000364j | 1.52e-02 | 3.14e+00 | pass | coefficient budgets + truncation | 4.31e-07 | 1.52e-02 |
| amplitude S2 (conj of miepython's) | m=1.333, x=10000, theta=0 deg | 50123458.0617+199310.985128j | 50123458.0614+199311.000364j | 1.52e-02 | 3.14e+00 | pass | coefficient budgets + truncation | 4.31e-07 | 1.52e-02 |
| amplitude S1 (conj of miepython's) | m=1.333, x=10000, theta=30 deg | 6766.17609533-3050.98164114j | 6766.17610186-3050.98164999j | 1.10e-05 | 2.91e-02 | pass | coefficient budgets + truncation | 5.91e-09 | 1.10e-05 |
| amplitude S2 (conj of miepython's) | m=1.333, x=10000, theta=30 deg | 8548.33584647-4324.08138572j | 8548.33585238-4324.08138225j | 6.85e-06 | 2.91e-02 | pass | coefficient budgets + truncation | 8.03e-09 | 6.86e-06 |
| amplitude S1 (conj of miepython's) | m=1.333, x=10000, theta=90 deg | -1079.00644359+678.464054091j | -1079.00644934+678.464081232j | 2.77e-05 | 1.66e-02 | pass | coefficient budgets + truncation | 1.81e-09 | 2.77e-05 |
| amplitude S2 (conj of miepython's) | m=1.333, x=10000, theta=90 deg | 345.877948057+93.0538152173j | 345.877941764+93.0535212014j | 2.94e-04 | 1.68e-02 | pass | coefficient budgets + truncation | 1.91e-09 | 2.94e-04 |
| amplitude S1 (conj of miepython's) | m=1.333, x=10000, theta=137.9 deg | 5623.73052318+3460.99572837j | 5623.73050959+3460.99571982j | 1.61e-05 | 2.57e-02 | pass | coefficient budgets + truncation | 8.86e-09 | 1.61e-05 |
| amplitude S2 (conj of miepython's) | m=1.333, x=10000, theta=137.9 deg | 2151.46403849+554.044947752j | 2151.46403763+554.045254797j | 3.07e-04 | 2.60e-02 | pass | coefficient budgets + truncation | 1.69e-09 | 3.07e-04 |
| amplitude S1 (conj of miepython's) | m=1.333, x=10000, theta=170 deg | 1078.80473995+1301.31776893j | 1078.80473642+1301.31775581j | 1.36e-05 | 5.05e-02 | pass | coefficient budgets + truncation | 2.33e-09 | 1.36e-05 |
| amplitude S2 (conj of miepython's) | m=1.333, x=10000, theta=170 deg | -1337.24450411-883.654071853j | -1337.24450932-883.653712505j | 3.59e-04 | 5.08e-02 | pass | coefficient budgets + truncation | 2.92e-09 | 3.59e-04 |
| amplitude S1 (conj of miepython's) | m=1.333, x=10000, theta=180 deg | -1400.40004943-5447.80772788j | -1400.39955827-5447.82818596j | 2.05e-02 | 3.14e+00 | pass | coefficient budgets + truncation | 1.60e-07 | 2.05e-02 |
| amplitude S2 (conj of miepython's) | m=1.333, x=10000, theta=180 deg | 1400.40004943+5447.80772788j | 1400.39955827+5447.82818596j | 2.05e-02 | 3.14e+00 | pass | coefficient budgets + truncation | 1.60e-07 | 2.05e-02 |
| coefficient a_n | m=1.333, x=10000, n=1 | 0.0201974278607+0.140675128465j | 0.0201974276645+0.140675127795j | 6.98e-10 | 2.87e-11 | xfail | stated bound + 16N u | 3.12e-13 | 6.98e-10 |
| coefficient b_n | m=1.333, x=10000, n=1 | 0.000318309309113+0.0178383852491j | 0.00031830926742+0.0178383840813j | 1.17e-09 | 2.87e-11 | xfail | stated bound + 16N u | 5.15e-13 | 1.17e-09 |
| coefficient a_n | m=1.333, x=10000, n=5044 | 0.432710644685-0.495451453385j | 0.432710645501-0.495451453496j | 8.24e-10 | 2.65e-11 | xfail | stated bound + 16N u | 3.28e-13 | 8.24e-10 |
| coefficient b_n | m=1.333, x=10000, n=5044 | 0.697659443808-0.45927197201j | 0.697659444706-0.459271971623j | 9.77e-10 | 2.65e-11 | xfail | stated bound + 16N u | 3.88e-13 | 9.78e-10 |
| coefficient a_n | m=1.333, x=10000, n=10089 | 7.14514509029e-15+8.45289600686e-08j | 7.14514507944e-15+8.45289600045e-08j | 6.41e-17 | 2.24e-11 | pass | stated bound + 16N u | 1.86e-20 | 6.42e-17 |
| coefficient b_n | m=1.333, x=10000, n=10089 | 5.09680421964e-15+7.13919058412e-08j | 5.09680421537e-15+7.13919058113e-08j | 2.99e-17 | 2.24e-11 | pass | stated bound + 16N u | 8.68e-21 | 2.99e-17 |
| efficiencies Qext | m=(1.333+1e-08j), x=500 | 2.03026159436764 | 2.0302615943674 | 2.48e-13 | 2.90e-11 | pass | coefficient budgets + truncation | 1.78e-15 | 2.46e-13 |
| efficiencies Qsca | m=(1.333+1e-08j), x=500 | 2.03024415862218 | 2.03024415862218 | 4.00e-15 | 2.99e-11 | pass | coefficient budgets + truncation | 2.22e-15 | 1.78e-15 |
| efficiencies Qback | m=(1.333+1e-08j), x=500 | 0.398431548660985 | 0.398431814247594 | 2.66e-07 | 6.82e-07 | pass | coefficient budgets + truncation | 3.72e-13 | 2.66e-07 |
| efficiencies g | m=(1.333+1e-08j), x=500 | 0.879601884112068 | 0.879601884112064 | 3.77e-15 | 2.76e-11 | pass | coefficient budgets + truncation | 1.33e-15 | 2.44e-15 |
| amplitude S1 (conj of miepython's) | m=(1.333+1e-08j), x=500, theta=0 deg | 126891.349648+3544.81747059j | 126891.349648+3544.81741646j | 5.41e-05 | 5.59e-05 | pass | coefficient budgets + truncation | 2.87e-10 | 5.41e-05 |
| amplitude S2 (conj of miepython's) | m=(1.333+1e-08j), x=500, theta=0 deg | 126891.349648+3544.81747059j | 126891.349648+3544.81741646j | 5.41e-05 | 5.59e-05 | pass | coefficient budgets + truncation | 2.87e-10 | 5.41e-05 |
| amplitude S1 (conj of miepython's) | m=(1.333+1e-08j), x=500, theta=30 deg | 99.415836183-498.202947232j | 99.4158361826-498.202940603j | 6.63e-06 | 6.70e-06 | pass | coefficient budgets + truncation | 5.67e-11 | 6.63e-06 |
| amplitude S2 (conj of miepython's) | m=(1.333+1e-08j), x=500, theta=30 deg | 23.5607169984-543.781429419j | 23.5607169985-543.781429136j | 2.83e-07 | 3.56e-07 | pass | coefficient budgets + truncation | 4.75e-11 | 2.83e-07 |
| amplitude S1 (conj of miepython's) | m=(1.333+1e-08j), x=500, theta=90 deg | -3.44130343315-76.9591800211j | -3.44130343344-76.9591839052j | 3.88e-06 | 3.93e-06 | pass | coefficient budgets + truncation | 1.04e-11 | 3.88e-06 |
| amplitude S2 (conj of miepython's) | m=(1.333+1e-08j), x=500, theta=90 deg | -1.87330275456+0.0845833646545j | -1.87330275457+0.0845840457259j | 6.81e-07 | 7.22e-07 | pass | coefficient budgets + truncation | 5.63e-12 | 6.81e-07 |
| amplitude S1 (conj of miepython's) | m=(1.333+1e-08j), x=500, theta=137.9 deg | 210.304962946+34.7466267215j | 210.304962946+34.7466292799j | 2.56e-06 | 2.62e-06 | pass | coefficient budgets + truncation | 2.42e-11 | 2.56e-06 |
| amplitude S2 (conj of miepython's) | m=(1.333+1e-08j), x=500, theta=137.9 deg | 67.8479450493-14.1641204199j | 67.8479450494-14.164122089j | 1.67e-06 | 1.73e-06 | pass | coefficient budgets + truncation | 1.06e-11 | 1.67e-06 |
| amplitude S1 (conj of miepython's) | m=(1.333+1e-08j), x=500, theta=170 deg | 30.0983354671-15.3409642613j | 30.0983354684-15.3409676559j | 3.39e-06 | 3.52e-06 | pass | coefficient budgets + truncation | 1.18e-11 | 3.39e-06 |
| amplitude S2 (conj of miepython's) | m=(1.333+1e-08j), x=500, theta=170 deg | -4.70027900565-58.3849983995j | -4.70027900563-58.3849982589j | 1.41e-07 | 2.70e-07 | pass | coefficient budgets + truncation | 1.84e-11 | 1.41e-07 |
| amplitude S1 (conj of miepython's) | m=(1.333+1e-08j), x=500, theta=180 deg | 121.086786584-101.192696901j | 121.08678659-101.192778912j | 8.20e-05 | 8.38e-05 | pass | coefficient budgets + truncation | 1.48e-10 | 8.20e-05 |
| amplitude S2 (conj of miepython's) | m=(1.333+1e-08j), x=500, theta=180 deg | -121.086786584+101.192696901j | -121.08678659+101.192778912j | 8.20e-05 | 8.38e-05 | pass | coefficient budgets + truncation | 1.48e-10 | 8.20e-05 |
| coefficient a_n | m=(1.333+1e-08j), x=500, n=1 | 0.0127714942153+0.112268619013j | 0.0127714942152+0.112268619013j | 8.17e-14 | 1.42e-12 | pass | stated bound + 16N u | 3.67e-14 | 4.50e-14 |
| coefficient b_n | m=(1.333+1e-08j), x=500, n=1 | 0.0148908492824-0.121092537827j | 0.0148908492824-0.121092537827j | 1.07e-13 | 1.42e-12 | pass | stated bound + 16N u | 4.93e-14 | 5.79e-14 |
| coefficient a_n | m=(1.333+1e-08j), x=500, n=267 | 0.0256325971374+0.158018814407j | 0.0256325971374+0.158018814407j | 1.15e-13 | 1.48e-12 | pass | stated bound + 16N u | 4.96e-14 | 6.52e-14 |
| coefficient b_n | m=(1.333+1e-08j), x=500, n=267 | 0.0168546157103+0.12871426834j | 0.0168546157103+0.12871426834j | 6.90e-14 | 1.48e-12 | pass | stated bound + 16N u | 2.91e-14 | 3.99e-14 |
| coefficient a_n | m=(1.333+1e-08j), x=500, n=534 | 7.73733068131e-14+1.43302394483e-08j | 7.73733068131e-14+1.43302394483e-08j | 2.55e-21 | 1.19e-12 | pass | stated bound + 16N u | 8.55e-22 | 1.69e-21 |
| coefficient b_n | m=(1.333+1e-08j), x=500, n=534 | 4.92525215606e-14+1.65139281679e-08j | 4.92525215605e-14+1.65139281679e-08j | 1.82e-21 | 1.19e-12 | pass | stated bound + 16N u | 6.52e-22 | 1.17e-21 |
| efficiencies Qext | m=(1.5+0.1j), x=1 | 0.482370456346987 | 0.482370456346957 | 3.00e-14 | 1.15e-12 | pass | coefficient budgets + truncation | 5.55e-17 | 3.00e-14 |
| efficiencies Qsca | m=(1.5+0.1j), x=1 | 0.208740018314837 | 0.208740018314837 | 1.39e-16 | 1.01e-14 | pass | coefficient budgets + truncation | 2.78e-17 | 1.11e-16 |
| efficiencies Qback | m=(1.5+0.1j), x=1 | 0.176962217249138 | 0.176962217249217 | 7.88e-14 | 5.50e-13 | pass | coefficient budgets + truncation | 1.94e-16 | 7.86e-14 |
| efficiencies g | m=(1.5+0.1j), x=1 | 0.205596688540912 | 0.205596688540911 | 1.39e-16 | 4.65e-13 | pass | coefficient budgets + truncation | 2.78e-16 | 1.39e-16 |
| amplitude S1 (conj of miepython's) | m=(1.5+0.1j), x=1, theta=0 deg | 0.120592614087-0.325482813167j | 0.120592614087-0.325482813167j | 5.00e-14 | 3.31e-13 | pass | coefficient budgets + truncation | 6.21e-17 | 4.99e-14 |
| amplitude S2 (conj of miepython's) | m=(1.5+0.1j), x=1, theta=0 deg | 0.120592614087-0.325482813167j | 0.120592614087-0.325482813167j | 5.00e-14 | 3.31e-13 | pass | coefficient budgets + truncation | 6.21e-17 | 4.99e-14 |
| amplitude S1 (conj of miepython's) | m=(1.5+0.1j), x=1, theta=30 deg | 0.117933254359-0.315282951695j | 0.117933254359-0.315282951695j | 5.22e-15 | 1.09e-13 | pass | coefficient budgets + truncation | 1.67e-16 | 5.38e-15 |
| amplitude S2 (conj of miepython's) | m=(1.5+0.1j), x=1, theta=30 deg | 0.104349643762-0.277137591472j | 0.104349643762-0.277137591472j | 2.90e-14 | 1.32e-13 | pass | coefficient budgets + truncation | 6.21e-17 | 2.90e-14 |
| amplitude S1 (conj of miepython's) | m=(1.5+0.1j), x=1, theta=90 deg | 0.101820110907-0.253928091423j | 0.101820110907-0.253928091423j | 3.51e-16 | 6.00e-14 | pass | coefficient budgets + truncation | 5.55e-17 | 2.99e-16 |
| amplitude S2 (conj of miepython's) | m=(1.5+0.1j), x=1, theta=90 deg | 0.00833596157345-0.0151653834282j | 0.00833596157344-0.0151653834282j | 2.70e-14 | 8.30e-14 | pass | coefficient budgets + truncation | 1.01e-16 | 2.69e-14 |
| amplitude S1 (conj of miepython's) | m=(1.5+0.1j), x=1, theta=137.9 deg | 0.0894053400228-0.207268422182j | 0.0894053400228-0.207268422182j | 4.36e-15 | 9.92e-14 | pass | coefficient budgets + truncation | 1.39e-17 | 4.36e-15 |
| amplitude S2 (conj of miepython's) | m=(1.5+0.1j), x=1, theta=137.9 deg | -0.0627812157715+0.147408847089j | -0.0627812157715+0.147408847089j | 2.49e-14 | 1.18e-13 | pass | coefficient budgets + truncation | 5.55e-17 | 2.48e-14 |
| amplitude S1 (conj of miepython's) | m=(1.5+0.1j), x=1, theta=170 deg | 0.0856018778754-0.193100274081j | 0.0856018778754-0.193100274081j | 3.69e-14 | 2.11e-13 | pass | coefficient budgets + truncation | 5.72e-17 | 3.68e-14 |
| amplitude S2 (conj of miepython's) | m=(1.5+0.1j), x=1, theta=170 deg | -0.0840669126945+0.189747890538j | -0.0840669126945+0.189747890538j | 1.44e-14 | 1.88e-13 | pass | coefficient budgets + truncation | 8.33e-17 | 1.43e-14 |
| amplitude S1 (conj of miepython's) | m=(1.5+0.1j), x=1, theta=180 deg | 0.0853680165171-0.192231256741j | 0.0853680165172-0.192231256741j | 4.86e-14 | 3.30e-13 | pass | coefficient budgets + truncation | 1.39e-16 | 4.85e-14 |
| amplitude S2 (conj of miepython's) | m=(1.5+0.1j), x=1, theta=180 deg | -0.0853680165171+0.192231256741j | -0.0853680165172+0.192231256741j | 4.86e-14 | 3.30e-13 | pass | coefficient budgets + truncation | 1.39e-16 | 4.85e-14 |
| coefficient a_n | m=(1.5+0.1j), x=1, n=1 | 0.0682287821494-0.170689482731j | 0.0682287821494-0.170689482731j | 6.21e-17 | 4.52e-15 | pass | stated bound + 16N u | 0.00e+00 | 6.21e-17 |
| coefficient b_n | m=(1.5+0.1j), x=1, n=1 | 0.00864512703725-0.0272424021477j | 0.00864512703725-0.0272424021477j | 3.82e-17 | 4.52e-15 | pass | stated bound + 16N u | 5.90e-17 | 2.11e-17 |
| coefficient a_n | m=(1.5+0.1j), x=1, n=3 | 4.33552825081e-05-0.000272564123264j | 4.33552825081e-05-0.000272564123264j | 2.17e-19 | 4.08e-15 | pass | stated bound + 16N u | 5.42e-20 | 1.63e-19 |
| coefficient b_n | m=(1.5+0.1j), x=1, n=3 | 2.95870324212e-06-1.17855402111e-05j | 2.95870324212e-06-1.17855402111e-05j | 1.27e-19 | 4.08e-15 | pass | stated bound + 16N u | 1.19e-20 | 1.15e-19 |
| coefficient a_n | m=(1.5+0.1j), x=1, n=7 | 2.20997265998e-13-1.46697580561e-12j | 2.20997265998e-13-1.46697580561e-12j | 6.06e-28 | 4.08e-15 | pass | stated bound + 16N u | 1.22e-27 | 1.82e-27 |
| coefficient b_n | m=(1.5+0.1j), x=1, n=7 | 4.14742219505e-15-1.69822200526e-14j | 4.14742219505e-15-1.69822200526e-14j | 4.10e-28 | 4.08e-15 | pass | stated bound + 16N u | 2.05e-29 | 4.01e-28 |
| efficiencies Qext | m=(1.5+0.1j), x=100 | 2.08982184326448 | 2.08982184280449 | 4.60e-10 | 4.61e-10 | pass | coefficient budgets + truncation | 4.44e-16 | 4.60e-10 |
| efficiencies Qsca | m=(1.5+0.1j), x=100 | 1.13213397112475 | 1.13213397112475 | 1.55e-15 | 5.88e-13 | pass | coefficient budgets + truncation | 4.44e-16 | 1.11e-15 |
| efficiencies Qback | m=(1.5+0.1j), x=100 | 0.0415348345655928 | 0.0415348354934666 | 9.28e-10 | 3.76e-09 | pass | coefficient budgets + truncation | 6.11e-16 | 9.28e-10 |
| efficiencies g | m=(1.5+0.1j), x=100 | 0.950391672887167 | 0.950391672887167 | 2.22e-16 | 1.01e-12 | pass | coefficient budgets + truncation | 1.11e-16 | 3.33e-16 |
| amplitude S1 (conj of miepython's) | m=(1.5+0.1j), x=100, theta=0 deg | 5224.55460816+261.693768432j | 5224.55460701+261.693768634j | 1.17e-06 | 1.17e-06 | pass | coefficient budgets + truncation | 1.55e-12 | 1.17e-06 |
| amplitude S2 (conj of miepython's) | m=(1.5+0.1j), x=100, theta=0 deg | 5224.55460816+261.693768432j | 5224.55460701+261.693768634j | 1.17e-06 | 1.17e-06 | pass | coefficient budgets + truncation | 1.55e-12 | 1.17e-06 |
| amplitude S1 (conj of miepython's) | m=(1.5+0.1j), x=100, theta=30 deg | 33.6789947561+10.5490787695j | 33.678994649+10.5490787417j | 1.11e-07 | 1.11e-07 | pass | coefficient budgets + truncation | 6.43e-14 | 1.11e-07 |
| amplitude S2 (conj of miepython's) | m=(1.5+0.1j), x=100, theta=30 deg | 17.7529352409+6.52844310942j | 17.7529351298+6.52844317436j | 1.29e-07 | 1.29e-07 | pass | coefficient budgets + truncation | 2.49e-14 | 1.29e-07 |
| amplitude S1 (conj of miepython's) | m=(1.5+0.1j), x=100, theta=90 deg | 1.19223570495-15.3731610326j | 1.19223571973-15.3731610287j | 1.53e-08 | 1.54e-08 | pass | coefficient budgets + truncation | 3.77e-15 | 1.53e-08 |
| amplitude S2 (conj of miepython's) | m=(1.5+0.1j), x=100, theta=90 deg | -0.850854179953+4.66331834493j | -0.850854164863+4.66331833521j | 1.79e-08 | 1.81e-08 | pass | coefficient budgets + truncation | 9.37e-15 | 1.79e-08 |
| amplitude S1 (conj of miepython's) | m=(1.5+0.1j), x=100, theta=137.9 deg | -10.1876202298-4.52645387822j | -10.1876201746-4.52645386268j | 5.73e-08 | 5.76e-08 | pass | coefficient budgets + truncation | 1.75e-14 | 5.73e-08 |
| amplitude S2 (conj of miepython's) | m=(1.5+0.1j), x=100, theta=137.9 deg | 8.38526331181+3.84444975899j | 8.38526336969+3.84444972575j | 6.67e-08 | 6.70e-08 | pass | coefficient budgets + truncation | 2.14e-14 | 6.67e-08 |
| amplitude S1 (conj of miepython's) | m=(1.5+0.1j), x=100, theta=170 deg | -9.41597852385-4.02881675658j | -9.41597852981-4.02881675364j | 6.65e-09 | 7.10e-09 | pass | coefficient budgets + truncation | 1.30e-13 | 6.65e-09 |
| amplitude S2 (conj of miepython's) | m=(1.5+0.1j), x=100, theta=170 deg | 9.31862905631+3.99377938042j | 9.3186290505+3.99377937902j | 5.97e-09 | 6.42e-09 | pass | coefficient budgets + truncation | 5.70e-14 | 5.97e-09 |
| amplitude S1 (conj of miepython's) | m=(1.5+0.1j), x=100, theta=180 deg | -9.54951905044+3.55580825121j | -9.54951906673+3.55580853363j | 2.83e-07 | 2.86e-07 | pass | coefficient budgets + truncation | 6.42e-14 | 2.83e-07 |
| amplitude S2 (conj of miepython's) | m=(1.5+0.1j), x=100, theta=180 deg | 9.54951905044-3.55580825121j | 9.54951906673-3.55580853363j | 2.83e-07 | 2.86e-07 | pass | coefficient budgets + truncation | 6.42e-14 | 2.83e-07 |
| coefficient a_n | m=(1.5+0.1j), x=100, n=1 | 0.463019646902-0.0949372493029j | 0.463019646902-0.0949372493029j | 5.33e-16 | 2.35e-13 | pass | stated bound + 16N u | 1.69e-16 | 6.68e-16 |
| coefficient b_n | m=(1.5+0.1j), x=100, n=1 | 0.536991502533+0.0949619630123j | 0.536991502533+0.0949619630123j | 3.12e-16 | 2.35e-13 | pass | stated bound + 16N u | 4.16e-17 | 3.51e-16 |
| coefficient a_n | m=(1.5+0.1j), x=100, n=60 | 0.531778919036+0.0597417064202j | 0.531778919036+0.0597417064202j | 6.66e-16 | 2.36e-13 | pass | stated bound + 16N u | 1.67e-16 | 5.06e-16 |
| coefficient b_n | m=(1.5+0.1j), x=100, n=60 | 0.431507841139-0.116579516994j | 0.431507841139-0.116579516994j | 7.73e-16 | 2.36e-13 | pass | stated bound + 16N u | 1.14e-16 | 6.60e-16 |
| coefficient a_n | m=(1.5+0.1j), x=100, n=120 | 1.29533974029e-08-6.86863038087e-09j | 1.29533974029e-08-6.86863038087e-09j | 6.52e-21 | 2.17e-13 | pass | stated bound + 16N u | 4.37e-23 | 6.56e-21 |
| coefficient b_n | m=(1.5+0.1j), x=100, n=120 | 1.20508442259e-08+3.78089269589e-09j | 1.20508442259e-08+3.78089269589e-09j | 6.15e-21 | 2.17e-13 | pass | stated bound + 16N u | 3.65e-23 | 6.19e-21 |
| efficiencies Qext | m=(1.5+0.1j), x=3000 | 2.00951129139544 | 2.00951129126324 | 1.32e-10 | 1.52e-10 | pass | coefficient budgets + truncation | 5.77e-15 | 1.32e-10 |
| efficiencies Qsca | m=(1.5+0.1j), x=3000 | 1.10100771259925 | 1.10100771259922 | 2.80e-14 | 1.39e-11 | pass | coefficient budgets + truncation | 5.77e-15 | 2.22e-14 |
| efficiencies Qback | m=(1.5+0.1j), x=3000 | 0.041533547832863 | 0.0415335533547501 | 5.52e-09 | 5.23e-05 | pass | coefficient budgets + truncation | 4.23e-16 | 5.52e-09 |
| efficiencies g | m=(1.5+0.1j), x=3000 | 0.950714190228123 | 0.950714190228122 | 9.99e-16 | 2.45e-11 | pass | coefficient budgets + truncation | 1.11e-16 | 8.88e-16 |
| amplitude S1 (conj of miepython's) | m=(1.5+0.1j), x=3000, theta=0 deg | 4521400.40564+33067.7414486j | 4521400.40534+33067.7410011j | 5.37e-04 | 5.81e-04 | pass | coefficient budgets + truncation | 1.84e-08 | 5.37e-04 |
| amplitude S2 (conj of miepython's) | m=(1.5+0.1j), x=3000, theta=0 deg | 4521400.40564+33067.7414486j | 4521400.40534+33067.7410011j | 5.37e-04 | 5.81e-04 | pass | coefficient budgets + truncation | 1.84e-08 | 5.37e-04 |
| amplitude S1 (conj of miepython's) | m=(1.5+0.1j), x=3000, theta=30 deg | 751.837880695+589.728943225j | 751.837878793+589.728938154j | 5.42e-06 | 6.16e-06 | pass | coefficient budgets + truncation | 4.06e-11 | 5.42e-06 |
| amplitude S2 (conj of miepython's) | m=(1.5+0.1j), x=3000, theta=30 deg | 410.990766082+273.198557661j | 410.990762051+273.198553597j | 5.72e-06 | 6.46e-06 | pass | coefficient budgets + truncation | 2.11e-11 | 5.72e-06 |
| amplitude S1 (conj of miepython's) | m=(1.5+0.1j), x=3000, theta=90 deg | 452.66056353+94.6649751758j | 452.660563955+94.664976301j | 1.20e-06 | 1.62e-06 | pass | coefficient budgets + truncation | 1.98e-12 | 1.20e-06 |
| amplitude S2 (conj of miepython's) | m=(1.5+0.1j), x=3000, theta=90 deg | -134.816348504-46.3715041486j | -134.816347605-46.3715032504j | 1.27e-06 | 1.69e-06 | pass | coefficient budgets + truncation | 1.27e-13 | 1.27e-06 |
| amplitude S1 (conj of miepython's) | m=(1.5+0.1j), x=3000, theta=137.9 deg | 303.157333922+141.236684702j | 303.157334357+141.236685865j | 1.24e-06 | 1.90e-06 | pass | coefficient budgets + truncation | 2.10e-12 | 1.24e-06 |
| amplitude S2 (conj of miepython's) | m=(1.5+0.1j), x=3000, theta=137.9 deg | -249.253457274-120.219342865j | -249.253456351-120.219341931j | 1.31e-06 | 1.96e-06 | pass | coefficient budgets + truncation | 1.02e-12 | 1.31e-06 |
| amplitude S1 (conj of miepython's) | m=(1.5+0.1j), x=3000, theta=170 deg | 304.603369389-40.2108603123j | 304.603370488-40.2108573827j | 3.13e-06 | 4.42e-06 | pass | coefficient budgets + truncation | 1.22e-12 | 3.13e-06 |
| amplitude S2 (conj of miepython's) | m=(1.5+0.1j), x=3000, theta=170 deg | -301.557556884+39.6015150586j | -301.557554557+39.6015174077j | 3.31e-06 | 4.58e-06 | pass | coefficient budgets + truncation | 2.69e-12 | 3.31e-06 |
| amplitude S1 (conj of miepython's) | m=(1.5+0.1j), x=3000, theta=180 deg | -172.412139251+252.437193897j | -172.412160545+252.437203962j | 2.36e-05 | 6.71e-05 | pass | coefficient budgets + truncation | 6.70e-12 | 2.36e-05 |
| amplitude S2 (conj of miepython's) | m=(1.5+0.1j), x=3000, theta=180 deg | 172.412139251-252.437193897j | 172.412160545-252.437203962j | 2.36e-05 | 6.71e-05 | pass | coefficient budgets + truncation | 6.70e-12 | 2.36e-05 |
| coefficient a_n | m=(1.5+0.1j), x=3000, n=1 | 0.415825558317-0.0574286242723j | 0.415825558317-0.0574286242723j | 3.15e-14 | 6.80e-12 | pass | stated bound + 16N u | 1.18e-16 | 3.16e-14 |
| coefficient b_n | m=(1.5+0.1j), x=3000, n=1 | 0.584174467635+0.0574286395698j | 0.584174467635+0.0574286395698j | 1.50e-14 | 6.80e-12 | pass | stated bound + 16N u | 1.52e-16 | 1.49e-14 |
| coefficient a_n | m=(1.5+0.1j), x=3000, n=1530 | 0.563062615726-0.0492717201672j | 0.563062615726-0.0492717201672j | 1.91e-14 | 6.82e-12 | pass | stated bound + 16N u | 1.04e-15 | 1.96e-14 |
| coefficient b_n | m=(1.5+0.1j), x=3000, n=1530 | 0.405348900656+0.0791768244439j | 0.405348900656+0.0791768244439j | 2.67e-14 | 6.82e-12 | pass | stated bound + 16N u | 8.36e-16 | 2.73e-14 |
| coefficient a_n | m=(1.5+0.1j), x=3000, n=3060 | 3.27206143499e-08+3.32254897164e-08j | 3.272061435e-08+3.32254897164e-08j | 1.06e-19 | 6.26e-12 | pass | stated bound + 16N u | 1.14e-21 | 1.07e-19 |
| coefficient b_n | m=(1.5+0.1j), x=3000, n=3060 | 1.5406312939e-08+4.13506672785e-08j | 1.5406312939e-08+4.13506672786e-08j | 4.97e-20 | 6.26e-12 | pass | stated bound + 16N u | 1.07e-21 | 5.08e-20 |
| efficiencies Qext | m=0.75, x=30 | 1.88005704273987 | 1.88005704273987 | 1.55e-15 | 8.70e-13 | pass | coefficient budgets + truncation | 6.66e-16 | 8.88e-16 |
| efficiencies Qsca | m=0.75, x=30 | 1.88005704273987 | 1.88005704273987 | 1.55e-15 | 4.13e-13 | pass | coefficient budgets + truncation | 6.66e-16 | 8.88e-16 |
| efficiencies Qback | m=0.75, x=30 | 0.034564611453254 | 0.0345646112945989 | 1.59e-10 | 3.10e-10 | pass | coefficient budgets + truncation | 1.53e-16 | 1.59e-10 |
| efficiencies g | m=0.75, x=30 | 0.853141231787364 | 0.853141231787364 | 1.11e-16 | 4.02e-13 | pass | coefficient budgets + truncation | 1.11e-16 | 0.00e+00 |
| amplitude S1 (conj of miepython's) | m=0.75, x=30, theta=0 deg | 423.012834616+105.253624783j | 423.012834616+105.253624769j | 1.35e-08 | 1.37e-08 | pass | coefficient budgets + truncation | 2.05e-13 | 1.35e-08 |
| amplitude S2 (conj of miepython's) | m=0.75, x=30, theta=0 deg | 423.012834616+105.253624783j | 423.012834616+105.253624769j | 1.35e-08 | 1.37e-08 | pass | coefficient budgets + truncation | 2.05e-13 | 1.35e-08 |
| amplitude S1 (conj of miepython's) | m=0.75, x=30, theta=30 deg | 3.45166034589-5.34675690686j | 3.45166034589-5.34675690642j | 4.43e-10 | 4.74e-10 | pass | coefficient budgets + truncation | 1.52e-14 | 4.43e-10 |
| amplitude S2 (conj of miepython's) | m=0.75, x=30, theta=30 deg | -4.59107403193-14.4120735247j | -4.59107403193-14.4120735232j | 1.50e-09 | 1.53e-09 | pass | coefficient budgets + truncation | 2.81e-14 | 1.50e-09 |
| amplitude S1 (conj of miepython's) | m=0.75, x=30, theta=90 deg | 7.25599862394-2.92308957151j | 7.25599862394-2.9230895715j | 9.75e-12 | 2.57e-11 | pass | coefficient budgets + truncation | 1.33e-15 | 9.75e-12 |
| amplitude S2 (conj of miepython's) | m=0.75, x=30, theta=90 deg | 1.42698327678-0.552714269885j | 1.42698327678-0.552714269585j | 3.00e-10 | 3.17e-10 | pass | coefficient budgets + truncation | 5.86e-15 | 3.00e-10 |
| amplitude S1 (conj of miepython's) | m=0.75, x=30, theta=137.9 deg | 1.84184939645-0.510683277286j | 1.84184939645-0.510683277164j | 1.22e-10 | 1.47e-10 | pass | coefficient budgets + truncation | 1.30e-14 | 1.22e-10 |
| amplitude S2 (conj of miepython's) | m=0.75, x=30, theta=137.9 deg | -1.68529428747+0.526746499817j | -1.68529428747+0.526746500792j | 9.75e-10 | 1.00e-09 | pass | coefficient budgets + truncation | 4.50e-15 | 9.75e-10 |
| amplitude S1 (conj of miepython's) | m=0.75, x=30, theta=170 deg | -2.02359743257+1.37785016349j | -2.02359743257+1.37785016357j | 7.67e-11 | 1.35e-10 | pass | coefficient budgets + truncation | 1.96e-14 | 7.67e-11 |
| amplitude S2 (conj of miepython's) | m=0.75, x=30, theta=170 deg | 0.333730734196-2.28384884972j | 0.333730734196-2.28384884705j | 2.67e-09 | 2.73e-09 | pass | coefficient budgets + truncation | 1.47e-14 | 2.67e-09 |
| amplitude S1 (conj of miepython's) | m=0.75, x=30, theta=180 deg | 0.915690117732+2.6341125992j | 0.915690117731+2.63411259243j | 6.78e-09 | 6.97e-09 | pass | coefficient budgets + truncation | 1.17e-14 | 6.78e-09 |
| amplitude S2 (conj of miepython's) | m=0.75, x=30, theta=180 deg | -0.915690117732-2.6341125992j | -0.915690117731-2.63411259243j | 6.78e-09 | 6.97e-09 | pass | coefficient budgets + truncation | 1.17e-14 | 6.78e-09 |
| coefficient a_n | m=0.75, x=30, n=1 | 0.769875528641+0.420912341278j | 0.769875528641+0.420912341278j | 2.07e-15 | 1.14e-13 | pass | stated bound + 16N u | 6.21e-16 | 1.45e-15 |
| coefficient b_n | m=0.75, x=30, n=1 | 0.941031752408+0.2355652635j | 0.941031752408+0.2355652635j | 1.27e-15 | 1.14e-13 | pass | stated bound + 16N u | 3.78e-16 | 8.97e-16 |
| coefficient a_n | m=0.75, x=30, n=22 | 0.0627629799487+0.242536158741j | 0.0627629799487+0.242536158741j | 1.44e-15 | 1.20e-13 | pass | stated bound + 16N u | 5.10e-16 | 9.26e-16 |
| coefficient b_n | m=0.75, x=30, n=22 | 0.00074648756042+0.027311724895j | 0.000746487560421+0.027311724895j | 1.50e-15 | 1.20e-13 | pass | stated bound + 16N u | 6.50e-16 | 8.55e-16 |
| coefficient a_n | m=0.75, x=30, n=44 | 2.17738740183e-18+1.47559730341e-09j | 2.17738740183e-18+1.47559730341e-09j | 2.07e-24 | 1.05e-13 | pass | stated bound + 16N u | 2.07e-25 | 1.86e-24 |
| coefficient b_n | m=0.75, x=30, n=44 | 9.79151850599e-20+3.12914021833e-10j | 9.79151850599e-20+3.12914021833e-10j | 0.00e+00 | 1.05e-13 | pass | stated bound + 16N u | 3.62e-25 | 3.62e-25 |
| efficiencies Qext | m=0.75, x=300 | 2.06719392821344 | 2.06719392821344 | 1.33e-15 | 3.44e-12 | pass | coefficient budgets + truncation | 0.00e+00 | 1.33e-15 |
| efficiencies Qsca | m=0.75, x=300 | 2.06719392821344 | 2.06719392821344 | 1.33e-15 | 3.07e-12 | pass | coefficient budgets + truncation | 0.00e+00 | 1.33e-15 |
| efficiencies Qback | m=0.75, x=300 | 0.0223302181552981 | 0.0223302184596924 | 3.04e-10 | 9.60e-08 | pass | coefficient budgets + truncation | 4.16e-17 | 3.04e-10 |
| efficiencies g | m=0.75, x=300 | 0.851672547007251 | 0.851672547007251 | 2.22e-16 | 2.71e-12 | pass | coefficient budgets + truncation | 2.22e-16 | 4.44e-16 |
| amplitude S1 (conj of miepython's) | m=0.75, x=300, theta=0 deg | 46511.8633848+2109.1917666j | 46511.8633848+2109.19176408j | 2.52e-06 | 2.59e-06 | pass | coefficient budgets + truncation | 3.50e-11 | 2.52e-06 |
| amplitude S2 (conj of miepython's) | m=0.75, x=300, theta=0 deg | 46511.8633848+2109.1917666j | 46511.8633848+2109.19176408j | 2.52e-06 | 2.59e-06 | pass | coefficient budgets + truncation | 3.50e-11 | 2.52e-06 |
| amplitude S1 (conj of miepython's) | m=0.75, x=300, theta=30 deg | -322.245754838-244.705823473j | -322.245754838-244.705823381j | 9.17e-08 | 9.58e-08 | pass | coefficient budgets + truncation | 4.82e-13 | 9.17e-08 |
| amplitude S2 (conj of miepython's) | m=0.75, x=300, theta=30 deg | -355.933810447-203.540995526j | -355.933810447-203.54099535j | 1.76e-07 | 1.80e-07 | pass | coefficient budgets + truncation | 1.11e-12 | 1.76e-07 |
| amplitude S1 (conj of miepython's) | m=0.75, x=300, theta=90 deg | -12.5407661163+63.3775235501j | -12.5407661163+63.3775235896j | 3.95e-08 | 4.18e-08 | pass | coefficient budgets + truncation | 2.77e-13 | 3.95e-08 |
| amplitude S2 (conj of miepython's) | m=0.75, x=300, theta=90 deg | 16.5956943925+33.8849184163j | 16.5956943925+33.8849184913j | 7.50e-08 | 7.73e-08 | pass | coefficient budgets + truncation | 1.57e-13 | 7.50e-08 |
| amplitude S1 (conj of miepython's) | m=0.75, x=300, theta=137.9 deg | -28.6412929122-36.1348353511j | -28.6412929122-36.134835309j | 4.21e-08 | 4.57e-08 | pass | coefficient budgets + truncation | 5.47e-13 | 4.21e-08 |
| amplitude S2 (conj of miepython's) | m=0.75, x=300, theta=137.9 deg | 17.2599169775+21.4489389922j | 17.2599169775+21.4489390722j | 8.00e-08 | 8.36e-08 | pass | coefficient budgets + truncation | 1.53e-13 | 8.00e-08 |
| amplitude S1 (conj of miepython's) | m=0.75, x=300, theta=170 deg | -17.5644277353-8.79021605569j | -17.5644277353-8.79021612951j | 7.38e-08 | 8.12e-08 | pass | coefficient budgets + truncation | 2.92e-13 | 7.38e-08 |
| amplitude S2 (conj of miepython's) | m=0.75, x=300, theta=170 deg | 16.553712948+0.892778288721j | 16.553712948+0.892778147225j | 1.41e-07 | 1.49e-07 | pass | coefficient budgets + truncation | 2.26e-13 | 1.41e-07 |
| amplitude S1 (conj of miepython's) | m=0.75, x=300, theta=180 deg | -19.9429565398+10.2327119057j | -19.9429565398+10.2327122403j | 3.35e-07 | 4.12e-07 | pass | coefficient budgets + truncation | 7.23e-14 | 3.35e-07 |
| amplitude S2 (conj of miepython's) | m=0.75, x=300, theta=180 deg | 19.9429565398-10.2327119057j | 19.9429565398-10.2327122403j | 3.35e-07 | 4.12e-07 | pass | coefficient budgets + truncation | 7.23e-14 | 3.35e-07 |
| coefficient a_n | m=0.75, x=300, n=1 | 0.093220505223-0.290741195273j | 0.0932205052231-0.290741195273j | 1.85e-14 | 8.45e-13 | pass | stated bound + 16N u | 1.69e-15 | 1.68e-14 |
| coefficient b_n | m=0.75, x=300, n=1 | 0.237297161688-0.42542592627j | 0.237297161688-0.42542592627j | 1.61e-14 | 8.45e-13 | pass | stated bound + 16N u | 2.22e-15 | 1.39e-14 |
| coefficient a_n | m=0.75, x=300, n=164 | 0.96063967887+0.194450729623j | 0.96063967887+0.194450729623j | 2.29e-15 | 8.28e-13 | pass | stated bound + 16N u | 5.98e-16 | 2.89e-15 |
| coefficient b_n | m=0.75, x=300, n=164 | 0.99311438673-0.0826934193277j | 0.99311438673-0.0826934193277j | 2.87e-15 | 8.28e-13 | pass | stated bound + 16N u | 6.89e-16 | 3.56e-15 |
| coefficient a_n | m=0.75, x=300, n=329 | 5.39396744534e-17+7.3443634478e-09j | 5.39396744534e-17+7.3443634478e-09j | 1.46e-22 | 7.38e-13 | pass | stated bound + 16N u | 7.44e-24 | 1.39e-22 |
| coefficient b_n | m=0.75, x=300, n=329 | 1.51556535816e-17+3.89302627548e-09j | 1.51556535816e-17+3.89302627548e-09j | 7.61e-23 | 7.38e-13 | pass | stated bound + 16N u | 3.31e-24 | 7.28e-23 |
| efficiencies Qext | m=(2+1j), x=0.1 | 0.11874022264274 | 0.118740222636743 | 6.00e-12 | 6.10e-12 | pass | coefficient budgets + truncation | 4.16e-17 | 6.00e-12 |
| efficiencies Qsca | m=(2+1j), x=0.1 | 0.000130829646870973 | 0.000130829646870973 | 2.71e-20 | 4.21e-18 | pass | coefficient budgets + truncation | 8.13e-20 | 5.42e-20 |
| efficiencies Qback | m=(2+1j), x=0.1 | 0.000195247303680279 | 0.000195247303704449 | 2.42e-14 | 2.43e-14 | pass | coefficient budgets + truncation | 2.71e-20 | 2.42e-14 |
| efficiencies g | m=(2+1j), x=0.1 | 0.00219048172730726 | 0.00219048172730725 | 1.08e-17 | 1.24e-10 | pass | coefficient budgets + truncation | 3.69e-17 | 2.60e-17 |
| amplitude S1 (conj of miepython's) | m=(2+1j), x=0.1, theta=0 deg | 0.000296850556607-0.000636387521267j | 0.000296850556592-0.000636387521226j | 4.34e-14 | 4.37e-14 | pass | coefficient budgets + truncation | 2.42e-19 | 4.34e-14 |
| amplitude S2 (conj of miepython's) | m=(2+1j), x=0.1, theta=0 deg | 0.000296850556607-0.000636387521267j | 0.000296850556592-0.000636387521226j | 4.34e-14 | 4.37e-14 | pass | coefficient budgets + truncation | 2.42e-19 | 4.34e-14 |
| amplitude S1 (conj of miepython's) | m=(2+1j), x=0.1, theta=30 deg | 0.000296640339385-0.000636221673018j | 0.000296640339378-0.000636221672998j | 2.11e-14 | 2.13e-14 | pass | coefficient budgets + truncation | 1.21e-19 | 2.11e-14 |
| amplitude S2 (conj of miepython's) | m=(2+1j), x=0.1, theta=30 deg | 0.000257174927167-0.000551006029477j | 0.000257174927172-0.000551006029493j | 1.63e-14 | 1.64e-14 | pass | coefficient budgets + truncation | 1.95e-19 | 1.63e-14 |
| amplitude S1 (conj of miepython's) | m=(2+1j), x=0.1, theta=90 deg | 0.000295282661304-0.000635150388725j | 0.000295282661304-0.000635150388725j | 1.58e-17 | 8.84e-17 | pass | coefficient budgets + truncation | 1.08e-19 | 1.59e-17 |
| amplitude S2 (conj of miepython's) | m=(2+1j), x=0.1, theta=90 deg | 1.10650121626e-06-8.7499662639e-08j | 1.10650120503e-06-8.74996320796e-08j | 3.26e-14 | 3.26e-14 | pass | coefficient budgets + truncation | 2.58e-20 | 3.26e-14 |
| amplitude S1 (conj of miepython's) | m=(2+1j), x=0.1, theta=137.9 deg | 0.000294121091857-0.000634233623182j | 0.00029412109186-0.000634233623189j | 6.89e-15 | 7.00e-15 | pass | coefficient budgets + truncation | 2.17e-19 | 6.89e-15 |
| amplitude S2 (conj of miepython's) | m=(2+1j), x=0.1, theta=137.9 deg | -0.000217733760709+0.000470546733149j | -0.000217733760697+0.000470546733114j | 3.67e-14 | 3.68e-14 | pass | coefficient budgets + truncation | 7.67e-20 | 3.67e-14 |
| amplitude S1 (conj of miepython's) | m=(2+1j), x=0.1, theta=170 deg | 0.000293741263858-0.000633933800451j | 0.000293741263872-0.000633933800489j | 4.05e-14 | 4.07e-14 | pass | coefficient budgets + truncation | 3.43e-19 | 4.05e-14 |
| amplitude S2 (conj of miepython's) | m=(2+1j), x=0.1, theta=170 deg | -0.000289245340751+0.000624300286335j | -0.000289245340763+0.000624300286367j | 3.42e-14 | 3.44e-14 | pass | coefficient budgets + truncation | 1.21e-19 | 3.42e-14 |
| amplitude S1 (conj of miepython's) | m=(2+1j), x=0.1, theta=180 deg | 0.000293717506115-0.000633915046203j | 0.00029371750613-0.000633915046244j | 4.34e-14 | 4.36e-14 | pass | coefficient budgets + truncation | 1.21e-19 | 4.34e-14 |
| amplitude S2 (conj of miepython's) | m=(2+1j), x=0.1, theta=180 deg | -0.000293717506115+0.000633915046203j | -0.00029371750613+0.000633915046244j | 4.34e-14 | 4.36e-14 | pass | coefficient budgets + truncation | 1.21e-19 | 4.34e-14 |
| coefficient a_n | m=(2+1j), x=0.1, n=1 | 0.000196855544348-0.000423433838321j | 0.000196855544348-0.000423433838321j | 6.06e-20 | 7.47e-18 | pass | stated bound + 16N u | 7.67e-20 | 2.71e-20 |
| coefficient b_n | m=(2+1j), x=0.1, n=1 | 8.91008776736e-07-4.4124569021e-07j | 8.91008776736e-07-4.4124569021e-07j | 2.12e-22 | 7.47e-18 | pass | stated bound + 16N u | 1.70e-20 | 1.71e-20 |
| coefficient a_n | m=(2+1j), x=0.1, n=3 | 2.27130974146e-11-5.99985583159e-11j | 2.27130974146e-11-5.99985583159e-11j | 3.23e-27 | 6.22e-18 | pass | stated bound + 16N u | 1.62e-26 | 1.45e-26 |
| coefficient b_n | m=(2+1j), x=0.1, n=3 | 4.03176437425e-14-2.0106428571e-14j | 4.03176437425e-14-2.0106428571e-14j | 0.00e+00 | 6.22e-18 | pass | stated bound + 16N u | 1.69e-27 | 1.69e-27 |
| efficiencies Qext | m=(2+1j), x=10 | 2.42406816055642 | 2.42406816047519 | 8.12e-11 | 8.19e-11 | pass | coefficient budgets + truncation | 0.00e+00 | 8.12e-11 |
| efficiencies Qsca | m=(2+1j), x=10 | 1.36638674643902 | 1.36638674643902 | 0.00e+00 | 1.56e-13 | pass | coefficient budgets + truncation | 0.00e+00 | 0.00e+00 |
| efficiencies Qback | m=(2+1j), x=10 | 0.198550007746399 | 0.198550008015876 | 2.69e-10 | 2.81e-10 | pass | coefficient budgets + truncation | 5.83e-16 | 2.69e-10 |
| efficiencies g | m=(2+1j), x=10 | 0.818924929080402 | 0.818924929080402 | 0.00e+00 | 2.08e-13 | pass | coefficient budgets + truncation | 1.11e-16 | 1.11e-16 |
| amplitude S1 (conj of miepython's) | m=(2+1j), x=10, theta=0 deg | 60.6017040139+6.2412735817j | 60.6017040119+6.24127358424j | 3.26e-09 | 3.28e-09 | pass | coefficient budgets + truncation | 9.44e-15 | 3.26e-09 |
| amplitude S2 (conj of miepython's) | m=(2+1j), x=10, theta=0 deg | 60.6017040139+6.2412735817j | 60.6017040119+6.24127358424j | 3.26e-09 | 3.28e-09 | pass | coefficient budgets + truncation | 9.44e-15 | 3.26e-09 |
| amplitude S1 (conj of miepython's) | m=(2+1j), x=10, theta=30 deg | -8.25008769486+0.222722187421j | -8.25008769465+0.222722187333j | 2.31e-10 | 2.35e-10 | pass | coefficient budgets + truncation | 7.15e-15 | 2.31e-10 |
| amplitude S2 (conj of miepython's) | m=(2+1j), x=10, theta=30 deg | -4.69791997464-1.58250858145j | -4.69791997437-1.58250858197j | 5.83e-10 | 5.87e-10 | pass | coefficient budgets + truncation | 2.22e-15 | 5.83e-10 |
| amplitude S1 (conj of miepython's) | m=(2+1j), x=10, theta=90 deg | 2.71855516772+0.985005287177j | 2.71855516772+0.985005287217j | 4.04e-11 | 4.26e-11 | pass | coefficient budgets + truncation | 1.26e-15 | 4.04e-11 |
| amplitude S2 (conj of miepython's) | m=(2+1j), x=10, theta=90 deg | -1.63964373738-0.853701704987j | -1.63964373737-0.853701705037j | 5.17e-11 | 5.38e-11 | pass | coefficient budgets + truncation | 1.12e-15 | 5.17e-11 |
| amplitude S1 (conj of miepython's) | m=(2+1j), x=10, theta=137.9 deg | -1.28639754518+1.97596373918j | -1.28639754545+1.9759637392j | 2.68e-10 | 2.71e-10 | pass | coefficient budgets + truncation | 3.14e-16 | 2.68e-10 |
| amplitude S2 (conj of miepython's) | m=(2+1j), x=10, theta=137.9 deg | 1.29137685044-1.68809426508j | 1.29137685008-1.68809426431j | 8.51e-10 | 8.55e-10 | pass | coefficient budgets + truncation | 1.29e-15 | 8.51e-10 |
| amplitude S1 (conj of miepython's) | m=(2+1j), x=10, theta=170 deg | 1.40213150744+1.73207503877j | 1.4021315068+1.73207503875j | 6.38e-10 | 6.45e-10 | pass | coefficient budgets + truncation | 7.96e-15 | 6.38e-10 |
| amplitude S2 (conj of miepython's) | m=(2+1j), x=10, theta=170 deg | -1.34456138696-1.76467590519j | -1.34456138785-1.76467590326j | 2.12e-09 | 2.13e-09 | pass | coefficient budgets + truncation | 2.00e-15 | 2.12e-09 |
| amplitude S1 (conj of miepython's) | m=(2+1j), x=10, theta=180 deg | 1.55261395616+1.59785484222j | 1.55261395584+1.59785484463j | 2.44e-09 | 2.46e-09 | pass | coefficient budgets + truncation | 4.53e-15 | 2.44e-09 |
| amplitude S2 (conj of miepython's) | m=(2+1j), x=10, theta=180 deg | -1.55261395616-1.59785484222j | -1.55261395584-1.59785484463j | 2.44e-09 | 2.46e-09 | pass | coefficient budgets + truncation | 4.53e-15 | 2.44e-09 |
| coefficient a_n | m=(2+1j), x=10, n=1 | 0.359459817111+0.171530503798j | 0.359459817111+0.171530503798j | 1.24e-16 | 4.41e-14 | pass | stated bound + 16N u | 2.78e-17 | 1.14e-16 |
| coefficient b_n | m=(2+1j), x=10, n=1 | 0.641931707896-0.175172103613j | 0.641931707896-0.175172103613j | 1.11e-16 | 4.41e-14 | pass | stated bound + 16N u | 8.33e-17 | 2.78e-17 |
| coefficient a_n | m=(2+1j), x=10, n=10 | 0.405707961141+0.00930831192957j | 0.405707961141+0.00930831192957j | 2.78e-16 | 4.21e-14 | pass | stated bound + 16N u | 1.00e-16 | 2.33e-16 |
| coefficient b_n | m=(2+1j), x=10, n=10 | 0.15521013027+0.213445438695j | 0.15521013027+0.213445438695j | 5.55e-17 | 4.21e-14 | pass | stated bound + 16N u | 1.39e-16 | 1.14e-16 |
| coefficient a_n | m=(2+1j), x=10, n=20 | 8.70529832131e-10-1.82077128992e-09j | 8.70529832131e-10-1.82077128992e-09j | 1.73e-23 | 4.01e-14 | pass | stated bound + 16N u | 1.03e-25 | 1.73e-23 |
| coefficient b_n | m=(2+1j), x=10, n=20 | 6.22795958132e-10+1.03795899933e-10j | 6.22795958132e-10+1.03795899933e-10j | 2.32e-23 | 4.01e-14 | pass | stated bound + 16N u | 1.66e-25 | 2.32e-23 |
| efficiencies Qext | m=(10+10j), x=50 | 2.09672646582453 | 2.09672646576019 | 6.43e-11 | 6.62e-11 | pass | coefficient budgets + truncation | 4.44e-16 | 6.43e-11 |
| efficiencies Qsca | m=(10+10j), x=50 | 1.85532538303658 | 1.85532538303658 | 1.33e-15 | 1.01e-12 | pass | coefficient budgets + truncation | 6.66e-16 | 6.66e-16 |
| efficiencies Qback | m=(10+10j), x=50 | 0.814321824696593 | 0.814321840562552 | 1.59e-08 | 1.65e-08 | pass | coefficient budgets + truncation | 4.44e-16 | 1.59e-08 |
| efficiencies g | m=(10+10j), x=50 | 0.55795934396761 | 0.55795934396761 | 1.11e-16 | 8.24e-13 | pass | coefficient budgets + truncation | 1.11e-16 | 0.00e+00 |
| amplitude S1 (conj of miepython's) | m=(10+10j), x=50, theta=0 deg | 1310.45404114+5.1555668183j | 1310.4540411+5.15556686649j | 6.28e-08 | 6.39e-08 | pass | coefficient budgets + truncation | 1.15e-12 | 6.28e-08 |
| amplitude S2 (conj of miepython's) | m=(10+10j), x=50, theta=0 deg | 1310.45404114+5.1555668183j | 1310.4540411+5.15556686649j | 6.28e-08 | 6.39e-08 | pass | coefficient budgets + truncation | 1.15e-12 | 6.28e-08 |
| amplitude S1 (conj of miepython's) | m=(10+10j), x=50, theta=30 deg | 16.1868820402+24.2222601764j | 16.1868820443+24.2222602212j | 4.51e-08 | 4.52e-08 | pass | coefficient budgets + truncation | 4.63e-14 | 4.51e-08 |
| amplitude S2 (conj of miepython's) | m=(10+10j), x=50, theta=30 deg | 0.115601565115-17.4698315591j | 0.115601571554-17.4698316167j | 5.79e-08 | 5.80e-08 | pass | coefficient budgets + truncation | 4.29e-14 | 5.79e-08 |
| amplitude S1 (conj of miepython's) | m=(10+10j), x=50, theta=90 deg | 23.3386540504+1.09059328035j | 23.33865405+1.09059327481j | 5.56e-09 | 5.63e-09 | pass | coefficient budgets + truncation | 2.22e-14 | 5.56e-09 |
| amplitude S2 (conj of miepython's) | m=(10+10j), x=50, theta=90 deg | -22.0837929885-2.28555118283j | -22.0837929892-2.28555117601j | 6.86e-09 | 6.94e-09 | pass | coefficient budgets + truncation | 2.98e-14 | 6.86e-09 |
| amplitude S1 (conj of miepython's) | m=(10+10j), x=50, theta=137.9 deg | -19.23964658+12.2061463274j | -19.2396465799+12.2061463271j | 3.17e-10 | 4.35e-10 | pass | coefficient budgets + truncation | 6.40e-15 | 3.17e-10 |
| amplitude S2 (conj of miepython's) | m=(10+10j), x=50, theta=137.9 deg | 19.0077476747-11.8425516176j | 19.0077476748-11.8425516176j | 1.55e-10 | 2.72e-10 | pass | coefficient budgets + truncation | 3.28e-14 | 1.55e-10 |
| amplitude S1 (conj of miepython's) | m=(10+10j), x=50, theta=170 deg | -19.0567173419+12.2026587309j | -19.056717341+12.2026587274j | 3.61e-09 | 3.87e-09 | pass | coefficient budgets + truncation | 6.08e-14 | 3.61e-09 |
| amplitude S2 (conj of miepython's) | m=(10+10j), x=50, theta=170 deg | 19.0894615723-12.16366909j | 19.0894615731-12.1636690885j | 1.68e-09 | 1.94e-09 | pass | coefficient budgets + truncation | 2.08e-14 | 1.68e-09 |
| amplitude S1 (conj of miepython's) | m=(10+10j), x=50, theta=180 deg | -13.0576102294+18.3970094182j | -13.0576102356+18.3970096833j | 2.65e-07 | 2.66e-07 | pass | coefficient budgets + truncation | 2.71e-14 | 2.65e-07 |
| amplitude S2 (conj of miepython's) | m=(10+10j), x=50, theta=180 deg | 13.0576102294-18.3970094182j | 13.0576102356-18.3970096833j | 2.65e-07 | 2.66e-07 | pass | coefficient budgets + truncation | 2.71e-14 | 2.65e-07 |
| coefficient a_n | m=(10+10j), x=50, n=1 | 0.124311487554-0.252176249122j | 0.124311487554-0.252176249122j | 9.37e-16 | 1.91e-13 | pass | stated bound + 16N u | 3.24e-16 | 8.15e-16 |
| coefficient b_n | m=(10+10j), x=50, n=1 | 0.875734758612+0.252172419899j | 0.875734758612+0.252172419899j | 1.69e-15 | 1.91e-13 | pass | stated bound + 16N u | 1.11e-16 | 1.59e-15 |
| coefficient a_n | m=(10+10j), x=50, n=33 | 0.811603948285-0.306481835229j | 0.811603948285-0.306481835229j | 6.73e-15 | 1.81e-13 | pass | stated bound + 16N u | 5.24e-16 | 6.56e-15 |
| coefficient b_n | m=(10+10j), x=50, n=33 | 0.181806818281+0.338118776363j | 0.181806818281+0.338118776363j | 3.88e-15 | 1.81e-13 | pass | stated bound + 16N u | 3.14e-16 | 3.80e-15 |
| coefficient a_n | m=(10+10j), x=50, n=66 | 1.52999570096e-09-1.32085467184e-08j | 1.52999570096e-09-1.32085467184e-08j | 4.43e-21 | 1.51e-13 | pass | stated bound + 16N u | 2.49e-23 | 4.43e-21 |
| coefficient b_n | m=(10+10j), x=50, n=66 | 9.01608597275e-10+1.02738579616e-08j | 9.01608597277e-10+1.02738579616e-08j | 2.63e-21 | 1.51e-13 | pass | stated bound + 16N u | 1.50e-23 | 2.63e-21 |
