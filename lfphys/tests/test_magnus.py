# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""``lfphys.theories.models.magnus`` (design explore_EX2_2026-11-18 §7 «E03», §11 item 39): the model at its sources'
tabulated points (Zhou, Zhang & Xu 2022, Table 2; Muto, Tsubokura & Oshima 2012, Table I; both checked on their texts
2026-11-18, ``lfphys/sources/s03_forces_2026-11-18.md``), the stated band, the force's geometry in 2-D and 3-D, and
the flight of S03's rolling ball with its real forces."""

import math

import numpy as np
import pytest

from lfphys.core.mechanics import G_STANDARD, Body, Medium, fly
from lfphys.theories.models import drag_quadratic as dq
from lfphys.theories.models import magnus as mg

G = G_STANDARD
STEEL = Body(0.0329, 0.020, "steel 20 mm")


def _eq8(Rr, re):
    """Zhou et al. (2022) eq. (8), written out here as printed."""
    b = 0.365 / (1 + math.exp(2.229 - 6.5 * Rr))
    return b + (Rr - b) * math.exp(-0.075 * (0.5 * Rr) ** 0.4 * re ** 0.71)


def test_the_table_is_consistent_with_its_own_definitions():
    """Each run's Rr = D Omega / u and Re = u D / nu (water, nu = 1.0e-6 m^2/s) recomputed from its D, u and Omega
    reproduce the printed values to their digits (a check of the transcription)."""
    assert len(mg.ZHOU_2022_TABLE2) == 22
    for n, D, u, Om, Rr, re, cl, cd in mg.ZHOU_2022_TABLE2:
        assert D * 1e-3 * Om / u == pytest.approx(Rr, abs=6e-4), n
        assert u * D * 1e-3 / mg.ZHOU_NU == pytest.approx(re, abs=0.6), n
        assert 0.09 < cl < 0.46 and 0.5 < cd < 0.81


def test_the_model_is_the_published_correlation():
    """cl_zhou(S, Re) is eq. (8) with Rr = 2S; drag_factor is eq. (17) below Rr = 2.5 and eq. (18) above."""
    for S in (0.05, 0.2, 0.5, 1.0, 1.7, 5.0):
        for re in (50.0, 600.0, 2000.0, 3472.0, 1e4):
            assert float(mg.cl_zhou(S, re)) == pytest.approx(_eq8(2 * S, re), rel=1e-14)
    for S in (0.0, 0.3, 1.0, 1.24):
        Rr = 2 * S
        assert float(mg.drag_factor(S)) == pytest.approx(0.989 + 0.482 * Rr - 0.093 * Rr * Rr, rel=1e-15)
    for S in (1.26, 3.0, 6.0):
        assert float(mg.drag_factor(S)) == pytest.approx(2.117 * (2 * S) ** -0.33, rel=1e-15)


def test_the_drag_factor_s_jump_at_the_fits_meeting_point_is_stated():
    """Review EX2, R2-E F4: eqs. (17) and (18) do not meet at Rr = 2.5 (S = 1.25): 1.61275 against 1.5646 (-2.99 %),
    a discontinuity of the source's model, stated in the module docstring, the validity text and ``drag_factor``."""
    below = float(mg.drag_factor(np.nextafter(1.25, 0.0)))
    at = float(mg.drag_factor(1.25))
    assert below == pytest.approx(1.61275, abs=1e-5) and at == pytest.approx(2.117 * 2.5 ** -0.33, rel=1e-15)
    assert at / below - 1 == pytest.approx(-0.0299, abs=5e-5)
    v = mg.ABOUT["validity"]
    text = v.msgid if hasattr(v, "msgid") else str(v)
    assert "jumps by −3.0 % at S = 1.25" in text
    assert "1.6128" in mg.__doc__ and "1.5646" in mg.__doc__ and "-3.0 %" in mg.drag_factor.__doc__


def test_the_model_at_the_tabulated_points():
    """At the 22 measured runs eq. (8) is within its fit's scatter of the printed C_L (R^2 = 0.873): within 0.05 of
    every run with S >= 0.25 except run 19 (0.449 against 0.365; run 8 at S 1.74 is 0.047 below); eq. (17)/(18) times their eq. (16)
    within 18 % of the printed C_D. At Re 10^4 (Muto et al.): the model's 0.365 against the simulated 0.301 at S = 1,
    and its drag factor against the simulated drag over the standard curve, 1.684 / 1.581 and 1.207 / 1.167."""
    for n, D, u, Om, Rr, re, cl, cd in mg.ZHOU_2022_TABLE2:
        S = Rr / 2
        model = float(mg.cl_zhou(S, re))
        if S >= 0.25 and n != 19:
            assert abs(cl - model) < 0.05, n
        cd0 = 24 / re + 2.5 / math.sqrt(re) + 0.4
        assert cd / (float(mg.drag_factor(S)) * cd0) == pytest.approx(1.0, abs=0.18), n
    run19 = [r for r in mg.ZHOU_2022_TABLE2 if r[0] == 19][0]
    assert run19[6] / float(mg.cl_zhou(run19[4] / 2, run19[5])) == pytest.approx(1.2302, abs=1e-4)
    cd_curve = float(dq.cd_standard(1e4))
    assert cd_curve == pytest.approx(0.3926, abs=1e-4)
    (g1, cd1, cl1, _), (g2, cd2, cl2, _) = mg.MUTO_2012_RE1E4
    assert cl2 / float(mg.cl_zhou(g2, 1e4)) == pytest.approx(0.8247, abs=1e-4)
    assert cd2 / cd_curve == pytest.approx(1.684, abs=1e-3) and float(mg.drag_factor(g2)) == pytest.approx(1.581)
    assert cd1 / cd_curve == pytest.approx(1.207, abs=1e-3) and float(mg.drag_factor(g1)) == pytest.approx(1.16692)
    # Gamma read as 2S would give drag factors 1.093 and 1.378 against 1.207 and 1.684: farther from the simulation
    assert abs(float(mg.drag_factor(g1 / 2)) - cd1 / cd_curve) > abs(float(mg.drag_factor(g1)) - cd1 / cd_curve)
    assert abs(float(mg.drag_factor(g2 / 2)) - cd2 / cd_curve) > abs(float(mg.drag_factor(g2)) - cd2 / cd_curve)


def test_the_band_is_the_spread_of_the_checked_values_and_the_docs_state_it():
    """LIFT_BAND = (0.8247, 1.2302): Muto's 0.301 at Re 10^4 and Zhou's run 19; DRAG_BAND = (0.9173, 1.0841): Zhou's
    runs 9 and 19. The module's validity text states them as −17.5 % / +23 % and −8.3 % / +8.4 %."""
    assert mg.LIFT_BAND == pytest.approx((0.8247, 1.2302), abs=1e-4)
    assert mg.DRAG_BAND == pytest.approx((0.9173, 1.0841), abs=1e-4)
    pts = mg._band_points()
    assert sorted(p[0] for p in pts) == sorted(["Muto 2012 Gamma 1.0"] + [f"Zhou 2022 run {n}" for n in
                                                                          (7, 9, 10, 12, 13, 19, 20, 21, 22)])
    v = mg.ABOUT["validity"]
    text = v.msgid if hasattr(v, "msgid") else str(v)
    assert f"−{100 * (1 - mg.LIFT_BAND[0]):.1f} %" in text and f"+{100 * (mg.LIFT_BAND[1] - 1):.0f} %" in text
    assert f"−{100 * (1 - mg.DRAG_BAND[0]):.1f} %" in text and f"+{100 * (mg.DRAG_BAND[1] - 1):.1f} %" in text
    lo, c, hi = mg.cl_band(0.7, 3000.0)
    assert lo == pytest.approx(mg.LIFT_BAND[0] * c) and hi == pytest.approx(mg.LIFT_BAND[1] * c)


def test_the_force_s_geometry_in_2d_and_3d():
    """Topspin (omega_z > 0 for a motion along +x) pushes down; the lift is normal to v (no work); its size is
    (1/2) rho C_L A v^2; a 3-D flight in the plane with the spin along z gives the 2-D force; a spin along v gives
    nothing."""
    air = Medium.air()
    m = mg.Magnus(0.020, 150.0, air)
    v = np.array([3.0, -1.0])
    F = m.force(0.0, None, v)
    sp = float(np.linalg.norm(v))
    S = 0.01 * 150.0 / sp
    cl = float(mg.cl_zhou(S, air.rho * sp * 0.02 / air.mu))
    assert np.linalg.norm(F) == pytest.approx(0.5 * air.rho * cl * math.pi * 1e-4 * sp * sp, rel=1e-14)
    assert F @ v == pytest.approx(0.0, abs=1e-18)
    assert mg.Magnus(0.020, 150.0, air).force(0.0, None, [3.0, 0.0])[1] < 0       # topspin: down
    assert mg.Magnus(0.020, -150.0, air).force(0.0, None, [3.0, 0.0])[1] > 0      # backspin: up
    m3 = mg.Magnus(0.020, [0.0, 150.0, 0.0], air)
    F3 = m3.force(0.0, None, [3.0, 0.0, -1.0])
    assert F3[[0, 2]] == pytest.approx(F, rel=1e-14) and F3[1] == pytest.approx(0.0, abs=1e-20)
    assert np.all(mg.Magnus(0.020, [3.0, 0.0, -1.0], air).force(0.0, None, [3.0, 0.0, -1.0]) == 0.0)
    assert np.all(mg.Magnus(0.020, [0.3, 0.0, -0.1], air).force(0.0, None, [3.0, 0.0, -1.0]) == 0.0)
    assert m.spin_ratio(0.0, v) == pytest.approx(S, rel=1e-15)
    for e in ("low", "high"):
        assert np.linalg.norm(mg.Magnus(0.020, 150.0, air, edge=e).force(0.0, None, v)) == pytest.approx(
            np.linalg.norm(F) * (mg.LIFT_BAND[0] if e == "low" else mg.LIFT_BAND[1]), rel=1e-14)


def test_spin_drag():
    """F = -(1/2) rho f(S) C_D(Re) A |v| v; along -v; f from eq. (17)."""
    air = Medium.air()
    sd = mg.SpinDrag(0.020, 150.0, air)
    v = np.array([2.0, -2.0])
    sp = float(np.linalg.norm(v))
    S = 0.01 * 150.0 / sp
    re = air.rho * sp * 0.02 / air.mu
    ref = -0.5 * air.rho * float(mg.drag_factor(S)) * float(dq.cd_standard(re)) * math.pi * 1e-4 * sp * v
    assert sd.force(0.0, None, v) == pytest.approx(ref, rel=1e-14)
    sd3 = mg.SpinDrag(0.020, [0.0, 150.0, 0.0], air)
    assert sd3.force(0.0, None, [2.0, 0.0, -2.0])[[0, 2]] == pytest.approx(ref, rel=1e-14)


@pytest.mark.parametrize("call", [lambda: mg.cl_zhou(0.5, 2e4), lambda: mg.cl_zhou(7.0, 1e3),
                                  lambda: mg.cl_zhou(-0.1, 1e3), lambda: mg.Magnus(0.0, 1.0),
                                  lambda: mg.Magnus(0.02, 1.0, edge="median"),
                                  lambda: mg.Magnus(0.02, [1.0, 2.0]).force(0.0, None, [1.0, 0.0, 0.0])])
def test_refusals(call):
    with pytest.raises(ValueError):
        call()


def test_the_rolling_ball_of_s03_s_chute():
    """The steel ball leaves the chute at 1.5 m/s rolling (omega = v0 / R = 150 rad/s, topspin) and falls 1 m: Re from
    2.0·10^3 to 6.2·10^3, S from 1 to 0.32 (inside the model's domain); the energy balance holds with the Magnus force
    doing no work; the Magnus force shortens the range by 1.08 mm (band 0.89–1.33 mm) and the spin's drag by 0.24 mm
    (0.18–0.30); a spin falling linearly by 7 % over the flight (the bound estimated in s03_forces) changes it by
    0.01 mm."""
    air = Medium.air()
    w = 1.5 / 0.010
    base = fly(STEEL, [0.0, 1.0], [1.5, 0.0], forces=[dq.CurveDrag.sphere(0.020)], medium=air)
    f = fly(STEEL, [0.0, 1.0], [1.5, 0.0], forces=[mg.SpinDrag(0.020, w, air), mg.Magnus(0.020, w, air)], medium=air)
    assert f.energy_balance() < 1e-9
    _, _, Wf = f.state(f.t_end)
    assert abs(Wf[1]) < 1e-12 * abs(Wf[0])  # the lift does no work
    re = f.reynolds()[0]
    assert re.min() == pytest.approx(1992.0, abs=1.0) and re.max() == pytest.approx(6197.0, abs=2.0)
    mag = mg.Magnus(0.020, w, air)
    assert mag.spin_ratio(0.0, [1.5, 0.0]) == pytest.approx(1.0) and mag.spin_ratio(f.t_end, f.landing["v"]) < 0.33
    lift = fly(STEEL, [0.0, 1.0], [1.5, 0.0], forces=[dq.CurveDrag.sphere(0.020), mg.Magnus(0.020, w, air)],
               medium=air)
    spin = fly(STEEL, [0.0, 1.0], [1.5, 0.0], forces=[mg.SpinDrag(0.020, w, air)], medium=air)
    assert (lift.range - base.range) * 1e3 == pytest.approx(-1.083, abs=0.002)
    assert (spin.range - base.range) * 1e3 == pytest.approx(-0.242, abs=0.002)
    T = f.t_end
    dec = fly(STEEL, [0.0, 1.0], [1.5, 0.0], medium=air,
              forces=[mg.SpinDrag(0.020, lambda t: w * (1 - 0.07 * min(t, T) / T), air),
                      mg.Magnus(0.020, lambda t: w * (1 - 0.07 * min(t, T) / T), air)])
    assert abs(dec.range - f.range) * 1e3 < 0.012
