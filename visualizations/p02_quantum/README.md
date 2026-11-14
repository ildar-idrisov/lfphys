# p02 — the quantum laboratory (quantum particles)

**English** | [Русский](README.ru.md)

A laboratory section (plan P15.3; framework P15.0: `../RULES.md` §6). The owner's words (2026-10-28): «в плейграунде
можно добавлять в мир разные объекты, менять параметры, смотреть за их изменением и взаимодействием, все должно быть не
задано заранее, а просчитываться в реалтайме» ("in the playground one can add different objects to the world, change
parameters, watch how they change and interact; nothing should be set in advance, everything computed in real
time"). The scene is built by hand from the palette, changed at any moment in the inspector, saved to a file and
started again from it; its record is the last minutes unless "● Keep the record".

## The laws of a world

A world parameter (a change is a new world): the space, a plane (x, y) or the volume. **Live** (changed at the current
moment, the world kept): the grid (points per axis), the window's size (plan P16.1, LB1, 2026-11-11; below) and the
window's edges (review UX-ui U12, ``Scene.set_edges``): open (absorbing ramps, 10 % of the window per side in a plane,
15 % in space) or closed ones (periodic: a charged particle next to a magnetic field or a flux tube is then refused —
the gauge's wrap at the window's face would be a sheet of field that is not on the scene, review B6-Q2); what the ramps
absorbed before a change stays absorbed (norm + absorbed = 1 throughout). Units: ħ = 1, the length 1 nm, the mass m_e;
so the unit of time is m_e nm²/ħ = 8.64 fs, of energy ħ²/(m_e nm²) = 0.0762 eV, of magnetic field ħ/(e nm²) = 658 T.
The world's time is in seconds.

### The grid and the window at the current moment (plan P16.1)

A change of the points per axis or of the window's size (the step is size / points; the window stays centred at 0)
resamples every particle's wave exactly as the band-limited function its grid holds (the trigonometric interpolant the
split operator evolves; `lfphys.core.quantum.schrodinger_nd.resample`, `Scene.regrid`): the same window — Fourier zero
padding (finer) or truncation (coarser); the same step — the samples themselves, zeros beyond a larger window; both
changed (a new size at the same number of points) — the interpolant evaluated at the new points, zeros beyond the old
window. Refused with the measured fraction, nothing changed, where more than **10⁻⁶ of a particle's norm**
(`QS.REGRID_TOL`) would be dropped or misplaced: a coarser grid while the wave's spectrum beyond the new band holds
more; a smaller window while more lies outside it, or (open edges) more would come under the new window's absorbing
layers that is outside the old layers now (review LB1-p02-ux Q6: a window 80 → 56 nm put 2.7·10⁻⁵ of the tunnel's wave
under the new layers without a word [error in earlier]); a larger window while more lies in the 4 outermost cells of
the old one (the grid is periodic: that part of the wave continues on the other side, which a larger window would cut).
The event states the probability inside the new layers and, for a larger window, what was inside the old ones (that
attenuated part becomes interior wave). A coarser grid is also refused by the scene's resolution rule (|k| + 6σ_k ≤
π/d, next to what acts on the particle ≤ ⅔·π/d) and by an object's edge narrower than ≈ 3 new steps; the help names
all three rules and the refusal says which one refused (review Q7: the help promised the 10⁻⁶ rule alone, and the
refusal spoke of a potential next to a free packet [error in earlier]). The action "Coarsen the grid with edges to match"
widens the edges set to 0 to the new grid and coarsens in one change (review X10). What a change drops (below the
tolerance; or gains, by the new grid's quadrature, when the step and the window both change) is banked as "a change of the
grid or the window (dropped; a minus: added by the quadrature)" (review Q10), so norm + absorbed = 1 stays exact; the event states, per particle,
the norm before and after and ⟨H⟩ before and after. A refinement carries the spectrum, so the norm and the kinetic
energy, exactly; its ΔE is the change of ⟨V⟩ evaluated on the finer grid — the grid's own error of the potential energy,
a reading of convergence (the double slit at 256 → 512 points: 3·10⁻⁶ eV of 0.378 eV). Coarsening a wave whose spectrum
has grown near the band's edge is refused with the number (the 3-D preset after its scattering, 96 → 64 points: 2.6·10⁻⁶
of the norm beyond the coarser band). The
objects keep their physical parameters: an edge set to 0 is the sharpest the grid resolves **when the object gets it**
and keeps that width (the potential must not change with the numerics), so a grid too coarse for an object's edge, or
a localisation length under 1.5 steps, is refused naming the object; a flux plane keeps the position it was asked for
(the nearest sample) and is refused outside the window. After the change the open edges' layers are rebuilt for the
new window (the probability inside the old layers goes on as it is), the absorbers' strengths and the time step are
tuned again, Bohm points outside a smaller window are registered as dropped by it, the energy reference and the flux
planes restart (`Scene.regrid`'s report, the run's checks). The view's axes and the 3-D box follow (messages `grid`,
`box`). Measured (CPU, 2 threads, the shared host): see "Latencies of the live changes" below.

**Another space** (2-D ↔ 3-D) stays a new world; with "carry the scene over" (plan P16.1, the framework's carry-over) it takes
over what means the same there (`Simulation._carried`): the plane's set-up is the section z = 0 of one that does not
change along z, so into space boxes, detectors, markers and regions go unbounded along z, a disk as a cylinder along z,
a packet with σz = σy (prepared afresh: a scene keeps packets, not waves); out of space only what crosses the plane z =
0, as its section there (a sphere as the disk of its section, a box bounded in z if it holds z = 0, a packet moving in
the plane within 2σz of it); walls, steps and flux planes across x or y and flux tubes go as they are (review
LB1-p02-ux Q4: they were refused with "there is no parameter “z”", 0 of the double slit's 4 objects went into space, and the
notes came before the add was tried [error in earlier]). Refused, named in the notice: what does not cross the plane, a
wall, a step or a flux plane across z, a packet moving out of the plane. **The same space** (a new world with the
scene carried, e.g. another grid from the form): each wave is carried itself (`carry_state`, `carry_world`,
`Scene.adopt_wave`: resampled exactly to the new grid, refused as a live change of the grid is — then a fresh packet,
said), with its absorbed records (a detector that was not carried: "in the previous world (before the scene was carried over)"), the world's random generators and
measured points; Bohm points are drawn again from the wave. The framework's one notice says what went with its state,
what was prepared afresh and why; the world's time goes on.

## The palette (all changed at the current moment)

**Placing** (review UX-ui U4, U8): a palette object goes where the pre-placement form or a click in the scene puts it.
A packet the scene cannot take there (inside a wall, against the window's face) goes to the nearest point where it can
— upstream first, in steps of its width — and a toast says so (in the double slit "＋ Particle (wave packet)" landed at (0, 0) inside
the 3 eV wall and was refused); a packet the grid cannot hold anywhere is refused with the wavelength it needs. An
object wholly outside the window is refused (a box at 10⁶ nm was taken without a word, and a packet there made the wave
NaN, review UX-params P29 [error in earlier]: the window test squared a negative distance); one partly outside is taken
with a note. The palette greys out what the scene cannot take now, with the reason (a magnetic field while a charged
particle is in the window; an object the grid could not hold next to the particles). Refusals say what in the scene is
wrong and what to change (the engine's sentence under "details").

| object | engine (`core.quantum.scene`) | parameters |
|---|---|---|
| particle (wave packet) | `Packet` of a `species`: electron, neutron (spin ½, CODATA moments), ⁴He, C₆₀, an atom of any mass | centre, de Broglie wavelength and direction, widths σ per axis, spin direction, the number of Bohm points |
| barrier or well, ball, wall with slits, step | `Box`, `Ball`, `SlitWall`, `Step` (smooth edges: the 10–90 % width is a physical length, at least ≈ 3 grid steps; a ball's radius at least 1.45 edges) | position, sizes (0: unbounded), height in eV, edge; the inspector shows the height the shape reaches (a shape narrower than its edges stays below its nominal height: the tunnel preset's barrier reaches 0.473 of 0.5 eV) |
| harmonic trap | `HarmonicTrap` (one V for all species, ħω given for the electron's mass) | centre, ħω in meV |
| magnetic field | `MagneticField` (on spins through −μ·B; on charges only a uniform Bz in a plane / a field along an axis in space, Landau gauge) | Bx, By, Bz in T, a gradient g about the region's centre (x_c, y_c; 0 for the whole scene): Bx = Bx₀ − g (x − x_c), By = By₀ + g (y − y_c) (div B = 0, rot B = 0), region |
| flux tube | `FluxTube` (Aharonov–Bohm; its field also acts on spins) | centre, flux in h/e, radius |
| detector | `Detector` (an absorbing region; the probability it takes is counted per particle) | region, strength (0: chosen for the particles' waves) , edge |
| which-path marker | `PathMarker` (a two-level detector that turns while the particle is in its region) | region, turning rate in rad/fs |
| environment | `Localization` (Lindblad localisation by quantum jumps; GRW form when everywhere) | rate λ in 1/ps, length a, region |
| flux plane | `Scene.add_plane` (the probability flux through it, integrated in time) | axis, position |

Actions: **"Prepare the packet anew"** — a fresh Gaussian packet from the particle's parameters at the current
moment (the former wave and its records discarded; dragging and throwing keep the wave, below). **"Measure the position"** — an unsharp position measurement (Gaussian Kraus operators of resolution σ): the
outcome is a point drawn by the Born rule or "already absorbed by detector k" with its probability; the wave collapses
to it. σ must be at least the grid step and large enough that the wave after it (its spectrum wider by 1/(2σ)) is
still held by the grid (`Scene.measure_min_sigma`; a refusal names the smallest σ; review B6-Q4); the time step follows
the wider spectrum. **Bohm points** (a particle's parameter) follow the probability current of its wave (de Broglie–Bohm,
`theories.interpretations.bohm`: an interpretation, flagged in the top bar), interpolated with the carrier of each
point's local wavevector (exact on the grid's samples; the plain interpolation erred by 2 nm over 30 nm at k d = 2,
review B6-Q1). Inside an absorber (a detector or an edge) a point is absorbed at the rate 2W — so the points not yet
absorbed stay |ψ|²-distributed and each absorber takes the share of points that it takes of the probability — and is
drawn where it was absorbed, credited to absorber k with probability W_k/W there. After a measurement the ensemble is
drawn again from |ψ|² (the outcome conditions on "not absorbed"); after a jump of the environment only the points not
yet absorbed are drawn again (the jump acts on the in-flight branch; review B6-Q5).

## Direct manipulation (plan P16.2)

Every palette type declares its handles (`ObjectType.handles`: the parameters a drag changes; a wall, a step and a flux
plane move along their own axis, `{"param": "position", "axis_param": "axis"}`), and every frame reports every
positioned object in `at` (nm; z = 0 in a plane): a packet at the mean position of its wave (not reported once a
detector has taken it), a wall, a step, a flux plane at their place on their axis, the rest at their centre (a field or
an environment that fills the scene has no position). The player selects, drags and throws (its framework); the world:

* **A packet dragged** (its position edited, in the inspector too) is prepared anew at the current moment as **the
  same wave in the new place**: ψ(r) → ψ(r − s), s = the point given − the wave's mean position now
  (`Scene.transform_particle`; exact for the band-limited wave, the norm and what was absorbed kept, its Bohm points
  moved with it). A charged particle in a vector potential gets the gauge factor of the **magnetic translation**,
  which keeps its kinetic momentum, its current and its whole kinetic distribution: past a flux tube the line integral
  of the tube's A from r − s to r (closed form, `schrodinger_nd.flux_tube_segment`), exact wherever the path the tube
  takes relative to the wave stays clear of it — also for a wave that went round the tube; in a field the straight-line
  integrals from the wave's mean position, exact in a uniform field. Where no translation keeps the wave the drag is
  **refused**, saying why: the tube's path crosses the wave (the flux its parts enclose would change) or the field
  differs between where the wave was and where it goes; the test is the share of the kinetic field (p − qA)ψ not carried
  along, > 10⁻⁶ refuses (review LB1-p02-ux Q1, Q2: the earlier factor, integrals from the mean position for every source,
  cut lines of phase qΦ into a wave that had gone round the AB tube — its high wavenumbers grew 1500–6200×, its
  kinetic energy 3 % — and moving a wave out of a field region changed its kinetic energy by −9.7 %, both announced as "the same
  wave moved by …" [error in earlier]). In the AB preset a drag along the wall after the electron passed is now exact (the tube's
  path stays inside the wall); one across a slit while the wave is in it is refused. The event gives the kinetic energy
  ⟨(p − qA)²⟩/2m before and after besides ⟨H⟩. Refused where more than 10⁻⁶ of its probability would cross a face of the
  periodic window **into the window** (with open edges what lands in the far side's absorbing layer is absorbed there,
  and said; review Q8: drags of a scattered wave were refused for its part already inside the layers), where the point
  is outside the window, or where the grid would not hold the wave there — the refusal says whether the place or the
  speed is the cause.
* **A packet thrown** (its velocity edited: parameters vx, vy, vz in nm per second of the world's time, the player's
  unit) gets the momentum that makes its mean kinetic wavenumber **k₀ = m v/ħ**: ψ → exp(iΔk·r) ψ, an impulse that
  shifts the whole momentum distribution (|ψ|² and the norm unchanged); its wavelength 2π/|k₀| and direction follow,
  and the event says so. A change of the wavelength or the direction in the inspector is the same impulse. Refused
  where more than 10⁻⁶ of the spectrum would pass the grid's band, or where the grid's resolution rule fails for the
  boosted wave, modelled by its measured spectrum (per axis its mean and the reach beyond which 10⁻³ of it lies, plus the
  packet's own (6 − 3.09)σ_k beyond it: a Gaussian's |k| + 6σ_k, and for a wave in parts its outer part's own; so a
  packet that a trap has accelerated is judged by its own momentum now, not by the momentum it was prepared with; the
  scattered tail at the 10⁻⁶ level that a barrier leaves is kept within the band by the alias test). **A throw (a
  drag's release) is never refused for its speed**: one faster than the scene takes there and then is clamped to the
  fastest it takes in that direction (`Scene.kick_limit`, bisection on the scene's own tests) and the event says so; a
  velocity typed in the inspector is refused with that limit. The throw's limit shown, the packet's hidden parameter
  `v_max` (`handles.velocity_max`, which the player clamps to beforehand), is computed from the wave itself
  (`Scene.kick_reach`: a bound the boost's tests pass in every direction) and follows it (checked every 20 frames, sent
  again when it moved by > 25 %). Review LB1-p02-ux Q5, X5: `v_max` was the fresh packet's formula, and the model of a
  wave reflected and transmitted at a wall read it as one Gaussian about its mean ≈ 0 (|k| + 6σ_k twice its reach):
  after the double slit's wall even a throw clamped to the limit shown, and one far below it, were refused [error in
  earlier].
* Any other change of a packet (species, widths, spin), or a drag of a packet a detector has taken, prepares a fresh
  packet from its parameters (said in the event). The packet's x, y (z) are **the centre at its preparation** (a drag
  writes the point it moved the wave to; where the wave is now: ⟨x⟩, ⟨y⟩ in the inspector — a mean, which for a wave in
  parts may lie between them); "Prepare the packet anew" prepares from the parameters or **where the wave is now**
  (⟨r⟩ and ⟨p − qA⟩; review X11, Q11: after a drag and a throw the fresh packet went back 6.6 nm behind the wave).
* **A potential, a field, a detector, a marker, a region or a flux plane dragged** moves at the current moment; the
  waves go on as they are. A drag evaluates only the moved object (the scene keeps every object's arrays by its
  parameters, `Scene._on_grid`), and a detector's strength is a function of its profile, not of where it stands.

## Instruments (plan P16.3)

`measurables()` (in every `scene` message) and every frame's `meas` (NaN, sent as null, with the reason in
`meas_note`): for the world the probability in the window and absorbed (sums over the particles); per particle its
probability in the window and absorbed, the energy ⟨H⟩ (eV, as the energy check), ⟨x⟩, ⟨y⟩ (⟨z⟩) (nm), ⟨p − qA⟩/ħ per
axis (nm⁻¹), the speed |⟨v⟩| (km/s), a spin's ⟨σ⟩ or a which-path marker's coherence; per flux plane the flux now (1/fs,
in total and per particle) and integrated since the scene's last change; per detector the probability it absorbed (in
total and per particle), the probability in its region now and the Bohm points it registered (NaN without Bohm
points); per marker the probability in its region now. One FFT per wave per frame (`Scene.observables`) and a few
sums (the marginals per axis): measured 1.3–1.7 ms on 256² against a scene step of 1.9–2.3 ms, 4.1–4.4 % of the
stepping at the double slit's default speed (16 steps per frame); 26 ms on 96³ against a step of 55 ms. The share is
larger at slower speeds, where the world is not limited by computation. `measure()` returns the values alone as a
dict (the sweeps' hook; review LB1-p02-ux Q3: it returned (values, notes) and every p02 sweep failed with
AttributeError [error in earlier]); the reasons of NaNs travel in the frame's `meas_note`. The probability absorbed
excludes what a change of the grid dropped (its own quantity).

## Choices the wrapper makes (all computed, all shown)

* **The time step** is a power of two with the largest kinetic energy a wave can reach turned by at most 0.1 rad per
  step: the packet's (|k| + 3σ_k)²/2m (σ_k widened by measurements and jumps) plus the potential energy it can convert
  (V at the packet's centre or averaged over the wave now, minus the lowest V). Barriers above the particle's energy
  are not counted (the engine's `suggest_dt` counts the whole range of V): for the double slit's 3 eV wall that would
  be 4 times more steps; the wave's true error at t = 12 (against a Richardson reference) is 2.6·10⁻⁴ with this step
  and 1.6·10⁻⁵ with that one, and 6.0·10⁻⁴ and 1.1·10⁻³ when the wall is raised to 30 and 300 eV at the same step
  (review B6-Q11 [error in earlier]: the earlier "8 times" and "1.0·10⁻³ → 6·10⁻⁵" were not reproduced; the companion's
  estimates are 3.7·10⁻³ and 2.3·10⁻⁴). The environment's bound λ·dt ≤ 0.05 is kept: an environment whose rate needs
  a shorter step gets it in the same change (review B6-Q6: it was refused).
* **The absorbers' strength** (open edges, detectors with strength 0): the W₀ (of a log-spaced set around the
  particles' energy) that minimises the worst reflection + leak, from stationary transfer matrices of the absorber's
  own profile — for the edges over the normal wavenumbers |k|, |k| ± 2σ_k and |k| at 60°, for a detector at normal
  incidence over |k|, |k| ± 2σ_k. Measured 2026-11-03 on the presets (review B6-Q8, Q11; [error in earlier]: the
  earlier numbers were at normal incidence only and the screen's "10⁻¹¹" and "1.6 %" were not reproduced): the plane's
  edges reflect 1.4·10⁻⁷ at normal incidence, 5·10⁻⁵ at 60° and 7.8·10⁻³ averaged over all directions weighted by the
  flux they carry to the face (grazing waves are reflected by any layer); the volume's (6-nm layers for λ = 4 nm)
  2·10⁻⁵, 2·10⁻² and 4·10⁻²; in the 3-D preset the probability that comes back inside |x_i| < 14 nm agrees with a
  60-nm window to 3·10⁻⁵ at t = 18–22 (it was 10⁻³ with 4-nm layers tuned at normal incidence). The double slit's
  3-nm-edged screen reflects ≤ 1.2·10⁻⁶ and leaks ≤ 6·10⁻⁹ over the packet's waves (W₀ = 0.70 eV); a 1-nm edge
  reflects much more (3·10⁻³ at W₀ = 0.38 eV, review B6 s08b), so the presets' screens keep 3-nm edges. Both are
  running checks (the edges' with the angular average, the normal and 60°
  values in its note).
* **Scene changes take milliseconds** (review UX-ui U3, UX-params P30 [error in earlier]: every change re-tuned the
  absorbers through ~440 000 pure-Python transfer-matrix steps, 18–65 s per palette click with the world frozen). The
  transfer matrices are now multiplied pairwise in vectorised levels (``transfer.chain``, equal to the sequential
  product to rounding), all candidate strengths of an absorber in one call, and a choice is kept for the same waves
  and absorber (a pure function of them), so a change that touches neither (a box far away, a packet moved) re-tunes
  nothing. Measured in the double slit (CPU, the same host, load ~10–30; `../../reviews/archive/2026-11-04_internal_UX-ui/
  response_checks_p01-p02-v03/`): moving the packet 17.2 s → 0.01 s, a box far away 26.7 s → 0.007 s, a new
  wavelength 26.9 s → 0.25 s, a new detector 44.2 s → 0.18 s, a detector's edge 64.8 s → 0.17 s, a marker 51.6 s →
  0.025 s, a flux plane 38.8 s → 0.003 s; the 3-D ball's detector 15.5 s → 0.16 s.
* The default speed: the fastest particle crosses a tenth of the window per second.
* **Latencies of the live changes** (2026-11-11, CPU of the container, 2 threads, the shared host at load ~4; each a
  whole command: the engine's change, the re-tuning, the scene and the new picture): the double slit (256²) refined to
  384² 0.16 s, to 512² 0.19 s, coarsened back to 256² 0.05 s; its window 80 → 78 nm (step and window) 0.13 s; a packet
  dragged 0.025 s, thrown 0.18 s (the absorbers re-tuned for the new wavenumber); the wall or the screen dragged 0.02 s.
  The 3-D ball: 64³ → 96³ 0.19 s, its window 40 → 44 nm at 96³ 0.29 s, a packet dragged 0.17 s, the ball dragged
  0.06 s. Before LB1 each of the grid changes was a new world with an empty or preset scene. After review LB1-p02-ux
  (2026-11-12, same conditions): the AB preset's charged electron dragged 0.11 s (the magnetic translation and its
  kinetic-field test), a throw clamped by the world after the double slit's wall 0.29 s (the bisection on the scene's
  tests), the throw limit's refresh 5.5 ms every 20 frames, the tunnel carried into a new world of 384² with its wave
  0.21 s.

## Presets that demonstrate an effect (measured 2026-11-03)

* **"Which-path marker in the upper slit: …"** (review B6-Q9 [error in earlier]: the earlier 3 × 3 nm marker at the thin wall, with
  a coupling of 31 % of the electron's energy, acted as a ±0.12 eV lens, turned the marker by ~48° only and left a
  visibility of 0.61, while the label said the interference vanishes): the slits are 12-nm channels and the marker
  fills the upper one, 10 nm along the beam, with c = 0.021 eV = 5.6 % of the electron's energy and its edges across
  inside the wall. The transmitted wave's marker turns to P(1) = 0.95 (coherence 0.04); the screen's visibility near
  the centre falls from 0.94 (marker removed) to 0.18. What remains is the packet's spread of speeds: the marker turns
  by the time spent in it.
* **"Aharonov–Bohm: …"** (review B6-Q10: the tube sat behind the wall, in the beams' overlap, and the pattern missed the
  ideal by 5.6 % of its peak, left-right asymmetric): a tube of half a flux quantum, R = 0.5 nm, inside the 3-nm wall
  between the slits (its field e^{−r²/R²} is e^{−9} at the wall's faces). The screen's pattern equals the ideal
  half-fringe shift 2 (S₁ + S₂) − P₀ built from single-slit runs to 3.4·10⁻⁴ of its peak.
* **"3-D: an electron scatters off a ball"**: λ = 4 nm (with λ = 3 nm the wave's wavenumbers next to the ball exceed 2/3
  of the 64³ grid's band, which the scene now refuses).

## Running checks

Per particle: norm + absorbed = 1 (tolerance 32 ε per step); the energy ⟨H⟩ of a closed system against the bound
2‖Hψ‖e + e²‖H‖ given the companion's step-error estimate e (a bound given that estimate, not a rigorous one; its
reference is dated when it is taken; information when absorbers or the environment act); the time step's accumulated
error (companion: one step dt against two dt/2 every 64 scene steps, whatever the playback speed — a leading-order
estimate, not a bound: sampled only before and after a wall interaction it fell three times below the true error,
review B6-Q7 [error in earlier]: "rigorous"); the flux through each plane integrated in time against the probability
gained beyond it (information: an O(dt²) mismatch); the grid (probability in the outer third of k-space, information:
the scene refuses waves its grid cannot hold, below; the density on the window's faces); the reflection of the edges
and of every detector; for each particle with Bohm points: the control's accuracy (8 points integrated again with
order-16 interpolation and 4 times tighter steps: the median distance below half a grid step, at most one absorbed
elsewhere) and the counts absorbed by each absorber against the absorbed probabilities (binomial, 5σ); the estimated
cost per step on the device in use (CPU or GPU 0) and the real-time limit it gives.

## What the player shows

In a plane the wave's window is the main view, across the whole centre (review UX-ui U15, as p04); the 3-D scene is
shown beside it on request ("Show the 3-D view alongside", the "View" panel); in space unchanged. The 3-D scene (z up): the objects (potentials orange / blue for wells, detectors and markers, fields, planes), the wave
|ψ|² summed over the particles (each its own probability) — an image on the plane z = 0, or a volume in space — and the
Bohm points (registered ones dimmer); the window of the plane z = 0 (|ψ|², amplitude, log, or the phase of a single
particle) with the objects' outlines, the Bohm points and the measured positions (×); the laboratory's panels.

## Approximations and limits

* Non-relativistic particles (Schrödinger; spin ½ by Pauli), **no interaction between particles** (each its own wave:
  distinguishable, no exchange); in a plane the fields vary only in it (exact for uniform fields); the environment is a
  Markovian localisation model, not a particular gas or radiation.
* A particle in a **scene file** is kept as its packet (parameters), not as its wave (a 2-D wave is megabytes): loaded,
  it starts again from its packet at the file's time. A duplicate is a new packet with the same parameters.
* **The grid's resolution** (engine `_resolution_reason`, review B6-Q4): a packet needs |k| + 6σ_k ≤ π/d per axis;
  next to anything that acts on it the wave's wavenumbers, raised by the potential energy it can convert, must stay
  within 2/3 of π/d (the product V·ψ aliases beyond: a −3 eV well 4 nm wide on the 0.31-nm grid transmitted 0.923
  instead of 0.997). A set-up, a packet or a measurement that breaks it is refused with the reason.
* **A uniform field cannot be changed while a charged particle is in the window** where its vector potential changes
  (review B6-Q3): the impulse of the switch's induced field depends on how the magnet is built, which the scene's
  Landau gauge does not give (two set-ups identical in the window ended 29 nm apart). A flux tube can be changed (its
  gauge is that of a thin solenoid). Place charged packets after the fields; clearing the scene (the API's scene command `clear`; the player has no
  clear-scene button, objects are removed one by one with ✕ or Delete) removes the particles first.
  A refused removal leaves the object as it was (review UX-params P28 [error in earlier]: the field had already lost
  its link to the engine and every later removal or clearing of the scene failed with "Scene: 'o1'").
  A packet needs 7.4 σ to the window's faces (the grid is periodic), so windows are large.
* Open items: `../../STATUS.md`.

## Tests

`tests/test_p02_quantum.py`: every preset builds, runs and keeps norm + absorbed = 1; a packet's energy from its
wavelength and widths; the trap's coherent state (energy from ħω in meV, return after a period); the cyclotron orbit
from the field in tesla (the classical circle, turning towards +y for the electron); a position measurement narrows
the wave to 1/√(1/σ₀² + 1/σ²) per axis (and a σ the grid cannot hold is refused); Bohm points absorbed by the
detectors in the proportions of the absorbed probabilities (negative control: points at half speed fail the check),
the control catches the plain interpolation at k d ≈ 2, a jump keeps the absorbed points; the which-path and
Aharonov–Bohm presets show their effects; a strong environment shortens the step; a field is not changed under a
charged packet and a closed window refuses it; the inspector's height of a shape; a refused change leaves the scene as
it was; a change at the current moment keeps the balance; the scene file starts the same set-up at its time; values
that would overflow are refused; a change of only the Bohm count keeps the wave; scene changes are fast and re-tune only
what they change (U3); a palette packet lands outside the wall and says so (U4); objects wholly outside the window and
far packets are refused, a wave never becomes NaN, the Bohm draw refuses in words (U8, P29); a refused removal keeps
the object and clearing the scene still works (P28); the edges change at the current moment (U12). LB1 (plan P16.1–P16.3):
the grid and the window change live in the same world (the refined wave equals the exact resampling; the norm kept; the
run's checks pass after a refinement, a larger window and a coarsening back); a change that would drop or misplace
more than 10⁻⁶ of the norm is refused with the number, and an object's edge the coarser grid cannot resolve names the
object; objects keep their physical edges; every type declares handles and every positioned object is in `at`; a
dragged packet is the same wave translated (its Bohm points moved), a thrown one has k₀ = m v/ħ (a neutron's 1838.7
times the electron's), the throw's limit `v_max` follows the grid; a wall and a detector move at the current moment and
a registered packet dragged back is prepared afresh; the measurables are declared and every frame carries their values
as the scene's own readings (NaN with the reason), cheaply; a new world of the other dimension takes over what makes
sense there and refuses the rest in the owner's terms; a world with live changes continues from its checkpoint byte for byte and
repeats them deterministically. The engine's resampling, moves and boosts: `../../lfphys/tests/test_quantum_scene_live.py`
(a free packet continued exactly across every kind of change; a second route term by term; the negative control of a
linear interpolation; the periodic face; the balance; flux planes; the magnetic translation). The
shared tests continue a world from its checkpoint byte for byte (`../tests/test_checkpoint.py`, with a measurement on
each side) and rebuild it by replay (`../tests/test_restore.py`). The physics of the scene:
`../../lfphys/tests/test_quantum_scene.py`.
