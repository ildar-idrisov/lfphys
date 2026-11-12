# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""lfphys.tools.colour (a display tool): the colour matching functions of Wyman, Sloan & Shirley (2013) against values
taken from the CIE 1931 standard (grepped 2026-10-28 from the Wikipedia texts citing the CIE): illuminant A, a black
body at 2856 K in modern units, has (x, y) = (0.44758, 0.40745); the equal-energy illuminant E has (1/3, 1/3) by the
normalisation of the CIE functions; the D65 white (X, Y, Z) = (0.9505, 1.0000, 1.0890) is sRGB (1, 1, 1). The
tolerances are the fit's own error bound (the paper's Table 2: maximum absolute errors 0.0142, 0.0080, 0.0222 per nm),
propagated to the chromaticity."""

import math

import numpy as np
import pytest
from scipy import constants as sc

from lfphys.core.optics import radiation
from lfphys.tools import colour as CO


def chroma_bound(power):
    """Largest change of (x, y) that CMF errors within the fit's bounds can cause, for a spectrum on LAMBDA_NM."""
    lam = CO.LAMBDA_NM
    X = CO.spectrum_xyz(lam, power)
    S = X.sum()
    tot = np.trapezoid(np.abs(power), lam)
    dX = np.array([CO.CMF_MAX_ABS_ERROR[k] * tot for k in "xyz"])
    x, y = X[0] / S, X[1] / S
    return (dX[0] + x * dX.sum()) / S, (dX[1] + y * dX.sum()) / S


def test_illuminant_a_chromaticity():
    """Illuminant A: a Planckian radiator at 2848 K with c2 = 1.435e-2 m K, i.e. 2848 * c2_now / 1.435e-2 K now."""
    c2 = sc.h * sc.c / sc.k
    T = 2848.0 * c2 / 1.435e-2
    B = radiation.planck_lambda(CO.LAMBDA_NM * 1e-9, T)
    x, y = CO.chromaticity(CO.spectrum_xyz(CO.LAMBDA_NM, B))
    bx, by = chroma_bound(B)
    assert abs(x - 0.44758) <= bx and abs(y - 0.40745) <= by
    assert abs(x - 0.44758) < 2e-3 and abs(y - 0.40745) < 2e-3  # measured: the fit is far inside its bound


def test_equal_energy_white_is_at_one_third():
    flat = np.ones_like(CO.LAMBDA_NM)
    x, y = CO.chromaticity(CO.spectrum_xyz(CO.LAMBDA_NM, flat))
    bx, by = chroma_bound(flat)
    assert abs(x - 1 / 3) <= bx and abs(y - 1 / 3) <= by


def test_d65_white_is_srgb_white():
    rgb = CO.XYZ_TO_SRGB @ np.array([0.9505, 1.0, 1.0890])
    assert np.allclose(rgb, 1.0, atol=1e-3)
    assert CO.srgb_encode(np.array([0.0, 0.0031308, 1.0])).tolist() == pytest.approx([0.0, 0.0031308 * 12.92, 1.0])


def test_blackbody_table_interpolates_direct_integration():
    """The log-T table (cubic splines in log X) against direct integration at the midpoints between its nodes:
    relative error < 1e-6 where the colour is visible (T >= 500 K; linear interpolation was 4e-4 there); below T0 a
    body is black; above T1 the Rayleigh-Jeans tail."""
    tab = CO.BlackbodyXYZ()
    mid = np.exp(0.5 * (tab.lnT[1:] + tab.lnT[:-1]))
    mid = mid[mid >= 500.0][::7]
    direct = CO.blackbody_xyz(mid)
    assert np.max(np.abs(tab(mid) / direct - 1)) < 1e-6
    assert np.all(tab(np.array([50.0, 199.0])) == 0.0)
    Y = CO.blackbody_xyz(np.array([200.0, 5800.0]))[:, 1]
    assert Y[0] / Y[1] < 1e-44  # what the table's floor leaves out is invisible next to anything else (1.3e-45)
    hot = tab(np.array([2e7, 4e7]))
    assert np.allclose(hot[1] / hot[0], 2.0)
    assert np.all(np.diff(tab(np.geomspace(600, 1e6, 50))[:, 1]) > 0)  # brighter when hotter


def test_hot_bodies_are_bluer_than_cool_ones():
    xy = CO.chromaticity(CO.BlackbodyXYZ()(np.array([2000.0, 6500.0, 30000.0])))
    assert xy[0, 0] > xy[1, 0] > xy[2, 0]  # x falls along the Planckian locus as T rises
    tab = CO.BlackbodyXYZ()
    rgb = CO.to_display(tab(np.array([2000.0, 30000.0])), exposure=1.0 / tab(np.array([6500.0]))[0, 1])
    assert rgb[0, 0] > rgb[0, 2] and rgb[1, 2] > rgb[1, 0]


def test_display_mapping_keeps_the_gamut_and_the_order():
    XYZ = np.array([[0.0, 0.0, 0.0], [0.9505, 1.0, 1.0890], [9.505, 10.0, 10.89], [9.505e5, 1e6, 1.089e6]])
    rgb = CO.to_display(XYZ)
    assert rgb.dtype == np.uint8 and rgb[0].tolist() == [0, 0, 0]
    assert rgb[1, 1] < rgb[2, 1] <= rgb[3, 1] <= 255
    assert math.isclose(float(rgb[2, 0]), float(rgb[2, 2]), abs_tol=3)
