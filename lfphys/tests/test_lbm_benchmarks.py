# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Plan P8: the 2-D lattice Boltzmann solver against published benchmarks (sources and the numbers as grepped:
sources/verification_2026-11-04_p8_lbm.md).

* Ghia, Ghia & Shin, J. Comput. Phys. 48, 387 (1982), the driven cavity at Re = 100: Table I (u on the vertical
  centre line) and Table II (v on the horizontal one), Re = 100 columns; the paper itself was not obtained (paywalled),
  the tables are taken from two transcriptions that agree.
* Schaefer & Turek (1996), "Benchmark computations of laminar flow around a cylinder", the DFG cases 2D-1 (Re = 20:
  "lower bound 5.5700 0.0104", "upper bound 5.5900 0.0110" for cD, cL; Table 3) and 2D-2 (Re = 100: "maximum drag
  coefficient cDmax , maximum lift coefficient cLmax , Strouhal number St", Table 4: cDmax 3.2200-3.2400, cLmax
  0.9900-1.0100, St 0.2950-0.3050). Channel 2.2 x 0.41 m, cylinder D = 0.1 m at (0.2, 0.2), nu = 1e-3, rho = 1, inflow
  4 Um y (H - y) / H^2, U = 2 Um / 3; "outflow condition can be chosen by the user". The data: ``lbm.GHIA_*``,
  ``lbm.DFG_*``.

The weakly compressible scheme carries sound; the channel's velocity inlet and pressure outlet reflect it, so a
standing wave of period 4 L / c_s (``Flow2D.acoustic_period``: 2.93 s at Ma = 0.1) rides on the forces: with the 3-s
smooth start used here +-1.5 % of cD at Ma = 0.1 and +-0.4 % at Ma = 0.05 (O(Ma^2)); after an impulsive start far more
(+-13 % between 8 and 12 s in the playground's former 2D-1 preset at Ma 0.067, review B7 L4). 2D-1 is therefore
averaged over whole acoustic periods. The cylinder runs take minutes on the CPU and run where GPU 0 is given.
"""

import math

import numpy as np
import pytest

from lfphys.core import backend
from lfphys.core.fluids import lbm

GHIA_Y, GHIA_U100 = np.array(lbm.GHIA_Y), np.array(lbm.GHIA_U100)
GHIA_X, GHIA_V100 = np.array(lbm.GHIA_X), np.array(lbm.GHIA_V100)


def _gpu():
    return backend.devices()["gpu"]["available"]


@pytest.fixture(autouse=True)
def _defaults():
    backend.configure(None)
    yield
    backend.configure(None)


def _cavity(Re, N, T=25.0):
    """The unit cavity, lid at 1 m/s, nu = 1/Re: centre-line u(y) and v(x) at the Ghia points, and the change over the
    last time unit (steadiness)."""
    fl = lbm.Flow2D((1.0, 1.0), 1.0 / N, nu=1.0 / Re, rho=1.0, u_max=1.0, mach=0.1, tau_max=None,
                    sides={"top": lbm.Wall(1.0)})
    fl.advance_to(T - 1.0)
    u_prev = fl.velocity()[0]
    fl.advance_to(T)
    ux, uy = fl.velocity()
    i = N // 2  # x = 0.5 lies half-way between the columns N/2 - 1 and N/2
    ucol = 0.5 * (ux[i - 1] + ux[i])
    vrow = 0.5 * (uy[:, i - 1] + uy[:, i])
    ye = np.concatenate([[0.0], fl.y, [1.0]])
    u = np.interp(GHIA_Y, ye, np.concatenate([[0.0], ucol, [1.0]]))
    v = np.interp(GHIA_X, ye, np.concatenate([[0.0], vrow, [0.0]]))
    return u, v, float(np.max(np.abs(ux - u_prev)))


def test_driven_cavity_against_ghia_at_re_100():
    """64 x 64 nodes: max |u - Ghia| 0.0050, max |v - Ghia| 0.0079 of the lid speed (128^2: 0.0052, 0.0088; 256^2:
    0.0051, 0.0089 - the solver has converged, the rest is the difference from Ghia's 129^2 solution; it is not the
    compressibility either: the profiles change by 2e-4 from Ma 0.1 to 0.05, review B7 r10); the flow is steady to
    1e-6. The bounds asserted, 0.008 and 0.012, leave a margin of 1.6 and 1.5 over the measured values. Negative
    control: Re = 125 against the Re = 100 columns is three times farther."""
    u, v, ch = _cavity(100.0, 64)
    du, dv = np.abs(u - GHIA_U100)[1:-1], np.abs(v - GHIA_V100)[1:-1]
    assert ch < 1e-6
    assert du.max() < 0.008 and dv.max() < 0.012, (du.max(), dv.max())
    u2, v2, _ = _cavity(125.0, 64)
    assert max(np.abs(u2 - GHIA_U100).max(), np.abs(v2 - GHIA_V100).max()) > 3 * max(du.max(), dv.max())


def _dfg(Um, ND, interpolated=True, ramp=1.0, mach=0.1):
    fl = lbm.Flow2D((2.2, 0.41), 0.1 / ND, nu=1e-3, rho=1.0, u_max=Um, mach=mach, tau_max=None,
                    sides={"left": lbm.Inlet(Um, "parabolic", ramp=ramp), "right": lbm.Outlet(0.0)})
    oid = fl.add_obstacle(lbm.Disk((0.2, 0.2), 0.05), interpolated=interpolated)
    return fl, oid


def _dfg_2d1(ND, interpolated):
    """Steady 2D-1: cD, cL averaged over two acoustic periods after a 3-s smooth start and 6 s of settling."""
    fl, oid = _dfg(0.3, ND, interpolated, ramp=3.0)
    T_ac = fl.acoustic_period()["period"]
    assert T_ac == pytest.approx(4 * 2.2 / (fl.units.c * lbm.CS), rel=1e-14)
    fl.advance_to(9.0)
    fl.reset_force_mean()
    fl.advance_to(fl.t + 2 * T_ac)
    m = fl.forces(u_ref=0.2)[oid]["mean"]
    return m["cd"], m["cl"], fl


@pytest.mark.skipif(not _gpu(), reason="needs GPU 0 for speed (minutes on the CPU)")
def test_cylinder_dfg_2d1_drag_and_lift():
    """D = 40 cells, interpolated walls: cD = 5.5790, cL = 0.010752 (bounds 5.5700-5.5900, 0.0104-0.0110; at D = 80:
    5.5775, 0.010755; at D = 20: 5.5893, 0.010483; measured 2026-11-04 on GPU 0 — the former 5.5799 / 0.01078 here
    [error in earlier], review B7 L17). Negative control: staircase walls at D = 20 give cD = 5.6367, cL = 0.011252,
    outside both ranges."""
    cd, cl, fl = _dfg_2d1(40, True)
    (lo, hi), (lo2, hi2) = lbm.DFG_2D1["cD"], lbm.DFG_2D1["cL"]
    assert lo <= cd <= hi and lo2 <= cl <= hi2, (cd, cl)
    assert abs(fl.balance()["mass"]["relative_residual"]) < 1e-12
    cd2, cl2, _ = _dfg_2d1(20, False)
    assert cd2 > hi and cl2 > hi2, (cd2, cl2)


def _dfg_2d2(ND, mach):
    """2D-2 from 0.005-s block means of the force record over the last 3 s of 12: St (zero crossings of cL), cDmax,
    cLmax, cLmin."""
    fl, oid = _dfg(1.5, ND, mach=mach)
    fl.advance_to(9.0)
    fl.record_forces(max(1, int(round(0.005 / fl.units.dt))))
    fl.advance_to(12.0)
    r = fl.force_record()
    ts = r["t_end"] - 0.5 * r["block"]
    q = 0.5 * 1.0 * 1.0**2 * 0.1
    cds, cls = r["obstacles"][oid]["force"][:, 0] / q, r["obstacles"][oid]["force"][:, 1] / q
    c = cls - cls.mean()
    up = np.flatnonzero((c[:-1] < 0) & (c[1:] >= 0))
    tz = ts[up] - c[up] * (ts[up + 1] - ts[up]) / (c[up + 1] - c[up])
    return {"St": 0.1 * (len(tz) - 1) / (tz[-1] - tz[0]), "cDmax": cds.max(), "cLmax": cls.max(), "cLmin": cls.min()}


@pytest.mark.skipif(not _gpu(), reason="needs GPU 0 for speed (minutes on the CPU)")
def test_cylinder_dfg_2d2_strouhal_and_the_maxima():
    """2D-2 at D = 20 cells, interpolated walls: St = 0.2990 inside 0.2950-0.3050 (at D = 40: 0.3009). The maxima are
    outside their bounds and are pinned here as measured (review B7 L9: the benchmark asks for cLmax, not the lift
    amplitude the test asserted before [error in earlier]): cLmax = 0.9793 against 0.9900-1.0100 (0.9804 at D = 40),
    cDmax = 3.330 against 3.2200-3.2400 (3.248 at D = 40). The lift's mean offset (cLmax + cLmin)/2 = -0.0185 is the same
    at Ma = 0.1 and 0.05 (-0.0185), so it is not the O(Ma^2) acoustic wave the former note blamed [error in earlier];
    its cause is open (STATUS V41 p)."""
    a = _dfg_2d2(20, 0.1)
    assert 0.2950 <= a["St"] <= 0.3050, a
    assert 0.976 <= a["cLmax"] <= 0.983 and a["cLmax"] < lbm.DFG_2D2["cLmax"][0], a
    assert 3.31 <= a["cDmax"] <= 3.35 and a["cDmax"] > lbm.DFG_2D2["cDmax"][1], a
    b = _dfg_2d2(20, 0.05)
    off_a, off_b = 0.5 * (a["cLmax"] + a["cLmin"]), 0.5 * (b["cLmax"] + b["cLmin"])
    assert abs(off_a - off_b) < 0.1 * abs(off_a), (a, b)  # O(Ma^2) would have shrunk it four times
