# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Maxwell's equations in time by the finite-difference time-domain method on the Yee grid (plan P1, batch B8).

The law: Maxwell's equations in linear, isotropic, possibly dispersive and conducting media,

    dD/dt = curl H - J - sigma E,   dB/dt = -curl E - M,   D = eps_inf E + sum_poles P,   B = mu H,

solved by Yee's scheme (Yee 1966): E and H on staggered nodes of a uniform cubic grid (cell dx), leapfrogged in time
(E at t_n = n dt, H at t_n - dt/2), second order in space and time. Its error is the grid's numerical dispersion,
stated exactly by the dispersion relation

    eps mu sin^2(omega dt / 2) / dt^2 = sum_u sin^2(k_u dx / 2) / dx^2

(``yee_frequency``, ``yee_wavenumber``; the tests measure it against this formula at every angle), plus the
treatment of material surfaces (``fdtd_geometry``), absorbing layers and sources.

* **Units**: normalized, c = eps0 = mu0 = 1 (so the impedance of vacuum is 1 and E, H have the same unit), with a
  length unit a of the user's choice; time is in a / c, frequencies f in c / a (ordinary, omega = 2 pi f), the
  conductivity sigma in eps0 c / a, current densities in (unit of H) / a. ``Units(a_m)`` converts to SI.
* **Grids**: 2-D with fields independent of z: TM_z (Ez, Hx, Hy), TE_z (Hz, Ex, Ey) or both; 3-D full Yee
  (Ex at (i+1/2, j, k), Ey at (i, j+1/2, k), Ez at (i, j, k+1/2), Hx at (i, j+1/2, k+1/2), Hy at (i+1/2, j, k+1/2),
  Hz at (i+1/2, j+1/2, k)). The interior (the user's domain) is [0, Lx] x [0, Ly] (x [0, Lz]), each length the
  realisable one nearest to the request: a whole number of cells, or between a PEC wall (an E plane) and a PMC wall
  (an H plane) an odd number of half cells (0.6 with dx = 0.05 becomes 0.625; ``describe()`` and ``checks()`` report
  the requested and the realised lengths; review B8-fdtd F9); absorbing layers lie outside it.
* **Stability**: the Courant number S = c dt / dx (default 0.5) must keep the scheme stable. Checked before any step
  (a world beyond it is refused with the reason): (1) per medium by the von Neumann amplification matrix (with its
  poles and conductivity) at 257 spatial frequencies of the grid's range (vacuum: S <= 1 / sqrt(D), D the number of
  axes with variation; 1 in 1-D, the "magic time step" at which the scheme is exact), cached by the medium's value;
  (2) over the actual node maps by two sufficient bounds, S <= S_vac sqrt(min_E eps min_H mu) and Gershgorin's on
  eps^-1/2 C^T mu^-1 C eps^-1/2 (review B8-fdtd F11: E nodes of one medium next to H nodes of another can be faster
  than either; sufficient for nodes without poles and conductivity, which use eps_inf there). Not seen: a double root
  exactly on the unit circle (linear growth, at isolated parameter values; the radius test admits 1 + 1e-6). The
  fields are checked for finiteness every 256 steps and at the end of every ``advance``.
* **Boundaries** per axis and side: ``periodic`` (with an optional Bloch wavevector: complex fields,
  F(r + L) = F(r) exp(i k L)), ``pec`` (tangential E = 0 on the integer grid plane), ``pmc`` (tangential H = 0 on the
  half plane: the wall lies half a cell inside the last integer plane), ``pml``: the convolutional PML (Roden & Gedney
  2000) with graded sigma(rho) = sigma_max rho^m, kappa(rho) = 1 + (kappa_max - 1) rho^m,
  alpha(rho) = alpha_max (1 - rho), sigma_max = factor x 0.8 (m + 1) / (dx sqrt(eps mu)) (the usual estimate of the
  optimum, quoted after Taflove & Hagness; their book was not obtained: the reflection this default gives is
  measured in the tests: -88...-95 dB for 10 cells from normal incidence to ~70 deg; at grazing incidence along a
  long boundary (81-87 deg) only -75...-52 dB, so grazing geometries need 16-20 cells (20 cells: -114...-136 dB;
  review B8-fdtd F10); a secondary open source for the estimate: Corbino, arXiv:2603.19056, eq. (29), citing Taflove &
  Hagness); a derivative d/du becomes (1/kappa) d/du + psi_u with
  psi^n = b psi^{n-1} + a (d/du)^n, b = exp(-(sigma/kappa + alpha) dt), a = sigma (b - 1) / (sigma kappa +
  kappa^2 alpha) (Roden & Gedney 2000, as quoted by two open papers: sources/verification_2026-11-04_p1_fdtd.md);
  terminated by a PEC plane.
* **Media** per node: eps_inf, mu, sigma and poles: ``Drude`` (chi = -wp^2 / (w^2 + i gamma w)), ``Lorentz`` (chi =
  d_eps w0^2 / (w0^2 - w^2 - i gamma w)), ``Debye`` (chi = d_eps / (1 - i w tau)), any number of each. The
  Lorentz/Drude polarization P'' + gamma P' + w0^2 P = s E is advanced explicitly by central differences at t_n
  (Young, IEEE TAP 43, 422 (1995): the "Lorentz-Young" scheme of Bidégaray-Fesquet, SIAM J. Numer. Anal. 46, 2551
  (2008), eq. (15), whose amplification matrix the engine's ``amplification_radius`` reproduces to 12 digits); the
  Debye polarization tau P' + P = d_eps E by the trapezoid, solved together with E (the scheme of Joseph, Hagness &
  Taflove, Opt. Lett. 16, 1412 (1991), as Bidégaray-Fesquet gives it, her eq. (10)); the conductivity by the average
  of E^n and E^{n+1}. Her sufficient stability conditions (Young: c_inf dt / dx <= 1/sqrt(2) in 1-D, 1/2 in 2-D, and
  w0 dt <= 2 / sqrt(2 eps_s / eps_inf - 1); Joseph: the vacuum condition) are quoted in a refusal; the engine admits
  by the computed radius, which also admits more (the conditions are sufficient, not necessary). The scheme's own
  permittivity is ``Medium.epsilon_discrete`` (second order in dt); the medium's ``epsilon`` is the model's. PEC
  bodies: an E component is zero where its whole Yee edge lies in the conductor (staircase, first order;
  ``fdtd_geometry``). A medium's model and parameters are the user's (fits of real materials are models:
  ``lfphys.theories.models``); the solver is exact Maxwell for the medium given.
* **Sources** (``fdtd_sources``): soft or hard currents J and M at points, on lines/planes and in boxes, with Gaussian,
  modulated Gaussian, ramped continuous-wave or sampled profiles (a hard E is set after the E update at t_{n+1}, a
  hard H after the H update at t_{n+1/2}: review B8-fdtd F2); the TF/SF plane wave as an exact discrete plane wave of
  the grid (2-D any angle; 3-D any direction within memory; Bloch-periodic slabs at the solver's k_par). ``checks()``
  counts the correction nodes on the total-field box's faces that are not in the background (a body crossing or
  touching a face: the injected wave is then not exact there; F12).
* **Monitors** (``fdtd_monitors``): probes, running DFTs on boxes, Poynting fluxes through planes and closed boxes (time
  and frequency), energies, absorbed power, cross sections and the near-to-far-field transform. The flux monitor
  averages the fields to its face's cell centres and so measures the grid's plane wave weaker than its true flux by a
  closed-form factor, ``monitor_factor`` (normal incidence cos(k dx/2) = 1 - (k dx)^2/8 + ...; checked to 2e-9 on the
  incident wave). Cross sections and incident intensities come with either normalisation (``normalisation="exact"``:
  the true intensity; ``"monitor"``: the incident wave as the monitor measures it, Meep's convention, exact for
  reflection and transmission along the incidence axis; review B8-fdtd F5). Cross-section and near-to-far boxes must
  lie wholly in the scattered- (or total-) field region, else refused.
* **Edits at any moment** (all or nothing; a refused edit leaves the world as it was): add, change or remove a body,
  change the background, add or remove a source or monitor. An edit keeps E and H at every node and changes the update
  coefficients from the next step on (the field energy then changes by (1/2) delta_eps |E|^2: the energy is reported
  by ``energy``); nodes that become PEC have E set to 0; a polarization is kept at nodes whose medium is the same (by
  value) before and after the edit, starts from 0 at nodes that become dispersive or change medium, and is dropped
  where a dispersive medium leaves (review B8-fdtd F3: it was matched by the position in the rebuilt media list); a
  new source acts from the next step (its profile is evaluated at the solver's time, so a pulse whose time has passed
  adds nothing; a plane wave's incident spectrum is counted from the step it was added, F4);
  removing a TF/SF plane wave leaves its field inside the total-field box, which then leaves the box as a free wave
  packet cut off at the box's faces; a new monitor starts its DFT at the current step.
* **Devices**: the field update runs on the CPU (NumPy, vectorised, on ``FDTD_THREADS`` row blocks) or on GPU 0 (a
  CuPy kernel per component, ``lfphys.core.backend`` kernel "em.fdtd", compiled without fused multiply-adds): the same
  floating-point operations in the same order, so a real-field run is bit-identical on both devices (tests); sources,
  monitors and dispersive nodes use the same array expressions on both. fp64 only.
* **State**: ``state_dict`` / ``from_state_dict`` continue bit-identically; ``cost_estimate`` from measured rates.

**Accuracy measured by the tests** (numbers and sources: ``sources/verification_2026-11-04_p1_fdtd.md``; restated
after review B8-fdtd, whose F5 showed that the earlier numbers mixed the flux monitor's own -(k dx)^2/8 into the
scheme's error [error in earlier]): the grid's dispersion relation to 6e-15 at every angle; the 1-D magic time step
exact to 5e-15 (hard sources of E and H to the profile's own 1.5e-8 jump); the discrete energy of a closed box of
non-dispersive media conserved to 3e-16 over 3000 steps; PEC-cavity modes at the grid's exact frequencies (5e-12) and
second order to the continuum; CPML of 10 cells -88...-95 dB up to ~70 deg (20 cells -106...-113 dB; grazing:
above); planar reflection, monitor-normalised, equal to the grid's exact closed form to 1e-4 and second order to
Fresnel (n = 2 at 10 cells per wavelength in the medium: +10.7 % / -10.3 % of R with the interface on an H / E node —
the scheme's own error); the TF/SF leak 2-3e-9 for pulses away from a Bloch wave's cut-off (near it ~0.3-0.4 x the
window tail, refused above 1e-6; a continuous wave: up to 4e-4 while its ramp lasts); a dielectric cylinder's Q_sca
(m = 1.5) at 40 cells per unit TM +0.03...+0.06 % (exact intensity) / +0.10...+0.37 % (monitor's), second order, TE
-0.12...+0.29 % / -0.07...+0.60 %, not monotone (the diagonal averaging; at eps = 6 TE converges at first order:
2.6, 1.4, 0.8 % at 40, 80, 160 cells); neither normalisation separates the scheme's error from the monitor's on the
scattered waves, which is of the same size; a PEC cylinder's (staircase, first order) TM -1.6...-2.0 %, TE
-1.7...+1.0 %; a sphere's Q_sca at 32 cells per unit -0.01...+0.76 % (exact) / +0.16...+0.84 % (monitor's) of Mie; a
dipole's power within 2 % at 20 cells per wavelength; against Meep 1.35 (like-normalised): the same discrete
reflectance to 1e-6 (slab) and 6e-6 (Drude, whose update differs from Meep's at second order), cylinders within both
codes' coarser-grid errors (20 rows, ``tests/external``).
"""

from __future__ import annotations

import json
import math
import os
import time

import numpy as np

from .. import backend
from . import fdtd_geometry as geo
from . import fdtd_monitors as mon
from . import fdtd_sources as src
from .fdtd_geometry import Box, Cylinder, HalfSpace, Mask, Polygon, Sphere  # noqa: F401 (public API)
from .fdtd_sources import (ContinuousWave, CurrentSource, Custom, GaussianPulse, ModulatedGaussian,  # noqa: F401
                           PlaneWave, Samples, yee_frequency, yee_normal_wavenumber, yee_wavenumber)

ABOUT = {
    "layer": "core", "kind": "numerical solution",
    "title": "Уравнения Максвелла во времени: метод FDTD (сетка Йи) в 2-D и 3-D",
    "statement": "Уравнения Максвелла в линейных изотропных средах (диэлектрики, магнетики, проводники, "
                 "диспергирующие среды Друде, Лоренца и Дебая, идеальный проводник) решаются схемой Йи: 2-D (TM и TE) "
                 "и 3-D; поглощающие слои CPML, стенки PEC и PMC, периодические стороны с фазой Блоха; точечные и "
                 "протяжённые токи, плоская волна методом полного/рассеянного поля; спектры, потоки Пойнтинга, "
                 "энергия, поглощение, сечения рассеяния и дальнее поле; правки сцены во время счёта.",
    "validity": "классическая электродинамика линейных изотропных сред (нет нелинейности, анизотропии, "
                "движущихся сред); погрешность схемы — численная дисперсия второго порядка (точное дисперсионное "
                "соотношение сетки проверено до 6e-15); границы тел: ступенька (1-й порядок для кривых; PEC-цилиндр "
                "TM −1.6…−2.0 % при 40 ячейках на единицу) или усреднение по ячейке — только диагональ тензора "
                "Фарджадпура (по их классификации схема VP-EP): 2-й порядок для плоских границ вдоль осей и для E "
                "вдоль оси цилиндра (TM), для E в плоскости кривой границы в общем случае 1-й порядок (цилиндр ε = 6, "
                "TE: 2.6 → 1.4 → 0.8 % при 40/80/160 ячейках); монитор потока видит плоскую волну слабее на "
                "множитель 1 − O((k dx)²) (cos(k dx/2) при нормальном падении), поэтому сечения даются в двух "
                "нормировках — по точной интенсивности и по интенсивности, измеренной тем же монитором (как в Meep); "
                "диэлектрический цилиндр m = 1.5 при 40 ячейках: TM +0.03…+0.06 % / +0.10…+0.37 %, TE −0.12…+0.29 % / "
                "−0.07…+0.60 %; шар при 32 ячейках −0.01…+0.76 % / +0.16…+0.84 % от Ми (ошибка схемы и ошибка "
                "монитора на рассеянных волнах одного порядка и не разделены); отражение плоской границы на грубой "
                "сетке — до ~11 % R при 10 ячейках на длину волны в среде (собственная ошибка схемы, второй порядок); "
                "CPML −88…−95 дБ при 10 ячейках от нормали до ~70°, у скользящего падения (81–87°) лишь −75…−52 дБ — "
                "там нужно 16–20 ячеек; длина оси — ближайшая реализуемая на сетке (между стенками PEC и PMC — "
                "нечётное число полуячеек; отклонение от заданной показывает checks()); устойчивость проверяется до "
                "счёта по каждой среде и по картам узлов (двойной корень на единичной окружности не виден); "
                "диспергирующие среды — модели пользователя (полюса), ε(ω) схемы отличается от модели на O(Δt²); "
                "energy() не включает энергию поляризации",
    "basis": ["Yee, IEEE Trans. Antennas Propag. 14, 302 (1966) — схема",
              "Schneider, Understanding the FDTD Method (2010) — дисперсионное соотношение (7.34), «магический» шаг "
              "(§7.4), отражение от границы на сетке (7.72), (7.90), TF/SF (§3.10, §8.5)",
              "Roden & Gedney, Microw. Opt. Technol. Lett. 27, 334 (2000) — CPML (формулы по двум открытым статьям); "
              "оценка σ_max: Corbino, arXiv:2603.19056, ур. (29), со ссылкой на Taflove & Hagness",
              "Farjadpour et al., Opt. Lett. 31, 2972 (2006), ур. (1) — усреднение на границах (движок берёт "
              "диагональ: схема VP-EP по их классификации)",
              "Young, IEEE Trans. Antennas Propag. 43, 422 (1995) — явная схема полюсов Лоренца/Друде; Joseph, Hagness "
              "& Taflove, Opt. Lett. 16, 1412 (1991) — трапеция Дебая (обе статьи не получены; схемы — как их "
              "приводит Bidégaray-Fesquet)",
              "Bidégaray-Fesquet, SIAM J. Numer. Anal. 46, 2551 (2008), arXiv:math/0506289 — устойчивость этих схем "
              "(матрица перехода совпадает с amplification_radius; достаточные условия — в отказе)"],
    "conflicts": [],
}

KERNEL = "em.fdtd"
FORMAT = "lfphys.fdtd/1"
COMPS = ("ex", "ey", "ez", "hx", "hy", "hz")
AXES = "xyz"
TWO_PI = 2.0 * math.pi
FDTD_THREADS = int(os.environ.get("LFPHYS_FDTD_THREADS", "0")) or min(4, os.cpu_count() or 1)
MIN_BLOCK_CELLS = 65536


class Unstable(RuntimeError):
    """The world's parameters make the scheme unstable (raised before any step), or the fields blew up."""


# --- units ------------------------------------------------------------------------------------------------------------
class Units:
    """SI values of the normalized units for a length unit ``a_m`` (metres) and a field scale ``E0`` (V/m per unit of
    E): time a / c, frequency c / a, H in E0 / eta0 (A/m), power flux E0^2 / eta0 (W/m^2)."""

    def __init__(self, a_m: float, E0: float = 1.0):
        from scipy.constants import c, epsilon_0, mu_0
        self.a, self.E0 = float(a_m), float(E0)
        self.c, self.eps0, self.mu0 = c, epsilon_0, mu_0
        self.eta0 = math.sqrt(mu_0 / epsilon_0)

    def time(self, t):
        return np.asarray(t) * self.a / self.c

    def frequency(self, f):
        return np.asarray(f) * self.c / self.a

    def wavelength(self, f):
        return self.a / np.asarray(f)

    def H(self, h):
        return np.asarray(h) * self.E0 / self.eta0

    def intensity(self, s):
        return np.asarray(s) * self.E0 ** 2 / self.eta0

    def conductivity(self, sigma):
        return np.asarray(sigma) * self.eps0 * self.c / self.a

    def params(self):
        return {"a_m": self.a, "E0": self.E0}


# --- media ------------------------------------------------------------------------------------------------------------
class Drude:
    """chi(f) = -fp^2 / (f^2 + i gamma f) (fp, gamma in frequency units: omega_p = 2 pi fp, rate 2 pi gamma)."""
    kind = "drude"

    def __init__(self, plasma_frequency: float, gamma: float = 0.0):
        self.fp, self.gamma = float(plasma_frequency), float(gamma)
        if not self.fp > 0 or self.gamma < 0:
            raise ValueError("Друде: плазменная частота > 0, затухание ≥ 0")

    def ode(self):  # (w0^2, gamma, s) of P'' + gamma P' + w0^2 P = s E
        return 0.0, TWO_PI * self.gamma, (TWO_PI * self.fp) ** 2

    def chi(self, f):
        w = TWO_PI * np.asarray(f, float)
        return -(TWO_PI * self.fp) ** 2 / (w * w + 1j * TWO_PI * self.gamma * w)

    def params(self):
        return {"kind": self.kind, "plasma_frequency": self.fp, "gamma": self.gamma}


class Lorentz:
    """chi(f) = d_eps f0^2 / (f0^2 - f^2 - i gamma f)."""
    kind = "lorentz"

    def __init__(self, delta_eps: float, frequency: float, gamma: float = 0.0):
        self.de, self.f0, self.gamma = float(delta_eps), float(frequency), float(gamma)
        if not self.f0 > 0 or self.gamma < 0:
            raise ValueError("Лоренц: резонансная частота > 0, затухание ≥ 0")

    def ode(self):
        w0 = TWO_PI * self.f0
        return w0 * w0, TWO_PI * self.gamma, self.de * w0 * w0

    def chi(self, f):
        w = TWO_PI * np.asarray(f, float)
        w0 = TWO_PI * self.f0
        return self.de * w0 * w0 / (w0 * w0 - w * w - 1j * TWO_PI * self.gamma * w)

    def params(self):
        return {"kind": self.kind, "delta_eps": self.de, "frequency": self.f0, "gamma": self.gamma}


class Debye:
    """chi(f) = d_eps / (1 - i omega tau)."""
    kind = "debye"

    def __init__(self, delta_eps: float, tau: float):
        self.de, self.tau = float(delta_eps), float(tau)
        if not self.tau > 0:
            raise ValueError("Дебай: время релаксации > 0")

    def chi(self, f):
        w = TWO_PI * np.asarray(f, float)
        return self.de / (1 - 1j * w * self.tau)

    def params(self):
        return {"kind": self.kind, "delta_eps": self.de, "tau": self.tau}


def pole_from_params(d):
    return {"drude": lambda: Drude(d["plasma_frequency"], d["gamma"]),
            "lorentz": lambda: Lorentz(d["delta_eps"], d["frequency"], d["gamma"]),
            "debye": lambda: Debye(d["delta_eps"], d["tau"])}[d["kind"]]()


class Medium:
    """A linear isotropic medium: ``eps`` (eps_inf), ``mu``, conductivity ``sigma`` and ``poles`` (Drude, Lorentz,
    Debye). ``Medium.pec()``: a perfect electric conductor."""

    def __init__(self, eps: float = 1.0, mu: float = 1.0, sigma: float = 0.0, poles=(), pec: bool = False,
                 label: str = ""):
        self.eps, self.mu, self.sigma = float(eps), float(mu), float(sigma)
        self.poles = tuple(poles)
        self.is_pec = bool(pec)
        self.label = str(label)
        if not (self.eps > 0 and self.mu > 0 and self.sigma >= 0):
            raise ValueError("среда: eps > 0, mu > 0, sigma ≥ 0")
        for p in self.poles:
            if not isinstance(p, (Drude, Lorentz, Debye)):
                raise ValueError("полюса среды: Drude, Lorentz или Debye")

    @classmethod
    def pec(cls, label: str = "PEC"):
        return cls(pec=True, label=label)

    @property
    def dispersive(self) -> bool:
        return bool(self.poles)

    @property
    def plain(self) -> bool:
        """No poles, no conductivity, not PEC: the medium may be averaged at surfaces."""
        return not (self.poles or self.sigma > 0 or self.is_pec)

    def epsilon(self, f):
        """The model's relative permittivity eps(f) (exp(-i omega t)): eps_inf + sum chi + i sigma / omega."""
        f = np.asarray(f, float)
        e = self.eps + 0j * f
        for p in self.poles:
            e = e + p.chi(f)
        if self.sigma:
            e = e + 1j * self.sigma / (TWO_PI * f)
        return e

    def epsilon_discrete(self, f, dt: float):
        """The permittivity the scheme realises for a field exp(-i omega t) sampled at the time step dt (it tends to
        ``epsilon`` as dt -> 0, error O(dt^2))."""
        w = TWO_PI * np.asarray(f, float)
        Om = 2.0 / dt * np.sin(w * dt / 2.0)
        cs = np.cos(w * dt / 2.0)
        e = self.eps + 0j * w
        for p in self.poles:
            if isinstance(p, Debye):
                e = e + p.de / (1 - 1j * p.tau * Om / cs)
            else:
                w02, g, s = p.ode()
                e = e + s / (w02 - Om * Om - 1j * g * np.sin(w * dt) / dt)
        if self.sigma:
            e = e + 1j * self.sigma * cs / Om
        return e

    def index(self, f):
        """Complex refractive index sqrt(eps mu) on the branch Im n >= 0."""
        n = np.sqrt(self.epsilon(f) * self.mu + 0j)
        return np.where(np.imag(n) < 0, -n, n)

    def params(self):
        return {"eps": self.eps, "mu": self.mu, "sigma": self.sigma, "poles": [p.params() for p in self.poles],
                "pec": self.is_pec, "label": self.label}

    @classmethod
    def from_params(cls, d):
        return cls(d["eps"], d["mu"], d["sigma"], [pole_from_params(p) for p in d["poles"]], d["pec"],
                   d.get("label", ""))


VACUUM = Medium(label="вакуум")


def _medium_key(m: Medium) -> str:
    """The medium's physics as a string (its label left out): two media with the same key have the same update
    coefficients and the same pole layout (review B8-fdtd F1, F3: media are compared by value, not by ``id``)."""
    p = m.params()
    p.pop("label", None)
    return json.dumps(p, sort_keys=True)


def _pole_coeffs(m: Medium, dt: float):
    """(lorentz list of (c1, c2, c3), debye list of (aD, bD), sum bD) for a medium."""
    L, D = [], []
    for p in m.poles:
        if isinstance(p, Debye):
            r = p.tau / dt
            D.append(((r - 0.5) / (r + 0.5), (p.de / 2.0) / (r + 0.5)))
        else:
            w02, g, s = p.ode()
            q = 1.0 + g * dt / 2.0
            L.append(((2.0 - w02 * dt * dt) / q, -(1.0 - g * dt / 2.0) / q, s * dt * dt / q))
    return L, D, float(sum(b for _, b in D))


def amplification_radius(m: Medium, dt: float, lams, mu: float | None = None) -> float:
    """Largest spectral radius of the one-step map of the scheme in medium ``m`` over the curl-curl eigenvalues
    ``lams`` (the von Neumann analysis; > 1 means unstable)."""
    if m.is_pec:
        return 0.0
    mu = m.mu if mu is None else mu
    L, D, sb = _pole_coeffs(m, dt)
    den = m.eps + m.sigma * dt / 2.0 + sb
    ca = (m.eps - m.sigma * dt / 2.0 - sb) / den
    cb, cx = dt / den, 1.0 / den
    nL, nD = len(L), len(D)
    N = 2 + 2 * nL + nD
    worst = 0.0
    for lam in lams:
        r = math.sqrt(max(lam, 0.0))
        M = np.zeros((N, N))
        for j in range(N):
            x = np.zeros(N)
            x[j] = 1.0
            E, H = x[0], x[1]
            P, Pm, PD = x[2:2 + nL], x[2 + nL:2 + 2 * nL], x[2 + 2 * nL:]
            H1 = H - dt / mu * r * E
            P1 = np.array([c1 * P[i] + c2 * Pm[i] + c3 * E for i, (c1, c2, c3) in enumerate(L)])
            X = float(np.sum(P1 - P)) + float(sum((aD - 1.0) * PD[i] for i, (aD, _) in enumerate(D)))
            E1 = ca * E + cb * r * H1 - cx * X
            PD1 = np.array([aD * PD[i] + bD * (E1 + E) for i, (aD, bD) in enumerate(D)])
            M[:, j] = np.concatenate([[E1, H1], P1, P, PD1])
        worst = max(worst, float(np.max(np.abs(np.linalg.eigvals(M)))))
    return worst


# --- absorbing layers -------------------------------------------------------------------------------------------------
class PML:
    """Convolutional PML: ``cells`` thick, grading order ``m``, sigma_max = ``sigma_factor`` x the optimum
    0.8 (m + 1) / (dx sqrt(eps mu)), ``kappa_max``, ``alpha_max`` (in 1 / time) with linear grading of alpha."""

    def __init__(self, cells: int = 10, m: float = 3.0, sigma_factor: float = 1.0, kappa_max: float = 1.0,
                 alpha_max: float = 0.0):
        self.cells, self.m = int(cells), float(m)
        self.sigma_factor, self.kappa_max, self.alpha_max = float(sigma_factor), float(kappa_max), float(alpha_max)
        if self.cells < 1 or self.m < 0 or self.sigma_factor < 0 or self.kappa_max < 1 or self.alpha_max < 0:
            raise ValueError("PML: cells ≥ 1, m ≥ 0, sigma_factor ≥ 0, kappa_max ≥ 1, alpha_max ≥ 0")

    def params(self):
        return {"cells": self.cells, "m": self.m, "sigma_factor": self.sigma_factor, "kappa_max": self.kappa_max,
                "alpha_max": self.alpha_max}


def _as_pml(p) -> PML:
    if isinstance(p, PML):
        return p
    if isinstance(p, dict):
        return PML(**p)
    return PML(int(p))


# --- CUDA kernels -----------------------------------------------------------------------------------------------------
_CUDA_BODY = r"""
extern "C" __global__ void fdtd_update(
    T* __restrict__ F, const T* __restrict__ S1, const T* __restrict__ S2,
    const double* __restrict__ cf, const double* __restrict__ ca, const double cfs,
    T* __restrict__ psi1, const double* __restrict__ b1, const double* __restrict__ a1, const double* __restrict__ k1,
    const int lo1, const int hi1,
    T* __restrict__ psi2, const double* __restrict__ b2, const double* __restrict__ a2, const double* __restrict__ k2,
    const int lo2, const int hi2,
    const int n0, const int n1, const int n2, const T ph1, const T ph2, const double rd)
{
    const long long N = (long long)n0 * n1 * n2;
    const long long idx = (long long)blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= N) return;
    const int c2 = (int)(idx % n2);
    const long long r = idx / n2;
    const int c1 = (int)(r % n1);
    const int c0 = (int)(r / n1);
    const int cc[3] = {c0, c1, c2};
    const int nn[3] = {n0, n1, n2};
    const long long st[3] = {(long long)n1 * n2, (long long)n2, 1LL};
#if HAS1
    T d1;
    {
        const int cv = cc[AX1]; const int nv = nn[AX1]; const long long sv = st[AX1];
        const T here = S1[idx];
#if KIND_E
        T nb = (cv > 0) ? S1[idx - sv] : PHB1(S1[idx + (long long)(nv - 1) * sv]);
        d1 = (here - nb) * rd;
#else
        T nb = (cv < nv - 1) ? S1[idx + sv] : PHF1(S1[idx - (long long)(nv - 1) * sv]);
        d1 = (nb - here) * rd;
#endif
        if ((lo1 > 0 && cv < lo1) || (hi1 > 0 && cv >= nv - hi1)) {
            const int L = lo1 + hi1;
            const int q = (cv < lo1) ? cv : cv - (nv - hi1) + lo1;
            long long p;
            if (AX1 == 0) p = ((long long)q * n1 + c1) * n2 + c2;
            else if (AX1 == 1) p = ((long long)c0 * L + q) * n2 + c2;
            else p = ((long long)c0 * n1 + c1) * L + q;
            const T ps = b1[cv] * psi1[p] + a1[cv] * d1;
            psi1[p] = ps;
            d1 = d1 * k1[cv] + ps;
        }
    }
#endif
#if HAS2
    T d2;
    {
        const int cv = cc[AX2]; const int nv = nn[AX2]; const long long sv = st[AX2];
        const T here = S2[idx];
#if KIND_E
        T nb = (cv > 0) ? S2[idx - sv] : PHB2(S2[idx + (long long)(nv - 1) * sv]);
        d2 = (here - nb) * rd;
#else
        T nb = (cv < nv - 1) ? S2[idx + sv] : PHF2(S2[idx - (long long)(nv - 1) * sv]);
        d2 = (nb - here) * rd;
#endif
        if ((lo2 > 0 && cv < lo2) || (hi2 > 0 && cv >= nv - hi2)) {
            const int L = lo2 + hi2;
            const int q = (cv < lo2) ? cv : cv - (nv - hi2) + lo2;
            long long p;
            if (AX2 == 0) p = ((long long)q * n1 + c1) * n2 + c2;
            else if (AX2 == 1) p = ((long long)c0 * L + q) * n2 + c2;
            else p = ((long long)c0 * n1 + c1) * L + q;
            const T ps = b2[cv] * psi2[p] + a2[cv] * d2;
            psi2[p] = ps;
            d2 = d2 * k2[cv] + ps;
        }
    }
#endif
#if HAS1 && HAS2
    const T curl = d1 - d2;
#elif HAS1
    const T curl = d1;
#else
    const T curl = -d2;
#endif
#if KIND_E
#if CA_ARRAY
    F[idx] = ca[idx] * F[idx] + cf[idx] * curl;
#else
    F[idx] = F[idx] + cf[idx] * curl;
#endif
#else
#if CF_ARRAY
    F[idx] = F[idx] - cf[idx] * curl;
#else
    F[idx] = F[idx] - cfs * curl;
#endif
#endif
}
"""

_GPU_MODULES: dict = {}


def _gpu_kernel(cp, kind_e: bool, ax1, ax2, cplx: bool, bloch1: bool, bloch2: bool, ca_array: bool, cf_array: bool):
    head = []
    if cplx:
        head.append("#include <cupy/complex.cuh>")
        head.append("typedef complex<double> T;")
    else:
        head.append("typedef double T;")
    head += [f"#define KIND_E {int(kind_e)}", f"#define HAS1 {int(ax1 is not None)}", f"#define HAS2 {int(ax2 is not None)}",
             f"#define AX1 {ax1 if ax1 is not None else 0}", f"#define AX2 {ax2 if ax2 is not None else 0}",
             f"#define CA_ARRAY {int(ca_array)}", f"#define CF_ARRAY {int(cf_array)}"]
    head.append("#define PHB1(x) ((x) * conj(ph1))" if bloch1 else "#define PHB1(x) (x)")
    head.append("#define PHB2(x) ((x) * conj(ph2))" if bloch2 else "#define PHB2(x) (x)")
    head.append("#define PHF1(x) ((x) * ph1)" if bloch1 else "#define PHF1(x) (x)")
    head.append("#define PHF2(x) ((x) * ph2)" if bloch2 else "#define PHF2(x) (x)")
    code = "\n".join(head) + _CUDA_BODY
    if code not in _GPU_MODULES:
        _GPU_MODULES[code] = cp.RawModule(code=code, options=("--fmad=false", "-std=c++17"))
    return _GPU_MODULES[code].get_function("fdtd_update")


# --- measured speeds (cost_estimate) ----------------------------------------------------------------------------------
# (cells, seconds per step) measured 2026-11-04 by ``bench`` (a periodic vacuum world, best of one run of 3-20 steps
# after a warm-up): 2-D TM (3 components), 3-D (6 components); CPU = the image's NumPy on up to 4 threads
# (FDTD_THREADS) in a container with 16 CPUs of an i9-9900K; GPU = RTX 2080 Ti (GPU 0), fp64, the state on the device.
# GPU / CPU: 2-D x1.0 at 64^2, x2.3 at 128^2, x7.6 at 256^2, x19 at 512^2, x58 at 1024^2, x71 at 2048^2, x67 at 4096^2
# (6.3 Gcell/s); 3-D x6 at 32^3, x25 at 64^3, x74 at 96^3, x80 at 128^3, x82 at 192^3, x76 at 256^3 (2.6 Gcell/s).
# Below ~512^2 the GPU's step is the ~60 us of its kernel launches from Python; sources, monitors and dispersive nodes
# add launches of their own (each a few us on the GPU, less on the CPU for small worlds).
RATES = {
    "2d": {"cpu": [(64 ** 2, 6.32e-5), (128 ** 2, 1.39e-4), (256 ** 2, 4.56e-4), (512 ** 2, 1.17e-3),
                   (1024 ** 2, 1.04e-2), (2048 ** 2, 4.79e-2), (4096 ** 2, 1.78e-1)],
           "gpu": [(64 ** 2, 6.45e-5), (128 ** 2, 5.95e-5), (256 ** 2, 6.00e-5), (512 ** 2, 6.05e-5),
                   (1024 ** 2, 1.81e-4), (2048 ** 2, 6.77e-4), (4096 ** 2, 2.67e-3)]},
    "3d": {"cpu": [(32 ** 3, 7.53e-4), (64 ** 3, 3.21e-3), (96 ** 3, 2.79e-2), (128 ** 3, 6.76e-2),
                   (192 ** 3, 2.29e-1), (256 ** 3, 4.98e-1)],
           "gpu": [(32 ** 3, 1.22e-4), (64 ** 3, 1.29e-4), (96 ** 3, 3.77e-4), (128 ** 3, 8.44e-4),
                   (192 ** 3, 2.78e-3), (256 ** 3, 6.52e-3)]},
}
RATES_NOTE = ("измерено 2026-11-04 (вакуум, периодические стороны): CPU (NumPy, до 4 потоков) 2-D 64²…4096² — "
              "0.06…178 мс/шаг, 3-D 32³…256³ — 0.75…498 мс/шаг; GPU 0 (RTX 2080 Ti, fp64) 2-D 0.06…2.7 мс/шаг, "
              "3-D 0.12…6.5 мс/шаг; GPU быстрее с 128² в 2-D (×2.3; ×67 на 4096²) и с 32³ в 3-D (×6; ×76 на 256³)")


def _interp_rate(key: str, dev: str, cells: int) -> float:
    pts = RATES[key][dev]
    x = np.log([q for q, _ in pts])
    y = np.log([s for _, s in pts])
    n = math.log(max(cells, 1))
    if x[0] <= n <= x[-1]:
        return float(np.exp(np.interp(n, x, y)))
    q, t = pts[0] if n < x[0] else pts[-1]
    return float(t * cells / q) if n > x[-1] else float(t)


# --- the solver -------------------------------------------------------------------------------------------------------
def _side_kinds(b):
    if isinstance(b, str):
        if b == "periodic":
            return ("periodic", "periodic")
        return (b, b)
    lo, hi = b
    return (lo, hi)


_PML_GRADE_ALPHA = 1.0


class FDTD:
    """Maxwell's equations on the Yee grid.

    ``size``: (Lx, Ly) for 2-D or (Lx, Ly, Lz) for 3-D (the interior, in the length unit); ``dx``: the cell;
    ``pol`` (2-D): "tm" (Ez, Hx, Hy), "te" (Hz, Ex, Ey) or "both"; ``courant``: S = c dt / dx (default 0.5);
    ``boundary``: one kind for all axes or {"x": kind or (lo, hi), ...} with kinds "pml", "pec", "pmc",
    "periodic" (default "pml"); ``pml``: cells or ``PML``; ``bloch``: the Bloch wavevector (2 pi / length; complex
    fields) on periodic axes; ``background``: a ``Medium`` without poles or conductivity; ``averaging``: "subpixel"
    (default) or "staircase"; ``device``: "auto" | "cpu" | "gpu".
    """

    def __init__(self, size, dx: float, pol: str = "tm", courant: float = 0.5, boundary="pml", pml=10, bloch=None,
                 background: Medium | None = None, averaging: str = "subpixel", device: str = "auto"):
        size = tuple(float(s) for s in size)
        if len(size) not in (2, 3) or any(not s > 0 for s in size):
            raise ValueError("размер области: (Lx, Ly) или (Lx, Ly, Lz), все > 0")
        self.dim = len(size)
        self.dx = float(dx)
        if not self.dx > 0:
            raise ValueError("dx > 0")
        if self.dim == 2:
            if pol not in ("tm", "te", "both"):
                raise ValueError("поляризация в 2-D: tm, te или both")
            self.pol = pol
            comps = {"tm": ("ez", "hx", "hy"), "te": ("ex", "ey", "hz"), "both": COMPS}[pol]
        else:
            self.pol = "3d"
            comps = COMPS
        self.comps = tuple(c for c in COMPS if c in comps)
        self.courant = float(courant)
        self.dt = self.courant * self.dx
        if averaging not in ("subpixel", "staircase"):
            raise ValueError("усреднение: subpixel или staircase")
        self.averaging = averaging
        self.background = VACUUM if background is None else background
        if not self.background.plain:
            raise ValueError("фон: среда без полюсов, проводимости и не PEC")
        self.device_mode = device
        self._pml_spec = _as_pml(pml)
        # boundaries
        if isinstance(boundary, (str, tuple, list)) and not isinstance(boundary, dict):
            bd = {AXES[u]: boundary for u in range(self.dim)}
        else:
            bd = {AXES[u]: boundary.get(AXES[u], "pml") for u in range(self.dim)}
        self.boundary = {}
        for u in range(self.dim):
            lo, hi = _side_kinds(bd[AXES[u]])
            for k in (lo, hi):
                if k not in ("pml", "pec", "pmc", "periodic"):
                    raise ValueError(f"граница {k!r}: pml, pec, pmc или periodic")
            if (lo == "periodic") != (hi == "periodic"):
                raise ValueError("периодическая граница — с обеих сторон оси")
            self.boundary[AXES[u]] = (lo, hi)
        bl = [0.0, 0.0, 0.0] if bloch is None else [float(v) for v in bloch] + [0.0] * (3 - len(bloch))
        self.bloch = np.array(bl[:3])
        for u in range(self.dim):
            if self.bloch[u] != 0 and self.boundary[AXES[u]][0] != "periodic":
                raise ValueError(f"фаза Блоха только на периодической оси ({AXES[u]})")
        self.complex = bool(np.any(self.bloch != 0))
        # grid
        self.shape, self.off, self.npml, self.periodic = [], [], [], []
        self.interior = []
        self.size_requested = list(size)
        P = self._pml_spec.cells
        for u in range(3):
            if u >= self.dim:
                self.shape.append(1)
                self.off.append(0.0)
                self.npml.append((0, 0))
                self.periodic.append(True)
                self.interior.append(0.0)
                continue
            lo, hi = self.boundary[AXES[u]]
            # the realisable length nearest to the requested one (review B8-fdtd F9): a PEC wall lies on an E plane
            # (integer index), a PMC wall on an H plane (half-integer), so between a PEC and a PMC wall the length is
            # an odd multiple of dx/2; next to a PML side the interior's edge is free and is put on the plane that
            # makes the length a whole number of cells
            walls = sorted(k for k in (lo, hi) if k in ("pec", "pmc"))
            if walls == ["pec", "pmc"]:
                m = int(math.floor(size[u] / self.dx + 1e-9)) + 0.5
            else:
                m = int(round(size[u] / self.dx))
            if m < 1:
                raise ValueError(f"ось {AXES[u]}: меньше одной ячейки")
            elo = {"pec": 0.0, "pmc": 0.5, "pml": float(P), "periodic": 0.0}[lo]
            ehi = {"pec": 0.0, "pmc": 0.5, "pml": float(P), "periodic": 0.0}[hi]
            if (lo, hi) == ("pml", "pmc"):
                elo = P + 0.5
            elif (lo, hi) == ("pmc", "pml"):
                ehi = P + 0.5
            n = int(math.ceil(m + elo + ehi - 1e-9))
            if lo != "periodic" and n < 2:
                raise ValueError(f"ось {AXES[u]}: непериодическая ось короче двух ячеек")
            self.shape.append(n)
            self.off.append(elo)
            self.npml.append((P if lo == "pml" else 0, P if hi == "pml" else 0))
            self.periodic.append(lo == "periodic")
            self.interior.append((n - elo - ehi) * self.dx)
        self.shape = tuple(self.shape)
        self.N = int(np.prod(self.shape))
        self.deriv = [u < self.dim and (self.shape[u] > 1 or self.bloch[u] != 0) for u in range(3)]
        self.phase = [complex(np.exp(1j * self.bloch[u] * self.shape[u] * self.dx)) for u in range(3)]
        self.rd = 1.0 / self.dx
        self.dV = self.dx ** self.dim
        self.lam_max = 0.0
        for u in range(3):
            if not self.deriv[u]:
                continue
            if self.shape[u] > 1:
                self.lam_max += 4.0 / self.dx ** 2
            else:
                self.lam_max += 4.0 / self.dx ** 2 * math.sin(self.bloch[u] * self.dx / 2) ** 2
        self.courant_limit = 2.0 / (self.dx * math.sqrt(self.lam_max)) if self.lam_max > 0 else math.inf
        # terms of the curl per component: (derivative axis, source component, sign)
        self._terms = {}
        for c in self.comps:
            a = AXES.index(c[1])
            p, q = (a + 1) % 3, (a + 2) % 3
            other = "h" if c[0] == "e" else "e"
            t = []
            for v, s, sign in ((p, other + AXES[q], 1), (q, other + AXES[p], -1)):
                if self.deriv[v] and s in self.comps:
                    t.append((v, s, sign))
            self._terms[c] = t
        self._media_check_cache = {}
        self._check_medium(self.background, "фон")
        # state
        self.xp, self.device = np, "cpu"
        dtype = complex if self.complex else float
        self.F = {c: np.zeros(self.shape, dtype) for c in self.comps}
        self.steps = 0
        self.t = 0.0
        self._bodies = {}
        self._next_body = 1
        self._sources = {}
        self._next_source = 1
        self._monitors = {}
        self._next_monitor = 1
        self._timing = {"steps": 0, "seconds": 0.0}
        self._reason = ""
        self._build_pml()
        self._build_materials(first=True)
        self._build_sources()
        self._choose()

    # --- coordinates ----------------------------------------------------------------------------------------------
    @staticmethod
    def offset_of(comp: str, u: int) -> float:
        a = AXES.index(comp[1])
        if comp[0] == "e":
            return 0.5 if u == a else 0.0
        return 0.0 if u == a else 0.5

    def offset(self, comp: str, u: int) -> float:
        if u >= self.dim:
            return 0.0
        return self.offset_of(comp, u)

    def coord(self, index, u: int):
        """Coordinate of (possibly fractional) index along axis u."""
        return (np.asarray(index, float) - self.off[u]) * self.dx

    def coords(self, comp: str):
        """Node coordinates (x, y[, z]) of a component, as 1-D arrays per axis."""
        out = []
        for u in range(self.dim):
            out.append(self.coord(np.arange(self.shape[u]) + self.offset(comp, u), u))
        return tuple(out)

    def index_of(self, x, u: int, off: float = 0.0) -> float:
        return float(x) / self.dx + self.off[u] - off

    def _mesh(self, comp, lo_idx=None, hi_idx=None):
        ax = []
        for u in range(3):
            a = 0 if lo_idx is None else lo_idx[u]
            b = self.shape[u] if hi_idx is None else hi_idx[u]
            if u < self.dim:
                ax.append(self.coord(np.arange(a, b) + self.offset(comp, u), u))
        return np.meshgrid(*ax, indexing="ij", sparse=True)

    # --- stability ------------------------------------------------------------------------------------------------
    def _medium_radius(self, m: Medium) -> float:
        """The largest spectral radius of the one-step map in medium ``m`` (cached by the medium's value and dt;
        review B8-fdtd F1: a cache by ``id`` let a new medium inherit a freed one's verdict)."""
        if m.is_pec:
            return 0.0
        key = (_medium_key(m), self.dt)
        rho = self._media_check_cache.get(key)
        if rho is None:
            rho = amplification_radius(m, self.dt, np.linspace(0.0, self.lam_max, 257))
            self._media_check_cache[key] = rho
        return rho

    def _check_medium(self, m: Medium, what: str):
        if m.is_pec:
            return
        rho = self._medium_radius(m)
        # a defective eigenvalue at the exact limit (|lambda| = 1, a Jordan block) is computed with an error of
        # ~sqrt(eps); a growing mode just beyond the limit has |lambda| - 1 ~ sqrt(excess): 1e-6 separates them (so a
        # double root exactly on the unit circle, linear growth at isolated parameter values, is not detected here)
        if rho > 1.0 + 1e-6 or (what == "фон" and self.courant > self.courant_limit * math.sqrt(m.eps * m.mu) * (1 + 1e-12)):
            nmin = math.sqrt(m.eps * m.mu)
            hint = ""
            if m.poles:
                # Bidegaray-Fesquet, SIAM J. Numer. Anal. 46, 2551 (2008), arXiv:math/0506289: Table 7 (1-D) and
                # §5 (2-D) for the Lorentz-Young scheme (the engine's Lorentz/Drude update); Table 1 for the
                # Debye-Joseph scheme (the engine's trapezoid)
                d = sum(1 for u in range(self.dim) if self.deriv[u])
                s_inf = self.courant / math.sqrt(m.eps * m.mu)
                hint = (f"; достаточные условия из литературы для одного полюса (Bidégaray-Fesquet 2008, табл. 7 и §5; "
                        f"схема Янга): число Куранта со скоростью c∞ = 1/√(ε∞μ) не больше 1/√2 в 1-D и 1/2 в 2-D "
                        f"(здесь {s_inf:.4g}, осей с производной {d}; для 3-D в статье нет) и для каждого полюса "
                        f"Лоренца ω0·Δt ≤ 2/√(2εs/ε∞ − 1), εs = ε∞ + Δε (для полюса Друде, предел ω0 → 0 при "
                        f"Δε·ω0² = ωp², "
                        f"выведено здесь: ωp·Δt ≤ √(2ε∞)); для полюса Дебая (трапеция Джозефа и др.) — условие вакуума")
            raise Unstable(f"схема неустойчива в среде {what} ({m.label or 'без имени'}): спектральный радиус шага "
                           f"{rho:.6g} > 1 при числе Куранта S = cΔt/dx = {self.courant:g} (предел вакуума "
                           f"{self.courant_limit:.4g}, для ε∞μ = {nmin ** 2:.4g} — {self.courant_limit * nmin:.4g}"
                           f"{hint}). Уменьшите courant или dx")

    def _node_courant_bounds(self, mats, coef):
        """Two sufficient Courant limits from the actual node maps (review B8-fdtd F11: E nodes of one medium next to H
        nodes of another can be faster than either medium): (1) S <= S_vac sqrt(min_E eps min_H mu), exact for a
        uniform medium (the curl-curl operator is bounded by its vacuum form over min eps min mu); (2) Gershgorin's
        bound on eps^-1/2 C^T mu^-1 C eps^-1/2 with the node values (local; equal to the vacuum limit in 2-D, 3/4 of it
        in 3-D). Nodes held at zero (PEC, walls) are left out. Sufficient for nodes without poles and conductivity;
        nodes with poles are checked per medium (``_check_medium``) with eps_inf here."""
        free_e, eps_min, mu_min = {}, math.inf, math.inf
        for c in self.comps:
            val = mats[c][0]
            free = np.ones(self.shape, bool)
            a = AXES.index(c[1])
            for u in range(self.dim):
                lo, hi = self.boundary[AXES[u]]
                if lo == "periodic" or a == u:
                    continue
                sl = [slice(None)] * 3
                if c[0] == "e":
                    sl[u] = 0
                    free[tuple(sl)] = False
                else:
                    if lo == "pmc":
                        sl[u] = 0
                        free[tuple(sl)] = False
                    if hi == "pmc":
                        sl[u] = self.shape[u] - 1
                        free[tuple(sl)] = False
            if c[0] == "e":
                free &= coef[c]["cb"] != 0.0
                free_e[c] = np.where(free, 1.0 / np.sqrt(val), 0.0)
                if np.any(free):
                    eps_min = min(eps_min, float(val[free].min()))
            else:
                free_e[c] = np.where(free, 1.0 / val, 0.0)  # 1/mu on free H nodes
                if np.any(free):
                    mu_min = min(mu_min, float(val[free].min()))
        simple = self.courant_limit * math.sqrt(eps_min * mu_min) if math.isfinite(eps_min * mu_min) else math.inf
        if self.courant <= simple * (1 + 1e-12):
            return simple, None
        g_max = 0.0
        q = {}
        for s in self.comps:
            if s[0] != "h":
                continue
            g = np.zeros(self.shape)
            for (v, e, _) in self._terms[s]:
                g += (free_e[e] + np.roll(free_e[e], -1, axis=v)) * self.rd
            q[s] = g * free_e[s]
        for c in self.comps:
            if c[0] != "e":
                continue
            r = np.zeros(self.shape)
            for (v, s, _) in self._terms[c]:
                r += (q[s] + np.roll(q[s], 1, axis=v)) * self.rd
            g_max = max(g_max, float(np.max(free_e[c] * r)))
        gersh = 2.0 / (self.dx * math.sqrt(g_max)) if g_max > 0 else math.inf
        return simple, gersh

    # --- PML --------------------------------------------------------------------------------------------------------
    def _build_pml(self):
        """1-D profiles (b, a, 1/kappa) along each axis for the E-update (integer positions) and the H-update (half
        positions); arrays of the full axis length (b = a = 0, 1/kappa = 1 outside the layers)."""
        spec = self._pml_spec
        nbg = math.sqrt(self.background.eps * self.background.mu)
        smax = spec.sigma_factor * 0.8 * (spec.m + 1) / (self.dx * nbg)
        self.prof = {}
        for u in range(3):
            lo, hi = self.npml[u]
            n = self.shape[u]
            for kind, off in (("e", 0.0), ("h", 0.5)):
                pos = np.arange(n) + off
                rho = np.zeros(n)
                if lo:
                    rho = np.maximum(rho, np.clip((lo - pos) / lo, 0, 1))
                if hi:
                    rho = np.maximum(rho, np.clip((pos - (n - hi)) / hi, 0, 1))
                sig = smax * rho ** spec.m
                kap = 1.0 + (spec.kappa_max - 1.0) * rho ** spec.m
                alp = spec.alpha_max * (1.0 - rho) ** _PML_GRADE_ALPHA
                alp = np.where(rho > 0, alp, 0.0)
                b = np.exp(-(sig / kap + alp) * self.dt)
                den = sig * kap + kap * kap * alp
                a = np.where(sig > 0, sig * (b - 1.0) / np.where(den > 0, den, 1.0), 0.0)
                self.prof[(u, kind)] = (np.where(rho > 0, b, 0.0), a, 1.0 / kap)
        self.psi = {}
        for c in self.comps:
            for (v, s, sign) in self._terms[c]:
                lo, hi = self.npml[v]
                if lo + hi:
                    sh = list(self.shape)
                    sh[v] = lo + hi
                    self.psi[(c, v)] = np.zeros(sh, complex if self.complex else float)

    # --- bodies -----------------------------------------------------------------------------------------------------
    def add_body(self, shape, medium: Medium, label: str = "", averaging: str | None = None) -> int:
        """Add a body (later bodies cover earlier ones); returns its id. ``averaging`` overrides the world's for this
        body ("subpixel" applies only to plain dielectric/magnetic media)."""
        shape._check(self.dim)
        if not isinstance(medium, Medium):
            raise ValueError("вещество тела: Medium")
        bid = self._next_body
        new = dict(self._bodies)
        new[bid] = {"shape": shape, "medium": medium, "label": str(label), "averaging": averaging}
        self._apply_bodies(new)
        self._next_body += 1
        return bid

    def remove_body(self, bid: int):
        if bid not in self._bodies:
            raise KeyError(f"нет тела {bid}")
        new = dict(self._bodies)
        del new[bid]
        self._apply_bodies(new)

    def update_body(self, bid: int, shape=None, medium: Medium | None = None, label: str | None = None):
        if bid not in self._bodies:
            raise KeyError(f"нет тела {bid}")
        b = dict(self._bodies[bid])
        if shape is not None:
            shape._check(self.dim)
            b["shape"] = shape
        if medium is not None:
            b["medium"] = medium
        if label is not None:
            b["label"] = str(label)
        new = dict(self._bodies)
        new[bid] = b
        self._apply_bodies(new)

    def set_background(self, medium: Medium):
        if not medium.plain:
            raise ValueError("фон: среда без полюсов, проводимости и не PEC")
        old = self.background
        self.background = medium
        try:
            self._check_medium(medium, "фон")
            self._apply_bodies(dict(self._bodies))
        except Exception:
            self.background = old
            raise

    def bodies(self) -> list[dict]:
        return [{"id": k, "shape": v["shape"].params() if v["shape"].kind != "mask" or v["shape"].array is not None
                 else {"kind": "mask"}, "medium": v["medium"].params(), "label": v["label"],
                 "averaging": v["averaging"]} for k, v in self._bodies.items()]

    def _apply_bodies(self, new: dict):
        """Rebuild the materials for a new body set, all or nothing."""
        for b in new.values():
            self._check_medium(b["medium"], b["label"] or b["shape"].kind)
        old = self._bodies
        self._bodies = new
        try:
            self._build_materials()
        except Exception:
            self._bodies = old
            raise

    def _assign(self, comp: str, media_index: dict):
        """(value map (eps for E, mu for H), medium index map) of a component's nodes."""
        e_kind = comp[0] == "e"
        bg = self.background
        val = np.full(self.shape, bg.eps if e_kind else bg.mu)
        mid = np.zeros(self.shape, np.int16)
        plain_map = np.ones(self.shape, bool)  # node's current material may be averaged with
        for bid in sorted(self._bodies):
            b = self._bodies[bid]
            shape, m = b["shape"], b["medium"]
            k = media_index[id(m)]
            mval = m.eps if e_kind else m.mu
            mode = b["averaging"] or self.averaging
            sub = (mode == "subpixel" and m.plain and shape.analytic)
            # index window of the body's bounding box (+ 1 cell)
            lo_i, hi_i = [], []
            for u in range(3):
                if u >= self.dim:
                    lo_i.append(0)
                    hi_i.append(1)
                    continue
                bl, bh = shape.bbox(self.dim)[u]
                off = self.offset(comp, u)
                a = 0 if not math.isfinite(bl) else max(0, int(math.floor(self.index_of(bl, u, off))) - 2)
                z = self.shape[u] if not math.isfinite(bh) else min(self.shape[u],
                                                                   int(math.ceil(self.index_of(bh, u, off))) + 3)
                lo_i.append(a)
                hi_i.append(max(a, z))
            if any(h <= l for l, h in zip(lo_i, hi_i)):
                continue
            sl = tuple(slice(l, h) for l, h in zip(lo_i, hi_i))
            Pm = self._mesh(comp, lo_i, hi_i)
            Pm = tuple(Pm[:self.dim])
            if not sub:
                ins = np.broadcast_to(shape.inside(Pm), tuple(h - l for l, h in zip(lo_i, hi_i))[:self.dim]
                                      ).reshape(tuple(h - l for l, h in zip(lo_i, hi_i)))
                a_ax = AXES.index(comp[1])
                if m.is_pec and e_kind and a_ax < self.dim:
                    # PEC: an E component is zero where its whole Yee edge (the node -+ dx/2 along the component)
                    # lies in the conductor (measured: the TE cylinder a = 0.5 at f = 0.4, 0.7, 1.0, largest |Q_sca
                    # error| 0.090 / 0.017 / 0.0082 at 20 / 40 / 80 cells per unit against 0.30 / 0.068 / 0.038 with
                    # the node alone; re-measured while processing review B8-fdtd)
                    ends = []
                    for sgn in (-0.5, 0.5):
                        Pe = list(Pm)
                        Pe[a_ax] = Pe[a_ax] + sgn * self.dx
                        ends.append(np.broadcast_to(shape.inside(tuple(Pe)), ins.shape[:self.dim]).reshape(ins.shape))
                    ins = ends[0] & ends[1]
                v = val[sl]
                v[ins] = mval
                mid[sl][ins] = k
                plain_map[sl][ins] = m.plain
                continue
            d, n = shape.sdf(Pm)
            shp = tuple(h - l for l, h in zip(lo_i, hi_i))
            d = np.broadcast_to(d, shp[:self.dim]).reshape(shp) / self.dx
            n = [np.broadcast_to(nn, shp[:self.dim]).reshape(shp) for nn in n]
            half = 0.5 * math.sqrt(self.dim) + 1e-12
            deep = d <= -half
            near = np.abs(d) < half
            v = val[sl]
            mm = mid[sl]
            pl = plain_map[sl]
            v[deep] = mval
            mm[deep] = k
            pl[deep] = True
            if np.any(near):
                nv = np.stack([nn[near] for nn in n], axis=-1)
                f = geo.cut_fraction(nv, -d[near])
                prev = v[near]
                prev_plain = pl[near]
                avg = f * mval + (1.0 - f) * prev
                inv = f / mval + (1.0 - f) / prev
                a_ax = AXES.index(comp[1])
                if e_kind:
                    na2 = nv[:, a_ax] ** 2 if a_ax < self.dim else np.zeros(len(f))
                else:
                    # mu on H nodes: the same averaging with the H component's axis
                    na2 = nv[:, a_ax] ** 2 if a_ax < self.dim else np.zeros(len(f))
                eff = 1.0 / (na2 * inv + (1.0 - na2) / avg)
                # where the node's previous material was not plain (conductor, dispersive): staircase rule
                eff = np.where(prev_plain, eff, np.where(f >= 0.5, mval, prev))
                v[near] = eff
                take = (f >= 0.5)
                mm_near = mm[near]
                mm_near[take] = k
                mm[near] = mm_near
                pl_near = pl[near]
                pl_near[take] = True
                pl[near] = pl_near
        return val, mid

    def _build_materials(self, first: bool = False):
        """Material maps, update coefficients and dispersive node lists from the bodies (host arrays, then moved to
        the device). Keeps fields; see the module docstring for what an edit does to them."""
        media = [self.background]
        for bid in sorted(self._bodies):
            m = self._bodies[bid]["medium"]
            if all(m is not x for x in media):
                media.append(m)
        if len(media) > 32000:
            raise ValueError("слишком много разных сред")
        media_index = {id(m): i for i, m in enumerate(media)}
        dt = self.dt
        coef, mats, disp = {}, {}, {}
        old_disp = getattr(self, "disp", {})
        # a polarization is kept where the node's medium is the same before and after the edit, compared by value
        # (review B8-fdtd F3: positions in the rebuilt media list shift when a body is removed or changed)
        old_keys = np.array([_medium_key(m) for m in getattr(self, "_media", [])] or [""], dtype=object)
        new_keys = np.array([_medium_key(m) for m in media], dtype=object)
        host_F = {c: backend.to_numpy(self.F[c]) for c in self.comps} if not first else None
        for c in self.comps:
            val, mid = self._assign(c, media_index)
            mats[c] = (val, mid)
            if c[0] == "e":
                sig = np.zeros(len(media))
                sb = np.zeros(len(media))
                pec = np.zeros(len(media), bool)
                for i, m in enumerate(media):
                    sig[i] = m.sigma
                    pec[i] = m.is_pec
                    sb[i] = _pole_coeffs(m, dt)[2]
                s_n, b_n, p_n = sig[mid], sb[mid], pec[mid]
                den = val + s_n * dt / 2.0 + b_n
                ca = (val - s_n * dt / 2.0 - b_n) / den
                cb = dt / den
                ca = np.where(p_n, 0.0, ca)
                cb = np.where(p_n, 0.0, cb)
                coef[c] = {"cb": cb, "ca": None if np.all(ca == 1.0) else ca}
                # dispersive nodes
                dmed = [i for i, m in enumerate(media) if m.dispersive]
                if dmed:
                    sel = np.isin(mid, dmed)
                    idx = np.flatnonzero(sel)
                else:
                    idx = np.zeros(0, np.int64)
                if len(idx):
                    nL = max(len(_pole_coeffs(media[i], dt)[0]) for i in dmed)
                    nD = max(len(_pole_coeffs(media[i], dt)[1]) for i in dmed)
                    mids = mid.ravel()[idx]
                    C = np.zeros((3, len(idx), max(nL, 1)))
                    A = np.ones((len(idx), max(nD, 1)))
                    B = np.zeros((len(idx), max(nD, 1)))
                    for i in dmed:
                        L, D, _ = _pole_coeffs(media[i], dt)
                        rows = mids == i
                        for j, (c1, c2, c3) in enumerate(L):
                            C[0, rows, j], C[1, rows, j], C[2, rows, j] = c1, c2, c3
                        for j, (aD, bD) in enumerate(D):
                            A[rows, j], B[rows, j] = aD, bD
                    cx = 1.0 / den.ravel()[idx]
                    dtype = complex if self.complex else float
                    d = {"idx": idx, "mid": mids, "c1": C[0], "c2": C[1], "c3": C[2], "aD": A, "bD": B, "cx": cx,
                         "P": np.zeros((len(idx), max(nL, 1)), dtype), "Pm": np.zeros((len(idx), max(nL, 1)), dtype),
                         "PD": np.zeros((len(idx), max(nD, 1)), dtype), "nL": nL, "nD": nD}
                    od = old_disp.get(c)
                    if od is not None and len(od["idx"]):
                        o_idx = backend.to_numpy(od["idx"])
                        o_mid = backend.to_numpy(od["mid"])
                        common, ia, ib = np.intersect1d(idx, o_idx, return_indices=True)
                        same = new_keys[mids[ia]] == old_keys[o_mid[ib]]
                        ia, ib = ia[same], ib[same]
                        for key, nk in (("P", "nL"), ("Pm", "nL"), ("PD", "nD")):
                            ov = backend.to_numpy(od[key])
                            w = min(ov.shape[1], d[key].shape[1])
                            d[key][ia, :w] = ov[ib, :w]
                    disp[c] = d
            else:
                db = dt / val
                coef[c] = {"db": dt if np.all(val == 1.0) else db}
        # the Courant limit of the node maps (all or nothing: nothing of the world is changed before this point)
        simple, gersh = self._node_courant_bounds(mats, coef)
        node_limit = max(simple, gersh or 0.0)
        if self.courant > node_limit * (1 + 1e-12):
            raise Unstable(f"схема неустойчива на стыке сред: узлы E одной среды рядом с узлами H другой дают скорость "
                           f"больше, чем в каждой среде; достаточный предел по картам узлов S ≤ {node_limit:.4g} "
                           f"(по min ε узлов E и min μ узлов H: {simple:.4g}; по Гершгорину: "
                           f"{(gersh if gersh is not None else math.inf):.4g}), а S = {self.courant:g}. Уменьшите "
                           f"courant или dx, либо измените среды (ε < 1 или μ < 1)")
        self._node_limit = node_limit
        self._media = media
        self._media_index = media_index
        # PEC nodes: E = 0
        if host_F is not None:
            for c in self.comps:
                if c[0] == "e":
                    pec_nodes = coef[c]["cb"] == 0.0
                    if np.any(pec_nodes):
                        host_F[c][pec_nodes] = 0.0
        self._mats = mats
        self._mid = {c: mats[c][1] for c in self.comps}
        self.coef = coef
        self.disp = disp
        if host_F is not None:
            self.F = {c: (self.xp.asarray(host_F[c]) if self.device == "gpu" else host_F[c]) for c in self.comps}
        if self.device == "gpu":
            self._to_device(self.xp)

    # --- sources ----------------------------------------------------------------------------------------------------
    def add_source(self, source) -> int:
        """A ``CurrentSource`` or a ``PlaneWave``; returns its id (acts from the next step)."""
        sid = self._next_source
        new = dict(self._sources)
        new[sid] = {"src": source}
        old = self._sources
        self._sources = new
        try:
            self._build_sources(only=sid)
        except Exception:
            self._sources = old
            raise
        self._next_source += 1
        return sid

    def add_plane_wave(self, pw: PlaneWave) -> int:
        return self.add_source(pw)

    def remove_source(self, sid: int):
        if sid not in self._sources:
            raise KeyError(f"нет источника {sid}")
        del self._sources[sid]

    def sources(self) -> list[dict]:
        out = []
        for k, v in self._sources.items():
            try:
                p = v["src"].params()
            except ValueError:
                p = {"type": type(v["src"]).__name__, "unsaved": True}
            out.append({"id": k, **p})
        return out

    def _build_sources(self, only=None):
        for sid, rec in self._sources.items():
            if only is not None and sid != only:
                continue
            s = rec["src"]
            if isinstance(s, CurrentSource):
                rec.update(self._build_current(s))
            elif isinstance(s, PlaneWave):
                rec.update(self._build_tfsf(s))
            else:
                raise ValueError("источник: CurrentSource или PlaneWave")
            if self.device == "gpu":
                self._source_to(rec, self.xp)

    def _build_current(self, s: CurrentSource) -> dict:
        c = s.component
        if c not in self.comps:
            raise ValueError(f"компоненты {c} нет в этом мире (поляризация {self.pol})")
        lo, hi = s.region
        if len(lo) != self.dim:
            raise ValueError(f"источник: {self.dim} координаты")
        ranges, zero_ext = [], 0
        for u in range(3):
            if u >= self.dim:
                ranges.append(np.array([0]))
                continue
            off = self.offset(c, u)
            if hi[u] == lo[u]:
                zero_ext += 1
                i = int(math.floor(self.index_of(lo[u], u, off) + 0.5))  # the nearest node (half up)
                ranges.append(np.array([i]))
            else:
                a = int(math.ceil(self.index_of(lo[u], u, off) - 1e-9))
                b = int(math.floor(self.index_of(hi[u], u, off) + 1e-9))
                ranges.append(np.arange(a, b + 1))
            r = ranges[-1]
            if len(r) == 0 or r.min() < 0 or r.max() >= self.shape[u]:
                raise ValueError(f"источник вне сетки по оси {AXES[u]}")
        I = np.meshgrid(*ranges, indexing="ij")
        idx = np.ravel_multi_index([i.ravel() for i in I], self.shape)
        idx_u, first = np.unique(idx, return_index=True)
        amp = s.amplitude
        if callable(amp):
            X = [self.coord(I[u].ravel()[first] + self.offset(c, u), u) for u in range(self.dim)]
            w = np.asarray(amp(*X), complex if self.complex else float) * np.ones(len(idx_u))
        else:
            w = np.full(len(idx_u), amp, dtype=complex if (self.complex or np.iscomplexobj(amp)) else float)
        if np.iscomplexobj(w) and not self.complex:
            if np.any(np.imag(w) != 0):
                raise ValueError("комплексная амплитуда источника — только в мире с фазой Блоха (комплексные поля)")
            w = np.real(w)
        if not s.hard:
            w = w / self.dx ** zero_ext
        return {"kind": "current", "idx": idx_u, "w": w, "comp": c, "idx_d": idx_u, "w_d": w}

    def _build_tfsf(self, pw: PlaneWave) -> dict:
        from .fdtd_tfsf import build_tfsf
        return build_tfsf(self, pw)

    # --- monitors ---------------------------------------------------------------------------------------------------
    def add_probe(self, point, components=None) -> int:
        """Record components at a point every step (linear interpolation from each component's nodes). The record's
        times "t" are the E times t_n; H components are H^{n-1/2}, half a step earlier (the leapfrog)."""
        comps = self.comps if components is None else tuple(components)
        p = tuple(float(v) for v in point)
        if len(p) != self.dim:
            raise ValueError(f"точка датчика: {self.dim} координаты")
        items = []
        for c in comps:
            if c not in self.comps:
                raise ValueError(f"компоненты {c} нет в этом мире")
            corner, wts = [], []
            for u in range(3):
                if u >= self.dim:
                    corner.append([0])
                    wts.append([1.0])
                    continue
                s = self.index_of(p[u], u, self.offset(c, u))
                i0 = int(math.floor(s))
                fr = s - i0
                if fr < 1e-12:
                    corner.append([i0])
                    wts.append([1.0])
                else:
                    corner.append([i0, i0 + 1])
                    wts.append([1.0 - fr, fr])
            idx, w = [], []
            for a, wa in zip(corner[0], wts[0]):
                for b, wb in zip(corner[1], wts[1]):
                    for cc, wc in zip(corner[2], wts[2]):
                        ii = (a, b, cc)
                        for u in range(3):
                            if not (0 <= ii[u] < self.shape[u]):
                                raise ValueError("датчик вне сетки")
                        idx.append(np.ravel_multi_index(ii, self.shape))
                        w.append(wa * wb * wc)
            items.append((c, np.array(idx), np.array(w)))
        mid = self._next_monitor
        self._monitors[mid] = {"kind": "probe", "point": p, "items": items, "t": [], "v": {c: [] for c in comps},
                               "buf": None}
        self._next_monitor += 1
        return mid

    def add_dft(self, region, freqs, components=None) -> int:
        """Running DFT of components on the nodes inside ``region`` = (lo, hi) (a point, line, plane or box)."""
        comps = self.comps if components is None else tuple(components)
        lo, hi = region
        accs = {}
        for c in comps:
            if c not in self.comps:
                raise ValueError(f"компоненты {c} нет в этом мире")
            ranges = []
            for u in range(3):
                if u >= self.dim:
                    ranges.append((0, 1))
                    continue
                off = self.offset(c, u)
                a = int(math.ceil(self.index_of(lo[u], u, off) - 1e-9))
                b = int(math.floor(self.index_of(hi[u], u, off) + 1e-9))
                if hi[u] == lo[u]:
                    a = b = int(round(self.index_of(lo[u], u, off)))
                a, b = max(a, 0), min(b, self.shape[u] - 1)
                if b < a:
                    raise ValueError(f"область DFT пуста по оси {AXES[u]} для {c}")
                ranges.append((a, b + 1))
            g = mon.Gather(self, c, ranges)
            accs[c] = mon.Accumulator(self, g, freqs, c[0] == "h")
        mid = self._next_monitor
        self._monitors[mid] = {"kind": "dft", "region": (tuple(lo), tuple(hi)), "freqs": np.asarray(freqs, float),
                               "accs": accs, "start": self.steps}
        self._next_monitor += 1
        return mid

    def _faces_of(self, region, freqs, closed: bool, direction=None):
        lo, hi = region
        if len(lo) != self.dim or len(hi) != self.dim:
            raise ValueError(f"область: {self.dim} координаты")
        idx_lo = [int(round(self.index_of(lo[u], u))) if u < self.dim else 0 for u in range(3)]
        idx_hi = [int(round(self.index_of(hi[u], u))) if u < self.dim else 1 for u in range(3)]
        faces = []
        if closed:
            for u in range(self.dim):
                if idx_hi[u] <= idx_lo[u]:
                    raise ValueError("замкнутый ящик: hi > lo по каждой оси")
            for v in range(self.dim):
                cells = [(idx_lo[u], idx_hi[u]) if u < self.dim else (0, 1) for u in range(3)]
                for p, sign in ((idx_lo[v], -1), (idx_hi[v], +1)):
                    self._check_plane(v, p)
                    faces.append(mon.Face(self, v, p, cells, sign, freqs))
        else:
            flat = [u for u in range(self.dim) if idx_hi[u] == idx_lo[u]]
            if len(flat) != 1:
                raise ValueError("плоскость потока: ровно одна ось с нулевой протяжённостью")
            v = flat[0]
            cells = [(idx_lo[u], idx_hi[u]) if u < self.dim else (0, 1) for u in range(3)]
            for u in range(self.dim):
                if u != v and cells[u][1] <= cells[u][0]:
                    raise ValueError("плоскость потока: hi > lo по поперечным осям")
            sign = 1 if direction is None else (1 if direction > 0 else -1)
            self._check_plane(v, idx_lo[v])
            faces.append(mon.Face(self, v, idx_lo[v], cells, sign, freqs))
        return faces

    def _check_plane(self, v, p):
        if not self.periodic[v] and not (1 <= p <= self.shape[v] - 1):
            raise ValueError(f"плоскость потока на границе сетки по оси {AXES[v]}")

    def add_flux(self, region, freqs=None, closed: bool | None = None, direction=None) -> int:
        """Poynting flux through a plane (``region`` with one zero extent; ``direction`` +1/-1 along its normal) or a
        closed box (outward), in time every step and, with ``freqs``, per frequency."""
        lo, hi = region
        if closed is None:
            closed = all(h != l for l, h in zip(lo, hi))
        faces = self._faces_of(region, freqs, closed, direction)
        mid = self._next_monitor
        self._monitors[mid] = {"kind": "flux", "region": (tuple(lo), tuple(hi)), "closed": closed, "faces": faces,
                               "freqs": None if freqs is None else np.asarray(freqs, float), "t": [], "p": [],
                               "start": self.steps, "buf": None}
        self._next_monitor += 1
        return mid

    def add_near2far(self, region, freqs) -> int:
        """Near-to-far-field transform from a closed box (place it in the scattered-field region of a plane wave, or
        around radiating sources), at ``freqs``."""
        faces = self._faces_of(region, freqs, True)
        mid = self._next_monitor
        self._monitors[mid] = {"kind": "near2far", "region": (tuple(region[0]), tuple(region[1])), "faces": faces,
                               "freqs": np.asarray(freqs, float), "start": self.steps}
        self._next_monitor += 1
        return mid

    def remove_monitor(self, mid: int):
        if mid not in self._monitors:
            raise KeyError(f"нет датчика {mid}")
        del self._monitors[mid]

    def monitors(self) -> list[dict]:
        out = []
        for k, m in self._monitors.items():
            d = {"id": k, "kind": m["kind"]}
            for key in ("point", "region", "closed"):
                if key in m:
                    d[key] = m[key]
            if m.get("freqs") is not None:
                d["freqs"] = np.asarray(m["freqs"]).tolist()
            out.append(d)
        return out

    # results
    def probe(self, mid: int) -> dict:
        m = self._monitors[mid]
        self._flush(m)
        out = {"t": np.array(m["t"])}
        for c, v in m["v"].items():
            out[c] = np.concatenate(v) if v else np.zeros(0)
        return out

    def dft(self, mid: int) -> dict:
        """{"freqs", comp: (nf, *nodes) complex, "coords": {comp: (x, y[, z]) of the nodes}}."""
        m = self._monitors[mid]
        out = {"freqs": m["freqs"], "coords": {}}
        for c, acc in m["accs"].items():
            a = acc.host()
            out[c] = a[..., 0] if self.dim == 2 else a
            out["coords"][c] = tuple(self.coord(np.arange(r0, r1) + self.offset(c, u), u)
                                     for u, (r0, r1) in enumerate(acc.g.ranges[:self.dim]))
        return out

    def flux(self, mid: int) -> dict:
        """{"t": times, "power": instantaneous power through the plane/box, "freqs", "spectrum": (1/2) Re of the
        DFT fluxes per frequency (for a box: outward)}."""
        m = self._monitors[mid]
        self._flush(m)
        out = {"t": np.array(m["t"]), "power": np.array(m["p"])}
        if m["freqs"] is not None:
            out["freqs"] = m["freqs"]
            out["spectrum"] = sum(f.flux_spectrum() for f in m["faces"])
        return out

    def _flush(self, m):
        if m.get("buf"):
            b = m["buf"]
            if m["kind"] == "probe":
                for c in m["v"]:
                    if b["v"][c]:
                        m["v"][c].append(backend.to_numpy(self.xp.stack(b["v"][c])))
                m["t"].extend(b["t"])
                b["v"] = {c: [] for c in m["v"]}
                b["t"] = []
            else:
                if b["p"]:
                    m["p"].extend(float(x) for x in backend.to_numpy(self.xp.stack(b["p"])))
                    m["t"].extend(b["t"])
                b["p"], b["t"] = [], []

    def far_field(self, mid: int, directions, freq_index: int | None = None, normalisation: str = "exact") -> dict:
        """Far-field amplitudes from a near-to-far box. 2-D: ``directions`` = angles phi (radians); returns "A" (TM:
        E_z, TE: H_z, as A with field = i k A exp(i(k rho + pi/4)) / sqrt(8 pi k rho)) and "dsigma_dphi"
        (normalized by the first plane wave's incident amplitude, if any). 3-D: ``directions`` = (theta, phi) arrays;
        returns "E_theta", "E_phi" (E = i k A exp(i k r) / (4 pi r)) and "dsigma_domega". ``normalisation``: as in
        ``cross_sections`` (the box's fields are averaged to the face centres like the flux monitor's)."""
        m = self._monitors[mid]
        if m["kind"] != "near2far":
            raise ValueError("не монитор дальнего поля")
        if normalisation not in ("exact", "monitor"):
            raise ValueError("нормировка: exact или monitor")
        rel = self._tf_relation(m["region"])
        if rel not in (None, "sf"):
            raise ValueError(f"ящик дальнего поля {mid} должен лежать всеми гранями в области рассеянного поля (с "
                             f"запасом в ячейку), а он {rel}: в дальнее поле вошла бы падающая волна (review B8-fdtd "
                             f"F12)")
        fs = m["freqs"]
        bg = self.background
        eta = math.sqrt(bg.mu / bg.eps)
        nb = math.sqrt(bg.eps * bg.mu)
        sel = range(len(fs)) if freq_index is None else [freq_index]
        inc = self._incident_dft(fs, m["start"])
        if inc is not None and normalisation == "monitor":
            inc = inc * np.sqrt(self.monitor_factor(fs))
        res = {"freqs": fs[list(sel)]}
        if self.dim == 2:
            phis = np.asarray(directions, float)
            A_all, ds = [], []
            for i in sel:
                k = TWO_PI * fs[i] * nb
                pols = ["tm"] if self.pol == "tm" else (["te"] if self.pol == "te" else ["tm", "te"])
                A = {p: mon.far_field_2d(m["faces"], self, i, phis, k, eta, p) for p in pols}
                A_all.append(A)
                if inc is not None:
                    G = inc[i]
                    pol = self._pw_pol()
                    amp = A.get(pol, next(iter(A.values())))
                    ref = abs(G) ** 2 if pol == "tm" else abs(G / eta) ** 2
                    ds.append(k * np.abs(amp) ** 2 / (8 * math.pi) / ref if ref > 0 else np.full(len(phis), np.nan))
            res["A"] = A_all if freq_index is None else A_all[0]
            if ds:
                res["dsigma_dphi"] = np.array(ds) if freq_index is None else ds[0]
            return res
        th, ph = directions
        Et, Ep, dso = [], [], []
        for i in sel:
            k = TWO_PI * fs[i] * nb
            a, b = mon.far_field_3d(m["faces"], self, i, th, ph, k, eta)
            Et.append(a)
            Ep.append(b)
            if inc is not None:
                ref = abs(inc[i]) ** 2
                dso.append(k * k / (16 * math.pi ** 2) * (np.abs(a) ** 2 + np.abs(b) ** 2) / ref)
        res["E_theta"] = np.array(Et) if freq_index is None else Et[0]
        res["E_phi"] = np.array(Ep) if freq_index is None else Ep[0]
        if dso:
            res["dsigma_domega"] = np.array(dso) if freq_index is None else dso[0]
        return res

    def _pw_pol(self):
        for rec in self._sources.values():
            if rec.get("kind") == "tfsf":
                return rec["pol2d"]
        return "tm"

    def _plane_wave_rec(self):
        for sid in sorted(self._sources):
            rec = self._sources[sid]
            if rec.get("kind") == "tfsf":
                return rec
        return None

    def _incident_dft(self, freqs, start_step: int):
        """DFT (over the steps since ``start_step``) of the first plane wave's E amplitude at its reference point."""
        rec = self._plane_wave_rec()
        if rec is None:
            return None
        g = np.asarray(rec["ref_series"])
        # the series starts at the step after the wave was added (review B8-fdtd F4: it was numbered from step 1)
        n = rec.get("ref_step0", 0) + np.arange(1, len(g) + 1)
        keep = n > start_step
        t = n[keep] * self.dt
        return np.exp(2j * math.pi * np.outer(np.asarray(freqs, float), t)) @ g[keep] * self.dt

    def _monitor_axis(self, rec, axis=None) -> int:
        if axis is not None:
            return AXES.index(axis) if isinstance(axis, str) else int(axis)
        if rec["family"] == "slab":
            return int(rec["un"])
        return int(np.argmax(np.abs(rec["khat"][:self.dim])))

    def monitor_factor(self, freqs, axis=None):
        """How the flux monitor sees the first plane wave: its measured flux density through a plane normal to
        ``axis`` (default: the slab's axis, or the axis nearest to the wave's direction) over the true one, a closed
        form (``fdtd_tfsf.monitor_factor``): cos(k dx/2) = 1 - (k dx)^2/8 + ... at normal incidence."""
        from .fdtd_tfsf import monitor_factor
        rec = self._plane_wave_rec()
        if rec is None:
            raise ValueError("нет плоской волны")
        return monitor_factor(self, rec, freqs, self._monitor_axis(rec, axis))

    def incident_intensity(self, freqs, start_step: int = 0, normalisation: str = "exact", axis=None):
        """The first plane wave's intensity per frequency, from G, its E amplitude's DFT since ``start_step``.

        ``normalisation="exact"``: (1/2)|G|^2 sqrt(eps/mu), the true intensity of the injected discrete wave (for a
        Bloch slab wave the true flux density through the planes normal to its axis, (1/2)|G|^2 K_n / (Omega mu)).
        ``"monitor"``: that times ``monitor_factor`` (planes normal to ``axis``): the incident wave as the flux monitor
        measures it, Meep's "normalisation run" in closed form. Dividing a flux measured by the monitor by it cancels
        the monitor's own bias exactly for plane waves along that axis (reflection, transmission; review B8-fdtd F5)."""
        if normalisation not in ("exact", "monitor"):
            raise ValueError("нормировка: exact или monitor")
        rec = self._plane_wave_rec()
        if rec is None:
            raise ValueError("нет плоской волны")
        G = self._incident_dft(freqs, start_step)
        bg = self.background
        f = np.asarray(freqs, float)
        if rec["family"] == "slab":
            from .fdtd_tfsf import slab_normal_factor
            I = 0.5 * np.abs(G) ** 2 * slab_normal_factor(self, rec, f)
        else:
            I = 0.5 * np.abs(G) ** 2 * math.sqrt(bg.eps / bg.mu)
        if normalisation == "monitor":
            I = I * self.monitor_factor(f, axis)
        return I

    def cross_sections(self, scattered: int | None = None, total: int | None = None,
                       normalisation: str = "exact") -> dict:
        """Cross sections per frequency from closed flux boxes (with freqs) of the first plane wave's run:
        ``scattered`` in the scattered-field region (sigma_sca = outward power / I_inc), ``total`` in the total-field
        region (sigma_abs = inward power / I_inc). 2-D: per unit length (scattering widths).

        ``normalisation`` (``incident_intensity``): "exact" divides by the true incident intensity, "monitor" by the
        incident wave as the flux monitor measures it through planes normal to the incidence axis (Meep's
        convention). The monitor measures every plane wave weaker by a factor 1 - O((k dx)^2) that depends on its
        direction (``monitor_factor``): with "exact" the cross sections carry the monitor's bias on the scattered
        waves (2-D TM: -(k dx)^2 (1 + sin^2 theta)/8 per wave at angle theta to a face's normal, TE: -(k dx)^2
        cos^2 theta / 8), with "monitor" the difference between that and the incident wave's -(k dx)^2/8; both are
        second order. The result keeps both: "sigma_*" by the normalisation asked, "monitor_factor" to convert."""
        out = {}
        ref = None
        if self._plane_wave_rec() is None:
            raise ValueError("нет плоской волны")
        for key, mid in (("sca", scattered), ("tot", total)):
            if mid is None:
                continue
            m = self._monitors[mid]
            if m["kind"] != "flux" or not m["closed"] or m["freqs"] is None:
                raise ValueError("нужен замкнутый ящик потока с частотами")
            rel = self._tf_relation(m["region"])
            want = "sf" if key == "sca" else "tf"
            if rel != want:
                raise ValueError(f"ящик потока {mid} должен лежать {'вне' if key == 'sca' else 'внутри'} области "
                                 f"полного поля всеми гранями (с запасом в ячейку), а он {rel}: сечение было бы "
                                 f"неверным (review B8-fdtd F12)")
            fs = m["freqs"]
            I = self.incident_intensity(fs, m["start"], normalisation)
            P = sum(f.flux_spectrum() for f in m["faces"])
            out["freqs"] = fs
            if key == "sca":
                out["sigma_sca"] = P / I
            else:
                out["sigma_abs"] = -P / I
            ref = I
        if "sigma_sca" in out and "sigma_abs" in out:
            out["sigma_ext"] = out["sigma_sca"] + out["sigma_abs"]
        out["incident_intensity"] = ref
        out["normalisation"] = normalisation
        if "freqs" in out:
            out["monitor_factor"] = self.monitor_factor(out["freqs"])
        return out

    def absorbed_power(self, mid: int) -> dict:
        """Absorbed power per frequency in the nodes of a DFT monitor (all E components recorded):
        (1/2) sum omega Im(eps_d(omega)) |E|^2 dV with the scheme's own eps_d of each node's medium."""
        m = self._monitors[mid]
        if m["kind"] != "dft":
            raise ValueError("нужен монитор DFT")
        fs = m["freqs"]
        P = np.zeros(len(fs))
        for c, acc in m["accs"].items():
            if c[0] != "e":
                continue
            a = acc.host()
            mid_nodes = self._mid[c][tuple(slice(r0, r1) for r0, r1 in acc.g.ranges)] if acc.g.contiguous else \
                self._mid[c][np.ix_(*acc.g.idx)]
            for i, med in enumerate(self._media):
                sel = mid_nodes == i
                if not np.any(sel) or med.plain or med.is_pec:
                    continue
                im = np.imag(med.epsilon_discrete(fs, self.dt))
                P += 0.5 * TWO_PI * fs * im * np.sum(np.abs(a[:, sel]) ** 2, axis=1) * self.dV
        return {"freqs": fs, "power": P}

    # --- energy -----------------------------------------------------------------------------------------------------
    def energy(self) -> dict:
        """Field energy (per unit length in 2-D): electric (1/2) sum eps |E^n|^2 dV (eps_inf on dispersive nodes),
        magnetic (1/2) sum mu H^{n-1/2}.H^{n+1/2} dV (H^{n+1/2} from E^n without absorbing layers) — their sum is
        exactly conserved by the scheme in a closed box of non-dispersive, non-conducting media — and the magnetic
        energy at n - 1/2. The poles' energy is not included, so with a dispersive body (even a lossless one) the sum
        exchanges energy with the polarization and is not constant (review B8-fdtd F15)."""
        xp = self.xp
        We = 0.0
        for c in self.comps:
            if c[0] == "e":
                eps = self._mats[c][0]
                f = backend.to_numpy(self.F[c])
                We += 0.5 * float(np.sum(eps * np.abs(f) ** 2)) * self.dV
        Wm, Wm_half = 0.0, 0.0
        for c in self.comps:
            if c[0] != "h":
                continue
            mu = self._mats[c][0]
            h0 = backend.to_numpy(self.F[c])
            curl = np.zeros(self.shape, h0.dtype)
            for (v, s, sign) in self._terms[c]:
                S = backend.to_numpy(self.F[s])
                ph = self.phase[v] if self.complex else 1.0
                nb = np.roll(S, -1, axis=v)
                if self.complex:
                    sl = [slice(None)] * 3
                    sl[v] = slice(-1, None)
                    nb[tuple(sl)] = nb[tuple(sl)] * ph
                curl += sign * (nb - S) * self.rd
            h1 = h0 - self.dt / mu * curl
            Wm += 0.5 * float(np.sum(mu * np.real(np.conj(h0) * h1))) * self.dV
            Wm_half += 0.5 * float(np.sum(mu * np.abs(h0) ** 2)) * self.dV
        _ = xp
        return {"electric": We, "magnetic": Wm, "total": We + Wm, "magnetic_half_step": Wm_half}

    def set_field(self, comp: str, values):
        """Set a component on its nodes (initial conditions; ``values`` broadcastable to the grid's 2-D or 3-D shape,
        or a callable of the node coordinates). E at t, H at t - dt/2 (the solver's staggering)."""
        if comp not in self.comps:
            raise ValueError(f"компоненты {comp} нет в этом мире")
        if callable(values):
            X = np.meshgrid(*self.coords(comp), indexing="ij")
            values = values(*X)
        a = np.asarray(values)
        if np.iscomplexobj(a) and not self.complex:
            raise ValueError("комплексное поле — только в мире с фазой Блоха")
        a = np.broadcast_to(a, self.shape[:self.dim]).reshape(self.shape).astype(complex if self.complex else float)
        self.F[comp] = self.xp.asarray(a.copy()) if self.device == "gpu" else a.copy()
        if comp[0] == "e":
            self._walls("e")
            pec = backend.to_numpy(self.coef[comp]["cb"]) == 0.0
            if np.any(pec):
                F = self.F[comp]
                F[self.xp.asarray(pec) if self.device == "gpu" else pec] = 0.0
        else:
            self._walls("h")

    # --- fields for display ---------------------------------------------------------------------------------------
    def field(self, comp: str) -> np.ndarray:
        """A component on its own nodes over the whole grid (absorbing layers included): 2-D arrays (nx, ny) in 2-D."""
        if comp not in self.comps:
            raise ValueError(f"компоненты {comp} нет в этом мире")
        a = backend.to_numpy(self.F[comp]).copy()
        return a[..., 0] if self.dim == 2 else a

    def _centered(self, comp):
        """A component averaged to the cell centres (i + 1/2 along every axis)."""
        a = backend.to_numpy(self.F[comp])
        for u in range(self.dim):
            if self.offset(comp, u) == 0.0:
                nb = np.roll(a, -1, axis=u)
                if self.complex and self.periodic[u]:
                    sl = [slice(None)] * 3
                    sl[u] = slice(-1, None)
                    nb[tuple(sl)] = nb[tuple(sl)] * self.phase[u]
                a = 0.5 * (a + nb)
        return a

    def interior_slices(self):
        out = []
        for u in range(3):
            if u >= self.dim:
                out.append(slice(0, 1))
                continue
            lo, hi = self.npml[u]
            a = int(math.floor(self.off[u]))
            b = a + int(round(self.interior[u] / self.dx))
            out.append(slice(a, b))
        return tuple(out)

    def snapshot(self, kind: str = "ez", plane=None, interior: bool = True) -> dict:
        """A field for display at the cell centres: a component ("ex" ... "hz"), "|E|^2", "|H|^2", "Sx", "Sy", "Sz"
        (instantaneous Poynting vector, H at t - dt/2), "|S|"; real part for complex fields. 3-D: ``plane`` =
        ("x"|"y"|"z", coordinate) gives the slice through the nearest cell centres. Returns {"values", "x", "y"
        (the slice's axes), "t"}."""
        vals = self._display(kind)
        sl = self.interior_slices() if interior else (slice(None),) * 3
        vals = vals[sl]
        ax = [self.coord(np.arange(self.shape[u])[sl[u]] + 0.5, u) if u < self.dim else np.zeros(1) for u in range(3)]
        if self.dim == 2:
            return {"values": vals[..., 0], "x": ax[0], "y": ax[1], "t": self.t}
        if plane is None:
            return {"values": vals, "x": ax[0], "y": ax[1], "z": ax[2], "t": self.t}
        a, pos = plane
        u = AXES.index(a)
        i = int(np.argmin(np.abs(ax[u] - float(pos))))
        take = [slice(None)] * 3
        take[u] = i
        rest = [AXES[w] for w in range(3) if w != u]
        return {"values": vals[tuple(take)], rest[0]: ax[AXES.index(rest[0])], rest[1]: ax[AXES.index(rest[1])],
                "at": float(ax[u][i]), "t": self.t, "axes": rest}

    def _display(self, kind):
        cen = lambda c: self._centered(c) if c in self.comps else np.zeros(self.shape)  # noqa: E731
        if kind in COMPS:
            v = cen(kind)
            return np.real(v)
        if kind in ("|E|^2", "|H|^2"):
            pre = "e" if kind == "|E|^2" else "h"
            return sum(np.abs(cen(pre + a)) ** 2 for a in AXES)
        if kind in ("Sx", "Sy", "Sz", "|S|"):
            E = [np.real(cen("e" + a)) for a in AXES]
            H = [np.real(cen("h" + a)) for a in AXES]
            S = [E[1] * H[2] - E[2] * H[1], E[2] * H[0] - E[0] * H[2], E[0] * H[1] - E[1] * H[0]]
            if kind == "|S|":
                return np.sqrt(S[0] ** 2 + S[1] ** 2 + S[2] ** 2)
            return S["xyz".index(kind[1])]
        raise ValueError("вид снимка: компонента, |E|^2, |H|^2, Sx, Sy, Sz, |S|")

    def material_map(self, kind: str = "eps", interior: bool = True) -> np.ndarray:
        """At the nodes of Ez (2-D TM, 3-D) or Ex (2-D TE), interior only: "eps" (eps_inf as the node has it, averaged
        at surfaces), "mu", "medium" (index into ``media()``), "pec" (bool)."""
        c = "ez" if "ez" in self.comps else "ex"
        if kind == "mu":
            c = "hz" if "hz" in self.comps else "hx"
        val, mid = self._mats[c]
        out = {"eps": val, "mu": val, "medium": mid, "pec": self.coef[c]["cb"] == 0.0 if c[0] == "e" else None}[kind]
        sl = self.interior_slices() if interior else (slice(None),) * 3
        out = out[sl]
        return out[..., 0] if self.dim == 2 else out

    def media(self) -> list[dict]:
        return [m.params() for m in self._media]

    # --- the step ---------------------------------------------------------------------------------------------------
    def advance(self, n: int = 1):
        """n time steps."""
        n = int(n)
        if n <= 0:
            return self
        self._choose()
        t0 = time.perf_counter()
        for _ in range(n):
            self._step()
            if self.steps % 256 == 0 and not self._healthy():
                raise Unstable(f"поля стали нечисловыми к t = {self.t:.6g} (шаг {self.steps})")
        # and at the end of every call (review B8-fdtd F20: short calls never reached a multiple of 256)
        if self.steps % 256 != 0 and not self._healthy():
            raise Unstable(f"поля стали нечисловыми к t = {self.t:.6g} (шаг {self.steps})")
        if self.device == "gpu":
            self.xp.cuda.Device(0).synchronize()
        self._timing["steps"] += n
        self._timing["seconds"] += time.perf_counter() - t0
        return self

    def advance_to(self, t: float):
        return self.advance(int(round((float(t) - self.t) / self.dt)))

    def _healthy(self) -> bool:
        xp = self.xp
        return all(bool(xp.isfinite(self.F[c]).all()) for c in self.comps)

    def _step(self):
        xp = self.xp
        n = self.steps
        t_h = (n + 0.5) * self.dt  # H^{n+1/2}
        t_e = (n + 1) * self.dt  # E^{n+1}
        flux_mons = [m for m in self._monitors.values() if m["kind"] == "flux"]
        for m in flux_mons:
            for f in m["faces"]:
                f.h_before(self)
        # H
        for c in self.comps:
            if c[0] == "h":
                self._update(c)
        self._walls("h")
        self._apply_sources("h", n * self.dt)
        # hard H sources at t_{n+1/2}, before the E update uses them (review B8-fdtd F2: imposed after the E update,
        # the E update never saw them and a hard H diverged)
        self._apply_hard("h", t_h)
        for m in flux_mons:
            p = sum(f.time_flux(self) for f in m["faces"])
            b = m.setdefault("buf", None) or {"p": [], "t": []}
            m["buf"] = b
            b["p"].append(p)
            b["t"].append(n * self.dt)
        for m in self._monitors.values():
            if m["kind"] in ("flux", "near2far"):
                for f in m["faces"]:
                    f.accumulate(self, "h", t_e)
            elif m["kind"] == "dft":
                for c, acc in m["accs"].items():
                    if c[0] == "h":
                        acc.add(self, t_e)
        # E
        pre = {c: self._disp_pre(c) for c in self.disp}
        for c in self.comps:
            if c[0] == "e":
                self._update(c)
        self._apply_sources("e", t_h)
        for c, d in self.disp.items():
            self._disp_post(c, d, pre[c])
        self._walls("e")
        # hard E sources at t_{n+1}, before the Debye polarization takes E^{n+1}
        self._apply_hard("e", t_e)
        for c, d in self.disp.items():
            self._disp_debye(c, d, pre[c])
        self.steps += 1
        self.t = self.steps * self.dt
        self._record_reference()
        for m in self._monitors.values():
            if m["kind"] in ("flux", "near2far"):
                for f in m["faces"]:
                    f.accumulate(self, "e", self.t)
            elif m["kind"] == "dft":
                for c, acc in m["accs"].items():
                    if c[0] == "e":
                        acc.add(self, self.t)
            elif m["kind"] == "probe":
                b = m.get("buf") or {"v": {c: [] for c in m["v"]}, "t": []}
                m["buf"] = b
                if m.get("dev") is None or m["dev"][0] is not xp:
                    m["dev"] = (xp, [(xp.asarray(i), xp.asarray(w)) for _, i, w in m["items"]])
                for (c, _, _), (i, w) in zip(m["items"], m["dev"][1]):
                    b["v"][c].append(xp.sum(self.F[c].ravel()[i] * w))
                b["t"].append(self.t)
        _ = xp

    # field update of one component (device dispatch)
    def _update(self, c):
        if self.device == "gpu":
            self._update_gpu(c)
        else:
            blocks = self._blocks()
            if len(blocks) == 1:
                self._update_np(c, 0, self.shape[0])
            else:
                list(_pool().map(lambda b: self._update_np(c, b[0], b[1]), blocks))

    def _blocks(self):
        n0 = self.shape[0]
        k = max(1, min(FDTD_THREADS, self.N // MIN_BLOCK_CELLS, n0))
        edges = [round(n0 * q / k) for q in range(k + 1)]
        return [(edges[q], edges[q + 1]) for q in range(k)]

    def _diff_np(self, S, v, i0, i1, kind_e, out):
        """out = backward (E) or forward (H) difference of S along v, rows [i0, i1), times 1/dx."""
        n0 = self.shape[0]
        nv = self.shape[v]
        bl = self.complex and self.bloch[v] != 0
        if v == 0:
            if kind_e:
                if i0 >= 1:
                    np.subtract(S[i0:i1], S[i0 - 1:i1 - 1], out=out)
                else:
                    if i1 > 1:
                        np.subtract(S[1:i1], S[0:i1 - 1], out=out[1:])
                    nb = S[n0 - 1] * np.conj(self.phase[0]) if bl else S[n0 - 1]
                    np.subtract(S[0], nb, out=out[0])
            else:
                if i1 < n0:
                    np.subtract(S[i0 + 1:i1 + 1], S[i0:i1], out=out)
                else:
                    if i1 - 1 > i0:
                        np.subtract(S[i0 + 1:n0], S[i0:n0 - 1], out=out[:-1])
                    nb = S[0] * self.phase[0] if bl else S[0]
                    np.subtract(nb, S[n0 - 1], out=out[-1])
        else:
            Sb = S[i0:i1]
            sl = lambda a, b: tuple([slice(None)] * v + [slice(a, b)])  # noqa: E731
            if kind_e:
                if nv > 1:
                    np.subtract(Sb[sl(1, None)], Sb[sl(None, -1)], out=out[sl(1, None)])
                nb = Sb[sl(nv - 1, nv)] * np.conj(self.phase[v]) if bl else Sb[sl(nv - 1, nv)]
                np.subtract(Sb[sl(0, 1)], nb, out=out[sl(0, 1)])
            else:
                if nv > 1:
                    np.subtract(Sb[sl(1, None)], Sb[sl(None, -1)], out=out[sl(None, -1)])
                nb = Sb[sl(0, 1)] * self.phase[v] if bl else Sb[sl(0, 1)]
                np.subtract(nb, Sb[sl(nv - 1, nv)], out=out[sl(nv - 1, nv)])
        np.multiply(out, self.rd, out=out)

    def _cpml_np(self, c, v, kind_e, i0, i1, d):
        lo, hi = self.npml[v]
        if not (lo + hi):
            return
        psi = self.psi[(c, v)]
        pb, pa, pk = self.prof[(v, "e" if kind_e else "h")]
        nv = self.shape[v]
        segs = []
        if lo:
            segs.append((0, lo, 0))
        if hi:
            segs.append((nv - hi, nv, lo))
        for a, b, p0 in segs:
            if v == 0:
                a2, b2 = max(a, i0), min(b, i1)
                if b2 <= a2:
                    continue
                ds = d[a2 - i0:b2 - i0]
                ps = psi[p0 + a2 - a:p0 + b2 - a]
                sh = (-1, 1, 1)
                B, A, K = pb[a2:b2].reshape(sh), pa[a2:b2].reshape(sh), pk[a2:b2].reshape(sh)
            else:
                idx_d = tuple([slice(None)] * v + [slice(a, b)])
                idx_p = tuple([slice(i0, i1)] + [slice(None)] * (v - 1) + [slice(p0, p0 + b - a)])
                ds = d[idx_d]
                ps = psi[idx_p]
                sh = [1, 1, 1]
                sh[v] = -1
                B, A, K = pb[a:b].reshape(sh), pa[a:b].reshape(sh), pk[a:b].reshape(sh)
            new = B * ps + A * ds
            ps[...] = new
            ds[...] = ds * K + new

    def _update_np(self, c, i0, i1):
        kind_e = c[0] == "e"
        F = self.F[c]
        terms = self._terms[c]
        if not terms:
            return
        bshape = (i1 - i0,) + self.shape[1:]
        dts = complex if self.complex else float
        ds = []
        for (v, s, sign) in terms:
            d = np.empty(bshape, dts)
            self._diff_np(self.F[s], v, i0, i1, kind_e, d)
            self._cpml_np(c, v, kind_e, i0, i1, d)
            ds.append((sign, d))
        if len(ds) == 2:
            curl = ds[0][1] - ds[1][1]
        elif ds[0][0] > 0:
            curl = ds[0][1]
        else:
            curl = -ds[0][1]
        co = self.coef[c]
        Fb = F[i0:i1]
        if kind_e:
            t2 = co["cb"][i0:i1] * curl
            if co["ca"] is not None:
                t1 = co["ca"][i0:i1] * Fb
                np.add(t1, t2, out=Fb)
            else:
                np.add(Fb, t2, out=Fb)
        else:
            db = co["db"]
            t2 = (db[i0:i1] if isinstance(db, np.ndarray) else db) * curl
            np.subtract(Fb, t2, out=Fb)

    def _update_gpu(self, c):
        cp = self.xp
        terms = self._terms[c]
        if not terms:
            return
        kind_e = c[0] == "e"
        co = self.coef[c]
        t = {1: None, 2: None}
        for (v, s, sign) in terms:
            t[1 if sign > 0 else 2] = (v, s)
        dummy = self._gpu_dummy
        args_terms = []
        for k in (1, 2):
            if t[k] is None:
                args_terms.append((dummy["T"], dummy["T"], dummy["d"], dummy["d"], dummy["d"], 0, 0, None))
                continue
            v, s = t[k]
            lo, hi = self.npml[v]
            psi = self.psi.get((c, v), dummy["T"])
            pb, pa, pk = self.prof[(v, "e" if kind_e else "h")]
            args_terms.append((self.F[s], psi, pb, pa, pk, lo, hi, v))
        bl1 = t[1] is not None and self.complex and self.bloch[t[1][0]] != 0
        bl2 = t[2] is not None and self.complex and self.bloch[t[2][0]] != 0
        ca_arr = kind_e and co["ca"] is not None
        cf_arr = kind_e or isinstance(co["db"], cp.ndarray)
        kern = _gpu_kernel(cp, kind_e, t[1][0] if t[1] else None, t[2][0] if t[2] else None, self.complex,
                           bl1, bl2, ca_arr, cf_arr)
        cf = co["cb"] if kind_e else (co["db"] if cf_arr else dummy["d"])
        cfs = 0.0 if (kind_e or cf_arr) else float(co["db"])
        ca = co["ca"] if ca_arr else dummy["d"]
        T = np.complex128 if self.complex else np.float64
        ph = [T(self.phase[t[k][0]]) if (t[k] is not None and self.complex) else T(1.0) for k in (1, 2)]
        (S1, psi1, b1, a1, k1, lo1, hi1, _), (S2, psi2, b2, a2, k2, lo2, hi2, _) = args_terms
        block = 256
        grid = ((self.N + block - 1) // block,)
        kern(grid, (block,), (self.F[c], S1, S2, cf, ca, np.float64(cfs), psi1, b1, a1, k1, np.int32(lo1),
                              np.int32(hi1), psi2, b2, a2, k2, np.int32(lo2), np.int32(hi2), np.int32(self.shape[0]),
                              np.int32(self.shape[1]), np.int32(self.shape[2]), ph[0], ph[1], np.float64(self.rd)))

    def _walls(self, kind):
        for u in range(self.dim):
            lo, hi = self.boundary[AXES[u]]
            if lo == "periodic":
                continue
            for c in self.comps:
                if c[0] != kind or AXES.index(c[1]) == u:
                    continue
                F = self.F[c]
                sl = [slice(None)] * 3
                if kind == "e":
                    sl[u] = 0
                    F[tuple(sl)] = 0.0
                else:
                    if lo == "pmc":
                        sl[u] = 0
                        F[tuple(sl)] = 0.0
                    if hi == "pmc":
                        sl[u] = self.shape[u] - 1
                        F[tuple(sl)] = 0.0

    # dispersion
    def _disp_pre(self, c):
        d = self.disp[c]
        if not len(d["idx"]):
            return None
        Fr = self.F[c].ravel()
        e_old = Fr[d["idx"]]
        P_new = d["c1"] * d["P"] + d["c2"] * d["Pm"] + d["c3"] * e_old[:, None]
        X = (P_new - d["P"]).sum(axis=1) + ((d["aD"] - 1.0) * d["PD"]).sum(axis=1)
        d["Pm"] = d["P"]
        d["P"] = P_new
        return e_old, X

    def _disp_post(self, c, d, pre):
        if pre is None:
            return
        e_old, X = pre
        Fr = self.F[c].reshape(-1)
        Fr[d["idx"]] = Fr[d["idx"]] - d["cx"] * X

    def _disp_debye(self, c, d, pre):
        if pre is None or d["nD"] == 0:
            return
        e_old, _ = pre
        Fr = self.F[c].reshape(-1)
        e_new = Fr[d["idx"]]
        d["PD"] = d["aD"] * d["PD"] + d["bD"] * (e_new + e_old)[:, None]

    # sources
    def _apply_sources(self, kind, t):
        """Soft currents (kind "e": J at t = t_{n+1/2}; kind "h": M at t_n) and TF/SF corrections."""
        for sid in sorted(self._sources):
            rec = self._sources[sid]
            if rec["kind"] == "current":
                s = rec["src"]
                if s.hard or rec["comp"][0] != kind:
                    continue
                val = float(s.profile(t))
                if val == 0.0:
                    continue
                F = self.F[rec["comp"]].reshape(-1)
                co = self.coef[rec["comp"]]
                if kind == "e":
                    F[rec["idx_d"]] = F[rec["idx_d"]] - co["cb"].reshape(-1)[rec["idx_d"]] * (rec["w_d"] * val)
                else:
                    db = co["db"]
                    dbv = db.reshape(-1)[rec["idx_d"]] if not isinstance(db, float) else db
                    F[rec["idx_d"]] = F[rec["idx_d"]] - dbv * (rec["w_d"] * val)
            elif rec["kind"] == "tfsf":
                from .fdtd_tfsf import apply_tfsf
                apply_tfsf(self, rec, kind)

    def _apply_hard(self, kind, t):
        """Hard sources of one kind: E^{n+1} = amplitude f(t_{n+1}) after the E update, H^{n+1/2} = amplitude
        f(t_{n+1/2}) after the H update."""
        for sid in sorted(self._sources):
            rec = self._sources[sid]
            if rec["kind"] == "current" and rec["src"].hard and rec["comp"][0] == kind:
                val = float(rec["src"].profile(t))
                F = self.F[rec["comp"]].reshape(-1)
                F[rec["idx_d"]] = rec["w_d"] * val

    def _record_reference(self):
        for rec in self._sources.values():
            if rec["kind"] == "tfsf":
                from .fdtd_tfsf import reference_value
                rec["ref_series"].append(reference_value(self, rec, self.t))

    # --- devices ----------------------------------------------------------------------------------------------------
    def _footprint(self) -> int:
        """Device bytes of the world: fields, coefficients, CPML memories, and (review B8-fdtd F18) the plane waves'
        incident tables and correction lists, the monitors' DFT accumulators and the dispersive nodes' arrays."""
        per = (16 if self.complex else 8)
        n = len(self.comps) * per + len(self.comps) * 8 * 2
        b = self.N * n
        b += sum(int(np.prod(p.shape)) * per for p in self.psi.values())
        for rec in getattr(self, "_sources", {}).values():
            if rec.get("kind") == "tfsf":
                t = rec.get("table")
                b += 0 if t is None else int(t.size) * per
                for L in rec.get("lists", []):
                    b += int(L["e_idx"].size) * (8 + 8 + 8 + per)  # index, coefficient, row, node weight
            elif rec.get("kind") == "current":
                b += int(np.size(rec.get("idx", []))) * (8 + per)
        for m in getattr(self, "_monitors", {}).values():
            for acc in m.get("accs", {}).values():
                b += int(np.prod(acc.acc.shape)) * 16
            for f in m.get("faces", []):
                for store in (f.E, f.H):
                    for s in store.values():
                        if s["acc"] is not None:
                            b += int(np.prod(s["acc"].acc.shape)) * 16
        for d in getattr(self, "disp", {}).values():
            k = len(d["idx"])
            b += k * (8 + 2 + 8 + 3 * 8 * max(d["nL"], 1) + 2 * 8 * max(d["nD"], 1)
                      + per * (2 * max(d["nL"], 1) + max(d["nD"], 1)))
        return int(b * 1.3)

    def _choose(self):
        force = "cpu" if self.device_mode == "cpu" else None
        size = self.N
        if self.device_mode == "gpu":
            cross = backend.settings()["crossover"].get(KERNEL, backend.kernels()[KERNEL].crossover)
            size = max(self.N, cross or 0)
        ch = backend.choose(KERNEL, size, footprint=self._footprint(), force=force,
                            why="выбрано для этого мира" if force else "")
        self._reason = ch.reason
        if ch.device != self.device:
            self._move(ch.device, ch.xp)

    def _move(self, device, xp):
        self.device, self.xp = device, (xp if device == "gpu" else np)
        self._to_device(self.xp)
        if device == "cpu":
            backend.release()

    def _to_device(self, xp):
        conv = (lambda a: xp.asarray(backend.to_numpy(a))) if xp is not np else (lambda a: backend.to_numpy(a))
        self.F = {c: conv(a) for c, a in self.F.items()}
        self.psi = {k: conv(a) for k, a in self.psi.items()}
        self.prof = {k: tuple(conv(x) for x in v) for k, v in self.prof.items()}
        for c, co in self.coef.items():
            for k, v in list(co.items()):
                if v is not None and not isinstance(v, float):
                    co[k] = conv(v)
        for c, d in self.disp.items():
            for k in ("idx", "mid", "c1", "c2", "c3", "aD", "bD", "cx", "P", "Pm", "PD"):
                d[k] = conv(d[k])
        for rec in self._sources.values():
            self._source_to(rec, xp)
        for m in self._monitors.values():
            self._flush(m)
            m["dev"] = None
            for f in m.get("faces", []):
                f.to(xp)
            for acc in m.get("accs", {}).values():
                acc.to(xp)
        if xp is not np:
            self._gpu_dummy = {"T": xp.zeros(1, complex if self.complex else float), "d": xp.zeros(1)}

    def _source_to(self, rec, xp):
        conv = (lambda a: xp.asarray(backend.to_numpy(a))) if xp is not np else (lambda a: backend.to_numpy(a))
        if rec["kind"] == "current":
            rec["idx_d"] = conv(rec["idx"])
            rec["w_d"] = conv(rec["w"])
        elif rec["kind"] == "tfsf":
            from .fdtd_tfsf import tfsf_to
            tfsf_to(rec, conv)

    # --- diagnostics ------------------------------------------------------------------------------------------------
    def describe(self) -> dict:
        return {"dim": self.dim, "pol": self.pol, "size": [self.interior[u] for u in range(self.dim)],
                "size_requested": [self.size_requested[u] for u in range(self.dim)], "dx": self.dx, "dt": self.dt,
                "courant": self.courant, "courant_limit": self.courant_limit,
                "shape": list(self.shape[:self.dim]), "boundary": {k: list(v) for k, v in self.boundary.items()},
                "pml": self._pml_spec.params(), "bloch": self.bloch[:self.dim].tolist(), "complex": self.complex,
                "averaging": self.averaging, "background": self.background.params(), "t": self.t,
                "steps": self.steps, "device": self.device, "device_reason": self._reason,
                "bodies": self.bodies(), "sources": self.sources(), "monitors": self.monitors()}

    def checks(self) -> dict:
        """The run's checks: the Courant number against the vacuum limit and the node maps' sufficient limit, the
        largest amplification radius of the world's media, finite fields, the realised lengths against the requested
        ones, per plane wave its window tail, omitted energy and correction nodes not in the background, and per flux
        or near-to-far monitor where its box lies relative to the total-field boxes."""
        radii = [self._medium_radius(m) for m in getattr(self, "_media", [self.background])]
        geo_ok = all(abs(self.interior[u] - self.size_requested[u]) <= 1e-9 * self.dx for u in range(self.dim))
        out = {"courant": {"value": self.courant, "limit": self.courant_limit,
                           "node_limit": getattr(self, "_node_limit", self.courant_limit),
                           "ok": self.courant <= min(self.courant_limit, getattr(self, "_node_limit", math.inf))
                           * (1 + 1e-12)},
               "stability": {"max_radius": max(radii) if radii else 1.0},
               "finite": self._healthy(),
               "geometry": {"requested": [self.size_requested[u] for u in range(self.dim)],
                            "realised": [self.interior[u] for u in range(self.dim)], "ok": geo_ok}}
        if not geo_ok:
            out["geometry"]["note"] = ("область отличается от заданной: длина оси — ближайшая реализуемая на сетке "
                                       "(целое число ячеек; между стенками PEC и PMC — нечётное число полуячеек)")
        for sid, rec in self._sources.items():
            if rec["kind"] == "tfsf":
                bad = self._tfsf_foreign_nodes(rec)
                d = {"window_tail": rec.get("tail", 0.0), "omitted_energy": rec.get("omitted", 0.0),
                     "foreign_nodes_at_faces": bad, "ok": bad == 0}
                if bad:
                    d["note"] = (f"{bad} узлов с поправками на гранях области полного поля не в фоновой среде (тело "
                                 f"пересекает грань или подходит к ней ближе полуячейки): падающая волна там не "
                                 f"точна, утечка не на уровне округления")
                out[f"tfsf_{sid}"] = d
        for mid, m in self._monitors.items():
            if m["kind"] in ("flux", "near2far"):
                rel = self._tf_relation(m["region"])
                if rel is not None:
                    ok = rel != "mixed" and (m["kind"] != "near2far" or rel == "sf")
                    out[f"monitor_{mid}"] = {"kind": m["kind"], "region": rel, "ok": ok}
        return out

    def _tfsf_foreign_nodes(self, rec) -> int:
        """Correction nodes of a TF/SF plane wave whose material is not the background's (review B8-fdtd F12)."""
        bg = self.background
        n = 0
        for L in rec["lists"]:
            c = L["target"]
            val, mid = self._mats[c]
            ref = bg.eps if c[0] == "e" else bg.mu
            idx = backend.to_numpy(L["e_idx"])
            bad = (mid.ravel()[idx] != 0) | (np.abs(val.ravel()[idx] - ref) > 1e-12 * ref)
            n += int(np.count_nonzero(bad))
        return n

    def _tf_relation(self, region):
        """Where a monitor's box (or plane) lies relative to the total-field boxes of the plane waves: "sf" (outside
        every one, with a cell's margin), "tf" (inside every one), "mixed", or None without plane waves."""
        lo_m, hi_m = [float(v) for v in region[0]], [float(v) for v in region[1]]
        rels = []
        g = self.dx * (1 - 1e-9)
        for rec in self._sources.values():
            if rec.get("kind") != "tfsf":
                continue
            lo_t, hi_t = rec["box"]
            inside = all(lo_m[u] >= lo_t[u] + g and hi_m[u] <= hi_t[u] - g for u in range(self.dim))
            disjoint = any(hi_m[u] <= lo_t[u] - g or lo_m[u] >= hi_t[u] + g for u in range(self.dim))
            encloses = all(lo_m[u] <= lo_t[u] - g and hi_m[u] >= hi_t[u] + g for u in range(self.dim))
            rels.append("tf" if inside else ("sf" if (disjoint or encloses) else "mixed"))
        if not rels:
            return None
        return rels[0] if all(r == rels[0] for r in rels) else "mixed"

    def cost_estimate(self) -> dict:
        key = "2d" if self.dim == 2 else "3d"
        comp_factor = len(self.comps) / (3 if self.dim == 2 else 6)
        cplx = 2.0 if self.complex else 1.0
        est = _interp_rate(key, self.device, self.N) * comp_factor * cplx
        meas = self._timing["seconds"] / self._timing["steps"] if self._timing["steps"] else None
        other = "gpu" if self.device == "cpu" else "cpu"
        return {"device": self.device, "cells": self.N, "per_step_s": est, "steps_per_s": 1.0 / est,
                "measured_per_step_s": meas, "sim_time_per_s": self.dt / (meas or est), "note": RATES_NOTE,
                "other_device_per_step_s": _interp_rate(key, other, self.N) * comp_factor * cplx}

    # --- state ------------------------------------------------------------------------------------------------------
    def state_dict(self) -> dict:
        """Plain data: ``FDTD.from_state_dict`` continues bit-identically (custom profiles, callable amplitudes and
        mask functions cannot be saved: refused with the reason)."""
        for m in self._monitors.values():
            self._flush(m)
        h = backend.to_numpy
        bodies = [{"id": k, "shape": v["shape"].params(), "medium": v["medium"].params(), "label": v["label"],
                   "averaging": v["averaging"]} for k, v in self._bodies.items()]
        sources = [{"id": k, "src": v["src"].params(), "ref_series": list(v.get("ref_series", [])),
                    "ref_step0": int(v.get("ref_step0", 0))} for k, v in self._sources.items()]
        mons = []
        for k, m in self._monitors.items():
            d = {"id": k, "kind": m["kind"]}
            if m["kind"] == "probe":
                d.update(point=list(m["point"]), components=[c for c, _, _ in m["items"]], t=list(m["t"]),
                         v={c: (np.concatenate(v) if v else np.zeros(0)) for c, v in m["v"].items()})
            elif m["kind"] == "dft":
                d.update(region=[list(m["region"][0]), list(m["region"][1])], freqs=m["freqs"].copy(),
                         components=list(m["accs"]), start=m["start"],
                         acc={c: a.host().copy() for c, a in m["accs"].items()})
            else:
                d.update(region=[list(m["region"][0]), list(m["region"][1])],
                         freqs=None if m["freqs"] is None else np.array(m["freqs"]), start=m["start"],
                         closed=m.get("closed", True),
                         direction=m["faces"][0].sign if (m["kind"] == "flux" and not m.get("closed", True)) else None,
                         faces=[{t: (s["acc"].host().copy() if s["acc"] is not None else None)
                                 for store in (f.E, f.H) for t, s in [(("e" if store is f.E else "h") + str(tt), ss)
                                                                      for tt, ss in store.items()]}
                                for f in m["faces"]])
                if m["kind"] == "flux":
                    d.update(t=list(m["t"]), p=list(m["p"]))
            mons.append(d)
        disp = {c: {k: h(d[k]).copy() for k in ("idx", "mid", "P", "Pm", "PD")} for c, d in self.disp.items()}
        return {
            "format": FORMAT, "size": [self.interior[u] for u in range(self.dim)],
            "size_requested": list(self.size_requested),
            "dx": self.dx, "pol": self.pol if self.dim == 2 else "tm", "courant": self.courant,
            "boundary": {k: list(v) for k, v in self.boundary.items()}, "pml": self._pml_spec.params(),
            "bloch": self.bloch[:self.dim].tolist(), "background": self.background.params(),
            "averaging": self.averaging, "device": self.device_mode, "shape": list(self.shape),
            "steps": self.steps, "t": self.t,
            "next": [self._next_body, self._next_source, self._next_monitor],
            "bodies": bodies, "sources": sources, "monitors": mons,
            "F": {c: h(a).copy() for c, a in self.F.items()},
            "psi": {f"{c}|{v}": h(a).copy() for (c, v), a in self.psi.items()},
            "disp": disp, "timing": dict(self._timing),
        }

    @classmethod
    def from_state_dict(cls, d: dict, device: str | None = None) -> "FDTD":
        if d.get("format") != FORMAT:
            raise ValueError(f"не состояние {FORMAT}")
        size = d["size"]
        o = cls.__new__(cls)
        o.__init__(size, d["dx"], pol=d["pol"], courant=d["courant"],
                   boundary={k: tuple(v) for k, v in d["boundary"].items()}, pml=PML(**d["pml"]),
                   bloch=d["bloch"] if any(d["bloch"]) else None, background=Medium.from_params(d["background"]),
                   averaging=d["averaging"], device="cpu")
        if list(o.shape) != list(d["shape"]):
            raise ValueError("сетка восстановленного мира не совпала с сохранённой")
        o.size_requested = list(d.get("size_requested", o.size_requested))
        o._bodies = {}
        for b in d["bodies"]:
            o._bodies[int(b["id"])] = {"shape": geo.shape_from_params(b["shape"]), "medium": Medium.from_params(
                b["medium"]), "label": b["label"], "averaging": b["averaging"]}
        o._next_body, o._next_source, o._next_monitor = d["next"]
        o._build_materials(first=True)
        for s in d["sources"]:
            o._sources[int(s["id"])] = {"src": src.source_from_params(s["src"])}
        o._build_sources()
        for s in d["sources"]:
            if "ref_series" in o._sources[int(s["id"])]:
                o._sources[int(s["id"])]["ref_series"] = list(s["ref_series"])
                o._sources[int(s["id"])]["ref_step0"] = int(s.get("ref_step0", 0))
        o.steps, o.t = int(d["steps"]), float(d["t"])
        o.F = {c: np.array(a) for c, a in d["F"].items()}
        o.psi = {(k.split("|")[0], int(k.split("|")[1])): np.array(a) for k, a in d["psi"].items()}
        for c, dd in d["disp"].items():
            od = o.disp[c]
            if not np.array_equal(od["idx"], dd["idx"]):
                raise ValueError("дисперсные узлы не совпали")
            for k in ("P", "Pm", "PD"):
                od[k] = np.array(dd[k])
        for m in d["monitors"]:
            k = m["kind"]
            if k == "probe":
                mid = o.add_probe(m["point"], m["components"])
                mm = o._monitors.pop(mid)
                mm["t"] = list(m["t"])
                mm["v"] = {c: ([np.asarray(v)] if len(v) else []) for c, v in m["v"].items()}
            elif k == "dft":
                mid = o.add_dft(m["region"], m["freqs"], m["components"])
                mm = o._monitors.pop(mid)
                mm["start"] = m["start"]
                for c, a in m["acc"].items():
                    mm["accs"][c].acc = np.array(a)
            else:
                if k == "flux":
                    mid = o.add_flux(m["region"], m["freqs"], m["closed"], m.get("direction"))
                else:
                    mid = o.add_near2far(m["region"], m["freqs"])
                mm = o._monitors.pop(mid)
                mm["start"] = m["start"]
                for f, saved in zip(mm["faces"], m["faces"]):
                    for store, kind in ((f.E, "e"), (f.H, "h")):
                        for tt, s in store.items():
                            a = saved.get(kind + str(tt))
                            if a is not None and s["acc"] is not None:
                                s["acc"].acc = np.array(a)
                if k == "flux":
                    mm["t"], mm["p"] = list(m["t"]), list(m["p"])
            o._monitors[int(m["id"])] = mm
        o._next_body, o._next_source, o._next_monitor = d["next"]
        o._timing = dict(d["timing"])
        o.device_mode = d["device"] if device is None else device
        o._choose()
        return o


_POOL = {}


def _pool():
    if "p" not in _POOL:
        from concurrent.futures import ThreadPoolExecutor
        _POOL["p"] = ThreadPoolExecutor(max_workers=FDTD_THREADS, thread_name_prefix="lfphys-fdtd")
    return _POOL["p"]


# --- benchmark and the kernel's registration ---------------------------------------------------------------------------
def _bench_world(size: int, dim: int, device: str):
    if dim == 2:
        n = max(16, int(round(math.sqrt(size))))
        w = FDTD((n * 0.05, n * 0.05), 0.05, pol="tm", boundary="periodic", device=device)
    else:
        n = max(8, int(round(size ** (1 / 3))))
        w = FDTD((n * 0.05,) * 3, 0.05, boundary="periodic", device=device)
    return w


def bench(size: int, dim: int = 2, device: str = "cpu", steps: int = 10) -> float:
    """Seconds per step of a periodic vacuum world of ``size`` cells (2-D TM or 3-D), after a warm-up."""
    w = _bench_world(size, dim, device)
    w.advance(2)
    t = time.perf_counter()
    w.advance(steps)
    return (time.perf_counter() - t) / steps


_BENCH = {}


def _bench(size: int, xp, cplx):
    dev = "gpu" if xp is not np else "cpu"
    key = (size, dev)
    if key not in _BENCH:
        _BENCH.clear()
        _BENCH[key] = _bench_world(size, 2, dev)
    _BENCH[key].advance(5)


backend.register(backend.KernelSpec(
    KERNEL, "Электромагнитное поле (FDTD, сетка Йи)",
    "шаг уравнений Максвелла: обновление E и H с CPML (песочница «Электричество и магнетизм», оптика)",
    gpu=True,
    precisions={"fp64": {"allowed": True},
                "fp32": {"allowed": False,
                         "why": "не проверено: накопление ошибки округления за 10⁴–10⁵ шагов и потоки энергии "
                                "(разности) — fp32 не предлагается"}},
    crossover=128 * 128,
    crossover_note=("измерено 2026-11-04 на RTX 2080 Ti против CPU контейнера (NumPy, 4 потока), fp64, мир в вакууме: "
                    "2-D TM — равны на 64², GPU ×2.3 на 128², ×19 на 512², ×67 на 4096²; 3-D — ×6 на 32³, ×25 на "
                    "64³, ×76 на 256³; источники и датчики добавляют свои запуски ядер; «Измерить заново» уточняет"),
    bench=_bench, bench_sizes=(64 * 64, 128 * 128, 256 * 256, 512 * 512, 1024 * 1024, 2048 * 2048)))
