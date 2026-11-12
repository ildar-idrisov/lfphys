# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Colour of a spectrum for display: CIE 1931 XYZ and sRGB. A display tool, not physics.

* Colour matching functions: the multi-lobe piecewise-Gaussian fit of Wyman, Sloan & Shirley, "Simple Analytic
  Approximations to the CIE XYZ Color Matching Functions", JCGT 2(2), 1-11 (2013), Table 1 / Listing 1 (coefficients
  grepped from the paper's text, 2026-10-28): x(l) = sum a_i exp(-((l - b_i) S)^2 / 2) with S = g_i below b_i and d_i
  above, wavelength l in nm. The paper's Table 2 gives its maximum squared errors against the 1 nm CIE 1931 tables:
  2.0e-4 (x), 6.4e-5 (y), 4.9e-4 (z), i.e. absolute errors below 0.0142, 0.0080, 0.0222. The CIE tables themselves
  are not copied here (only the published formula is implemented).
* A black body at temperature T: X = int B_lambda(T) xbar(lambda) dlambda over 360-830 nm (Planck's law from
  lfphys.core.optics.radiation), tabulated on a logarithmic grid of T for speed (``BlackbodyXYZ``) and interpolated
  in log X; above the table's top the Rayleigh-Jeans tail (X proportional to T) continues it, below its bottom a body
  is black on screen.
* XYZ to sRGB: the IEC 61966-2-1 matrix and transfer curve as given in the sRGB article's text (rounded four-decimal
  matrix; 12.92 x below 0.0031308, 1.055 x^(1/2.4) - 0.055 above; grepped 2026-10-28), D65 white.
* Tone mapping for a display: an exposure scale, then the luminance compressed as L / (1 + L) with the chromaticity
  kept, then colours beyond the gamut brought in by scaling (no hue shift).
"""

from __future__ import annotations

import math

import numpy as np
from scipy.interpolate import CubicSpline

from ..core.optics import radiation
from lfphys.i18n import T

ABOUT = {
    "layer": "tools", "kind": "display",
    "title": T("The colour of a spectrum on screen: CIE 1931 XYZ and sRGB"),
    "statement": T("The CIE 1931 colour-matching functions by the analytic approximation of Wyman–Sloan–Shirley "
                   "(2013); the colour of a black body by Planck's law; the transform XYZ → sRGB (IEC 61966-2-1); "
                   "tone mapping for the screen."),
    "validity": T("a display tool, not physics: the CIE functions are approximated with an error up to 0.022 "
                  "(absolute); the brightness on screen is compressed"),
    "basis": ["Wyman, Sloan, Shirley, JCGT 2(2), 1 (2013): Table 1, Listing 1",
              T("IEC 61966-2-1:1999 (sRGB): the matrix XYZ → linear sRGB and the transfer curve")],
    "conflicts": [],
}

# (alpha, beta [nm], gamma, delta [1/nm]) for each lobe: Wyman, Sloan & Shirley (2013), Table 1
_LOBES = {
    "x": ((0.362, 442.0, 0.0624, 0.0374), (1.056, 599.8, 0.0264, 0.0323), (-0.065, 501.1, 0.0490, 0.0382)),
    "y": ((0.821, 568.8, 0.0213, 0.0247), (0.286, 530.9, 0.0613, 0.0322)),
    "z": ((1.217, 437.0, 0.0845, 0.0278), (0.681, 459.0, 0.0385, 0.0725)),
}
#: the paper's maximum absolute errors against the 1 nm CIE 1931 tables (square roots of Table 2's squared errors)
CMF_MAX_ABS_ERROR = {"x": math.sqrt(2.0e-4), "y": math.sqrt(6.4e-5), "z": math.sqrt(4.9e-4)}

#: XYZ -> linear sRGB (IEC 61966-2-1, the four-decimal matrix)
XYZ_TO_SRGB = np.array([[3.2406, -1.5372, -0.4986],
                        [-0.9689, 1.8758, 0.0415],
                        [0.0557, -0.2040, 1.0570]])

LAMBDA_NM = np.arange(360.0, 830.0 + 0.5, 1.0)  # integration grid (1 nm, as the CIE tables)


def cmf(lam_nm, which: str):
    """One colour matching function (fit) at wavelengths in nm."""
    lam = np.asarray(lam_nm, float)
    out = np.zeros_like(lam)
    for a, b, g, d in _LOBES[which]:
        t = (lam - b) * np.where(lam < b, g, d)
        out = out + a * np.exp(-0.5 * t * t)
    return out


def cmfs(lam_nm):
    """(xbar, ybar, zbar) stacked on the last axis."""
    return np.stack([cmf(lam_nm, k) for k in "xyz"], axis=-1)


def spectrum_xyz(lam_nm, power):
    """XYZ of a spectral power (or radiance) sampled at ``lam_nm`` (trapezoid rule, per nm)."""
    lam = np.asarray(lam_nm, float)
    p = np.asarray(power, float)
    w = cmfs(lam) * p[..., None]
    return np.trapezoid(w, lam, axis=-2) if hasattr(np, "trapezoid") else np.trapz(w, lam, axis=-2)


def blackbody_xyz(T):
    """XYZ of black-body radiance B_lambda(T) (W m^-2 sr^-1 per nm of wavelength) by direct integration."""
    T = np.atleast_1d(np.asarray(T, float))
    lam_m = LAMBDA_NM * 1e-9
    B = np.stack([radiation.planck_lambda(lam_m, float(t)) * 1e-9 for t in T])  # per nm
    return spectrum_xyz(LAMBDA_NM, B)


def chromaticity(XYZ):
    XYZ = np.asarray(XYZ, float)
    s = XYZ.sum(axis=-1, keepdims=True)
    return XYZ[..., :2] / np.where(s > 0, s, 1.0)


class BlackbodyXYZ:
    """XYZ of black bodies tabulated on a logarithmic grid of temperature (T0 .. T1 K) and interpolated in log XYZ by
    cubic splines (B is analytic in T; tests: below 1e-6 of direct integration from 500 K up). Below T0 a body is
    black on screen (at 200 K its luminance is 1.3e-45 of a 5800 K body's: the Wien factor exp(-hc/(lambda k T)));
    above T1 the Rayleigh-Jeans tail continues the table, X proportional to T (at T1 = 1e7 K the next term is
    hc/(lambda k T) <= 4e-3 of it in the visible)."""

    def __init__(self, T0: float = 200.0, T1: float = 1.0e7, n: int = 1200):
        self.T0, self.T1 = float(T0), float(T1)
        self.lnT = np.linspace(math.log(T0), math.log(T1), n)
        X = blackbody_xyz(np.exp(self.lnT))
        self.lnX = np.log(np.maximum(X, 1e-300))
        self.spline = CubicSpline(self.lnT, self.lnX, axis=0)
        self.top = X[-1]

    def __call__(self, T):
        T = np.asarray(T, float)
        lt = np.log(np.clip(T, self.T0, self.T1))
        out = np.exp(self.spline(lt))
        out = np.where((T >= self.T0)[..., None], out, 0.0)
        hot = (T > self.T1)[..., None]
        return np.where(hot, self.top * (np.maximum(T, self.T1) / self.T1)[..., None], out)


def srgb_encode(lin):
    """Linear sRGB (0..1) to encoded values (0..1)."""
    x = np.clip(np.asarray(lin, float), 0.0, 1.0)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1.0 / 2.4) - 0.055)


def to_display(XYZ, exposure: float = 1.0):
    """XYZ (any scale) -> sRGB uint8 for a screen: scaled by ``exposure``, luminance compressed as L / (1 + L) with
    the chromaticity kept, colours outside the gamut brought in by scaling (negative components clipped)."""
    XYZ = np.asarray(XYZ, float) * exposure
    Y = XYZ[..., 1:2]
    k = np.where(Y > 0, 1.0 / (1.0 + Y), 1.0)
    rgb = XYZ @ XYZ_TO_SRGB.T * k
    rgb = np.maximum(rgb, 0.0)
    m = rgb.max(axis=-1, keepdims=True)
    rgb = rgb / np.maximum(m, 1.0)
    return np.round(255.0 * srgb_encode(rgb)).astype(np.uint8)
