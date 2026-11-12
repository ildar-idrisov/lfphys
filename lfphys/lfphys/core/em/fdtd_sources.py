# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Sources of the FDTD solver (``lfphys.core.em.fdtd``): time profiles, current sources and the plane wave of the
total-field / scattered-field (TF/SF) method, built as an exact plane wave of the Yee grid.

Units are the solver's: c = eps0 = mu0 = 1, a length unit chosen by the user, time in length / c; frequencies f are
ordinary (cycles per time unit; omega = 2 pi f).

**Time profiles** f(t): ``GaussianPulse`` exp(-(t - t0)^2 / (2 w^2)); ``ModulatedGaussian`` the same times
sin(2 pi f0 (t - t0) + phase) (spectral width sigma_f = 1 / (2 pi w)); both are exactly zero outside
|t - t0| <= cutoff w (default 6 w: the jump is exp(-18) = 1.5e-8); ``ContinuousWave`` sin(2 pi f0 t + phase) times a
C2 ramp s(t / T) = 10 s^3 - 15 s^4 + 6 s^5 over the ramp time T; ``Samples`` (values on a uniform time grid, linear
interpolation); any callable (not kept in a saved state).

**Current sources** (``CurrentSource``): a current density J (on an E component) or a magnetic current density M (on an
H component) on the component's Yee nodes in a region. A point (zero extent along every axis) is one node (the nearest)
and its ``amplitude`` is the current moment: J dV = amplitude f(t) (3-D: I l; 2-D: the current I of a line source per
unit length); zero extent along one axis (a line in 2-D, a plane in 3-D) gives a sheet with surface current amplitude
f(t), J = K / dx; a full box gives J = amplitude f(t). Soft (the default): the current enters Ampere's law, dD/dt = curl
H - J, at the half step t_{n+1/2} (a magnetic current M Faraday's law at t_n); hard: the field at the nodes is set to
amplitude f(t) right after its own update — E^{n+1} = amplitude f(t_{n+1}) after the E update, H^{n+1/2} = amplitude
f(t_{n+1/2}) after the H update, before the E update uses it (it reflects whatever arrives; review B8-fdtd F2: a hard H
was set after the E update, which never saw it, and diverged). A spatial factor ``amplitude(x, y[, z])`` (a callable or
complex numbers with Bloch periodicity) may vary over the region.

**The plane wave (TF/SF).** Inside a box ("total field") the solver carries the total field, outside it the
scattered field; along the box's faces every update whose stencil crosses the face is corrected with the incident
field at the node across (Schneider, Understanding the FDTD Method, §3.10, §8.5, §9.5). The leak of the incident wave into the scattered-field region is the mismatch
between the incident field used and the waves the grid itself carries. Here the incident field is an **exact plane
wave of the Yee grid**: every frequency omega of the source's sampled profile travels with the wavevector k that solves
the grid's dispersion relation

    eps mu sin^2(omega dt / 2) / dt^2 = sum_u sin^2(k_u dx / 2) / dx^2,

and the components' amplitudes satisfy the discrete Maxwell equations, H = K x E / (Omega mu), K . E = 0, with
K_u = (2 / dx) sin(k_u dx / 2), Omega = (2 / dt) sin(omega dt / 2), each component sampled at its own node and time.
Such a field solves the update equations exactly, so the leak is round-off plus what the injection's start cuts off
(measured in the tests). For a pulse the incident time series of every node on the faces is computed once by FFT (a
window around the pulse's arrival); the window's tail — what the periodic FFT wraps into the series, i.e. the
incident wave's value before the run starts — is checked: the measured leak is ~0.3-0.4 x the tail, 2-3e-9 for
pulses away from the end of the propagating band; a pulse whose spectrum reaches a Bloch wave's cut-off (or the grid's
band edge) has a precursor there that no window length removes, and a tail above 1e-6 is refused (review B8-fdtd F7).
For a continuous wave the one frequency is exact and the ramp travels with the discrete group delay (dk/domega of the
grid's wave; an approximation only while the ramp lasts). Two families:

* a fixed direction (2-D any angle, 3-D any direction; in 3-D the faces' series must fit in memory, else refused; a
  3-D polarization (nearly) along the direction is refused, F16);
* with Bloch-periodic sides spanned by the box: the wave keeps the solver's Bloch wavevector k_par along them and each
  frequency takes its own angle (k_n from the dispersion relation); frequencies below the cut-off (evanescent) are
  left out and their share of the source energy is reported.
"""

from __future__ import annotations

import math

import numpy as np

from ...i18n import T, is_t

ABOUT = {
    "layer": "core", "kind": "numerics",
    "title": T("FDTD: sources (pulses, currents, a total-field/scattered-field plane wave)"),
    "statement": T("Time profiles (a Gaussian pulse, a modulated Gaussian, a continuous wave with a smooth switch-on, "
                   "samples); current sources J and M at a point, on a line or plane and in a volume (soft and hard: "
                   "a hard E is set after the E update, a hard H after the H update); a plane wave by the "
                   "total-field/scattered-field method, built as an exact plane wave of the Yee grid (every frequency "
                   "with the wave vector from the grid's dispersion relation), so that the leak through the boundary is "
                   "the round-off level plus what the start of the run cuts off (the tail of the series' window)."),
    "validity": T("a plane wave in a homogeneous lossless background at the faces (bodies on the faces are flagged in "
                  "checks()); for a pulse the leak is ~0.3–0.4 of the window's tail: 2–3e-9 away from a cut-off, at a "
                  "Bloch wave's cut-off a precursor, a tail above 1e-6 is refused; a continuous wave is exact after "
                  "its switch-on, while it switches on the envelope travels with the discrete group delay; in 3-D at "
                  "oblique incidence limited by memory"),
    "basis": [T("Schneider, Understanding the FDTD Method (2010), §3.10, §8.5, §9.5 (TF/SF); §7.4 (the dispersion "
                "relation of Yee's scheme, eqs. 7.33–7.34)")],
    "conflicts": [],
}


def as_text(x):
    """A label as given: a translatable text (``lfphys.i18n.T``; its JSON form from a saved state becomes a ``T``
    again) or a string."""
    if is_t(x):
        return x if isinstance(x, T) else T(x)  # rebuilt from its JSON form (lfphys.i18n.T)
    return str(x)


TWO_PI = 2.0 * math.pi


# --- time profiles ----------------------------------------------------------------------------------------------------
class Profile:
    kind = "profile"
    frequency = None  # the carrier (cycles per time unit), if any

    def __call__(self, t):
        raise NotImplementedError

    def end(self) -> float:
        """Time after which the profile is zero (inf for a continuous wave)."""
        return math.inf

    def params(self) -> dict:
        raise NotImplementedError


class GaussianPulse(Profile):
    kind = "gaussian"

    def __init__(self, width: float, t0: float | None = None, cutoff: float = 6.0):
        self.width = float(width)
        if not self.width > 0:
            raise ValueError(T("pulse width > 0"))
        self.cutoff = float(cutoff)
        self.t0 = self.cutoff * self.width if t0 is None else float(t0)

    def __call__(self, t):
        t = np.asarray(t, float)
        s = (t - self.t0) / self.width
        return np.where(np.abs(s) <= self.cutoff, np.exp(-0.5 * s * s), 0.0)

    def end(self):
        return self.t0 + self.cutoff * self.width

    def params(self):
        return {"kind": self.kind, "width": self.width, "t0": self.t0, "cutoff": self.cutoff}


class ModulatedGaussian(Profile):
    """sin(2 pi f0 (t - t0) + phase) exp(-(t - t0)^2 / (2 w^2)); give ``width`` w (time) or ``fwidth`` (the spectral
    standard deviation in frequency, w = 1 / (2 pi fwidth))."""
    kind = "modulated_gaussian"

    def __init__(self, frequency: float, width: float | None = None, fwidth: float | None = None,
                 t0: float | None = None, phase: float = 0.0, cutoff: float = 6.0):
        self.frequency = float(frequency)
        if (width is None) == (fwidth is None):
            raise ValueError(T("modulated pulse: give width or fwidth"))
        self.width = float(width) if width is not None else 1.0 / (TWO_PI * float(fwidth))
        if not (self.width > 0 and self.frequency > 0):
            raise ValueError(T("pulse frequency and width > 0"))
        self.cutoff, self.phase = float(cutoff), float(phase)
        self.t0 = self.cutoff * self.width if t0 is None else float(t0)

    def __call__(self, t):
        t = np.asarray(t, float)
        s = (t - self.t0) / self.width
        return np.where(np.abs(s) <= self.cutoff,
                        np.sin(TWO_PI * self.frequency * (t - self.t0) + self.phase) * np.exp(-0.5 * s * s), 0.0)

    def end(self):
        return self.t0 + self.cutoff * self.width

    def params(self):
        return {"kind": self.kind, "frequency": self.frequency, "width": self.width, "t0": self.t0,
                "phase": self.phase, "cutoff": self.cutoff}


def smootherstep(s):
    s = np.clip(s, 0.0, 1.0)
    return s * s * s * (10.0 + s * (-15.0 + 6.0 * s))


class ContinuousWave(Profile):
    """sin(2 pi f0 t + phase) s(t / ramp), s the C2 ramp 10 s^3 - 15 s^4 + 6 s^5 (ramp 0: switched on at once)."""
    kind = "cw"

    def __init__(self, frequency: float, ramp: float = 0.0, phase: float = 0.0):
        self.frequency, self.ramp, self.phase = float(frequency), float(ramp), float(phase)
        if not self.frequency > 0 or self.ramp < 0:
            raise ValueError(T("frequency > 0, switch-on time ≥ 0"))

    def envelope(self, t):
        t = np.asarray(t, float)
        if self.ramp == 0:
            return np.where(t >= 0, 1.0, 0.0)
        return smootherstep(t / self.ramp)

    def __call__(self, t):
        t = np.asarray(t, float)
        return np.sin(TWO_PI * self.frequency * t + self.phase) * self.envelope(t)

    def params(self):
        return {"kind": self.kind, "frequency": self.frequency, "ramp": self.ramp, "phase": self.phase}


class Samples(Profile):
    """Values on the times t0 + k dt_s (linear interpolation; zero outside)."""
    kind = "samples"

    def __init__(self, values, dt: float, t0: float = 0.0):
        self.values = np.asarray(values, float).ravel()
        self.dt_s, self.t0 = float(dt), float(t0)
        if len(self.values) < 2 or not self.dt_s > 0:
            raise ValueError(T("samples: at least two, step > 0"))

    def __call__(self, t):
        t = np.asarray(t, float)
        tt = self.t0 + self.dt_s * np.arange(len(self.values))
        return np.interp(t, tt, self.values, left=0.0, right=0.0)

    def end(self):
        return self.t0 + self.dt_s * (len(self.values) - 1)

    def params(self):
        return {"kind": self.kind, "values": self.values.tolist(), "dt": self.dt_s, "t0": self.t0}


class Custom(Profile):
    """Any callable f(t) (vectorised); ``end``: when it is zero for good (inf if never). Not kept in a saved state."""
    kind = "custom"

    def __init__(self, fn, end: float = math.inf, frequency: float | None = None):
        self.fn, self._end = fn, float(end)
        self.frequency = None if frequency is None else float(frequency)

    def __call__(self, t):
        return np.asarray(self.fn(np.asarray(t, float)), float)

    def end(self):
        return self._end

    def params(self):
        raise ValueError(T("a profile given as a function is not saved in the state: give it as samples (Samples)"))


def profile_from_params(d: dict) -> Profile:
    k = d["kind"]
    if k == "gaussian":
        return GaussianPulse(d["width"], d["t0"], d.get("cutoff", 6.0))
    if k == "modulated_gaussian":
        return ModulatedGaussian(d["frequency"], width=d["width"], t0=d["t0"], phase=d.get("phase", 0.0),
                                 cutoff=d.get("cutoff", 6.0))
    if k == "cw":
        return ContinuousWave(d["frequency"], d.get("ramp", 0.0), d.get("phase", 0.0))
    if k == "samples":
        return Samples(d["values"], d["dt"], d.get("t0", 0.0))
    raise ValueError(T("unknown profile {kind}", kind=repr(k)))


def _as_profile(p) -> Profile:
    if isinstance(p, Profile):
        return p
    if callable(p):
        return Custom(p)
    raise ValueError(T("profile: a Profile object or a function f(t)"))


# --- current sources --------------------------------------------------------------------------------------------------
COMPONENTS = ("ex", "ey", "ez", "hx", "hy", "hz")


class CurrentSource:
    """A current J (on ``component`` ex/ey/ez) or a magnetic current M (hx/hy/hz) in a region: ``position`` (a point)
    or ``region`` = (lo, hi). ``amplitude``: a number (complex allowed) or a callable of the coordinates; with the
    profile f(t). ``hard``: set the field instead of adding a current."""

    def __init__(self, component: str, profile, position=None, region=None, amplitude=1.0, hard: bool = False,
                 label: str = ""):
        if component not in COMPONENTS:
            raise ValueError(T("source component: one of {options}", options=", ".join(COMPONENTS)))
        if (position is None) == (region is None):
            raise ValueError(T("source: a point (position) or a region (region), one of the two"))
        self.component = component
        self.profile = _as_profile(profile)
        if position is not None:
            p = tuple(float(v) for v in position)
            self.region = (p, p)
        else:
            lo, hi = region
            self.region = (tuple(float(v) for v in lo), tuple(float(v) for v in hi))
            if len(self.region[0]) != len(self.region[1]) or any(h < l for l, h in zip(*self.region)):
                raise ValueError(T("source region: lo ≤ hi along every axis"))
        self.amplitude = amplitude
        self.hard = bool(hard)
        self.label = as_text(label)

    def params(self) -> dict:
        amp = self.amplitude
        if callable(amp):
            raise ValueError(T("a spatial factor given as a function is not saved in the state"))
        amp = [float(np.real(amp)), float(np.imag(amp))]
        return {"type": "current", "component": self.component, "profile": self.profile.params(),
                "region": [list(self.region[0]), list(self.region[1])], "amplitude": amp, "hard": self.hard,
                "label": self.label}


# --- the Yee grid's dispersion ----------------------------------------------------------------------------------------
def omega_tilde(omega, dt):
    """Omega = (2 / dt) sin(omega dt / 2): the time derivative's eigenvalue on the leapfrog grid."""
    return 2.0 / dt * np.sin(np.asarray(omega, float) * dt / 2.0)


def yee_wavenumber(omega, direction, dx, dt, n_bg: float = 1.0):
    """|k| solving eps mu sin^2(omega dt/2)/dt^2 = sum_u sin^2(k u_u dx/2)/dx^2 for a unit ``direction`` u (D comps),
    omega >= 0 (array). NaN where no real k exists (beyond the grid's band edge along that direction)."""
    w = np.atleast_1d(np.asarray(omega, float))
    u = np.asarray(direction, float)
    u = u / np.linalg.norm(u)
    rhs = (n_bg * np.sin(w * dt / 2.0) / dt) ** 2 * dx * dx  # sum_u sin^2(k u_u dx / 2)
    umax = np.max(np.abs(u))
    kmax = math.pi / (dx * umax)  # the LHS increases up to here
    lhs_max = float(np.sum(np.sin(kmax * np.abs(u) * dx / 2.0) ** 2))
    k = np.full(w.shape, np.nan)
    ok = rhs <= lhs_max * (1 + 1e-15)
    lo = np.zeros(w.shape)
    hi = np.full(w.shape, kmax)
    # bisection (monotone), then Newton polish
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        val = np.sum(np.sin(mid[..., None] * np.abs(u) * dx / 2.0) ** 2, axis=-1)
        big = val > rhs
        hi = np.where(big, mid, hi)
        lo = np.where(big, lo, mid)
    kk = 0.5 * (lo + hi)
    for _ in range(3):
        s = np.sin(kk[..., None] * np.abs(u) * dx / 2.0)
        c = np.cos(kk[..., None] * np.abs(u) * dx / 2.0)
        f = np.sum(s * s, axis=-1) - rhs
        fp = np.sum(2 * s * c * np.abs(u) * dx / 2.0, axis=-1)
        step = np.where(fp > 0, f / np.where(fp > 0, fp, 1.0), 0.0)
        kk = np.clip(kk - step, 0.0, kmax)
    k[ok] = kk[ok]
    return k if np.ndim(omega) else float(k[0])


def yee_normal_wavenumber(omega, k_par, dx, dt, n_bg: float = 1.0):
    """k_n >= 0 along the normal axis for a fixed parallel wavevector (Bloch): sin^2(k_n dx/2) = dx^2 [eps mu
    sin^2(omega dt/2)/dt^2 - sum_par sin^2(k_p dx/2)/dx^2]; NaN where evanescent or beyond the band edge."""
    w = np.atleast_1d(np.asarray(omega, float))
    kp = np.asarray(k_par, float)
    s2 = (n_bg * np.sin(w * dt / 2.0) / dt) ** 2 * dx * dx - float(np.sum(np.sin(kp * dx / 2.0) ** 2))
    k = np.full(w.shape, np.nan)
    ok = (s2 >= 0) & (s2 <= 1)
    k[ok] = 2.0 / dx * np.arcsin(np.sqrt(s2[ok]))
    return k


def yee_frequency(k, dx, dt, n_bg: float = 1.0):
    """omega(k) of the Yee grid for a wavevector k (array (..., D)): sin(omega dt/2) = (dt/(n dx)) sqrt(sum sin^2)."""
    k = np.asarray(k, float)
    s = np.sqrt(np.sum(np.sin(k * dx / 2.0) ** 2, axis=-1)) * dt / (n_bg * dx)
    return 2.0 / dt * np.arcsin(np.clip(s, -1.0, 1.0))


# --- the plane wave of the TF/SF method --------------------------------------------------------------------------------
class PlaneWave:
    """A plane wave injected by the TF/SF method. ``box`` = (lo, hi): the total-field region (+-inf: no face on that
    side; a periodic axis must be spanned entirely or left at +-inf). ``direction``: an angle (2-D, radians from +x
    toward +y) or a vector (3-D); ignored on Bloch-periodic sides spanned by the box, where the wave takes the
    solver's Bloch wavevector and travels along the box's one finite normal (``normal_axis``: inferred). Polarization:
    2-D TM (Ez) and TE (Hz) are implied by the solver's ``pol`` (with pol "both", ``polarization`` "tm" or "te");
    3-D: ``polarization`` a vector (made orthogonal to the grid's K). ``amplitude``: the E amplitude at the reference
    point (the box's entry corner, or ``reference``)."""

    def __init__(self, profile, box, direction=0.0, polarization=None, amplitude: float = 1.0, reference=None,
                 label: str = ""):
        self.profile = _as_profile(profile)
        lo, hi = box
        self.box = (tuple(float(v) for v in lo), tuple(float(v) for v in hi))
        if len(self.box[0]) != len(self.box[1]) or any(not h > l for l, h in zip(*self.box)):
            raise ValueError(T("total-field region: hi > lo along every axis"))
        self.direction = direction
        self.polarization = polarization
        self.amplitude = float(amplitude)
        self.reference = None if reference is None else tuple(float(v) for v in reference)
        self.label = as_text(label)

    def params(self) -> dict:
        d = self.direction
        d = float(d) if np.ndim(d) == 0 else [float(v) for v in d]
        p = self.polarization
        p = p if (p is None or isinstance(p, str)) else [float(v) for v in p]
        return {"type": "planewave", "profile": self.profile.params(), "box": [list(self.box[0]), list(self.box[1])],
                "direction": d, "polarization": p, "amplitude": self.amplitude,
                "reference": None if self.reference is None else list(self.reference), "label": self.label}


def source_from_params(d: dict):
    if d["type"] == "current":
        a = d["amplitude"]
        amp = complex(a[0], a[1]) if a[1] != 0 else a[0]
        return CurrentSource(d["component"], profile_from_params(d["profile"]), region=d["region"], amplitude=amp,
                             hard=d["hard"], label=d.get("label", ""))
    if d["type"] == "planewave":
        box = d["box"]
        box = ([float(v) for v in box[0]], [float(v) for v in box[1]])
        return PlaneWave(profile_from_params(d["profile"]), box, d["direction"], d["polarization"], d["amplitude"],
                         d["reference"], d.get("label", ""))
    raise ValueError(T("unknown source {kind}", kind=repr(d["type"])))
