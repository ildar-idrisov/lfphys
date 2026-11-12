# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""p04: the fluids playground. Every preset and the default laws build, run and keep their balances; the wrapper's
pieces against closed forms (the NACA four-digit profile's thickness and the angle of attack's sense, the Reynolds
number of a cylinder and of a lid); the sides' bookkeeping (one condition per side, a removed inlet gives the wall
back); a refused change leaves the scene as it was; the field shown on request; the scene file and its time base; the
fixes of review B7 (L1-L5, L8, L10, L11, L15, L16): an inlet edit keeps the inflow, the forces' mean over the sound
period, the benchmark comparisons for their set-ups only, the surface velocity labelled as one, the Kármán preset
within its cell-Reynolds limit, the coefficient length set back to 0, the picture's averaging. The flow itself
(Poiseuille, Couette, Taylor–Green, the DFG cylinder, Ghia's cavity) is tested in ``lfphys/tests/test_lbm*.py``; the
shared tests continue every world from its checkpoint byte for byte and rebuild it by replay
(``../tests/test_checkpoint.py``, ``../tests/test_restore.py``)."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.core import backend  # noqa: E402
from p04_fluids.viz import SCHEMA, naca4, resample  # noqa: E402

V = "p04_fluids"
SMALL = {}  # the presets at their own grids (a coarser one is refused where it cannot resolve the flow)


def run(h, seconds, n=10):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + seconds * k / n)
        h.runner._frame(0.0)


def failed(h):
    return [c["id"] for c in h.checks().values() if c.get("ok") is False]


@pytest.mark.parametrize("preset", list(SCHEMA.presets) + [None])
def test_every_preset_and_the_default_laws_build_run_and_keep_their_balances(preset):
    """The presets, and the default laws without a preset (review B7 L11: the former defaults — water, 2.2 × 0.41 m,
    440 nodes — were refused by the engine, τ − ½ = 8·10⁻⁵)."""
    h = Harness(V, preset, SMALL)
    run(h, 2.0 * h.sim.default_speed)
    assert not h.errors(), h.errors()
    assert not failed(h), {k: h.checks()[k] for k in failed(h)}
    assert {"mass", "momentum", "mach", "re_cell"} <= set(h.checks())
    assert h.of("field") and h.of("vectors")
    if preset is not None:
        assert h.of("shapes")


def test_the_naca_profile_and_the_angle_of_attack():
    """NACA 0012: the thickness 12 % of the chord, largest at x ≈ 0.3 c (y_t(0.3) = 0.0600 c from the series of
    Abbott & von Doenhoff with the closed trailing edge); a cambered 2412 has its camber line above the chord. The angle
    of attack lowers the trailing edge for a stream along +x."""
    P = naca4("0012", 1.0, n=400)
    assert P[:, 1].max() - P[:, 1].min() == pytest.approx(0.12, rel=2e-3)
    assert P[np.argmax(P[:, 1]), 0] == pytest.approx(0.30, abs=0.01)
    Q = naca4("2412", 1.0)
    assert Q[:, 1].max() > -Q[:, 1].min()
    h = Harness(V, "airfoil", SMALL)
    foil = [o for o in h.sim.objects.values() if o["type"] == "airfoil"][0]
    pts = h.sim._foil(foil["values"])
    lead, trail = pts[np.argmin(pts[:, 0])], pts[np.argmax(pts[:, 0])]
    assert trail[1] < lead[1]
    assert math.degrees(math.atan2(lead[1] - trail[1], trail[0] - lead[0])) == pytest.approx(8.0, abs=0.5)


def test_reynolds_numbers_of_a_cylinder_and_of_a_lid():
    h = Harness(V, "karman", SMALL)
    run(h, 0.002, 1)
    now = h.of("frame")[-1]["now"]
    cyl = [k for k, o in h.sim.objects.items() if o["type"] == "disk"][0]
    assert now[cyl]["Re (по длине и скорости для коэффициентов)"] == pytest.approx(100.0, rel=1e-12)
    h = Harness(V, "cavity", SMALL)
    run(h, 0.05, 2)
    lid = [k for k, o in h.sim.objects.items() if o["type"] == "lid"][0]
    assert h.of("frame")[-1]["now"][lid]["Re = U·L/ν"] == pytest.approx(100.0, rel=1e-12)


def test_one_condition_per_side_and_a_removed_inlet_gives_the_wall_back():
    """One condition per side: a palette outlet asked on a taken side lands on the first free one with a note (review
    UX-ui U4); moving an existing object onto a taken side is refused with the free sides named, and leaves the scene;
    a removed inlet gives the wall back."""
    h = Harness(V, "cylinder_re20", SMALL)
    h.cmd("scene", op="add", type="outlet", values={"side": "left"})
    assert not h.errors(), h.errors()
    new = [o for o in h.sim.objects.values() if o["type"] == "outlet"][-1]
    assert new["values"]["side"] == "top" and h.sim.fl.sides()["top"]["kind"] == "outlet"
    assert any("занята" in m.get("text", "") and m.get("notify") for m in h.of("event"))
    before = [o["id"] for o in h.of("scene")[-1]["objects"]]
    h.cmd("scene", op="set", id=new["id"], values={"side": "left"})
    assert any("уже занята" in e and "свободны" in e for e in h.errors()), h.errors()
    assert [o["id"] for o in h.of("scene")[-1]["objects"]] == before and h.sim.fl.sides()["top"]["kind"] == "outlet"
    inlet = [k for k, o in h.sim.objects.items() if o["type"] == "inlet"][0]
    h.cmd("scene", op="remove", id=inlet)
    assert h.sim.fl.sides()["left"]["kind"] == "wall"
    n = len(h.errors())
    h.cmd("scene", op="add", type="outlet", values={"side": "left"})
    assert len(h.errors()) == n and h.sim.fl.sides()["left"]["kind"] == "outlet"


def test_dye_needs_a_world_with_dye_and_the_field_is_shown_on_request():
    h = Harness(V, "cavity", {"dye": "off", "scene": None})
    h.cmd("scene", op="add", type="dye_source", values={"x": 0.5, "y": 0.2})
    assert any("краситель выключен" in e for e in h.errors())
    h = Harness(V, "cavity", SMALL)
    h.cmd("view", op="field", field="vorticity")
    assert h.of("field")[-1]["name"] == "vorticity"
    lo, hi = h.of("field")[-1]["range"]
    assert lo == pytest.approx(-hi)


def test_an_obstacle_added_while_the_flow_runs_keeps_the_balances():
    h = Harness(V, "channel", SMALL)
    run(h, 2.0 * h.sim.default_speed, 5)
    h.cmd("scene", op="add", type="disk", values={"x": 0.05, "y": 0.01, "radius": 0.002})
    run(h, h.sim.t + 2.0 * h.sim.default_speed, 5)
    assert not h.errors() and not failed(h)


def test_the_scene_file_starts_the_same_set_up_at_its_time_and_keeps_it():
    """Review B7 L2: a world from a file starts at the file's time with no steps; advancing it twice keeps t = T +
    steps dt (before, the first advance dropped the engine's time to ≈ 0 and the second computed T/dt steps at once,
    with the inlet off meanwhile); its inlet ramps from the file's time."""
    h = Harness(V, "cylinder_re20", SMALL)
    run(h, 0.2, 2)
    h.cmd("scene", op="export")
    sc = h.of("scene_export")[-1]["scene"]
    h2 = Harness(V, None, {**sc["laws"], "scene": sc})
    a = [(o["type"], o["label"], o["values"]) for o in h.sim.objects.values()]
    b = [(o["type"], o["label"], o["values"]) for o in h2.sim.objects.values()]
    assert a == b
    fl, T, dt = h2.sim.fl, sc["t"], h2.sim.fl.units.dt
    assert fl.steps == 0 and fl.t == pytest.approx(T) and h2.sim.t == pytest.approx(T)
    for k in (1, 2):
        h2.run_to(T + 0.01 * k)
        h2.runner._frame(0.0)
        assert fl.steps == round(0.01 * k / dt) and fl.t == pytest.approx(T + 0.01 * k, abs=dt)
    assert 0.0 < fl.inlet_scales()["left"] < 1e-3  # the ramp (3 s) started at the file's time


def test_editing_an_inlet_keeps_the_inflow():
    """Review B7 L1: at a developed state, an edit of the inlet's dye and a second inlet added on another side leave
    the inflow as it was (before, both restarted every inlet's ramp: the inflow dropped to zero within a step and the
    Kármán preset blew up 0.13 s later)."""
    h = Harness(V, "cylinder_re20", SMALL)
    run(h, 3.1, 2)
    fl = h.sim.fl
    q0 = fl.flow_rates()["left"]
    inlet = [k for k, o in h.sim.objects.items() if o["type"] == "inlet"][0]
    h.cmd("scene", op="set", id=inlet, values={"dye": 0.5})
    h.run_to(h.sim.t + 0.01)
    assert fl.inlet_scales()["left"] == 1.0 and fl.flow_rates()["left"] == pytest.approx(q0, rel=1e-12)
    h.cmd("scene", op="add", type="inlet", values={"side": "top", "speed": 0.01, "profile": "uniform"})
    h.run_to(h.sim.t + 0.01)
    assert fl.flow_rates()["left"] == pytest.approx(q0, rel=1e-12) and not h.errors()


def test_a_coefficient_length_set_back_to_zero_is_the_diameter_again():
    """Review B7 L10: «0 — диаметр» after a custom length (before, 0.2 m stayed: C_x, C_y half their values)."""
    h = Harness(V, "cylinder_re20", SMALL)
    cyl = [k for k, o in h.sim.objects.items() if o["type"] == "disk"][0]
    eid = h.sim.ref[cyl][1]
    for ref, want in ((0.2, 0.2), (0.0, 0.1)):
        h.cmd("scene", op="set", id=cyl, values={"ref": ref})
        assert h.sim.fl.forces()[eid]["length"] == pytest.approx(want, rel=1e-12)
    assert not h.errors()


def test_the_forces_are_shown_averaged_over_the_sound_period_with_their_window():
    """Review B7 L4: the inspector and the check show C_x, C_y averaged over the domain's slowest sound period (4L/c_s
    here: the inlet closes the channel for sound, the outlet opens it) next to the last step's values, labelled as
    such; the mean is the engine's own mean over exactly the window's steps (a second method: ``reset_force_mean`` at
    the window's start, to 1e-12); the window is the period to half a block."""
    h = Harness(V, "cylinder_re20", SMALL)
    sim, fl = h.sim, h.sim.fl
    w = sim.win
    assert w["kind"] == "closed-open" and w["period"] == pytest.approx(4 * 2.2 / (fl.units.c * 3**-0.5), rel=1e-12)
    assert abs(w["n"] * w["every"] * fl.units.dt - w["period"]) <= 0.5 * w["every"] * fl.units.dt
    fl.reset_force_mean()  # at step 0: the record's first block starts here too
    target = w["n"] * w["every"]
    h.run_to(target * fl.units.dt)
    assert fl.steps == target
    h.runner._frame(0.0)
    cyl = [k for k, o in sim.objects.items() if o["type"] == "disk"][0]
    eid = sim.ref[cyl][1]
    now = h.of("frame")[-1]["now"][cyl]
    mean = fl.forces(u_ref=0.2)[eid]["mean"]
    assert now["C_x, среднее за период звука"] == pytest.approx(mean["cd"], rel=1e-12)
    assert now["C_y, среднее за период звука"] == pytest.approx(mean["cl"], rel=1e-10)
    assert "4L/c_s" in now["окно среднего"] and "C_x за последний шаг (со звуком схемы)" in now
    sim.checks()
    c = h.checks()[f"cd_{cyl}"]
    assert "среднее за период звука" in c["label"] and c["value"] == pytest.approx(mean["cd"], rel=1e-12)


def test_benchmark_comparisons_appear_for_their_set_ups_only():
    """Review B7 L5: the DFG 2D-1 preset, past its ramp and one sound period, shows C_D and C_L against Schäfer &
    Turek's ranges (with the grid and the wall); moving the disk ends the comparison. The cavity shows Ghia's
    centre-line differences; the channel the Poiseuille profile at its probe; a world that is none of them shows none."""
    h = Harness(V, "cylinder_re20", SMALL)
    run(h, 5.2, 4)
    h.sim.checks()
    ch = h.checks()
    assert {"dfg_cD", "dfg_cL"} <= set(ch), sorted(ch)
    assert "5.5700" in ch["dfg_cD"]["note"] and "D = 20 ячеек" in ch["dfg_cD"]["note"] and ch["dfg_cD"]["info"]
    assert "интерполированная" in ch["dfg_cD"]["note"]
    cyl = [k for k, o in h.sim.objects.items() if o["type"] == "disk"][0]
    h.cmd("scene", op="set", id=cyl, values={"x": 0.25})
    assert h.sim._dfg_case() is None
    h = Harness(V, "cavity", SMALL)
    run(h, 0.1, 2)
    h.sim.checks()
    assert {"ghia_u", "ghia_v"} <= set(h.checks())
    h = Harness(V, "channel", SMALL)
    run(h, 0.6, 2)  # past its 0.5-s ramp
    h.sim.checks()
    assert any(k.startswith("pois_") for k in h.checks())
    h = Harness(V, "airfoil", SMALL)
    run(h, 0.01, 1)
    h.sim.checks()
    assert not [k for k in h.checks() if k.startswith(("dfg", "ghia", "pois", "couette"))]
    # plane Couette flow built by hand (periodic along x, the top wall moving): its steady profile against U y / H
    h = Harness(V, None, {"fluid": "custom", "rho": 1.0, "nu": 2e-4, "Lx": 0.1, "Ly": 0.0125, "nx": "128",
                          "u_max": 0.1, "dye": "off"})
    h.cmd("scene", op="add", type="periodic", values={"axis": "x"})
    h.cmd("scene", op="add", type="lid", values={"side": "top", "speed": 0.05})
    run(h, 2.4, 3)  # over 3 viscous times H^2 / nu = 0.78 s: the slowest mode down by exp(-3 pi^2)
    h.sim.checks()
    c = h.checks()["couette"]
    assert c["info"] and c["value"] < 1e-6, c


def test_the_surface_velocity_is_labelled_as_one_and_the_cascade_is_flagged():
    """Review B7 L3: the palette calls a body's velocity what the engine does with it — a surface velocity on a shape
    that stays where it is — and the world's approximations say so when one is set; L5: the periodic airfoil preset is
    labelled a cascade, and so is any periodic world with a body."""
    h = Harness(V, "cylinder_re20", SMALL)
    disk = h.sim.PALETTE["disk"].schema.by_id
    assert "поверхности" in disk["vx"].label and "НЕ перемещается" in disk["vx"].help
    assert not any("поверхность" in a for a in h.sim._approx())
    cyl = [k for k, o in h.sim.objects.items() if o["type"] == "disk"][0]
    h.cmd("scene", op="set", id=cyl, values={"wall": "staircase", "vx": 0.05})
    assert not h.errors(), h.errors()
    approx = [m for m in h.of("approximations")][-1]["approximations"]
    assert any("стоят на месте" in a for a in approx)
    assert "решётка" in SCHEMA.presets["airfoil"]["label"]
    h = Harness(V, "airfoil", SMALL)
    assert any("решётка тел" in a for a in h.sim._approx())


def test_the_karman_preset_stays_within_its_cell_reynolds_limit():
    """Review B7 L8: at 880 nodes (D = 40 cells) the measured cell Reynolds number stays below the open limit 10
    past the ramp (0.5 s) and past the time the former 440-node preset crossed it (0.44 s); on GPU 0 the developed
    street (to 6 s: max 5.59 measured) too, with the DFG 2D-2 comparisons shown."""
    gpu = backend.devices()["gpu"]["available"]
    h = Harness(V, "karman", SMALL)
    fl = h.sim.fl
    worst = 0.0
    T = 6.0 if gpu else 0.55
    while h.sim.t < T - 1e-9:
        h.run_to(min(T, h.sim.t + 0.05))
        h.runner._frame(0.0)
        worst = max(worst, fl.numbers()["re_cell"])
    assert worst < 0.7 * fl.re_cell_limit(), worst
    h.sim.checks()
    assert not failed(h) and not h.errors()
    if gpu:
        assert {"dfg_St", "dfg_cDmax", "dfg_cLmax"} <= set(h.checks())


def test_the_picture_averages_the_fluid_only_and_spans_the_domain():
    """Review B7 L16: a picture point covering fluid and solid cells shows the fluid's mean (before, solid cells counted
    as the scale's low end), and the points cover equal shares of the whole domain (before, trailing rows were cropped
    while the picture kept the domain's size). A field constant in the fluid stays constant at every fluid point; a
    field's integral is kept (the points' shares sum to the domain)."""
    nx, ny = 1000, 190
    fluid = np.ones((nx, ny), bool)
    fluid[300:420, 50:121] = False
    a = np.where(fluid, 3.0, np.nan)
    val, frac = resample(a, fluid, 512)
    assert val.shape == (round(nx / (1000 / 512)), round(ny / (1000 / 512)))
    assert np.allclose(val[frac > 0], 3.0, rtol=0, atol=1e-12)
    assert ((frac > 0) & (frac < 1)).any()  # mixed points exist, and read the fluid's value
    X = (np.arange(nx) + 0.5)[:, None] * np.ones(ny)
    lin, _ = resample(X, np.ones((nx, ny), bool), 512)
    mx, my = lin.shape
    assert lin.sum() * (nx / mx) * (ny / my) == pytest.approx(X.sum(), rel=1e-12)
    assert np.all(np.diff(lin[:, 0]) > 0)


def test_the_view_marks_the_picture_as_an_approximation():
    """Review B7 L15: the flow picture's window is marked an approximation, with the reason (2-D, weakly compressible,
    walls)."""
    js = (Path(__file__).resolve().parents[1] / "web" / "view.js").read_text()
    assert "approximation: true" in js and "approximation: false" not in js and "exact: false" in js
    assert "слабосжимаемая" in js
