# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The air (and water) data used by the drag laws: ``lfphys.core.data.fluid_properties`` (moved there from
``core.fluids.lbm`` on 2026-11-14, design explore_2026-11-14 §4; ``lbm`` re-exports it unchanged), against the
U.S. Standard Atmosphere 1976's own tables and an independent modern reference."""

import math

import pytest

from lfphys.core import data
from lfphys.core.fluids import lbm
from lfphys.core.mechanics import air


def test_lbm_re_exports_the_same_objects():
    for name in ("fluid_properties", "FLUIDS", "WATER_1ATM", "WATER_SOURCE", "AIR_SOURCE", "P_ATM", "AIR_M0",
                 "AIR_RSTAR", "AIR_BETA", "AIR_S"):
        assert getattr(lbm, name) is getattr(data, name)
    assert lbm.fluid_properties("air", 20.0) == data.fluid_properties("air", 20.0)


def test_air_against_the_standard_atmosphere_tables():
    """USSA 1976: table I (p. 52) at sea level, 288.150 K, 1.01325e3 mb: 1.2250 kg/m^3; table III (p. 100): the
    dynamic viscosity 1.7894e-5 N s/m^2 (the formula with S = 110.4 K; with the 110 K of table 2B it would be
    1.7912e-5, outside the printed digits)."""
    a = data.fluid_properties("air", 15.0)
    assert round(a["rho"], 4) == 1.2250
    assert round(a["mu"] * 1e5, 4) == 1.7894
    TK = 288.15
    assert round(data.AIR_BETA * TK ** 1.5 / (TK + 110.0) * 1e5, 4) != 1.7894


def test_air_against_lemmon_2000_and_lemmon_jacobsen_2004():
    """Independent: Lemmon, Jacobsen, Penoncello & Friend, J. Phys. Chem. Ref. Data 29, 331 (2000), table A2 (the
    0.101325 MPa isobar): 290 K 0.042040 mol/dm^3, 300 K 0.040634 mol/dm^3, M = 28.9586 g/mol; the formula is 1.9e-4
    and 8e-5 below (the standard's M0 is 2e-4 above the modern molar mass). Lemmon & Jacobsen, Int. J. Thermophys. 25,
    21 (2004), table V: the dilute-gas viscosity at 300 K, 18.5230 uPa s (uncertainty 1 %); the formula is 0.34 %
    below."""
    for T_K, mol in ((290.0, 0.042040), (300.0, 0.040634)):
        rho = data.fluid_properties("air", T_K - 273.15)["rho"]
        assert rho == pytest.approx(mol * 28.9586, rel=2.5e-4)
    mu = data.fluid_properties("air", 300.0 - 273.15)["mu"]
    assert mu == pytest.approx(18.5230e-6, rel=0.004)


def test_air_at_20_C_used_by_the_drag_laws():
    a = air()
    assert a == data.fluid_properties("air", 20.0, data.P_ATM)
    assert a["rho"] == pytest.approx(101325.0 * 28.9644 / (8314.32 * 293.15), rel=1e-15)
    assert a["rho"] == pytest.approx(1.2041, abs=5e-5)
    assert a["mu"] == pytest.approx(1.458e-6 * 293.15 ** 1.5 / (293.15 + 110.4), rel=1e-15)
    assert a["mu"] == pytest.approx(1.8134e-5, rel=5e-5)
    assert math.isclose(a["nu"], a["mu"] / a["rho"], rel_tol=1e-15)
    with pytest.raises(ValueError):
        air(150.0)
    with pytest.raises(ValueError):
        air(20.0, -1.0)


# --- a body in the air: buoyancy and added mass (design explore_EX2_2026-11-18 §7 «E03», §11 item 40) --------------
import numpy as np  # noqa: E402

from lfphys.core.mechanics import G_STANDARD, Body, Medium, fly, vacuum_state  # noqa: E402

G = G_STANDARD


def test_medium_air_is_the_data_s_air():
    m = Medium.air()
    a = air()
    assert (m.rho, m.mu, m.added_mass) == (a["rho"], a["mu"], 0.5)
    assert Medium.air(15.0).rho == pytest.approx(1.2250, abs=5e-5)
    with pytest.raises(ValueError):
        Medium(-1.0)
    with pytest.raises(ValueError):
        Medium(1.0, added_mass=-0.1)
    with pytest.raises(ValueError):
        Body(1.0, 0.1, volume=-1.0)
    assert Body(1.0, 0.1).displaced_volume == pytest.approx(math.pi * 1e-3 / 6, rel=1e-15)
    assert Body(1.0, 0.1, volume=2e-3).displaced_volume == 2e-3


@pytest.mark.parametrize("rho_f,ca,rho_b", [(1.2041, 0.5, 7850.0), (1.2041, 0.5, 377.0), (998.2, 0.5, 2700.0),
                                            (998.2, 1.0, 1200.0), (998.2, 0.0, 7850.0)])
@pytest.mark.parametrize("h,v,th", [(1.0, 1.5, 0.0), (0.0, 5.0, 45.0), (2.0, 3.0, -30.0)])
def test_buoyancy_and_added_mass_are_vacuum_with_g_and_the_inertia_rescaled(rho_f, ca, rho_b, h, v, th):
    """Without drag the body in a fluid at rest flies the vacuum path with g' = g (m - m_f) / (m + C_A m_f) (exact):
    the trajectory against vacuum_state with g', the work of the buoyancy m_f g (y - y0) and of the added mass
    -C_A m_f (v^2 - v0^2) / 2, and the energy balance (measured 1e-15–1e-13). Steel, the light ball (377 kg/m^3) in
    air; aluminium, a plastic and steel in water."""
    d = 0.02
    V = math.pi * d ** 3 / 6
    body = Body(rho_b * V, d)
    mf = rho_f * V
    gp = G * (body.mass - mf) / (body.mass + ca * mf)
    v0 = [v * math.cos(math.radians(th)), v * math.sin(math.radians(th))]
    f = fly(body, [0.0, h], v0, medium=Medium(rho_f, ca, 1e-3))
    s = f.sample(rate=240.0)
    r, vv = vacuum_state(s["t"], [0.0, h], v0, gp)
    scale = max(h, v * v / G)
    assert np.max(np.abs(s["r"] - r)) < 1e-9 * scale
    assert np.max(np.abs(s["v"] - vv)) < 1e-9 * max(v, math.sqrt(2 * G * h))
    Wb = mf * G * (s["r"][:, 1] - h)
    Wa = -0.5 * ca * mf * (np.einsum("ij,ij->i", s["v"], s["v"]) - v * v)
    Escale = 0.5 * body.mass * v * v + body.mass * G * h
    assert np.max(np.abs(s["W_i"][:, 0] - Wb)) < 1e-9 * Escale
    assert np.max(np.abs(s["W_i"][:, 1] - Wa)) < 1e-9 * Escale
    assert f.energy_balance() < 1e-9
    assert f.inertia == pytest.approx(body.mass + ca * mf, rel=1e-15)
    fl = f.fluid_forces(0.5 * f.t_end)
    assert fl["buoyancy"] == pytest.approx([0.0, mf * G], rel=1e-15)
    assert fl["added_mass"] == pytest.approx([0.0, ca * mf * gp], rel=1e-9)


def test_a_medium_without_density_changes_nothing_and_no_medium_is_the_old_flight():
    """rho_f = 0: the same flight as without a medium (to round-off: the two extra work columns change the step
    control's norm)."""
    b = Body(0.0329, 0.02)
    f0 = fly(b, [0.0, 1.0], [1.5, 0.0])
    f1 = fly(b, [0.0, 1.0], [1.5, 0.0], medium=Medium(0.0))
    assert f1.range == pytest.approx(f0.range, rel=1e-13) and f1.flight_time == pytest.approx(f0.flight_time, rel=1e-13)
    assert f0.inertia == b.mass and f0.medium is None


def test_s03_s_balls_in_air_buoyancy_and_added_mass_lengthen_the_ranges():
    """Design A.8 (with the measured drag curve): +0.035–0.078 mm on the chute (h 0.2–1 m), +0.29–0.58 mm on the
    launcher (5 m/s, 15–75°): the engine's flights reproduce the measured +0.0778 mm at h = 1 m and +0.582 mm at 45°.
    C_A = 1/2 is checked only up to Re 300 (Magnaudet et al. 1995); a change of C_A by 0.5 moves the chute's range
    (1 m) by 0.026 mm, the launcher's (45°) by 0.195 mm and the light ball's (20 m/s, 45°) by 46 mm (0.16 %): the
    stated uncertainty of the added mass at S03's Reynolds numbers."""
    from lfphys.theories.models import drag_quadratic as dq
    steel = Body(0.0329, 0.020)
    cd = dq.CurveDrag.sphere(0.020)
    a = Medium.air()
    base = fly(steel, [0.0, 1.0], [1.5, 0.0], forces=[cd])
    med = fly(steel, [0.0, 1.0], [1.5, 0.0], forces=[cd], medium=a)
    assert (med.range - base.range) * 1e3 == pytest.approx(0.0778, abs=2e-4)
    v0 = [5.0 * math.cos(math.radians(45)), 5.0 * math.sin(math.radians(45))]
    base2 = fly(steel, [0.0, 0.0], v0, forces=[cd])
    med2 = fly(steel, [0.0, 0.0], v0, forces=[cd], medium=a)
    assert (med2.range - base2.range) * 1e3 == pytest.approx(0.5819, abs=2e-4)
    for ca in (0.0, 1.0):
        alt = fly(steel, [0.0, 0.0], v0, forces=[cd], medium=Medium(a.rho, ca, a.mu))
        assert abs(alt.range - med2.range) * 1e3 == pytest.approx(0.1945, abs=2e-4)
