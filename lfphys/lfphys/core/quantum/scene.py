# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""A quantum scene for the playground (plan P15.3): objects placed and changed by hand at any moment on a 1-D, 2-D or
3-D grid, non-interacting particles as wave packets, one solver family (the split operator of
``lfphys.core.quantum.schrodinger_nd``) and checkable invariants.

Every particle obeys its own Schroedinger or Pauli equation (hbar = 1 in the scene's units, ``Units``)

    i d psi/dt = [ (p - q A)^2 / 2m + V_s(r) - i W(r) + b_s(r) . sigma ] psi,

with the scene's potentials shared by all particles and coupled per species: V_s = V_energy + q V_charge (a shape
is a potential energy for every species, or with ``coupling="charge"`` an electrostatic potential that acts through
q), A through q (``MagneticField`` of a uniform field normal to the plane, ``FluxTube``), b_s = -mu B through the
signed magnetic moment mu of a spin-1/2 species (``MagneticField`` of any field, the field inside a ``FluxTube``), or
the coupling of a which-path marker (``PathMarker``). **The particles do not interact**: each has its own wave and the
scene evolves them independently (no mutual potential, no exchange symmetry: distinguishable particles); what they
share is the set-up.

Objects (each a plain dataclass whose parameters are physical, with ``params()`` and a closed-form evaluation on any
grid; ``bbox`` for drawing)

* **Shapes** (potential energy, any sign): ``Box`` (barrier or well, a dimension may be unbounded), ``Ball`` (disk or
  sphere, or a cylinder in 3-D; R >= 1.45 edge, else its profile has a kink at the centre: review B6-Q14), ``SlitWall`` (a wall of a thickness and height with N slits; in 3-D the slits run
  through the window or have a length), ``Step``, ``HarmonicTrap`` (frequency omega for a stated mass:
  V = mass omega_i^2 (x_i - c_i)^2 / 2, the same V for every species). Edges are smooth: the sharp shape blurred by a
  Gaussian, so every edge is the error-function step

      S(u) = (1 + erf(u / eps)) / 2,    eps = w / (2 erfinv(0.8)),

  where the **edge width w is the 10 %-90 % rise distance, a physical length**, the same on every grid. A box and a
  wall are the exact Gaussian blurs of the sharp box and of the sharp wall with non-overlapping holes (separable:
  blur(1_[lo,hi])(x) = [erfc((x - hi)/eps) - erfc((x - lo)/eps)] / 2 per axis); a ball is the radial step
  S(R - |r - c|) (not the blur of the ball; its closed form is that). An edge is refused when the grid cannot
  resolve it: the spectrum of the step's derivative, exp(-k^2 eps^2 / 4), must be below ``EDGE_TOL`` = 1e-3 at the
  grid's largest wavenumber pi/d, i.e. w >= (4 erfinv(0.8)/pi) sqrt(ln 1/EDGE_TOL) d = 3.03 d (``edge_min``).
* **Magnetic objects.** ``MagneticField``: B(r) = f(r) [B0 + G (r - c)] with an optional box profile f (edges as
  above) and a gradient G that must be symmetric and traceless (in vacuum div B = 0 and curl B = 0; refused
  otherwise). Grid axes 0, 1, 2 are x, y, z; a 2-D scene is the plane z = c_z of a 3-D field, a 1-D scene the line
  y = c_y, z = c_z. It couples to a spin by b = -mu B. It couples to a charge (orbital, through A) only when it is
  uniform and normal to the plane (2-D: B0 along z) or, in 3-D, along a grid axis with a region unbounded along that
  axis (a prism: a field confined in its own direction would have div B != 0): then
      A_b = B g(x_b) F(x_a),   F(x_a) = int_{-inf}^{x_a} f_a,   B along e_a x e_b,
  the Landau gauge of the region's profile f_a(x_a) g(x_b) (closed form: F = J(x_a - lo) - J(x_a - hi),
  J(u) = [u erfc(-u/eps) + eps exp(-u^2/eps^2)/sqrt(pi)]/2). Its curl is the field and nothing else; outside the
  region A vanishes except in the half-strip beyond the region along +a (``string = +1``; -a with -1), where
  A_b = B W_a g(x_b) is a pure gauge whose line integral across the window along b is the flux Phi = B W_a H_b:
  there the split operator's gauge phase wraps at the window's edges, so psi must vanish at those edges (the open
  edges absorb: ``EdgeLayers``). With a closed (periodic) axis the wrap is a sheet of field of flux -Phi at the face
  (a whole-window field: the jump of B (x - c) across it; a flux tube: the twist of its line integral), which kicked a
  packet that never came near the field (review B6-Q2): a charged particle next to any vector potential is refused
  unless absorbing edges cover every axis (``_gauge_reason``). A packet placed in the strip carries the gauge factor
  (below). Any other field with a charged particle in the scene is refused (its orbital coupling needs motion out of
  the plane or an A this module does not build). A change of the set-up keeps psi, so a vector potential changed
  while a charged wave is in the window changes its kinetic momentum by -q Delta A(r): the impulse of the switch's
  induced field -dA/dt only in the gauge of the magnet that makes it (for a z-invariant field with E -> 0 far away,
  Faraday's law fixes the Coulomb gauge). A flux tube's A is that gauge about its axis (a thin solenoid): kept. A
  uniform field's Landau gauge is not (its reference is an implementation detail: two set-ups identical in the window
  ended 29 nm apart, review B6-Q3): changing such a field while a charged particle's probability is where Delta A !=
  0 is refused (``_switch_reason``); place charged packets after the fields. A far-field (momentum) pattern next to
  a flux must be read in kinetic momentum, e.g. after the gauge transformation that removes A where the wave is (the
  tube's A ~ Phi/(2 pi r) still shifts the canonical momentum by 5 % in the tests' double slit). The fields of a
  2-D scene vary in the plane; the out-of-plane variation Maxwell's equations then require (e.g. B_y = G z for
  B_z = B0 + G y) is not felt by a wave confined to the plane: exact for uniform fields, a thin-beam approximation
  otherwise (stated). The edges of a confined gradient field model the
  magnet's fringe field (there div B = B . grad f need not vanish). ``FluxTube``: an Aharonov-Bohm tube
  (``schrodinger_nd.flux_tube``: Gaussian field profile, symmetric gauge outside), its field
  B = Phi/(pi R^2) exp(-r^2/R^2) also couples to a spin.
* **Detectors**: ``Detector`` = a complex absorbing potential W = W0 x (box profile) of a stated strength and edge;
  ``EdgeLayers``: the window's open edges, W0 (s/width)^power (``schrodinger_nd.absorbing_layer``). The probability W
  removes is accumulated per point (``SplitOperator.track_absorbed``) and attributed to the detectors in proportion
  W_k / W_total at each point (exact in the limit dt -> 0, d P_k/dt = 2 int W_k |psi|^2; the scheme's total is exact);
  at every change of W the attribution so far is banked. So per particle norm + sum_k absorbed_k = 1 to round-off.
  Reflection of a detector's face and leak through it: stationary 1-D transfer matrices of its profile
  (``Detector.reflection``, as ``schrodinger_nd.layer_reflection`` for the edge layers, ``Scene.edge_reflection``).
* **The grid's resolution** (``_resolution_reason``, review B6-Q4): a packet is admitted when |k_i| + 6 sigma_k,i <=
  pi/d_i (free motion is exact inside the band). Next to anything that acts on it the wave's largest wavenumber,
  K = |k| + 6 sigma_k (``k_spread``: widened by every measurement and jump) raised by the potential energy it can
  convert, K_loc = sqrt(K^2 + 2 m dV), must stay within 2/3 of the band: the product V psi carries the wavenumbers of
  both, and what passes pi/d is aliased into the band (the 2/3 rule of pseudo-spectral products; measured on a 4-nm
  well: the transmission against a grid twice as fine errs by 6e-7 at K_loc d = 1.78, 1.5e-4 at 2.11, 7.4e-2 at
  3.10). Checked at every change of the set-up, for every new packet and (with the measurement's widening) before a
  measurement; jumps of an environment widen the spectrum as the run goes (one jump is included at its admission).
* **Measurement** (``Scene.measure``): an unsharp position measurement of resolution s, Kraus operators
      K_x = (2 pi s^2)^(-d/4) exp(-|r - x|^2 / (4 s^2)),   int K_x^dag K_x d^d x = 1 (a POVM),
  outcome density p(x) = ||K_x psi||^2 = (|psi|^2 * N(0, s^2))(x). On the grid p(x) = sum_i rho_i dV G_s(x - r_i)
  (the trapezoidal rule of the convolution: for a band-limited density its error is of the order
  exp(-2 pi^2 s^2 / d^2), 2.7e-9 at s = d, so s >= max d is required, and s >= ``measure_min_sigma``: the
  post-measurement wave, its spectrum widened by 1/(4 s^2) in variance, must pass the resolution rule above); it is
  sampled exactly as x = r_i + s xi with
  cell i drawn with probability rho_i dV / N and xi ~ N(0, I) (or r = ``at`` given by the caller, e.g. a Bohm
  particle's position, which is |psi|^2-distributed by equivariance); then psi -> K_x psi / ||K_x psi||. A particle is
  a mixture "absorbed by detector k" (probability A_k) or "in flight" (probability N, the norm): the outcome
  "absorbed by k" is drawn with probability A_k (the particle is then gone), the position outcome with probability N;
  either way the record is conditioned on the outcome (norm 1 and nothing absorbed, or norm 0 and A_k = 1).
* **Decoherence** (``Localization``): an environment that localizes the particle, the Lindblad family
      L_y = sqrt(lambda chi(y)) (pi a^2)^(-d/4) exp(-|r - y|^2 / (2 a^2)),   y over all space,
  rate lambda, length a, region chi (a box profile, or everywhere): d rho(r, r')/dt = -i[H, rho](r, r') +
  [lambda K(r, r') - (Gamma(r) + Gamma(r'))/2] rho(r, r'), K(r, r') = int chi(y) L_y(r) L_y(r') dy / lambda =
  exp(-|r - r'|^2/(4 a^2)) chi~((r + r')/2), Gamma(r) = lambda chi~(r), chi~ the region blurred once more (edge
  eps^2 + a^2); everywhere (chi = 1) this is the GRW form lambda [1 - exp(-|r - r'|^2/(4 a^2))] (Bassi et al. 2013).
  Unravelled exactly as quantum jumps in the waiting-time form (Dalibard, Castin & Moelmer 1992; Plenio & Knight 1998):
  between jumps the no-jump evolution with H - i Gamma/2 (Gamma enters W next to the detectors), the probability of
  no jump is exp(-int <Gamma>) with <Gamma> = int Gamma |psi|^2 / N (the detectors' loss is kept apart: the step's
  loss at each point is split by W_k : Gamma/2, the norm is restored for the Gamma part only), a jump when the
  integrated hazard reaches -ln r (r uniform); the step in which it happens is redone as half step, jump, half step
  (the jump at the step's midpoint: the timing error is symmetric, so the bias of averages is second order in dt);
  the jump position y ~ |psi|^2 * N(0, a^2/2) (x chi(y) by rejection), psi -> L_y psi rescaled to its norm. The
  number of jumps in a step is the number of thresholds E_1, E_1 + E_2, ... (E_i ~ Exp(1)) its integrated hazard
  crosses (Poisson(lambda dt) for a uniform rate), all placed at the midpoint; in a region the hazard of a step with
  several jumps is that of its no-jump evolution (an error O((lambda dt)^2) per step), so lambda dt <=
  ``LOC_MAX_STEP`` = 0.05 is required. One environment per scene.
* **Which-path marker** (``PathMarker``): a two-level marker (Englert's detector, as v11 and ``marks``) that turns
  while the particle is in a region: b = c f(r) e_y on the marker's two components (|0> -> cos|0> + sin|1>). It uses
  the wave's second component, so it cannot be combined with a spin that needs a spinor (a spin-1/2 particle in a field
  that is not along one fixed direction, or with a spin that is not an eigenstate of it): refused with the reason.
* **Particles** (``Packet``): Gaussian packets (centre, wavevector k, spreads sigma_i of |psi|^2; an axis may be
  unbounded, sigma = inf with k_i = 0) of a ``Species`` (``species``: electron, neutron, 4He, C60, any atom by its
  mass, with charge and signed magnetic moment from CODATA via scipy.constants). A charged packet in a vector
  potential carries the gauge factor exp(i q Lambda), Lambda the line integral of A from its centre
  (``VectorPotential.gauge``), so its kinetic momentum is k. A spin-1/2 particle keeps a scalar wave while its spin
  factorizes exactly (no spin field, or all fields along one fixed direction n with the spin an eigenstate of n.sigma:
  then V gains -mu s B_n); otherwise it becomes a spinor psi_c = chi_c psi (exact, at the moment of the change).
* **Invariants and errors** (``Scene.checks``): per particle norm + absorbed = 1; <H> of a closed system against its
  value at the last change, with the bound 2 ||H psi|| e + e^2 ||H|| from the time-step error estimate e; the
  probability flux through a plane (8th- or 16th-order centred differences) integrated in time (trapezoid) against the
  change of the probability beyond the plane (trapezoid with the Euler-Maclaurin end correction d^2/12 d rho/dn);
  the time step by a companion (``Scene.step_error``): one step dt against two steps dt/2, local error
  (4/3) ||psi_dt - psi_dt/2|| (Strang: C dt^3 against C dt^3/4), accumulated over the steps since by the trapezoid;
  for a contraction (unitary or absorbing) the sum of the true local errors bounds the global error, so the
  accumulated estimate is a leading-order estimate of a bound, as good as its sampling (review B6-Q7: sampled only
  before and after a wall interaction it fell three times below the true error); ``error_every`` takes an estimate
  every that many steps of each particle, independent of who reads the checks, and the energy bound is a bound given
  that estimate. The grid's resolution: the probability in the outer third of k-space; the density at the window's
  faces (the periodic wrap).
* **Bohm trajectories** live in ``theories.interpretations.bohm`` (an interpretation, outside the core); the scene
  gives what they need: ``advance(n, snapshots=True)`` keeps psi at t, t + n dt/2, t + n dt per particle
  (``snapshots``), and ``guidance`` gives the grid, the Hamiltonian (for A) and the array module.
* **Live changes in the same world** (plan P16.1, P16.2; LB1, 2026-11-11). ``regrid``: a new grid (points and step) or
  window at the current moment; every wave resampled exactly as the band-limited function its grid holds
  (``schrodinger_nd.resample``: the same window — Fourier zero padding or truncation; the same step — the samples, zeros
  beyond; both — the trigonometric interpolant evaluated at the new points), refused with the measured fraction where
  more than ``REGRID_TOL`` = 1e-6 of a particle's norm would be dropped (the spectrum beyond a coarser band, the
  probability outside a smaller window) or misplaced (the probability in the ``FACE_CELLS`` outermost cells a larger
  window pads: the periodic grid continues it on the other side); the objects keep their physical parameters (an edge
  the new grid cannot resolve is refused), what was dropped is banked as "regrid" (norm + absorbed = 1 stays exact),
  the report gives the norm and <H> before and after. ``transform_particle`` (``move_particle``, ``boost_particle``): a
  particle's wave prepared anew as the same wave moved, psi(r - s) (with the gauge factor that keeps a charged
  particle's kinetic momentum in a vector potential: the magnetic translation), and/or given a momentum,
  exp(i dk.r) psi; refused where the move would carry more than ``REGRID_TOL`` across a periodic face or the boost
  would alias. ``observables``: a particle's norm, <r>, <p - qA>/hbar and <H> from one FFT (the instruments). Every
  object's arrays are kept by its parameters (``_on_grid``, at most ``OBJ_CACHE_DOUBLES`` per grid point): a change that
  moves one object evaluates that object alone.
* **State**: ``state_dict`` / ``Scene.from_state_dict``: plain data (the objects' parameters, the waves and the
  absorbed records as NumPy arrays, the random generator's state); the continuation is bit-identical.
* **Cost** (``cost_estimate``): seconds per step from measured rates on the CPU and on GPU 0 (kernel
  "quantum.split_operator"), with the running measured speed.

Units: hbar = 1, lengths in ``Units.length`` (m), masses in ``Units.mass`` (kg); time M L^2/hbar, energy
hbar^2/(M L^2), magnetic field hbar/(e L^2) (so the flux quantum h/e is 2 pi), magnetic moment e hbar/M; charges in
elementary charges.
"""

from __future__ import annotations

import copy
import dataclasses
import math
import time
from dataclasses import dataclass, field

import numpy as np
from scipy import constants as sc
from scipy import special

from lfphys.codes import coded
from lfphys.i18n import T, text_of

from .. import backend
from . import particles as PT
from . import schrodinger_nd as S

ABOUT = {
    "layer": "core", "kind": "law",
    "title": T("Quantum scene: particles as packets, potentials, fields, detectors, measurements and decoherence in "
               "2-D/3-D"),
    "statement": T("Every particle is its own wave packet under the Schrödinger or the Pauli equation (the particles "
                   "do not interact); a common potential of shapes with smooth edges (the edge width is a physical "
                   "length), magnetic fields (the Landau gauge for a uniform field in a region, an Aharonov–Bohm "
                   "tube, spin through the magnetic moment), absorbing detectors with the absorbed probability "
                   "accounted for (norm + absorbed = 1), unsharp position measurement (Gaussian Kraus operators), "
                   "localisation by an environment (the Lindblad equation) by quantum jumps, a which-path mark; "
                   "checks: the energy of a closed system, the flux through a plane, the time-step error."),
    "validity": T("a non-relativistic particle (spin ½ after Pauli), no interaction between the particles; the grid "
                  "finer than the wavelength and the shapes' edges (edges narrower than 3 grid steps are refused; next "
                  "to a potential the particle's wavenumbers stay within 2/3 of the grid's band), a window with "
                  "absorbers at its edges (a charged particle in a field only with open edges); in 2-D the field "
                  "varies only in the plane (the out-of-plane variation Maxwell's equations require is not included: "
                  "exact for uniform fields); a Markovian environment; the time-step error is of second order, "
                  "estimated in the run"),
    "basis": ["Schrödinger 1926; Pauli 1927",
              T("Feit, Fleck, Steiger, J. Comput. Phys. 47, 412 (1982) — split-operator method"),
              "Aharonov & Bohm, Phys. Rev. 115, 485 (1959)",
              T("Jacobs & Steck, Contemp. Phys. 47, 279 (2006), arXiv:quant-ph/0611067 — Gaussian position "
                "measurement"),
              T("Dalibard, Castin, Mølmer, PRL 68, 580 (1992); Plenio & Knight, Rev. Mod. Phys. 70, 101 (1998) — "
                "quantum jumps"),
              T("Bassi et al., Rev. Mod. Phys. 85, 471 (2013) — Gaussian localisation operators"),
              T("CODATA 2022 (scipy.constants) — masses and magnetic moments"),
              T("lfphys/sources/verification_2026-11-03_p15_3.md — check of the quotations and derivations")],
    "conflicts": [],
}

ERF80 = float(special.erfinv(0.8))  # S(u) rises from 0.1 to 0.9 over u in [-eps erfinv(0.8), +eps erfinv(0.8)]
EDGE_TOL = 1e-3                     # the edge's spectrum at the grid's largest wavenumber, relative to the step
EDGE_STEPS = 4.0 * ERF80 / math.pi * math.sqrt(math.log(1.0 / EDGE_TOL))  # = 3.03: w_min / d
LOC_MAX_STEP = 0.05                 # lambda dt: at most one localization jump per step (P(2 or more) < 1.3e-3)
LOC_MIN_STEPS = 1.5                 # a >= 1.5 d: the jump's Gaussian is resolved (quadrature error exp(-pi^2 a^2/d^2))
PACKET_NYQUIST = 6.0                # |k_i| + 6 sigma_k,i <= pi/d_i (sigma_k = 1/(2 sigma)): |phi(k)|^2 < 1.5e-8 there
PACKET_TAIL = 1e-12                 # |psi|^2 at the window's faces relative to the peak (the grid is periodic)
INTERACT_BAND = 2.0 / 3.0           # next to a potential a wave's wavenumbers (6 sigma) must stay below 2/3 pi/d: the
                                    # product V psi on the grid aliases beyond (review B6-Q4: measured, module docstring)
BALL_MIN = math.sqrt(math.log(1.0 / EDGE_TOL)) / (2.0 * ERF80)  # = 1.45: R >= 1.45 edge (no kink at a ball's centre)
SPLIT_LOCAL = 4.0 / 3.0             # one Strang step dt against two dt/2: local error = (4/3) ||difference||
BALANCE_EPS = 32                    # |norm + absorbed - 1| <= 32 eps per step (measured: see the tests)
REGRID_TOL = 1e-6                   # a live change of the grid, the window or a wave's place may drop or misplace at most
                                    # this fraction of a particle's norm (the spectrum beyond a coarser band, the
                                    # probability outside a smaller window, the wave at a face a padding or a move meets)
FACE_CELLS = 4                      # the old window's outermost cells whose probability a larger window's padding meets
SPECTRUM_TAIL = 1e-3                # a boosted wave's model (``_spec_model``): its core reaches K where |k| > K holds this
                                    # fraction (a Gaussian's |k| + 3.09 sigma_k; the rule then takes 6 sigma_k as for a packet)
OBJ_CACHE_DOUBLES = 8               # the objects' arrays kept between changes (``Scene._on_grid``): at most this many
                                    # doubles per grid point; beyond, an object is evaluated at every change
EPS = float(np.finfo(float).eps)
#: where a carried-over wave loses its norm (``Scene.adopt_wave``), in words
_LOSS = {"spectrum": T("beyond the grid's band"), "outside": T("outside the window"),
         "face": T("at the window's faces")}
#: the machine code (``lfphys.codes``) of a refused live change by its ``what`` (``Scene._refusal``)
_WHAT_CODES = {"resolution": "qscene.resolution", "dim": "qscene.regrid_dimension", "kind": "qscene.regrid_kind",
               "spectrum": "qscene.regrid_loss", "outside": "qscene.regrid_loss", "face": "qscene.regrid_loss",
               "layers": "qscene.layers", "no_wave": "qscene.no_wave", "wrap": "qscene.wrap", "alias": "qscene.alias"}

# Measured seconds per scene step of one particle (2026-11-03, image lfphys-viz, fp64, absorbing edges on, the
# state kept on the device, timed over >= 0.6 s with a norm (a host sync) at the end): CPU of the container (numpy's
# pocketfft), GPU 0 = RTX 2080 Ti (CuPy). Keys (device, dimension, kind), kind "scalar" | "spinor" (spin or marker) |
# "scalar_A" | "spinor_A" (a charged particle in a vector potential: per-axis FFTs and gauge phases); values
# [(points, seconds per step)]: 2-D at 256^2 and 512^2, 3-D at 64^3.
RATES = {
    ("cpu", 2, "scalar"): [(65536, 2.53e-3), (262144, 9.86e-3)],
    ("cpu", 2, "spinor"): [(65536, 6.11e-3), (262144, 2.43e-2)],
    ("cpu", 2, "scalar_A"): [(65536, 2.89e-3), (262144, 1.49e-2)],
    ("cpu", 2, "spinor_A"): [(65536, 9.08e-3), (262144, 3.88e-2)],
    ("cpu", 3, "scalar"): [(262144, 1.02e-2)],
    ("cpu", 3, "spinor"): [(262144, 2.77e-2)],
    ("cpu", 3, "scalar_A"): [(262144, 2.10e-2)],
    ("cpu", 3, "spinor_A"): [(262144, 5.58e-2)],
    ("gpu", 2, "scalar"): [(65536, 2.18e-4), (262144, 4.97e-4)],
    ("gpu", 2, "spinor"): [(65536, 4.79e-4), (262144, 1.14e-3)],
    ("gpu", 2, "scalar_A"): [(65536, 4.53e-4), (262144, 8.22e-4)],
    ("gpu", 2, "spinor_A"): [(65536, 7.19e-4), (262144, 1.97e-3)],
    ("gpu", 3, "scalar"): [(262144, 3.90e-4)],
    ("gpu", 3, "spinor"): [(262144, 1.12e-3)],
    ("gpu", 3, "scalar_A"): [(262144, 1.12e-3)],
    ("gpu", 3, "spinor_A"): [(262144, 2.61e-3)],
}
RATES_NOTE = T("an estimate from the measured rates (see RATES); the measured speed of this run is more accurate")


# --- units and species ---------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Units:
    """The scene's units: hbar = 1, a length (m) and a mass (kg); charges in e."""

    length: float = 1e-9
    mass: float = sc.m_e

    @property
    def time(self) -> float:
        """Seconds per unit of time, M L^2 / hbar."""
        return self.mass * self.length**2 / sc.hbar

    @property
    def energy(self) -> float:
        """Joules per unit of energy, hbar^2 / (M L^2)."""
        return sc.hbar**2 / (self.mass * self.length**2)

    @property
    def field(self) -> float:
        """Tesla per unit of magnetic field, hbar / (e L^2): q B in units of hbar / L^2 per elementary charge."""
        return sc.hbar / (sc.e * self.length**2)

    @property
    def moment(self) -> float:
        """J/T per unit of magnetic moment, (energy unit) / (field unit) = e hbar / M."""
        return sc.e * sc.hbar / self.mass

    def k_of_wavelength(self, wavelength_m: float) -> float:
        """The wavenumber 2 pi / lambda in units of 1/L."""
        return 2.0 * math.pi * self.length / float(wavelength_m)

    def params(self) -> dict:
        return {"length": float(self.length), "mass": float(self.mass)}


@dataclass(frozen=True)
class Species:
    """A particle species in the scene's units: mass, charge (in e), signed magnetic moment mu (the spin's coupling
    is H = -mu B . sigma; mu < 0 for the electron and the neutron) and whether it has spin 1/2."""

    name: str
    mass: float
    charge: float = 0.0
    moment: float = 0.0
    spin_half: bool = False

    def params(self) -> dict:
        return dataclasses.asdict(self)


def species(name: str, units: Units | None = None, mass_u: float | None = None, charge_e: float = 0.0,
            moment_muB: float | None = None) -> Species:
    """A species in the units ``units``: "electron" (m_e, -e, mu_e; CODATA), "neutron" (m_n, 0, mu_n), "he4" (the 4He
    atom, spin 0), "c60", or "atom" / "custom" with ``mass_u`` (u), ``charge_e`` and, for a spin-1/2 particle, its
    moment ``moment_muB`` in Bohr magnetons (signed: positive when the moment is along the spin)."""
    u = units or Units()
    if name == "electron":
        return Species("electron", sc.m_e / u.mass, -1.0,
                       sc.physical_constants["electron mag. mom."][0] / u.moment, True)
    if name == "neutron":
        return Species("neutron", sc.m_n / u.mass, 0.0,
                       sc.physical_constants["neutron mag. mom."][0] / u.moment, True)
    if name in ("he4", "c60"):
        return Species(name, PT.SPECIES[name][1] / u.mass, 0.0, 0.0, False)
    if name in ("atom", "custom"):
        if mass_u is None or mass_u <= 0:
            raise ValueError(T("particle: give the mass in u (> 0)"))
        mom = 0.0 if moment_muB is None else float(moment_muB) * sc.physical_constants["Bohr magneton"][0] / u.moment
        return Species(name, float(mass_u) * PT.U / u.mass, float(charge_e), mom, moment_muB is not None)
    raise ValueError(T("unknown particle {name}: electron, neutron, he4, c60, atom, custom", name=repr(name)))


# --- smooth profiles -------------------------------------------------------------------------------------------------
def edge_eps(w: float) -> float:
    """eps of the error-function step whose 10 %-90 % rise distance is w."""
    return float(w) / (2.0 * ERF80)


def edge_min(d: float, tol: float = EDGE_TOL) -> float:
    """The narrowest edge a grid of step d resolves: exp(-pi^2 eps^2 / (4 d^2)) = tol at its Nyquist wavenumber."""
    return 4.0 * ERF80 / math.pi * math.sqrt(math.log(1.0 / tol)) * float(d)


def edge_spectrum(w: float, k) -> np.ndarray:
    """|Fourier transform| of the step's derivative S'(u) at wavenumber k, relative to k = 0: exp(-k^2 eps^2/4)."""
    e = edge_eps(w)
    return np.exp(-(np.asarray(k, float) * e) ** 2 / 4.0)


def smooth_step(u, w: float) -> np.ndarray:
    """S(u) = (1 + erf(u/eps))/2 = erfc(-u/eps)/2: 0 -> 1, 0.1 at u = -w/2 and 0.9 at u = +w/2."""
    return 0.5 * special.erfc(-np.asarray(u, float) / edge_eps(w))


def smooth_interval(x, lo, hi, w: float) -> np.ndarray:
    """The Gaussian blur of the indicator of [lo, hi] (either end may be None or infinite):
    [erfc((x - hi)/eps) - erfc((x - lo)/eps)] / 2, evaluated in the form without cancellation on each side."""
    x = np.asarray(x, float)
    lo = -np.inf if lo is None else float(lo)
    hi = np.inf if hi is None else float(hi)
    if lo == -np.inf and hi == np.inf:
        return np.ones_like(x)
    e = edge_eps(w)
    with np.errstate(invalid="ignore"):
        right = 0.5 * (special.erfc((x - hi) / e) - special.erfc((x - lo) / e))   # accurate for x beyond the middle
        left = 0.5 * (special.erfc((lo - x) / e) - special.erfc((hi - x) / e))    # accurate below it
    if lo == -np.inf:
        return right
    if hi == np.inf:
        return left
    return np.where(x >= 0.5 * (lo + hi), right, left)


def ramp_integral(u, w: float) -> np.ndarray:
    """J(u) = int_{-inf}^{u} S(s) ds = [u erfc(-u/eps) + eps exp(-u^2/eps^2)/sqrt(pi)] / 2."""
    u = np.asarray(u, float)
    e = edge_eps(w)
    return 0.5 * (u * special.erfc(-u / e) + e * np.exp(-(u / e) ** 2) / math.sqrt(math.pi))


def _box_profile(grid: S.Grid, lo, hi, w) -> np.ndarray:
    """prod_i smooth_interval(x_i, lo_i, hi_i, w) on the grid (separable: evaluated on the axes, then multiplied)."""
    X = grid.mesh()
    out = 1.0
    for i in range(grid.ndim):
        a, b = lo[i], hi[i]
        if (a is None or a == -np.inf) and (b is None or b == np.inf):
            continue
        out = out * smooth_interval(X[i], a, b, w)
    return np.broadcast_to(np.asarray(out, float), grid.shape).copy()


def _finite(v) -> bool:
    return v is not None and math.isfinite(float(v))


def _vec(v, n: int, what: T) -> list:
    """A vector of n entries (a scalar is broadcast); None entries kept (unbounded)."""
    if v is None:
        return [None] * n
    if np.isscalar(v):
        return [float(v)] * n
    v = list(v)
    if len(v) != n:
        raise ValueError(T("{what}: {n} components needed, {m} given", what=what, n=int(n), m=len(v)))
    return [None if x is None else float(x) for x in v]


def _arg(v):
    """A value as an argument of a text: a plain number as it is (the player formats it), anything else as a string."""
    if isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, float, np.integer, np.floating)):
        return str(v)
    return v.item() if isinstance(v, (np.integer, np.floating)) else v


def _list_text(items):
    """Texts joined by commas, as one translatable text."""
    out = ""
    for x in items:
        out = x if out == "" else T("{a}, {b}", a=out, b=x)
    return out


def _check_edge(w, d, what: T):
    if w is None or not (float(w) > 0):
        raise ValueError(T("{what}: the edge width (10–90 %) must be given and > 0 — it is a physical length, not the "
                           "grid step", what=what))
    wmin = edge_min(d)
    if float(w) < wmin * (1 - 1e-12):
        raise ValueError(T("{what}: the edge {w:.4g} is narrower than a grid of step {d:.4g} can resolve (it needs ≥ "
                           "{wmin:.4g} = {steps:.2f} steps: the edge's spectrum exp(−k²ε²/4) at k = π/d must be ≤ "
                           "{tol}); make the edge wider or the grid finer",
                           what=what, w=float(w), d=float(d), wmin=float(wmin), steps=float(EDGE_STEPS),
                           tol=float(EDGE_TOL)))


# --- objects -----------------------------------------------------------------------------------------------------------
class SceneObject:
    """Base of the scene's objects: ``params()`` plain data, ``from_params`` back, ``check(scene)`` raises ValueError
    with the reason when the object does not fit the scene, ``bbox(ndim)`` (lo, hi) for drawing."""

    TYPE = ""
    NAME = None  # the object kind in words (a translatable text) for the scene's events

    def params(self) -> dict:
        def plain(v):
            if isinstance(v, (list, tuple)):
                return [plain(x) for x in v]
            if isinstance(v, (np.floating, np.integer)):
                return v.item()
            return v
        return {f.name: plain(getattr(self, f.name)) for f in dataclasses.fields(self)}

    @classmethod
    def from_params(cls, d: dict):
        return cls(**d)

    def check(self, scene: "Scene"):
        pass

    def bbox(self, ndim: int):
        return np.full(ndim, -np.inf), np.full(ndim, np.inf)


class Shape(SceneObject):
    """A potential: ``V(grid)`` the potential energy (or, with coupling "charge", the electrostatic potential in
    energy per elementary charge, acting as q V)."""

    def V(self, grid: S.Grid) -> np.ndarray:
        raise NotImplementedError

    def _check_coupling(self):
        if getattr(self, "coupling", "energy") not in ("energy", "charge"):
            raise ValueError(T("shape coupling: 'energy' (for every particle) or 'charge' (through the charge q)"))

    def peak(self, ndim: int):
        """The extremum of V in closed form (a shape narrower than its edges does not reach its nominal height:
        review B6-Q14), or None where V has none (a trap)."""
        return None


@dataclass
class Box(Shape):
    """A box barrier (height > 0) or well (height < 0): height x prod_i blur(1_[c_i - s_i/2, c_i + s_i/2]) (a size
    None or inf: unbounded along that axis)."""

    center: list
    size: list
    height: float
    edge: float
    coupling: str = "energy"
    TYPE = "box"
    NAME = T("a box")

    def _lohi(self, n):
        c, s = _vec(self.center, n, T("centre")), _vec(self.size, n, T("size"))
        lo = [None if (s[i] is None or not math.isfinite(s[i])) else c[i] - 0.5 * s[i] for i in range(n)]
        hi = [None if (s[i] is None or not math.isfinite(s[i])) else c[i] + 0.5 * s[i] for i in range(n)]
        return lo, hi

    def check(self, scene):
        self._check_coupling()
        lo, hi = self._lohi(scene.ndim)
        for i in range(scene.ndim):
            if lo[i] is not None:
                if not hi[i] > lo[i]:
                    raise ValueError(T("box: the size must be > 0"))
                _check_edge(self.edge, scene.grid.d[i], T("box"))

    def V(self, grid):
        lo, hi = self._lohi(grid.ndim)
        return float(self.height) * _box_profile(grid, lo, hi, self.edge)

    def peak(self, ndim):
        """height x prod_i erf(s_i / (2 eps)): the blur of the box at its centre."""
        lo, hi = self._lohi(ndim)
        f = 1.0
        for a, b in zip(lo, hi):
            if a is not None:
                f *= math.erf((b - a) / (2 * edge_eps(self.edge)))
        return float(self.height) * f

    def bbox(self, ndim):
        lo, hi = self._lohi(ndim)
        return (np.array([-np.inf if a is None else a for a in lo]), np.array([np.inf if b is None else b for b in hi]))


@dataclass
class Ball(Shape):
    """A disk (2-D), sphere (3-D) or, with ``axes`` a subset, a cylinder: height x S(R - |r - c|) over those axes."""

    center: list
    radius: float
    height: float
    edge: float
    axes: list | None = None
    coupling: str = "energy"
    TYPE = "ball"
    NAME = T("a ball")

    def _axes(self, n):
        return list(range(n)) if self.axes is None else [int(a) for a in self.axes]

    def check(self, scene):
        self._check_coupling()
        if not float(self.radius) > 0:
            raise ValueError(T("ball: the radius must be > 0"))
        ax = self._axes(scene.ndim)
        _check_edge(self.edge, max(scene.grid.d[a] for a in ax), T("ball"))
        _vec(self.center, scene.ndim, T("centre"))
        if float(self.radius) < BALL_MIN * float(self.edge) * (1 - 1e-12):
            # S(R - |r|) has a kink at r = 0 of slope exp(-R^2/eps^2) relative to the edge's steepest: a cone whose
            # spectrum the grid cannot hold (review B6-Q14); the edge rule's EDGE_TOL bounds it
            raise ValueError(T("ball: the radius {r:.4g} is less than {k:.2f} edge widths {w:.4g}: the profile has a "
                               "kink at the centre (a cone, slope {slope:.2g} of the steepest) and does not reach the "
                               "height (only {frac:.3g} of it); make the ball larger or the edge narrower (the grid "
                               "finer)",
                               r=float(self.radius), k=float(BALL_MIN), w=float(self.edge),
                               slope=math.exp(-(float(self.radius) / edge_eps(self.edge)) ** 2),
                               frac=0.5 * math.erfc(-float(self.radius) / edge_eps(self.edge))))

    def peak(self, ndim):
        """height x S(R): the radial step at the centre."""
        return float(self.height) * 0.5 * math.erfc(-float(self.radius) / edge_eps(self.edge))

    def V(self, grid):
        c = _vec(self.center, grid.ndim, T("centre"))
        X = grid.mesh()
        r2 = 0.0
        for a in self._axes(grid.ndim):
            r2 = r2 + (X[a] - c[a]) ** 2
        r = np.sqrt(np.broadcast_to(r2, grid.shape))
        return float(self.height) * smooth_step(float(self.radius) - r, self.edge)

    def bbox(self, ndim):
        c = np.array(_vec(self.center, ndim, T("centre")), float)
        lo, hi = np.full(ndim, -np.inf), np.full(ndim, np.inf)
        for a in self._axes(ndim):
            lo[a], hi[a] = c[a] - self.radius, c[a] + self.radius
        return lo, hi


@dataclass
class Step(Shape):
    """A potential step: height x S(x_axis - position)."""

    axis: int
    position: float
    height: float
    edge: float
    coupling: str = "energy"
    TYPE = "step"
    NAME = T("a potential step")

    def check(self, scene):
        self._check_coupling()
        if not 0 <= int(self.axis) < scene.ndim:
            raise ValueError(T("potential step: no such axis"))
        _check_edge(self.edge, scene.grid.d[int(self.axis)], T("potential step"))

    def V(self, grid):
        X = grid.mesh()
        return np.broadcast_to(float(self.height) * smooth_step(X[int(self.axis)] - float(self.position), self.edge),
                               grid.shape).copy()

    def peak(self, ndim):
        return float(self.height)

    def bbox(self, ndim):
        lo, hi = np.full(ndim, -np.inf), np.full(ndim, np.inf)
        lo[int(self.axis)] = self.position
        return lo, hi


@dataclass
class SlitWall(Shape):
    """A wall normal to ``axis`` (mid-plane at ``position``, ``thickness``, ``height``) with slits [[centre, width],
    ...] along the transverse axis ``along`` (default: the next axis); in 3-D a slit runs through the window along the
    remaining axis, or has ``length`` = [centre, length] there. V = height blur(slab)(x_n) (1 - sum_j blur(hole_j)):
    the exact Gaussian blur of the sharp wall (holes must not overlap)."""

    axis: int
    position: float
    thickness: float
    height: float
    slits: list
    edge: float
    along: int | None = None
    length: list | None = None
    coupling: str = "energy"
    TYPE = "slit_wall"
    NAME = T("a wall with slits")

    def _along(self, n):
        if self.along is not None:
            return int(self.along)
        return (int(self.axis) + 1) % n

    def _third(self, n):
        rest = [a for a in range(n) if a not in (int(self.axis), self._along(n))]
        return rest[0] if rest else None

    def check(self, scene):
        self._check_coupling()
        n = scene.ndim
        if n < 2:
            raise ValueError(T("wall with slits: needs a 2-D or 3-D grid"))
        ax, al = int(self.axis), self._along(n)
        if not (0 <= ax < n and 0 <= al < n and ax != al):
            raise ValueError(T("wall with slits: the wall's axis and the slits' axis must be different grid axes"))
        if not float(self.thickness) > 0:
            raise ValueError(T("wall with slits: the thickness must be > 0"))
        _check_edge(self.edge, scene.grid.d[ax], T("wall (across)"))
        _check_edge(self.edge, scene.grid.d[al], T("slits (along the wall)"))
        sl = sorted((float(c), float(w)) for c, w in self.slits)
        for c, w in sl:
            if not w > 0:
                raise ValueError(T("slit: the width must be > 0"))
        for (c1, w1), (c2, w2) in zip(sl, sl[1:]):
            if c2 - 0.5 * w2 < c1 + 0.5 * w1:
                raise ValueError(T("the slits overlap: the distance between centres must exceed the half-sum of the "
                                   "widths"))
        if self.length is not None:
            if n != 3:
                raise ValueError(T("the slits' length is set only in 3-D"))
            _check_edge(self.edge, scene.grid.d[self._third(n)], T("slits (along their length)"))
            if not float(self.length[1]) > 0:
                raise ValueError(T("the slit length must be > 0"))

    def V(self, grid):
        n = grid.ndim
        X = grid.mesh()
        ax, al = int(self.axis), self._along(n)
        t = 0.5 * float(self.thickness)
        slab = smooth_interval(X[ax], self.position - t, self.position + t, self.edge)
        holes = 0.0
        for c, w in self.slits:
            h = smooth_interval(X[al], float(c) - 0.5 * float(w), float(c) + 0.5 * float(w), self.edge)
            if self.length is not None:
                lc, ll = float(self.length[0]), float(self.length[1])
                h = h * smooth_interval(X[self._third(n)], lc - 0.5 * ll, lc + 0.5 * ll, self.edge)
            holes = holes + h
        return np.broadcast_to(float(self.height) * slab * (1.0 - holes), grid.shape).copy()

    def bbox(self, ndim):
        lo, hi = np.full(ndim, -np.inf), np.full(ndim, np.inf)
        lo[int(self.axis)] = self.position - 0.5 * self.thickness
        hi[int(self.axis)] = self.position + 0.5 * self.thickness
        return lo, hi

    def peak(self, ndim):
        """height x erf(thickness / (2 eps)): the slab's middle away from the slits."""
        return float(self.height) * math.erf(float(self.thickness) / (2 * edge_eps(self.edge)))

    def openings(self, ndim) -> list:
        """The sharp slits as boxes (lo, hi) for drawing."""
        out = []
        for c, w in self.slits:
            lo, hi = self.bbox(ndim)
            lo[self._along(ndim)], hi[self._along(ndim)] = c - 0.5 * w, c + 0.5 * w
            if self.length is not None:
                k = self._third(ndim)
                lo[k], hi[k] = self.length[0] - 0.5 * self.length[1], self.length[0] + 0.5 * self.length[1]
            out.append((lo, hi))
        return out


@dataclass
class HarmonicTrap(Shape):
    """V = mass sum_i omega_i^2 (x_i - c_i)^2 / 2: frequency omega_i for a particle of ``mass`` (scene units); the
    same potential for every species (for another mass m' the frequency is omega sqrt(mass/m')). omega_i = 0 leaves
    axis i free."""

    center: list
    omega: list
    mass: float = 1.0
    TYPE = "harmonic_trap"
    NAME = T("a harmonic trap")
    coupling = "energy"

    def check(self, scene):
        om = _vec(self.omega, scene.ndim, T("frequency"))
        if any(o is None or o < 0 for o in om) or not float(self.mass) > 0:
            raise ValueError(T("trap: frequencies ≥ 0 and mass > 0"))

    def V(self, grid):
        c, om = _vec(self.center, grid.ndim, T("centre")), _vec(self.omega, grid.ndim, T("frequency"))
        X = grid.mesh()
        v = 0.0
        for i in range(grid.ndim):
            v = v + 0.5 * float(self.mass) * om[i] ** 2 * (X[i] - c[i]) ** 2
        return np.broadcast_to(v, grid.shape).copy()

    def bbox(self, ndim):
        c, om = np.array(_vec(self.center, ndim, T("centre"))), _vec(self.omega, ndim, T("frequency"))
        L = np.array([3.0 / math.sqrt(self.mass * o) if o and o > 0 else np.inf for o in om])
        return c - L, c + L


def _plane_axes(c: int) -> tuple[int, int]:
    """(a, b) with e_a x e_b = e_c."""
    return {2: (0, 1), 0: (1, 2), 1: (2, 0)}[c]


@dataclass
class MagneticField(SceneObject):
    """B(r) = f(r) [B0 + G (r - c)] (module docstring): B0 = ``B`` (Bx, By, Bz), G = ``gradient`` (3 x 3, symmetric,
    traceless) about ``center`` (x, y, z), f the box profile of ``lo``/``hi`` per grid axis (None: unbounded) with edge
    width ``edge``. Couples to spins (b = -mu B); to charges only when uniform and normal to the plane / along a grid
    axis with an unbounded region along it (Landau gauge, the gauge string towards ``string`` x e_a)."""

    B: list
    gradient: list | None = None
    center: list | None = None
    lo: list | None = None
    hi: list | None = None
    edge: float | None = None
    string: int = 1
    TYPE = "magnetic_field"
    NAME = T("a magnetic field")

    def _region(self, n):
        return _vec(self.lo, n, T("field region")), _vec(self.hi, n, T("field region"))

    def _G(self):
        return np.zeros((3, 3)) if self.gradient is None else np.asarray(self.gradient, float).reshape(3, 3)

    def check(self, scene):
        B0 = np.asarray(self.B, float)
        if B0.shape != (3,):
            raise ValueError(T("field: B = (Bx, By, Bz)"))
        G = self._G()
        scale = max(float(np.max(np.abs(G))), 1e-300)
        if np.max(np.abs(G - G.T)) > 1e-12 * scale:
            raise ValueError(T("the field gradient is not symmetric: in vacuum curl B = 0 requires ∂B_i/∂x_j = "
                               "∂B_j/∂x_i"))
        if abs(np.trace(G)) > 1e-12 * scale:
            raise ValueError(T("the trace of the field gradient is not zero: div B = 0 (there are no magnetic "
                               "charges)"))
        lo, hi = self._region(scene.ndim)
        for i in range(scene.ndim):
            if lo[i] is not None and hi[i] is not None and not hi[i] > lo[i]:
                raise ValueError(T("field: the region is empty"))
            if lo[i] is not None or hi[i] is not None:
                _check_edge(self.edge, scene.grid.d[i], T("edge of the field region"))
        if int(self.string) not in (1, -1):
            raise ValueError(T("field: string = +1 or −1"))

    def field(self, grid: S.Grid) -> np.ndarray:
        """B (3, *shape) on the grid (grid axes i < ndim are x, y, z; the others at the centre's coordinate)."""
        n = grid.ndim
        c = np.zeros(3) if self.center is None else np.asarray(self.center, float).reshape(3)
        X = grid.mesh()
        r = [X[i] - c[i] if i < n else 0.0 for i in range(3)]
        lo, hi = self._region(n)
        f = _box_profile(grid, lo, hi, self.edge) if any(v is not None for v in lo + hi) else 1.0
        B0, G = np.asarray(self.B, float), self._G()
        out = np.empty((3,) + grid.shape)
        for j in range(3):
            out[j] = np.broadcast_to((B0[j] + sum(G[j, i] * r[i] for i in range(3))) * f, grid.shape)
        return out

    def orbital_reason(self, ndim: int) -> T | None:
        """None when the orbital coupling (A) is built, else why it is not."""
        B0 = np.asarray(self.B, float)
        if np.any(self._G() != 0):
            return T("for a field with a gradient the orbital coupling of a charge is not built (it needs a vector "
                     "potential out of the plane)")
        nz = np.flatnonzero(B0)
        if len(nz) == 0:
            return None
        if ndim == 1:
            return T("in 1-D there is no orbital coupling (motion across the field is not modelled)")
        if len(nz) > 1:
            return T("the field is not along one grid axis: for a charge only a field along an axis is built")
        c = int(nz[0])
        if ndim == 2 and c != 2:
            return T("in 2-D a charge feels only the field perpendicular to the plane (Bz): a field in the plane "
                     "would take it out of the plane")
        if ndim == 3:
            lo, hi = self._region(3)
            if lo[c] is not None or hi[c] is not None:
                return T("a field bounded along its own direction has div B ≠ 0: for a charge the field region must "
                         "be unbounded along B (a prism)")
        return None

    def vector_potential(self, ndim: int) -> S.VectorPotential | None:
        """The Landau-gauge A of a uniform field (module docstring), None if the field is zero or not supported."""
        if self.orbital_reason(ndim) is not None:
            return None
        B0 = np.asarray(self.B, float)
        nz = np.flatnonzero(B0)
        if len(nz) == 0:
            return None
        c = int(nz[0])
        a, b = _plane_axes(c)
        Bc = float(B0[c])
        lo, hi = self._region(ndim)
        cen = np.zeros(3) if self.center is None else np.asarray(self.center, float).reshape(3)
        w, sgn = self.edge, int(self.string)

        def fn(i, *X):
            if i != b:
                return np.zeros(np.broadcast(*X).shape)
            g = smooth_interval(X[b], lo[b], hi[b], w) if (lo[b] is not None or hi[b] is not None) else 1.0
            if lo[a] is not None and hi[a] is not None:
                F = ramp_integral(X[a] - lo[a], w) - ramp_integral(X[a] - hi[a], w)
                if sgn < 0:
                    F = F - (hi[a] - lo[a])
            elif lo[a] is None and hi[a] is None:
                F = X[a] - cen[a]
            else:
                raise ValueError(T("field for a charge: the region along axis a is bounded on one side only — the "
                                   "flux is infinite"))
            return Bc * g * F
        return S.VectorPotential(fn, T("uniform field B = {B} in a region (Landau gauge)", B=Bc))

    def bbox(self, ndim):
        lo, hi = self._region(ndim)
        return (np.array([-np.inf if v is None else v for v in lo]), np.array([np.inf if v is None else v for v in hi]))


@dataclass
class FluxTube(SceneObject):
    """An Aharonov-Bohm flux tube (``schrodinger_nd.flux_tube``): ``flux`` (units hbar/e; the flux quantum h/e is
    2 pi) along e_a x e_b of grid axes ``axes``, Gaussian field profile of ``radius``; its field
    Phi/(pi R^2) exp(-r^2/R^2) also couples to spins."""

    center: list
    flux: float
    radius: float
    axes: list = field(default_factory=lambda: [0, 1])
    TYPE = "flux_tube"
    NAME = T("a flux tube")

    def check(self, scene):
        if scene.ndim < 2:
            raise ValueError(T("flux tube: needs a 2-D or 3-D grid"))
        a, b = (int(v) for v in self.axes)
        if not (0 <= a < scene.ndim and 0 <= b < scene.ndim and a != b):
            raise ValueError(T("flux tube: two different grid axes"))
        if not float(self.radius) > 0:
            raise ValueError(T("flux tube: radius > 0"))
        if float(self.radius) < 1.5 * max(scene.grid.d[a], scene.grid.d[b]):
            raise ValueError(T("flux tube: the radius {r} is less than 1.5 grid steps — the field in the tube is not "
                               "resolved", r=float(self.radius)))

    def vector_potential(self, ndim) -> S.VectorPotential:
        return S.flux_tube(float(self.flux), tuple(float(v) for v in self.center), float(self.radius),
                           tuple(int(v) for v in self.axes))

    def field(self, grid: S.Grid) -> np.ndarray:
        a, b = (int(v) for v in self.axes)
        X = grid.mesh()
        r2 = (X[a] - self.center[0]) ** 2 + (X[b] - self.center[1]) ** 2
        mag = np.broadcast_to(float(self.flux) / (math.pi * self.radius**2) * np.exp(-r2 / self.radius**2), grid.shape)
        n = np.cross(np.eye(3)[a], np.eye(3)[b])
        return np.stack([n[j] * mag for j in range(3)])

    def bbox(self, ndim):
        lo, hi = np.full(ndim, -np.inf), np.full(ndim, np.inf)
        a, b = (int(v) for v in self.axes)
        for ax, c in ((a, self.center[0]), (b, self.center[1])):
            lo[ax], hi[ax] = c - 3 * self.radius, c + 3 * self.radius
        return lo, hi


@dataclass
class Detector(SceneObject):
    """An absorbing region: W = strength x prod_i blur(1_[lo_i, hi_i]) (None: unbounded), edge width ``edge``."""

    lo: list
    hi: list
    strength: float
    edge: float
    name: str = ""
    TYPE = "detector"
    NAME = T("a detector")

    def check(self, scene):
        if not float(self.strength) > 0:
            raise ValueError(T("detector: absorption strength W0 > 0"))
        lo, hi = _vec(self.lo, scene.ndim, T("detector")), _vec(self.hi, scene.ndim, T("detector"))
        for i in range(scene.ndim):
            if lo[i] is not None and hi[i] is not None and not hi[i] > lo[i]:
                raise ValueError(T("detector: the region is empty"))
            if lo[i] is not None or hi[i] is not None:
                _check_edge(self.edge, scene.grid.d[i], T("detector edge"))

    def W(self, grid):
        return float(self.strength) * _box_profile(grid, _vec(self.lo, grid.ndim, ""), _vec(self.hi, grid.ndim, ""),
                                                   self.edge)

    def reflection(self, k, mass: float, axis: int = 0, slices: int = 4000, strengths=None):
        """(R, T) of a wave with wavenumber k (array) normal to the face across ``axis`` (in through ``lo`` or, if
        unbounded there, through ``hi``): stationary 1-D transfer matrices (``transfer.staircase_transmission``, the
        route of ``transfer.transmission_profile``) of the complex potential -i W along that axis; T is the leak
        through the detector, 1 - R - T is absorbed. ``strengths`` (array): the same profile at each of these W0 at
        once, results (len(strengths), len(k)) (review UX-ui U3: the playground picks the strength from a set)."""
        from .transfer import staircase_transmission
        n = max(axis + 1, len(self.lo))
        lo, hi = _vec(self.lo, n, ""), _vec(self.hi, n, "")
        a, b = lo[axis], hi[axis]
        k = np.atleast_1d(np.asarray(k, float))
        E = k**2 / (2 * mass)
        e = edge_eps(self.edge)
        if a is None and b is None:
            raise ValueError(T("the detector is unbounded along this axis: it has no face"))
        if a is None:  # entered through hi from above: mirror
            a, b = -b, np.inf
        x0 = a - 6 * e
        x1 = (b + 6 * e) if b is not None and math.isfinite(b) else a + 6 * e
        edges = np.linspace(x0, x1, slices + 1)
        xs = np.concatenate([[x0 - 1.0], 0.5 * (edges[1:] + edges[:-1]), [x1 + 1.0]])
        prof = smooth_interval(xs, a, b, self.edge)
        W0 = np.atleast_1d(np.asarray(float(self.strength) if strengths is None else strengths, float))
        Tr, R = staircase_transmission(E[None, :], -1j * W0[:, None, None] * prof[None, None, :], (x1 - x0) / slices,
                                       mass, 1.0)
        return (R[0], Tr[0]) if strengths is None else (R, Tr)

    def bbox(self, ndim):
        lo, hi = _vec(self.lo, ndim, ""), _vec(self.hi, ndim, "")
        return (np.array([-np.inf if v is None else v for v in lo]), np.array([np.inf if v is None else v for v in hi]))


@dataclass
class EdgeLayers:
    """The window's open edges: W0 (s/width)^power in a layer of ``width`` at both ends of each axis in ``axes``
    (default all); ``schrodinger_nd.absorbing_layer``."""

    width: float
    strength: float
    power: int = 2
    axes: list | None = None

    def params(self) -> dict:
        return {"width": float(self.width), "strength": float(self.strength), "power": int(self.power),
                "axes": None if self.axes is None else [int(a) for a in self.axes]}

    def W(self, grid):
        W = np.zeros(grid.shape)
        for ax in (range(grid.ndim) if self.axes is None else self.axes):
            for side in ("low", "high"):
                W += S.absorbing_layer(grid, int(ax), side, float(self.width), float(self.strength), int(self.power))
        return W

    def reflection(self, kn, mass: float, strengths=None, slices: int = 2000):
        """(R, T) of one layer for waves whose wavenumber normal to it is ``kn`` (array): the ramp
        -i W0 (s/width)^power, free space on both sides, by the transfer matrices of
        ``schrodinger_nd.layer_reflection`` (the same staircase, ``transfer.staircase_transmission``); 1 - R - T is
        absorbed. ``strengths`` (array): every W0 at once, results (len(strengths), len(kn)) (review UX-ui U3)."""
        from .transfer import staircase_transmission
        kn = np.atleast_1d(np.asarray(kn, float))
        E = kn**2 / (2 * mass)
        w = float(self.width)
        edges = np.linspace(0.0, w, slices + 1)
        xs = np.concatenate([[-1.0], 0.5 * (edges[1:] + edges[:-1]), [w + 1.0]])
        prof = np.clip(xs / w, 0.0, 1.0) ** int(self.power) * ((xs > 0) & (xs <= w))
        W0 = np.atleast_1d(np.asarray(float(self.strength) if strengths is None else strengths, float))
        T, R = staircase_transmission(E[None, :], -1j * W0[:, None, None] * prof[None, None, :], w / slices, mass, 1.0)
        return (R[0], T[0]) if strengths is None else (R, T)

    def check(self, grid):
        if not (float(self.width) > 0 and float(self.strength) > 0):
            raise ValueError(T("window edges: width and absorption strength > 0"))
        for ax in (range(grid.ndim) if self.axes is None else self.axes):
            if 2 * float(self.width) >= grid.shape[int(ax)] * grid.d[int(ax)]:
                raise ValueError(T("window edges: the absorbing layers are wider than the window"))


@dataclass
class Localization(SceneObject):
    """An environment that localizes the particles (module docstring): rate ``rate`` (lambda), length ``length`` (a),
    region ``lo``/``hi`` with ``edge`` (None everywhere: the GRW form)."""

    rate: float
    length: float
    lo: list | None = None
    hi: list | None = None
    edge: float | None = None
    TYPE = "localization"
    NAME = T("a localisation environment")

    def uniform(self) -> bool:
        return self.lo is None and self.hi is None

    def check(self, scene):
        if not (float(self.rate) > 0 and float(self.length) > 0):
            raise ValueError(T("environment: rate λ > 0 and length a > 0"))
        if float(self.length) < LOC_MIN_STEPS * float(max(scene.grid.d)):
            raise ValueError(T("environment: the localisation length a = {a} is less than {k} grid steps — the "
                               "Gaussian jump is not resolved", a=float(self.length), k=float(LOC_MIN_STEPS)))
        if float(self.rate) * scene.dt > LOC_MAX_STEP:
            raise ValueError(T("environment: λ·dt = {x:.3g} > {lim}: two jumps are possible within a step — reduce the "
                               "time step to {dt:.3g}", x=float(self.rate * scene.dt), lim=float(LOC_MAX_STEP),
                               dt=float(LOC_MAX_STEP / self.rate)))
        if not self.uniform():
            lo, hi = _vec(self.lo, scene.ndim, T("environment")), _vec(self.hi, scene.ndim, T("environment"))
            for i in range(scene.ndim):
                if lo[i] is not None or hi[i] is not None:
                    _check_edge(self.edge, scene.grid.d[i], T("edge of the environment's region"))

    def chi(self, X: np.ndarray) -> np.ndarray:
        """The region's profile chi(y) at points X (N, ndim)."""
        if self.uniform():
            return np.ones(len(X))
        n = X.shape[1]
        lo, hi = _vec(self.lo, n, ""), _vec(self.hi, n, "")
        out = np.ones(len(X))
        for i in range(n):
            if lo[i] is not None or hi[i] is not None:
                out *= smooth_interval(X[:, i], lo[i], hi[i], self.edge)
        return out

    def gamma(self, grid) -> np.ndarray:
        """Gamma(r) = lambda chi~(r): the region blurred once more by N(0, a^2/2) (eps_tot^2 = eps^2 + a^2)."""
        if self.uniform():
            return np.full(grid.shape, float(self.rate))
        e_tot = math.sqrt(edge_eps(self.edge) ** 2 + float(self.length) ** 2)
        w_tot = 2 * ERF80 * e_tot
        return float(self.rate) * _box_profile(grid, _vec(self.lo, grid.ndim, ""), _vec(self.hi, grid.ndim, ""), w_tot)

    def bbox(self, ndim):
        lo, hi = _vec(self.lo, ndim, ""), _vec(self.hi, ndim, "")
        return (np.array([-np.inf if v is None else v for v in lo]), np.array([np.inf if v is None else v for v in hi]))


@dataclass
class PathMarker(SceneObject):
    """A which-path marker: inside the box profile (``lo``, ``hi``, ``edge``) the marker turns, b = coupling f(r) e_y
    on the wave's two components (marker |0>, |1>): exp(-i c sigma_y t) |0> = cos(ct)|0> + sin(ct)|1>."""

    lo: list
    hi: list
    coupling: float
    edge: float
    TYPE = "path_marker"
    NAME = T("a which-path marker")

    def check(self, scene):
        lo, hi = _vec(self.lo, scene.ndim, T("which-path mark")), _vec(self.hi, scene.ndim, T("which-path mark"))
        for i in range(scene.ndim):
            if lo[i] is not None and hi[i] is not None and not hi[i] > lo[i]:
                raise ValueError(T("which-path mark: the region is empty"))
            if lo[i] is not None or hi[i] is not None:
                _check_edge(self.edge, scene.grid.d[i], T("edge of the which-path mark's region"))

    def b(self, grid) -> np.ndarray:
        out = np.zeros((3,) + grid.shape)
        out[1] = float(self.coupling) * _box_profile(grid, _vec(self.lo, grid.ndim, ""), _vec(self.hi, grid.ndim, ""),
                                                     self.edge)
        return out

    def bbox(self, ndim):
        lo, hi = _vec(self.lo, ndim, ""), _vec(self.hi, ndim, "")
        return (np.array([-np.inf if v is None else v for v in lo]), np.array([np.inf if v is None else v for v in hi]))


OBJECT_TYPES = {c.TYPE: c for c in (Box, Ball, Step, SlitWall, HarmonicTrap, MagneticField, FluxTube, Detector,
                                    Localization, PathMarker)}


@dataclass
class Packet:
    """A Gaussian packet: |psi|^2 spreads ``sigma`` (inf: uniform along that axis, then k = 0 there), mean
    wavevector ``k``, centre ``center``; ``spin`` (c_up, c_down) along z for a spin-1/2 species (default up)."""

    species: Species
    center: list
    k: list
    sigma: list
    spin: list | None = None

    def params(self) -> dict:
        sp = None if self.spin is None else [[complex(c).real, complex(c).imag] for c in self.spin]
        return {"species": self.species.params(), "center": [float(v) for v in self.center],
                "k": [float(v) for v in self.k], "sigma": [float(v) for v in self.sigma], "spin": sp}

    @classmethod
    def from_params(cls, d):
        sp = None if d["spin"] is None else [complex(a, b) for a, b in d["spin"]]
        return cls(Species(**d["species"]), list(d["center"]), list(d["k"]), list(d["sigma"]), sp)


# --- the scene ------------------------------------------------------------------------------------------------------
class _Particle:
    def __init__(self, pid, packet):
        self.id, self.packet, self.species = pid, packet, packet.species
        self.kind, self.s = "scalar", 0          # "scalar" | "spin" | "marker"; s: spin eigen-sign along the field axis
        self.chi = None                          # spin state (2,) while the wave is scalar or carries a marker
        self.psi = None
        self.acc = None
        self.banked: dict = {}
        self.active, self.detected = True, None
        self.E_jump, self.S_haz = math.inf, 0.0
        self.E_ref, self.t_ref = None, 0.0
        self.err_local, self.err_sum, self.err_since, self.err_ref = 0.0, 0.0, 0, 0.0
        self.planes: dict = {}
        self.jumps: list = []
        self.snaps, self.snap_ok = None, True
        self.sk_extra2 = 0.0                     # spectral variance added since the packet (measurements, jumps)
        self.kspec = None                        # (k mean, sigma_k) per axis of a wave set by hand (set_wave)


class Scene:
    """A quantum scene on a grid of ``shape`` points with ``spacing`` (scalar or per axis) about ``center``, time step
    ``dt`` (scene units), ``units``, open window edges ``edges`` (``EdgeLayers`` or None: periodic and closed), a
    ``seed`` for the scene's own random generator (decoherence jumps), ``device`` "auto" (GPU 0 where it pays) or
    "cpu". Objects: ``add``, ``remove``, ``update``; particles: ``add_particle``, ``remove_particle``,
    ``replace_particle``, ``set_wave``; time: ``advance``; actions: ``measure``; checks: ``checks``, ``step_error``,
    planes ``add_plane``; drawing: ``density``, ``potential``, ``absorber``, ``bbox``; ``state_dict``."""

    def __init__(self, shape, spacing, center=None, dt: float = 0.01, units: Units | None = None,
                 edges: EdgeLayers | None = None, seed: int = 0, device: str = "auto"):
        self.units = units or Units()
        self.grid = S.Grid(shape, spacing, m=1.0, hbar=1.0, center=center)
        self.ndim = self.grid.ndim
        if self.ndim not in (1, 2, 3):
            raise ValueError(T("scene: a 1-D, 2-D or 3-D grid"))
        if not float(dt) > 0:
            raise ValueError(T("the time step must be > 0"))
        self.dt = float(dt)
        if edges is not None:
            edges.check(self.grid)
        self.edges = edges
        if device not in ("auto", "cpu"):
            raise ValueError("device: 'auto' or 'cpu'")
        self.device_mode = device
        self.device = None
        self.xp = np
        self.objects: dict[int, SceneObject] = {}
        self.particles: dict[int, _Particle] = {}
        self.planes: dict[int, dict] = {}
        self._next_obj, self._next_pid, self._next_plane = 1, 1, 1
        self.rng = np.random.default_rng(seed)
        self.t, self.steps = 0.0, 0
        self.events: list = []
        self._ops, self._ops_half, self._H, self._grids = {}, {}, {}, {}
        self._timing = {"steps": 0, "seconds": 0.0}
        self._tnow = 0.0
        # the companion's estimate of the step error every this many steps of each particle (0: only on request,
        # step_error); a schedule in steps, independent of who reads the checks and how often (review B6-Q7)
        self.error_every = 0
        self._obj_cache: dict = {}  # each object's arrays on the grid by its type and parameters (``_on_grid``)
        self._arr = self._compute(self.objects, self.edges)

    def __getstate__(self):
        # the objects' arrays are a cache of pure functions of their parameters: not part of the state (a checkpoint)
        d = dict(self.__dict__)
        d["_obj_cache"] = {}
        return d

    # --- shared arrays ----------------------------------------------------------------------------------------------
    def _on_grid(self, ob, what: str, keys: list):
        """An object's array on the grid (``what``: V, W, field, b), kept by its type, parameters and the grid: a change
        that moves one object evaluates that object alone (plan P16.2: a drag must not rebuild the unrelated ones)."""
        g = self.grid
        key = (what, ob.TYPE, repr(ob.params()), g.shape, tuple(g.d.tolist()), tuple(np.asarray(g.center).tolist()))
        keys.append(key)
        hit = self._obj_cache.get(key)
        if hit is None:
            hit = getattr(ob, what)(g)
            used = sum(int(v.nbytes) for v in self._obj_cache.values())
            if used + hit.nbytes <= OBJ_CACHE_DOUBLES * 8 * g.size:  # bounded: ~8 doubles per grid point
                self._obj_cache[key] = hit
        return hit

    def _prune_cache(self, arr: dict):
        """Keep the cached arrays of the set-up now in force (``arr`` from ``_compute``)."""
        keep = set(arr.get("_keys", ()))
        self._obj_cache = {k: v for k, v in self._obj_cache.items() if k in keep}

    def _compute(self, objects: dict, edges) -> dict:
        g = self.grid
        V_e = np.zeros(g.shape)
        V_q = None
        W_parts, A_list, B, bmark, loc = {}, [], None, None, None
        keys: list = []
        for oid, ob in objects.items():
            if isinstance(ob, Shape):
                if getattr(ob, "coupling", "energy") == "charge":
                    Vo = self._on_grid(ob, "V", keys)
                    V_q = Vo.copy() if V_q is None else V_q + Vo
                else:
                    V_e += self._on_grid(ob, "V", keys)
            elif isinstance(ob, Detector):
                W_parts[f"detector {oid}"] = self._on_grid(ob, "W", keys)
            elif isinstance(ob, (MagneticField, FluxTube)):
                Bf = self._on_grid(ob, "field", keys)
                B = Bf.copy() if B is None else B + Bf
                A = ob.vector_potential(self.ndim)
                if A is not None:
                    A_list.append(A)
            elif isinstance(ob, Localization):
                loc = ob
            elif isinstance(ob, PathMarker):
                bm = self._on_grid(ob, "b", keys)
                bmark = bm.copy() if bmark is None else bmark + bm
        if edges is not None:
            W_parts["edges"] = edges.W(g)
        W_loc = None
        if loc is not None and not loc.uniform():
            W_loc = 0.5 * loc.gamma(g)
        W_tot = None
        if W_parts or W_loc is not None:
            W_tot = sum(W_parts.values(), np.zeros(g.shape))
            if W_loc is not None:
                W_tot = W_tot + W_loc
        u = {}
        if W_tot is not None:
            safe = np.where(W_tot > 0, W_tot, 1.0)
            for k, Wk in W_parts.items():
                u[k] = np.where(W_tot > 0, Wk / safe, 0.0)
        A = None
        if A_list:
            if len(A_list) == 1:
                A = A_list[0]
            else:
                fns = [a.fn for a in A_list]
                label = A_list[0].label
                for vp in A_list[1:]:
                    label = T("{a} + {b}", a=label, b=vp.label)
                A = S.VectorPotential(lambda i, *X: sum(f(i, *X) for f in fns), label)
        axis = None
        if B is not None:
            mag = np.sqrt(np.sum(B * B, axis=0))
            bmax = float(mag.max())
            if bmax == 0:
                B = None
            else:
                i = np.unravel_index(int(np.argmax(mag)), g.shape)
                n = B[(slice(None),) + i] / bmax
                perp = B - n.reshape((3,) + (1,) * g.ndim) * np.tensordot(n, B, axes=1)[None]
                if float(np.max(np.abs(perp))) <= 1e-12 * bmax:
                    axis = n
        return {"V_e": V_e, "V_q": V_q, "W_parts": W_parts, "W_loc": W_loc, "W_tot": W_tot, "u": u, "A": A, "B": B,
                "B_axis": axis, "bmark": bmark, "loc": loc, "_keys": keys}

    # --- kinds (scalar / spinor / marker) ----------------------------------------------------------------------------
    def _kind_for(self, p: _Particle, arr: dict) -> tuple[str, int]:
        """The wave's form under the arrays ``arr``; ValueError for a spin that needs a spinor next to a marker."""
        sp = p.species
        spin_coupled = sp.spin_half and sp.moment != 0 and arr["B"] is not None
        marker = arr["bmark"] is not None or p.kind == "marker"
        if p.kind == "spin":
            if marker:
                raise ValueError(T("particle {pid}: its spin already needs the wave's second component, and the "
                                   "which-path mark takes the same component — spin and mark cannot be used together",
                                   pid=int(p.id)))
            return "spin", 0
        s = 0
        if spin_coupled:
            n = arr["B_axis"]
            if n is not None:
                chi = p.chi
                sv = np.array([2 * (np.conj(chi[0]) * chi[1]).real, 2 * (np.conj(chi[0]) * chi[1]).imag,
                               abs(chi[0]) ** 2 - abs(chi[1]) ** 2])
                proj = float(n @ sv)
                if abs(proj) >= 1 - 1e-12:
                    s = 1 if proj > 0 else -1
            if s == 0:
                if marker:
                    raise ValueError(T("particle {pid}: spin ½ in this field needs a spinor (the field is not along "
                                       "one direction or the spin is not along the field), and the which-path mark takes "
                                       "the same second component of the wave — spin and mark cannot be used together",
                                       pid=int(p.id)))
                return "spin", 0
        return ("marker" if marker else "scalar"), s

    def _convert(self, p: _Particle, kind: str, s: int):
        """Change the wave's form exactly at this moment: scalar -> spinor chi (x) psi, scalar -> (psi, 0) marker."""
        if kind == p.kind:
            p.s = s
            return
        xp = np if isinstance(p.psi, np.ndarray) else self.xp
        if p.kind == "scalar" and kind == "spin":
            chi = p.chi
            p.psi = xp.stack([complex(chi[0]) * p.psi, complex(chi[1]) * p.psi])
            p.chi = None
        elif p.kind == "scalar" and kind == "marker":
            p.psi = xp.stack([p.psi, xp.zeros_like(p.psi)])
        else:
            raise ValueError(T("the wave's form does not change back (a spinor stays a spinor)"))
        p.kind, p.s = kind, s

    def _key(self, p: _Particle):
        sp = p.species
        return (sp.mass, sp.charge, sp.moment, p.kind, p.s)

    # --- operators ------------------------------------------------------------------------------------------------------
    def _grid_for(self, mass: float) -> S.Grid:
        if mass not in self._grids:
            # its own copy of the centre: no two arrays of the state share a buffer (a checkpoint would split them)
            self._grids[mass] = S.Grid(self.grid.shape, self.grid.d, m=mass, hbar=1.0, center=np.array(self.grid.center))
        return self._grids[mass]

    def hamiltonian(self, key) -> S.Hamiltonian:
        if key not in self._H:
            mass, q, mu, kind, s = key
            a = self._arr
            V = a["V_e"] if a["V_q"] is None or q == 0 else a["V_e"] + q * a["V_q"]
            if s != 0:
                V = V - mu * s * np.tensordot(a["B_axis"], a["B"], axes=1)
            b = None
            if kind == "spin":
                b = np.zeros((3,) + self.grid.shape) if a["B"] is None else -mu * a["B"]
            elif kind == "marker":
                b = np.zeros((3,) + self.grid.shape) if a["bmark"] is None else a["bmark"]
            A = a["A"] if q != 0 else None
            self._H[key] = S.Hamiltonian(self._grid_for(mass), V=V, W=a["W_tot"], A=A, q=q if q != 0 else 1.0, b=b)
        return self._H[key]

    def _op(self, key, half: bool = False) -> S.SplitOperator:
        store = self._ops_half if half else self._ops
        if key not in store:
            H = self.hamiltonian(key)
            force = self.device_mode == "cpu" or self.device == "cpu"
            op = S.SplitOperator(H, self.dt / 2 if half else self.dt, track_absorbed=True, force_cpu=force,
                                 why=T("the scene is on the CPU"))
            if self.device is None:
                self.device, self.xp = op.device, op.xp
            elif op.device != self.device:
                raise coded(RuntimeError(T("a scene operator on {op} but the scene on {scene} (GPU memory short?)",
                                           op=str(op.device), scene=str(self.device))), "qscene.device_memory")
            store[key] = op
        return store[key]

    def _drop_ops(self):
        self._ops, self._ops_half, self._H = {}, {}, {}

    # --- bookkeeping of the absorbed probability ----------------------------------------------------------------------
    def absorbed(self, pid: int) -> dict:
        """Probability absorbed so far by each detector ("detector <id>", "edges") for particle ``pid``."""
        p = self.particles[pid]
        out = dict(p.banked)
        if p.acc is not None and self._arr["W_tot"] is not None:
            acc = backend.to_numpy(p.acc) * self.grid.dV
            for k, u in self._arr["u"].items():
                out[k] = out.get(k, 0.0) + float(np.sum(acc * u))
        return out

    def _bank(self):
        """Attribute what each particle's absorbed record holds to the detectors of the current arrays, then zero it
        (before W changes)."""
        for p in self.particles.values():
            if p.acc is not None:
                p.banked = self.absorbed(p.id)
                for plid, st in p.planes.items():
                    if st and plid in self.planes:
                        st["acc_banked"] = st.get("acc_banked", 0.0) + self._acc_beyond(p, self.planes[plid])
                p.acc = self.xp.zeros(self.grid.shape)

    def norm(self, pid: int) -> float:
        p = self.particles[pid]
        if p.psi is None:
            return 0.0
        return float(backend.to_numpy(self.xp.sum(self._rho(p.psi)))) * self.grid.dV

    def _rho(self, psi):
        r = psi.real * psi.real + psi.imag * psi.imag
        return r.sum(axis=0) if psi.ndim == self.ndim + 1 else r

    # --- the grid's resolution of the waves (review B6-Q4) ------------------------------------------------------
    def k_spread(self, pid) -> tuple[np.ndarray, np.ndarray]:
        """(mean wavevector, spread sigma_k per axis) of particle ``pid``'s wave (or of a _Particle): its packet's k and
        1/(2 sigma) widened in quadrature by the measurements (1/(4 s^2) each) and localization jumps (1/(2 a^2)
        each) since — exact for these Gaussian operations; for a wave set by hand, the moments of its spectrum. Free
        motion keeps it; a potential converts energy (``_resolution_reason``)."""
        p = pid if isinstance(pid, _Particle) else self.particles[pid]
        if p.kspec is not None:
            k, sk = (np.array(v, float) for v in p.kspec)
        else:
            k = np.array([float(v) for v in _vec(p.packet.k, self.ndim, "k")])
            sg = np.array(_vec(p.packet.sigma, self.ndim, "σ"), float)
            sk = np.where(np.isfinite(sg), 1.0 / (2.0 * np.where(np.isfinite(sg), sg, 1.0)), 0.0)
        return k, np.sqrt(sk * sk + p.sk_extra2)

    def _scatter_axes(self, p: _Particle, arr: dict) -> list:
        """The axes along which something acting on the particle varies (a potential, an absorber other than the open
        edges' ramps, its vector potential, its spin's field, a marker; an environment: all): momentum can be
        exchanged only along them; along the others it is conserved."""
        sp = p.species
        arrays = []
        if np.any(arr["V_e"] != 0):
            arrays.append(arr["V_e"])
        if sp.charge != 0 and arr["V_q"] is not None:
            arrays.append(arr["V_q"])
        arrays += [W for k, W in arr["W_parts"].items() if k != "edges"]
        if arr["bmark"] is not None:
            arrays += list(arr["bmark"])
        if sp.spin_half and sp.moment != 0 and arr["B"] is not None:
            arrays += list(arr["B"])
        axes = set()
        if arr["loc"] is not None:
            axes = set(range(self.ndim))
        if sp.charge != 0 and arr["A"] is not None:  # the Lorentz force turns the momentum in the plane of A_i, x_j
            for i, Ai in enumerate(arr["A"].arrays(self.grid)):
                if np.any(Ai != 0):
                    axes.add(i)
                    arrays.append(Ai)
        for A_ in arrays:
            A_ = np.broadcast_to(A_, self.grid.shape)
            for i in range(self.ndim):
                if self.grid.shape[i] > 1 and np.any(np.diff(A_, axis=i) != 0):
                    axes.add(i)
        return sorted(a_ for a_ in axes if a_ < self.ndim)

    def _convertible(self, p: _Particle, arr: dict) -> float:
        """The potential energy the particle can turn into motion: V (+ the spin's or marker's |b|) where its packet
        started or averaged over its wave now, whichever is higher, minus the lowest V - |b| in the window (>= 0)."""
        sp = p.species
        V = arr["V_e"] if arr["V_q"] is None or sp.charge == 0 else arr["V_e"] + sp.charge * arr["V_q"]
        bm = 0.0
        if sp.spin_half and sp.moment != 0 and arr["B"] is not None:
            bm = abs(sp.moment) * np.sqrt(np.sum(arr["B"] ** 2, axis=0))
        if arr["bmark"] is not None:
            bm = bm + np.abs(arr["bmark"][1])
        g = self.grid
        hi = np.broadcast_to(V + bm, g.shape)
        lo = V - bm
        c = [0.0 if v is None else v for v in _vec(p.packet.center, self.ndim, T("centre"))]
        ic = tuple(int(np.clip(np.rint((c[a] - g.axes[a][0]) / g.d[a]), 0, g.shape[a] - 1)) for a in range(g.ndim))
        top = float(hi[ic])
        rho = backend.to_numpy(self._rho(p.psi)) if p.psi is not None else None
        if rho is not None and rho.sum() > 0:
            top = max(top, float(np.sum(rho * hi) / rho.sum()))
        return max(0.0, top - float(np.min(lo)))

    def _excess(self, p: _Particle, arr: dict, extra2: float = 0.0):
        """(ratio, K, limit, dV) of the particle's largest wavenumber to what the grid holds under ``arr``
        (``_resolution_reason``; ratio <= 1: resolved), with ``extra2`` added to its spectral variance."""
        g = self.grid
        k, sk = self.k_spread(p)
        s2 = sk * sk + float(extra2)
        S_ = self._scatter_axes(p, arr)
        if arr["loc"] is not None:
            s2 = s2 + 0.5 / float(arr["loc"].length) ** 2
        kN = np.pi / np.asarray(g.d, float)
        worst = (0.0, 0.0, 0.0, 0.0)
        for a_ in range(self.ndim):  # free axes: the packet rule
            if a_ not in S_ and g.shape[a_] > 1:
                K = abs(float(k[a_])) + 6.0 * math.sqrt(float(s2[a_]))
                worst = max(worst, (K / kN[a_], K, float(kN[a_]), 0.0))
        if S_:
            dV = self._convertible(p, arr)
            K = float(np.linalg.norm(k[S_])) + 6.0 * math.sqrt(float(np.max(s2[S_])))
            Kl = math.sqrt(K * K + 2.0 * p.species.mass * dV)
            lim = INTERACT_BAND * float(min(kN[S_]))
            worst = max(worst, (Kl / lim, Kl, lim, dV))
        return worst

    def _resolution_reason(self, arr: dict, parts, extra2: float = 0.0) -> T | None:
        """None when the grid holds every wave in ``parts`` under the arrays ``arr``, else why not (review B6-Q4).
        Free motion is exact for a wave inside the band |k_i| <= pi/d_i (the packet rule). Along the axes where
        something acts on the particle (``_scatter_axes``) its momentum can turn into any of them and gain the potential
        energy it can convert, so there the largest wavenumber K_loc = sqrt(K^2 + 2 m dV), K = |k_S| + 6 sigma_k
        (``k_spread``, plus one jump of an environment, 1/(2 a^2), and ``extra2``), must stay within INTERACT_BAND = 2/3
        of the band: the product V psi carries the wavenumbers of both, and what passes pi/d is aliased into the band
        (the classical 2/3 rule of pseudo-spectral products). Measured (a 4 nm smooth well, transmission against a grid
        twice as fine): 6e-7 at K_loc d = 1.78, 1.5e-4 at 2.11, 4e-3 at 2.65, 7.4e-2 at 3.10."""
        info = self._resolution_info(arr, parts, extra2)
        return None if info is None else info["text"]

    def _resolution_info(self, arr: dict, parts, extra2: float = 0.0) -> dict | None:
        """``_resolution_reason`` with its numbers: None, or {"text", "pid", "K", "lim", "dV", "inter" (the 2/3 band
        next to what acts on the particle; else the packet rule pi/d of free motion), "conv" (potential energy it can
        convert counted)} for the first particle the grid does not hold (a wrapper says which rule refused)."""
        for p in parts:
            if not p.active or p.psi is None:
                continue
            ratio, K, lim, dV = self._excess(p, arr, extra2)
            if ratio > 1 + 1e-12:
                conv = 2.0 * p.species.mass * dV > 1e-6 * K * K
                inter = lim < min(math.pi / float(d) for d in self.grid.d) * (1 - 1e-12) or conv
                if conv:
                    text = T("the grid does not resolve the wave of particle {pid}: its wavenumbers reach {K:.4g} "
                             "(|k| + 6σ_k and the energy {dV:.4g} that the potential can turn into motion), while "
                             "next to what acts on the particle the grid resolves ≤ {lim:.4g} (2/3·π/d: beyond it the "
                             "product V·ψ on the grid is distorted by aliasing); make the grid finer, the particle "
                             "slower or the potential lower", pid=int(p.id), K=float(K), dV=float(dV), lim=float(lim))
                elif inter:
                    text = T("the grid does not resolve the wave of particle {pid}: its wavenumbers reach {K:.4g} "
                             "(|k| + 6σ_k), while next to what acts on the particle the grid resolves ≤ {lim:.4g} "
                             "(2/3·π/d: beyond it the product V·ψ on the grid is distorted by aliasing); make the "
                             "grid finer, the particle slower or the potential lower", pid=int(p.id), K=float(K),
                             lim=float(lim))
                else:
                    text = T("the grid does not resolve the wave of particle {pid}: its wavenumbers reach {K:.4g} "
                             "(|k| + 6σ_k), while the grid resolves ≤ {lim:.4g} (π/d); make the grid finer, the "
                             "particle slower or the potential lower", pid=int(p.id), K=float(K), lim=float(lim))
                return {"text": text, "pid": p.id, "K": K, "lim": lim, "dV": dV, "inter": bool(inter),
                        "conv": bool(conv)}
        return None

    def _closed_axes(self, edges) -> list:
        if edges is None:
            return list(range(self.ndim))
        cov = range(self.ndim) if edges.axes is None else [int(a) for a in edges.axes]
        return [a for a in range(self.ndim) if a not in cov]

    def _gauge_reason(self, arr: dict, edges, charges) -> T | None:
        """None unless a charged particle meets a vector potential the closed (periodic) window cannot hold (review
        B6-Q2). The split operator's gauge phases wrap at the window's faces: where A is not periodic across a closed
        face the wrap is a sheet of field (flux -Phi) that is not on the scene, and a non-zero line integral of A_i
        across the window twists the boundary condition (e^{i q Phi} for a wave crossing the face). The scene's
        vector potentials (Landau strips, a whole-window field, flux tubes) all do one or the other; open edges absorb
        the wave before the faces."""
        A = arr["A"]
        charges = [float(q) for q in charges if q != 0]
        if A is None or not charges:
            return None
        g = self.grid
        X = list(g.mesh())
        for i in self._closed_axes(edges):
            L = g.shape[i] * g.d[i]
            x0 = float(g.axes[i][0])
            lo_, hi_ = list(X), list(X)
            lo_[i], hi_[i] = np.array(x0), np.array(x0 + L)
            jump = max(float(np.max(np.abs(np.broadcast_to(A.fn(j, *hi_) - A.fn(j, *lo_), g.shape))))
                       for j in range(g.ndim))
            scale = max(float(np.max(np.abs(np.broadcast_to(A.fn(j, *X), g.shape)))) for j in range(g.ndim))
            hol = 0.0
            xg, wg = np.polynomial.legendre.leggauss(8)
            for a_, w_ in zip(xg, wg):
                Y = list(X)
                Y[i] = X[i] + 0.5 * g.d[i] * (1.0 + a_)
                hol = hol + 0.5 * g.d[i] * w_ * np.broadcast_to(np.asarray(A.fn(i, *Y), float), g.shape)
            hol = np.sum(hol, axis=i)
            twist = max(float(np.max(np.abs(np.remainder(q * hol + math.pi, 2 * math.pi) - math.pi))) for q in charges)
            if jump > 1e-9 * max(scale, 1e-300) or twist > 1e-9:
                if jump > 1e-9 * max(scale, 1e-300):
                    return T("closed (periodic) window edges along {axis}: the vector potential is not periodic across "
                             "the window's faces — the face would carry a sheet of field that is not in the scene (flux "
                             "−Φ); a charged particle next to a field or a flux tube is allowed only with open "
                             "(absorbing) window edges along every axis", axis="xyz"[i])
                return T("closed (periodic) window edges along {axis}: the vector potential gives a phase q∮A = "
                         "{twist:.3g} rad across the window — a wave crossing the face would acquire the Aharonov–Bohm "
                         "phase of a flux that is not there; a charged particle next to a field or a flux tube is "
                         "allowed only with open (absorbing) window edges along every axis",
                         axis="xyz"[i], twist=float(twist))
        return None

    def _switch_reason(self, old: dict, new: dict) -> T | None:
        """None unless a uniform field's vector potential (Landau gauge, ``MagneticField``) changes where a charged
        particle's wave is (review B6-Q3). psi is kept at a change, so the kinetic momentum jumps by -q Delta A: that
        is the impulse of the induced field -dA/dt of the switch only in the gauge of the magnet that makes it (for a
        z-invariant field and E -> 0 far away, Faraday's law fixes it: the Coulomb gauge); the Landau gauge's reference
        is an implementation detail (two set-ups identical in the window ended 29 nm apart), and a field over the whole
        window has no defined axis. Refused while the wave's probability where Delta A != 0 exceeds the round-off of
        the balance. A flux tube's A is the Coulomb gauge about its axis (Phi/(2 pi r) outside): its switch is the
        induced field of a thin solenoid, kept."""
        charged = [p for p in self.particles.values() if p.active and p.psi is not None and p.species.charge != 0]
        if not charged:
            return None
        po = {oid: ob.params() for oid, ob in old.items() if isinstance(ob, MagneticField)}
        pn = {oid: ob.params() for oid, ob in new.items() if isinstance(ob, MagneticField)}
        if po == pn:
            return None
        g = self.grid
        dA = [np.zeros(g.shape) for _ in range(g.ndim)]
        for objs, sgn in ((new, 1.0), (old, -1.0)):
            for ob in objs.values():
                if isinstance(ob, MagneticField):
                    A = ob.vector_potential(self.ndim)
                    if A is not None:
                        for i, a in enumerate(A.arrays(g)):
                            dA[i] += sgn * a
        mag = np.sqrt(sum(a * a for a in dA))
        top = float(mag.max())
        if top == 0:
            return None
        mask = mag > 1e-12 * top
        tol = BALANCE_EPS * EPS * (self.steps + 1)
        for p in charged:
            P = float(np.sum(backend.to_numpy(self._rho(p.psi))[mask])) * g.dV
            if P > tol:
                return T("the field cannot be changed while the charged particle {pid} is in the window where the "
                         "vector potential changes (probability {P:.3g}): the impulse of the induced field when the "
                         "magnet is switched (Faraday's law) depends on how the magnet is built and where its axis is, "
                         "and the scene's Landau gauge does not carry it; set the field before the particle or remove the "
                         "particle (a flux tube may be changed: its field is a thin solenoid)", pid=int(p.id), P=P)
        return None

    # --- changes of the set-up ----------------------------------------------------------------------------------------
    def _validate(self, objects: dict, edges):
        """The checks of a new set-up (raise ValueError with the reason): every object, the edges, one environment, a
        charged particle's orbital coupling, the closed window's gauge, a switch of a uniform field under a charged wave,
        what the grid holds. Returns (arrays, the waves' forms); changes nothing."""
        for ob in objects.values():
            ob.check(self)
        if edges is not None:
            edges.check(self.grid)
        n_loc = sum(isinstance(o, Localization) for o in objects.values())
        if n_loc > 1:
            raise ValueError(T("one environment (localisation) per scene"))
        arr = self._compute(objects, edges)
        charges = [p.species.charge for p in self.particles.values() if p.active and p.species.charge != 0]
        if charges:
            for ob in objects.values():
                if isinstance(ob, MagneticField) and ob.orbital_reason(self.ndim) is not None:
                    raise ValueError(T("there is a charged particle in the scene: {reason}",
                                       reason=ob.orbital_reason(self.ndim)))
        same = (objects == self.objects and (edges is self.edges or (edges is not None and self.edges is not None
                                                                     and edges.params() == self.edges.params())))
        if not same:  # a change of the time step alone changes neither the gauge nor what the grid must hold
            for code, reason in (("qscene.gauge", self._gauge_reason(arr, edges, charges)),
                                 ("qscene.field_with_charge", self._switch_reason(self.objects, objects)),
                                 ("qscene.resolution", self._resolution_reason(arr, self.particles.values()))):
                if reason:
                    raise coded(ValueError(reason), code)
        kinds = {p.id: self._kind_for(p, arr) for p in self.particles.values() if p.active}
        return arr, kinds

    def _check(self, objects: dict, edges) -> ValueError | None:
        try:
            self._validate(objects, edges)
        except ValueError as e:
            return e
        return None

    def _reason(self, objects: dict, edges) -> T | None:
        e = self._check(objects, edges)
        return None if e is None else text_of(e)

    def addition_check(self, obj: SceneObject) -> ValueError | None:
        """The refusal ``add(obj)`` would raise now (with its machine code ``code``, ``lfphys.codes``), or None; changes
        nothing."""
        return self._check({**self.objects, self._next_obj: obj}, self.edges)

    def addition_reason(self, obj: SceneObject) -> T | None:
        """Why ``add(obj)`` would be refused now, or None; changes nothing (a laboratory's palette: review UX-ui U7).
        ``addition_check`` gives the refusal with its code."""
        return self._reason({**self.objects, self._next_obj: obj}, self.edges)

    def removal_reason(self, oid: int) -> T | None:
        """Why ``remove(oid)`` would be refused now, or None; changes nothing (review UX-params P28)."""
        return self._reason({k: v for k, v in self.objects.items() if k != oid}, self.edges)

    def edges_reason(self, edges) -> T | None:
        """Why ``set_edges(edges)`` would be refused now, or None; changes nothing."""
        return self._reason(dict(self.objects), edges)

    def particle_check(self, packet: Packet) -> ValueError | None:
        """The refusal ``add_particle(packet)`` would raise now (with its machine code ``code``), or None; changes
        nothing."""
        p = _Particle(self._next_pid, packet)
        try:
            p.psi = self._prepare(packet, p)
            reason = self._resolution_reason(self._arr, [p])
            if reason:
                return coded(ValueError(reason), "qscene.resolution")
            self._kind_for(p, self._arr)
        except ValueError as e:
            return e
        return None

    def particle_reason(self, packet: Packet) -> T | None:
        """Why ``add_particle(packet)`` would be refused now, or None; changes nothing (review UX-ui U4: a free spot
        for a new packet). ``particle_check`` gives the refusal with its code."""
        e = self.particle_check(packet)
        return None if e is None else text_of(e)

    def _commit(self, objects: dict, edges, what: T, dt: float | None = None):
        """Validate the new set-up, then bank, convert the waves and rebuild: the change acts from now on."""
        old_dt = self.dt
        if dt is not None:
            self.dt = float(dt)
        try:
            arr, kinds = self._validate(objects, edges)
        except Exception:
            self.dt = old_dt
            raise
        self._bank()
        new_env = arr["loc"] is not None and (self._arr["loc"] is None or
                                              self._arr["loc"].params() != arr["loc"].params())
        self.objects, self.edges, self._arr = objects, edges, arr
        self._prune_cache(arr)
        self._drop_ops()
        for pid, (kind, s) in kinds.items():
            self._convert(self.particles[pid], kind, s)
        for pid in sorted(self.particles):
            p = self.particles[pid]
            if arr["W_tot"] is None:
                p.acc = None
            if new_env:
                self._new_clock(p)
            p.snaps = None  # the interval of the last snapshots ran under the old set-up (review B6-Q12)
            self._reset_refs(p, continuity=False)
        self.events.append({"t": self.t, "what": what})

    def add(self, obj: SceneObject, dt: float | None = None) -> int:
        """Add an object now (with ``dt``: and change the time step in the same change, e.g. for an environment whose
        rate needs a shorter step); returns its id."""
        if not isinstance(obj, SceneObject):
            raise TypeError("a scene object expected")
        oid = self._next_obj
        objs = dict(self.objects)
        objs[oid] = obj
        self._commit(objs, self.edges, T("added {type} #{oid}", type=obj.NAME or obj.TYPE, oid=int(oid)), dt=dt)
        self._next_obj += 1
        return oid

    def remove(self, oid: int):
        objs = dict(self.objects)
        ob = objs.pop(oid)
        self._commit(objs, self.edges, T("removed {type} #{oid}", type=ob.NAME or ob.TYPE, oid=int(oid)))

    def update(self, oid: int, dt: float | None = None, **changes):
        """Change parameters of object ``oid`` now (a new object of the same type with the changed parameters; with
        ``dt``, the time step in the same change)."""
        ob = self.objects[oid]
        new = type(ob).from_params({**ob.params(), **changes})
        objs = dict(self.objects)
        objs[oid] = new
        what = _list_text([T("{k} = {v}", k=k, v=_arg(v)) for k, v in changes.items()])
        self._commit(objs, self.edges, T("changed {type} #{oid}: {changes}", type=ob.NAME or ob.TYPE, oid=int(oid),
                                         changes=what), dt=dt)

    def set_edges(self, edges: EdgeLayers | None):
        self._commit(dict(self.objects), edges, T("window edges changed"))

    def set_dt(self, dt: float):
        if not float(dt) > 0:
            raise ValueError(T("the time step must be > 0"))
        self._commit(dict(self.objects), self.edges, T("time step {old} → {new}", old=float(self.dt), new=float(dt)),
                     dt=dt)

    # --- particles -----------------------------------------------------------------------------------------------------
    def _prepare(self, packet: Packet, p: _Particle) -> np.ndarray:
        """psi0 of a packet on the host (checked: resolution, window, orbital coupling)."""
        g, n = self.grid, self.ndim
        sp = packet.species
        if not sp.mass > 0:
            raise ValueError(T("particle mass > 0"))
        c, k, s = (_vec(v, n, what) for v, what in ((packet.center, T("centre")), (packet.k, "k"),
                                                     (packet.sigma, T("width"))))
        X = g.mesh()
        psi = 1.0
        for i in range(n):
            if s[i] is None or not s[i] > 0:
                raise ValueError(T("packet: width σ > 0 (inf: uniform along the axis)"))
            half = 0.5 * g.shape[i] * g.d[i]
            if math.isinf(s[i]):
                if k[i] != 0:
                    raise ValueError(T("a packet uniform along an axis must have k = 0 along it"))
                continue
            kn = math.pi / g.d[i]
            if abs(k[i]) + PACKET_NYQUIST / (2 * s[i]) > kn:
                raise coded(ValueError(T("packet: |k| + 6σ_k = {K:.4g} along axis {i} exceeds π/d = {kn:.4g} — the "
                                         "grid does not resolve the wave (a finer grid or a smaller momentum)",
                                         K=float(abs(k[i]) + PACKET_NYQUIST / (2 * s[i])), i=int(i), kn=float(kn))),
                            "qscene.packet_band")
            gap = half - abs(c[i] - g.center[i])
            need = s[i] * math.sqrt(2 * math.log(1 / PACKET_TAIL))
            ax = "xyz"[i] if i < 3 else str(i)
            lo_w, hi_w = float(g.center[i]) - half, float(g.center[i]) + half
            if not gap > 0:  # review UX-params P29: a centre outside the window passed (gap^2 large) and psi was 0/0
                raise ValueError(T("the packet's centre is outside the window along {ax}: {c:.4g}, while the window runs "
                                   "from {lo:.4g} to {hi:.4g} — put the centre inside the window, no closer than {need:.3g} "
                                   "to its edge", ax=ax, c=float(c[i]), lo=lo_w, hi=hi_w, need=float(need)))
            if gap * gap / (2 * s[i] ** 2) < math.log(1 / PACKET_TAIL):
                raise ValueError(T("the packet does not fit into the window along {ax}: from the centre to the window's "
                                   "edge is {gap:.4g}, while a packet of width σ = {s:.4g} needs ≥ {need:.4g} (the grid is "
                                   "periodic: the tail beyond the edge would come in from the other side) — move the "
                                   "centre towards the middle of the window or reduce σ",
                                   ax=ax, gap=float(gap), s=float(s[i]), need=float(need)))
            psi = psi * np.exp(-((X[i] - c[i]) ** 2) / (4 * s[i] ** 2) + 1j * k[i] * X[i])
        psi = np.broadcast_to(np.asarray(psi, complex), g.shape).copy()
        if sp.charge != 0:
            for ob in self.objects.values():
                if isinstance(ob, MagneticField) and ob.orbital_reason(n) is not None:
                    raise ValueError(T("a charged particle in this field: {reason}", reason=ob.orbital_reason(n)))
            reason = self._gauge_reason(self._arr, self.edges, [sp.charge])
            if reason:
                raise coded(ValueError(reason), "qscene.gauge")
            A = self._arr["A"]
            if A is not None:
                cen = [ci if ci is not None else 0.0 for ci in c]
                psi = psi * np.exp(1j * sp.charge * A.gauge(g, cen))
        psi /= math.sqrt(g.norm(psi))
        if sp.spin_half:
            chi = np.array([1.0, 0.0], complex) if packet.spin is None else np.asarray(packet.spin, complex)
            nr = float(np.linalg.norm(chi))
            if not nr > 0:
                raise ValueError(T("spin: a non-zero vector (c↑, c↓)"))
            p.chi = chi / nr
        return psi

    def add_particle(self, packet: Packet) -> int:
        """Add a particle (its own wave) now; returns its id."""
        pid = self._next_pid
        p = _Particle(pid, packet)
        p.psi = self._prepare(packet, p)
        reason = self._resolution_reason(self._arr, [p])
        if reason:
            raise coded(ValueError(reason), "qscene.resolution")
        kind, s = self._kind_for(p, self._arr)
        self._convert(p, kind, s)
        p.psi = self._op(self._key(p)).put(p.psi)
        if self._arr["W_tot"] is not None:
            p.acc = self.xp.zeros(self.grid.shape)
        self._new_clock(p)
        self.particles[pid] = p
        self._next_pid += 1
        self._reset_refs(p, continuity=True)
        name = packet.species.name
        self.events.append({"t": self.t, "what": T("added particle {pid} ({species})", pid=int(pid),
                                                   species=PT.SPECIES[name][0] if name in PT.SPECIES else name)})
        return pid

    def remove_particle(self, pid: int):
        self.particles.pop(pid)
        self.events.append({"t": self.t, "what": T("removed particle {pid}", pid=int(pid))})

    def replace_particle(self, pid: int, packet: Packet):
        """A new packet for particle ``pid`` now (its records restart)."""
        old = self.particles[pid]
        p = _Particle(pid, packet)
        p.psi = self._prepare(packet, p)
        reason = self._resolution_reason(self._arr, [p])
        if reason:
            raise coded(ValueError(reason), "qscene.resolution")
        kind, s = self._kind_for(p, self._arr)
        self._convert(p, kind, s)
        p.psi = self._op(self._key(p)).put(p.psi)
        if self._arr["W_tot"] is not None:
            p.acc = self.xp.zeros(self.grid.shape)
        p.planes = {k: {} for k in old.planes}
        self._new_clock(p)
        self.particles[pid] = p
        self._reset_refs(p, continuity=True)
        self.events.append({"t": self.t, "what": T("particle {pid}: a new packet", pid=int(pid))})

    def set_wave(self, pid: int, psi):
        """Replace particle ``pid``'s wave now by ``psi`` (host array of the wave's form: scalar (shape) or (2, shape));
        normalized; its records restart (norm 1, nothing absorbed)."""
        p = self.particles[pid]
        psi = np.asarray(psi, complex)
        want = self.grid.shape if p.kind == "scalar" else (2,) + self.grid.shape
        if psi.shape != want:
            raise ValueError(T("the wave of particle {pid}: shape {want}, given {got}", pid=int(pid), want=str(want),
                               got=str(psi.shape)))
        psi = psi / math.sqrt(self.grid.norm(psi))
        comps = psi if psi.ndim == self.ndim + 1 else psi[None]
        w = np.sum(np.abs(np.fft.fftn(comps, axes=tuple(range(1, self.ndim + 1)))) ** 2, axis=0)
        K = self.grid.kmesh()
        km = np.array([float(np.sum(np.broadcast_to(K[a], w.shape) * w) / w.sum()) for a in range(self.ndim)])
        sd = np.array([math.sqrt(max(float(np.sum((np.broadcast_to(K[a], w.shape) - km[a]) ** 2 * w) / w.sum()), 0.0))
                       for a in range(self.ndim)])
        p.kspec, p.sk_extra2 = (km, sd), 0.0
        p.psi = self.xp.asarray(psi)
        p.snaps = None
        p.banked, p.active, p.detected = {}, True, None
        if p.acc is not None:
            p.acc = self.xp.zeros(self.grid.shape)
        self._reset_refs(p, continuity=True)
        self.events.append({"t": self.t, "what": T("particle {pid}: wave set", pid=int(pid))})

    def adopt_wave(self, pid: int, psi, shape, spacing, banked: dict | None = None, kspec=None, sk_extra2: float = 0.0,
                   old_edges=None, active: bool = True, detected=None, tol: float = REGRID_TOL) -> dict:
        """Take over a wave from another scene of the same dimension and window centre (a new world that keeps the
        scene, plan P16.1): ``psi`` (host; scalar, or (2, shape) for a spin or a marker) on a grid of ``shape`` points
        with ``spacing``, carried to this grid exactly (``schrodinger_nd.resample``) and kept unnormalized (its norm is
        what the old scene had left), with its absorbed records ``banked`` (keys of this scene: "detector <id>",
        "edges", ...), its spectral model (``kspec``, ``sk_extra2``) and, for a particle a detector took (``active``
        False), no wave and the detector's key ``detected``. Refused (ValueError with ``what``; nothing changed) as
        ``regrid`` refuses: more than ``tol`` of its norm dropped or misplaced, more than ``tol`` under this scene's
        open edges' layers that was outside ``old_edges``' (``EdgeLayers`` or None), a wave this grid does not hold, or
        a spinor where the particle here is a scalar. Returns the norm before and after and what was dropped."""
        p = self.particles[pid]
        old = S.Grid(shape, spacing, m=1.0, hbar=1.0, center=np.array(self.grid.center))
        if old.ndim != self.ndim:
            raise self._refusal(T("a wave of another dimension"), pid=pid, what="dim")
        if not active:
            p.psi, p.active, p.detected, p.acc, p.snaps = None, False, detected, None, None
            p.banked = dict(banked or {})
            self.events.append({"t": self.t, "what": T("particle {pid}: carried over as detected", pid=int(pid))})
            return {"norm_before": 0.0, "norm_after": 0.0, "dropped": 0.0}
        psi = np.asarray(psi, complex)
        spinor = psi.ndim == self.ndim + 1
        if spinor and p.kind == "scalar":
            raise self._refusal(T("a wave with a spin or a mark, while the particle here has neither"), pid=pid,
                                what="kind")
        loss = S.regrid_losses(psi, old, self.grid, FACE_CELLS)
        for what in ("spectrum", "outside", "face"):
            if loss[what] > tol:
                raise self._refusal(T("particle {pid}: on this grid {share:.3g} of its norm is lost ({kind}), more than "
                                      "the tolerance {tol}", pid=int(pid), share=float(loss[what]), kind=_LOSS[what],
                                      tol=float(tol)), pid=pid, what=what, value=loss[what])
        n0 = float(np.sum(np.abs(psi) ** 2)) * float(np.prod(old.d))
        same = old.shape == self.grid.shape and np.allclose(old.d, self.grid.d, rtol=1e-14, atol=0.0)
        psi2 = psi.copy() if same else S.resample(psi, old, self.grid)
        exposed, _ = self._layer_shares(psi2, self.grid, self.edges, old, old_edges)
        if exposed > tol:
            raise self._refusal(T("particle {pid}: {share:.3g} of its probability lies in the absorbing layers of this "
                                  "window's edges, more than the tolerance {tol}", pid=int(pid), share=float(exposed),
                                  tol=float(tol)), pid=pid, what="layers", value=exposed)
        if not spinor and p.kind == "spin":
            chi = np.asarray(p.packet.spin if p.packet.spin is not None else [1.0, 0.0], complex)
            chi = chi / np.linalg.norm(chi)
            psi2 = np.stack([complex(chi[0]) * psi2, complex(chi[1]) * psi2])
            p.chi = None
        elif not spinor and p.kind == "marker":
            psi2 = np.stack([psi2, np.zeros_like(psi2)])
        sh = copy.copy(p)
        sh.psi = psi2
        if kspec is not None:
            sh.kspec = (np.array(kspec[0], float), np.array(kspec[1], float))
        sh.sk_extra2 = float(sk_extra2)
        info = self._resolution_info(self._arr, [sh])
        if info:
            raise self._refusal(info["text"], what="resolution",
                                **{k: info[k] for k in ("pid", "K", "lim", "dV", "inter", "conv")})
        p.psi = self._op(self._key(p)).put(psi2)
        p.kspec, p.sk_extra2 = sh.kspec, sh.sk_extra2
        p.banked, p.active, p.detected, p.snaps = dict(banked or {}), True, None, None
        if self._arr["W_tot"] is not None:
            p.acc = self.xp.zeros(self.grid.shape)
        self._reset_refs(p, continuity=True)
        n1 = self.norm(pid)
        self.events.append({"t": self.t, "what": T("particle {pid}: wave carried over from another scene",
                                                   pid=int(pid))})
        return {"norm_before": n0, "norm_after": n1, "dropped": n0 - n1, **loss}

    # --- live changes of the grid, the window and a wave's place (plan P16.1, P16.2) -------------------------------
    def _energy_of(self, p: _Particle) -> float | None:
        """<H> (the Hermitian part) of particle p's wave, normalized; None without a wave."""
        if not p.active or p.psi is None:
            return None
        psi = backend.to_numpy(p.psi)
        comps = psi if psi.ndim == self.ndim + 1 else psi[None]
        nn = float(np.real(np.vdot(comps, comps)))
        if not nn > 0:
            return None
        H = self.hamiltonian(self._key(p))
        return float(np.real(np.vdot(comps, H.apply(comps))) / nn)

    def observables(self, pid: int) -> dict:
        """The particle's readings now, cheaply (one FFT per component; a charged particle in a vector potential also
        H applied once): ``norm`` (probability in the window), ``r`` (<r> of |psi|^2 / norm), ``k`` (the mean kinetic
        wavenumber <p - qA>/hbar), ``E`` (<H>, the Hermitian part, of the normalized wave: as ``checks``), ``active``.
        Without a wave: norm 0 and the rest None."""
        p = self.particles[pid]
        if not p.active or p.psi is None:
            return {"norm": 0.0, "r": None, "k": None, "E": None, "active": p.active}
        g = self.grid
        psi = backend.to_numpy(p.psi)
        comps = psi if psi.ndim == self.ndim + 1 else psi[None]
        rho = np.sum(comps.real ** 2 + comps.imag ** 2, axis=0)
        tot = float(rho.sum())
        if not tot > 0:
            return {"norm": 0.0, "r": None, "k": None, "E": None, "active": True}
        others = lambda a: tuple(i for i in range(self.ndim) if i != a)  # noqa: E731 - the marginals: one pass per axis
        r = [float(np.dot(np.sum(rho, axis=others(a)), g.axes[a]) / tot) for a in range(self.ndim)]
        F = np.fft.fftn(comps, axes=tuple(range(1, self.ndim + 1)))
        w = np.sum(F.real ** 2 + F.imag ** 2, axis=0)
        ws = float(w.sum())
        wm = [np.sum(w, axis=others(a)) for a in range(self.ndim)]
        k = [float(np.dot(wm[a], g.k[a]) / ws) for a in range(self.ndim)]
        H = self.hamiltonian(self._key(p))
        A = H.A_arrays() if p.species.charge != 0 else None
        if A is not None:
            k = [k[a] - p.species.charge * float(np.sum(A[a] * rho) / tot) for a in range(self.ndim)]
            nn = float(np.real(np.vdot(comps, comps)))
            E = float(np.real(np.vdot(comps, H.apply(comps))) / nn)
        else:
            E = sum(float(np.dot(wm[a], g.k[a] ** 2)) for a in range(self.ndim)) / ws / (2.0 * p.species.mass)
            if H.V is not None:
                E += float(np.sum(H.V * rho) / tot)
            if H.b is not None and comps.shape[0] == 2:
                ab = np.conj(comps[0]) * comps[1]
                bx, by, bz = H.b
                E += float(np.sum(2 * bx * ab.real + 2 * by * ab.imag + bz * (np.abs(comps[0]) ** 2
                                                                            - np.abs(comps[1]) ** 2)) / tot)
        return {"norm": tot * g.dV, "r": r, "k": k, "E": E, "active": True}

    @staticmethod
    def _refusal(text: T, **who) -> ValueError:
        """A refused live change: the reason, and which particle (``pid``), object (``oid``) or plane (``plane``) it
        is about, as attributes (a wrapper names them in its own terms); its machine code (``lfphys.codes``) follows
        ``what`` (``_WHAT_CODES``)."""
        e = coded(ValueError(text), _WHAT_CODES.get(who.get("what"), "qscene.refused"))
        for k_, v in who.items():
            setattr(e, k_, v)
        return e

    @staticmethod
    def _layer_shares(psi, new: S.Grid, new_edges, old: S.Grid, old_edges) -> tuple[float, float]:
        """(exposed, inside): the shares of a wave on the grid ``new`` inside the absorbing layers of ``new_edges``
        (``EdgeLayers`` or None) — all of it, and the part outside the layers ``old_edges`` had on ``old`` (where they
        start: ``schrodinger_nd.absorbing_layer``'s inner faces), i.e. wave the change would put under an absorber."""
        if new_edges is None:
            return 0.0, 0.0
        p = np.asarray(psi)
        comps = p if p.ndim == new.ndim + 1 else p[None]
        rho = np.sum(comps.real ** 2 + comps.imag ** 2, axis=0)
        tot = float(rho.sum())
        if not tot > 0:
            return 0.0, 0.0
        inside = new_edges.W(new) > 0
        was = np.zeros(new.shape, bool)
        if old_edges is not None:
            w = float(old_edges.width)
            for ax in (range(new.ndim) if old_edges.axes is None else [int(a) for a in old_edges.axes]):
                shp = [1] * new.ndim
                shp[ax] = -1
                x = new.axes[ax].reshape(shp)
                was |= np.broadcast_to((x < float(old.axes[ax][0]) + w) | (x > float(old.axes[ax][-1]) - w), new.shape)
        return float(rho[inside & ~was].sum()) / tot, float(rho[inside].sum()) / tot

    def regrid(self, shape, spacing, edges=False, tol: float = REGRID_TOL) -> dict:
        """Change the grid now, in the same world (plan P16.1): ``shape`` points per axis with ``spacing`` (scalar or per
        axis), the window's centre kept; ``edges`` the open edges for the new window (``EdgeLayers`` or None; False:
        keep). Every wave is resampled exactly as the band-limited function the grid holds
        (``schrodinger_nd.resample``: the same window — Fourier zero padding or truncation; the same spacing — the
        samples, zeros beyond the old window; both changed — the interpolant evaluated at the new points). Refused (a
        ValueError with the measured fraction, nothing changed) when for any particle more than ``tol`` of its norm
        would be dropped or misplaced (``schrodinger_nd.regrid_losses``): the spectrum beyond a coarser grid's band,
        the probability outside a smaller window, the probability at the faces a larger window pads (the periodic
        grid continues it on the other side), the probability the new window's open edges' layers would cover that is
        outside the old layers now (review LB1-p02-ux Q6: a smaller window, or edges opened, moves the absorbers over
        the wave), or when the set-up does not fit the new grid (an object's edge narrower
        than it resolves, a localization length under 1.5 steps, the resolution rule of ``_resolution_reason``, a flux
        plane outside the window or too near its face). The objects keep their physical parameters (their edges are
        lengths). What the absorbed records hold is attributed to the detectors first (``_bank``); the probability
        the change dropped (norm before - norm after, measured) is banked as "regrid", so norm + absorbed = 1 holds
        to round-off; the energy reference and the flux planes restart (``_reset_refs``). The time step is not changed
        (the caller re-tunes it). Returns a report: per particle the norm and <H> before and after, what was dropped
        and why, the probability that was inside the old edge layers (``in_layers``: a larger window makes that
        attenuated part interior wave) and inside the new ones (``in_new_layers``; ``exposed``: the part of it that was
        outside the old layers). Note: on the same window length the periodic cell moves by (d - d2)/2
        (``schrodinger_nd.window``), exact for the wave; the drawn window and the layers shift by up to half a step."""
        old = self.grid
        shape = tuple(int(n) for n in (np.atleast_1d(shape) if not np.isscalar(shape) else [shape] * self.ndim))
        if len(shape) != self.ndim:
            raise ValueError(T("new grid: {n} point counts needed", n=int(self.ndim)))
        if min(shape) < 8:
            raise ValueError(T("new grid: at least 8 points per axis"))
        new = S.Grid(shape, spacing, m=1.0, hbar=1.0, center=np.array(old.center))
        new_edges = self.edges if edges is False else edges
        rep = {"changed": False, "old": {"shape": list(old.shape), "d": old.d.tolist()},
               "new": {"shape": list(new.shape), "d": new.d.tolist()}, "particles": {}}
        if new.shape == old.shape and np.allclose(new.d, old.d, rtol=1e-14, atol=0.0):
            if new_edges is not self.edges:
                self.set_edges(new_edges)
                rep["changed"] = True
            return rep
        layers = self._arr["W_parts"].get("edges")
        waves = {}
        for pid, p in sorted(self.particles.items()):
            if not p.active or p.psi is None:
                continue
            psi = backend.to_numpy(p.psi)
            loss = S.regrid_losses(psi, old, new, FACE_CELLS)
            if loss["spectrum"] > tol:
                raise self._refusal(
                    T("particle {pid}: beyond the band of the new grid (|k| ≥ π/step = {kn:.4g}) lies {share:.3g} of "
                      "its wave's norm, more than the tolerance {tol}: coarsening the grid would discard it",
                      pid=int(pid), kn=math.pi / float(max(new.d)), share=float(loss["spectrum"]), tol=float(tol)),
                    pid=pid, what="spectrum", value=loss["spectrum"])
            if loss["outside"] > tol:
                raise self._refusal(
                    T("particle {pid}: outside the new window lies {share:.3g} of its probability, more than the "
                      "tolerance {tol}: shrinking the window would discard it", pid=int(pid),
                      share=float(loss["outside"]), tol=float(tol)), pid=pid, what="outside", value=loss["outside"])
            if loss["face"] > tol:
                raise self._refusal(
                    T("particle {pid}: at the faces of the present window ({cells} outermost cells) lies {share:.3g} of "
                      "its probability, more than the tolerance {tol}: the grid is periodic, this part of the wave "
                      "continues from the other side of the window, and in a larger window its continuation would be "
                      "cut off", pid=int(pid), cells=int(FACE_CELLS), share=float(loss["face"]), tol=float(tol)),
                    pid=pid, what="face", value=loss["face"])
            rho = backend.to_numpy(self._rho(p.psi))
            loss["in_layers"] = (float(rho[layers > 0].sum() / rho.sum()) if layers is not None and rho.sum() > 0
                                 else 0.0)
            psi2 = S.resample(psi, old, new)
            loss["exposed"], loss["in_new_layers"] = self._layer_shares(psi2, new, new_edges, old, self.edges)
            if loss["exposed"] > tol:
                raise self._refusal(
                    T("particle {pid}: {share:.3g} of its probability, now outside the layers, would lie in the "
                      "absorbing layers of the new window, more than the tolerance {tol}: the layers would absorb this "
                      "part of the wave", pid=int(pid), share=float(loss["exposed"]), tol=float(tol)), pid=pid,
                    what="layers", value=loss["exposed"])
            waves[pid] = (psi2, loss, self.norm(pid), self._energy_of(p))
        saved = (self.grid, self._grids)
        self.grid, self._grids = new, {}
        try:
            for oid, ob in self.objects.items():
                try:
                    ob.check(self)
                except ValueError as e:
                    raise self._refusal(T("object #{oid} on the new grid: {reason}", oid=int(oid), reason=text_of(e)),
                                        oid=oid) from None
            if new_edges is not None:
                new_edges.check(new)
            arr = self._compute(self.objects, new_edges)
            charges = [p.species.charge for p in self.particles.values() if p.active and p.species.charge != 0]
            reason = self._gauge_reason(arr, new_edges, charges)
            if reason:
                raise coded(ValueError(reason), "qscene.gauge")
            shadows = []
            for pid, (psi2, *_rest) in waves.items():
                sh = copy.copy(self.particles[pid])
                sh.psi = psi2
                shadows.append(sh)
            info = self._resolution_info(arr, shadows)
            if info:
                raise self._refusal(info["text"], what="resolution", **{k: info[k] for k in
                                                                        ("pid", "K", "lim", "dV", "inter", "conv")})
            kinds = {pid: self._kind_for(p, arr) for pid, p in self.particles.items() if p.active}
            planes = {}
            for plid, pl in self.planes.items():
                ax, order = int(pl["axis"]), int(pl["order"])
                want = float(pl.get("requested", pl["position"]))
                idx = int(np.argmin(np.abs(new.axes[ax] - want)))
                lo, hi = S.window(new, ax)
                if not (lo <= want < hi) or idx - order // 2 < 0 or idx + order // 2 >= new.shape[ax]:
                    raise self._refusal(T("flux plane #{plid} ({ax} = {pos:.4g}) is outside the new window or closer "
                                          "than {n} steps to its edge", plid=int(plid), ax="xyz"[ax], pos=want,
                                          n=int(order // 2)), plane=plid)
                planes[plid] = {**pl, "index": idx, "position": float(new.axes[ax][idx]), "requested": want}
        finally:
            self.grid, self._grids = saved
        # commit: the records banked on the old grid, then the new grid, its arrays and the resampled waves
        self._bank()
        self.grid, self._grids = new, {}
        self.edges, self._arr, self.planes = new_edges, arr, planes
        self._prune_cache(arr)
        self._drop_ops()
        self.device, self.xp = None, np
        for pid in sorted(self.particles):
            p = self.particles[pid]
            p.snaps = None
            p.acc = None
            if pid in waves:
                psi2, loss, n0, E0 = waves[pid]
                p.psi = psi2
                self._convert(p, *kinds[pid])
                p.psi = self._op(self._key(p)).put(p.psi)
                n1 = self.norm(pid)
                p.banked["regrid"] = p.banked.get("regrid", 0.0) + (n0 - n1)
                self._reset_refs(p, continuity=True)
                rep["particles"][pid] = {**loss, "norm_before": n0, "norm_after": n1, "dropped": n0 - n1,
                                         "E_before": E0, "E_after": self._energy_of(p)}
            else:
                self._reset_refs(p, continuity=True)
        if arr["W_tot"] is not None:
            for p in self.particles.values():
                if p.active and p.psi is not None:
                    p.acc = self.xp.zeros(new.shape)
        rep["changed"] = True
        self.events.append({"t": self.t, "what": T("grid {old_n} × {old_d} → {new_n} × {new_d}", old_n=str(list(old.shape)),
                                                   old_d=str(old.d.tolist()), new_n=str(list(new.shape)),
                                                   new_d=str(new.d.tolist()))})
        return rep

    def _packet_s0(self, p: _Particle) -> np.ndarray:
        """The packet's own spread sigma_k = 1/(2 sigma) per axis, widened by measurements and jumps (``sk_extra2``):
        the margin of ``_spec_model`` beyond a measured reach."""
        sg = np.array([np.inf if v is None else float(v) for v in _vec(p.packet.sigma, self.ndim, "σ")], float)
        s0 = np.where(np.isfinite(sg), 1.0 / (2.0 * np.where(np.isfinite(sg), sg, 1.0)), 0.0)
        return np.sqrt(s0 * s0 + float(p.sk_extra2))

    def _spec_model(self, psi, s0=None):
        """(mean, sigma_k) per axis of a wave on the grid (host) as the resolution rule models a packet: the mean of its
        spectrum's marginal along the axis and sigma_k = (K - |mean|) / z, K the wavenumber beyond which |k_a| holds
        SPECTRUM_TAIL = 1e-3 of the spectrum and z = ndtri(1 - SPECTRUM_TAIL) (3.09: for a Gaussian, K = |mean| + z
        sigma_k, so the rule's |mean| + 6 sigma_k is the Gaussian's; a wave split in two is modelled by its outer part).
        The core, not the far tail: a wave that has met a barrier carries a scattered tail at the 1e-6 level up to the
        band's edge, which the scene's rule (a packet's |k| + 6 sigma_k) does not count for the wave unboosted either;
        that tail is kept out of the band by the alias test of ``transform_particle``.

        With ``s0`` (the packet's own spread per axis, ``_packet_s0``) the model's |mean| + 6 sigma_k is the reach plus
        the Gaussian's remaining (6 - z) s0: sigma_k = (K - |mean| + (6 - z) s0) / 6 — the same for a Gaussian of
        spread s0, and for a wave split into parts its outer part's own |k| + 6 sigma_k (review LB1-p02-ux Q5: without
        it a wave reflected and transmitted at -k0, +k0 had mean 0 and |mean| + 6 sigma_k = 6 K / z, twice its reach, and
        every throw of it was refused, even one that stopped it)."""
        g = self.grid
        comps = psi if psi.ndim == self.ndim + 1 else psi[None]
        F = np.fft.fftn(comps, axes=tuple(range(1, self.ndim + 1)))
        w = np.sum(F.real ** 2 + F.imag ** 2, axis=0)
        ws = float(w.sum())
        z = float(special.ndtri(1.0 - SPECTRUM_TAIL))
        mean, sk = [], []
        for a in range(self.ndim):
            marg = np.sum(w, axis=tuple(i for i in range(self.ndim) if i != a)) / ws
            ka = g.k[a]
            m = float(np.dot(marg, ka))
            # the spectrum by |k| (cells of the grid's wavenumber step dk about each |k_m|), from the largest down; the
            # reach: where the mass beyond crosses SPECTRUM_TAIL, inside its cell by linear interpolation (the cell's
            # mass spread evenly): no bias of half a step
            n_ = len(ka)
            mag = np.abs(np.rint(np.fft.fftfreq(n_) * n_)).astype(int)
            mm = np.bincount(mag, weights=marg)[::-1]
            u = (np.arange(len(mm))[::-1]) * (2.0 * math.pi / (n_ * float(g.d[a])))
            dkk = 2.0 * math.pi / (n_ * float(g.d[a]))
            C = np.cumsum(mm)
            i = int(min(np.searchsorted(C, SPECTRUM_TAIL, side="left"), len(C) - 1))
            prev = float(C[i - 1]) if i > 0 else 0.0
            frac = (SPECTRUM_TAIL - prev) / float(mm[i]) if mm[i] > 0 else 0.0
            reach = float(u[i]) + 0.5 * dkk - min(max(frac, 0.0), 1.0) * dkk
            mean.append(m)
            if s0 is None:
                sk.append(max(reach - abs(m), 0.0) / z)
            else:
                sk.append(max(reach - abs(m) + (6.0 - z) * float(s0[a]), 0.0) / 6.0)
        return np.array(mean), np.array(sk)

    def move_particle(self, pid: int, shift, tol: float = REGRID_TOL) -> dict:
        """Move particle ``pid``'s wave by ``shift`` now (``transform_particle`` with a shift only)."""
        return self.transform_particle(pid, shift=shift, tol=tol)

    def boost_particle(self, pid: int, dk, tol: float = REGRID_TOL) -> dict:
        """Give particle ``pid``'s wave the momentum hbar dk now (``transform_particle`` with a boost only)."""
        return self.transform_particle(pid, dk=dk, tol=tol)

    def _move_gauge(self, s, c) -> np.ndarray:
        """The phase chi (q chi is added to a charged wave's phase) of the move by ``s`` of a wave about ``c``, per source
        of the vector potential (they add): for a flux tube the line integral of its A from r - s to r
        (``schrodinger_nd.flux_tube_segment``: the exact magnetic translation wherever the tube's path relative to the
        wave, [c0, c0 + s], keeps clear of it); for a field (``MagneticField``) Lambda_{c+s}(r) - Lambda_c(r - s), the
        straight-line integrals of A from the wave's mean position (``VectorPotential.gauge``): exact in a uniform field
        (grad chi = A(r) - A(r - s) for any gauge of it: the magnetic translation), and where the field differs between
        r - s and r no factor is (``_moved`` measures how far the result is from it)."""
        g = self.grid
        chi = np.zeros(g.shape)
        shifted = S.Grid(g.shape, g.d, center=np.array(g.center) - s)  # its points are r - s
        for ob in self.objects.values():
            if isinstance(ob, FluxTube):
                chi += S.flux_tube_segment(g, float(ob.flux), s, tuple(float(v) for v in ob.center), float(ob.radius),
                                           tuple(int(v) for v in ob.axes))
            elif isinstance(ob, MagneticField):
                A = ob.vector_potential(self.ndim)
                if A is not None:
                    chi += A.gauge(g, c + s) - A.gauge(shifted, c)
        return chi

    def _moved(self, p: _Particle, psi: np.ndarray, s: np.ndarray, c) -> tuple[np.ndarray, dict]:
        """The wave ``psi`` (host) of particle ``p`` moved by ``s`` (its mean position ``c``) and what the move did to it:
        ``eps`` — the share of the kinetic field (p - qA) psi that is not the old one carried along,
        ||(p - qA(r)) psi'(r) - f(r) [(p - qA) psi](r - s)||^2 / ||(p - qA) psi||^2 with f the gauge factor (zero for the
        exact magnetic translation psi' = f T_s psi, grad chi = A(r) - A(r - s), which keeps |psi|^2, the current and
        the whole kinetic distribution; measured by spectral derivatives on the grid, so a phase cut of the factor, a
        field that differs between r - s and r or a factor that pushes the canonical spectrum out of the band all count),
        ``T0``, ``T1`` — <(p - qA)^2>/2m before and after, ``tubes`` — per flux tube the probability of the moved wave
        within 3 radii of the path its axis takes relative to the wave, ``fields`` — the fields that differ where the moved
        wave is. Without a vector potential or a charge: the exact translation (eps 0)."""
        g, nd = self.grid, self.ndim
        comps = psi if psi.ndim == nd + 1 else psi[None]
        ax = tuple(range(1, nd + 1))
        K = g.kmesh()
        F = np.fft.fftn(comps, axes=ax)
        ph = 1.0
        for a in range(nd):
            ph = ph * np.exp(-1j * K[a] * float(s[a]))
        Ft = F * ph
        tr = np.fft.ifftn(Ft, axes=ax)
        q, m = float(p.species.charge), float(p.species.mass)
        nn = float(np.sum(comps.real ** 2 + comps.imag ** 2))
        A = self._arr["A"]
        info = {"eps": 0.0, "T0": None, "T1": None, "tubes": {}, "fields": []}
        if A is None or q == 0:
            w = np.sum(F.real ** 2 + F.imag ** 2, axis=0)
            T = sum(float(np.sum(w * np.broadcast_to(K[a] ** 2, g.shape))) for a in range(nd)) / float(w.sum()) / (2 * m)
            info["T0"] = info["T1"] = T
            return (tr if psi.ndim == nd + 1 else tr[0]), info
        f = np.exp(1j * q * self._move_gauge(s, c))
        new = tr * f
        Fn = np.fft.fftn(new, axes=ax)
        Ar = A.arrays(g)
        As = A.arrays(S.Grid(g.shape, g.d, center=np.array(g.center) - s))  # A(r - s)
        num = den = tn = 0.0
        for a in range(nd):
            Ka = np.broadcast_to(K[a], g.shape)
            Dt = np.fft.ifftn(1j * Ka * Ft, axes=ax) - 1j * q * As[a] * tr   # [(grad - iqA) psi](r - s)
            Dn = np.fft.ifftn(1j * Ka * Fn, axes=ax) - 1j * q * Ar[a] * new  # (grad - iqA) psi'
            dd = Dn - f * Dt
            num += float(np.sum(dd.real ** 2 + dd.imag ** 2))
            den += float(np.sum(Dt.real ** 2 + Dt.imag ** 2))
            tn += float(np.sum(Dn.real ** 2 + Dn.imag ** 2))
        info["eps"] = num / den if den > 0 else 0.0
        info["T0"], info["T1"] = den / nn / (2 * m), tn / nn / (2 * m)
        rho = np.sum(new.real ** 2 + new.imag ** 2, axis=0)
        tot = float(rho.sum())
        X = g.mesh()
        shifted = S.Grid(g.shape, g.d, center=np.array(g.center) - s)
        for oid, ob in self.objects.items():
            if isinstance(ob, FluxTube):
                a_, b_ = (int(v) for v in ob.axes)
                u = np.array([s[a_], s[b_]])
                ra, rb = X[a_] - float(ob.center[0]), X[b_] - float(ob.center[1])
                L2 = float(u @ u)
                t = np.clip((ra * u[0] + rb * u[1]) / L2, 0.0, 1.0) if L2 > 0 else 0.0
                dist2 = (ra - t * u[0]) ** 2 + (rb - t * u[1]) ** 2
                near = np.broadcast_to(dist2 < (3.0 * float(ob.radius)) ** 2, g.shape)
                info["tubes"][oid] = float(rho[near].sum()) / tot
            elif isinstance(ob, MagneticField) and ob.vector_potential(nd) is not None:
                B1, B0 = ob.field(g), ob.field(shifted)
                big = float(np.max(np.abs(B1))) or 1.0
                diff = float(np.sum(rho * np.sum((B1 - B0) ** 2, axis=0))) / tot
                if math.sqrt(diff) > 1e-6 * big:
                    info["fields"].append(oid)
        return (new if psi.ndim == nd + 1 else new[0]), info

    def _alias(self, w: np.ndarray, dk) -> float:
        """The share of the spectrum ``w`` (|F|^2 on the grid's modes) that the boost by ``dk`` takes past the band."""
        g = self.grid
        out = np.zeros(g.shape, bool)
        for a, K in enumerate(g.kmesh()):
            kn = math.pi / float(g.d[a])
            out |= np.broadcast_to((K + dk[a] < -kn) | (K + dk[a] >= kn), g.shape)
        return float(w[out].sum() / w.sum())

    def transform_particle(self, pid: int, shift=None, dk=None, tol: float = REGRID_TOL) -> dict:
        """Prepare particle ``pid``'s wave anew now as the same wave moved by ``shift`` and/or given the momentum
        hbar ``dk`` (plan P16.2), one change (both validated before either is applied; refused: nothing changed).

        * **Move**: psi(r) -> psi(r - shift) (``schrodinger_nd.translate``: exact for the band-limited wave, unitary on
          the grid: the norm kept to round-off), its records kept (what was absorbed stays absorbed). A charged particle
          in a vector potential gets the gauge factor exp(i q chi) of the magnetic translation (``_move_gauge``), which
          keeps the kinetic momentum: exact in a uniform field, and past an Aharonov-Bohm tube wherever the path the
          tube takes relative to the wave stays clear of it. Where no translation can keep the wave — the field differs
          between where the wave was and where it goes, or the tube's path crosses the wave (the flux the wave's parts
          enclose would change: review LB1-p02-ux Q1, Q2) — the move is refused: ``_moved`` measures how much of the
          kinetic field (p - qA) psi is not carried along, and more than ``tol`` of it refuses (what="gauge", with the
          kinetic energy's change and the tubes and fields that cause it). Refused also when more than ``tol`` of the
          norm would cross a face of the periodic window into the window (``wrap_fraction``; with open edges what lands
          in the far side's absorbing layer is absorbed there and only reported).
        * **Boost**: psi -> exp(i dk . r) psi, an impulse that shifts the whole momentum distribution by dk (a Galilean
          boost; |psi|^2 and the norm unchanged; for a charged particle the kinetic momentum gains dk in any gauge).
          Refused when more than ``tol`` of the spectrum would pass the grid's band and alias (what="alias"). The
          packet's k becomes the new mean kinetic wavenumber (what tunes the absorbers and the time step) and the wave's
          model for the resolution rule (``k_spread``) is measured on the boosted spectrum (``_spec_model``: per axis
          its mean and the reach where |k| holds SPECTRUM_TAIL = 1e-3, as a Gaussian's mean and sigma_k). The model
          shifted by dk was tried and rejected: a packet a potential has accelerated (a trap) has a model k far from
          its mean, and a throw from rest in the trap was refused; the reach at 1e-9 and at 1e-6 was rejected too:
          after a barrier the wave's scattered tail at those levels reaches the band's edge, which the same wave
          passes unboosted. ``kick_limit`` finds the largest throw these tests take.

        Also refused when the grid would not hold the new wave next to what acts on it (``_resolution_info``;
        what="resolution", with its flags ``inter``, ``conv``). The energy reference and the flux planes restart; Bohm
        snapshots are dropped. Returns the norm, <H> and the kinetic energy <(p - qA)^2>/2m before and after, the mean
        positions and kinetic wavenumbers, the fraction that crossed a face into the window (``wrap``) or into the far
        side's absorbing layer (``far_layer``), the share inside the open edges' layers before the move
        (``in_layers``), the kinetic misfit of the move (``gauge``) and what aliased."""
        p = self.particles[pid]
        if not p.active or p.psi is None:
            raise self._refusal(T("particle {pid} was registered by a detector: there is no wave — nothing to move or "
                                  "accelerate", pid=int(pid)), pid=pid, what="no_wave")
        g = self.grid
        s = None if shift is None else np.array([0.0 if v is None else float(v)
                                                 for v in _vec(shift, self.ndim, T("shift"))])
        dk = None if dk is None else np.array([0.0 if v is None else float(v) for v in _vec(dk, self.ndim, "Δk")])
        psi = backend.to_numpy(p.psi)
        before = self.observables(pid)
        new, wrap, far, alias, eps = psi, 0.0, 0.0, 0.0, 0.0
        T0 = T1 = None
        layers = self._arr["W_parts"].get("edges")
        rho0 = backend.to_numpy(self._rho(p.psi))
        in_layers = float(rho0[layers > 0].sum() / rho0.sum()) if layers is not None and rho0.sum() > 0 else 0.0
        packet = p.packet
        if s is not None and np.any(s != 0):
            margin = float(self.edges.width) if self.edges is not None else 0.0
            wrap = S.wrap_fraction(psi, g, s, margin)
            if wrap > tol:
                raise self._refusal(T("particle {pid}: a shift by {shift} would carry {share:.3g} of its probability "
                                      "across a face of the window (the grid is periodic) — more than the tolerance {tol}",
                                      pid=int(pid), shift=str(np.round(s, 4).tolist()), share=float(wrap),
                                      tol=float(tol)), pid=pid, what="wrap", value=wrap)
            far = S.wrap_fraction(psi, g, s) - wrap if margin > 0 else 0.0
            new, mv = self._moved(p, psi, s, np.array(before["r"]))
            eps, T0, T1 = mv["eps"], mv["T0"], mv["T1"]
            if eps > tol:
                dT = (T1 - T0) / T0 if T0 else float("nan")
                raise self._refusal(
                    T("particle {pid}: a move by {shift} does not keep the wave — {share:.3g} of its kinetic field "
                      "(p − qA)ψ does not move with it (the kinetic energy would change by {pct:.3g} %), more than the "
                      "tolerance {tol}: the magnetic field where the wave goes is not the one where it was, or the path "
                      "of a flux tube relative to the wave passes through it (the flux its parts enclose would change)",
                      pid=int(pid), shift=str(np.round(s, 4).tolist()), share=float(eps), pct=float(100 * dT),
                      tol=float(tol)), pid=pid, what="gauge", value=eps, dT=dT,
                    tubes=mv["tubes"], fields=mv["fields"])
            packet = dataclasses.replace(packet, center=[(0.0 if v is None else float(v)) + float(d_) for v, d_ in
                                                         zip(_vec(packet.center, self.ndim, T("centre")), s)])
        kspec, extra2 = p.kspec, p.sk_extra2
        if dk is not None and np.any(dk != 0):
            comps = new if new.ndim == self.ndim + 1 else new[None]
            F = np.fft.fftn(comps, axes=tuple(range(1, self.ndim + 1)))
            alias = self._alias(np.sum(F.real ** 2 + F.imag ** 2, axis=0), dk)
            if alias > tol:
                raise self._refusal(T("particle {pid}: with the momentum ħΔk, Δk = {dk}, {share:.3g} of its wave's "
                                      "spectrum would leave the grid's band (π/step = {kn:.4g}) — more than the tolerance "
                                      "{tol}", pid=int(pid), dk=str(np.round(dk, 4).tolist()), share=float(alias),
                                      kn=math.pi / float(max(g.d)), tol=float(tol)), pid=pid, what="alias", value=alias)
            X = g.mesh()
            new = new * np.exp(1j * sum(dk[a] * X[a] for a in range(self.ndim)))
            # the wave's model for the resolution rule (``k_spread``) from its boosted spectrum (``_spec_model``), and
            # the packet's k the new mean kinetic wavenumber (what tunes the absorbers and the time step)
            kspec, extra2 = self._spec_model(new, self._packet_s0(p)), 0.0
            packet = dataclasses.replace(packet, k=[float(v) + float(d_) for v, d_ in zip(before["k"], dk)])
        sh = copy.copy(p)
        sh.psi, sh.packet, sh.kspec, sh.sk_extra2 = new, packet, kspec, extra2
        info = self._resolution_info(self._arr, [sh])
        if info:
            raise self._refusal(info["text"], what="resolution",
                                **{k: info[k] for k in ("pid", "K", "lim", "dV", "inter", "conv")})
        E0 = self._energy_of(p)
        p.psi = self._op(self._key(p)).put(new)
        p.packet, p.kspec, p.sk_extra2 = packet, kspec, extra2
        p.snaps = None
        self._reset_refs(p, continuity=True)
        after = self.observables(pid)
        if dk is not None and np.any(dk != 0):
            T0 = T0 if T0 is not None else self.kinetic_energy(pid, psi)
            T1 = self.kinetic_energy(pid)
        self.events.append({"t": self.t, "what": T("particle {pid}: wave prepared anew — shift {shift}, Δk {dk}",
                                                   pid=int(pid), shift=str(None if s is None else np.round(s, 6).tolist()),
                                                   dk=str(None if dk is None else np.round(dk, 6).tolist()))})
        return {"norm_before": before["norm"], "norm_after": after["norm"], "E_before": E0, "E_after": after["E"],
                "T_before": T0, "T_after": T1, "r_before": before["r"], "r_after": after["r"],
                "k_before": before["k"], "k_after": after["k"], "wrap": wrap, "far_layer": far, "in_layers": in_layers,
                "gauge": eps, "alias": alias}

    def kinetic_energy(self, pid: int, psi=None) -> float | None:
        """<(p - qA)^2>/2m of particle ``pid``'s wave (or of ``psi``, host, of its form), normalized, by spectral
        derivatives (hbar = 1); None without a wave."""
        p = self.particles[pid]
        if psi is None:
            if not p.active or p.psi is None:
                return None
            psi = backend.to_numpy(p.psi)
        g, nd = self.grid, self.ndim
        comps = psi if psi.ndim == nd + 1 else psi[None]
        ax = tuple(range(1, nd + 1))
        nn = float(np.sum(comps.real ** 2 + comps.imag ** 2))
        if not nn > 0:
            return None
        F = np.fft.fftn(comps, axes=ax)
        K = g.kmesh()
        q, m = float(p.species.charge), float(p.species.mass)
        A = self._arr["A"] if q != 0 else None
        if A is None:
            w = np.sum(F.real ** 2 + F.imag ** 2, axis=0)
            return sum(float(np.sum(w * np.broadcast_to(K[a] ** 2, g.shape))) for a in range(nd)) / float(w.sum()) / (2 * m)
        Ar = A.arrays(g)
        t = 0.0
        for a in range(nd):
            D = np.fft.ifftn(1j * np.broadcast_to(K[a], g.shape) * F, axes=ax) - 1j * q * Ar[a] * comps
            t += float(np.sum(D.real ** 2 + D.imag ** 2))
        return t / nn / (2 * m)

    def kick_limit(self, pid: int, k_target, shift=None, tol: float = REGRID_TOL, rel: float = 1e-3) -> float | None:
        """The largest a in [0, 1] for which ``transform_particle(pid, shift, dk)`` that makes the mean kinetic
        wavenumber a * ``k_target`` passes the boost's tests (the alias test and ``_resolution_info`` on the boosted
        wave's measured model, the very functions the change applies), by bisection to ``rel``; 1.0 when the whole
        throw passes, None when even a = 0 (the wave stopped) does not. The move by ``shift`` is applied first (its own
        tests are ``transform_particle``'s). Nothing changes (review LB1-p02-ux Q5: a throw's limit is the one the
        scene applies)."""
        p = self.particles[pid]
        if not p.active or p.psi is None:
            return None
        g = self.grid
        psi = backend.to_numpy(p.psi)
        before = self.observables(pid)
        kin = np.array(before["k"], float)
        packet = p.packet
        new = psi
        s = None if shift is None else np.array([0.0 if v is None else float(v)
                                                 for v in _vec(shift, self.ndim, T("shift"))])
        if s is not None and np.any(s != 0):
            new, _ = self._moved(p, psi, s, np.array(before["r"]))
            packet = dataclasses.replace(packet, center=[(0.0 if v is None else float(v)) + float(d_) for v, d_ in
                                                         zip(_vec(packet.center, self.ndim, T("centre")), s)])
        comps = new if new.ndim == self.ndim + 1 else new[None]
        F = np.fft.fftn(comps, axes=tuple(range(1, self.ndim + 1)))
        w = np.sum(F.real ** 2 + F.imag ** 2, axis=0)
        X = g.mesh()
        kt = np.array([float(v) for v in k_target], float)
        s0 = self._packet_s0(p)

        def ok(a):
            dk = a * kt - kin
            if self._alias(w, dk) > tol:
                return False
            boosted = new * np.exp(1j * sum(dk[i] * X[i] for i in range(self.ndim)))
            sh = copy.copy(p)
            sh.psi, sh.kspec, sh.sk_extra2 = boosted, self._spec_model(boosted, s0), 0.0
            sh.packet = dataclasses.replace(packet, k=[float(v) for v in a * kt])
            return self._resolution_info(self._arr, [sh]) is None
        if ok(1.0):
            return 1.0
        if not ok(0.0):
            return None
        lo, hi = 0.0, 1.0
        while hi - lo > rel:
            mid = 0.5 * (lo + hi)
            if ok(mid):
                lo = mid
            else:
                hi = mid
        return lo

    def kick_reach(self, pid: int, tol: float = REGRID_TOL) -> float:
        """The largest |k| a throw may give particle ``pid``'s wave now in every direction (the limit a player shows and
        clamps to beforehand; the scene decides a throw exactly with ``kick_limit``): a bound that the tests of the boost
        pass for any direction of the thrown kinetic wavenumber k, from the measured spectrum alone (no trial boosts).
        With rho_a the reach of |k_a - mean_a| holding all but SPECTRUM_TAIL of the marginal (the canonical spectrum),
        off = mean - <p - qA> and s0 the packet's spread (``_packet_s0``), the boosted model (``_spec_model``) has
        |mean_a| + 6 sigma_k,a <= |k| + |off_a| + rho_a + (6 - z) s0_a; so per free axis that must stay <= pi/d, along
        the axes where something acts sqrt((|k| + |off_S| + max(rho + (6 - z) s0))^2 + 2 m dV) <= 2/3 pi/d
        (``_excess``), and for the alias test |k| + |off_a| + the marginal's reach at tol/ndim <= pi/d. Exact for a
        Gaussian along its worst direction, conservative for a wave in parts. 0 without a wave."""
        p = self.particles[pid]
        if not p.active or p.psi is None:
            return 0.0
        g, nd = self.grid, self.ndim
        psi = backend.to_numpy(p.psi)
        comps = psi if psi.ndim == nd + 1 else psi[None]
        F = np.fft.fftn(comps, axes=tuple(range(1, nd + 1)))
        w = np.sum(F.real ** 2 + F.imag ** 2, axis=0)
        ws = float(w.sum())
        kin = np.array(self.observables(pid)["k"], float)
        z = float(special.ndtri(1.0 - SPECTRUM_TAIL))
        s0 = self._packet_s0(p)
        if self._arr["loc"] is not None:
            s0 = np.sqrt(s0 * s0 + 0.5 / float(self._arr["loc"].length) ** 2)
        kN = np.pi / np.asarray(g.d, float)

        def reach(dist, marg, level):
            o = np.argsort(dist)[::-1]
            tail = np.cumsum(marg[o])
            j = int(np.searchsorted(tail, level, side="right"))
            return float(dist[o][min(j, len(o) - 1)])
        mean, rho, ral = np.zeros(nd), np.zeros(nd), np.zeros(nd)
        for a in range(nd):
            marg = np.sum(w, axis=tuple(i for i in range(nd) if i != a)) / ws
            mean[a] = float(np.dot(marg, g.k[a]))
            dist = np.abs(g.k[a] - mean[a])
            rho[a] = reach(dist, marg, SPECTRUM_TAIL)
            ral[a] = reach(dist, marg, tol / nd)
        off = np.abs(mean - kin)
        lims = [float(kN[a] - off[a] - ral[a]) for a in range(nd)]
        S_ = self._scatter_axes(p, self._arr)
        for a in range(nd):
            if a not in S_ and g.shape[a] > 1:
                lims.append(float(kN[a] - off[a] - rho[a] - (6.0 - z) * s0[a]))
        if S_:
            dV = self._convertible(p, self._arr)
            lim = INTERACT_BAND * float(min(kN[S_]))
            v = lim * lim - 2.0 * p.species.mass * dV
            lims.append(math.sqrt(max(v, 0.0)) - float(np.linalg.norm(off[S_]))
                        - float(np.max(rho[S_] + (6.0 - z) * s0[S_])))
        return max(min(lims), 0.0)

    def _new_clock(self, p):
        p.E_jump = -math.log(1.0 - self.rng.random()) if self._arr["loc"] is not None else math.inf
        p.S_haz = 0.0

    def _reset_refs(self, p: _Particle, continuity: bool):
        """Restart the energy reference (the set-up or the wave changed) and, for ``continuity``, the planes."""
        p.E_ref, p.t_ref = None, self.t
        if continuity:
            for pl in self.planes:
                p.planes[pl] = {}

    # --- time ------------------------------------------------------------------------------------------------------
    def _swap(self, p, op):
        if op.loss is not None:
            if p.acc is None:
                p.acc = self.xp.zeros(self.grid.shape)
            op.acc = p.acc

    def _plain_step(self, p, op):
        self._swap(p, op)
        p.psi = op.step(p.psi, 1)

    def _det_sum(self, p):
        """sum_points acc * (W_det / W_tot) dV: the detectors' share of the particle's absorbed record now."""
        if p.acc is None:
            return 0.0
        u = self._u_det_dev()
        return float(backend.to_numpy(self.xp.sum(p.acc * u))) * self.grid.dV

    def _u_det_dev(self):
        if "_u_det" not in self._arr:
            W_loc, W_tot = self._arr["W_loc"], self._arr["W_tot"]
            u = np.where(W_tot > 0, (W_tot - W_loc) / np.where(W_tot > 0, W_tot, 1.0), 0.0)
            self._arr["_u_det"] = self.xp.asarray(u)
        return self._arr["_u_det"]

    def _region_substep(self, p, op):
        """One no-jump step in a localization region: the loss split into the detectors' part (kept) and Gamma's part
        (restored); returns (psi, its target norm, hazard of the step, acc before)."""
        n0 = float(backend.to_numpy(self.xp.sum(self._rho(p.psi)))) * self.grid.dV
        self._swap(p, op)
        acc0 = p.acc.copy()
        a0 = self._det_sum(p)
        psi1 = op.step(p.psi, 1)
        dA = self._det_sum(p) - a0
        n1 = float(backend.to_numpy(self.xp.sum(self._rho(psi1)))) * self.grid.dV
        target = max(n0 - dA, 0.0)
        h = math.log(target / n1) if n1 > 0 and target > 0 else 0.0
        return psi1, target, n1, h, acc0

    def _count(self, p: _Particle, h: float) -> int:
        """The number of jumps in a step of integrated hazard h: the thresholds E_1, E_1 + E_2, ... (E_i ~ Exp(1))
        crossed by the particle's integrated hazard (a Poisson process in the hazard: Poisson(h) jumps for a constant
        rate); the overshoot carries over."""
        k = 0
        while p.S_haz + h >= p.E_jump:
            h -= p.E_jump - p.S_haz
            p.S_haz = 0.0
            p.E_jump = -math.log(1.0 - self.rng.random())
            k += 1
        p.S_haz += h
        return k

    def _step(self, p: _Particle, op: S.SplitOperator):
        loc = self._arr["loc"]
        if loc is None:
            self._plain_step(p, op)
            return
        if loc.uniform():
            k = self._count(p, float(loc.rate) * self.dt)
            if k == 0:
                self._plain_step(p, op)
                return
            oph = self._op(self._key(p), half=True)
            self._plain_step(p, oph)
            for _ in range(k):
                self._jump(p, loc)
            self._plain_step(p, oph)
            return
        psi1, target, n1, h, acc0 = self._region_substep(p, op)
        k = self._count(p, h)
        if k == 0:
            p.psi = psi1 * math.sqrt(target / n1) if n1 > 0 else psi1
            return
        # jumps in this step: redo it as half step, the jumps at the midpoint, half step (the step's hazard h, from its
        # no-jump evolution, has been counted; the second half's is part of it)
        p.acc[...] = acc0
        oph = self._op(self._key(p), half=True)
        psi_h, t_h, n_h, _, _ = self._region_substep(p, oph)
        p.psi = psi_h * math.sqrt(t_h / n_h) if n_h > 0 else psi_h
        for _ in range(k):
            self._jump(p, loc)
        psi2, t2, n2, _, _ = self._region_substep(p, oph)
        p.psi = psi2 * math.sqrt(t2 / n2) if n2 > 0 else psi2

    def _jump(self, p: _Particle, loc: Localization):
        """psi -> L_y psi at the current point of the step, y ~ |psi|^2 * N(0, a^2/2) times chi(y) (rejection)."""
        g = self.grid
        rho = backend.to_numpy(self._rho(p.psi)).ravel()
        tot = rho.sum()
        if not tot > 0:
            return
        prob = rho / tot
        a = float(loc.length)
        coords = np.stack([ax.ravel() for ax in g.mesh(sparse=False)], axis=1) if g.ndim > 1 else g.axes[0][:, None]
        for _ in range(10000):
            idx = self.rng.choice(len(prob), size=64, p=prob)
            Y = coords[idx] + (a / math.sqrt(2.0)) * self.rng.standard_normal((64, g.ndim))
            acc = self.rng.random(64) < loc.chi(Y)
            if np.any(acc):
                y = Y[int(np.argmax(acc))]
                break
        else:
            raise coded(RuntimeError(T("localisation jump: no point found in the environment's region")),
                        "qscene.no_localisation_point")
        X = g.mesh()
        f = 1.0
        for i in range(g.ndim):
            f = f * np.exp(-((X[i] - y[i]) ** 2) / (2 * a * a))
        f = self.xp.asarray(np.broadcast_to(f, g.shape))
        n_before = float(backend.to_numpy(self.xp.sum(self._rho(p.psi))))
        new = p.psi * f
        n_after = float(backend.to_numpy(self.xp.sum(self._rho(new))))
        p.psi = new * math.sqrt(n_before / n_after)
        p.jumps.append((self._tnow + 0.5 * self.dt, y.copy()))
        p.sk_extra2 += 0.5 / (a * a)  # the jump multiplies psi by exp(-|r - y|^2 / (2 a^2)): sigma_k^2 + 1/(2 a^2)
        p.snap_ok = False
        self._reset_refs(p, continuity=True)

    def advance(self, n: int = 1, snapshots: bool = False):
        """n time steps of every particle. With ``snapshots`` (n even) psi at t, t + n dt/2, t + n dt is kept per
        particle for Bohm trajectories (``snapshots``)."""
        n = int(n)
        if n <= 0:
            return
        t0 = time.perf_counter()
        for pid in sorted(self.particles):
            p = self.particles[pid]
            if not p.active:
                continue
            op = self._op(self._key(p))
            snaps = [p.psi] if snapshots else None
            p.snap_ok = True
            for k in range(n):
                self._tnow = self.t + k * self.dt
                self._step(p, op)
                self._planes_step(p, op)
                p.err_since += 1
                if self.error_every and p.err_since >= self.error_every and p.psi is not None:
                    self._companion(p)
                if snapshots and 2 * (k + 1) == n:
                    snaps.append(p.psi)
            if snapshots:
                snaps.append(p.psi)
                p.snaps = (tuple(snaps), n * self.dt) if (n % 2 == 0 and p.snap_ok) else None
            else:
                p.snaps = None
        self.t += n * self.dt
        self.steps += n
        self._timing["steps"] += n
        self._timing["seconds"] += time.perf_counter() - t0

    def describe(self) -> dict:
        """The scene for an inspector: objects (type, parameters, box for drawing), particles (species, the wave's
        form, active or which detector took it), planes, time, device."""
        objs = []
        for oid, ob in self.objects.items():
            lo, hi = self.bbox(oid)
            objs.append({"id": oid, "type": ob.TYPE, "params": ob.params(), "bbox": [lo.tolist(), hi.tolist()]})
        parts = [{"id": pid, "species": p.species.params(), "packet": p.packet.params(), "wave": p.kind,
                  "spin_sign": p.s, "active": p.active, "detected": p.detected, "jumps": len(p.jumps)}
                 for pid, p in sorted(self.particles.items())]
        return {"t": self.t, "steps": self.steps, "dt": self.dt, "ndim": self.ndim, "shape": list(self.grid.shape),
                "spacing": self.grid.d.tolist(), "device": self.device, "edges": None if self.edges is None else
                self.edges.params(), "objects": objs, "particles": parts, "planes": dict(self.planes)}

    # --- Bohm support (the trajectories themselves: theories.interpretations.bohm) ----------------------------------
    def snapshots(self, pid: int):
        """((psi_t, psi_t+h/2, psi_t+h), h) of the last ``advance(n, snapshots=True)``, or None when a jump or a
        measurement broke the interval."""
        return self.particles[pid].snaps

    def guidance(self, pid: int):
        """(grid, Hamiltonian, array module) of particle ``pid``: the arguments ``bohm.advance_ensemble`` needs."""
        p = self.particles[pid]
        return self._grid_for(p.species.mass), self.hamiltonian(self._key(p)), self.xp

    # --- measurement --------------------------------------------------------------------------------------------------
    def kraus(self, x, sigma: float) -> np.ndarray:
        """K_x(r) = (2 pi s^2)^(-d/4) exp(-|r - x|^2 / (4 s^2)) on the grid (host)."""
        g = self.grid
        X = g.mesh()
        out = (2 * math.pi * sigma**2) ** (-g.ndim / 4)
        for i in range(g.ndim):
            out = out * np.exp(-((X[i] - x[i]) ** 2) / (4 * sigma**2))
        return np.broadcast_to(out, g.shape)

    def outcome_density(self, pid: int, X, sigma: float) -> np.ndarray:
        """p(x) = ||K_x psi||^2 at points X (N, ndim): sum_i rho_i dV (2 pi s^2)^(-d/2) exp(-|r_i - x|^2/(2 s^2))."""
        g = self.grid
        rho = backend.to_numpy(self._rho(self.particles[pid].psi)) * g.dV
        X = np.atleast_2d(np.asarray(X, float))
        out = np.empty(len(X))
        for j, x in enumerate(X):
            out[j] = float(np.sum(rho * self.kraus(x, sigma) ** 2))
        return out

    def measure_min_sigma(self, pid: int) -> float:
        """The smallest resolution s of a position measurement after which the grid still holds the wave (review
        B6-Q4): at least the largest grid step (the outcome density's quadrature), and such that the wave's spectrum,
        widened by 1/(4 s^2) in variance, passes ``_resolution_reason``; inf when no s is enough. (Bisection in log s:
        the excess falls monotonically with s.)"""
        p = self.particles[pid]
        dmax = float(max(self.grid.d))
        if not p.active or p.psi is None:
            return dmax
        ok = lambda s_: self._excess(p, self._arr, 0.25 / s_ ** 2)[0] <= 1.0  # noqa: E731
        if ok(dmax):
            return dmax
        if self._excess(p, self._arr, 0.0)[0] > 1.0:
            return math.inf
        lo, hi = math.log(dmax), math.log(dmax)
        while not ok(math.exp(hi)):
            hi += 1.0
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            lo, hi = (lo, mid) if ok(math.exp(mid)) else (mid, hi)
        return math.exp(hi)

    def measure(self, pid: int, sigma: float, rng, at=None) -> dict:
        """An unsharp position measurement of particle ``pid`` now (module docstring). ``rng``: the caller's numpy
        Generator; ``at``: the point r the outcome is drawn around (default: drawn from |psi|^2). Returns
        {"outcome": "position", "x", "p_flight"} or {"outcome": "absorbed", "detector", "p"}."""
        p = self.particles[pid]
        g = self.grid
        if not p.active:
            raise ValueError(T("particle {pid} has already been registered by a detector", pid=int(pid)))
        if not float(sigma) >= float(max(g.d)) * (1 - 1e-12):
            raise ValueError(T("the measurement resolution σ = {sigma} is less than the grid step {d}: the grid does "
                               "not resolve the outcome", sigma=float(sigma), d=float(max(g.d))))
        smin = self.measure_min_sigma(pid)
        if float(sigma) < smin * (1 - 1e-12):
            raise ValueError(T("the measurement resolution σ = {sigma} is too small for this grid: the wave after the "
                               "measurement (its spectrum wider by 1/(2σ)) would not fit into the grid's band — it needs "
                               "σ ≥ {smin:.4g} (or a finer grid)", sigma=float(sigma), smin=float(smin)))
        A = self.absorbed(pid)
        n = self.norm(pid)
        u = rng.random()
        tot = 0.0
        for k, v in sorted(A.items()):
            tot += v
            if u < tot:
                p.psi, p.active, p.detected = None, False, k
                p.banked, p.acc = {k: 1.0}, None
                self.events.append({"t": self.t, "what": T("measurement of particle {pid}: already absorbed ({where})",
                                                           pid=int(pid), where=k)})
                return {"outcome": "absorbed", "detector": k, "p": v}
        if at is None:
            rho = backend.to_numpy(self._rho(p.psi)).ravel()
            i = int(rng.choice(rho.size, p=rho / rho.sum()))
            idx = np.unravel_index(i, g.shape)
            r = np.array([g.axes[a][idx[a]] for a in range(g.ndim)])
        else:
            r = np.asarray(at, float).reshape(g.ndim)
        x = r + float(sigma) * rng.standard_normal(g.ndim)
        K = self.xp.asarray(np.ascontiguousarray(self.kraus(x, float(sigma))))
        new = p.psi * K
        nn = float(backend.to_numpy(self.xp.sum(self._rho(new)))) * g.dV
        p.psi = new / math.sqrt(nn)
        p.banked = {}
        if p.acc is not None:
            p.acc = self.xp.zeros(g.shape)
        p.snap_ok, p.snaps = False, None  # review B6-Q12: the last interval's snapshots are stale
        p.sk_extra2 += 0.25 / float(sigma) ** 2  # K_x multiplies psi by exp(-|r - x|^2 / (4 s^2)): sigma_k^2 + 1/(4 s^2)
        self._reset_refs(p, continuity=True)
        self.events.append({"t": self.t, "what": T("position measurement of particle {pid}: x = {x}, σ = {sigma}",
                                                   pid=int(pid), x=str(np.round(x, 4).tolist()), sigma=float(sigma))})
        return {"outcome": "position", "x": x, "p_flight": n}

    # --- readouts -------------------------------------------------------------------------------------------------------
    def wave(self, pid: int) -> np.ndarray | None:
        """psi of particle ``pid`` on the host (scalar or (2, shape))."""
        p = self.particles[pid]
        return None if p.psi is None else backend.to_numpy(p.psi)

    def density(self, pid: int | None = None) -> np.ndarray:
        """|psi|^2 of one particle, or the sum over all particles (each its own probability density)."""
        if pid is not None:
            p = self.particles[pid]
            return np.zeros(self.grid.shape) if p.psi is None else backend.to_numpy(self._rho(p.psi))
        out = np.zeros(self.grid.shape)
        for p in self.particles.values():
            if p.psi is not None:
                out += backend.to_numpy(self._rho(p.psi))
        return out

    def spin(self, pid: int) -> np.ndarray:
        """<sigma> (x, y, z) of the particle's spin (normalized), or of its marker for a marker wave."""
        p = self.particles[pid]
        if p.psi is None and p.kind != "scalar":
            raise ValueError(T("particle {pid} was absorbed by a detector: there is no wave", pid=int(pid)))
        if p.kind == "spin" or p.kind == "marker":
            ps = backend.to_numpy(p.psi)
            a, b = ps[0], ps[1]
            ab = np.sum(np.conj(a) * b)
            n = np.sum(np.abs(a) ** 2 + np.abs(b) ** 2)
            return np.array([2 * ab.real, 2 * ab.imag, np.sum(np.abs(a) ** 2 - np.abs(b) ** 2)]) / n
        chi = p.chi
        if chi is None:
            raise ValueError(T("the particle has no spin"))
        ab = np.conj(chi[0]) * chi[1]
        return np.array([2 * ab.real, 2 * ab.imag, abs(chi[0]) ** 2 - abs(chi[1]) ** 2])

    def marker_state(self, pid: int) -> np.ndarray:
        """The marker's reduced density matrix (2 x 2, trace 1) of a marker wave."""
        p = self.particles[pid]
        if p.kind != "marker":
            raise ValueError(T("the particle has no which-path mark"))
        ps = backend.to_numpy(p.psi).reshape(2, -1)
        rho = ps @ ps.conj().T
        return rho / np.trace(rho).real

    def potential(self, species_: Species | None = None) -> np.ndarray:
        """V for a species (default: the energy part only, for drawing)."""
        a = self._arr
        if species_ is None or a["V_q"] is None:
            return a["V_e"].copy()
        return a["V_e"] + species_.charge * a["V_q"]

    def absorber(self) -> np.ndarray:
        """W of the detectors and the edges (the localization's Gamma/2 left out)."""
        return sum(self._arr["W_parts"].values(), np.zeros(self.grid.shape))

    def bbox(self, oid: int):
        """(lo, hi) of object ``oid`` clipped to the window (for drawing)."""
        lo, hi = self.objects[oid].bbox(self.ndim)
        wl = np.array([ax[0] - 0.5 * d for ax, d in zip(self.grid.axes, self.grid.d)])
        wh = np.array([ax[-1] + 0.5 * d for ax, d in zip(self.grid.axes, self.grid.d)])
        return np.maximum(lo, wl), np.minimum(hi, wh)

    def edge_reflection(self, k, mass: float):
        """(R, T) of the window's edge layers for normal wavenumbers k (``schrodinger_nd.layer_reflection``)."""
        e = self.edges
        if e is None:
            raise ValueError(T("the window's edges are closed (periodic)"))
        return S.layer_reflection(k, float(e.width), float(e.strength), mass, 1.0, int(e.power))

    # --- flux planes -----------------------------------------------------------------------------------------------
    def add_plane(self, axis: int, position: float, order: int = 16) -> int:
        """A plane normal to ``axis`` at the grid sample nearest ``position``: the flux through it is integrated in
        time per particle and compared in ``checks`` with the change of the probability beyond it."""
        g = self.grid
        idx = int(np.argmin(np.abs(g.axes[axis] - position)))
        if idx - order // 2 < 0 or idx + order // 2 >= g.shape[axis]:
            raise ValueError(T("the flux plane is too close to the window's edge"))
        plid = self._next_plane
        self._next_plane += 1
        self.planes[plid] = {"axis": int(axis), "index": idx, "position": float(g.axes[axis][idx]), "order": int(order),
                             "requested": float(position)}
        for p in self.particles.values():
            p.planes[plid] = {}
        return plid

    def remove_plane(self, plid: int):
        self.planes.pop(plid)
        for p in self.particles.values():
            p.planes.pop(plid, None)

    def _plane_flux(self, p, op, pl) -> float:
        j = op.flux(p.psi, pl["axis"], pl["index"], pl["order"])
        return float(np.sum(j)) * self.grid.dV / self.grid.d[pl["axis"]]

    def _beyond(self, p, op, pl) -> float:
        """Probability beyond the plane: trapezoid in the normal direction with the Euler-Maclaurin end correction
        (d^2/12) d rho/dn on the plane, plus what was absorbed beyond it."""
        g = self.grid
        ax, i = pl["axis"], pl["index"]
        rho = backend.to_numpy(self._rho(p.psi))
        sl = [slice(None)] * g.ndim
        sl[ax] = slice(i + 1, None)
        tot = float(np.sum(rho[tuple(sl)]))
        sl[ax] = i
        tot += 0.5 * float(np.sum(rho[tuple(sl)]))
        pc, dpsi = op.plane(p.psi, ax, i, pl["order"])
        drho = 2.0 * np.real(np.sum(np.conj(pc) * dpsi, axis=0))
        P = tot * g.dV + g.d[ax] ** 2 / 12.0 * float(np.sum(drho)) * g.dV / g.d[ax]
        return P + self._acc_beyond(p, pl)

    def _acc_beyond(self, p, pl) -> float:
        """What the particle's absorbed record (since the last banking) holds beyond the plane (half on the plane)."""
        if p.acc is None:
            return 0.0
        g = self.grid
        ax, i = pl["axis"], pl["index"]
        acc = backend.to_numpy(p.acc)
        sl = [slice(None)] * g.ndim
        sl[ax] = slice(i + 1, None)
        a = float(np.sum(acc[tuple(sl)]))
        sl[ax] = i
        a += 0.5 * float(np.sum(acc[tuple(sl)]))
        return a * g.dV

    def _planes_step(self, p, op):
        if not self.planes:
            return
        for plid, pl in self.planes.items():
            st = p.planes.setdefault(plid, {})
            J = self._plane_flux(p, op, pl)
            if not st:
                st.update({"F": 0.0, "J": J, "P0": self._beyond(p, op, pl), "t0": self.t, "valid": True})
                continue
            st["F"] += 0.5 * (st["J"] + J) * self.dt
            st["J"] = J
        if self._arr["loc"] is not None:
            for st in p.planes.values():
                st["valid"] = False

    # --- checks -----------------------------------------------------------------------------------------------------
    def _companion(self, p: _Particle):
        """One companion estimate for particle p now (``step_error``)."""
        key = self._key(p)
        op, oph = self._op(key), self._op(key, half=True)
        scratch = self.xp.zeros(self.grid.shape) if op.loss is not None else None
        if scratch is not None:
            op.acc = scratch
            oph.acc = scratch
        a = op.step(p.psi, 1)
        b = oph.step(oph.step(p.psi, 1), 1)
        d = a - b
        diff = math.sqrt(float(backend.to_numpy(self.xp.sum(self._rho(d)))) * self.grid.dV)
        local = SPLIT_LOCAL * diff
        prev = p.err_local if p.err_local > 0 else local
        p.err_sum += 0.5 * (prev + local) * p.err_since  # trapezoid over the steps since the last estimate
        p.err_local, p.err_since = local, 0

    def step_error(self) -> dict:
        """The companion estimate of the time step's error per particle: one step dt against two steps dt/2 from the
        current state (the particle's records untouched); local error (4/3)||difference|| per step, accumulated over
        the steps since the last estimate by the trapezoid. Costs three extra steps per particle. The sum is a
        leading-order estimate of the global error, not a bound: it is as good as its sampling — with estimates only
        at the start and the end of a wall interaction it fell three times below the true error (review B6-Q7);
        ``error_every`` takes one every that many steps of each particle, whoever reads the checks."""
        out = {}
        for pid, p in self.particles.items():
            if not p.active:
                continue
            self._companion(p)
            out[pid] = {"local": p.err_local, "accumulated": p.err_sum}
        return out

    def checks(self, error: bool = False) -> dict:
        """Running checks per particle (module docstring): norm + absorbed - 1, energy drift of a closed system and
        its bound, flux planes, the time-step error (with ``error`` a fresh companion estimate), the grid's spectral
        tail and the density at the window's faces."""
        if error:
            self.step_error()
        g = self.grid
        out = {}
        for pid, p in self.particles.items():
            A = self.absorbed(pid)
            n = self.norm(pid)
            r = {"norm": n, "absorbed": A, "balance": n + sum(A.values()) - 1.0,
                 "balance_tol": BALANCE_EPS * EPS * (self.steps + 1), "active": p.active}
            if p.active:
                key = self._key(p)
                op = self._op(key)
                H = op.H
                psi = backend.to_numpy(p.psi)
                comps = psi if psi.ndim == g.ndim + 1 else psi[None]
                Hpsi = H.apply(comps)
                nn = float(np.real(np.vdot(comps, comps)))
                E = float(np.real(np.vdot(comps, Hpsi)) / nn)
                Hn = math.sqrt(float(np.real(np.vdot(Hpsi, Hpsi))) / nn)
                if p.E_ref is None:  # the reference is the energy now: its time too (review B6-Q13)
                    p.E_ref, p.err_ref, p.t_ref = E, p.err_sum, self.t
                lo, hi = H.bounds()
                e = p.err_sum - p.err_ref
                r["energy"] = {"E": E, "E_ref": p.E_ref, "drift": E - p.E_ref, "since": p.t_ref,
                               "bound": 2 * Hn * e + e * e * max(abs(lo), abs(hi)),
                               "closed": self._arr["loc"] is None and (self._arr["W_tot"] is None or
                                                                         sum(A.values()) < 1e-12)}
                r["step_error"] = {"local": p.err_local, "accumulated": p.err_sum}
                planes = {}
                for plid, pl in self.planes.items():
                    st = p.planes.get(plid) or {}
                    if not st:
                        continue
                    dP = self._beyond(p, op, pl) + st.get("acc_banked", 0.0) - st["P0"]
                    planes[plid] = {"flux_integral": st["F"], "delta_beyond": dP, "mismatch": dP - st["F"],
                                    "since": st["t0"], "valid": st["valid"]}
                r["planes"] = planes
                F = np.fft.fftn(comps, axes=tuple(range(1, g.ndim + 1)))
                w = np.sum(np.abs(F) ** 2, axis=0)
                K = g.kmesh()
                outer = np.zeros(g.shape, bool)
                for i in range(g.ndim):
                    outer |= np.broadcast_to(np.abs(K[i]) > (2.0 / 3.0) * math.pi / g.d[i], g.shape)
                r["spectral_tail"] = float(w[outer].sum() / w.sum())
                rho = np.sum(np.abs(comps) ** 2, axis=0)
                face = 0.0
                for i in range(g.ndim):
                    sl = [slice(None)] * g.ndim
                    for j in (0, -1):
                        sl[i] = j
                        face = max(face, float(rho[tuple(sl)].max()))
                r["window_face"] = face / max(float(rho.max()), 1e-300)
            out[pid] = r
        return out

    # --- cost -------------------------------------------------------------------------------------------------------
    def cost_estimate(self) -> dict:
        """Seconds per scene step: from the measured RATES (log-log interpolation in the number of points) for the
        device the scene runs on and each particle's wave (scalar or spinor, with or without A), plus the running
        measured speed of this scene; the playground's real-time budget is 1 / (seconds per step) steps per second."""
        dev = self.device or ("cpu" if self.device_mode == "cpu" or not backend.devices()["gpu"]["available"]
                              else "gpu")
        per = []
        for pid, p in self.particles.items():
            if not p.active:
                continue
            kind = ("scalar" if p.kind == "scalar" else "spinor") + ("_A" if (self._arr["A"] is not None and
                                                                              p.species.charge != 0) else "")
            pts = RATES[(dev, 3 if self.ndim == 3 else 2, kind)]
            x = np.log([q for q, _ in pts])
            y = np.log([s for _, s in pts])
            n = math.log(self.grid.size)
            if x[0] <= n <= x[-1]:
                sec = float(np.exp(np.interp(n, x, y)))
            else:  # outside the measured sizes: proportional to the points from the nearest measurement
                q, t = pts[0] if n < x[0] else pts[-1]
                sec = float(t * self.grid.size / q)
            per.append({"id": pid, "kind": kind, "seconds": sec})
        est = sum(d["seconds"] for d in per)
        meas = self._timing["seconds"] / self._timing["steps"] if self._timing["steps"] else None
        return {"device": dev, "points": self.grid.size, "per_step_s": est, "per_particle": per,
                "measured_per_step_s": meas, "note": RATES_NOTE}

    def suggest_dt(self, phase: float = 0.1) -> float:
        """A time step with the largest relevant energy turning by ``phase`` rad per step: the particles' kinetic
        energies (|k| + 3 sigma_k)^2/2m and the range of V."""
        Emax = 0.0
        for p in self.particles.values():
            k = np.array([abs(v) for v in _vec(p.packet.k, self.ndim, "k")])
            s = np.array(_vec(p.packet.sigma, self.ndim, "σ"))
            sk = np.where(np.isfinite(s), 1.0 / (2 * np.where(np.isfinite(s), s, 1.0)), 0.0)
            Emax = max(Emax, float(np.sum((k + 3 * sk) ** 2)) / (2 * p.species.mass))
        V = self._arr["V_e"]
        Emax = max(Emax, float(np.max(np.abs(V))) if V.size else 0.0, 1e-300)
        return phase / Emax

    # --- state ------------------------------------------------------------------------------------------------------
    def state_dict(self) -> dict:
        """The scene as plain data: parameters of the grid, units, edges and objects; per particle its packet, wave,
        records (absorbed per point and banked, the jump clock) and checks' accumulators; the random generator's
        state. ``Scene.from_state_dict`` continues bit-identically."""
        g = self.grid
        parts = []
        for pid, p in sorted(self.particles.items()):
            parts.append({
                "id": pid, "packet": p.packet.params(), "kind": p.kind, "s": p.s,
                "chi": None if p.chi is None else np.array(p.chi),
                "psi": None if p.psi is None else backend.to_numpy(p.psi).copy(),
                "acc": None if p.acc is None else backend.to_numpy(p.acc).copy(),
                "banked": dict(p.banked), "active": p.active, "detected": p.detected,
                "E_jump": p.E_jump, "S_haz": p.S_haz, "E_ref": p.E_ref, "t_ref": p.t_ref,
                "err": [p.err_local, p.err_sum, p.err_since, p.err_ref],
                "sk_extra2": p.sk_extra2,
                "kspec": None if p.kspec is None else [np.array(v) for v in p.kspec],
                "planes": {k: dict(v) for k, v in p.planes.items()},
                "jumps": [(t, np.array(y)) for t, y in p.jumps]})
        return {
            "version": 1,
            "grid": {"shape": list(g.shape), "spacing": g.d.tolist(), "center": g.center.tolist()},
            "units": self.units.params(), "dt": self.dt, "t": self.t, "steps": self.steps,
            "device_mode": self.device_mode, "error_every": int(self.error_every),
            "edges": None if self.edges is None else self.edges.params(),
            "objects": [{"id": oid, "type": ob.TYPE, "params": ob.params()} for oid, ob in self.objects.items()],
            "next": [self._next_obj, self._next_pid, self._next_plane],
            "planes": {k: dict(v) for k, v in self.planes.items()},
            "particles": parts, "rng": self.rng.bit_generator.state, "events": [dict(e) for e in self.events],
            "timing": dict(self._timing)}

    @classmethod
    def from_state_dict(cls, d: dict) -> "Scene":
        gd = d["grid"]
        sc_ = cls(gd["shape"], gd["spacing"], center=gd["center"], dt=d["dt"], units=Units(**d["units"]),
                  edges=None if d["edges"] is None else EdgeLayers(**d["edges"]), device=d["device_mode"])
        objs = {int(o["id"]): OBJECT_TYPES[o["type"]].from_params(o["params"]) for o in d["objects"]}
        for ob in objs.values():
            ob.check(sc_)
        sc_.objects = objs
        sc_._arr = sc_._compute(objs, sc_.edges)
        sc_._next_obj, sc_._next_pid, sc_._next_plane = d["next"]
        sc_.planes = {int(k): dict(v) for k, v in d["planes"].items()}
        sc_.t, sc_.steps = float(d["t"]), int(d["steps"])
        sc_.error_every = int(d.get("error_every", 0))
        for pd in d["particles"]:
            p = _Particle(int(pd["id"]), Packet.from_params(pd["packet"]))
            p.kind, p.s = pd["kind"], int(pd["s"])
            p.chi = None if pd["chi"] is None else np.array(pd["chi"], complex)
            op = sc_._op(sc_._key(p))
            p.psi = None if pd["psi"] is None else op.put(pd["psi"])
            p.acc = None if pd["acc"] is None else sc_.xp.asarray(np.array(pd["acc"], float))
            p.banked, p.active, p.detected = dict(pd["banked"]), bool(pd["active"]), pd["detected"]
            p.E_jump, p.S_haz, p.E_ref, p.t_ref = pd["E_jump"], pd["S_haz"], pd["E_ref"], pd["t_ref"]
            p.err_local, p.err_sum, p.err_since, p.err_ref = pd["err"]
            p.sk_extra2 = float(pd.get("sk_extra2", 0.0))
            p.kspec = None if pd.get("kspec") is None else tuple(np.array(v, float) for v in pd["kspec"])
            p.planes = {int(k): dict(v) for k, v in pd["planes"].items()}
            p.jumps = [(t, np.array(y)) for t, y in pd["jumps"]]
            sc_.particles[p.id] = p
        sc_.rng.bit_generator.state = d["rng"]
        sc_.events = [dict(e) for e in d["events"]]
        sc_._timing = dict(d["timing"])
        return sc_
