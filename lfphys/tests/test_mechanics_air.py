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
