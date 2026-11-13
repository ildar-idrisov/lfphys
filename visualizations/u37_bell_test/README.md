# v07 — The Bell test with entangled pairs

**English** | [Русский](README.ru.md)

Pairs of polarisation-entangled photons |Φ+⟩ = (|HH⟩ + |VV⟩)/√2 or spin-½ singlets (|↑↓⟩ − |↓↑⟩)/√2 fly from a
source to two stations; each station measures its particle with one of two settings; the run counts coincidences
and estimates the correlations E and the CHSH parameter S. Owner guide: `../README.md`; rules: `../RULES.md`.

The visualization is a **wrapper over the engine `lfphys`** (`../../lfphys/LAYERS.md`): every law comes from an engine
module; the folder's own code is the time line, the apparatus logic (stations, choices, bookkeeping), the messages
and the drawing.

| engine module | layer | used for |
|---|---|---|
| `core.quantum.qubits` | core | the states `PHI_PLUS`, `SINGLET`; polariser projectors and Stern–Gerlach projectors; Born-rule sampling of a pair (`sample_pairs`); exact `correlation`, `joint_probabilities` (marginals), `chsh`, `concurrence`, `entropy` |
| `theories.alternatives.local_hidden` | theories (alternative) | LHV worlds: `polarization_model` (photons), `sign_model` (spin), with their exact `*_E`; in quantum worlds only the comparison curve on the E(Δ) plot (not listed among the world's modules) |
| `core.causality` (new, 2026-10-23) | core | interval s², causal relation, order-reversal speed of each pair's events |
| `core.relativity` | core | `boost_matrix`: an independent check of the order-reversal speed |
| `core.constants` | core | c (CODATA, exact) |
| `tools.bell_stats` (new, 2026-10-23) | tools | E and its error, S and its error, marginal differences, χ² of the E(Δ) points |

## The causal chain of one pair (all computed in the run)

Geometry: a line, the source at x = 0, Alice's station at x = −L, Bob's at x = +L (lab frame). Photons fly at c;
spin-½ particles at v = β c (world parameter, illustrative). Both particles of a pair arrive at t_e + L/v.

1. **Emission** at a time of a Poisson stream (rate live).
2. **Setting choice** (mode "random": "Choice of the setting" =
   "random for every particle (as in loophole-free experiments)"): the station's random-number generator delivers a
   fair bit (0 → a or b, 1 → a′ or b′) at t_c = t_arr − τ, i.e. τ before the particle arrives (τ = latency of the
   generator and the switch). The bit does not depend on anything in the run; it is drawn when the run reaches t_c
   (or, when τ exceeds the flight time, when the pair is emitted: then t_c lies before the emission, as for a
   generator whose output is delayed by τ). Mode "fixed" ("fixed: Alice a, Bob b"): Alice uses a, Bob uses b; the
   "choice event" of a station is the moment its setting was last set.
3. **Detection** at t_arr: the analyser angle in force at that moment (a live change of an angle applies to every
   particle that arrives after it), and the outcomes of both particles by the world's law:
   * quantum: `qubits.sample_pairs(state, Π(α_A), Π(α_B))` — the joint Born probabilities Tr(ρ Π_i ⊗ Π_j); index 0
     (transmitted by the polariser / spin up along the magnet's direction) is the outcome +1. At perfectly
     (anti)correlated settings one of them is exactly 0, which the float trace gives as ±1e-17; the engine sets a
     negative value within the round-off of the trace (4·dim·eps) to 0 (`qubits.born_probabilities`, review
     2026-10-23 V7-1: before, about half of such settings, e.g. a = b = 30°, stopped the run);
   * local hidden variables: `local_hidden.polarization_model(α_A, α_B)` (photons: a common polarisation λ, Malus law
     independently on each side, E = ½ cos 2(α_A − α_B)) or `local_hidden.sign_model(θ_A, θ_B)` (spin: a common unit
     vector λ, A = sign(a·λ), B = −sign(b·λ), E = −1 + 2θ/π). The engine function draws λ and both outcomes in one
     call; its code computes A from (α_A, λ) only and B from (α_B, λ) only (locality by construction), and the run calls
     it at the common arrival instant, when both settings are known; this is equal in distribution to drawing λ at the
     emission.

   The outcomes are revealed (message `pairs`, flash in the view) only at t_arr. The run computes nothing about a pair
   before its time except the emission bookkeeping. To keep the record small, a `pairs` message carries the per-pair
   detail (times, settings, outcomes, choice events, spacetime flags) of at most the newest 16 pairs of each step and
   the number of pairs; every pair enters the counts, which the frames carry.
4. **Spacetime relations of the pair's events** (`core.causality.relation`, lab frame): Alice's choice
   (t_cA, −L) against Bob's detection (t_arr, +L) and Bob's choice against Alice's detection (locality: space-like means
   no signal from the choice can reach the other detection); each choice against the emission (t_e, 0) (freedom of
   choice). For photons in the symmetric geometry both conditions are 0 < cτ < 2L. For particles slower than light the
   locality condition stays cτ < 2L but the freedom-of-choice condition becomes |L/v − τ| c < L; both can hold only if
   v > c/3 (computed per pair; shown as fractions).

Coincidence counts are kept per pair of analyser angles actually used (at most 200 pairs; the oldest unused one is
dropped). The four CHSH cells are the current (a, b), (a, b′), (a′, b), (a′, b′); after an angle change the cells refer
to the new angles, and the old angle pairs stay on the E(Δ) plot. The action "Reset the statistics" starts the counts
anew.

## Live set-up, world parameters, actions (RULES.md §2.4)

* Live (apply at once): the four angles, the mode (fixed / random), τ, L, the pair rate.
  * an angle: particles arriving after the change are measured at the new angle; in mode "fixed" the station's choice
    event becomes the moment of the change;
  * the mode: switching to "random" schedules the choices of the pairs in flight at max(t_arr − τ, now) — never before
    the switch; switching to "fixed" makes the current moment the choice event of both stations;
  * τ: pending choices are rescheduled at max(t_arr − τ, now);
  * L (the stations move): a particle already beyond the new station position is lost (counted, notice); the others
    arrive when they reach it (t_e + L_new/v);
  * the rate: the next emission is drawn anew (the Poisson stream is memoryless).
* World parameters (a new world): the pair type, the speed of spin-½ particles, the law. The law has
  `standard = "quantum"`; "lhv" is flagged "MODIFIED PHYSICS".
* Action: "Reset the statistics".

## Checks (panel "Checks: computed ↔ reference")

* Source state (quantum worlds): concurrence = 1 and one-particle entropy = 1 bit (engine) — identities.
* Settings, exact (re-emitted after each angle change): S of the law at the current angles — quantum: the engine's
  trace against the closed forms cos 2(α_A − α_B) (photons) and −cos(θ_A − θ_B) (spin), tolerance 1e-12; |S| ≤ 2√2
  (quantum); for LHV |S| ≤ 2; exact no-signalling of the law (quantum: marginals from the joint Born probabilities,
  max difference < 1e-14). In LHV worlds two lines are identities of the model and are shown **for information**
  (≈, `info: true`, never ✓/✗): the law's no-signalling (P(+) = 1/2 at any setting of the other side by
  construction: each side's outcome depends on its own setting and λ only) and |S| ≤ 2√2 (implied by |S| ≤ 2);
  the no-signalling test of an LHV world is the one from the run's counts below.
* Statistics of the run's pairs (re-emitted as the counts grow by 30 %, at least every 100 pairs; a cell is compared
  once it has ≥ 30 pairs): E of each cell against the law's exact E (z-score with the error under the reference,
  tolerance 5σ); S against the law's S (5σ). The error of S: four distinct cells are independent samples, Var S =
  Σ Var E_k; with coinciding settings (a′ = a or b′ = b) two cells are the same angle pair, i.e. the same counts, so
  the error groups them: S = Σ_c w_c E_c over the distinct cells, w_c the sum of the CHSH signs of the cells equal to
  c, Var S = Σ_c w_c² Var E_c (`bell_stats.chsh(…, keys)`; e.g. a′ = a: S = 2E(a,b), Var S = 4 Var E(a,b)); the S
  line then says that the settings coincide and that S is not a CHSH test (review 2026-10-23 V7-2: before, the error
  assumed four independent cells and was 1.55–1.65× too small at a = a′ = 0, b = 45°, b′ = 0, and 0.032 instead of 0
  at b′ = 45°, b = 0). A no-signalling difference between two coinciding cells is 0 identically and is shown for
  information. Quantum worlds: (|S| − 2)/σ, ✓ once it exceeds 5 (with the number of pairs
  still needed while it does not); LHV worlds: |S| ≤ 2 + 5σ; |S| ≤ 2√2 + 5σ; χ² of all measured E(Δ) points against the
  law (p > 1e-6); no-signalling from the counts: P_A(+|x, b) − P_A(+|x, b′) and P_B(+|a, y) − P_B(+|a′, y) against 0
  with the pooled binomial error (5σ).
* Spacetime (re-emitted after changes of L, τ, mode): for a pair emitted now, s² of Alice's choice and Bob's detection
  (engine) against the closed form c²τ² − (2L)²; its relation in the label; for space-like events the order-reversal
  speed v*/c = cτ/(2L) (engine) against a root search on the Lorentz matrices of `core.relativity`, applied to the
  events' separation (boosting the events apart cancelled terms ~L and lost ~εL/(cτ) of the root: 1.2·10⁻⁸ at
  τ = 1 ps, L = 10⁵ m, a failed check on a correct world — review UX-params P21); s² of the choice
  and the emission against c²(L/v − τ)² − L². The fractions of detected pairs with both choices space-like separated from the other
  detection and from the emission (no reference).

The 5σ tolerance makes a false failure of one check about 6·10⁻⁷ per evaluation; each check is re-evaluated as the
counts grow, so over a long run a few dozen evaluations per check remain far from a false alarm.

## Approximations and limits (stated)

* Ideal source and detectors: every emitted pair is detected at both stations (no losses, no dark counts, no
  multi-pair emission, unit visibility). Real tests must close the **detection loophole** (efficiency high enough or
  CH/Eberhard inequalities) and the **locality loophole** (space-like separation of each setting choice from the
  other side's measurement, including the measurement's duration); loophole-free tests: Hensen et al. 2015, Giustina
  et al. 2015, Shalm et al. 2015. Here the measurement is an instant at the arrival time.
* One line, a symmetric source in the middle, both particles at the same speed: the two detections of a pair are
  simultaneous in the lab frame.
* The setting choice is a fair coin from the run's seeded generator (pseudo-random); the "freedom of choice" shown is
  the spacetime relation only.
* The two LHV models are illustrative members of the class bounded by CHSH (|S| ≤ 2): the polarisation model gives at
  most |S| = √2, the sign model reaches 2 at the spin-optimal angles. Any local model obeys |S| ≤ 2; the visualization
  does not search the class for the best one.
* Statistical errors use the normal approximation (≥ 30 pairs per cell).
* Presets are illustrative (distances and τ are not taken from a specific experiment).

## Tests

`tests/test_v07_bell.py` (harness `../tests/harness.py`): every preset runs without errors and without a failed check;
quantum worlds give |S| within 5σ of 2√2 and above 2 by > 15σ (40 000 pairs); LHV worlds never exceed 2 + 5σ (three
seeds each) and reproduce their model's S; no-signalling from the counts; the wrapper's sampling against the textbook
closed forms at random angles for all four law × pair combinations; outcomes revealed only at arrival (t_arr = t_e +
L/c); random choice space-like, slow choice (cτ > 2L) time-like; the spacetime checks against closed forms for four
geometries; a live angle change applies to the next arrivals and keeps both angle pairs on the E(Δ) plot; a refused
change leaves the world unchanged; moving the stations loses exactly the overtaken pairs; mode switches reschedule
choices not before the switch; the clear action; a new world with another law in the same run; the frame and header
content the view draws; perfectly (anti)correlated fixed settings (photons a = b = 30°, a − b = −90°; spins a = b = 30°,
a = 50°, b = 230°) run without errors with E = ±1 exactly (V7-1); the error of S with coinciding settings matches the
spread over 40 seeds and the settings are flagged (V7-2); in LHV worlds the law's no-signalling and Tsirelson lines
are information, not checks (V7-3). Engine tests of the new modules: `lfphys/tests/test_causality.py` (against
`core.relativity.boost_matrix`), `lfphys/tests/test_bell_stats.py` (against Monte-Carlo repetitions, including coinciding cells),
`lfphys/tests/test_born_round_off.py` (zero cells of the joint Born probabilities).

## Sources

Bell, Physics 1, 195 (1964); Clauser, Horne, Shimony, Holt, PRL 23, 880 (1969); Tsirelson, Lett. Math. Phys. 4, 93
(1980); Aspect, Dalibard, Roger, PRL 49, 1804 (1982); Weihs et al., PRL 81, 5039 (1998); Hensen et al., Nature 526, 682
(2015); Giustina et al., PRL 115, 250401 (2015); Shalm et al., PRL 115, 250402 (2015). These are cited for the
standard physics and the loophole terminology; no number of the run is taken from them.
