# v10 — What a fast observer really sees

**English** | [Русский](README.ru.md)

A wrapper over the engine `lfphys` (plan item P14.2, on P9, P10 and P11) and the third world of the player's 3-D
environment (`../RULES.md` §2.10). Self-luminous bodies (black bodies with patterns) move past an observer, or the
observer flies through them; the run computes the observer's image by light-time ray tracing and shows, in 3-D, the lab
at the current moment and where the light the observer receives now was emitted.

## What the run computes (engine modules)

| module | layer | role |
|---|---|---|
| `core.raytrace` | core | the image: every pixel's photon Lorentz-transformed into the lab (aberration), its past light ray intersected exactly with the bodies' world tubes in their rest frames (light-time), the light seen as a black body at D T (Doppler colour, searchlight); the sky and stars; the retarded points of bodies; Penrose's outline by bisection; the references (closed forms) of the checks; CPU or GPU 0 (kernel "relativity.raytrace") |
| `core.lorentz` | core | boosts, `retarded_time`, `sphere_outline`, `aberrate` (references) |
| `core.optics.radiation` | core | Planck's law |
| `tools.colour` | tools | display only: the CIE 1931 functions (fit of Wyman, Sloan & Shirley 2013), black-body XYZ, sRGB |

The apparatus (`viz.py`, no physics of its own): the scenes, the meshes of the bodies for the 3-D view, the observer's
piecewise-uniform worldline (the live boosts), the colours of the image (exposure, tone mapping, false colours).

## The physics

* **Bodies** are rigid in their rest frames and move uniformly: a body point q (rest-frame offset from the centre) is in
  the lab at c0 + v t + q − γ/(γ + 1) (β·q) β at lab time t (Lorentz contraction along v).
* **Aberration.** The camera is in the observer's rest frame (the axes of `boost(u)`); the photon arriving from the
  look direction d′ has the observer-frame wave vector k′ = (1, −d′) and the lab wave vector k = boost(−u) k′.
* **Light-time.** The pixel's past light ray X(s) = (c t − s, x − s n) (n the photon's lab direction, s ≥ 0 the lab
  distance) is, in a body's rest frame, a straight line P + s Q; the photon left the body where the line first meets the
  surface (sphere: a quadratic; box: slabs; rectangle: one linear equation). The nearest emission over all bodies wins.
  So an approaching body is seen where it was long ago (far away, stretched), a receding one where it was recently;
  a cube passing at speed shows its back face (Terrell 1959); a sphere's outline stays a circle (Penrose 1959).
* **Colour and brightness.** Every surface emits as a black body at the temperature T of its rest-frame pattern,
  isotropically in its rest frame. I_ν/ν³ is invariant, so the observer sees a black body at D T, D = ν_obs/ν_emit =
  (k·U_obs)/(k·U_body): the colour (Planck at D T through the CIE functions) and the brightness (radiance ∝ (D T)⁴,
  the searchlight effect) follow exactly. A uniform black-body sky at rest in the lab is seen at T/(γ(1 − β cos θ′)) —
  the dipole of the cosmic background; point stars at rest in the lab are aberrated, seen at D T with flux D² times
  that at rest.
* **For comparison only** (labelled in the window and the image's status; not what is seen):
  * "for comparison: geometry only" — the same light-time and aberration, colours and brightness of the rest frame (D set to 1);
  * "for comparison: an instantaneous snapshot" — the observer's simultaneity instead of the past light cone (light of infinite speed in the observer's
    frame): the Lorentz-contracted bodies of textbooks, which light never shows. For a moving observer that
    simultaneity contains lab times after the world's time; the bodies' motion is fixed for the world (nothing a live
    change could alter), so this comparison reveals no consequence ahead of its time;
  * false colours of D and of the emission delay.
* **Live boosts.** The observer's velocity is live: a boost of a point observer at the current event changes the
  image at once (the same light, other directions and frequencies — aberration is instantaneous); the worldline stays
  continuous, the proper time runs on. The bodies' velocity is a world parameter: an instantaneous velocity change of an
  extended body is not a rigid motion (the parts would change velocity at different times in its new frame), so it is
  not offered as a live change.

## The scene in 3-D (env3d)

* The lab at the current lab time: every body's mesh at its lab-simultaneous place (semi-transparent, contracted
  along its velocity: an affine map per frame, `frame.bodies[].A, b`), the floor and towers at rest.
* The retarded shapes (meshes updated with every image): the points of each moving body's world tube on the
  observer's past light cone — where the light the observer receives now was emitted — in the observed colours, the
  points the observer actually sees bright, hidden ones dim. They come from `raytrace.retarded_points`
  (`lorentz.retarded_time`) and a visibility trace.
* The observer: a marker, its velocity (arrow) and the lab directions from which the light at the image's border
  arrives (aberration of the field of view seen in the lab: a fast observer's forward field of view takes light from
  a much wider lab cone).
* Slices: `planes.max = 0`. The world computes images (directions) and surfaces (retarded shapes), not a field over
  space; the only candidate fields (the Doppler factor or the emission delay of light from a point to the observer)
  depend on the direction and the distance in closed form and would add nothing a slice could check. Every element is
  switched off on its own in "Scene layers".
* The region starts from the scene at t = 0 (bodies where they are, the observer) and grows (`box` messages) when a
  present position nears its edge: it never frames where bodies will be.

## The camera window

`../player/js/imagewin.js` (shared): the image the run computed (deflate-compressed RGB), its mode (a comparison mode is
marked), its time, angles on its axes, PNG export, and the values under the cursor from the run's per-pixel data: the
body (or the sky), D, the observed temperature D T and the rest temperature, how long before the observation the light
was emitted. The per-pixel data are quantised for the window (log₂ D in 32 octaves on 16 bits: 3.4·10⁻⁴ relative; the
delay on 16 bits of its maximum; T rounded to 1 K); the checks use the run's fp64 values.

"Exposure": "as for the scene at rest" (the default: a fixed scale from the median rest temperature of the scene, so the
searchlight shows as brighter and darker) or "per frame" (the 99th percentile of the luminance; colours visible, the
brightness levelled), with a correction in stops ("Exposure correction, stops"). The luminance is compressed as L/(1 + L) with the chromaticity kept.

## Checks

| id | quantity | reference | tolerance |
|---|---|---|---|
| `sky_T` | the sky's temperature in every pixel | T/(γ(1 − β cos θ′)) (closed form, no matrices) | 16 ε γ² (boost round-off; measured ≤ 2.7 ε γ²) |
| `stars` | the stars' apparent directions | cos θ′ = (cos θ + β)/(1 + β cos θ) | 16 ε γ² |
| `ret_N` | for every pixel that sees moving body N: its emission time and D | `lorentz.retarded_time` of the rest-frame point the tracer found; D = γ_obs(1 − u·n)/(γ_body(1 − v·n)) | 64 ε γ_obs² γ_body² (measured ≤ 4 ε γ²) |
| `penrose_N` | the outline of moving sphere N: its deviation from a circle and from `lorentz.sphere_outline` | Penrose: a circle | 64 ε γ² (1 + \|P\|/r), P the observation event in the sphere's frame (measured ~1e-13 rad) |
| `rest_equal` | (all velocities zero) the tracer's distances and bodies | plain ray casting (`raytrace.static_render`) | 4 ε (measured: identical) |
| `energy` | (the sky scene, whole-sky camera) (1/4π) ∫ (T′/T)⁴ dΩ′ over the pixels (exact solid angles) | γ²(1 + β²/3) | the quadrature's error estimated from the half resolution (Richardson) |

The `ret_N` and `penrose_N` checks show the worst value over the images of the world (Penrose: at the start, after a
live change and every 20th image). A check that fails is shown failed.

## Approximations and limits

* Special relativity in flat space-time; geometric optics (bodies much larger than the wavelength); rigid bodies in
  uniform motion; equilibrium (black-body) emission, isotropic in the body's frame; no reflection, no absorption between
  bodies, no shadows (all light is the bodies' own).
* Each pixel is one ray through its centre (no anti-aliasing): edges are pixel-stepped; the checks do not depend on it
  (they use exact directions).
* A star is a point: its light goes into one pixel, as bright as a surface of its temperature at rest there, times its
  flux factor (its colour D T and flux factor D² computed).
* The observer inside a body: refused for that image with a notice (the world goes on).
* The image is refreshed every 7th frame while the world runs, 0.35 s of play at 20 frames/s (and at once after a
  live change); counted in frames, not wall time, so a world continued from its record renders the same images:
  the record grows by about 3.6 (fly-by), 3.9 (train), 7.7 (sky) and 11.4 (city, many textured towers and stars) MB
  per minute of play at the default image size (measured by the tests, 2026-10-28).
* Colour is a display: the CIE fit errs by up to 0.022 (absolute) per nm; the screen compresses the luminance.

## Tests

`tests/test_v10_fast_observer.py`: every preset builds, renders and passes its checks; images use only light already
emitted (the delays are non-negative, the retarded shapes lie on the past light cone); the region grows only with
present positions; a live boost changes the image at once on a continuous worldline (position and proper time); the
comparison modes are labelled and the snapshot shows the contraction that what is seen does not; the observer inside a
body gets a notice, not an error; the edges of the schema (β = 0.99, the largest image, 2000 stars, oblique velocity and
view, field of view 150°); the lab bodies are contracted by 1/γ; the record's growth per minute. The engine's tests:
`../../lfphys/tests/test_raytrace.py` (the sky dipole, the energy density γ²(1 + β²/3), the stars' aberration, emission
times and D for spheres, boxes and rectangles at β up to 0.99 with a moving observer, Penrose's circle by two routes,
the snapshot's simultaneity and contraction, the observer inside, bodies behind the camera, grazing rays, the patterns,
GPU against CPU) and `test_colour.py` (illuminant A, the equal-energy white, the D65 white, the black-body table). The
page: headless Chromium (WebGL by SwiftShader), all presets, no page errors (2026-10-28).

Open items: `../../STATUS.md`.
