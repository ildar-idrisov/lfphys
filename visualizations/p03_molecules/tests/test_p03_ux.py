# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""p03 after the reviews of 2026-11-04 (UX-ui U4–U8, U12, U13; UX-params P4, P31–P33): a new object lands where it can
exist (the nearest free spot, a crystal around the atoms already there, a piston above the gas, a wall or a piston on a
periodic axis makes it walled) or is refused at once in Russian with what to change; the hard world's pressure at zero
temperature; a temperature the time step cannot resolve; molecule edits in one engine edit (time bounds); the live laws
(the pair model, its cutoff and shift, the time step) with the energy balance kept and the world rebuilt by replay of
the same commands; the engine's English refusals translated."""

import math
import queue
import re
import sys
import time
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.i18n import T as T_, english, is_t, msgids, text_of  # noqa: E402
from lfviz import registry  # noqa: E402
from lfviz.i18n import catalogue  # noqa: E402
from lfviz.sim import Runner  # noqa: E402
from p03_molecules.viz import KELVIN, NM, PS  # noqa: E402

V = "p03_molecules"
ENGINE = ("jammed", "overlap: an inserted", "Traceback", "bond would", "piston needs", "it has no wall", "outside the walls on axis")
RU = catalogue("ru")


class _Text(str):
    """An English rendering that remembers the text it renders (``translated`` checks the text itself)."""


def en(x):
    """A text as the player shows it in English (numbers in Python's format)."""
    s = _Text(english(x))
    s.raw = x
    return s


def translated(x):
    """The owner's text: a translatable text whose every part has a Russian translation, with none of the engine's
    English sentences (review UX-ui U13)."""
    x = getattr(x, "raw", x)
    ids = msgids(x) if is_t(x) else set()
    return bool(ids) and all(i in RU or not re.search(r"[A-Za-z]", re.sub(r"\{\w+(?::[^{}]*)?\}", "", i)) for i in ids) \
        and not any(w in english(x) for w in ENGINE)



def run(h, ps, n=10):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + ps * 1e-12 * k / n)
        h.runner._frame(0.0)



def added(h, typ):
    return [o for o in h.sim.objects.values() if o["type"] == typ]


def test_hard_disks_with_one_atom_at_rest_run():
    """U6 / P32: the hard world, “+ Atom” with its defaults (at rest: T = 0) used to stop every frame with a division by
    zero in the pressure; now the frames run, the pressure is 0 and Z has no value."""
    h = Harness(V, None, {"dynamics": "hard"})
    h.cmd("scene", op="add", type="atom", values={})
    run(h, 2.0, 5)
    assert not h.errors(), h.errors()
    st = h.of("stats")[-1]
    assert st["p"] == 0.0
    assert not any(c["id"] == "eos" and c.get("value") is not None for c in h.of("check"))


@pytest.mark.parametrize("values", [{"n": 1, "start": "same_speed"}, {"n": 50, "T": 0.0, "start": "same_speed"}])
def test_gas_of_equal_speeds_with_one_atom_or_at_zero_temperature(values):
    """P32: “all with one speed” with one atom or at T = 0 divided 0 by 0."""
    h = Harness(V)
    h.cmd("scene", op="add", type="gas", values=values)
    run(h, 0.5, 3)
    assert not h.errors(), h.errors()


def test_a_temperature_the_step_cannot_resolve_is_refused_and_a_shorter_step_takes_it():
    """P32: a gas at 10^5 K crashed the world («two interacting particles at the same point»); now it is refused at once,
    in the owner's language, with the largest temperature for this step and the step for this temperature; 1500 K (control) is taken;
    after “Time step” = 1 fs (a live law now) the 10^5 K gas is taken and runs."""
    h = Harness(V)
    h.cmd("scene", op="add", type="gas", values={"T": 1e5, "n": 100})
    err = en(h.errors()[-1])
    assert translated(err) and "fs" in err and "K" in err and not added(h, "gas")
    h.cmd("scene", op="add", type="gas", values={"T": 1500.0, "n": 100})
    assert len(h.errors()) == 1 and added(h, "gas")
    h.cmd("scene", op="remove", id=added(h, "gas")[0]["id"])
    h.set(dt_fs=1.0)
    assert h.sim.md.dt == pytest.approx(1e-3 / PS)
    h.cmd("scene", op="add", type="gas", values={"T": 1e5, "n": 100})
    assert len(h.errors()) == 1, h.errors()
    run(h, 0.05, 5)
    assert len(h.errors()) == 1
    # a longer step is now refused for the hot gas: the live law checks the motion present
    h.set(dt_fs=10.0)
    assert len(h.errors()) == 2 and translated(en(h.errors()[-1])) and h.sim.md.dt == pytest.approx(1e-3 / PS)


def test_a_wall_and_a_piston_on_the_default_periodic_box():
    """U7 / P31: the default box is periodic; “Wall” made it refuse «axis y is periodic», “Piston” «a piston needs a
    walled axis». Now the axis becomes walled at the current moment (a note says so), the piston lands above the gas,
    the atoms stay below it; removing the last of them makes the axis periodic again."""
    h = Harness(V)
    h.cmd("scene", op="add", type="gas", values={"n": 150})
    h.cmd("scene", op="add", type="wall", values={})
    assert not h.errors(), h.errors()
    assert not h.sim.md.periodic[1] and any("now has walls" in en(m["text"]) for m in h.of("event")
                                            if m.get("notify"))
    h.cmd("scene", op="add", type="piston", values={})
    assert not h.errors(), h.errors()
    X = h.sim.md.piston()["X"]
    assert np.all(h.sim.md.positions()[:, 1] <= X)
    run(h, 2.0, 4)
    assert not h.errors(), h.errors()
    assert np.all(h.sim.md.positions()[:, 1] <= h.sim.md.piston()["X"] + 1e-12)
    for o in added(h, "piston") + added(h, "wall"):
        h.cmd("scene", op="remove", id=o["id"])
    assert not h.errors() and h.sim.md.periodic[1]
    # an explicit piston position below the gas is refused with the lowest admissible one (not in English)
    h.cmd("scene", op="add", type="gas", values={"n": 30, "y": 6.0, "sy": 12.0, "x": 6.0, "sx": 12.0, "color": "1"})
    h.cmd("scene", op="add", type="piston", values={"position": 1.0})
    pist = added(h, "piston")[0]
    h.cmd("scene", op="set", id=pist["id"], values={"position": 0.5})
    assert translated(en(h.errors()[-1])) and "at least" in en(h.errors()[-1])


def test_atoms_land_on_free_spots_and_an_occupied_one_is_refused_with_the_nearest():
    """U4: the second “+ Atom” with the defaults and a copy land at least sigma from the first; an atom moved by hand
    onto another is refused, naming the nearest free spot; one moved far outside the walls likewise (U8)."""
    h = Harness(V, None, {"boundary": "walls"})
    for _ in range(2):
        h.cmd("scene", op="add", type="atom", values={})
    a = added(h, "atom")
    h.cmd("scene", op="duplicate", id=a[0]["id"])
    assert not h.errors(), h.errors()
    x = h.sim.md.positions() * NM
    d = np.sqrt(((x[:, None] - x[None]) ** 2).sum(-1)) + np.eye(len(x)) * 99
    assert len(x) == 3 and d.min() >= NM * (1 - 1e-6)
    h.cmd("scene", op="set", id=a[1]["id"], values={"x": a[0]["values"]["x"], "y": a[0]["values"]["y"]})
    assert "the nearest free place" in en(h.errors()[-1]) and translated(en(h.errors()[-1]))
    h.cmd("scene", op="set", id=a[1]["id"], values={"x": 900.0})
    assert "beyond the wall" in en(h.errors()[-1])


def test_a_crystal_in_a_gas_leaves_the_occupied_sites_empty():
    """U4 / U7: “Crystal” with its defaults in a scene with a gas was refused («overlap … 7.5e+27»); now it fills the free
    sites and says how many were left empty."""
    h = Harness(V, "maxwell")
    h.cmd("scene", op="add", type="crystal", values={})
    assert not h.errors(), h.errors()
    cr = added(h, "crystal")[0]
    assert h.sim.info[cr["id"]]["skipped"] > 0
    assert any("left empty" in en(m["text"]) for m in h.of("event") if m.get("notify"))
    run(h, 0.5, 3)
    assert not h.errors()


@pytest.mark.parametrize("op,values,limit", [
    ("set", {"shape": "chain"}, 10.0),
    ("set", {"shape": "bent"}, 3.0),
    ("set", {"start": "maxwell"}, 3.0),
    ("duplicate", None, 3.0),
    ("set", {"count": 2000}, 1.0),           # refused at once: denser than random packing
    ("set", {"shape": "chain", "atoms": 50}, 1.0),
])
def test_molecule_edits_are_quick(op, values, limit):
    """U5 / P33: in the preset «molecules» (3-D) these edits took 30 s to over 2 min (one engine edit per try); now the
    candidates go in one edit and what cannot fit is refused at once. Bounds generous for a loaded CPU (measured: 2.1 s,
    0.08 s, 0.07 s, 0.12 s, 0.006 s, 0.006 s)."""
    h = Harness(V, "molecules")
    oid = added(h, "molecule")[0]["id"]
    t0 = time.perf_counter()
    if op == "set":
        h.cmd("scene", op="set", id=oid, values=values)
    else:
        h.cmd("scene", op="duplicate", id=oid)
    assert time.perf_counter() - t0 < limit
    if values and values.get("count") == 2000 or values and values.get("atoms") == 50:
        assert translated(en(h.errors()[-1])) and "at most" in en(h.errors()[-1])
    else:
        assert not h.errors(), h.errors()
        run(h, 0.2, 2)
        assert not h.errors()


def test_a_large_gas_is_refused_at_once_with_the_count_that_fits():
    """P33: 20 000 atoms in the default 3-D box jammed for minutes; now refused at once with the count that fits;
    that count (control) is placed."""
    h = Harness(V, None, {"dim": "3d"})
    t0 = time.perf_counter()
    h.cmd("scene", op="add", type="gas", values={"n": 20000})
    assert time.perf_counter() - t0 < 1.0
    err = en(h.errors()[-1])
    assert translated(err) and "at most" in err
    import re
    n_ok = int(re.search(r"at most (\d+) atoms", err).group(1))
    h.cmd("scene", op="add", type="gas", values={"n": n_ok // 2})
    assert len(h.errors()) == 1, h.errors()


def test_live_pair_model_cutoff_and_step_keep_the_energy_balance():
    """U12: LJ -> WCA, the cutoff 2.5 -> 3.0 σ, the step 10 -> 5 fs at the current moment: the same atoms; the first-law
    residual stays at its value (the edit moves E0 by the energy it changes); the approximations follow the cutoff; the
    hard world keeps them for the forces (LB1)."""
    h = Harness(V, "maxwell")
    run(h, 1.0, 4)
    x0 = h.sim.md.positions().copy()
    h.set(model="wca")
    assert isinstance(h.sim.md.pair, type(h.sim._pair_term())) and h.sim.live["model"] == "wca"
    assert np.array_equal(h.sim.md.positions(), x0)
    assert abs(h.sim.md.energy_balance()["residual"]) < 1e-9
    h.set(model="lj", cutoff=3.0)
    assert any("3 σ" in a or "3.0 σ" in a for a in english(h.of("approximations")[-1]["approximations"]))
    h.set(dt_fs=5.0)
    assert h.sim.md.dt == pytest.approx(5e-3 / PS)
    run(h, 1.0, 4)
    assert not h.errors(), h.errors()
    assert h.of("live")[-1]["values"]["dt_fs"] == 5.0
    # the hard world keeps them for the forces (LB1: the dynamics is live): taken, said so, acting after a switch
    hard = Harness(V, "hard_disks")
    hard.set(model="wca")
    assert not hard.errors() and hard.sim.live["model"] == "wca" and hard.sim.hard
    assert "after the switch to continuous forces" in en(hard.of("event")[-1]["text"])


def test_a_cutoff_beyond_half_the_box_is_refused_in_translated():
    h = Harness(V, None, {"Lx": 2.5, "Ly": 2.5})
    h.cmd("scene", op="add", type="gas", values={"n": 5})
    h.set(cutoff=6.0)
    assert translated(en(h.errors()[-1])) and "Cutoff radius" in en(h.errors()[-1])
    assert h.sim.live["cutoff"] == 2.5


def test_charges_in_a_periodic_box_refused_in_russian_and_taken_once_walled():
    """U13 / P31: «charges in a box with a periodic axis…» was shown in English; now in Russian with the fix, which works:
    walls on both axes, then the charged gas is taken."""
    h = Harness(V)
    q = {"n": 20, "substance": "custom", "charge": 0.05}
    h.cmd("scene", op="add", type="gas", values=q)
    assert "Ewald" in en(h.errors()[-1]) and translated(en(h.errors()[-1]))
    h.cmd("scene", op="add", type="wall", values={"axis": "x"})
    h.cmd("scene", op="add", type="wall", values={"axis": "y"})
    h.cmd("scene", op="add", type="gas", values=q)
    assert len(h.errors()) == 1, h.errors()


def _world(params):
    viz = registry.load(V)
    p, errors = viz["schema"].resolve(None, params)
    assert not errors
    frames, script = [], []

    def emit(meta, blobs=None):
        if meta.get("type") == "frame":
            frames.append((meta, blobs))
            script.append({"frame": meta["t"]})
        elif meta.get("type") == "command":
            script.append({"t": meta["t"], "cmd": meta["cmd"], "args": meta["args"]})
    sim = viz["simulation"](p, 7, emit)
    return sim, Runner(sim, emit, queue.Queue()), frames, script


def test_live_laws_and_placements_are_replayed_by_a_restore():
    """The live laws and the placements (``place``, the walls that made an axis walled) are deterministic: a world
    rebuilt from the record's commands gives the same frame."""
    params = dict(registry.load(V)["schema"].presets["maxwell"]["params"])
    sim, run_, frames, script = _world(params)
    run_._start_world()
    run_._advance(0.5e-12)
    run_._frame(0.0)
    run_.handle({"cmd": "set", "args": {"values": {"model": "wca", "dt_fs": 6.0}}})
    run_.handle({"cmd": "scene", "args": {"op": "add", "type": "atom", "values": {}}})
    run_.handle({"cmd": "scene", "args": {"op": "add", "type": "wall", "values": {"kind": "thermal"}}})
    run_._advance(1.0e-12)
    run_._frame(0.0)
    sim2, run2, frames2, _ = _world(params)
    run2.restore(1, list(script)[:-1], sim.t, lambda on: None)
    run2._frame(0.0)
    a, b = frames[-1], frames2[-1]
    assert np.array_equal(a[1]["q"], b[1]["q"]) and a[0]["n"] == b[0]["n"] and a[0]["walled"] == b[0]["walled"]
    assert sim2.live == sim.live


def test_palette_state_names_a_full_box():
    h = Harness(V)
    assert h.sim.palette_state() == {}
    h.cmd("scene", op="add", type="crystal", values={"density": 1.1})
    st = h.sim.palette_state()
    assert "gas" in st and translated(en(st["gas"]))


def test_a_probe_or_a_thermostat_outside_the_walls_is_refused():
    """U8: a thermometer or a thermostat's region far outside a walled box was accepted without a word."""
    h = Harness(V, None, {"boundary": "walls"})
    h.cmd("scene", op="add", type="probe", values={})
    pid = added(h, "probe")[0]["id"]
    h.cmd("scene", op="set", id=pid, values={"x": 1000.0})
    assert "outside the box" in en(h.errors()[-1]) and translated(en(h.errors()[-1]))
    h.cmd("scene", op="add", type="thermostat", values={"x": 500.0, "y": 500.0, "sx": 1.0, "sy": 1.0})
    assert "outside the box" in en(h.errors()[-1]) and not added(h, "thermostat")


def _old_format(sc, model):
    """A scene file as p03 wrote it before 2026-11-05: one combined «model» (lj | wca | hard), no «dynamics»."""
    laws = {k: v for k, v in sc["laws"].items() if k not in ("dynamics", "model")}
    laws["model"] = model
    return {**sc, "laws": laws}


@pytest.mark.parametrize("model", ["hard", "lj", "wca"])
def test_an_old_format_scene_file_still_loads(model):
    """Scene files saved before the split of the combined «model» into «dynamics» (world) and «model» (live) load with
    the same laws and say so in a notice (“a file of the old format”): hard disks stay hard disks, LJ and WCA stay forces
    with that pair model; the objects and the box come back. Negative control: a file of the new format has no notice."""
    src = Harness(V, "hard_disks" if model == "hard" else "maxwell")
    if model == "wca":
        src.set(model="wca")
    src.cmd("scene", op="export")
    new = src.of("scene_export")[-1]["scene"]
    old = _old_format(new, model)
    params = {**old["laws"], "scene": old}
    p, errors = registry.load(V)["schema"].resolve(None, params)
    assert not errors, errors
    assert p["dynamics"] == ("hard" if model == "hard" else "forces")
    h = Harness(V, None, params)
    assert not h.errors(), h.errors()
    notes = [en(m["text"]) for m in h.of("notice")]
    assert any(t.startswith("a file of the old format") for t in notes), notes
    assert h.sim.hard == (model == "hard") and (model == "hard" or h.sim.live["model"] == model)
    assert [o["type"] for o in h.sim.objects.values()] == [o["type"] for o in new["objects"]]
    run(h, 0.3, 2)
    assert not h.errors(), h.errors()
    fresh = Harness(V, None, {**new["laws"], "scene": new})
    assert not any(en(m["text"]).startswith("a file of the old format") for m in fresh.of("notice"))



def _lj(dim=2, box=(10.0, 10.0), boundary="walls"):
    from lfphys.core.md.system import MD
    from lfphys.theories.models import interatomic as IA
    m = MD(dim=dim, box=box, boundary=boundary, pair=IA.LennardJones(2.5))
    m.add_species("A")
    return m


def _hard(boundary="walls", sigma=1.0):
    from lfphys.core.md.hard import HardSpheres
    h = HardSpheres(2, (10.0, 10.0), boundary)
    h.add_species("A", sigma=sigma)
    return h


def _piston(m):
    m.fill("A", n=4, arrangement="random", region=((0.5, 0.5), (4.0, 4.0)))
    m.set_piston(1, X=8.0, mass=10.0)
    return m


def _molecules_stretched():
    h = Harness(V, "molecules")
    md = h.sim.md
    return lambda: md.deform(np.asarray(md.L) * np.array([1.2] + [1.0] * (md.dim - 1)), mode="affine",
                             max_bond_strain=0.1)


# code -> (a call that triggers it in the engine, the world's msgid). Review i18n-code F5: the world matches the
# engine's machine code, never its wording; each mapping is triggered here.
CODE_CASES = {
    "md.jammed": (lambda: _lj().fill("A", n=1000, arrangement="random"),
                  "only {k:d} of {n:d} atoms could be placed without overlaps"),
    "md.overlap": (lambda: (lambda m: (m.add("A", [[5.0, 5.0]]), m.add("A", [[5.0, 5.05]])))(_lj()),
                   "the new atoms would lie on those already there (insertion energy {e:.3g} ε at the limit {lim:.3g} ε)"),
    "md.refused/md.same_point": (lambda: (lambda m: (m.add("A", [[5.0, 5.0]]), m.add("A", [[5.0, 5.0]])))(_lj()),
                                 "two atoms would be at the same point"),
    "md.hard_overlap": (lambda: _hard().add("A", [[5.0, 5.0], [5.2, 5.0]]), "hard disks (spheres) would overlap"),
    "md.region": (lambda: _lj().fill("A", n=3, region=((5.0, 5.0), (4.0, 4.0)), arrangement="random"),
                  "the object's region lies outside the box (nothing of it is left inside the walls)"),
    "md.outside_walls": (lambda: (lambda m: (m.fill("A", n=20, arrangement="random", T=1.0),
                                             m.deform((3.0, 10.0), mode="wall")))(_lj()),
                         "an atom would be beyond the wall on the axis {a}"),
    "md.cutoff": (lambda: (lambda m: (m.fill("A", n=4, arrangement="random"), m.deform((4.0, 10.0))))(
                      _lj(boundary="periodic")),
                  "the cutoff radius with its margin ({rc:.3g} nm) exceeds half the periodic box ({half:.3g} nm)"),
    "md.ewald": (lambda: (lambda m: (m.add_species("Q", charge=1.0), m.fill("Q", n=2, arrangement="random")))(
                     _lj(boundary="periodic")),
                 "charges in a box with a periodic axis are not supported (the Ewald sum is not implemented)"),
    "md.hard_box": (lambda: _hard("periodic", sigma=3.0).fill("A", n=1),
                    "the periodic box is shorter than four diameters of the largest atom ({d:.3g} nm)"),
    "md.piston/axis": (lambda: _piston(_lj()).deform((10.0, 9.0)),
                       "along the axis {a} the piston sets the volume: the box does not change affinely along it"),
    "md.piston/face": (lambda: _piston(_lj()).deform((10.0, 7.0), mode="wall"),
                       "the piston stands at {x:.4g} nm, above the new upper wall"),
    "md.piston/hi side": (lambda: _piston(_lj()).set_wall(1, "hi", "specular"),
                          "the upper side of this axis is the piston"),
    "md.piston/x_min": (lambda: _lj().set_piston(1, X=20.0, mass=10.0), "the piston's position is outside the box"),
    "md.periodic_axis": (lambda: (lambda m: (m.fill("A", n=4, arrangement="random"),
                                             m.deform((12.0, 10.0), mode="wall")))(_lj(boundary="periodic")),
                         "the axis {a} is periodic: there is no wall to move"),
    "md.bond_strain": (None, "the molecules' bonds would stretch or shrink by {p:.3g} % (the limit is {lim:.3g} % per "
                             "change: the atoms move with the box, and so do the bonds)"),
    "md.no_free_site": (lambda: (lambda m: (m.fill("A", density=0.5, region=((2, 2), (8, 8))),
                                            m.fill("A", density=0.5, region=((2, 2), (8, 8)), skip_occupied=True)))(_lj()),
                        "all the crystal's sites are taken by atoms already there"),
    "md.lattice_cell": (lambda: _lj().fill("A", density=0.01, region=((4, 4), (5, 5))),
                        "the crystal's region is smaller than one lattice cell at this density"),
    "md.non_finite": (lambda: _lj().add("A", [[5.0, 5.0]], v=[[float("nan"), 0.0]]),
                      "the forces became infinite (atoms too close)"),
    "md.thermal_wall": (lambda: _lj().set_wall(1, "lo", "thermal", T=0.0), "a thermal wall needs a temperature above 0 K"),
}


@pytest.mark.parametrize("case", sorted(CODE_CASES))
def test_each_engine_code_maps_to_the_worlds_text(case):
    """Review i18n-code F5: p03 puts the engine's refusals (``core.md``) into its own terms by their machine code
    (``lfphys.codes``), with the numbers from ``data_of``. Each mapping of ``_MD`` is triggered in the engine here: the
    code (for a refused transactional edit, its cause) and the world's msgid with its numbers, translated."""
    from lfphys.codes import code_of
    from p03_molecules import viz as P3
    code = case.split("/")[0] if not case.startswith("md.refused") else "md.refused"
    trigger, msgid = CODE_CASES[case]
    if trigger is None:
        trigger = _molecules_stretched()
    with pytest.raises(Exception) as info:
        trigger()
    e = info.value
    assert code_of(e) == code, (code_of(e), str(e))
    if code == "md.refused":
        assert P3._cause(e) == "md.same_point"
    r = text_of(P3._owner(e))
    assert r["$t"] == "{text}. What to change: {hint}", r      # the world's text with its hint
    t = r["a"]["text"]
    assert t["$t"] == msgid, t
    assert "{" not in english(t) and translated(t), english(t)
    assert set(t.get("a") or {}) == {k for k in re.findall(r"\{(\w+)", msgid)}


def test_every_md_mapping_has_a_test():
    from p03_molecules import viz as P3
    tested = {c.split("/")[0] for c in CODE_CASES} | {"md.same_point"}
    assert set(P3._MD) <= tested, set(P3._MD) - tested


def test_a_failed_verlet_step_names_the_reason_in_the_owners_words():
    """Language review F11: the reason inside «the Verlet step failed ({why})» was the engine's English
    («non-finite forces»); it is the world's own text for a mapped code, else the engine's translatable text."""
    from lfphys.codes import coded
    from p03_molecules import viz as P3
    assert english(P3._why(coded(FloatingPointError(T_("non-finite forces")), "md.non_finite"))) \
        == "the forces became infinite (atoms too close)"
    assert english(P3._why(coded(FloatingPointError(T_("a FENE bond stretched to R0 (the bond broke)")),
                                 "md.bond_broke"))) == "a FENE bond stretched to R0 (the bond broke)"
