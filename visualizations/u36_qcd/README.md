# u36 — QCD: asymptotic freedom and quarkonium

**English** | [Русский](README.ru.md)

A wrapper over `lfphys`.

* `lfphys.core.qcd.running`: alpha_s(mu) from the renormalisation-group equation with the MS-bar beta function to
  1-4 loops (coefficients of van Ritbergen, Vermaseren & Larin 1997, verified against the paper), quark thresholds at
  the PDG 2024 MS-bar masses m_q(m_q) with the decoupling relation of one loop less than the running (RunDec /
  Chetyrkin-Kniehl-Steinhauser: continuous at 1-2 loops, the (11/72)(alpha_s/pi)^2 and the three-loop term at 3-4
  loops; until 2026-10-23 the matching was continuous at every order, which shifted alpha_s(m_tau) by -1.5e-3 and
  alpha_s just below m_c by -5.6e-3 relative at 4 loops), from the PDG 2024 world average alpha_s(M_Z) =
  0.1180 +- 0.0009 (`lfphys.core.data`). Play sweeps the probe scale over 1 GeV - 10 TeV; the world's time is the
  logarithm of the scale; a live change of the sweep speed continues from the probe's current scale.
* `lfphys.core.qcd.su3`: the Casimirs C_F = 4/3 and C_A = 3 computed from the Gell-Mann matrices (checks).
* `lfphys.theories.models.cornell` + `lfphys.core.quantum.radial`: quarkonium in V = -kappa/r + r/a^2 with the fitted
  parameters quoted by Eichten & Quigg (1995) for the model of Eichten et al. (1980) (the original 1980 text could not
  be read; `lfphys/sources/verification_2026-10-23.md`). The model fixes no absolute mass scale: the 1S level is
  anchored to the measured spin-averaged mass and the model predicts the splittings, compared with PDG 2024 within
  10 % (model outside the core). The radial box grows with the size of the highest state (its turning point plus
  8 decay lengths), so the levels are not box levels (residual < 1 MeV); quark masses below 1 GeV are refused: the
  non-relativistic heavy-quark model means nothing there.
* The model's kappa is shown next to 4/3 alpha_s(1/<r>) of the core at the bound state's scale (a comparison of two
  layers, not a check: shown as ≈, never as a failure).

Checks: one-loop and two-loop closed forms (the one-loop check at 2 GeV is skipped, with the reason, when a large
alpha_s(M_Z) puts the Landau pole above 2 GeV), the jump at each quark threshold against the decoupling relation
written out in the check (on the side away from M_Z), convergence of the loop expansion at 2 GeV, the Casimirs, the
model splittings against PDG. On the plot values above 0.5 leave the frame (towards the Landau pole) and are marked. alpha_s(M_Z) is a world parameter with its PDG value as the standard: a
different value is a declared modification. A coupling pushed past the pole bound by a threshold's matching is the
Landau pole there (α_s(M_Z) = 0.19 at 4 loops: at m_b; it was refused as "RG integration failed", review UX-params P5).
Failures that are the point of a world carry "Expected: …" (the convergence check at a changed α_s(M_Z), the levels of a
model with other parameters than the fit; P23), and the preset "What if α_s(M_Z) = 0.15 (a changed coupling)" (`strong`) says so.

Limits: perturbative running below ~1.5 GeV is not reliable (the curve starts at 1 GeV for orientation); no lattice
QCD; quarkonium without spin-dependent forces, relativistic corrections or coupled channels.

Tests: `tests/test_u36_qcd.py`.
