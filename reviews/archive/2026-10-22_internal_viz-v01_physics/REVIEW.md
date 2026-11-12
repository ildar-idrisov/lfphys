# Physics review of `visualizations/v01_light_travel` (internal lens "physics")

**Status: awaiting processing** (by a participant other than the reviewer; `reviews/README.md`).
Delivered 2026-10-22. Reviewer: Claude (Opus) subagent, a separate agent with no part in building v01.
Scope: `v01_light_travel/engine/*.py`, `viz.py`, `web/view.js`, `tests/`; context `server/lfviz/` (sim, protocol,
runner) and `player/js/player.js`. Owner's requirements reviewed against (verbatim, `visualizations/RULES.md` §0):
"все визуализации должны быть точно выверены и согласованы с общепринятой физикой … должны отображать результат из
расчетов текущего запуска, а не из известного факта … должны иметь четкие причинно-следственные связи в запуске."

Code state reviewed (first 12 hex of md5): `apparatus.py a9d3122fc93c`, `arrivals.py 5d21a59e8888`,
`checks.py bac6da9245a4`, `kepler.py 3c215305d9b5`, `laws.py 958cee2ae172`, `light.py 70d86a72878d`,
`schwarzschild.py ddb8fcc3e91f`, `worldlines.py 188561ab8ee2`, `world.py 829b729eca99`, `viz.py 7777e636e990`,
`view.js 81c2271b9922`, `lfviz/sim.py 618d1c0cd38c`. Environment: Docker image `light-funnel-viz:latest`
(sha256:9bb51ebede18…), Python 3.11.17, numpy 2.4.6, scipy 1.17.1, mpmath 1.3.0. The project's own suite passes
(`35 passed`).

## Summary verdict

The core numerics are right and well built. The Schwarzschild quadrature (substitution, turning point, branches,
both image sides, radial rays) agrees with an independent 30-digit mpmath quadrature and with independent shooting
to 1e-12; the RK geodesic fans and their initial conditions from local static-frame directions agree with an
independent polar DOP853 integration to 3e-9; aberration, frame matrices, GR clock rates, the closed forms in
`checks.py` and the rod apparatus (140 configurations, SR/ether/emission, both synchronisations, both directions)
agree with hand-derived events to 2e-13; the exact Kepler hyperbolae agree with direct integration to 6e-11. The
separation "events solved exactly, drawing only interpolates" is sound.

The weak points are the **event bookkeeping around actions and the edges of the solvers**, and several places where
the display **reveals a value before the run has reached it** or **draws a fact instead of the run's result**:
GR/Newton arrivals are silently lost for receivers faster than ~0.6c (R1); a boost at an arrival time duplicates the
arrival (R2, systematic in GR/Newton); the declared modification emission + newton crashes in the Sun–Earth scene
and loses near-radial images (R3); B's clock is displayed as synchronised before the Einstein exchange has happened
(R4); in the emission theory a one-way result reaches A before B's reading can (R5); the lensing checks publish the
beam's future at t = 0 (R6); and the drawn light cone of an observer moving along y is wrong in SR (R7). None of
these change the headline numbers of the default presets (all their checks pass), but each breaks one of the
owner's three requirements in a reachable situation.

**Counts: 7 error, 9 should-fix, 10 nit (26 findings).**

| ID | sev. | one line |
|---|---|---|
| R1 | error | GR and Newton arrivals at receivers faster than ~0.6c are silently dropped (fixed-point iteration, 60 steps) |
| R2 | error | Boosting an observer exactly at an arrival time reveals the same arrival twice (always in GR/Newton) |
| R3 | error | Newtonian corpuscles: `kepler._radial` always raises (quad tolerance); inward radial crossings missing; Sun–Earth "emission + newton" crashes |
| R4 | error | B's clock shown with its Einstein-synchronised reading before the synchronisation exchange is complete |
| R5 | error | Emission theory: passing-flash result revealed at A before B's reading can reach A (order B→A) |
| R6 | error | Lensing: capture-boundary and swept-angle checks published at t = 0, before the beam reaches the hole |
| R7 | error | Drawn future light cone of an observer with v_y ≠ 0 has slopes ±c/γ instead of ±c (SR) |
| R8 | should-fix | GR local speed-of-light check uses the limit c as reference for a finite rod: shown FAILED in standard physics |
| R9 | should-fix | Doppler check pairs two pulses across a boost: shown FAILED in standard physics |
| R10 | should-fix | Boost validated only at the current event: GR worldline turns spacelike (run dies), rocket flies through the Sun with the exterior metric |
| R11 | should-fix | Reflection events at B are drawn on A's worldline in the spacetime diagram |
| R12 | should-fix | Apparatus rebuild relocates end B instantaneously (spacelike influence); light in flight is erased |
| R13 | should-fix | A completed passing measurement (both readings taken) is withdrawn by a later boost and never delivered |
| R14 | should-fix | Observer-frame slices reach into the lab future: pending events missing, worldlines extrapolated, nothing marked |
| R15 | should-fix | Photon-sphere circle drawn from the closed form 1.5 rs (RULES §2.1) |
| R16 | should-fix | Scenario texts state fixed numbers/claims ("8 мин 17 с", "на дни", "2.5 млн лет", "Шварцшильд") regardless of the run |
| R17 | nit | Receivers inside the photon sphere get no connection (light does reach them) |
| R18 | nit | Only the two lowest-order images are solved; README and two docstrings say "every image" |
| R19 | nit | Turning point by the trigonometric formula loses accuracy near b_c (affects only higher-order windings) |
| R20 | nit | Two checks are tautological (`flat_…` is the residual of the solved equation; `rate_station` repeats the formula) |
| R21 | nit | "Next event" is stuck when a pending event is at the current time |
| R22 | nit | 45° button uses the standard c, not the run's c; preset `andromeda_fast` fixes the walk speed in m/s from the standard c |
| R23 | nit | GR local cone uses the radial coordinate speed c(1 − rs/r) for the x direction also off the axis |
| R24 | nit | "seen" mode mixes retarded object positions with fronts on the simultaneity slice; no occlusion by the body |
| R25 | nit | Passing-flash direction taken from a zero vector when the source sits at A (accepted by accident) |
| R26 | nit | Undocumented modelling choices (emission-theory reflection rule, Kepler orbit with gravity "none", coordinate time in arrival texts, train pairs keyed by image index, dead code) |

## Findings

Evidence lines are quoted from `outputs/*.txt`; every script is in this folder and runs with `run_all.sh`.

### R1 (error) GR and Newton arrivals at fast receivers are silently dropped

*Location.* `engine/arrivals.py:114-128` (`gr_arrivals`), `:148-160` (`newton_arrivals`).

*What is wrong.* A moving receiver's arrival is the fixed point t = t0 + Δt(x_R(t)), iterated at most 60 times to
1e-13. The iteration contracts with factor ≈ (receiver velocity along the line of sight)/(light speed), so for
β ≳ 0.6 it cannot reach 1e-13 in 60 steps; `ok` stays False and the image is dropped without a notice. An observer
who is boosted to 0.7c in the lensing scene never receives the flash.

*Evidence.* `check_causality.py` probe B (independent root by `brentq` on F(t) = t − t0 − Δt(x_R(t)) with the
engine's own `connect`):
```
beta = 0.6: engine arrivals {-1: 0.031188447088384183, 1: 0.031232202031965424}; independent root {1: 0.03123220203207278, -1: 0.031188447088491004}
beta = 0.75: engine arrivals {}; independent root {1: 0.0501576609130571, -1: 0.05008470445283848}
```
`check_fast_receivers.py`: lensing and lensing_newton, boost 0.7c or 0.9c (0°, 90°): `scheduled arrivals at obs = 0`.

*Fix.* Replace the iteration by bracketing root finding on F(t) per image side. For a subluminal receiver F is
strictly increasing (dF/dt = 1 − (∇Δt)·v > 0), so a doubling bracket from max(t0, t_from) plus `brentq` always
converges. If no root exists, emit a notice instead of dropping the image. Add a test with a 0.9c receiver in GR and
in Newton mode.

### R2 (error) A boost at an arrival time duplicates the arrival

*Location.* `engine/world.py:399-402` (rescheduling all pulses after a boost from `t_from = t`);
`engine/arrivals.py:125, 159` (`t >= t_from`), `:90` (`s >= 0.0`).

*What is wrong.* "Next event" followed by an action at that moment is the natural way to act at an arrival. The
arrival at time t has just been revealed. After the boost, the recomputation from `t_from = t` finds the same event
again, because the fixed point equals t_from (GR, Newton) or the quadratic has a root s ≈ 0 by round-off (flat).
The arrival is revealed a second time. In GR and Newton mode this happens every time; in flat runs it depends on
round-off.

*Evidence.* `check_causality.py` probe G:
```
lensing              obs boost +0.2c at its arrival t = 0.0123913843526: arrival revealed 2x [0.012391384352624, 0.012391384352624] -> FINDING: duplicate
lensing_newton       obs boost +0.2c at its arrival t = 0.0115661896305: arrival revealed 2x ...
sun_earth            rocket boost +0.2c at its arrival t = 247.181832585: arrival revealed 2x ...
measure_c            obs3 boost +0.2c at its arrival t = 0.00867128190396: arrival revealed 2x ...
```

*Fix.* Keep a set of revealed (pulse, receiver, image side) keys and skip them when rescheduling; or require
t_arr > t_from strictly. For the flat quadratic, require s > a round-off margin when tau0 > 0. Add a test: jump to
an arrival, boost, assert one arrival per (pulse, receiver, image).

### R3 (error) Newtonian corpuscles: radial paths crash or are lost

*Location.* `engine/kepler.py:83-90` (`_radial`), `:41` (radial branch), `:97-133` (`connect_newton` scan).

*What is wrong.*
1. `_radial` calls `integrate.quad(..., epsabs=0.0, epsrel=1e-14)`. scipy 1.17 rejects this, because epsrel must be
   greater than 50·eps = 1.1e-14. So every outward radial corpuscle raises `ValueError`. In the Sun–Earth scene the
   flare, the station and the rocket are on the x axis, so the emission angle α = 0 of the scan is exactly radial.
   The declared modification "emission + newton" therefore crashes at the first flash (the pulse is already drawn,
   but its arrivals are not scheduled).
2. For an inward radial corpuscle `_radial` returns `[]` (`if rdot < 0`), although the corpuscle crosses every
   radius between its start and the absorber.
3. In `connect_newton`, the scan point where a crossing list is empty disables both neighbouring intervals. A target
   close to the source–body line on the near side is therefore never connected, even 1e-3 rs off the line.

*Evidence.* `check_sweep.py`: `[sun_earth emission+newton] EXCEPTION at t = 0: … ValueError: If 'epsabs'<=0,
'epsrel' must be greater than both 5e-29 and 50*(machine epsilon).` `check_causality.py` probe O (source at
(−100, 0) rs):
```
target [-5.e+01  1.e-03] rs: 0 image(s), dt = []
target [-200.    0.] rs: ValueError: If 'epsabs'<=0, ...
kepler.crossings for a radially inward corpuscle to r = 50 rs: []  <- the corpuscle does cross r = 50 rs
```
Generic (non-radial) hyperbolae are correct (see "checked and correct").

*Fix.* Use epsrel ≥ 1e-13, or the elementary antiderivative of dr/√(2E + 2μ/r). Return the inward crossing for
r_abs < rT < r0 (bound orbits are already rejected). With the radial point no longer empty, the scan
brackets near-radial roots. Add a test for the preset with `kinematics = emission, gravity = newton` in `sun_earth`,
and a near-radial target test.

### R4 (error) B's clock is displayed as synchronised before the synchronisation has happened

*Location.* `engine/apparatus.py:83` (offset fixed at build time from the future return event t3),
`:100-105` (`reading` returns it whenever the offset exists), `engine/world.py:416-418` (frame sends `tau_b`),
`web/view.js:272` (shows "(нет синхр.)" only if `tau_b` is null).

*What is wrong.* The Einstein offset is computed at assembly from events t2 and t3 that lie in the future. From the
first frame on, the frame carries B's synchronised reading, and the view prints it as `B τ=…`; only the rod's opacity
hints that synchronisation is incomplete. This is a value derived from a future event shown before the run reaches
that event. It also displays a synchronisation that does not yet exist.

*Evidence.* `check_causality.py` probe A:
```
t = 0.0005 s, obs2: synced = False, sync completes at t = 0.002311 s, tau_B sent to the view = -6.733344090500885e-05
```

*Fix.* Until `t_sync_done <= t`, send `tau_b = None` (or B's raw clock, labelled unsynchronised). In the view, test
`o.synced`.

### R5 (error) Emission theory: a one-way result reaches A before B's reading can

*Location.* `engine/apparatus.py:131-137` (`passing`: `if second == "A": t_known = t_second`).

*What is wrong.* When the flash passes B first, the code assumes B's reading arrives at A together with the flash.
That holds when the reading signal and the flash have the same lab speed (SR, ether). In the emission theory the
flash moves at c + u and B's signal at c + v_B. For u "faster" than v_B along the propagation direction, the result
is revealed before the information can be at A. This is a causality violation inside the declared modification.

*Evidence.* `check_causality.py` probe F (emission, source moving at −0.5c from +x, rod at rest):
```
measure event revealed at t = 0.008671282 s; flash at B 0.008004154, at A 0.008671282; B's reading can reach A at 0.009004846 s; measured 1.500000 c
FINDING: result revealed 0.3336 ms before B's reading can arrive at A
```
The measured value itself (1.5c = c + s(u − v)) is right.

*Fix.* `t_known = max(t_second, self.light(t_first, "B", "A"))` when `first == "B"`, still capped below by
`t_sync_done`. Add an emission-theory test with the order B→A.

### R6 (error) Lensing checks publish the beam's future at t = 0

*Location.* `viz.py:273-277` (`at_zero` calls `_deflection_checks` right after tracing), `:298-337`.

*What is wrong.* The capture boundary (which rays are captured), the swept angles of whole ray paths and the
deflections are emitted as checks at t = 0, when the beam has just been launched. The captured rays reach the
horizon only 4–5 ms later. RULES §2.2: "A consequence is revealed to the viewer only when the run's time reaches
it." The values are correct; their timing is not.

*Evidence.* `check_causality.py` probe S:
```
check 'bc' emitted at t = 0.0: value 2.6273285475484083, note: граница между захваченными и ушедшими лучами пучка: [2.5426, 2.7121] r
the beam's captured rays reach the horizon at lab t in [4.097e-03, 5.002e-03] s (~42-51 rs/c), i.e. after the check was shown
```

*Fix.* Schedule the `bc` check as an event at the latest end time of the rays that define the bracket, and each
`swept_` check at its ray's end time. `defl_` (quadrature of an infinite path) is not a run event: show it with the
swept check, or label it as a reference computation.

### R7 (error) Drawn light cone of an observer moving along y is wrong in SR

*Location.* `engine/world.py:446-448` (`_cone`: `emit_velocities([[±1, 0]], v)`); drawn at `web/view.js:417`.

*What is wrong.* The diagram is an (x, t) projection. The future cone's x-extent is the extreme lab x-velocity of the
emitted light, ±c in SR. The engine instead takes the rays emitted along ±x in the observer's rest frame. With
v_y ≠ 0 these have lab x-velocity ±c/γ, so the drawn cone is too narrow. For the emission theory the same code gives
v_x ± c, which is right. For the ether it gives ±c, also right.

*Evidence.* `check_causality.py` probe D: `obs1 v = (0, 0.8c): cone 'fut' x-slopes = [0.6, -0.5999999999999998] c,
'past' = [1.0, -1.0] c`.

*Fix.* SR and ether: `fut = [c, −c]`. Emission: `[v_x + c, v_x − c]`. Equivalently, take the extreme x-component
over the lab velocities of the whole fan.

### R8 (should-fix) GR local c check is shown FAILED in standard physics

*Location.* `engine/world.py:366-381`.

*What is wrong.* The rod has proper length ell = 1e-3 r, and the measured round-trip speed differs from c by
O(ell·rs/r²). That is a correct finite-size effect. The check, however, compares it with c at the default tolerance
1e-9, so at 60 rs it shows ✗.

*Evidence.* `check_causality.py` probe C:
```
lensing: c_loc = 299793716.843, ref = 299792458, rel = 4.199e-06, tol = 1e-09 -> shown ✗ (FAILED)
closed form for this rod: 2 ell / (sqrt(f_A) * 2 [Δr + rs ln((r_B - rs)/(r_A - rs))]/c) = 299793716.843; engine vs closed form rel = 1.14e-13
```

*Fix.* Use the closed form for the finite radial rod as the reference (above), and put "→ c as ell → 0" in the
note. Alternatively shrink the rod and set the tolerance to the analytic bound.

### R9 (should-fix) Doppler check pairs pulses across a boost

*Location.* `engine/world.py:251-263` (`_train_arrival`: consecutive arrivals in `train_arrivals[(train, obj,
image)]`).

*What is wrong.* After a receiver (or the source) is boosted, the next arrival is paired with one received before
the boost. The interval mixes two motions, while the reference uses the new velocity. The check is shown FAILED
although the physics is standard.

*Evidence.* `check_causality.py` probe E (obs1 boosted to 0.3c between pulses):
`t = 0.017224: Частота у «Наблюдатель 1» … value 0.844668396, ref 0.733799386, rel +1.51e-01`.

*Fix.* On a boost of the receiver, clear its lists; on a boost of the source, start a new pairing segment. Pair only
arrivals whose emission and reception lie in single inertial segments; otherwise emit with ref = None and a note.

### R10 (should-fix) Boosts validated only at the current event; GR worldlines that cross the body or turn spacelike

*Location.* `engine/world.py:388-394` (`clock_rate` at `obj.wl.pos(t)` only); `engine/worldlines.py:26-45`
(`clock_rate`) and the `Piecewise` docstring "inertial segments"; `engine/schwarzschild.py:156` (no connection
below r_abs).

*What is wrong.* In GR a boost sets a constant Schwarzschild coordinate velocity. That is not an inertial motion: it
needs thrust, and the docstring calls it "inertial". It can be timelike now and spacelike later. In the lensing scene,
0.5c inward is accepted, works down to r = 2 rs, and then every `frame()` raises, so the run is dead. A rocket boosted
towards the Sun flies through the absorbing body. Its clock keeps running with the exterior metric inside the Sun,
and its arrivals vanish silently. The run dies near the centre.

*Evidence.* `check_causality.py` probes H and I:
```
last good frame at r = 2.000 rs; exception at t = 0.0114764 s (observer at r = 1.750 rs): ValueError: worldline is not timelike
t = 495 s: rocket at r = 0.863 R_sun (inside the Sun), frame OK, tau = 428.682506
exception at t = 500.0 s, rocket at r = 0.2144 R_sun: ValueError: clock inside the horizon
```

*Fix.* Validate the whole future straight segment: the minimum of q(t) along a straight coordinate line, plus its
intersection with r = R or r_abs. End the worldline at the body (an event "collided/absorbed") or refuse the boost
with the reason. State in the UI and README that the GR "speed" is the coordinate velocity, and that the local speed
for a static observer is (v_r/f, v_t/√f).

### R11 (should-fix) Reflection events drawn on the wrong worldline

*Location.* `engine/world.py:296` (sync events scheduled with `obj = observer`), `:356` (measurement reflection);
`web/view.js:392-399` (every event drawn at `wlPos(wls.get(e.obj), e.t)`).

*What is wrong.* "Signal reflected from B" is drawn on A's worldline at the reflection time, hundreds of km from
where it happened.

*Evidence.* `check_causality.py` probe R:
`'Наблюдатель 1: сигнал синхронизации отражён от B' … marker drawn at A x = 0.00 km; the reflection happened at B x =
300.00 km` (similarly obs2: 259.8 vs 519.6 km; obs3: −86.6 vs 173.2 km).

*Fix.* Send the event's position (x, y) with every event and draw it there, or give B its own object id.

### R12 (should-fix) Apparatus rebuild is an instantaneous, spacelike relocation of B

*Location.* `engine/apparatus.py:54-67` (`build`), `engine/world.py:397-398`; `web/view.js:487` (old signals cut at
the rebuild time).

*What is wrong.* When A is boosted, B is placed at once at its new rest-frame position, at a distance of hundreds of
km, so the action at A changes B at a spacelike separation. The light already in flight in the old rod disappears
from the diagram at the same lab instant. The README says "re-assembled" but not that this step is acausal and
frame-dependent: the jump is defined at A's lab time.

*Evidence.* `check_causality.py` probe L: `at lab t = 0.005: A at x = 749.481 km; B before 1009.289 km, after 929.481
km: jump -79.808 km in zero time, at distance 259.8 km from the boost event`.

*Fix.* Either model it causally: A sends a light signal, B changes velocity on reception, the rod is usable after B
is at rest in the new frame and re-synchronised. Or state it in the README and UI as an explicit idealisation and
draw the relocation as such. In both cases let light already emitted continue its path.

### R13 (should-fix) A completed measurement is withdrawn by a later boost

*Location.* `engine/world.py:395` (`_cancel` of every pending event with the observer in `deps`), `:307-308`.

*What is wrong.* Both readings of a passing flash were taken before the boost, and B's reading was already on its way
to A. After the boost the pending result is cancelled and never recomputed, because rescheduling starts at t and
`min(ta, tb) < t_build` rejects it. Withdrawing the result of a past measurement rewrites the past (RULES §2.2: "the
past is never rewritten").

*Evidence.* `check_causality.py` probe M: `pending result for obs2 at t_known = 0.028325 (now 0.0279); B's passage
already happened: True` → `measure events for obs2 after the run: 0`.

*Fix.* On a boost, keep results whose readings are complete. Recompute only the delivery of B's reading to A along
A's new worldline: B's signal is already emitted, so its arrival at A changes but the reading does not.

### R14 (should-fix) Observer-frame slices are partly extrapolated and partly empty, unmarked

*Location.* `web/view.js:110-130` (`onSliceWl` extrapolates the last segment), `:183-186` (pulses filtered by lab
time), `:444-452` (table uses only revealed `emit` events); `engine/world.py:450-470` (`_now_at`).

*What is wrong.* An observer's simultaneity slice reaches into the lab future, by days at Andromeda and by Myr at
±0.5c. On that part, worldlines are drawn where they would be if nobody acted, but an action at a later lab time can
change them. Events that the observer's own slice has already passed are not shown, because the run has not
revealed them in lab time. In the Andromeda paradox with the event at lab +2 d, the walker towards Andromeda has the
event on the past side of his "now" (+4.26 d), yet neither the diagram nor the table can show it. The paradox
display thus depends on lab revelation, and the viewer cannot tell computed parts from extrapolated parts.

*Evidence.* `check_causality.py` probe K: `walk_to's 'now' at Andromeda = lab t +4.2642 d (event at +2 d is on his
PAST side); emit events known to the view: 0`.

*Fix.* Grey out or hatch the part of the slice with lab time > t ("not yet computed — the world may still change").
Pass scripted world events from the initial data to the view as planned events, so that they can appear on an
observer's slice. State the rule in the help text.

### R15 (should-fix) Photon sphere drawn from the closed form

*Location.* `web/view.js:172-175`; `viz.py:451` (`photon_sphere = 1.5 * rs` in the header).

*What is wrong.* A dashed circle at 1.5 rs is drawn into the scene from the known result. RULES §2.1: "Closed-form
results of the known theory may appear only as references in the checks panel." The circle is also drawn inside a
star (R > 1.5 rs), where no photon sphere exists. It is hidden under the body's fill, but the logic is wrong.

*Fix.* Remove it, or draw a computed object (for example, the radius around which the traced near-critical rays
wind), labelled as computed. Keep 1.5 rs as a reference in the checks panel only.

### R16 (should-fix) Scenario texts state fixed results and claims independent of the run

*Location.* `viz.py:200-204` (sun_earth), `:292-296` (lensing), `:371-377` (andromeda).

*What is wrong.* The header text, shown in "О запуске" and the help, asserts numbers and mechanisms as known facts.
They are wrong as soon as the parameters or laws change. This is exactly what the owner excluded ("not from a known
fact").

*Evidence.* `check_causality.py` probe J:
```
sun_earth, 5 au, c x 0.5: header text says 'примерно за 8 мин 17 с'; the run computed 83.09 min
andromeda, 1000 ly, ±0.5c: text says '...различается на дни...', '...через 2.5 млн лет;...'; the run's 'now' offset at Andromeda = 500.0 yr
lensing with gravity 'none' (modified): text still says: '... Всё это — интегрирование нулевых геодезических Шварцшильда, никаких готовых формул отклонения.'
```

*Fix.* Keep the texts qualitative and law-aware, or fill the numbers in from the run's computed events once they
exist.

### R17 (nit) No connection for receivers inside the photon sphere

*Location.* `engine/schwarzschild.py:156`. `connect` returns `[]` when min(r1, r2) ≤ 1.5 rs, although light reaches
r ∈ (r_abs, 1.5 rs] (for example radially). `check_causality.py` probe N: `radial connection 60 rs -> 1.4 rs: 0
image(s)`. Such receivers are reachable only by boosts, and R10 interferes there. *Fix:* implement the in-branch for
r < 1.5 rs, or emit a notice "connection not computed".

### R18 (nit) "Every image" means the two lowest-order images

*Location.* `v01_light_travel/README.md:14` ("for every image (GR)"), `engine/arrivals.py:13` and
`engine/kepler.py:10` ("every image"). `gr_arrivals` and `schwarzschild.connect` correctly say "primary and
secondary". For a black hole the swept angle diverges at b_c, so images with θ + 2πk exist; only k = 0 on both sides
is solved. The RK fan can show looping rays that reach the observer with no arrival event. *Fix:* say "primary and
secondary (lowest-order) images" everywhere, or solve θ + 2πk while Φ allows.

### R19 (nit) Turning point near b_c

*Location.* `engine/schwarzschild.py:36-42`. acos near −1 is ill-conditioned. At b/b_c − 1 = 1e-11 the root has
relative error 7e-12 and Δφ has relative error 2e-7. With the turning point refined in 40 digits, the engine's own
`integrals` is exact to 9e-13, so the error comes from the root formula alone (`check_schwarzschild.txt`, last
block). This matters only for windings beyond 2π, where b lies very close to b_c. *Fix:* in the turned branch, solve
for r_tp and compute b = r_tp/√(1 − rs/r_tp) (well conditioned).

### R20 (nit) Two checks cannot fail independently

*Location.* `engine/world.py:216-219`: the `flat_…` check compares the solver's root with |x_R(t_root) − x_0|/c, which
is the residual of the equation the solver just solved. `viz.py:212-214`: `rate_station` compares
`tau(1) − tau(0) = sqrt(1 − rs/r)` with `sqrt(1 − rs/r)`. *Fix:* label them as self-consistency or residual checks,
or replace them with independent quantities (for example, the station's rate from the received period of a pulse
train).

### R21 (nit) "Next event" stuck at the current time

*Location.* `server/lfviz/sim.py:104, 134`. `_advance(target)` does nothing when target == sim.t, so a pending event
at the current time (for example, a zero-delay arrival after a flash at a point where other observers are) is never
revealed by ⏭. `check_causality.py` probe Q: `after pressing 'next event' 3x: sim t = 0.0, arrivals revealed: 0`.
*Fix:* call `sim.advance(te)` also when te == sim.t.

### R22 (nit) Standard c hard-wired in two places

*Location.* `web/view.js:63`: the 45° button uses `C_SI`, so light is not at 45° when c_factor ≠ 1; `c()` exists.
`viz.py:120`: preset `andromeda_fast` sets `an_walk = 0.5 * 299792458` m/s, which is not 0.5c with a modified c.
*Fix:* use `c()`; express that preset's speed in units of the run's c.

### R23 (nit) GR local cone off the axis

*Location.* `engine/world.py:441-445`. The x-direction coordinate light speed at a point off the x axis is
c f / √(cos²α + f sin²α) (α the angle between x̂ and the radial direction). It equals c f only on the axis; for
tangential directions it is c √f. Observers leave the axis after a boost with an angle. *Fix:* use the formula above.

### R24 (nit) "seen" mode

*Location.* `web/view.js:182-201`, `engine/world.py:472-497`. Objects are placed at their retarded (past-cone)
events, while light fronts are still drawn on the simultaneity slice. In flat runs with a body (sun_earth with
gravity "none"), `_seen` ignores occlusion by the body. *Fix:* hide fronts (or show only light that has reached the
observer) in "seen" mode, and test the segment against the body.

### R25 (nit) Passing-flash direction from a zero vector

*Location.* `engine/world.py:309-313`, `engine/arrivals.py:96`. When the flash is emitted at A (dt = 0, for example
obs1 flashing at t = 0 in `measure_c`), the A-arrival direction is [0, 0]. The rest-frame cosine is then computed
from −v (or is NaN for v = 0), and the |cos| ≈ 1 filter passes by accident. The measured values are right
(`check_colocated_flash.txt`). *Fix:* take the direction from the B passage, or from x_B(t_b) − x_A(t_a).

### R26 (nit) Undocumented modelling choices

1. Emission theory: a moving mirror re-emits at c relative to itself (`apparatus.light`, B as source). Historical
   emission theories differ on reflection (source, mirror and image-source variants). This choice should be named.
2. `viz.py:182-184`: Earth keeps its Kepler orbit when gravity is "none" (a code comment only; not in the README or
   UI).
3. `world.py:204`: "пришёл свет … через Δt" is Schwarzschild coordinate time, not any clock's reading; say so in GR
   runs.
4. `world.py:253`: train pairs are keyed by image index (time order), not by image side. Order changes would mix
   images.
5. `viz.py:264-266`: dead code (`r_abs` computed and unused).

## Checked and found correct (with evidence)

- **Schwarzschild quadrature** (`schwarzschild.py`): integrands dφ/dr, c dt/dr; P = (r − r_tp)Q factorisation;
  s-substitution dφ = 2b ds/√(rQ), c dt = 2r^{3/2} ds/(f√Q); u = ln r route; trigonometric largest root; branch logic
  out / in / turned with the joins at b(r1) and b(r2); both sides; radial b = 0; local emission and arrival directions
  sin α = b√f/r. Over 18 images in 9 geometries (outward, inward, near 1.6 rs, same radius, radial both ways,
  1e6 rs): Δφ to 1.6e-12 and Δt to 1.1e-13 against a 30-digit tanh-sinh quadrature of the original integrands.
  Shooting from the engine's `emit_dir` with an independent polar DOP853 integration reaches the target at the
  engine's Δt (1e-11 typical; 3e-7 at 1e6 rs, limited by the reference integrator).
  `outputs/check_schwarzschild.txt`.
- **Darwin closed form** (`checks.darwin_deflection`): matches the standard form (Q² = (P − 2M)(P + 6M),
  k² = (Q − P + 6M)/(2Q), sin²ζ = (Q − P + 2M)/(Q − P + 6M)), and the project's tests agree with the quadrature to
  1e-10. The text of Darwin (1959) itself was not re-read (see "not checked").
- **RK geodesics** (`light.trace_gr`): the Cartesian central-force form is exactly the null geodesic. Its energy
  integral gives r′² = 1 − (L²/r²)(1 − rs/r), and the initial |V|² = n_r² + n_φ²/f = 1 + rs L²/r³ is consistent.
  Initial conditions from local static-frame directions match an explicit tetrad (6.7e-16; null residual 1e-15). At
  the default η = 4e-3, 71 escaping rays agree with an independent polar DOP853 integration to 2e-10 in r and
  2.8e-9 in ct. `outputs/check_rk_and_frames.txt`.
- **Frames and aberration**: `Laws.frame_matrix` equals the textbook boost (Jackson eq. 11.98) to 0. `aberrate_sr`
  and `emit_velocities` match the textbook boost to 4e-16 and the closed form cos θ = (cos θ′ + β)/(1 + β cos θ′) to
  2e-16, with |u| = c to 1e-15. `local_velocity_static_frame` (v_r/f, v_t/√f) is exact.
- **Proper time**: dτ/dt = √(f − (v_r²/f + v_t²)/c²) re-derived from the metric. The circular orbit with ω² = GM/r³
  (exact in Schwarzschild coordinates) gives √(1 − 1.5 rs/r); the static rate is √(1 − rs/r); Galilean τ = t.
- **Flat arrival solver**: quadratic coefficients A = u² − c², B = 2d·u − 2c²τ₀, C = d² − c²τ₀² re-derived;
  stable root selection; the emission theory's front centred on the moving source; the orbit branch is monotone for
  subluminal receivers.
- **Apparatus and reference formulas** (`apparatus.py`, `checks.py`): 140 configurations (SR/ether/emission ×
  Einstein/lab sync × v ∈ {0, ±0.5, 0.9}c × u ∈ {0, ±0.3}c × both directions). The engine's measured one-way speed
  agrees with hand-made event geometry to 2.2e-13, and `checks.one_way_speed` agrees to 1.2e-13. `round_trip_speed`
  (along/across, all kinematics) agrees to 2e-16 and `doppler_ratio` to 1e-15. The Lorentz-transformed rest-frame
  rod gives the right lab length (L0/γ). `outputs/check_apparatus.txt`.
- **Kepler hyperbolae** (`kepler.crossings`, non-radial): 293 random unbound orbits (both senses, before or after
  periapsis, absorption) agree with DOP853 in the count of crossings, to 6e-11 in time and 2e-11 in position.
  `connect_newton` images re-shot to 1.3e-11. `outputs/check_kepler.txt`.
- **Simultaneity and "seen"** at 2.5 Mly: `now_at` equals t + v(x_q − x_o)/c² (SR) or t (Galilean), and `seen` equals
  t − |x_o − x_q|/c, to 0.016 s at t = 7e13 s, which is one ulp of t. The ±4.264 d offsets are right. Blobs are
  float64 end to end (`protocol.py`), so the day-level offsets survive. `outputs/check_simultaneity.txt`.
- **Modified physics flags and consistency**: `c_factor`, kinematics and gravity are flagged, and gravity is
  correctly un-flagged in mass-free scenes. Invalid combinations are refused. In a sweep of 24 configurations
  (c × 0.5/2/3, all laws, star lens, collinear ring, near observer, 1e-9 and 1e4 Mly, ±0.99c) no check failed and no
  error occurred, except the R3 crash. `outputs/check_sweep.txt`.
- **Gravitational redshift** reference √(f_e/f_r) and the README numbers (496.684 s, Shapiro excess 52.9 µs).
- **Co-located flash** (dt = 0): the measured values are right in SR, ether and emission (c; c(1 − β²) = 0.75c;
  0.5c and 1.5c). `outputs/check_colocated_flash.txt`.
- **Pending-event recomputation after a boost** is right in substance apart from R2, R9 and R13: arrivals at the
  boosted observer are recomputed on the new worldline, light already emitted by it is untouched, the apparatus is
  rebuilt and re-synchronised, and trains are rescheduled by proper time.

## Not checked

- No browser was run. The `view.js` findings (R7 drawing, R11, R14, R15, R22–R24) come from reading the code against
  the frame data produced by the harness.
- Replay and seek behaviour of the player (timeline rewinds while view state accumulates) beyond reading
  `player.js`; the server, record thinning and performance.
- The Darwin (1959) and Soldner citations were not re-read from the sources. The formulas were checked numerically
  and against the standard form only.
- STATUS items V1–V3 (no observer frames, apparatus or "seen" in GR) are known limitations and are not repeated here.

## Files

| file | what it does |
|---|---|
| `check_schwarzschild.py` | 30-digit mpmath quadrature and shooting against `connect`/`integrals`; turning point vs numpy/mpmath; near-b_c precision |
| `check_rk_and_frames.py` | RK fan vs polar DOP853; tetrad and textbook-boost check of initial conditions and aberration; drawing interpolation error |
| `check_apparatus.py` | hand-made event geometry vs engine apparatus and `checks.py` (one-way, round trip, Doppler) |
| `check_kepler.py` | Kepler crossings and `connect_newton` vs direct integration |
| `check_simultaneity.py` | `now_at` / `seen` vs closed forms at Andromeda distances |
| `check_causality.py` | probes A–S (causality, bookkeeping, robustness; the R-findings above) |
| `check_sweep.py` | 24 parameter sets: errors, failed checks, arrivals |
| `check_colocated_flash.py`, `check_fast_receivers.py` | edge cases for R25 and R1 |
| `run_all.sh` | re-runs everything in Docker into `outputs/` (about 2.5 min) |
| `outputs/*.txt` | the outputs quoted above |

Reproduce from the light-funnel root: `sh reviews/2026-10-22_internal_viz-v01_physics/run_all.sh`. A single script:
`docker run --rm -v $PWD:/lf -w /lf/visualizations -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server
light-funnel-viz python3 /lf/reviews/2026-10-22_internal_viz-v01_physics/<script>.py`. The scripts touch nothing
outside this folder; the root path is marked by a comment in each script.
