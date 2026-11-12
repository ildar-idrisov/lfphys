# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The laws of a 2-D flow changed at the current moment (review 2026-11-04 UX-ui U12) and the playground's limits
(UX-ui U7, UX-params P25): the density (a flow given its new density half-way equals one that had it from the start,
populations and pressures bit for bit), the collision operator (the switched flow equals one restored from the same
state with the other operator), the dye switched off and on (its balance closes across), the body force the rest state
carries (``gravity_limit`` against ``set_gravity``'s own refusal, with a control on each side), the memory estimate
against the state's own footprint."""

import math

import numpy as np
import pytest

from lfphys.core import backend
from lfphys.core.fluids import lbm


@pytest.fixture(autouse=True)
def _cpu():
    backend.configure(None)
    yield
    backend.configure(None)


def _channel(rho=1.0, collision="trt", dye=1e-3):
    fl = lbm.Flow2D(size=(0.4, 0.1), dx=0.005, nu=1e-3, rho=rho, u_max=0.3, collision=collision, dye=dye,
                    device="cpu", sides={"left": lbm.Inlet(velocity=0.1, profile="parabolic"), "right": lbm.Outlet()})
    fl.add_obstacle(lbm.Disk((0.12, 0.05), 0.015), label="d")
    return fl


def test_density_change_equals_a_flow_that_had_it_from_the_start():
    """The lattice does not depend on rho (incompressible scheme): 200 steps at rho = 1, then rho = 1000 and 100 more,
    equal 300 steps at rho = 1000 bit for bit in the populations; pressures and forces then carry the new scale, the
    velocities are the same; the balances' relative residuals are untouched by the change."""
    a, b = _channel(rho=1.0), _channel(rho=1000.0)
    a.advance(200)
    r0 = a.balance()["mass"]["relative_residual"]
    a.set_density(1000.0)
    assert a.balance()["mass"]["relative_residual"] == r0
    a.advance(100)
    b.advance(300)
    assert np.array_equal(a.populations(), b.populations())
    fa, fb = a.fields(), b.fields()
    for k in ("p", "ux", "uy", "rho"):
        assert np.array_equal(fa[k], fb[k], equal_nan=True)
    Fa, Fb = a.forces(), b.forces()
    assert Fa[0]["force"] == pytest.approx(Fb[0]["force"], rel=1e-12)
    # negative control: the pressure of the flow that kept rho = 1 is a thousand times smaller
    c = _channel(rho=1.0)
    c.advance(300)
    assert np.nanmax(np.abs(c.fields()["p"])) == pytest.approx(np.nanmax(np.abs(fa["p"])) / 1000.0, rel=1e-9)
    with pytest.raises(ValueError):
        a.set_density(0.0)


def test_collision_switch_equals_a_restored_flow_with_the_other_operator():
    """TRT -> BGK after 150 steps: the populations are kept; 100 more steps equal a flow restored from the same state
    with collision = "bgk" (the engine's own restore path) bit for bit; tau- becomes tau+; the negative control (the
    flow that stayed TRT) differs."""
    a = _channel()
    a.advance(150)
    d = a.state_dict()
    f0 = a.populations()
    a.set_collision("bgk")
    assert np.array_equal(a.populations(), f0) and a.tau_m == a.tau_p
    d["collision"] = "bgk"
    b = lbm.Flow2D.from_state_dict(d, device="cpu")
    a.advance(100)
    b.advance(100)
    assert np.array_equal(a.populations(), b.populations())
    c = _channel()
    c.advance(250)
    assert not np.array_equal(c.populations(), a.populations())
    with pytest.raises(ValueError):
        a.set_collision("mrt")


def test_dye_switched_off_and_on_keeps_its_balance():
    """Dye injected, the flow run, the dye switched off (its amount booked as removed), on again (zero), injected
    again: the dye balance closes to round-off throughout; switching off is refused while a dye source exists."""
    fl = _channel()
    fl.add_dye(lbm.Disk((0.05, 0.05), 0.01), concentration=1.0)
    fl.advance(100)
    fl.disable_dye()
    assert fl.dye_D is None and "dye" not in fl.balance()
    fl.advance(50)
    fl.enable_dye(1e-3)
    fl.add_dye(lbm.Disk((0.05, 0.05), 0.01), concentration=0.5)
    fl.advance(100)
    b = fl.balance()["dye"]
    assert abs(b["relative_residual"]) < 1e-12
    sid = fl.add_dye_source(lbm.Disk((0.3, 0.05), 0.005))
    with pytest.raises(ValueError):
        fl.disable_dye()
    fl.remove_dye_source(sid)
    fl.disable_dye()


def test_gravity_limit_is_the_refusals_edge():
    """``gravity_limit`` is where ``set_gravity`` starts refusing: 0.999 of it accepted, 1.001 refused (the state then
    unchanged); a closed box at Ma 0.1 of u_max = 0.45 m/s carries g of a few m/s² over 0.41 m, not 9.81."""
    fl = lbm.Flow2D(size=(2.2, 0.41), dx=0.005, nu=1e-3, rho=1.0, u_max=0.45, device="cpu", dye=None)
    lim = fl.gravity_limit((0.0, -1.0))
    assert 1.0 < lim < 9.81
    f0 = fl.populations()
    with pytest.raises(ValueError):
        fl.set_gravity((0.0, -1.001 * lim))
    assert np.array_equal(fl.populations(), f0) and fl.gravity == (0.0, 0.0)
    fl.set_gravity((0.0, -0.999 * lim))
    # the limit scales with c_s^2, i.e. with u_max^2
    fl2 = lbm.Flow2D(size=(2.2, 0.41), dx=0.005, nu=1e-3, rho=1.0, u_max=0.9, device="cpu", dye=None)
    assert fl2.gravity_limit((0.0, -1.0)) == pytest.approx(4.0 * lim, rel=1e-6)
    # along a periodic axis the force drives the flow: no hydrostatic limit
    per = lbm.Flow2D(size=(1.0, 0.2), dx=0.01, nu=1e-3, rho=1.0, u_max=0.45, device="cpu", dye=None,
                     sides={"left": "periodic", "right": "periodic"})
    assert math.isinf(per.gravity_limit((1.0, 0.0)))


def test_memory_estimate_covers_the_state():
    fl = _channel()
    assert lbm.Flow2D.memory_estimate(fl.nx, fl.ny, True) > fl._footprint()
    assert lbm.Flow2D.memory_estimate(1000, 1000, False) == 800_000_000


def test_shape_mask_and_solid_are_the_engines():
    fl = _channel()
    m = fl.shape_mask(lbm.Disk((0.12, 0.05), 0.015))
    assert np.array_equal(m, fl.solid())
    assert m.sum() == pytest.approx(math.pi * 0.015 ** 2 / 0.005 ** 2, rel=0.15)
