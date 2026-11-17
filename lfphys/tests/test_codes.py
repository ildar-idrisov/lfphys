# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The engine's machine codes of refusals are stable (review 2026-11-12 i18n-code F5): the worlds match ``exc.code``,
never the English wording, so a code is never renamed, removed or reused. The list below is frozen: a new code is
added here and in ``lfphys.codes.CODES`` together; a code a world matches is raised by its condition (one test each)."""

import ast
import math
import pickle
import re
from pathlib import Path

import pytest

from lfphys.codes import CODES, code_of, coded, data_of
from lfphys.i18n import T, is_t

PKG = Path(__file__).resolve().parents[1] / "lfphys"

FROZEN = {
    "airy.grazing", "airy.lossy_index", "airy.total_reflection", "angular_spectrum.backward",
    "angular_spectrum.plane_extent", "beams.memory", "beams.mode_index", "beams.z", "cornell.box",
    "fdtd.incident_memory", "fdtd.monitor_region", "fdtd.non_finite", "fdtd.outside_grid", "fdtd.unstable_interface",
    "fdtd.unstable_medium", "film.below_critical", "film.too_many_nodes", "fit.no_convergence", "fit.singular",
    "geometry.zero_normal", "gr.inside_horizon",
    "gr.not_timelike", "hydrogen.level", "jp.irregular", "jp.no_bound_orbit", "jp.no_isco", "jp.no_photon_orbit",
    "jp.no_stable_orbit", "jp.outside_bounds", "jp.photon_sphere", "kerr.axis_view", "kerr.image", "kerr.spin",
    "kinematics.superluminal", "kn.inside_capture", "kn.no_horizon", "kn.no_isco", "kn.no_photon_orbit", "kn.observer",
    "kn.on_axis", "kn.step_underflow", "kn.superluminal", "kn.zero_direction", "kn_change.refused",
    "lbm.adopt_unstable", "lbm.cell_reynolds", "lbm.cut_by_edge", "lbm.dye_has_sources", "lbm.interp_moving",
    "lbm.mach", "lbm.rebuild_unstable", "lbm.rest_density", "lbm.tau", "lbm.unstable", "md.bond_broke",
    "md.bond_strain", "md.cutoff", "md.drift", "md.ewald", "md.hard_affine", "md.hard_box", "md.hard_overlap",
    "md.hard_unsupported", "md.insertion", "md.jammed", "md.lattice_cell", "md.no_free_site", "md.non_finite",
    "md.outside_walls", "md.overlap", "md.periodic_axis", "md.piston", "md.potential", "md.ramp", "md.refused",
    "md.region", "md.same_point", "md.samples", "md.thermal_wall", "md.thermostat", "md.value",
    "mechanics.bad_gravity", "mechanics.below_ground", "mechanics.no_flight", "mechanics.no_landing",
    "mechanics.nonfinite", "mie.index",
    "mie.mx_too_large", "mie.no_convergence", "mie.size", "mie.size_bound", "nbody.body", "nbody.collision",
    "nbody.refused", "newton.unbound", "optics.z", "orbit.horizon", "orbit.no_circular", "orbit.no_fall",
    "orbit.not_bound", "orbit.superluminal", "pn.above_circular", "pn.invalid", "pn.no_circular", "pn.plunge",
    "pn.plunge_integration", "pn.pn_breakdown", "pn.start_below_stop", "pn.unbound", "pn.unresolved",
    "qcd.landau_pole", "qcd.rg_failed", "qscene.alias", "qscene.device_memory", "qscene.field_with_charge",
    "qscene.gauge", "qscene.layers", "qscene.packet_band", "qscene.no_localisation_point", "qscene.no_wave", "qscene.refused",
    "qscene.regrid_dimension", "qscene.regrid_kind", "qscene.regrid_loss", "qscene.resolution", "qscene.wrap",
    "quantum.negative_probability", "rainbow.impact", "rainbow.order", "raytrace.camera_up", "slit.geometry",
    "slit.overlap", "water.out_of_range", "worldline.boost_order",
}


def test_the_codes_are_frozen():
    assert set(CODES) == FROZEN, (f"added: {sorted(set(CODES) - FROZEN)}; removed or renamed: "
                                  f"{sorted(FROZEN - set(CODES))} — a code is never renamed or removed")
    assert all(re.fullmatch(r"[a-z0-9_]+\.[a-z0-9_]+", c) for c in CODES)
    assert all(isinstance(v, str) and v for v in CODES.values())


def _codes_in_code() -> set:
    """Every code the engine's code raises: ``coded(..., "<code>")`` literals, class attributes ``code = "..."``,
    ``_WHAT_CODES`` of the quantum scene, NoOrbit's reasons ("pn." + reason)."""
    out = set()
    for path in PKG.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "coded":
                if isinstance(n.args[1], ast.Constant):  # else a table's value (scene._WHAT_CODES)
                    out.add(n.args[1].value)
            elif isinstance(n, ast.For) and isinstance(n.target, ast.Tuple) and \
                    getattr(n.target.elts[0], "id", None) == "code":  # for code, reason in (("...", ...), ...)
                out |= {t.elts[0].value for t in ast.walk(n.iter) if isinstance(t, ast.Tuple) and t.elts
                        and isinstance(t.elts[0], ast.Constant)}
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "NoOrbit" and n.args \
                    and isinstance(n.args[0], ast.Constant):
                out.add("pn." + n.args[0].value)
            elif isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.value, ast.Constant):
                t = n.targets[0]
                if isinstance(t, ast.Name) and t.id == "code" and isinstance(n.value.value, str):
                    out.add(n.value.value)
            elif isinstance(n, ast.Assign) and any(isinstance(t, ast.Attribute) and t.attr == "code"
                                                   for t in getattr(n.targets[0], "elts", n.targets)):
                for c in ast.walk(n.value):
                    if isinstance(c, ast.Constant) and isinstance(c.value, str) and "." in c.value[:-1]:
                        out.add(c.value)
    from lfphys.core.quantum import scene
    out |= set(scene._WHAT_CODES.values()) | {"qscene.refused"}
    return out


def test_every_code_is_raised_somewhere_and_every_raised_code_is_known():
    used = _codes_in_code()
    assert not sorted(used - set(CODES)), "codes raised but not in CODES"
    assert not sorted(set(CODES) - used), "codes in CODES that nothing raises"


def test_coded_keeps_the_type_the_text_and_the_numbers_through_pickle():
    e = coded(ValueError(T("Mach number {ma:.3g} > {max}: x", ma=0.5, max=0.3)), "lbm.mach", extra=1)
    assert isinstance(e, ValueError) and is_t(e.args[0])
    assert code_of(e) == "lbm.mach" and data_of(e) == {"ma": 0.5, "max": 0.3, "extra": 1}
    e2 = pickle.loads(pickle.dumps(e))
    assert type(e2) is ValueError and code_of(e2) == "lbm.mach" and data_of(e2) == data_of(e)
    assert code_of(ValueError("plain")) is None and data_of(ValueError("plain")) == {}
    with pytest.raises(KeyError):
        coded(ValueError("x"), "no.such_code")


def _raises(code, fn, *a, exc=ValueError, **k):
    with pytest.raises(exc) as e:
        fn(*a, **k)
    assert code_of(e.value) == code, (code, code_of(e.value), str(e.value))
    assert is_t(e.value.args[0]), "a coded refusal is a translatable text"
    return e.value


# --- the codes the worlds match (one condition each) ---------------------------------------------------------------
def test_lbm_codes():
    from lfphys.core.fluids import lbm
    e = _raises("lbm.mach", lbm.Flow2D, (0.1, 0.1), 1e-3, nu=1e-4, u_max=1.0, mach=0.35)
    assert e.data["ma"] > e.data["max"] == lbm.MACH_MAX
    _raises("lbm.tau", lbm.Flow2D, (0.1, 0.1), 1e-3, nu=1e-9, dt=1e-3)
    e = _raises("lbm.cell_reynolds", lbm.Flow2D, (0.1, 0.1), 1e-3, nu=1e-6, u_max=0.02, mach=0.1,
                sides={"left": lbm.Inlet(0.02), "right": lbm.Outlet()})
    assert e.data["rec"] > e.data["lim"]


def test_thin_film_codes():
    from lfphys.core.optics import thin_films as TF
    _raises("airy.lossy_index", TF.airy, 1.0, 1.5 + 0.1j, 1.0, 1e-6, 5e-7, 0.0, "s")
    _raises("airy.total_reflection", TF.airy, 1.5, 1.0, 1.5, 1e-6, 5e-7, 1.2, "s")
    _raises("film.below_critical", TF.evanescent_length, 1.5, 1.0, 5e-7, 0.1)


def test_mie_codes():
    from lfphys.core.optics import mie
    e = _raises("mie.size_bound", mie.coefficient_bound, 2.0 * mie.MAX_X)
    assert e.data["xmax"] == mie.MAX_X
    _raises("mie.index", mie.coefficients, 1.33 - 0.1j, 10.0)
    _raises("mie.size", mie.coefficients, 1.33, 0.0)


def test_md_codes():
    from lfphys.core.md.system import MD
    md = MD(dim=2, box=(10.0, 10.0), boundary="walls")
    md.add_species("A")
    e = _raises("md.jammed", md.fill, "A", n=1000, arrangement="random")
    assert e.data["n"] == 1000 and e.data["k"] < 1000
    md2 = MD(dim=2, box=(10.0, 10.0), boundary="periodic")
    md2.add_species("A")
    md2.fill("A", n=4)
    e = _raises("md.periodic_axis", md2.deform, (12.0, 10.0), mode="wall")
    assert e.data["axis"]


def test_scene_codes():
    from lfphys.core.quantum import scene as Q
    s = Q.Scene((128, 128), 0.2, dt=0.01)
    el = Q.species("electron")
    e = _raises("qscene.packet_band", s.add_particle, Q.Packet(el, [0, 0], [14.0, 0], [1.0, 1.0]))
    assert e.data["K"] > e.data["kn"]
    assert code_of(s.particle_check(Q.Packet(el, [0, 0], [14.0, 0], [1.0, 1.0]))) == "qscene.packet_band"
    assert s.particle_check(Q.Packet(el, [0, 0], [1.0, 0], [1.0, 1.0])) is None
    # next to a potential the 2/3 band applies (the resolution rule): a packet the free grid holds is refused there
    s.add(Q.Box([0.0, 0.0], [2.0, 2.0], 5.0, 0.8))
    e = s.particle_check(Q.Packet(el, [0, 0], [11.0, 0], [1.0, 1.0]))
    assert code_of(e) == "qscene.resolution" and data_of(e)["K"] > data_of(e)["lim"], e


def test_gravity_and_qcd_codes():
    from lfphys.core.gravity import kerr_newman as KN
    from lfphys.core.gravity import pn_binary as P
    from lfphys.core.qcd import running
    from lfphys.theories.alternatives import kn_change_whatif as WI
    e = _raises("qcd.landau_pole", running._evolve, 4.0 / (4 * math.pi), math.log(4.0), math.log(1.0), 4, 4)
    assert e.data["mu"] == pytest.approx(2.0)
    e2 = pickle.loads(pickle.dumps(e))
    assert code_of(e2) == "qcd.landau_pole" and e2.mu == e.mu and str(e2) == str(e)
    e = _raises("pn.no_circular", P.circular_speed, -1.0, 0.25)
    e2 = pickle.loads(pickle.dumps(e))
    assert code_of(e2) == "pn.no_circular" and e2.reason == "no_circular" and str(e2) == str(e)
    g = KN.Geodesics(0.9, 0.0, capture_eps=1e-4)
    g.add_body(8.0, 1.0, 0.0, key="far")
    e = _raises("kn_change.refused", WI.carry, g, 0.9, 0.5)
    assert isinstance(e, WI.Refused)


def test_kinematics_and_optics_codes():
    from lfphys.core import relativity as R
    from lfphys.theories.approx import rainbow as RB
    _raises("kinematics.superluminal", R.gamma, 1.5)
    e = _raises("rainbow.order", RB.descartes, 0.9, 2)
    assert e.data == {"p": 2, "m": 0.9}


def test_mechanics_codes():
    from lfphys.core import mechanics as M
    from lfphys.theories.models import drag_quadratic as DQ
    ball = M.Body(0.058, 0.067)
    e = _raises("mechanics.below_ground", M.fly, ball, (0.0, -0.5), (5.0, 1.0))
    assert e.data["h"] == pytest.approx(0.5)
    _raises("mechanics.no_flight", M.fly, ball, (0.0, 0.0), (5.0, 0.0))
    _raises("mechanics.no_flight", M.fly, ball, (0.0, 0.0), (5.0, -1.0))
    _raises("mechanics.no_flight", DQ.hodograph, 10.0, 0.0, 0.0, 0.01)
    _raises("mechanics.nonfinite", M.fly, ball, (0.0, 1.0), (float("nan"), 1.0))
    e = _raises("mechanics.bad_gravity", M.fly, ball, (0.0, 1.0), (5.0, 1.0), g=0.0)
    assert e.data["g"] == 0.0
    e = _raises("mechanics.no_landing", M.fly, ball, (0.0, 1000.0), (5.0, 1.0), t_max=1.0)
    assert e.data["t"] == 1.0


def test_fit_codes(monkeypatch):
    from lfphys.tools import stats as S
    _raises("fit.singular", S.linear_fit, [2.0, 2.0, 2.0, 2.0], [1.0, 1.1, 0.9, 1.05], 0.0, 0.05, "line")
    _raises("fit.singular", S.linear_fit, [30.0, 30.0, 30.0, 40.0], [1.0, 1.1, 0.9, 1.05], 0.5, 0.05, "quadratic")
    _raises("fit.singular", S.linear_fit, [0.0, 0.0, 0.0], [1.0, 1.1, 0.9], 0.1, 0.05, "line0")
    monkeypatch.setattr(S, "YORK_MAX_ITER", 2)  # Pearson-York needs more: the refusal of a slope that has not settled
    x = [0.0, 0.9, 1.8, 2.6, 3.3, 4.4, 5.2, 6.1, 6.5, 7.4]
    y = [5.9, 5.4, 4.4, 4.6, 3.5, 3.7, 2.8, 2.8, 2.4, 1.5]
    wx = [1000, 1000, 500, 800, 200, 80, 60, 20, 1.8, 1]
    wy = [1, 1.8, 4, 8, 20, 20, 70, 70, 100, 500]
    _raises("fit.no_convergence", S.linear_fit, x, y, [v ** -0.5 for v in wx], [v ** -0.5 for v in wy], "line")
