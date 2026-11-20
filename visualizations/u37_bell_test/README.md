# u37 — The Bell test with entangled pairs

**English** | [Русский](README.ru.md)

Pairs of polarisation-entangled photons or spin-½ singlets fly from a source to two stations; each station chooses one
of two settings of its analyser per locally defined time slot; two **real detectors** behind each analyser click with
their efficiency, dark counts, dead time and timing jitter; the run counts coincidences and the slots' outcomes and
estimates the correlations E, the CHSH parameter S under the fair-sampling assumption (so named), and the CH and
CH–Eberhard J inequalities, which need no such assumption. Owner guide: `../README.md`; rules: `../RULES.md`; design:
`../../lfphys/sources/explore_EX2_2026-11-18_design.md` §4.

The visualization is a **wrapper over the engine `lfphys`** (`../../lfphys/LAYERS.md`): every law comes from an engine
module; the folder's own code is the time line, the apparatus logic (stations, slots, choices, coincidence logic,
bookkeeping), the messages and the drawing.

| engine module | layer | used for |
|---|---|---|
| `core.quantum.qubits` | core | the states `PHI_PLUS`, `SINGLET`, `eberhard_state(r)`, `werner(ψ, V)`; polariser and Stern–Gerlach projectors; the joint Born probabilities of a pair (`joint_probabilities`, `sample_pairs`); `correlation`, `chsh`, `concurrence`, `entropy` |
| `theories.models.photodetector` | theories (model) | the detectors: `Detector`, `DEVICES["spcm_nir_800_13"]` (the default), `detect` (efficiency, Poisson dark and background counts, the non-paralysable dead time), `detector_rate`, `coincidence_rates`, `window_share`, `dark_click_probability`, `slot_coupling`, `pair_slots` (the slots simulated in time: the independent check of the counting by slots and the slots shown) |
| `tools.bell_stats` | tools | E, S and their errors; `accidentals`, `chsh_subtracted`; `slot_probabilities`, `sample_counts`, `plus_table`, `j_estimate`, `ch_estimate`, `j_value`, `ch_value`; `threshold_efficiency` (the thresholds table) |
| `theories.alternatives.local_hidden` | theories (alternative) | the local worlds: `polarization_model` (photons), `sign_model` (spin), `gisin_gisin` and `gisin_gisin_table` (Gisin and Gisin's detection-loophole model); in a quantum world only the comparison curves |
| `core.causality` | core | the interval s², the causal relation, the order-reversal speed of each coincidence's events |
| `core.relativity` | core | `boost_matrix`: an independent check of the order-reversal speed |
| `core.constants` | core | c |

## The screens

* **Watch** — «Pairs, S above 2, and a local model» (recording `story`, 50 s at 20 frames per second): the first two
  pairs' flights slowly (the script's speed changes sit on the run's own emission times, 190.9 µs and 501.1 µs), then
  about 200 coincidences per played second; S passes 2 under fair sampling and settles near 2√2 (at 33.95 s: S =
  2.804 ± 0.040 after 4 975 coincidences, 19.9 standard errors above 2); at 34 s a new world of local hidden
  variables (flagged «MODIFIED PHYSICS»), where S stays near √2. Captions in English and Russian; each comes no later
  than its event (`tests/test_u37_screens.py`). «More recordings»: `chsh`, `local_model`, `scan`.
* **Explore** — the CHSH bench (156 points): «Pairs» (photons, spin ½) × «Angle step Δ» (a = 0, b = Δ, a′ = 2Δ,
  b′ = 3Δ; 0–90° by 7.5°) × «Choice before its slot τ» (100 ns, 5 µs) × «Law and source» (quantum with an ideal
  source, quantum with a source of visibility 0.85, local hidden variables — modified physics). Each point: the
  devices' default values, 10⁴ pairs per second, slots of 1 µs, stopped 0.1 s of world time after the
  4 000th coincidence. Readouts: S with its
  error and the law's value, (|S| − 2)/σ, the coincidences counted. Earlier points stay as traces on the S(Δ) plot.
* **Lab work** — the bench «Entangled photons and the Bell inequality», four parts (a bench, not a test: nothing is
  hidden, the fit prints its output and judges nothing):
  1. «The correlation E(α, β)»: fixed settings, «Pairs» × Alice's angle α {0°, 45°, 90°} × Bob's angle β (0–180° by
     7.5°), 1 000 coincidences each; the four coincidence counters (√N), E of the run with its error; formula columns E
     from the four counts, cos 2(β − α), cos(β − α).
  2. «The CHSH test» and 3. «The same test in a local world»: Explore's points (one atlas); E of the four setting pairs
     with the run's errors, the fraction of coincidences outside the cone; formula columns S = E₁ − E₂ + E₃ + E₄,
     3 cos 2Δ − cos 6Δ, −(3 cos Δ − cos 3Δ).
  4. «Real detectors»: 10⁹ slots of 1 µs at 10⁴ pairs per second (189 points): «Detection efficiency η» {0.60, 0.70,
     0.75, 0.80, 0.85, 0.90, 1.00} × «Source» (|Φ+⟩ at the CHSH angles, Eberhard's state r = −2.9 at Giustina's angles,
     Gisin and Gisin's local model — modified physics) × «Dark and background counts» (the detectors' 250 dark counts
     per second; 10⁵ background counts per second; none — an idealisation) × «Coincidence window w» (0.5, 2, 25 ns).
     Readouts: S, J per pair, coincidences; columns η, the coincidences N_c and the accidentals' estimate N_acc, S
     (fair sampling), S − acc. (the accidentals subtracted), J per pair, CH per slot, J per pair / η.
  The task sheet («bench», «procedure», «record») quotes Dehlinger and Mitchell (2002), Giustina et al. (2015) and
  Gisin and Gisin (1999) verbatim; the teacher's variants preselect the spins, a slow choice, a real source, the local
  world, Alice's analyser at 45°, Eberhard's state without background, Gisin and Gisin's model.

What folds away at `ui: "standard"`: the quick set-up bar and the toolbar (Watch, Explore, Lab work: the screens'
sliders and overlays replace them), the left form (hidden), the panels «Set-up and spacetime», «Counters», «Last
coincidences» (into «How we know this is right»); «▶ Compute live» keeps the full player. Below 1000 px the statistics
are on top, the set-up line a strip under them, the spacetime diagram folded under «Spacetime of the last coincidence».

## The model (all computed in the run)

Geometry: a line, the source at x = 0, Alice's station at x = −L_A, Bob's at x = +L_B (lab frame). Photons fly at c;
spin-½ particles at v = β c (illustrative). The atlases keep L_A = L_B = 500 m; the live player varies them.

1. **Emission**: a Poisson stream of the source's rate, drawn from its own generator in blocks (the same emission times
   whatever the frames of the run; a change of the rate starts a new block at the moment of the change).
2. **Slots and settings**: each station divides its time into slots T_s on its own clock, starting when the first
   particle could arrive (slot k of station X is [L_X/v + k T_s, L_X/v + (k + 1) T_s)), so a pair's two particles fall
   into slots of the same index (Giustina et al. 2015: «locally defined time slots»). With the random choice («random
   for every time slot (as in loophole-free experiments)»), each station's own generator gives a fair bit for slot k
   (0: a or b; 1: a′ or b′), made τ before the slot starts. With «fixed: Alice a, Bob b» the choice event is the moment
   the setting was set.
3. **The ports**: a particle meets the setting of the slot of its arrival. Quantum: the joint Born probabilities of the
   source's state ρ = V|ψ⟩⟨ψ| + (1 − V) I/4 (|Φ+⟩, the singlet or Eberhard's (|VH⟩ + r|HV⟩)/√(1 + r²)); with L_A ≠ L_B
   the first particle by the reduced state, its partner conditioned on it (Lüders). The local models: the engine's
   samplers at the common arrival (they need L_A = L_B; the world refuses otherwise). Gisin and Gisin's model also
   gives «no outcome» for one particle in half of the pairs (detection decided by λ).
4. **The detectors**: two per station, behind the ports «+» and «−», each the engine's `photodetector.detect`:
   efficiency η, Poisson dark and background counts, the non-paralysable dead time (carried from one step of the run to
   the next), then the Gaussian jitter added to the recorded times. A recorded time equal to an arrival identifies the
   pair (the simulation knows it; an experimenter does not).
5. **Coincidences**: every pair of clicks of the two stations within the window w on the delay-compensated times (the
   rule of `photodetector.coincidences`, enumerated), assigned to the setting pair of the clicks' slots. The accidentals'
   estimate is Dehlinger and Mitchell's w·N_A·N_B/T per detector pair, with the singles counted while each angle was in
   force; the run also knows its own accidental coincidences (shown only in the drawer, as a check of the estimate).
6. **Trials**: each slot is a trial; each station's outcome «+», «−», «0» (no click) or «+−» (both clicked). CH and J
   reduce the two detectors to «+»/«0» (`plus_table`) and come from all the trials of the four setting pairs.
7. **Spacetime**: for each coincidence the relation of each station's choice event to the other station's click
   (locality) and, for a true coincidence, to the emission (freedom of choice).

**The counting by slots** («10⁹ slots: the counts from the exact probabilities, a few slots shown in time», part 4 and
the presets `detectors`, `giustina`, `gisin`): the trials ending in each step are split among the setting pairs (a
multinomial of ¼ each); each setting pair's outcome table is drawn from the engine's exact multinomial
(`bell_stats.slot_probabilities`, a Poisson number of pairs per slot μ = R·T_s, dark clicks over the slot); the
coincidences, true and accidental, and the singles from Poisson laws of `photodetector.coincidence_rates` over the
time of that setting pair. 10⁵ slots before the end of each step are simulated in time (`photodetector.pair_slots`,
a generator of their own: Poisson emissions, the ports by the law, each detector's efficiency, dark counts, dead time
and jitter, the clicks binned into the slots): a separate sample of the same process, not added to the counts. Their
outcome tables against the engine's slot probabilities are the run's independent check of the counting by slots
(10⁶ slots per point of part 4; it resolves an error of 10 % in η, not one of 5 %); the last 40 of them are shown in
the strips. The plot of J per pair against η draws the engine's curve for this source, background and angles; its
dashed lines are the thresholds without dark counts or background (Eberhard's 2/3 and |Φ+⟩'s 2/(1 + √2) = 82.8 %),
and a triangle marks where this curve crosses 0 (87.6 % for |Φ+⟩ at the CHSH angles with the SPCM-NIR's dark counts;
90.55 % for Eberhard's state at Giustina's angles, above the 90.23 % of the best angles).

The detectors' default values are a real device, the Excelitas SPCM-NIR (SPCM-800-13) at 800 nm from its product brief
(`photodetector.DEVICES["spcm_nir_800_13"]`): η 0.68, 250 dark counts per second, dead time 20 ns, timing resolution
350 ps read as FWHM (σ = 149 ps). «Ideal detectors (an idealisation)» is a preset.

## Checks (the drawer «How we know this is right»)

* Source: concurrence against (3V − 1)/2 or 2|r|/(1 + r²); one particle's entropy against 1 bit or the binary entropy
  of 1/(1 + r²).
* The law at the current settings, exact: S of the engine's trace against the closed forms (V cos 2Δ, −V cos Δ,
  Eberhard's V(−cos 2α cos 2β + 2r/(1 + r²) sin 2α sin 2β)), absolute tolerance 10⁻¹²; |S| ≤ 2√2; no signalling of the
  law; the local models' |S| ≤ 2 (the polarisation and sign models) or, for Gisin and Gisin's model, |S| of the detected
  pairs above 2 explained (the detection loophole).
* The detectors: the device's identity (for spin pairs, a line that they are an illustration); independent slots
  (t_d + 5σ)/T_s < 0.1; the window's share erf(w/(4σ)) of a pair's two clicks against the run's own share since the
  last «Reset the statistics» (time stream; [error in earlier] until 2026-11-19 the pairs detected at both sides were
  counted over the whole run against the segment's true coincidences, so the check failed after a reset); the singles of each station's two detectors against
  (ηR + d)/(1 + (ηR + d)t_d) (a Poisson z per station: a pair detected at both sides counts at both, so the four
  detectors' sum varies by about 1 + η times its mean; [error in earlier] until 2026-11-19 the sum with one Poisson σ,
  which failed at 5.01σ on an ordinary sample); μ; for the bench's sources, the efficiency threshold of J for this state
  and background (`THRESHOLDS`, computed by `bell_stats.threshold_efficiency`).
* The coincidences (re-evaluated as the counts grow by half, at least every 250; in the counting by slots at 1, 2, 5 ×
  10ⁿ trials): E of each setting pair against the engine's prediction for these devices (`coincidence_rates`: the
  accidentals, the live fractions, the window's share), with the error under the prediction floored at one count of
  the rarer outcome (2/N); S against its prediction; S with the accidentals subtracted against S of the true
  coincidences; the accidentals' estimate against the run's own count (each pair of settings once, σ² twice the
  estimate: two pairs emitted within the window give two accidentals at once; [error in earlier] until 2026-11-19 the
  four cells summed, four times the same cell at Δ = 0, with one Poisson σ); |S| ≤ 2√2 + 5σ; for local laws |S| ≤ 2 +
  5σ; (|S| − 2)/σ; χ² of all measured E(Δ) points; no signalling from the counts; the space-like fractions. With
  coinciding settings (a′ = a or b′ = b) the error of S counts each angle pair once and the S line says that this is
  not a CHSH test (review 2026-10-23 V7-2).
* All the trials: J = p₊₊(a′b) − p₊₀(a′b′) − p₀₊(ab) − p₊₊(ab′) and CH (Gisin and Gisin's (15)) per slot against the
  engine's slot probabilities (the multinomial error of each setting pair, 5σ); for a local law J ≤ 5σ; for quantum
  mechanics J/σ, a violation above 5σ, an event.
* The counting by slots draws its counts from the engine's slot probabilities and coincidence rates, so its rows of E,
  S, the accidentals, J, CH, E(Δ) and no signalling against those predictions test the bookkeeping, not the physics:
  they stand in a group of their own that says so («Counting by slots: the counts drawn from the engine's prediction,
  against it»); its independent check is the slots simulated in time against `Law.slot_table` (Pearson's χ² over the
  outcome classes expected at least 5 times, p > 10⁻⁶; review R2-W F2).
* Spacetime: s² of a station's choice and the latest click at the other station in its slot against
  c²(τ + T_s + (L_Y − L_X)/v)² − (L_A + L_B)², in the direction X → Y in which that click comes later (each station's
  slots start at its own arrival time L/v; [error in earlier] until 2026-11-19 c²(τ + T_s)², right only for L_A = L_B);
  the order-reversal speed against the Lorentz matrices (review UX-params P21); s² of the choice and the emission at the
  station whose choice comes nearer the emission.

## Approximations and limits (stated)

* Not modelled (the detector model's conflicts, `photodetector.ABOUT`): afterpulsing (1 % typical for the SPCM-NIR),
  twilight events at the end of the dead time, a count-rate-dependent efficiency, the non-Gaussian tail of the timing
  response, and thermal (non-Poisson) pair statistics. The data sheet's dead-time correction holds «at low count rate»
  (its linearity table implies an effective 28 ns for the SPCM-AQRH); at the bench's 3 700 counts per second per
  detector the dead time removes 7·10⁻⁵ of the counts.
* **With the SPCM-NIR's dark counts in 1 µs slots J does not show the Eberhard state's advantage**: 250 counts per
  second give a dark click in 2.5·10⁻⁴ of the slots at each detector, against a violation of μ·J_pair ≈ 10⁻⁴ per slot.
  The thresholds of J at μ = 0.01 rise from 82.9 % (2/(1 + √2) = 82.8 % as μ → 0) to 87.6 % (|Φ+⟩) and from 72.6 % to
  90.2 % (r = −2.9); with 10⁵ background counts per second no efficiency violates. The loophole-free experiments count
  only a short window per trial at a pulsed source (Shalm et al.: a background of 8.9·10⁻⁷ per window); this bench has a
  continuous source and counts the whole slot. The value «none (an idealisation)» of part 4's «Dark and background
  counts» shows the thresholds without background.
* The slots are independent trials when (t_d + 5σ)/T_s ≪ 1 (0.021 here); the counting by slots needs it below 0.1.
  Its slot outcomes and its coincidences are two draws, each exact in distribution; that they are the same clicks is
  modelled only in the time stream.
* Gisin and Gisin's slot table: the model's pairs split into three independent Poisson streams (both particles with an
  outcome, ½ of the pairs; Alice's alone, ¼; Bob's alone, ¼), each by `slot_probabilities`, their click sets combined
  by their union (`engine/experiment.py or_tables`; tested against a Monte Carlo of `local_hidden.gisin_gisin`).
  The bench's detectors act on the model's outcomes (at η = 1 each station detects 75 % of the pairs, as in the model).
* The counting by slots is refused for the polarisation and sign models (not needed on the bench).
* The spin pairs' particle detectors are given the photon detectors' model and values: an illustration of the same
  statistics, not a real spin measurement, and the drawer says so («The detectors of spin pairs: an illustration»).
  No real spin measurement has a counter's efficiency, dark counts, dead time and jitter to cite: a spin read-out gives
  every trial an outcome and errs by reading the wrong one (Hensen et al., Nature 526, 682 (2015), arXiv:1508.05949:
  the combined initialisation and single-shot read-out fidelity of the two NV centres' electron spins was
  (97.1 ± 0.2) % and (96.3 ± 0.3) %); such read-out errors are not modelled.
* A setting switches at the slot's boundary instantly; the measurement is the arrival instant (its duration enters only
  through the jitter and the dead time).
* The setting choice is a fair coin from the run's seeded generator; the «freedom of choice» shown is the spacetime
  relation only. Every generator of a run (the emissions, each station's setting bits, the outcomes and the detectors'
  draws, the slots simulated in time) is seeded by the seed and the set-up together (`engine/experiment.py setup_key`: the
  parameters as sorted JSON, hashed), so the points of an atlas, which share one seed, are independent samples.
  [error in earlier] Until 2026-11-19 they came from the seed alone: every point drew the same emission times, bits
  and outcome draws, E's residuals at two angles correlated (r = 0.36 over 400 seeds; −0.04 now), the fits across
  points showed χ²/ν 0.32 (part 1) and 0.60 (S(Δ)), and τ = 5 µs gave the very draws of τ = 100 ns. Two illustrative
  local models plus Gisin and Gisin's; the optimal local model for given settings is
  not searched.
* The significance is the normal approximation of i.i.d. trials; the experiments' martingale p-values are not computed.

## Tests

`tests/test_u37_bell.py`: every preset runs without a failed check; quantum worlds reach 2√2 and pass 2 by more than
15σ under fair sampling while J stays below 0 at η 0.68; the local models never exceed 2 (three seeds) and keep J ≤ 0;
Gisin and Gisin's model gives 2√2 from the coincidences, J ≤ 0 and 75 % per station; the ports against the closed forms
at random angles for every law; the sequential quantum draw equals the joint Born rule; the counts against the
detectors' closed forms; a bright background with a wide window adds the accidentals the estimate finds; the emissions
and the bits do not depend on the run's steps and the dead time carries across them; outcomes revealed at the arrival
with the jitter; the random choice per slot space-like, a slow one time-like; fixed settings age into time-like; the
spacetime checks against closed forms; unequal distances (the locality check in the direction of the later
detection, R2-W F8); the refusals; the counting by slots against the engine's prediction (and J > 0 at Giustina's state
and efficiencies only without dark counts); its independent check, which fails for a slot table with η 10 % low while
every sampled row stays ✓ (R2-W F2); the J(η) curve and its marked zero (R2-W F9); the window's share after a reset
(R2-W F7); the live changes; the reviews' regressions V7-1, V7-2, V7-3 and P21.

`tests/test_u37_screens.py`: every point of the three atlases (495) builds with every check ✓ and stops by its rule;
the bench's references against closed forms; E from four counts against `bell_stats.correlation`; S(Δ) against the
law's E and the visibility's scaling; every way of the bench on the atlas's own points, fitted by `linear_fit`; part 4's
shown slots against the engine's slot probabilities; Gisin and Gisin's slot table against a Monte Carlo; the
thresholds table against `bell_stats.threshold_efficiency`; the story's captions against the recording.
`tests/u37_screens.mjs` (a browser, from the view's `canvas.__layout`): the caption clear of the pictures, at 390 px
the view, the step's control and «Measure» on screen together, no horizontal scroll, no text out of its canvas, the
labels of three earlier points stacked on S(Δ), none over another.

## Sources

D. Dehlinger, M. W. Mitchell, Am. J. Phys. 70, 903 (2002); M. Giustina et al., PRL 115, 250401 (2015); L. K. Shalm et
al., PRL 115, 250402 (2015); N. Gisin, B. Gisin, Phys. Lett. A 260, 323 (1999); Excelitas SPCM-NIR product brief (Rev
2018-09); quotations checked against the downloaded texts (`../../lfphys/sources/detectors_bell_2026-11-18.md`).
Bell (1964), Clauser, Horne, Shimony, Holt (1969), Tsirelson (1980), Clauser, Horne (1974), Eberhard (1993), Hensen et
al. (2015) for the standard physics and the loophole terminology.
