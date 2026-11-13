# r13 — when does the particle arrive? Arrival times in 2-D by the rules in use

**English** | [Русский](README.ru.md)

A wrapper over the engine `lfphys` (plan item P14.6, on P6 and r12). A wave packet flies along z to a detecting plane,
freely or through r12's double slit. Quantum mechanics has no self-adjoint time operator, so the Born rule does not
fix the distribution of the time at which the particle reaches the plane; several rules are in use, and the run
computes each of them from the same experiment, so that one sees where they agree (far from the source) and where
they part (near the source, on a train of packets, under backflow, behind two slits).

## What the run computes (engine modules)

| module | layer | role |
|---|---|---|
| `core.quantum.schrodinger_nd` | core | the wave on the plane (r12's split operator), the current J(x, t) through the plane, ψ and ∂ψ/∂z on it (`plane_values`, order 32), the probability absorbed in a region (`absorbed_in`) |
| `core.quantum.schrodinger1d` | core | `FreeGaussians`: superpositions of free Gaussian packets in closed form (ψ, ∂ψ, current, momentum amplitude, P(z < L)): the initial state's longitudinal factor, the references of the checks |
| `core.quantum.transfer` | core | the soft detector's stationary reflection; the absorbing layers |
| `theories.interpretations.arrival_times` | interpretation | the intrinsic rules: quantum flux, Bohm's first arrival (in 1-D: the running maximum of the flux's integral), Aharonov–Bohm–Kijowski, semiclassical |
| `theories.models.detection` | model | the detector models: the absorbing boundary rule (Werner, Tumulka), the exponential rules (Włodarz, Marchewka–Schuss), the absorbing step |
| `theories.interpretations.bohm` | interpretation | the Bohm ensemble (r12) |
| `core.quantum.particles`, `core.backend` | core | the physical scale; GPU 0 or CPU |

The apparatus (`engine/apparatus.py`, no physics of its own): the free geometry and the slit geometry lengthened for a
train, the initial states, the soft detector's potential, the choice of the screen's absorbing layer.

## The model

* **Units** as in r12: lengths in λ of the mean momentum ħk₀, ħ = m = 1, k₀ = 2π, v₀ = 2π, E₀ = 2π²; one unit of time
  is mλ²/ħ of the particle; t₀ = D/v₀ is the classical flight time from the leading packet's centre to the plane.
* **Initial states**, separable: χ(x)·φ(z), χ a Gaussian of width σx, φ a superposition of Gaussians whose leading
  packet is centred at the source (z = 0 in free flight; r12's source point 4.5σz + w/2 + λ before the plate):
  `gauss` — one packet of wavenumber k₀; `train` — N equal packets sep apart, each the translate of the first (carrier
  phase e^{ik₀ j·sep}, Das & Struyve 2021 eq. 18; sep ≥ 6σz); `backflow` — a slow packet (k₀/4, amplitude 1.5) at the source and
  a fast one (k₀, amplitude 1) 3D behind it, timed so that both centres reach the plane together: there they overlap
  and the current flows back for a while (closed form: 1.53 % of the probability). The initial state may hold at most
  10⁻⁴ beyond the plane (refused otherwise).
* **The ideal plane.** In the main run the plane z = L is the face of the screen: what crosses it is absorbed by a
  reflectionless layer 4λ behind it (r12, with the layer chosen for the state's spectrum: r12's 6λ/2E₀ reflects 2.5 %
  at k₀/4, so the narrowest of (6λ, 2E₀), (12λ, E₀), (24λ, E₀/2), (36λ, E₀/2), (48λ, E₀/4) with reflection < 10⁻⁵ and
  leak < 10⁻⁶ over ±3σ of every packet is taken). The run records at every step J(t) = ∫ j_z(x, L, t) dx, J(x, t) in
  bins (≤ 360 × 240) for the joint distribution, ∫|ψ(x, L, t)|² dx and ∫|∂ψ/∂z(x, L, t)|² dx.
* **The rules** (densities per unit time; Π dt is the probability of arrival in [t, t + dt]):
  * quantum flux — Π = J(t); negative under backflow (then not a probability density);
  * Bohm — the first crossing of the plane by each trajectory of the ensemble (r12's integration); in free flight also
    the exact law of first arrival from the run's flux: P(T ≤ t) = max_{s ≤ t} ∫₀ˢ J (the trapezoid rule from J(0) = 0:
    a rectangle sum ran dt/2 ahead, review B4-7) (one-dimensional trajectories
    keep their order; the separable state's motion along z is one-dimensional);
  * Aharonov–Bohm–Kijowski — Π = (ħ/2πm) Σ_α |∫dk θ(αk) √|k| ψ̃(k) e^{ikD − iħk²t/2m}|² (Das & Nöth 2021, eq. 5), from
    the initial state's momentum amplitude (free flight only); its weight at t < 0 (read as "not detected") is reported;
  * semiclassical — Π = (mD/ħt²)|ψ̃(mD/ħt)|² (Das & Struyve 2021, eq. 3), the flight measured from the leading packet's
    centre; computed through its cumulative distribution in k, P(T ≤ t) = ∫_{k ≥ mD/ħt}|ψ̃|² dk, drawn as bin averages
    and summarised by quadrature in k (review B4-2: samples of the density aliased the comb of a long train and gave
    totals of 0.73–1.17);
  * absorbing boundary (Werner 1987; Tumulka 2022, eqs. 3, 7) — ∂ψ/∂z = iκψ on the plane, clicks (ħκ/m)|ψ(L, t)|²,
    ψ(L, t) by the image solution (free flight, k > 0); κ in units of k₀ (a wave with k = κ is absorbed fully, others
    reflected by (k − κ)²/(k + κ)²);
  * exponential (Das & Struyve 2021, eq. 5 and Table I) — Π = λ e^{−∫λ} with λ_W = λ₀ v₀ ∫|ψ(x, L, t)|² dx (Włodarz) or
    λ_MS = λ₀ (v₀/k₀²) ∫|∂ψ/∂z(x, L, t)|² dx (Marchewka–Schuss: Table I's (λ₀′ε/π)|∂ψ̄|² with ψ̄ the solution with a
    Dirichlet wall at L, ∂ψ̄ = 2∂ψ, ε = ħ/m, so λ₀′ = πλ₀v₀/(4k₀²) = λ₀/8 here), so that λ₀ is the mean
    number of clicks a packet would cause if it did not vanish; on the plane, a Poisson process with the rate density
    λ(x, t) (the world's generalisation of the one-dimensional rules); the first click in a step of length dt has
    probability e^{−Λᵢ₋₁} − e^{−Λᵢ}; what never clicks is reported;
  * soft detector (Allcock 1969; Muga, Palao & Leavens 1999) — a second run of the same experiment whose screen is an
    absorbing potential −iW₀ rising over the edge width at the plane (and r12's layer behind it): its clicks are the
    probability it absorbs; the rest is reflected.
* **Through the slits** the flight is not free: the ABK, semiclassical and absorbing-boundary rules are not defined
  there and are not drawn; the flux, Bohm, exponential and soft-detector rules are. Closing a slit in flight acts on
  both runs at once (Das, Deckert, Kellers, Krekels, Struyve 2024: the dynamic double slit).

## Live and world parameters (review UX-ui U12)

r12's table holds for r12's parameters (the slits open or closed, the plate's a, d, w, V₀ — through the slits — are
live with r12's rules and act on both runs; the edge, L, the particle and λ, the packet's widths, the grid and the Bohm
ensemble are world parameters for r12's reasons). This world's own:

| parameter | | what an edit does to the state; or why it stays a world parameter |
|---|---|---|
| λ₀ of Włodarz's and of Marchewka–Schuss's rule | **live** (U12) | a detector made more or less sensitive at the current moment: the rule's rate uses λ₀ in force when each sample of ψ on the plane was recorded (a sample at the moment of the change belongs to the value before it), so the clicks up to the change stay as they were and the survival e^{−Λ} is continuous (the past is not rewritten); the wave is not touched (the rules do not act back on it). A change at t = 0, or before 10⁻⁶ of the unit-strength signal (v₀∫∫\|ψ\|², (v₀/k₀²)∫∫\|∂ψ/∂z\|²) reached the plane, is the experiment with the new λ₀ from the start (bit for bit); after it `arr_train` (one λ₀ for the whole flight) is reported as not applicable |
| soft detector's height W₀ | **live** (U12) | the second run's absorbing potential −iW₀ is rebuilt at the current moment (its wave is kept, its clicks go on); `soft_grid` is computed for the highest W₀ the run has had; a change at t = 0 or before 10⁻⁶ of the probability reached the detector (absorbed there or held behind L − 5 edge widths) is the experiment with the new W₀ from the start (bit for bit), after it `arr_soft_reflection` (stationary theory for one W₀) is reported as not applicable. Refused when the world has no soft detector |
| flight (free / through the slits) | world | another window and apparatus (no plate in free flight; the window is lengthened differently) |
| initial state, packets in the train, their distance | world | the initial state: ABK, the semiclassical and the absorbing-boundary rules are functionals of it, computed at the start |
| κ of the absorbing boundary | world | its rule is computed in closed form from the initial state for one κ over the whole flight (`detection.abr_density`); a κ changed at a moment is a time-dependent boundary condition, which the engine does not solve |
| soft detector on / off | world | it is a second run of the whole experiment from t = 0: switched on later it would need its wave from the start |

The world's parameters (the header's `params`) are its own: r12's fixed path mark and flux are not among them. With
them, "▶ Start a new world" without a scenario sent them back and every such new world was refused ("there is no
parameter “mark”"; found while processing U12) [error in earlier].

## What is shown when

r12's scene, in 3-D since the owner's correction of 2026-10-28: nothing depends on y, so the wave is the exact
product ψ(x, z, t)·η(y, t) with a free Gaussian η of width σy (world parameter), drawn as a volume; the Bohm particles
and their trajectories in x, y, z (y₀·σy(t)/σy); the detecting plane shows P(x, y) (r12's README, "The plane and the
third dimension"); the plate if any; the window of the plane y = 0. The arrival time does not depend on y (the
product's flux through the plane is J(x, t)|η(y, t)|²), so the rules below are those of the plane. This world's
panels: "Distribution of the arrival time" — Π(t)·t₀ against t/t₀ for every
rule (the Bohm ensemble as a histogram normalised to the whole ensemble), each up to the time shown (the rules
computed from the initial state too: their curves come with the run's messages as its time reaches them); the time
axis starts at 2 t₀ (a set-up scale) and grows with the run's time — the window's length is a consequence of the run
and appears only in the totals (review B4-5); "Place and time of
arrival" — the joint distribution J(x, t) (warm colours into the plane, blue back; bins of t₀/120, a bin drawn once
it lies wholly in the past) with the Bohm hits (x, t) over it;
"Totals by rule" at the end of the window — each rule's probability within the window and its mean time, what the
exponential rules never click, the soft detector's reflection, ABK's weight at t < 0, the backflow. The window of
observation ends when all but 10⁻⁴ has crossed the plane in free flight (closed form, ×1.02), or when the wave has
left the window (r12's rule) behind the slits.

## Checks

r12's (`grid_k`, `grid_wall` with a plate, `absorbers` over the state's spectrum, `norm`, `numerics`, `flux_absorbed`,
`bohm_born`, `bohm_fraction`, `bohm_accuracy`, `symmetry`, the third dimension's `screen_y`, `bohm_y` and
`bohm_y_motion`, and with the
slits `no_crossing`, `ref_*`, `visibility`), and:

| id | quantity | reference | tolerance |
|---|---|---|---|
| `arr_state` | the initial state's longitudinal momentum distribution (FFT of the grid state projected on χ) | the closed form the rules use | 10⁻³ of the peak (the window cuts the amplitude's tails, ~10⁻⁴) |
| `soft_grid` | the wavenumber in the soft detector \|q\| = (k⁴ + 4W₀²)^{1/4} at the top of the spectrum, over k_max | resolved | < 0.8 |
| `arr_flux_exact` | J(t) through the plane (free flight) | the exact free current | < 1 % of the peak |
| `arr_plane_psi` | ∫\|ψ(x, L, t)\|² dx (free flight; the exponential rules' input) | the exact free density | < 1 % of the peak |
| `arr_bohm_times` | Kolmogorov–Smirnov distance of the Bohm hit times | free: the first-arrival law from the run's flux; slits: the flux (its positive part) | 1.95/√n (99.9 %) |
| `arr_soft_reflection` | the soft detector run's reflected fraction (free flight) | stationary transfer matrices of the detector's profile −iW(z), averaged over \|ψ̃(k)\|² (Richardson over 1500/3000 slices) | 10 % + 2·10⁻⁴ |
| `arr_det_norm` | the soft detector run's norm + absorbed − 1 | 0 | 10⁻⁹ |
| `arr_abr_identity` | ∫Π_ABR over the window — both sides from the image formula: a test of the quadratures in t and k, not of the rule (the rule is tested in the engine against Crank–Nicolson with the Robin condition; review B4-9) | ∫\|ψ̃\|²(1 − R_k) dk | 2·10⁻³ |
| `arr_abk_norm` | ∫Π_ABK over the window + its weight at t < 0 | 1 | information |
| `arr_train` | the train's successive peaks: the flux's and Włodarz's | e^{−λ₀/N} for Włodarz (Das & Struyve 2021, eqs. 24–25, no spreading) | information |

Measured on the presets (GPU 0, λ/6, 2000 Bohm particles, 2026-10-28): every check passes; 10–138 s per experiment.

| preset | `arr_flux_exact` | `arr_plane_psi` | soft detector: reflected, run / stationary | the rules' mean arrival time / t₀ |
|---|---|---|---|---|
| `gauss` (σz = 5λ, L = 30λ) | 5.8·10⁻⁶ | 1.4·10⁻⁵ | 1.98·10⁻³ / 1.94·10⁻³ | flux, Bohm, ABK, ABR 1.0002, semiclassical 1.0003; Włodarz and Marchewka–Schuss 0.954 (37 % never click at λ₀ = 1) |
| `near` (σz = λ, L = 5λ) | 8.0·10⁻⁷ | 9.0·10⁻⁷ | 2.35·10⁻³ / 2.34·10⁻³ | flux, ABK, semiclassical 1.006: the means agree, the shapes do not (the semiclassical density is narrower: it knows only the momentum spread) |
| `train` (4 packets 30λ apart) | 5.1·10⁻⁵ | 7.9·10⁻⁵ | 1.97·10⁻³ / 1.93·10⁻³ | flux 2.50 (four equal peaks), semiclassical 1.000 (one peak: Das & Struyve 2021), Włodarz and Marchewka–Schuss 1.89 (later peaks damped by e^(−λ₀/N) to 3 %; 13.5 % never click) |
| `backflow` (σz = 3λ, L = 16.5λ) | 6.3·10⁻⁵ | 1.7·10⁻⁴ | 0.2000 / 0.1999 | backflow 1.512 % (closed form 1.513 %); flux and Bohm 4.03, semiclassical 3.11 (it does not know that the fast packet starts 3D behind); detected: Włodarz 0.955, Marchewka–Schuss 0.38 (|∂ψ|² of the slow packet is 16 times smaller), absorbing boundary 0.75, soft detector 0.80 |
| `slits` | — | — | — | 17.9 % reach the screen; flux 1.048, Bohm 1.051; `numerics` 5·10⁻⁴, visibility 0.93 |

The third dimension (σy = 3λ): `screen_y` ≤ 1.1·10⁻⁵ of the peak, `bohm_y` 0.008–0.011 (2000 particles; behind the
slits 0.037 against 0.10), measured before `bohm_y_motion` found the hits' y of a step taken at its first hit's time
(r12's README; 1.4·10⁻⁴ of η's width in the tests' geometry, fixed). After the fix, preset `gauss` (GPU 0, 27 s):
`bohm_y` 0.011, `bohm_y_motion` < 10⁻⁶ of η's width (passes; η spreads by 3.5 % over the flight). The Bohm hit times pass the KS test in every preset (D = 0.020–0.026 against 1.95/√n = 0.044 for 2000 particles;
behind the slits 0.026 against 0.10).

## Approximations and limits

* r12's: non-relativistic, two dimensions (nothing depends on y), absorbing layers as detectors of the ideal plane,
  geometry in wavelengths.
* ABK, semiclassical and the absorbing boundary are computed for free flight from the initial state and a separable
  state (the transverse packet a spectator): the time marginal of each rule for the plane equals its one-dimensional
  form for φ(z).
* The exponential rules on the plane are the world's generalisation of the one-dimensional rules (a Poisson process
  with rate density λ(x, t)); their λ₀ is a free parameter of the detector, as in the papers.
* The soft detector's edge is a world parameter (≥ the grid step): a sharp step converges only as h² on the grid (45 %
  off at λ/6 in one dimension), a resolved edge reflects much less than a sharp step (the stationary value of the sharp
  step is given for comparison in the check's note).
* Cost: the presets take 10–138 s on GPU 0 (the main run, the companion, the soft detector run, 2000 Bohm particles);
  an experiment estimated above 10 min on GPU 0 or an hour on the CPU is refused (r12's rule).
* Closing a slit while the wave is inside it is a sudden switch of the wall: it makes waves the grid may not resolve,
  and `numerics` reports it (a closing ramp, as in Das et al., is not implemented).
* Open items: `../../STATUS.md` (V30).

## Tests

`tests/test_r13_arrival_times_2d.py` (small geometries): every preset builds and passes its static checks; a small free
packet passes every check, the ideal rules agree on the mean time far from the source, the joint distribution is
recorded; nothing arrives before the wave can; the backflow state's flux goes negative while Bohm's first-arrival
density does not, and the flux follows the closed form through it; a train's exponential rule damps the later peaks;
through the slits, a slit closed in flight acts on both runs and the checks pass; refusals (overlapping packets, a
plane too close to the source); GPU = CPU for the soft detector run and ψ, ∂ψ on the plane. Live detectors (review
UX-ui U12): λ₀ and W₀ set at t = 0 give a world built with them, bit for bit; λ₀ raised while the signal arrives leaves
the density before the change as it was and after it equals λ₀′v₀ρe^{−Λ} computed by hand from the record (the
unchanged world's differs: the negative control); W₀ raised at the detector rebuilds the second run's absorber, keeps its
norm + absorbed = 1, and the stationary comparison is reported as not applicable; W₀ without a soft detector and the
plate in free flight are refused with the world unchanged; through the slits a live plate acts on both runs; a new world
from the header's parameters and the live values builds (with r12's fixed keys it is refused: the negative control);
every parameter with a unit names it in its label (U19). The engine's side:
`lfphys/tests/test_arrival_times.py` (closed forms, trajectories one by one through backflow, Das & Struyve 2021 eq. 43, an
independent Crank–Nicolson solution of the Robin boundary).
