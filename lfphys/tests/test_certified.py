# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The core's float64 results against rigorous Arb enclosures (lfphys.core.certified), by independent routes."""

import math

import numpy as np
import pytest

flint = pytest.importorskip("flint")

from lfphys.core import certified as A  # noqa: E402
from lfphys.core.constants import C, GM_SUN  # noqa: E402
from lfphys.core.gravity import kerr, orbits  # noqa: E402
from lfphys.core.gravity import schwarzschild as S  # noqa: E402
from lfphys.core.optics import scalar  # noqa: E402
from lfphys.core.quantum import compton, hydrogen, transfer  # noqa: E402
from lfphys.theories.approx import paraxial  # noqa: E402


@pytest.mark.parametrize("ra,rp", [(30.0, 12.0), (60.0, 9.0), (1e3, 200.0)])
def test_periapsis_advance_strong_field(ra, rp):
    m, r = A.mid_rad(A.periapsis_advance(1 / ra, 1 / rp))
    assert r < 1e-60
    assert orbits.advance_from_turning(1 / ra, 1 / rp) == pytest.approx(m, rel=1e-12)


def test_periapsis_advance_of_mercury_and_its_float_cancellation():
    """Weak field: 4K/sqrt(.) - 2 pi cancels ~7 digits in float64; Arb gives the certified value."""
    from lfphys.core import data
    M = GM_SUN / C**2
    a, e = data.MERCURY["a_m"], data.MERCURY["ecc"]
    u1, u2 = M / (a * (1 + e)), M / (a * (1 - e))
    m, r = A.mid_rad(A.periapsis_advance(u1, u2))
    assert orbits.advance_from_turning(u1, u2) == pytest.approx(m, rel=1e-8)
    arcsec = m * 36525.0 / data.MERCURY["period_days"] * 180 / math.pi * 3600
    assert arcsec == pytest.approx(42.98, abs=0.02) and r < 1e-50


@pytest.mark.parametrize("b_over_rs", [2.7, 4.0, 50.0, 1e5])
def test_light_deflection_against_the_rigorous_integral(b_over_rs):
    rs = 1.0
    b = b_over_rs * rs
    m, r = A.mid_rad(A.schwarzschild_deflection(b, rs))
    assert r < 1e-20
    assert S.deflection_from_quadrature(b, rs, 1.0) == pytest.approx(m, rel=1e-9)


@pytest.mark.parametrize("chi", [0.1, 0.5, 0.9, 0.998])
@pytest.mark.parametrize("pro", [True, False])
def test_kerr_isco_closed_form_satisfies_the_radial_conditions(chi, pro):
    r, R0, R1, R2 = A.kerr_isco_residuals(chi, pro)
    for b in (R0, R1, R2):
        m, rad = A.mid_rad(b)
        assert abs(m) + rad < 1e-50  # the conditions R = R' = R'' = 0 hold to the precision of the ball
    assert kerr.isco(chi, pro) == pytest.approx(A.mid_rad(r)[0], rel=1e-13)


@pytest.mark.parametrize("x", [50.0, 9.999e3, 1.0001e4, 3e5, 1e8])
def test_hankel_functions_both_branches(x):
    for nu in (0, 1):
        ref = A.hankel1(nu, x)
        val = complex(scalar.hankel1(nu, np.array([x]))[0])
        refc = complex(float(ref.real.mid()), float(ref.imag.mid()))
        assert abs(val - refc) <= 1e-10 * abs(refc)


@pytest.mark.parametrize("args", [
    dict(x=3e-4, z=0.5, k=2 * math.pi / 633e-9, e1=-60e-6, e2=-40e-6),
    dict(x=-1e-3, z=1.0, k=2 * math.pi / 500e-9, e1=10e-6, e2=30e-6, L1=0.4, src=2e-5, kappa=3e4),
    dict(x=0.0, z=2e-4, k=2 * math.pi / 633e-9, e1=-10e-6, e2=10e-6),  # near field (Fresnel number ~0.8)
])
def test_paraxial_closed_form_against_the_defining_integral(args):
    ref = A.slit_amplitude(**args)
    refc = complex(float(ref.real.mid()), float(ref.imag.mid()))
    a = dict(args)
    x, z, k = a.pop("x"), a.pop("z"), a.pop("k")
    e1, e2 = a.pop("e1"), a.pop("e2")
    c = 0.5 * (e1 + e2)
    val = complex(paraxial.slit_amplitudes(np.array([x]), z, k, [c], e2 - e1, **a)[0, 0])
    assert abs(val - refc) <= 1e-9 * abs(e2 - e1)


def test_dirac_levels():
    for n, j in ((1, 0.5), (2, 0.5), (2, 1.5), (3, 2.5)):
        m, r = A.mid_rad(A.dirac_level(n, j, hydrogen.ALPHA, hydrogen.ME_C2))
        assert hydrogen.dirac_level(n, j, M=math.inf) == pytest.approx(m, rel=1e-11)


@pytest.mark.parametrize("ratio", [1e-5, 0.01, 1.0, 30.0])
def test_klein_nishina_total_two_rigorous_routes(ratio):
    E = ratio * compton.ME_C2
    closed, integ = A.klein_nishina_total(E, compton.ME_C2, compton.R_E)
    mc, rc = A.mid_rad(closed)
    mi, ri = A.mid_rad(integ)
    assert abs(mc - mi) <= rc + ri + 1e-25 * mc
    assert compton.total_cross_section(E) == pytest.approx(mc, rel=1e-11)


@pytest.mark.parametrize("E,a", [(0.5, 1.0), (0.5, 5.0), (0.3, 12.0), (2.0, 3.0)])
def test_transfer_matrix_transmission_against_the_closed_form(E, a):
    m, r = A.mid_rad(A.rectangular_barrier(E, 1.0, a))
    T, R, *_ = transfer.transmission(E, [0.0, a], [0.0, 1.0, 0.0])
    assert T == pytest.approx(m, rel=1e-9)
