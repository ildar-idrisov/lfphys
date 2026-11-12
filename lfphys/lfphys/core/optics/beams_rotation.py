# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The rotational Doppler effect (plan P14.7): closed forms and measurables computed from sampled fields.

Conventions: time exp(-i omega t); a rotation rate Omega > 0 turns from +x towards +y (counter-clockwise about +z, the
direction of propagation); a field of total angular momentum m = l + sigma about z (``lfphys.core.optics.beams``:
exp(i l phi) times the circular vector e_sigma = (x^ + i sigma y^)/sqrt2, or the exact vector beam) obeys
R_alpha^-1 E(R_alpha r) = exp(i m alpha) E(r).

* **An observer rotating at Omega** (its position and its polarisation axes co-rotating) samples
  R(-Omega t) E(R(Omega t) r0) exp(-i omega t) = E(r0) exp(-i (omega - m Omega) t): the frequency omega - m Omega.
  (For circular polarisation alone, B. A. Garetz, J. Opt. Soc. Am. 71, 609 (1981); for the total angular momentum,
  I. & Z. Bialynicki-Birula, Phys. Rev. Lett. 78, 2539 (1997): texts not obtained, see the sources file.)
* **A beam turned at Omega_b** (an image rotator, ideally a Dove prism turned at Omega_b / 2: the image is mirrored
  across the prism's axis and so turned by twice its angle; l -> -l, and for an ideal mirror-like rotator also
  sigma -> -sigma): the output has m_out = -(l + sigma) and the frequency omega + m_out Omega_b. J. Courtial et al.,
  Phys. Rev. Lett. 80, 3217 (1998) (abstract and thesis, verified): "the frequency shift, l Omega, imparted to a
  mm-wave beam with an orbital angular momentum of l hbar per photon, when the beam is rotated at angular frequency
  Omega"; with a half-wave plate turning too, (l + sigma) Omega (Phys. Rev. Lett. 81, 4828 (1998)). The scalar
  rotator (``vector=False``) leaves the polarisation alone: omega + l_out Omega_b.
* **Light scattered by a spinning surface** (M. P. J. Lavery, F. C. Speirits, S. M. Barnett, M. J. Padgett, Science
  341, 537 (2013), accepted manuscript, Eqs. 3-4): the surface's complex reflectance rho turns at Omega,
  rho(r, phi - Omega t) = sum_n rho_n(r) exp(i n (phi - Omega t)); the light scattered on the axis (the zero
  transverse spatial frequency, int U rho dA) of an incident exp(i l phi) beam takes only n = -l: frequency
  omega - l Omega, independent of polarisation; for an incident superposition of +l and -l the on-axis intensity
  beats at 2 |l| Omega ("f_mod = 2|l| Omega / 2 pi"). The shift follows from the rotation alone (the harmonic n = -l of
  any reflectance turning at Omega); the surface itself, a thin phase screen, is a model of the approximation layer
  (``lfphys.theories.approx.beams_thin_masks``: ``SpinningSurface``, ``on_axis_amplitude``; review B8-beams, O7).
  Sign: in this engine's conventions the light scattered onto the axis from an exp(i l phi) beam by a disc turning
  in the positive sense (Omega > 0, the sense of the beam's orbital angular momentum for l > 0) is red-shifted by
  l Omega: the light does work on the disc ("Doing work against this force is the energy input required to shift the
  frequency of the light", Lavery et al.); Lavery's Fig. 2 states "the light scattered from the positive l beam will
  be blue-shifted" for their disc, whose sense of rotation relative to the beam's l the caption does not fix, so the
  two agree for a disc turning against the positive l beam's orbital angular momentum.

Measurables: ``sample_rotating`` (an observer's samples), ``image_rotator`` (the output field of a turned rotator),
and ``spectrum`` / ``peak_frequency`` of the sampled series (the tests and v16 compare the measured frequency with the
closed forms).
"""

from __future__ import annotations

import math
from typing import Callable

import numpy as np

from lfphys.i18n import T

ABOUT = {
    "layer": "core", "kind": "exact consequence",
    "title": T("Rotational Doppler effect"),
    "statement": T("A field with total angular momentum m = l + σ in a frame rotating at Ω has the frequency ω − mΩ; "
                   "a beam rotated at the rate Ω (a Dove prism at Ω/2) is shifted by m_out·Ω; light scattered onto the "
                   "axis by a rotating surface is shifted by −lΩ, and a superposition of ±l gives beats at 2|l|Ω. "
                   "Closed forms and a measurement from a time sample of the field (its spectrum)."),
    "validity": T("Ω ≪ ω (non-relativistic rotation); an ideal rotation of the image; the model of the scattering "
                  "surface (a thin phase screen, scalar) is in theories.approx.beams_thin_masks"),
    "basis": [T("Courtial et al., Phys. Rev. Lett. 80, 3217 (1998) (abstract; Courtial's thesis, 1999)"),
              T("Courtial et al., Phys. Rev. Lett. 81, 4828 (1998) — the (l + σ)Ω shift (abstract)"),
              T("Lavery, Speirits, Barnett, Padgett, Science 341, 537 (2013), eqs. 1, 3, 4"),
              T("Garetz, J. Opt. Soc. Am. 71, 609 (1981) (full text not obtained)")],
    "conflicts": [],
}


# --- closed forms ------------------------------------------------------------------------------------------------------
def rotating_frame_frequency(omega: float, m: int, Omega: float) -> float:
    """The frequency an observer rotating at Omega about the axis measures for a field of total angular momentum m."""
    return omega - m * Omega


def rotated_beam_frequency(omega: float, m_out: int, Omega_beam: float) -> float:
    """The frequency of a beam of total angular momentum m_out turned at Omega_beam (the rotator's output)."""
    return omega + m_out * Omega_beam


def scattered_on_axis_shift(l: int, Omega: float) -> float:
    """Frequency shift of the light scattered onto the axis by a surface spinning at Omega (incident OAM l): -l Omega."""
    return -l * Omega


def superposition_beat(l: int, Omega: float) -> float:
    """Angular frequency of the on-axis intensity beat for an incident superposition of +l and -l: 2 |l| Omega."""
    return 2 * abs(l) * Omega


# --- measurables ----------------------------------------------------------------------------------------------------------
def _rot(a):
    c, s = np.cos(a), np.sin(a)
    return c, s


def sample_rotating(field_fn: Callable, r0: float, phi0: float, z0: float, Omega: float, omega: float, times):
    """The complex field an observer rotating at Omega records at the co-rotating point (r0, phi0 + Omega t, z0), in
    its co-rotating axes, times exp(-i omega t). ``field_fn(x, y, z) -> E (3, n)`` (complex amplitudes; a scalar field
    may return shape (n,)). Returns (3, nt) (or (nt,) for a scalar)."""
    t = np.asarray(times, float)
    c, s = _rot(phi0 + Omega * t)
    E = np.asarray(field_fn(r0 * c, r0 * s, np.full_like(t, z0)), complex)
    ph = np.exp(-1j * omega * t)
    if E.ndim == 1:
        return E * ph
    ca, sa = _rot(Omega * t)  # R(-Omega t) applied to the components
    return np.stack([ca * E[0] + sa * E[1], -sa * E[0] + ca * E[1], E[2]]) * ph


def circular_components(E, sigma: int):
    """The coefficient of e_sigma = (x^ + i sigma y^)/sqrt2 in E (3, ...): (E_x - i sigma E_y)/sqrt2."""
    return (E[0] - 1j * sigma * E[1]) / math.sqrt(2.0)


def image_rotator(field_fn: Callable, alpha: float, vector: bool = True) -> Callable:
    """The output of an ideal image rotator (a Dove prism) whose axis is at angle alpha: the transverse field mirrored
    across the line at alpha, E_out(r) = M E(M r), M = reflection (for ``vector``; the scalar rotator mirrors only the
    pattern). Turning the prism by alpha turns the image by 2 alpha."""
    c2, s2 = math.cos(2 * alpha), math.sin(2 * alpha)

    def out(x, y, z):
        x, y = np.asarray(x, float), np.asarray(y, float)
        xm, ym = c2 * x + s2 * y, s2 * x - c2 * y
        E = np.asarray(field_fn(xm, ym, z), complex)
        if E.ndim == x.ndim or not vector:
            return E
        return np.stack([c2 * E[0] + s2 * E[1], s2 * E[0] - c2 * E[1], E[2]])
    return out


def spectrum(signal, dt: float, pad: int = 8, window: bool = True):
    """(angular frequencies [rad per unit time], power) of a sampled series (complex or real), zero-padded ``pad``
    times, Hann window optional; frequencies sorted (two-sided), in the physics convention of this module: a series
    exp(-i omega t) has its line at +omega."""
    v = np.asarray(signal, complex)
    if window:
        v = v * np.hanning(len(v))
    n = pad * len(v)
    F = np.fft.fftshift(np.fft.ifft(v, n)) * n  # sum_j v_j exp(+i omega t_j): exp(-i omega t) peaks at +omega
    f = 2 * math.pi * np.fft.fftshift(np.fft.fftfreq(n, dt))
    return f, np.abs(F) ** 2


def peak_frequency(signal, dt: float, pad: int = 16, positive: bool = False, exclude_dc: bool = False,
                   window: bool = True) -> float:
    """The angular frequency of the strongest spectral line of a sampled series, refined by a parabola through the
    logarithm of the three largest padded samples. ``positive``: only frequencies > 0 (a real series);
    ``exclude_dc``: the mean is removed first."""
    v = np.asarray(signal, complex)
    if exclude_dc:
        v = v - v.mean()
    f, P = spectrum(v, dt, pad, window)
    mask = f > 0 if positive else np.ones_like(f, bool)
    idx = np.nonzero(mask)[0]
    i = int(idx[np.argmax(P[idx])])
    if 0 < i < len(P) - 1 and P[i - 1] > 0 and P[i + 1] > 0:
        a, b, c = np.log(P[i - 1]), np.log(P[i]), np.log(P[i + 1])
        den = a - 2 * b + c
        d = 0.5 * (a - c) / den if den != 0 else 0.0
        return float(f[i] + d * (f[1] - f[0]))
    return float(f[i])


def modulation_depth(series) -> float:
    """(max - min) / (max + min) of a real series (0 for a constant)."""
    v = np.asarray(series, float)
    s = v.max() + v.min()
    return float((v.max() - v.min()) / s) if s else 0.0
