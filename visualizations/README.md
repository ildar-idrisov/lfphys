# Visualizations of the consequences of hypotheses

Русская версия: [README.ru.md](README.ru.md)

One server for all of the project's visualizations: it opens in a browser from any machine of the local network, the
visualizations are started from the browser with a button, and each one is an interactive player.

```
http://<the machine's address in the local network>:8479/
```

The rules for visualizations (physics, causality, modified laws, the one API, the interface's languages) are in
[`RULES.md`](RULES.md). How each visualization works and its physical model: `<id>/README.md` (e.g. `u32_double_slit/README.md`).
The physics of all visualizations lives in the shared engine [`../lfphys/`](../lfphys/README.md): its core holds only
verified physics; approximations, interpretations, models and alternatives are separate layers. A visualization is a
wrapper over the engine; which of its modules the current world uses, the player shows in the panel "Physics of this
world".

Each visualization belongs to one audience, named by its folder's prefix and numbered as in the plan: `uNN_` university, `rNN_` research, `sNN_` school (planned), `pNN_` laboratories. The worlds were renamed on 2026-11-13 (`v02_double_slit` is now `u32_double_slit`, `v11_double_slit_2d` is `r12_double_slit_2d`, …); the old ids still work in addresses and in old runs (the table: [`RULES.md`](RULES.md) §8).

The interface speaks English (the default) and Russian: the switch **EN | RU** in the top bar of every page changes
the language at once and is remembered in this browser; `?lang=ru` or `?lang=en` in the address overrides it in that
tab, also on the pages its links lead to. Records are language-neutral: a run recorded in one language is read in the
other (records made before the interface was translated, on 2026-11-12, show their labels in the language chosen and
their sentences with numbers as they were recorded, in Russian).

---

## Starting the server

From the root of the repository (the engine and the visualizations):

```bash
docker compose -f visualizations/docker/docker-compose.yml build        # once (and after a change of requirements.lock)
docker compose -f visualizations/docker/docker-compose.yml up -d viz    # start; from then on it runs by itself and restarts
```

The server gets only GPU 0 (the second card of the development machine computes wrongly); the heavy parts of the engine
move to it where that is faster. Where and with what precision to compute is set on the page **⚙ Devices**
(`/settings`): changes are saved at once and apply to new runs; a single run can be given its own device and precision
right on the start page (the line "For this run:" under "More: parameters, seed, device, precision" on the
demonstration's card). In every run the panel "About the run"
records what computed on what — separately for the drawing and for the checks (the checks are always fp64). If a world
chose an approximation itself (for example, a slice of the slit by the reduced 2-D model), the run is marked
"approximation" in the list and "APPROXIMATION: …" in the player's top bar. On a machine without an NVIDIA graphics
card: `docker compose -f visualizations/docker/docker-compose.yml --profile cpu up -d viz-cpu`.

The server listens on port **8479** on all of the machine's addresses. The address in the local network: `hostname -I`
(for example `192.168.1.10`). The port is changed with the variable `VIZ_PORT`. **There is no login:** anyone who
reaches the port can start worlds; on a shared network restrict access (for example, `VIZ_PORT=127.0.0.1:8479` in
`visualizations/docker/.env` — this machine only). To stop it: `docker compose -f
visualizations/docker/docker-compose.yml stop viz`.

The server serves the code of the player and of the visualizations from disk: changes to the JS show after reloading
the page; changes to a visualization's Python, in the next run (every run is a new process). Changes to the server
itself (`server/lfviz/`) take effect after
`docker compose -f visualizations/docker/docker-compose.yml restart viz`.

Checks (all tests, in Docker):

```bash
docker compose -f visualizations/docker/docker-compose.yml run --rm viz-test
docker run --rm -v "$PWD":/lf:ro -w /lf/visualizations node:24 \
    sh -c 'node --test player/js/tests/*.test.mjs'   # the player's JS: message decoding against the Python codec's bytes, the texts' rendering
```

---

## How to use it

**The start page** (`/`): learning materials in physics by audience. Four tiles, each with its count: **School**,
**University**, **Research** and **Laboratories**. A tile opens its page (`/#school`, `/#university`, `/#research`,
`/#labs`; the old address `/#playground` leads to the laboratories): the demonstrations by section in teaching order,
the section chips with their counts, and a search box ("Search…"); at school, "By:" section or grade. The school
demonstrations are being built along the curriculum: until they land, the school page shows the planned ones as planned,
with what is already there at another level on the same topic. The planned university and research items are listed
folded, by section, under the worlds. Under the tiles, "Continue:" shows the last runs that are open or paused, each with its state ("computing" or "paused").

On a demonstration's card: its picture, its title, what you will see, its courses (university) or its question, "Status:
hypothesis" and the prior art (research); "Scenario:" (the presets); **"▶ Compute live"**: the server starts a new run
and opens the player; **"▷ Recording m:ss"**: plays the scenario's saved recording at once, with nothing computed. It
is enabled when this server has the recording, or when the public site is published and has it from the same version of
the world; otherwise it is greyed, with the tooltip "No recording yet: record it locally (site/record.py) or compute live"
(a scenario that has no recording at all: "No recording for this scenario: compute it live"; see "Recordings and the
public site" below). "More: parameters, seed, device, precision" (folded on a university card, open on a research card)
holds "Parameters…" (the world's laws and parameters by hand), the seed and the line "For this run:" with the device and
the precision. "Same topic:" links the same topic at other levels. If a world cannot be made with the chosen parameters,
the card says why under its buttons.

**My runs** (`/runs`, "My runs" in the top bar): the runs on this server: computing, paused, suspended; "☆" keeps a run
for good, "✕" deletes it (a run not open in any tab; a running one is suspended first). There is no stop (2026-10-28): a run either records (computes further) or is paused. Without
viewers it pauses after a minute and after half an hour frees its worker ("suspended"); open it and press ⏺ — the
world goes on from its saved state (2026-10-29): the worker saves the world's whole state when the run is suspended,
when it pauses and every two minutes of computation, and it goes on from the last save, as one record, without
recomputing. If there is no save, or the code that this world loaded (the files of the engine and of the visualization)
or the versions of Python and the libraries changed since, the world is recomputed along the record from its start
(the same result frame for frame; the exception is the "ghost" of u34, `STATUS.md` V32); which way it went on, a
message in the events says. While the world is being restored, the status line shows "the world is being restored —
the recording resumes by itself"; the set-up cannot be changed meanwhile. Going back through the history, the player
starts from the nearest key frame (as in a video: a snapshot of what has accumulated every 100 messages, at most 256
per world — beyond that sparser, evenly over the whole record), not from the start of the record. From the start of the
record it rebuilds the view where a key frame does not fit: u40 and u41 (the clouds), u37 after old detections have
passed the limit, r12 and r13 before their latest change of the set-up. If resuming failed (for example, the
visualization's code has changed incompatibly since), the run stays suspended with the reason ("resuming failed — ⏺
tries again"); the record is intact. Runs not touched for longer than the removal period (a view, a command) are
removed, except those marked ★; beyond the quota those untouched longest go first; a run open in a tab is not removed.
The removal period is the field above the list on the page "My runs" ("Remove runs without actions after … days", 3 by
default); it is saved on the server (`runs/settings.json`) and applies at once: if the new period would remove some
runs, the page first shows their list and removes them only after confirmation.

**The player** (`/run?id=…`):

| where | what is there |
|---|---|
| top | the title, the scene, the badge **"standard physics"** or **"MODIFIED PHYSICS: …"**, the switch of worlds ("World 2 (current): …", if the run has several), the indicator "the set-up is being rebuilt…" (and "resuming: the world is being restored…"), the state (computing / paused / suspended; live / history / end of the record), "☆", **EN \| RU**, the theme, the help |
| left | **Set-up — changes at once**: everything the experimenter may change during the experiment (source, particle, slits, screen, observer, elements). There is no "apply" button: a change takes effect as soon as you release the slider, choose an item of a list or press Enter in a number field. An impossible change is refused, and the field goes back to its former value. **Actions** — one-off events (a flash, a measurement) by a button; the observer's speed by a slider, also at once. **New world: …** — the laws and the initial conditions (they cannot change inside a running world): the new world starts in the same run, the earlier ones stay in the record |
| centre | the visualization's scene; above it, quick elements of the set-up (in the double-slit experiment: the observer, the detector's coupling, the distance to the screen, the width and the period of the slits) — they change at once, as in the panel on the left |
| right | **Checks: computed ↔ reference**: a quantity computed in this run next to the reference of accepted physics (✓/✗); the fresh groups on top, the earlier ones folded; the visualization's panels; **Events** (a click goes to that moment) |
| bottom | **⏺ record**: the world is computed further and frames are added to the history; again — pause. **⏮ / ⏭** — to the start / the end of the history, **◀ / ▶** — play the history backwards / forwards at the chosen speed. The slider at the end of the history shows the record live; in the middle, the history goes on growing while the chosen moment is shown. "\|▶" — a frame forward (at the end: a step of the computation), "⏭ event" — to the next event (past the last one: compute up to it). The speed is world seconds per wall second (for computing and for playback; the scale is logarithmic, labelled in time units — from fractions of a second to years, within the limits the world allows; if the computation cannot keep up, "actual: …" appears next to it in orange), "1:1" real time, the history scale of the current world |

Everything shown is as of the slider: the scene (trajectories, the screen, clouds), the slice windows, the checks, the
set-up, the events; when you go back, the view is rebuilt from the record up to that moment. The set-up, actions and
slices can be changed only at the end of the history.

Keys: Space — compute/pause, ← / → — play the history backwards/forwards, Home / End — to the start/to the end, N — to
the event, T — the theme, ? — the help.

**Words.** A *recording* ("RECORDING", "▷ Recording") is a saved file that plays without computing. A *run* is a live
computation on this server; while it computes, its state is "computing" (its tab says "… · computing"), and what ⏺ adds
to is the run's *record*. The two are never called by the same word (`RULES.md` §7, glossary).

If the world takes long to compute a change (the scene, the set-up, a new world), the top bar shows what exactly and for
how many seconds; "✕ cancel" returns the world to the moment before that change. If a world cannot be made with the
chosen parameters, the start page says why right under the card's button "▶ Compute live", and the field with the
unsuitable value is highlighted. In a laboratory, a palette button opens the object's parameters; the place can be typed or clicked in the
scene ("⌖ Point at a place in the scene"), then "Place". ⇤ and ⇥ at the top (keys [ and ]) hide the side columns. Each
worker has its own memory (`--worker-mem-gb`, by default 60 % of the server's memory, at most 8 GB): a world that
does not fit in it refuses with an explanation instead of taking the memory of the whole computer.

**3-D worlds** (now u38, r11, u39, r12, r13, u40, u41, u42, u43 and u44; the rule for all 3-D visualizations is
`RULES.md` §2.10). In the centre is the 3-D scene: the apparatus (for example, a screen with slits), the incident wave,
the computed fields (the light behind the aperture, the energy flow) and the target. On the right are the slice windows
(up to three), each with its own colour.

| to do | how |
|---|---|
| rotate / pan / zoom the view | left mouse button — rotate; right (or Shift + left) — pan; wheel — zoom to the point under the cursor; double click — make the point under the cursor the centre of rotation; F — show everything drawn, Shift+F — the whole region; the buttons "Iso", "Side", "Top", "From the source", "From the target" (in plane worlds "Iso", "Top"/"Front", "Edge"). Until the view is moved by hand, it follows the size of the window and the growth of the region; after that it stays where it was put |
| add a slice | "＋ Slice": the plane is placed in the middle of the region, perpendicular to those already there (y = c, then x = c, then z = c); its window appears at once |
| select a slice | a click on the plane in 3-D or on its window; pointing at a window highlights its plane |
| move / tilt a slice by hand | on the selected slice: the arrow moves it along its normal, two rings tilt it (W — move, E — tilt) |
| set a slice by numbers | the panel "Slice: position and tilt": the centre x, y, z; the normal's tilt θ from the z axis and the azimuth φ; the buttons y = c, x = c, z = c, "to the centre", "remove", "default" (one slice y = 0) |
| remove the selected slice | the Delete key (Backspace does not delete a slice) or "remove" in the slice's panel |
| auto-shift | the tick "auto-shift along the normal" in the same panel (off by default): the slice moves along its normal while the world's time runs (▶); while it moves the slice is coarse, without verification, and full when the auto-shift is off; without the tick the slice stays where it was put |
| switch off a part of the scene | the panel "Scene layers": each part on its own (the screen, the wave, the target, the light, the energy flow, each slice); the light has a density (the optical depth of the densest line of sight along an axis of the region, the same in every world) and a threshold; the colour scale is in the lower right corner of the 3-D view |
| the slice window | intensity / amplitude / logarithm / phase; the coordinates and the value under the cursor; CSV — the data; the line under the window — how the slice was computed and its check against the exact field |
| a snapshot | 📷 — a PNG of the 3-D view |
| the observer's camera (u39) | a window to the right of the 3-D view: the image computed by the run; pointing shows the Doppler factor D, the temperature, when the light was emitted; PNG — a snapshot at the computed resolution |
| the experiment's plane (r12, r13) | a window to the right of the 3-D view: the wave \|ψ\|² (intensity, amplitude, logarithm, phase) with the Bohm trajectories over it; going back, it shows the wave of that moment; in p02 in a plane the wave's window is the main view across the whole centre, the 3-D view comes by the button "Show the 3-D view alongside" (the panel "View") |
| the third dimension (r12, r13) | along the slits (the y axis) the apparatus does not change, so the wave is the exact product of the wave on the plane and a free Gaussian packet along y (the width σy is the world parameter "Packet: width along y σy, λ"). In 3-D: the layer "Wave \|ψ\|² in the volume: ψ(x, z, t)·η(y, t)" (density and threshold by the layer's sliders), the Bohm particles and trajectories in all three coordinates, on the screen the pattern P(x, y). The plane y = 0 is a separate layer (off) and the window on the right |
| an observer at a slit (r12) | in the new world's form, "Path mark in slit B": "the particle's spin: …" (electron, neutron: a field in the slit turns the spin) or "an observer: a path detector at slit B (…)" (Englert's two-level detector, any particle); then on the left "Mark in slit B: turn θ, °" — it changes on the go: 0 — the path is not marked, 180° — the slit's main transverse mode is marked fully (the fringes almost fade; not to zero — part of the wave is turned differently, probably the higher modes of the narrow slit and the spread of speeds). In 3-D the observer is an orange block in slit B, the denser the stronger the mark; the presets "Path mark: …" and "An observer at slit B: …" |
| the cloud and its phases (u40, u41) | the cloud \|ψ\|² is the layer "Cloud \|ψ\|² (probability density)", with a density and a threshold; the arrows are the probability current (real orbitals have none). In a superposition the cloud oscillates with the Bohr period: 24 phases of the period are revealed when the world's time reaches them (the panel "State": which phase is drawn and how many are revealed); going back shows the cloud of that moment; the state changes on the go (on the left, "Set-up — changes at once"): a new n, l, m, a superposition or a cloud grid — in the same world, from the moment of the change (an ideal preparation: the former state is discarded), the slices stay; the superposition's period is counted from the moment of preparation; another atom (quark pair) is a new world |
| the atom's and the quarkonium's panels (u40, u41) | "State" — the energy, ⟨r⟩ by quadrature (and by the formula for hydrogen), the weight and phase of each state of a superposition; "Radial distribution r²\|R(r)\|²" with ⟨r⟩ as a dash; "Energy levels" — the world's levels (its states highlighted, ħω for a superposition); for quarkonium the PDG measurements dotted |
| arrival time (r13) | on the right: "Distribution of the arrival time" — the density of each rule against t/t₀ (a click on a rule hides it; what is above the frame is cut and marked ▲), "Place and time of arrival" — the current into the plane j_z(x, t) with the hits of the Bohm particles, "Totals by rule" — the probability of arrival within the window, the mean time and the spread for each rule |

A slice is computed exactly by the engine for its plane when the plane is released; while the plane is dragged, the
window shows a preview (marked). The window's axes are the real coordinates x, y, z. The slices are kept when you
change the world's parameters (a new world in the same run). A world from the record (the switch of worlds) is for viewing
only: its slices do not change; in the past of the experiment (the slider not at the end), neither: "＋ Slice" is
inactive and the slice's panel says why.

The records are kept in `visualizations/runs/` (the removal period after the last action is 3 days by default, set on
the page "My runs", or until the quota of 5 GB; "☆" protects a run).
At most three runs compute at once.

---

## Recordings and the public site

**Watching a recording.** A recording is a run of one scenario made once by the recorder and saved: it plays at once,
back and forth, with nothing computed. Open it with "▷ Recording m:ss" on a card, or by its address
`/run?rec=<world>/<recording>` (an old id works too: `/run?rec=v02_double_slit/young`). The player on a recording has
the badge "RECORDING · date · code …" in its top bar (its tooltip names the scenario; when the recording was made by
other code than this server runs, it names both codes); "⏺", "☆" and "⚙ Devices" are absent. ▶ (or Space) plays the
recording; the slider, ◀ ▶ and ⏮ ⏭ go through it as through a run's history. The set-up, the actions and the laws are
shown "as recorded" and cannot be changed (the reason: "a recording: this needs a live run"); a 3-D world shows the
slices that were recorded and adds none. The checks, the events, "Physics of this world" and the instruments' plots work
as in a run; the instruments' CSV is made in the browser from the frames the recording kept (its time column says "from
the recording: every frame" or "one frame in k of the run"); parameter sweeps need a live run. "About the recording"
holds its passport (the code, the recorder, the date, the frames) and "Download the recording (.lfrec.gz)". A view's
own speed buttons (the double slit's "▷ flight" and "▷▷ build-up", the same in u35 and u37) set the player's speed; any
other button that would change the world says "a recording: this needs a live run". The help (?) describes the
recording, and the tab's title ends with "· recording". On the server, "▶ Compute this scenario live" starts a run of
the same scenario, which can then be changed; on the public site the note on the left links to how to run lfphys
locally. On a phone (a window narrower than 1000 px) the player is one column: the picture first, the set-up and the
checks under it, the transport at the bottom of the screen. An address with an unknown world or recording says "No
such recording", with a link to the start page.

**Where the server finds recordings.** In `visualizations/recordings/` (not in git; the variable `LFVIZ_RECORDINGS`
names another folder), one folder per world with its `index.json`. When a world has no local recording, the player plays
the public site's one, but only when the site is published (`site/site.json`) and its recording was made from the same
version of the world. Otherwise it says why: "No recording yet: record it locally (site/record.py) or compute live" (the
site is not published or has no such recording), "The public site could not be reached: …", or, for another version,
"No recording for this version: record it locally or compute live".

**Recording locally** (`site/record.py`, in Docker, on the CPU):

```bash
docker run --rm --memory=12g -e LFPHYS_NO_GPU=1 --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf/visualizations \
    lfphys-viz python3 site/record.py --stale            # or: --world u32_double_slit (repeatable), --all
```

`--stale` records the worlds whose recordings are missing or were made by other code: a recording's key covers its
scenario, the recorder's version and the code a run executes (the world's folder, `server/lfviz/` without the server's
own `app.py` and `runs.py`, and the engine). Most worlds take seconds to two minutes; the exact two-slit world r12 about
20 minutes. Each file must stay within the site's budget (3 MB aimed at, 10 MB at most; a world 12 MB, at most 25 MB); a
recording over the limit fails with the advice to shorten it in the world's `VIZ["recordings"]`. The pictures of the
cards and of the README (`docs/images/<id>.jpg`) are taken from the recordings by `site/posters.mjs`.

**Building the public site locally** (`site/build.py`, then `site/check.py`, which fails on anything missing, stale or
over budget):

```bash
python3 site/build.py --recordings recordings --out /tmp/site --base /lfphys/
python3 site/check.py /tmp/site --base /lfphys/
cd /tmp && mkdir -p srv && ln -s /tmp/site srv/lfphys && cd srv && python3 -m http.server 8000   # http://127.0.0.1:8000/lfphys/
```

The site is the same player in its static mode: the start page and the recordings, with nothing computed; the
laboratories are greyed with "Works only with a running server"; there is no "My runs" and no "⚙ Devices". Details:
[`site/README.md`](site/README.md) (in English).

**Publication.** The site is published on GitHub Pages (`https://ildar-idrisov.github.io/lfphys/`) by the workflow
`.github/workflows/pages.yml` (active since 2026-11-14). A push to `main` checks, records and builds; the site is
deployed only when the author starts the workflow by hand (Actions → pages → Run workflow) with `deploy: true`.

---

## Visualizations

| folder | what it shows | what for |
|---|---|---|
| [`u31_light_travel/`](u31_light_travel/README.md) | light from the Sun to the Earth (the front flies for 8 min 17 s), gravitational deflection and delay at a black hole and a star, the speed of light measured by observers at rest and moving along and against the light, clock synchronisation, the relativity of simultaneity (the Andromeda paradox), Doppler and gravitational redshift | the light cone, the absoluteness of the speed of light, the Andromeda paradox; the laws can be changed: an ether, ballistic light, Newtonian corpuscles, another c |
| [`u32_double_slit/`](u32_double_slit/README.md) | particles one by one through slits (a photon with its energy, frequency, polarisation; an electron, a neutron, an atom, C60, a particle of your own), a which-path observer (a qubit detector, photon scattering), marks by polarisation and spin, the quantum eraser, the Aharonov–Bohm effect, partial coherence, Bohm's flow lines; the screen with slits is Kirchhoff's scalar model (the default) or a perfect conductor of a given thickness (slits up to 20.7 λ): vector diffraction for both polarisations (TE — E along the slits, TM — across), the photons' hits by the energy flow of the vector solution, next to it the scalar curve, the difference (if it exceeds the method's error estimate), the power balance and the method's error estimate | how the particle behaves and why interference appears and disappears; the laws can be changed: the Born-rule exponent, GRW collapse, a forced choice of slit |
| [`u33_quantum_1d/`](u33_quantum_1d/README.md) | an electron as a wave packet at a barrier, a double barrier, a step, a well or in a harmonic trap: tunnelling, resonance, levels; detectors at the edges absorb the wave | transmission by the exact solution of the Schrödinger equation against the stationary reference; one computation read three ways: a click and a collapse, Bohm trajectories, Everett's branches |
| [`u34_orbits/`](u34_orbits/README.md) | a body's orbit about a central mass: the periapsis advance (Mercury 43″ per century, a neutron star), the instability inside the ISCO, the fall through the horizon, the body's clock against a distant observer's; Kerr | exact GR against Newton and the weak field (PPN) on one and the same orbit |
| [`u35_optics_bench/`](u35_optics_bench/README.md) | single photons at a boundary between media and at coatings: Brewster's angle, total and frustrated total reflection, an anti-reflection layer, a Bragg mirror, Fabry–Pérot, a metal film, the plasmon dip | a wave computation decides each photon's fate; the photon counts converge to R, T, A; curves against the angle and the wavelength |
| [`u36_qcd/`](u36_qcd/README.md) | the running of the strong coupling α_s from 1 GeV to 10 TeV (1–4 loops, quark thresholds, the Landau pole), quarkonium in the Cornell potential | asymptotic freedom and the growth of the coupling at low energies; the quarkonium model as a model (it predicts splittings, not masses) |
| [`u37_bell_test/`](u37_bell_test/README.md) | entangled pairs of photons or spins, two stations choosing their settings, coincidences, correlations E and the CHSH parameter S | quantum mechanics (S up to 2√2) against local hidden variables (\|S\| ≤ 2) on the same events |
| [`u38_wave_3d/`](u38_wave_3d/README.md) | a wave behind an aperture in a full 3-D scene: the screen, the incident wave, the light, the energy flow, the target (each part can be switched off); up to three slices at any angle with their own windows — moved and turned by the mouse or by numbers, they stay in place, auto-shift if wanted; the accuracy of every world and every slice is measured | how the engine's 3-D modelling works and the choice of device: CPU or GPU |
| [`r11_thomas_3d/`](r11_thomas_3d/README.md) | Thomas–Wigner precession in 3-D: a craft performs a manoeuvre (burns and turns of its thrust in its own frame); back at rest, its gyroscopes are turned — a rotation in SO(3) and the spinor's sign in SU(2); the fuel and the isoperimetric bound; planar loops (Thomas, a circle, a triangle, a polygon — checked against the area) and non-planar ones (a crown, a helix, a ball's seam); the scene is the velocity ball with its field of rotations and slices, or ordinary space with the trajectory | how a gyroscope turns without any torque, and how much rotation a unit of fuel gives |
| [`u39_fast_observer/`](u39_fast_observer/README.md) | what an observer or its camera sees at speeds close to c: a cube and a ball fly past (Terrell rotation, the ball stays a circle), a flight down a street between towers (aberration, blue and brightness ahead), a black-body sky and stars (the dipole), a train passing posts; the image is computed by ray tracing with the light's travel time, the colour is a black body at D·T; in 3-D, the laboratory now (the bodies Lorentz-contracted) and the places the visible light came from; the observer's speed changes on the go | why the Lorentz contraction is not seen and a rotation is; how the world looks to a fast observer |
| [`r12_double_slit_2d/`](r12_double_slit_2d/README.md) | a real double-slit experiment (long slits, shown in 3-D): the packet of a particle (an electron, a neutron, an atom, C₆₀) passes two slits in a wall of finite thickness and reaches the screen; the Schrödinger equation is solved on the whole plane — reflection by the plate, the wave in the slits, diffraction to any angle; the pattern accumulates as the wave arrives; an ensemble of particles follows Bohm trajectories, each labelled by its slit; on the go — change the plate (the width of the slits, the distance between them, the thickness, the height of the wall), close a slit, turn the spin in slit B or the state of an observer — a path detector at slit B (a path mark), switch on an Aharonov–Bohm flux | where the paraxial theory fails (narrow slits, large angles), how a path mark kills the interference, and how the Bohm trajectories go |
| [`r13_arrival_times_2d/`](r13_arrival_times_2d/README.md) | when a particle arrives at a detector: a packet flies to a plane freely or through two slits (in 3-D: the wave as a volume, the particles in all three coordinates); a run solves the Schrödinger equation and, from the record on the plane and the initial state, computes the distribution of the arrival time by every rule — the quantum flux, the first arrivals of Bohm particles, Aharonov–Bohm–Kijowski, semiclassical, the absorbing boundary, Włodarz, Marchewka–Schuss, a soft detector (a second run with an absorbing potential); a train of packets, backflow, the joint distribution of place and time behind two slits; on the go — the plate, the strength λ₀ of the exponential rules and the height W₀ of the soft detector | quantum mechanics does not fix the arrival time uniquely: where the rules agree (far from the source) and where they diverge (near the source, for a train of packets, under backflow) |
| [`u40_hydrogen_3d/`](u40_hydrogen_3d/README.md) | the hydrogen atom in 3-D (also deuterium, the ion He⁺, positronium): the cloud \|ψ\|² of the exact solution for any n ≤ 12, l, m; real orbitals (p_x, d_xy, d_z², …) are standing waves without current, complex ones with m ≠ 0 are doughnuts with a ring current; a superposition of two levels (1s + 2p_z) sways at the Bohr frequency; slices at any angle with \|ψ\|² and the phase, checked against an independent computation; the radial distribution and the levels; the state changes on the go, in the same world | what orbitals and their nodes look like, how real states differ from complex ones, how the cloud moves in a superposition |
| [`u41_quarkonium_3d/`](u41_quarkonium_3d/README.md) | quarkonium cc̄ and bb̄ in the Cornell model (a fitted model, flagged): the clouds 1S, 2S, 3S, 1P, 1D…, the current, the superposition 1S + 1P; the radial functions are a numerical solution with measured convergence; the model's splittings against the PDG measurements | what the states of a heavy quark pair look like and how charmonium differs from bottomonium; what the model predicts (splittings) and what it does not (absolute masses) |
| [`u42_kerr_shadow/`](u42_kerr_shadow/README.md) | the shadow of a spinning black hole with a disk of gas: every pixel of the screen is a ray traced back in closed form; the shadow, the lensing ring, the photon ring; the shadow's edge against Bardeen's formula, the rings' demagnification against e^(−γ), the size against EHT (M87*, Sgr A*); "what if": the Johannsen metric | where the shadow and the rings on the EHT images come from, how they depend on the spin and the inclination, and how the shadow's size tests whether the hole is Kerr |
| [`u43_optical_vortices/`](u43_optical_vortices/README.md) | an optical vortex in 3-D: a Laguerre–Gauss beam LG_pl (or a Gaussian beam behind a spiral phase plate, or a "fork" hologram, whose order m carries the charge m·l) — helical surfaces of equal phase (they rotate: the optical phase is shown slowed down), a ring of intensity, twisted lines of the energy flow, slices with the phase on a colour wheel; the orbital and spin angular momentum per photon measured from the field — the exact vector solution of Maxwell's equations or the paraxial model (under tight focusing the longitudinal field shows, and that the split of the angular momentum into spin and orbit depends on its definition: the canonical one per unit length and the one by Barnett's flux go different ways, while the total l + σ is one); a beam whose waist is narrower than the wavelength is flagged or not built (the exact beam has only propagating waves); a rotating rough disc or a Dove prism shifts the frequency — a detector accumulates counts, the beats 2\|l\|f are measured from the spectrum; the rotation frequency changes on the go | what the orbital angular momentum of light is, where the paraxial picture fails, how rotation gives a frequency shift lΩ |
| [`u44_mie_scattering/`](u44_mie_scattering/README.md) | a water drop in light: the exact Mie series — the phase function and polarisation, the Debye series (reflection, transmission, one and two internal reflections) against Descartes' rays and Airy's theory, the scattered light as a surface around the drop, the near field of a small drop (the focus behind the drop) in the volume and in slices; a cloud of drops of different sizes in sunlight — the colour of the sky against the scattering angle is summed wavelength by wavelength: the primary and secondary rainbows, Alexander's band, the supernumerary bows (seen for equal drops, washed out by a spread), the fogbow, the glory at the antisolar point; the checks: the values of the coefficients by a second route (the Debye series) and Wiscombe's published values; the identities of the series' form (the optical theorem in series form, energy, the Mueller matrix) are labelled as identities; if the Debye series diverges (a weakly absorbing drop with m ≈ 1), the run says so | where the rainbow and its supernumerary bows come from, where ray optics and Airy's theory go wrong, why small drops give a white bow, where the glory comes from |

---

## Laboratories (B6, 2026-11-03)

The start page's tile **"Laboratories"** (`/#labs`) opens one laboratory per branch of physics, `pNN_*`, where the
scene is built by hand and everything is computed in real time (the owner's request of 2026-10-28); the demonstrations
`sNN_`/`uNN_`/`rNN_*` above are the prepared experiments. The laboratories need a running server: there is nothing to
replay, so the public site shows them greyed, with "Works only with a running server". On a section's card: a scenario (a ready scene),
"▶ Begin", "Laws…" (the world's laws: which solver, space, grid — changing them starts a new
world) and "📂 From a scene file…".

On the left of a laboratory's player:

* **Palette: add to the scene** — add an object at the world's current moment: before it is placed, a form of its
  parameters opens, and the point can be given by a click in the scene; the world moves the object to a free spot or
  explains why it cannot be placed, and unavailable buttons show the reason;
* **Scene objects** — select, ⧉ copy, ✕ delete (also at the current moment);
* **Drag and throw** — an object is selected by a click in the scene or in a slice window (a ring with its name; the
  inspector shows it) and dragged with the mouse: the drag moves a "ghost" (in 3-D, in the plane through the object
  across the view; in a plane world and in a window, in their plane; the piston and the walls along their axis), and
  the change is applied on release, at the world's current moment. Shift + drag throws: the speed is how the hand moved
  over the last 0.1 s at the current playback speed, times the throw scale (the field "Throw (Shift): scale ×" in
  "Scene objects"); the speed shows at the cursor. The automatic throw scale is fitted to the world itself: a brisk
  flick (the view's width in a second) throws the object across the whole region of the world in about 2 seconds at
  the current playback speed, but no faster than half of the largest speed the world has declared. If a throw is
  clamped by that speed or the world did not accept it, the player says so: "reduce the throw scale". If the world
  cannot place the object so, it explains why and the ghost goes back; in the past of the record and while the world
  is computing nothing can be moved. Delete removes the selected object, also one selected in a plane world's window;
  Esc cancels the drag;
* **A new world that carries the scene over** — the form "New world: …" shows every law of the new world, including
  those that change on the go (the grid, the window, the edges — at their current values). With the tick "carry the
  scene over" (on) the objects pass into the new world under the same numbers, and the time goes on. The message after
  the carry says object by object: carried with its state; by its parameters (it has no state of its own); its state
  not carried and started afresh from its parameters (with the reason); what was changed in the carry; what the new
  world did not accept — and what happened to the state of the world itself (for example, the flow carried over or
  started afresh from rest);
* **Inspector** — the parameters of the selected object, changed at once; under them "now:" — its computed state;
* **Scene: file** — save the scene to a file and start a new world from a file;
* **Record: window** — the record keeps the last 10 minutes of computation (pauses and suspensions do not count) or
  1 GB. Saw an effect — "● Keep the record": the window and everything after it are kept. A suspended world can go on
  from a checkpoint inside the window (one per minute of computation and at a pause); if the world's start has already
  left the window (or the kept record has a hole — recording was switched on and off), there is nothing to recompute
  the world from its start with — the player says so.

On the right: the running checks of the conservation laws, **Probes** (detectors, clocks, field probes) and **Scene
changes** (a click goes to that moment). Messages and refusals appear at the lower right in a stack, the newest on top;
each stays while the cursor is on it and closes on a click.

**Instruments and the parameter sweep.** If the world reports measurable quantities, the panel "Instruments" appears on
the right: the quantities by group and the value of each at the slider. Tick a quantity and its plot over the record
appears (each its own): bright up to the slider, pale after it (the record's future), a line at the slider; point at it
to read the value. Folded groups and the chosen quantities are remembered for this run. "⤓ CSV" gives the ticked
quantities from the record, every frame, full precision ("only up to the slider" cuts it); the first line holds the
time unit and the labels with their units.

"Parameter sweep": the same experiment from the world's current moment is repeated for each value of a law (from "Laws
of the world — change at once") or of an object's parameter, and for each a quantity is measured — at the end, the mean
of the last N, the maximum or the minimum. Under "What to change" it says what is set now; for an object's position,
also where it is now. Each value is applied afresh, an equal one too: a position and a velocity as a drag and a throw
at the moment of the sweep. The values are separated by ";" or a space (with a decimal point or a comma), or "from …
to …". The computing time is in the world's scale units (for example fs), by default five seconds of the world at the
chosen speed; next to "Readings" it shows how much world time lies between the readings. First "Estimate" (how much
computation it will take; the limit is 10 min), then "▶ Start the sweep"; after a start the estimate has to be made
again.

A sweep computes in a separate process and does not change the running world: the sweep has its own, smaller share of
memory, and if memory runs short the system stops the sweep first, not the world. A sweep stops by itself if it would
exceed the limit. "✕ cancel" stops it, what was computed stays; "remove" deletes a finished sweep with its
results. The result is a table, a plot and "⤓ CSV of the table" (the first lines of the CSV say from which moment, how
many readings and how often); a world's refusal is in the table with its reason, and if not a single value was
measured, the sweep is marked "not computed". The same sweep from the same state gives the same numbers; for a
suspended run, from its last saved state (said above the result).

| folder | section | what can be built |
|---|---|---|
| [`p01_gravity/`](p01_gravity/README.md) | Space and gravity | stars, planets, Newtonian "black holes", test bodies (Newton: N bodies, mergers); a binary in GR radiating gravitational waves, with a detector; bodies, light rays and observers with clocks at a Kerr–Newman black hole (spin, charge); the black hole's mass (for a Kerr–Newman hole it is an object of the scene) and the binary's total mass change on the go as a change of scale (the bodies in units of M or m at their former places, seconds and metres rescaled); the hole's spin and charge on the go are the engine's "what if" model (lfphys.theories.alternatives.kn_change_whatif: the place by Boyer–Lindquist coordinates, the proper time and the momentum by ZAMO; there is no limit of the speed below c; the rule depends on the coordinates — said in the event with the numbers); bodies can be dragged, a thrown body gets the throw's speed; a body thrown at a hole is no faster than half the speed of light in the picture's coordinates (a brisk flick — a quarter); instruments: the energy and the angular momentum and their drift, distances, speeds, orbital elements, the radial period, the binary's phase, h₊ and h× at the detector; a new world of other laws carries over what makes sense (hole ↔ hole, binary → two bodies); in a new world with "carry the scene over" the bodies at a hole go on with their state (another mass — a change of scale; another spin or charge — from the former place with the momentum by ZAMO; under the new horizon — afresh from their parameters, said) |
| [`p02_quantum/`](p02_quantum/README.md) | Quantum particles | wave packets of an electron, a neutron, atoms (with spin) in a plane or in a volume; barriers, wells, walls with slits, a trap, a magnetic field, an Aharonov–Bohm tube, detectors, a path mark, an environment (decoherence), flux planes; "Measure the position"; Bohm particles; the grid and the window change on the go (the wave is resampled exactly; the window will not move the absorbing edges onto the wave); a packet can be dragged — the same wave at a new place (with a flux tube, if its path relative to the wave crosses the wave, and at the edge of the field there is no such wave — the move is not accepted, with an explanation) — and thrown (k₀ = m v/ħ; the world clamps a throw that is too fast to the largest speed the grid carries and says so); "Prepare the packet anew" — from the parameters or where the wave is now; "Coarsen the grid with edges to match"; a new world of the same space ("▶ Start a new world") carries the wave itself; instruments: probability, energy, ⟨x⟩, ⟨p⟩, flux, absorbed |
| [`p03_molecules/`](p03_molecules/README.md) | Particles and molecules | a gas, a crystal, atoms and molecules (bonds and angles) with the Lennard-Jones model or repulsion only; walls (mirror, soft, thermal — baths), a piston, thermostats, a field, thermometers; the Maxwell distribution, g(r), temperature, pressure, heat and work. The world does not restart: on the go change the dynamics (continuous forces ↔ hard disks/spheres — the same atoms; to hard ones if no pair is closer than σ), the interaction model, the cut-off radius, the time step and the box's size (affinely — the matter is compressed with the box over a given time, 50 ps by default: the slower, the closer to adiabatic, the work counted in the first law; 0 — at once, irreversibly; or by shifting a wall through empty space). A gas, a crystal, molecules and an atom are dragged whole and thrown (a throw (Shift) up to 500 m/s), a thermometer and the piston are dragged. Instruments: temperature, pressure, energy, density, heat and work, momentum, order, displacement, thermometers, the piston, the temperatures of the molecules' modes. A new world (plane ↔ volume, boundaries) carries the scene; in the same space, with the atoms, their positions and velocities |
| [`p04_fluids/`](p04_fluids/README.md) | Fluids | flow in a plane (the lattice Boltzmann method): cylinders, rectangles, NACA wing profiles, inlets and outlets, moving walls, periodicity, dye, velocity probes; drag and lift, the balances of mass and momentum. On the go change the viscosity, the density, the collision operator and the dye; water and air — with the speeds the grid resolves, or in their own scenarios (millimetre and centimetre channels). Also on the go: the grid (nodes along x), the size of the domain (on the side chosen in "The domain grows or shrinks"; the new part at rest or with the incoming flow) and the largest expected speed (the time step): the flow is moved to the new grid, not started afresh (the event names the mass and the momentum before and after); bodies, dye and probes are dragged; instruments: C_x and C_y (per step and averaged over a sound period), forces, velocity and pressure at the probes, the flow rates through the sides, the balances' residuals, Re and Ma; on a change of the grid, the domain or the largest speed the event names the domain's new height (if the number of nodes along y became a different whole number) and splits the change of mass: the scheme's compressibility (the same pressure, a different sound speed of the scheme), the new part of the domain, the interpolation; the balances of a transfer close by construction, the accuracy of the transfer shows in the checks "Benchmarks" (a channel with a body force and periodic ends); a new world with "carry the scene over" continues the flow (on another grid by the engine's transfer), what was started afresh is said |

The other sections (optics and waves, electricity and magnetism, relativity) are batch B9 of the plan
(`../lfphys/PLAN.md`); the start page shows them as planned.

If GPU 0 has warmed to 82 °C, new computations go to the CPU by themselves until it cools to 70 °C (the reason for the
choice of device: "GPU cooling down: …"); in the quantum section the device shows in the check "Computation: seconds
per step (…)".

---

## A new visualization — on request

Describe what you want to see and which hypothesis or effect is tested. The agent creates a folder
`uNN_<name>/` (or `sNN_`, `rNN_`: the audience and the plan's id) by the contract of [`RULES.md`](RULES.md) §1 and §4: the physics comes from the engine `../lfphys/`
(what is missing is added to the engine); the visualization's `engine/` holds only the apparatus, the drawing is in
`web/view.js`, then the checks and tests, a README with the model in every language of
[`../LANGUAGES.md`](../LANGUAGES.md), the translations of its texts (`locales/`), and an independent review of the
physics in `../reviews/`; a demonstration also declares its recordings (`VIZ["recordings"]`), which are recorded with
`site/record.py`, and gets its picture from `site/posters.mjs`. The server, the player, the start page and the catalogue
of the root README (`site/readme.py`) pick the folder up by themselves.

---

## If something is wrong

| symptom | cause |
|---|---|
| the page does not open from the laptop | the server is not up (`docker ps` → `lf-viz`) or the port is closed by a firewall |
| "all 3 workers are busy with open runs: …" | three runs are open in a browser: close the tab of one (it will pause and free its worker; it goes on with ⏺). Runs without viewers free their workers by themselves |
| "this record was made before the version that can continue runs: …" | the run was created before 2026-10-28: it can be watched but not continued — start a new world or a new run |
| a run is at once "failure" | the laws are incompatible (for example, GR with an ether) — the reason is in "Events" and in `runs/<id>/worker.log` |
| "resuming failed — ⏺ tries again" | the world could not be recomputed along the record (the reason is in the status line's tooltip and in "Events"); the record is intact, ⏺ tries again once the cause is removed |
| "the world is still being restored: the change was not accepted — …" | a change came while the world was being restored along the record (for example, from another tab); repeat it when the record resumes |
| a run on the page "My runs" has no "✕" | it is open in a tab (👁 in the list): close it |
| the world runs slower than the chosen speed | the computation cannot keep up: next to the speed, "actual: …" in orange (before 2026-10-28 the player did not show this, though this guide said otherwise); lower the speed or the source's rate |
| a change to the server does not show (including an "ImportError" of a new visualization: the server holds the engine loaded at its start) | `docker compose -f visualizations/docker/docker-compose.yml restart viz` — no runs are lost: the running ones are suspended and go on with ⏺ |

---

## Licence, citation, contact

The source code is open for reading (source-available), but it is not open source: the program may be used for
noncommercial research, study and teaching; any commercial use only under a separate written agreement. In the player
all of this and the texts of the licences are on the page "Licence" (`/legal`).

* **Code** (the server, the player, the visualizations, and also the texts and images the program shows while it runs —
  its interface and help): lfphys Research Licence 1.0 (`LICENSE.md`). **Commercial use by anyone — including a
  university or an institute working for a company — only under an agreement** (`COMMERCIAL.md`).
* **The author's documentation and figures** (the descriptions and guides in files, their figures): CC BY-NC-SA 4.0
  (`LICENSE-DOCS.txt`); figures and short quotations may be published in scholarly publications, including those of
  commercial publishers and under CC BY, with the author and the version named (`PUBLICATIONS.md`). Snapshots of your
  own runs and short excerpts of the code may be published anywhere with the credit "Ildar Idrisov, lfphys
  &lt;version&gt;" (`LICENSE.md` §6.3).
* **Your results** are yours; if the program computed, modelled, drew or checked something a publication reports,
  **citing it with its version is required** (`LICENSE.md` §5, `CITATION.cff`; the player shows the version and the
  build code on the page "Licence"). Selling data sets made mainly of its results only under an agreement.
* **Notices**: `NOTICE`, the texts of the licences and the authorship lines in the files go with every copy.
  **Contributing**: `CONTRIBUTING.md`, the contributor agreement `CLA.md`.
* **No warranty.** This is a research tool: the models, the numerical methods and the results may contain errors; the
  tests check the stated cases, not every problem. Before using a result, check the input data, the model's
  applicability, the convergence and the result itself (`LICENSE.md` §8).

Copyright (c) 2026 Ildar Idrisov. **For all questions and for commercial use: idrisov.sci@gmail.com**
