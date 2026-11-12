# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Water's refractive index (IAPWS R9-97) and density at 0.1 MPa (IAPWS SR6-08) in lfphys.core.data against the
releases' own values for program verification, and the size average of the Mie series (lfphys.core.optics.mie_poly)
against closed forms."""

import math

import numpy as np
import pytest
from scipy import special

from lfphys.core import data as D
from lfphys.core.optics import mie, mie_poly


def test_water_density_against_sr6_table_8():
    """SR6-08 Table 8 prints 9 significant digits; the formulation reproduces them within half a unit."""
    for T, rho in D.IAPWS08_RHO_CHECK:
        assert abs(float(D.water_density_01mpa(T)) - rho) <= 0.5e-6
    with pytest.raises(ValueError):
        D.water_density_01mpa(400.0)


def test_water_index_against_r9_table_3():
    """R9-97 Table 3 (0.1 MPa, 0 C) with the density of SR6-08 (uncertainty 1e-6 relative, as the release requires
    "to one part in 10^6"): within one unit of the last printed digit (1e-6), as the release promises (measured
    within 0.4 units). Negative control: the density of 1000 kg/m^3 instead misses by more."""
    rho = float(D.water_density_01mpa(273.15))
    for lam, n in D.IAPWS97_RINDEX_CHECK_0C_01MPA:
        assert abs(float(D.water_refractive_index(lam, 273.15, rho)) - n) <= 1.0e-6
        assert abs(float(D.water_refractive_index(lam, 273.15, 1000.0)) - n) > 1.0e-6
    assert abs(float(D.water_index(589.0, 0.0)) - 1.334344) <= 1e-6
    # dispersion: n falls with wavelength across the visible; warm water has a lower index
    lam = np.linspace(380, 780, 41)
    n = D.water_index(lam, 20.0)
    assert np.all(np.diff(n) < 0) and 1.328 < n[-1] < n[0] < 1.347  # 1.3290 at 780 nm, 1.3456 at 380 nm
    assert float(D.water_index(550.0, 40.0)) < float(D.water_index(550.0, 0.0))
    with pytest.raises(ValueError):
        D.water_refractive_index(1.5, 293.15, 998.0)


def test_sun_nominal_temperature():
    assert D.SUN_TEFF_NOMINAL_K == 5772.0


# --- the size average ------------------------------------------------------------------------------------------------
def test_monodisperse_average_is_the_single_sphere():
    th = np.radians(np.linspace(100, 180, 81))
    nodes = mie_poly.size_nodes(5.0, 0.0, 0.55)
    av = mie_poly.average(1.333, 0.55, nodes, th)
    x = 2 * math.pi * 5.0 / 0.55
    r = mie.scattering(1.333, x, th)
    k = 2 * math.pi / 0.55
    assert np.allclose(av["dsdo"], r["S11"] / k ** 2, rtol=1e-12)
    assert np.allclose(av["dsdo_pol"], r["S12"] / k ** 2, rtol=1e-12, atol=1e-14 * av["dsdo"].max())
    assert av["C_sca"] == pytest.approx(r["Qsca"] * math.pi * 25.0, rel=1e-13)


def test_rayleigh_cloud_against_gamma_moments():
    """Small drops: C_sca = (8 pi/3) k^4 |K|^2 r^6 (1 + O(x^2)), so <C_sca> = (8 pi/3) k^4 |K|^2 <r^6> with the gamma
    moment <r^6> = theta^6 Gamma(k + 6)/Gamma(k): within the O(x^2) correction (the cut at 8 sigma removes < 1e-12);
    and the half-sum error estimate is tiny for this smooth integrand. Negative control: <r>^6 instead of <r^6>."""
    m, lam, rm, w = 1.333, 0.55, 0.002, 0.3
    nodes = mie_poly.size_nodes(rm, w, lam, n_sigma=8.0, dx_max=1e-5)
    av = mie_poly.average(m, lam, nodes, np.array([math.pi / 2]))
    k = 2 * math.pi / lam
    K = (m * m - 1) / (m * m + 2)
    sh, sc = 1 / w ** 2, rm * w ** 2
    r6 = sc ** 6 * math.exp(special.gammaln(sh + 6) - special.gammaln(sh))
    ref = 8 * math.pi / 3 * k ** 4 * abs(K) ** 2 * r6
    xmax = k * rm * (1 + 8 * w)
    assert abs(av["C_sca"] / ref - 1) <= 3 * xmax ** 2 + 1e-9
    assert abs(8 * math.pi / 3 * k ** 4 * abs(K) ** 2 * rm ** 6 / ref - 1) > 3 * xmax ** 2 + 1e-9
    assert av["err_C_sca"] <= 1e-6 * av["C_sca"]


def test_cloud_phase_function_integrates_to_the_mean_cross_section():
    """int <dsigma/dOmega> dOmega = <C_sca>: Gauss-Legendre in cos(theta) on the averaged intensities."""
    lam, rm, w = 0.55, 2.0, 0.1
    nodes = mie_poly.size_nodes(rm, w, lam)
    N = mie.n_terms(float(nodes["x"].max()))
    mu, wq = np.polynomial.legendre.leggauss(2 * N + 20)
    av = mie_poly.average(1.333, lam, nodes, np.arccos(mu))
    tot = 2 * math.pi * (wq @ av["dsdo"])
    assert abs(tot / av["C_sca"] - 1) <= 1e-10
    assert av["n_nodes"] >= 9 and av["dx"] <= 0.25


def test_size_average_converges_with_the_node_spacing():
    """Near the rainbow of 100 um drops (x ~ 1140) with a 5 % width: the average with dx_max = 0.25 against 0.1. The
    half-sum estimate "err" is an order-of-magnitude estimate of the LARGEST error over the angles, not a per-angle
    error (review B8-mie, M7: per angle it is exceeded at 35-51 % of the angles): the largest difference stays within
    5 times the largest estimate. Negative control: the coarse dx = 4 (which aliases the ripple) is farther off."""
    th = np.radians(np.linspace(136, 146, 101))
    out = {}
    for dx in (0.25, 0.1, 4.0):
        nodes = mie_poly.size_nodes(100.0, 0.05, 0.55, dx_max=dx)
        out[dx] = mie_poly.average(1.333, 0.55, nodes, th)
    ref = out[0.1]["dsdo"]
    d = np.abs(out[0.25]["dsdo"] - ref)
    assert d.max() <= 5 * (out[0.25]["err"].max() + out[0.1]["err"].max())
    assert np.max(np.abs(out[4.0]["dsdo"] - ref)) > d.max()


def test_the_cut_of_the_size_distribution():
    """The +-n_sigma cut (default 4, review B8-mie M7): "tail" is the gamma mass outside the cut (against a direct
    quadrature of the pdf), and the cut's bias on <dsigma/dOmega> against a 9-sigma cut on the same fine grid stays
    below 3 tail of the peak for 8 um +- 10 % (the glory preset: measured 2.1e-4 against tail 1.6e-4). Negative
    control: the former 3-sigma cut, unstated, was biased by 2.6e-3 of the peak — beyond the 4-sigma bound."""
    from scipy import integrate
    r, w, lam = 8.0, 0.10, 0.55
    th = np.radians(np.linspace(125.0, 180.0, 221))
    nd9 = mie_poly.size_nodes(r, w, lam, dx_max=0.01, n_sigma=9.0, max_nodes=10 ** 6)
    full = mie_poly.average(1.3354, lam, nd9, th)
    top = full["dsdo"].max()
    nd4 = mie_poly.size_nodes(r, w, lam)
    assert nd4["n_sigma"] == 4.0
    lo, hi = r * (1 - 4 * w), r * (1 + 4 * w)
    inside = integrate.quad(lambda v: float(mie_poly.gamma_pdf(v, r, w)), lo, hi, epsabs=0, epsrel=1e-12)[0]
    assert abs(nd4["tail"] - (1 - inside)) <= 1e-10
    bias = {}
    for ns in (3.0, 4.0):
        keep = (nd9["r"] >= r * (1 - ns * w)) & (nd9["r"] <= r * (1 + ns * w))
        nd = dict(nd9)
        ww = np.where(keep, nd9["w"], 0.0)
        nd["w"] = ww / ww.sum()
        bias[ns] = np.abs(mie_poly.average(1.3354, lam, nd, th)["dsdo"] - full["dsdo"]).max() / top
    assert bias[4.0] <= 3 * nd4["tail"]
    assert bias[3.0] > 3 * nd4["tail"]
    av = mie_poly.average(1.3354, lam, nd4, th)
    assert av["tail"] == nd4["tail"]
