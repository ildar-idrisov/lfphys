# Response (demonstration worlds v01, v02, v06, v07, v08, v13–v17) to review UX-ui (2026-11-04): U13, U19

Processed on 2026-11-05 by a subagent (Claude) that did not write the review (agent H). This file covers **U13**
(refusals in the engine's language) and **U19** (units missing on primary parameters) for the worlds v01, v02, v06,
v07, v08, v13, v14, v15, v16, v17. The framework's part of U13 (the range texts of `params.py`, the translation of
library messages) is in `RESPONSE_framework.md`; the playgrounds' in their agents' files. The review's evidence for U13
and U19 names p02–p04, v10, v11, v12 and v15; v15's «incl: 179.3 > max 179.0» is the framework's range text (its P2).
The work behind these items, with the scripts and screenshots, is in
`../2026-11-04_internal_UX-params/RESPONSE_v-worlds.md` and its `response_checks_v-worlds/`.

| ID | one line | decision | status tag | where | verified by |
|---|---|---|---|---|---|
| U13 (these worlds) | refusals in English, with internal ids, or without what to change | **fixed** | [useful] | see below | the tests and browser shots named below |
| U19 (these worlds) | units missing on primary parameters | **checked: none missing**; one label made explicit | [neutral] | `v06_qcd/viz.py` | `response_checks_v-worlds/labels.py`, `labels.out` |

## U13 — the refusals of these worlds, in the owner's terms

Every refusal found in these worlds that came in English, with an internal id, or without saying what to change is now
a Russian text that names the parameter by its label, gives the numbers, and says what to change (the framework's
`Refusal(text, hint)` where it helps: «… Что изменить: …»):

- **v15** (UX-params P6): «the metric is not regular outside the horizon …», «the photon shell is not a single band …»,
  `float() argument … 'complex'` → what fails (A₁ ≤ 0, det g = 0, closed timelike curves, no single band of photon
  orbits) and, for each deviation with the others as they are, the values the world takes; the inclination at which no
  photon orbit is visible; a notice instead of the engine's English when the circular orbits are not found.
- **v01** (P7, P12): «worldline is not timelike» → the walkers' speed against this world's light, with the speed and
  the factor to choose; two laws that do not go together → which choice to make.
- **v02** (P8, P17, P18): «элемент 'rot_y' не подходит для этой частицы», «щели №5 нет», «Unable to allocate 2.03 GiB
  …», «array is too big …» → the element by its label, the particle, and the elements that act on it; the slit
  number's range; the shift, the grid, the size and the probe wavelength that fits; the dark counts per particle and
  the numbers to change.
- **v06** (P5): «RG integration failed» → the Landau pole (the curve ends, a notice says where); a genuine failure of
  the integrator in Russian with what to choose.
- **v13, v14** (P10): «нужно 0 ≤ l < n …», «второе состояние совпадает с первым» → the numbers are fitted and said; an
  equal or non-orthogonal second state chosen by hand is refused with what to change.
- **v16** (P11): «порядки голограммы не разойдутся: уменьшите период Λ или увеличьте перетяжку w0» (advice that could
  not be followed) → the waist is chosen by the world; a period no waist can take is refused with the largest period
  that works.
- **v17** (P16): an index-matched drop → why it is refused and what to change.
- **v08** (P26): the window refusal → what to change and a scenario that works for that source.

**Verified.** The worlds' tests named in the UX-params response (each checks the text, and that the named alternative
works), e.g. v15's test asserts no English word in its refusals; in the browser, the catalogue's form shows them
(`../2026-11-04_internal_UX-params/response_checks_v-worlds/pw_final/shots/v01_*_refused.png`, `v02_dark_refused.png`,
`v15_jp_refused.png`, `v16_fork_period8_refused.png`, `v17_matched_refused.png`).

## U19 — units

Every numeric parameter of these worlds was listed with its label (`labels.out`). Lengths, times, energies, masses,
speeds, rates, angles and frequencies carry their units in the label («Длина волны, нм», «Масса тела, M☉», «Источник:
расстояние, rs», «Полуширина экрана, M», «Длина области, в z_R», «Скорость, × c»); the rest are dimensionless and say
what they are (quantum numbers, shares, indices, the Born exponent, the deviations α of the Johannsen metric in units of
M). One label was made explicit: v06 «κ (кулоновская часть)» → «κ (кулоновская часть, безразмерная)». The labels the
review names (v11, v12) are not in these worlds.

## Changes for the integrator

None from this part.
