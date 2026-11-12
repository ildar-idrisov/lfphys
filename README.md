# lfphys

**English** | [Русский](README.ru.md)

[![Licence: lfphys Research Licence 1.0, noncommercial](https://img.shields.io/badge/licence-lfphys%20Research%201.0%20%C2%B7%20noncommercial-informational)](LICENSE.md)

lfphys is a physics engine and a set of interactive visualizations built on it. The engine, a Python package, keeps
three kinds of physics apart: a **core** of established physics, where every function is tested against a closed form
or an independent second method; the **approximations, interpretations and phenomenological models** that physicists
use widely, each stating where it departs from the core; and **declared alternatives** for "what if" worlds. The
visualizations run in a browser and compute what you see: an interference pattern, an orbit or a rainbow appears
because the run computed it, not because it was drawn, and every run shows its own checks, computed values next to
independent references. There are 17 prepared **demonstrations**, from Young's experiment and the rainbow to the shadow
of a spinning black hole, and 4 **playgrounds**, where you build a scene by hand and the world computes it live.

> The player's interface, its help and the preset names are in Russian for now. Each visualization's README (linked
> in the tables below) is in English, and the presets are given here in translation.

<a href="docs/images/v15-m87.jpg"><img src="docs/images/v15-m87.jpg" width="49%" alt="v15: the shadow of a Kerr black hole computed ray by ray"></a>
<a href="docs/images/v17-rainbow.jpg"><img src="docs/images/v17-rainbow.jpg" width="49%" alt="v17: the rainbow and Alexander's band from the exact Mie series"></a>

## Contents

* [Quick start](#quick-start)
* [Demonstrations for school students](#for-school-students)
* [Demonstrations for university students](#for-university-students)
* [Demonstrations for researchers](#for-researchers)
* [Playgrounds: the laboratory](#playgrounds-the-laboratory)
* [What is computed and how it is checked](#what-is-computed-and-how-it-is-checked)
* [Coverage and roadmap](#coverage-and-roadmap)
* [Documentation](#documentation)
* [Licence and citation](#licence-and-citation)

## Quick start

```bash
git clone https://github.com/ildar-idrisov/lfphys.git
cd lfphys

# with an NVIDIA GPU and the NVIDIA Container Toolkit
docker compose -f visualizations/docker/docker-compose.yml up -d --build viz

# without a GPU
docker compose -f visualizations/docker/docker-compose.yml --profile cpu up -d --build viz-cpu
```

Open <http://localhost:8479>, choose a demonstration and its scenario, and press **▶ Запустить** (Run). The player
opens; **⏺** records (computes the world further), and the slider goes back through the history. The switch
**Плейграунд** at the top of the catalogue opens the playgrounds.

| requirement | |
|---|---|
| Docker | Docker Engine with the Compose plugin v2 (`docker compose`) |
| disk | about 3.3 GB for the image; most of it is NVIDIA's CUDA libraries from PyPI, which only the GPU path uses. Run records go to `visualizations/runs/`, up to a quota of 5 GB; a run nobody opened for 3 days is removed unless marked ☆ (the period is set in the catalogue) |
| memory | the server's container is limited to 6 GB; each running world gets at most 60 % of it. A machine with 8 GB of RAM or more is advisable |
| CPU | each run computes in its own process with 2 threads; at most 3 runs compute at once |
| GPU (optional) | an NVIDIA GPU with a driver for CUDA 12 (version 525 or newer) and the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html); the server uses one GPU, device 0 |

**With or without a GPU.** The same code runs in both cases and gives the same checks; only the speed differs. With a
GPU, the heavy kernels move to it where measurement shows a gain: wave propagation by the angular spectrum, the ray
tracers of v10 and v15, the 2-D/3-D Schrödinger solver, lattice Boltzmann flow, molecular-dynamics pair forces and the
FDTD solver (measured, for example, ×26–29 for the Schrödinger solver on 1024²–2048² grids and ×8–155 for lattice
Boltzmann flow: `lfphys/README.md`, "CPU and GPU"). Checks are always computed in double precision. Without a GPU most
worlds still run at their default speed. The clearest exception is the flow of p04: in the Kármán-street scenario a
step took 13 ms on an 8-core desktop CPU and 0.19 ms on an RTX 2080 Ti, so without a GPU the street forms about 30 times
slower than the default speed. The exact two-slit world v11 computes slower than its default speed on either device,
and its pattern takes several minutes to form. The page **⚙ Устройства** (`/settings`) shows what runs where and lets
you choose the device and the precision per kernel.

**Settings.** Optional; a fresh clone works without them. Copy the template and edit it:

```bash
cp visualizations/docker/.env.example visualizations/docker/.env
```

* `UID`, `GID`: the owner of the clone (`id -u`, `id -g`) when it is not 1000:1000. The server writes the run
  records into `visualizations/runs/` as this user.
* `VIZ_PORT`: another port (8479 by default). `VIZ_PORT=127.0.0.1:8479` keeps the server reachable from this machine
  only.
* `VIZ_CPUS`: a CPU limit for the container (0, the default, means none).
* `LFPHYS_GPU_PCI`: on a host with several GPUs, paste GPU 0's bus id from
  `nvidia-smi --query-gpu=pci.bus_id --format=csv`; the engine then refuses any other device.

The server listens on all of the machine's addresses, so other computers on the local network can open
`http://<this machine's address>:8479`. It has no login: anyone who can reach the port can start runs. Keep it on a
trusted network, or bind it to `127.0.0.1` as above.

**Stop and start again.**

```bash
docker compose -f visualizations/docker/docker-compose.yml stop viz         # or: stop viz-cpu
docker compose -f visualizations/docker/docker-compose.yml start viz        # or: start viz-cpu
docker compose -f visualizations/docker/docker-compose.yml --profile cpu down   # remove the container
```

On stop the server suspends its runs and each world saves its state; a suspended run continues from it when you open
it and press ⏺. The records stay in `visualizations/runs/` after `down`. The server restarts with Docker unless you
stopped it.

**Tests and the engine as a library.**

```bash
docker compose -f visualizations/docker/docker-compose.yml run --rm viz-test   # visualizations and server
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf/lfphys lfphys-viz \
    python3 -m pytest -q -p no:cacheprovider                                  # the engine
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -e PYTHONPATH=/lf/lfphys lfphys-viz \
    python3 -c "from lfphys import registry; print(len(registry.catalogue()), 'modules')"
```

A research project uses the engine as an external library: `import lfphys` with `lfphys/` of this repository on
`PYTHONPATH`.

## Demonstrations by audience

Each card gives a picture of a run, the visualization's name (linked to its README with the model, the checks and the
approximations), what you will see, the physics sections, and the scenarios (presets) that suit this audience. A
demonstration that serves several audiences appears in each group with that group's presets. *Enrichment* marks topics
beyond a typical school curriculum that are still accessible to upper-school students. "Modified" marks a world with a
deliberately changed law; the player flags such worlds as **МОДИФИЦИРОВАННАЯ ФИЗИКА**.

### For school students

School courses begin with mechanics, electricity and magnetism; this collection does not cover them yet (see
[Coverage and roadmap](#coverage-and-roadmap)). What it has for school is heat and molecules, light, the atom,
relativity and gravitation, mostly the later chapters of a course. The curriculum references are examples of where the
topic is taught.

**Gravitation and orbits**

| | |
|---|---|
| <a href="docs/images/p01-inner.jpg"><img src="docs/images/p01-inner.jpg" width="300" alt="p01: the inner planets and Jupiter on their orbits"></a> | **[p01 · Space and gravity](visualizations/p01_gravity/README.md)** (playground)<br>Build a planetary system and watch Newton's law move it, body by body; energy, momentum and angular momentum are checked as it runs.<br>*Mechanics: gravitation · Astronomy* · IB D.1, AQA 3.7.2<br>Presets: "Sun and Earth (circular orbit, 1 au)"; "Sun, Mercury, Venus, Earth, Mars, Jupiter (circular orbits)" |
| <a href="docs/images/v04-newton.jpg"><img src="docs/images/v04-newton.jpg" width="300" alt="v04: a Newtonian ellipse with the general-relativity orbit as a ghost"></a> | **[v04 · Orbits and clocks: general relativity and Newton](visualizations/v04_orbits/README.md)** · *enrichment*<br>Newton's orbit closes into an ellipse; the ghost of the same start under general relativity does not. The player flags this world as modified physics, since its standard law is general relativity.<br>*Mechanics: gravitation · Relativity*<br>Preset: "Newton: a closed ellipse (ghost: GR)" |

**Heat and molecules**

| | |
|---|---|
| <a href="docs/images/p03-maxwell.jpg"><img src="docs/images/p03-maxwell.jpg" width="300" alt="p03: argon atoms and their velocity distribution against Maxwell's"></a> | **[p03 · Particles and molecules](visualizations/p03_molecules/README.md)** (playground)<br>A gas computed atom by atom: start every atom with the same speed and the Maxwell distribution appears by itself; a piston does work and a wall exchanges heat, and the first law balances; a crystal melts when heated.<br>*Thermal and molecular physics* · IB B.1, B.3, B.4, AP Physics 2 Unit 9, AQA 3.6.2<br>Presets: "Argon gas started with equal speeds: the Maxwell distribution sets in by itself"; "Gas under a piston: compression and heat exchange with a wall (the first law)"; "A 2-D crystal heated by a thermostat to 120 K: the order vanishes, atoms start to diffuse (melting)" |

**Fluids**

| | |
|---|---|
| <a href="docs/images/p04-airfoil.jpg"><img src="docs/images/p04-airfoil.jpg" width="300" alt="p04: flow past a NACA 2412 wing profile"></a> | **[p04 · Fluids](visualizations/p04_fluids/README.md)** (playground) · *enrichment*<br>Flow past a wing and a cylinder, computed by the lattice Boltzmann method; dye shows the stream, and drag and lift are measured.<br>*Fluids* · AP Physics 1 Unit 8<br>Presets: "NACA 2412 wing profile at 8° angle of attack (a cascade: periodic top and bottom)"; "Water: flow past a 1 mm cylinder in a 22 × 4.1 mm channel, Re = 20" |

**Light**

| | |
|---|---|
| <a href="docs/images/v05-tir.jpg"><img src="docs/images/v05-tir.jpg" width="300" alt="v05: total internal reflection of single photons"></a> | **[v05 · Optical bench: boundaries and coatings](visualizations/v05_optics_bench/README.md)**<br>Photons one by one at a glass–air boundary: beyond the critical angle every one is reflected, and an evanescent wave appears behind the boundary; a quarter-wave coating cuts the reflection.<br>*Optics* · IB C.3, AQA 3.3.2<br>Presets: "Total internal reflection: glass 1.5 → air, θ = 60° beyond the critical angle"; "Anti-reflection λ/4 layer with n = 1.38 (like MgF₂), λ₀ = 550 nm" |
| <a href="docs/images/v17-rainbow.jpg"><img src="docs/images/v17-rainbow.jpg" width="300" alt="v17: the sky around the antisolar point with the primary and secondary rainbows"></a> | **[v17 · Light scattered by a drop: the rainbow and the glory](visualizations/v17_mie_scattering/README.md)**<br>Sunlight on a cloud of water drops, summed wavelength by wavelength from the exact scattering by one drop: the primary and secondary bows, Alexander's dark band between them.<br>*Optics: refraction and dispersion* · AQA 3.3.2<br>Preset: "Rainbow: drops 0.15 mm ± 2 % in sunlight" |
| <a href="docs/images/v02-young.jpg"><img src="docs/images/v02-young.jpg" width="300" alt="v02: Young's experiment, single photons building up the fringes"></a> | **[v02 · The double-slit experiment](visualizations/v02_double_slit/README.md)**<br>Young's experiment with single photons: each lands at one point, and the fringes build up hit by hit.<br>*Optics · Quantum physics* · IB C.3, AQA 3.3.2 and 3.2.2<br>Preset: "Photons 633 nm, two slits (Young, one photon at a time)" |

**Relativity and astronomy**

| | |
|---|---|
| <a href="docs/images/v01-sun-earth.jpg"><img src="docs/images/v01-sun-earth.jpg" width="300" alt="v01: the light front from the Sun reaches the Earth after 8 min 17 s"></a> | **[v01 · Light over large distances](visualizations/v01_light_travel/README.md)**<br>A flash leaves the Sun and reaches the Earth 8 min 17 s later, on a map and on a spacetime diagram; observers moving along and against the light measure the same speed c.<br>*Relativity · Astronomy* · IB A.5 (HL), AQA 3.12 (option)<br>Presets: "Sun → Earth"; "Measuring c: at rest, moving along the light, against it" |
| <a href="docs/images/v10-city.jpg"><img src="docs/images/v10-city.jpg" width="300" alt="v10: the view of an observer flying down a street at 0.9 c"></a> | **[v10 · What a fast observer really sees](visualizations/v10_fast_observer/README.md)** · *enrichment*<br>The camera image of an observer near the speed of light, traced ray by ray with the light's travel time: the scene crowds forward, turns blue and brightens ahead.<br>*Relativity · Optics*<br>Presets: "A flight down a street at β = 0.9: aberration, blue ahead, brightness"; "The scene at rest (β = 0)" |
| <a href="docs/images/v15-m87.jpg"><img src="docs/images/v15-m87.jpg" width="300" alt="v15: the shadow of a black hole with its photon ring"></a> | **[v15 · The shadow of a Kerr black hole and its photon rings](visualizations/v15_kerr_shadow/README.md)** · *enrichment*<br>Why the Event Horizon Telescope saw a dark disk in a bright ring: every pixel is a light ray traced back from the observer.<br>*Relativity: black holes · Astronomy*<br>Presets: "No rotation (a = 0): the shadow is a circle of radius √27 M"; "M87*: a = 0.9, inclination 163°" |

**Atoms and quanta**

| | |
|---|---|
| <a href="docs/images/v13-2pz.jpg"><img src="docs/images/v13-2pz.jpg" width="300" alt="v13: the 2p_z orbital of hydrogen"></a> | **[v13 · The hydrogen atom in 3-D](visualizations/v13_hydrogen_3d/README.md)**<br>Orbitals from the exact solution of the Schrödinger equation: their shapes and nodes, the energy levels and the radial distribution.<br>*Atomic physics* · IB E.1, AQA 3.2.2<br>Presets: "1s: the ground state of hydrogen"; "2p_z: a dumbbell along z, nodal plane z = 0"; "3d_z²: lobes along z and a ring" |
| <a href="docs/images/p02-double-slit.jpg"><img src="docs/images/p02-double-slit.jpg" width="300" alt="p02: an electron wave passing two slits"></a> | **[p02 · Quantum particles](visualizations/p02_quantum/README.md)** (playground) · *enrichment*<br>An electron's wave passes two slits and interferes; the detector registers single particles.<br>*Quantum physics* · AQA 3.2.2<br>Preset: "Double slit: an electron, a wall with two slits, a detecting screen, Bohm particles" |

### For university students

**Mechanics and gravitation**

| | |
|---|---|
| <a href="docs/images/v04-rosette.jpg"><img src="docs/images/v04-rosette.jpg" width="300" alt="v04: a precessing orbit around a black hole with the periapsis advance measured"></a> | **[v04 · Orbits and clocks: general relativity and Newton](visualizations/v04_orbits/README.md)**<br>One body on an orbit computed from the exact geodesic equation: the periapsis advance is measured on the orbit and compared with the exact elliptic integral and with the post-Newtonian estimate; the body's clock against a distant one.<br>*Mechanics · General relativity*<br>Presets: "Mercury at the Sun (weak field, 43″ per century)"; "Black hole 10 M☉: a rosette (periapsis 20M)"; "Radial fall from rest at 20M (cycloid)" |
| <a href="docs/images/p01-inner.jpg"><img src="docs/images/p01-inner.jpg" width="300" alt="p01: planets on their orbits"></a> | **[p01 · Space and gravity](visualizations/p01_gravity/README.md)** (playground)<br>Newtonian N bodies with close encounters and mergers, computed by a time-symmetric Hermite scheme.<br>*Mechanics: gravitation, chaos*<br>Presets: "Pythagorean three-body problem (Burrau): masses 3, 4, 5 at rest, close encounters"; "Newtonian black hole of 1000 M☉ and stars: orbits and capture" |

**Fluids, heat and statistical physics**

| | |
|---|---|
| <a href="docs/images/p04-karman.jpg"><img src="docs/images/p04-karman.jpg" width="300" alt="p04: the Kármán vortex street behind a cylinder"></a> | **[p04 · Fluids](visualizations/p04_fluids/README.md)** (playground)<br>Viscous flow by the lattice Boltzmann method: a Poiseuille profile, a vortex street, drag and lift coefficients, the Strouhal number.<br>*Fluids*<br>Presets: "Channel flow (Poiseuille, Re ≈ 2) and a plate across it"; "Kármán vortex street behind a cylinder, Re = 100" |
| <a href="docs/images/p03-molecules.jpg"><img src="docs/images/p03-molecules.jpg" width="300" alt="p03: diatomic molecules and the velocity distribution"></a> | **[p03 · Particles and molecules](visualizations/p03_molecules/README.md)** (playground)<br>Molecular dynamics: equipartition among the modes of molecules, liquid–vapour coexistence, the radial distribution function g(r), pressure from the virial and from the walls.<br>*Thermal and statistical physics · Condensed matter*<br>Presets: "Diatomic molecules start with translation only: collisions share the energy with rotation and vibration"; "Liquid and vapour in 3-D at 90 K in a field: the density profile" |

**Waves and optics**

| | |
|---|---|
| <a href="docs/images/v05-tir.jpg"><img src="docs/images/v05-tir.jpg" width="300" alt="v05: reflection and transmission curves"></a> | **[v05 · Optical bench](visualizations/v05_optics_bench/README.md)**<br>Fresnel coefficients and multilayers by characteristic matrices decide each photon's fate; the photon counts converge to R, T, A.<br>*Optics*<br>Presets: "Glass n = 1.5 in air at Brewster's angle (unpolarised light: only s is reflected)"; "Frustrated total reflection: a 200 nm gap to a second prism (photon tunnelling)"; "Fabry–Pérot: a film n = 2.3, 2 µm thick" |
| <a href="docs/images/v08-circle.jpg"><img src="docs/images/v08-circle.jpg" width="300" alt="v08: light behind a circular aperture in 3-D, with a slice"></a> | **[v08 · A wave in 3-D: diffraction by an aperture](visualizations/v08_wave_3d/README.md)**<br>Fresnel diffraction behind apertures in a full 3-D scene with slice planes at any angle; the accuracy of each world and slice is measured.<br>*Waves · Optics*<br>Presets: "Circular aperture: dips and peaks of intensity on the axis"; "Gaussian beam, w = 1.5 µm: divergence"; "Two slits of finite length: the whole volume" |
| <a href="docs/images/v17-rainbow.jpg"><img src="docs/images/v17-rainbow.jpg" width="300" alt="v17: the rainbow"></a> | **[v17 · Light scattered by a drop](visualizations/v17_mie_scattering/README.md)**<br>The exact Mie series against Descartes' rays and Airy's theory: supernumerary bows, and why small drops give a white fogbow.<br>*Optics: scattering*<br>Presets: "Supernumerary bows: equal drops 0.1 mm ± 0.5 %"; "Fogbow: drops 15 µm ± 15 %, a broad white bow"; "Large drops 0.3 mm ± 10 %: supernumeraries washed out" |
| <a href="docs/images/v16-lg3.jpg"><img src="docs/images/v16-lg3.jpg" width="300" alt="v16: helical wavefronts of a Laguerre–Gauss beam"></a> | **[v16 · Optical vortices](visualizations/v16_optical_vortices/README.md)**<br>Laguerre–Gauss beams: helical wavefronts, energy flow spiralling around the axis, orbital and spin angular momentum per photon measured from the field; a rotating disk shifts the frequency.<br>*Optics: beams, angular momentum of light*<br>Presets: "LG₀³, σ = +1: three helical fronts, exact model, a rotating disk"; "LG₂¹: three rings"; "Fork hologram, l = 1"; "Control: a Gaussian beam without a vortex (l = 0)" |

**Relativity**

| | |
|---|---|
| <a href="docs/images/v01-lensing.jpg"><img src="docs/images/v01-lensing.jpg" width="300" alt="v01: light bent around a black hole"></a> | **[v01 · Light over large distances](visualizations/v01_light_travel/README.md)**<br>Relativity of simultaneity, clock synchronisation, light bending and delay near a black hole; flashes and the observers' speeds are set during the run.<br>*Special and general relativity*<br>Presets: "The Andromeda paradox: pedestrians at 1.4 m/s"; "Measuring c: clocks synchronised in the lab frame"; "Black hole of 10 M☉: deflection, shadow, two images" |
| <a href="docs/images/v10-terrell.jpg"><img src="docs/images/v10-terrell.jpg" width="300" alt="v10: a cube and a sphere flying past at 0.9 c"></a> | **[v10 · What a fast observer really sees](visualizations/v10_fast_observer/README.md)**<br>Why the Lorentz contraction is invisible and a rotation (Terrell–Penrose) is seen instead; Doppler colour and the searchlight effect, from ray tracing with the light's travel time.<br>*Special relativity · Optics*<br>Presets: "A cube and a sphere fly past at β = 0.9: Terrell rotation, the sphere stays round"; "For comparison: an instantaneous snapshot"; "A train at β = 0.8 past poles" |
| <a href="docs/images/v09-thomas.jpg"><img src="docs/images/v09-thomas.jpg" width="300" alt="v09: the velocity ball with the rotation field of Thomas precession"></a> | **[v09 · Thomas–Wigner precession in 3-D](visualizations/v09_thomas_3d/README.md)**<br>A craft flies a loop and comes back to rest with its gyroscopes turned, with no torque on them.<br>*Special relativity*<br>Presets: "Thomas precession: uniform circular motion, γ = 1.34"; "Ordinary space: the path and the gyroscopes in Thomas precession" |
| <a href="docs/images/v15-edge.jpg"><img src="docs/images/v15-edge.jpg" width="300" alt="v15: a black hole seen edge-on"></a> | **[v15 · The shadow of a Kerr black hole](visualizations/v15_kerr_shadow/README.md)**<br>Photon orbits and the shadow's edge against Bardeen's formula; the images of the disk n = 0, 1, 2.<br>*General relativity*<br>Presets: "Disk edge-on (θ = 90°), a = 0.99: a flattened shadow"; "A narrow ring of gas at 6 M: its images n = 0, 1, 2" |

**Quantum physics**

| | |
|---|---|
| <a href="docs/images/v03-tunnel.jpg"><img src="docs/images/v03-tunnel.jpg" width="300" alt="v03: an electron packet at a barrier, reflected and transmitted parts"></a> | **[v03 · A quantum particle in one dimension](visualizations/v03_quantum_1d/README.md)**<br>An electron packet at a barrier, a step, a well or in a trap: the exact time-dependent solution, its transmission against the stationary one, and detectors that click.<br>*Quantum physics*<br>Presets: "Electron tunnelling through a 1 eV × 0.6 nm barrier"; "Resonant tunnelling: a double barrier"; "Step: reflection at E > V₀"; "A packet in a harmonic trap (coherent state)" |
| <a href="docs/images/v02-young.jpg"><img src="docs/images/v02-young.jpg" width="300" alt="v02: the double slit"></a> | **[v02 · The double-slit experiment](visualizations/v02_double_slit/README.md)**<br>Which-path detectors, polarisation marks, the quantum eraser, partial coherence, electrons, neutrons and C₆₀.<br>*Quantum physics · Optics*<br>Presets: "Electrons + which-path detector (θ = 90°, not read)"; "Quantum eraser: H/V marks + 45° analyser"; "Photons: a wide source (partial coherence)"; "Electrons: Aharonov–Bohm effect" |
| <a href="docs/images/v11-mark180.jpg"><img src="docs/images/v11-mark180.jpg" width="300" alt="v11: the exact two-slit wave with Bohm trajectories"></a> | **[v11 · The double slit with long slits, in 3-D](visualizations/v11_double_slit_2d/README.md)**<br>The time-dependent Schrödinger equation on the whole plane of the experiment, no paraxial approximation: reflection by the plate, the wave in the slits, the pattern as it arrives.<br>*Quantum physics*<br>Presets: "One slit (B closed): the envelope without fringes"; "Slits a = 6λ in a thin high wall: closer to paraxial theory"; "Aharonov–Bohm: flux Φ₀/2 between the slits shifts the fringes by half a period" |
| <a href="docs/images/v07-bell.jpg"><img src="docs/images/v07-bell.jpg" width="300" alt="v07: the Bell test with the CHSH parameter"></a> | **[v07 · The Bell test with entangled pairs](visualizations/v07_bell_test/README.md)**<br>Entangled photons or spins at two stations: coincidences, correlations E and the CHSH parameter S against the bounds 2 and 2√2; the settings are chosen outside each other's light cone.<br>*Quantum physics*<br>Presets: "Photons \|Φ+⟩: optimal CHSH angles, random choice"; "Spin-½ singlet: optimal angles, random choice"; "The curve E(Δ): fixed settings, move b" |
| <a href="docs/images/p02-trap.jpg"><img src="docs/images/p02-trap.jpg" width="300" alt="p02: a packet in a harmonic trap"></a> | **[p02 · Quantum particles](visualizations/p02_quantum/README.md)** (playground)<br>Wave packets in 2-D and 3-D in a scene of barriers, traps and fields you build; position measurements as actions.<br>*Quantum physics*<br>Presets: "Tunnelling: a packet at a thin barrier higher than its energy"; "Harmonic trap: a displaced packet oscillates; a position measurement"; "An electron in a 100 T magnetic field: a circular orbit"; "3-D: an electron scattered by a sphere" |

**Atomic and particle physics**

| | |
|---|---|
| <a href="docs/images/v13-m1.jpg"><img src="docs/images/v13-m1.jpg" width="300" alt="v13: the complex 2p orbital with m = +1 and its ring current"></a> | **[v13 · The hydrogen atom in 3-D](visualizations/v13_hydrogen_3d/README.md)**<br>Real orbitals are standing waves without current; complex ones with m ≠ 0 carry a ring current; a superposition of two levels oscillates at the Bohr frequency.<br>*Atomic physics · Quantum physics*<br>Presets: "2p_x real: a standing wave, no current"; "2p, m = +1 complex: a doughnut and a ring current"; "1s + 2p_z: the cloud oscillates along z at the Bohr frequency" |
| <a href="docs/images/v06-qcd.jpg"><img src="docs/images/v06-qcd.jpg" width="300" alt="v06: the running strong coupling and the charmonium levels"></a> | **[v06 · QCD: asymptotic freedom and quarkonium](visualizations/v06_qcd/README.md)**<br>The strong coupling α_s runs from 1 GeV to 10 TeV (one to four loops, quark thresholds); charmonium and bottomonium levels in the Cornell model against measured ones.<br>*Particle physics*<br>Presets: "Asymptotic freedom and charmonium (PDG 2024, Cornell model)"; "Bottomonium" |
| <a href="docs/images/v14-1p.jpg"><img src="docs/images/v14-1p.jpg" width="300" alt="v14: the 1P state of charmonium"></a> | **[v14 · Quarkonium in 3-D](visualizations/v14_quarkonium_3d/README.md)**<br>Wave functions of a heavy quark pair in the Cornell model, a heavy-quark analogue of the hydrogen atom; the model's level splittings against the Particle Data Group values.<br>*Particle physics*<br>Presets: "cc̄ 1S (J/ψ, η_c without spin)"; "cc̄ 1P (χ_c, h_c), p_z"; "cc̄ 2S (ψ(2S)): one radial node"; "bb̄ 1S (Υ(1S)): a tighter cloud" |

### For researchers

**General relativity and black holes**

| | |
|---|---|
| <a href="docs/images/v15-m87.jpg"><img src="docs/images/v15-m87.jpg" width="300" alt="v15: the image of M87*"></a> | **[v15 · The shadow of a Kerr black hole; what if the hole is not Kerr](visualizations/v15_kerr_shadow/README.md)**<br>The shadow's size against the EHT measurements of M87* and Sgr A*; the photon ring's demagnification against the Lyapunov exponent; a Johannsen metric as a declared alternative.<br>*General relativity · Astrophysics*<br>Presets: "M87*: a = 0.9, inclination 163°"; "Sgr A*: a = 0.5, inclination 30°, comparison with EHT 2022"; "What if: the Johannsen metric α₁₃ = 3" (modified) |
| <a href="docs/images/v04-rosette.jpg"><img src="docs/images/v04-rosette.jpg" width="300" alt="v04: orbits in strong gravity"></a> | **[v04 · Orbits and clocks](visualizations/v04_orbits/README.md)**<br>Exact geodesics against the weak-field (PPN) expansion on the same orbit, the instability inside the ISCO, equatorial Kerr orbits.<br>*General relativity*<br>Presets: "Neutron star: strong precession"; "Black hole: a circular orbit near the ISCO (6.2M)"; "Plunge inside the ISCO" |
| <a href="docs/images/p01-inspiral.jpg"><img src="docs/images/p01-inspiral.jpg" width="300" alt="p01: a binary inspiral with the gravitational-wave signal"></a> | **[p01 · Space and gravity](visualizations/p01_gravity/README.md)** (playground)<br>A post-Newtonian binary with radiation reaction and the wave signal h₊, h× at a detector; bodies, light rays and clocks around a Kerr–Newman black hole.<br>*General relativity · Gravitational waves*<br>Presets: "GR: a 10 + 10 M☉ binary from 20 G m/c² and a wave detector (inspiral)"; "GR: an eccentric 30 + 10 M☉ binary (e = 0.5)"; "At a black hole (a = 0.9): bodies, light rays, observers' clocks" |

**Special relativity and the history of its tests**

| | |
|---|---|
| <a href="docs/images/v09-seam.jpg"><img src="docs/images/v09-seam.jpg" width="300" alt="v09: a non-planar loop on the velocity sphere"></a> | **[v09 · Thomas–Wigner precession in 3-D](visualizations/v09_thomas_3d/README.md)**<br>The holonomy of a manoeuvre in SO(3) and SU(2), velocity-space geometry and the isoperimetric bound on the rotation per unit of fuel; planar and non-planar loops.<br>*Special relativity · Lorentz group*<br>Presets: "Three impulses: Wigner angle = area of the velocity triangle"; "A circle through rest: equality in the isoperimetric bound"; "SU(2): the gyroscopes are back, the spinor changed sign"; "A ball's seam on the velocity sphere (non-planar, 96 impulses)" |
| <a href="docs/images/v10-terrell.jpg"><img src="docs/images/v10-terrell.jpg" width="300" alt="v10: Terrell rotation"></a> | **[v10 · What a fast observer really sees](visualizations/v10_fast_observer/README.md)**<br>Light-time ray tracing of moving bodies, each photon Lorentz-transformed, the light as a black body at the Doppler-shifted temperature.<br>*Special relativity*<br>Presets: "A 4000 K sky at β = 0.9: dipole, stars crowd forward"; "Same at β = 0.99"; "The scene at rest (β = 0): a check of the tracer" |
| <a href="docs/images/v01-sun-earth.jpg"><img src="docs/images/v01-sun-earth.jpg" width="300" alt="v01: light cones and simultaneity"></a> | **[v01 · Light over large distances](visualizations/v01_light_travel/README.md)**<br>The same measurements in worlds with other laws of light: an ether, ballistic (Ritz) light, Newtonian corpuscles.<br>*Special relativity · History of physics*<br>Presets (modified): "Measuring c in a world with an ether"; "Measuring c with ballistic light"; "An arm across the motion (Michelson–Morley), ether"; "Newtonian corpuscles at a black hole" |

**Optics and electromagnetic waves**

| | |
|---|---|
| <a href="docs/images/v02-vector.jpg"><img src="docs/images/v02-vector.jpg" width="300" alt="v02: vector diffraction by narrow slits in a conducting screen"></a> | **[v02 · The double-slit experiment](visualizations/v02_double_slit/README.md)**<br>Vector diffraction by slits in a perfectly conducting screen of finite thickness (TE and TM) against the scalar model; a three-slit test of the Born rule.<br>*Electromagnetic waves · Quantum foundations*<br>Presets: "Vector diffraction: 0.5 µm slits in a 0.2 µm conducting screen"; "Three slits: a test of the Born rule (Sorkin)" |
| <a href="docs/images/v16-tight.jpg"><img src="docs/images/v16-tight.jpg" width="300" alt="v16: a tightly focused vortex beam"></a> | **[v16 · Optical vortices](visualizations/v16_optical_vortices/README.md)**<br>The exact vector beam against the paraxial model under tight focusing: the longitudinal field and the spin–orbit split of angular momentum, which depends on its definition; the rotational Doppler effect.<br>*Optics · Angular momentum of light*<br>Presets: "Tight focusing: l = 1, σ = −1, w0 = 0.6 λ"; "The same in the paraxial model (approximation): what it misses"; "A rotating Dove prism: frequency shift 2\|l\|f"; "Linear polarisation, l = 1" |
| <a href="docs/images/v17-glory.jpg"><img src="docs/images/v17-glory.jpg" width="300" alt="v17: the glory around the antisolar point"></a> | **[v17 · Light scattered by a drop](visualizations/v17_mie_scattering/README.md)**<br>The glory, the near field of a small drop, an absorbing sphere; the Debye series against Descartes and Airy, checked against Wiscombe's published values.<br>*Optics: Mie theory*<br>Presets: "Glory: cloud drops 8 µm ± 10 %, coloured rings at the antisolar point"; "Near field: a 1 µm drop in 550 nm light"; "An absorbing sphere 2 µm, n = 1.6 + 0.05i" |
| <a href="docs/images/v05-spr.jpg"><img src="docs/images/v05-spr.jpg" width="300" alt="v05: the surface plasmon resonance dip"></a> | **[v05 · Optical bench](visualizations/v05_optics_bench/README.md)**<br>Thin metal films and the surface plasmon resonance by Abelès matrices, with the field \|E\|² inside the layers.<br>*Optics*<br>Presets: "Metal film 30 nm, n = 0.2 + 3.3i (like gold at 633 nm)"; "Surface plasmon resonance (Kretschmann)" |
| <a href="docs/images/v08-double.jpg"><img src="docs/images/v08-double.jpg" width="300" alt="v08: two slits of finite length, the whole volume"></a> | **[v08 · A wave in 3-D](visualizations/v08_wave_3d/README.md)**<br>Full 3-D modelling against a chosen 2-D slice computed by a simplified model; the method's accuracy measured per world and per slice.<br>*Computational optics*<br>Presets: "Two slits: slices only, y = c by a simplified 2-D model (approximation)"; "Square aperture, grid 512: slices only" |

**Quantum foundations**

| | |
|---|---|
| <a href="docs/images/v11-narrow.jpg"><img src="docs/images/v11-narrow.jpg" width="300" alt="v11: narrow slits, diffraction to large angles, Bohm trajectories"></a> | **[v11 · The double slit with long slits, in 3-D](visualizations/v11_double_slit_2d/README.md)**<br>Where paraxial theory fails (narrow slits, large angles); how a which-path mark kills the fringes; Bohm trajectories labelled by their slit.<br>*Quantum foundations*<br>Presets: "Narrow slits a = 2λ: paraxial theory fails"; "Which-path mark: spin in slit B turned by 180°"; "Partial mark: 90° turn, visibility cos 45°"; "An observer at slit B: a which-path detector for a spinless ⁴He atom" |
| <a href="docs/images/v12-near.jpg"><img src="docs/images/v12-near.jpg" width="300" alt="v12: arrival-time distributions by several rules"></a> | **[v12 · When does the particle arrive? Arrival times in 2-D](visualizations/v12_arrival_times_2d/README.md)**<br>Quantum mechanics does not fix the arrival time; the run computes it by the quantum flux, Bohm's first arrivals, Aharonov–Bohm–Kijowski, semiclassical and absorbing-boundary rules and detector models, and shows where they agree and where they differ.<br>*Quantum foundations*<br>Presets: "One packet: all rules nearly agree far from the source"; "Close to the source: the rules diverge"; "A train of 4 packets (Das & Struyve 2021)"; "Backflow"; "Through two slits: the joint distribution of place and time (Das et al. 2024)" |
| <a href="docs/images/v07-bell.jpg"><img src="docs/images/v07-bell.jpg" width="300" alt="v07: the Bell test"></a> | **[v07 · The Bell test](visualizations/v07_bell_test/README.md)**<br>Quantum mechanics (S up to 2√2) against local hidden-variable models (\|S\| ≤ 2) on the same events; the locality loophole when the choice comes too early.<br>*Quantum foundations*<br>Presets: "Photons, local hidden variables: a polarisation model" (modified); "Spin-½ singlet: Bell's sign model" (modified); "Photons: the choice made 5 µs before arrival, the locality loophole is open" |
| <a href="docs/images/v03-bohm.jpg"><img src="docs/images/v03-bohm.jpg" width="300" alt="v03: Bohm trajectories through a barrier"></a> | **[v03 · A quantum particle in one dimension](visualizations/v03_quantum_1d/README.md)**<br>One computation read three ways: a click and a collapse, Bohm trajectories, Everett's branches; the statistics are the same.<br>*Quantum foundations · Interpretations*<br>Presets: "The same through Bohm's eyes: trajectories"; "The same by Everett: branches" |
| <a href="docs/images/v02-vector.jpg"><img src="docs/images/v02-vector.jpg" width="300" alt="v02: the double slit"></a> | **[v02 · The double-slit experiment](visualizations/v02_double_slit/README.md)**<br>Changed laws as named parameters: a Born-rule exponent, enhanced GRW collapse, a forced choice of slit.<br>*Quantum foundations*<br>Presets (modified): "Three slits with P ∝ \|ψ\|^2.4"; "C60 with enhanced GRW collapse"; "Forced choice of a slit" |
| <a href="docs/images/p02-trap.jpg"><img src="docs/images/p02-trap.jpg" width="300" alt="p02: quantum playground"></a> | **[p02 · Quantum particles](visualizations/p02_quantum/README.md)** (playground)<br>Which-path markers, Aharonov–Bohm flux tubes, decoherence by an environment, Bohm points, parameter sweeps.<br>*Quantum foundations*<br>Presets: "Which-path mark in the upper slit: the fringes almost vanish (visibility 0.94 → 0.18)"; "Aharonov–Bohm: a flux tube h/2e shifts the fringes by half a period" |

**Atoms, QCD, molecular and fluid benchmarks**

| | |
|---|---|
| <a href="docs/images/v14-1p.jpg"><img src="docs/images/v14-1p.jpg" width="300" alt="v14: quarkonium"></a> | **[v14 · Quarkonium in 3-D](visualizations/v14_quarkonium_3d/README.md)** and **[v13 · The hydrogen atom in 3-D](visualizations/v13_hydrogen_3d/README.md)**<br>What a fitted model predicts (splittings) and what it does not (absolute masses); high-n states and hydrogen-like ions.<br>*Particle and atomic physics*<br>Presets: v14 "cc̄ 1S + 1P_z: the pair oscillates at the transition frequency"; v13 "n = 10, l = 3, m = 1: a large cloud, 6 radial nodes", "He⁺ ion, 3d_xy" |
| <a href="docs/images/v06-qcd.jpg"><img src="docs/images/v06-qcd.jpg" width="300" alt="v06: running alpha_s"></a> | **[v06 · QCD](visualizations/v06_qcd/README.md)**<br>How much the higher loops matter, and a world with another coupling.<br>*Particle physics*<br>Presets: "One loop only: how much the higher orders matter"; "What if α_s(M_Z) = 0.15" (modified) |
| <a href="docs/images/p03-molecules.jpg"><img src="docs/images/p03-molecules.jpg" width="300" alt="p03: molecular dynamics"></a> | **[p03 · Particles and molecules](visualizations/p03_molecules/README.md)** and **[p04 · Fluids](visualizations/p04_fluids/README.md)** (playgrounds)<br>Published benchmarks inside the playgrounds: the hard-disk equation of state; the DFG cylinder benchmarks and Ghia's cavity.<br>*Statistical mechanics · Fluid dynamics*<br>Presets: p03 "Hard disks: pressure against the equation of state (Kolafa and Rottner)"; p04 "Flow past a cylinder, Re = 20 (DFG 2D-1)", "Lid-driven cavity, Re = 100 (Ghia, Ghia, Shin 1982)" |

### Playgrounds: the laboratory

In a playground the scene is not prepared: you build it from a palette, change it at any moment, and the world computes
what follows in real time. The catalogue's switch **Плейграунд** opens them; each starts from a scenario or from an
empty scene.

* **Palette and objects**: add bodies, packets, atoms, walls, obstacles, detectors and probes at the current moment;
  copy or delete them; the inspector changes an object's parameters live and shows its computed state.
* **Live laws**: the laws the engine can change at the current moment (a viscosity, a time step, an interaction model,
  the grid) change at once; other laws start a new world, which can take the scene and its state along.
* **Drag and throw**: drag an object to move it; Shift-drag throws it with the speed of your hand.
* **Instruments**: every measurable quantity with its value at the history cursor; tick one to plot it over the
  record, export to CSV.
* **Parameter sweeps**: the same experiment from the current moment repeated for a list of values of a law or an
  object's parameter, in a separate process; a table, a plot and a CSV.
* **Scene files and recording**: save a scene to a file and start from it; the record keeps the last 10 minutes of
  computing (at most 1 GB), or everything from the moment you press «● Сохранять запись».
* Conservation laws are checked as the world runs.

| | |
|---|---|
| <a href="docs/images/p01-inspiral.jpg"><img src="docs/images/p01-inspiral.jpg" width="300" alt="p01 playground"></a> | **[p01 · Space and gravity](visualizations/p01_gravity/README.md)**<br>Stars, planets, Newtonian black holes and test bodies (Newton's N bodies with mergers); a general-relativistic binary radiating gravitational waves, with a detector; bodies, light rays and observers with clocks at a Kerr–Newman black hole.<br>All presets: Sun and Earth · inner planets and Jupiter · Pythagorean three-body problem · black hole and stars · Kerr black hole with bodies, rays and clocks · GR binary inspiral · eccentric GR binary |
| <a href="docs/images/p02-double-slit.jpg"><img src="docs/images/p02-double-slit.jpg" width="300" alt="p02 playground"></a> | **[p02 · Quantum particles](visualizations/p02_quantum/README.md)**<br>Wave packets of electrons, neutrons and atoms (with spin) in a plane or a volume; barriers, wells, walls with slits, traps, magnetic fields, Aharonov–Bohm tubes, detectors, which-path marks, an environment; position measurements; Bohm particles.<br>All presets: double slit · which-path mark · Aharonov–Bohm · tunnelling · harmonic trap · electron in 100 T · 3-D scattering by a sphere |
| <a href="docs/images/p03-maxwell.jpg"><img src="docs/images/p03-maxwell.jpg" width="300" alt="p03 playground"></a> | **[p03 · Particles and molecules](visualizations/p03_molecules/README.md)**<br>Gases, crystals, atoms and molecules with bonds and angles; mirror, soft and thermal walls, a piston, thermostats, a field, thermometers; temperature, pressure, heat and work, the Maxwell distribution, g(r).<br>All presets: Maxwell distribution · melting · gas under a piston · liquid and vapour · diatomic molecules · hard disks |
| <a href="docs/images/p04-karman.jpg"><img src="docs/images/p04-karman.jpg" width="300" alt="p04 playground"></a> | **[p04 · Fluids](visualizations/p04_fluids/README.md)**<br>2-D flow by the lattice Boltzmann method: cylinders, rectangles, NACA profiles, inlets and outlets, moving walls, dye, velocity probes; drag and lift, mass and momentum balances; viscosity, grid and domain changed live.<br>All presets: cylinder Re = 20 (DFG 2D-1) · Kármán street Re = 100 (DFG 2D-2) · lid-driven cavity · channel with a plate · water cylinder · air cylinder · NACA 2412 cascade |

## What is computed and how it is checked

* **Layers.** The engine's core holds established physics only; approximations, interpretations, phenomenological
  models and declared alternatives sit outside it, each stating where it disagrees with the core
  ([`lfphys/LAYERS.md`](lfphys/LAYERS.md)). Every module carries a passport (layer, statement, validity, basis,
  conflicts); the player's panel «Физика этого мира» lists the modules a world uses, inside and outside the core.
* **Computed, not drawn.** Every visible consequence comes from the run's own computation; closed forms of the known
  theory appear only as references in the checks. Consequences appear when the world's time reaches them.
* **Checks in every run.** The panel «Проверки» shows each quantity computed in the run next to its reference (✓ or ✗):
  a closed form, an independent method or a measured value. A world with a changed law is flagged «МОДИФИЦИРОВАННАЯ
  ФИЗИКА», an approximation «ПРИБЛИЖЕНИЕ».
* **Tests.** About 1,600 test functions: each engine function against a closed form or a second method, with
  certified interval references (Arb ball arithmetic) for key quantities; each visualization and the server.
* **Reviews.** New physics is reviewed by a reviewer other than its author, and each finding is answered in a
  response: fixed, rejected with a reason, or deferred to `STATUS.md`. The 32 processed reviews so far are internal
  (run within the project) and are kept with their responses in [`reviews/archive/`](reviews/archive/).
* **Third-party libraries, for comparison only.** 2,961 comparisons with CRunDec (rundec), KerrGeoPy, tmm, QuTiP,
  Astropy and miepython: no failures, 19 known disagreements recorded with their numbers
  ([`lfphys/tests/external/RESULTS.md`](lfphys/tests/external/RESULTS.md)); a one-off comparison with the FDTD solver
  Meep ([`lfphys/sources/comparison_2026-11-04_meep.md`](lfphys/sources/comparison_2026-11-04_meep.md)).

This is a research tool: the tests check the stated cases within the stated ranges, not every problem. Open problems
are listed in [`STATUS.md`](STATUS.md).

## Coverage and roadmap

The collection is strongest in optics, quantum physics and relativity, where it reaches from school topics to research
questions. The first half of a school course has no demonstrations yet. The main gaps, in order of their weight in
school and university courses, and what the engine already has for them:

| section | now | main gaps | already in the engine |
|---|---|---|---|
| mechanics | orbits (p01, v04) | kinematics and projectiles, Newton's laws with friction, energy, collisions, rotation | exact elastic collisions of disks and spheres (`core.md.hard`), N bodies with mergers (`core.gravity.nbody`); rigid bodies need a new module |
| oscillations and waves | diffraction (v02, v08, v11), the quantum oscillator (v03) | pendulum and spring, damped and driven oscillations, resonance; standing waves, sound, the Doppler effect | a 2-D/3-D Maxwell solver (`core.em.fdtd`), not yet used by any visualization |
| electricity and magnetism | none | field lines and potential, capacitors, DC and AC circuits, fields of currents, induction | fields and radiation of moving point charges (`core.em.charges`, not yet used); a playground is planned (`lfphys/PLAN.md` P15.5); circuits need a new solver |
| optics | v02, v05, v08, v16, v17 | lenses, mirrors and image formation, prisms, gratings, polarisation | Snell's law and ray-transfer matrices (`theories.approx.ray_optics`); a playground is planned (P15.2) |
| thermal physics | p03 | named gas-law and heat-engine scenarios with a P–V plot | the piston, heat baths, heat and work counters and sweeps of p03 |
| relativity | v01, v04, v09, v10, v15, p01 | time dilation and the twin paradox, spacetime diagrams, relativistic collisions | `core.relativity`, `core.worldlines`, `core.lorentz`; a playground is planned (P15.6) |
| quantum and atomic physics | v02, v03, v07, v11, v12, v13, p02 | the photoelectric effect, Compton scattering, black-body spectrum, line spectra, Stern–Gerlach, Rabi oscillations | Compton scattering (`core.quantum.compton`), the two-level atom (`core.quantum.two_level`), both not yet used; Planck's law, hydrogen levels and dipole matrix elements |
| nuclear physics | none | decay and half-life, binding energy, fission and fusion | none |
| astrophysics and cosmology | v01, v15, p01 | the Hubble law and the expansion history | the FLRW background with Planck 2018 parameters (`core.cosmology.flrw`), not yet used |

Where a module exists, a demonstration still has to be designed, built, tested and reviewed; the order of the work is
the author's decision. Plans: [`lfphys/PLAN.md`](lfphys/PLAN.md); open items: [`STATUS.md`](STATUS.md).

## Documentation

* [`visualizations/README.md`](visualizations/README.md): the guide to the server and the player, every world and its
  controls (in Russian).
* Each world's README, with its model, checks, approximations and tests: v01–v17 and p01–p04, linked in the tables
  above.
* [`visualizations/RULES.md`](visualizations/RULES.md): the rules every visualization follows (physics, causality,
  modified laws, the 3-D environment, the playground) and the server's API.
* [`lfphys/README.md`](lfphys/README.md): the engine's catalogue of modules, CPU and GPU, certified references;
  [`lfphys/LAYERS.md`](lfphys/LAYERS.md): the layers; [`lfphys/PLAN.md`](lfphys/PLAN.md): the development plan.
* [`STATUS.md`](STATUS.md): open problems and plans. [`reviews/`](reviews/README.md): the reviews and their
  responses. [`AGENTS.md`](AGENTS.md): the rules for work in this repository.

## Licence and citation

lfphys is **source-available, not open source**. The code is under the
[lfphys Research Licence 1.0](LICENSE.md): use for noncommercial research, study and teaching is free; any commercial
use, by anyone, needs a separate written agreement ([`COMMERCIAL.md`](COMMERCIAL.md)). The documentation and the
author's figures are under CC BY-NC-SA 4.0 ([`LICENSE-DOCS.txt`](LICENSE-DOCS.txt)), with additional permissions for
scholarly publications ([`PUBLICATIONS.md`](PUBLICATIONS.md)). Your results are yours; a publication of results
obtained substantially with lfphys must cite it with its version, as in [`CITATION.cff`](CITATION.cff) (the player
shows the version on its page «Лицензия»). Third-party components keep their own licences ([`NOTICE`](NOTICE)).
Contributions: [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CLA.md`](CLA.md). No warranty: [`LICENSE.md`](LICENSE.md) §8.

Questions and commercial use: [idrisov.sci@gmail.com](mailto:idrisov.sci@gmail.com).

Copyright (c) 2026 Ildar Idrisov.
