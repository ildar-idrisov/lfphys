# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""p03: the particles-and-molecules playground. Every preset builds, runs and keeps its laws, and shows what its label
says, measured in the run (review B7-md M2–M5): the crystal melts at 120 K (ψ6 falls, the atoms diffuse; at 20 K it
stays), liquid and vapour coexist in 3-D at 90 K with NIST's densities (at 120 K, above the model's critical point,
they do not), collisions share the molecules' energy among translation, rotation and vibration, the hard disks' Z
agrees with the equation of state; the wrapper's units against argon's; a gas started with equal speeds becomes
Maxwellian by itself; molecules carry their bonds and start at their temperature; a change of the substance keeps the
same atoms at the same temperature while a change of their number makes new ones; a refused change leaves the world
bit for bit as it was (M6); removing the first object (M7); the momentum check (M8); the piston kept where it is (M12);
the hard world's edits (M5); the texts (M16, M19, M20); the scene file. The engine's physics is tested in
``lfphys/tests/test_md*.py``; the shared tests continue every world from its checkpoint byte for byte and rebuild it by
replay."""

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from p03_molecules import viz as P3  # noqa: E402
from p03_molecules.viz import KELVIN, NM, PS, SCHEMA, U  # noqa: E402

V = "p03_molecules"
HARD = importlib.util.find_spec("lfphys.core.md.hard") is not None


def run(h, ps, n=10):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + ps * 1e-12 * k / n)
        h.runner._frame(0.0)


def failed(h):
    return [c["id"] for c in h.checks().values() if c.get("ok") is False]


def stats_after(h, t_ps):
    return [m for m in h.of("stats") if m["t"] >= t_ps * 1e-12]


@pytest.mark.parametrize("preset", list(SCHEMA.presets))
def test_every_preset_builds_runs_and_keeps_its_laws(preset):
    if SCHEMA.presets[preset]["params"].get("dynamics") == "hard" and not HARD:
        pytest.skip("hard spheres not in the engine yet")
    h = Harness(V, preset)
    run(h, 4.0)
    assert not h.errors(), h.errors()
    assert not failed(h), {k: h.checks()[k] for k in failed(h)}
    assert h.of("stats") and h.of("frame")[-1]["n"] > 0


def test_argon_units():
    """σ = 3.405 Å, ε/k = 119.8 K, m = 39.948 u: τ = σ √(m/ε) = 2.156 ps; the 3-D pressure unit ε/σ³ = 418.9 bar."""
    assert NM == pytest.approx(0.3405, rel=1e-12)
    assert KELVIN == pytest.approx(119.8, rel=1e-12)
    m = 39.948 * 1.66053906892e-27
    eps = 119.8 * 1.380649e-23
    assert PS == pytest.approx(3.405e-10 * math.sqrt(m / eps) * 1e12, rel=1e-9)
    assert PS == pytest.approx(2.156, abs=1e-3)
    assert U.to_bar(1.0) == pytest.approx(eps / 3.405e-10 ** 3 / 1e5, rel=1e-9)


def test_equal_speeds_become_maxwellian():
    """The Maxwell preset starts every atom with one speed (the KS distance from the Gaussian is then large); collisions
    make the velocity components Gaussian within the DKW bound — a consequence computed by the run. The gas starts at
    random places (review B7-md M17): no two atoms share a coordinate, none nearer than σ."""
    h = Harness(V, "maxwell")
    v = np.asarray(h.sim.md.velocities())
    speeds = np.linalg.norm(v, axis=1)
    assert np.ptp(speeds) / speeds.mean() < 0.3  # nearly one speed at the start (the momentum removed)
    assert h.sim.md.velocity_ks()["within"] is False
    x = h.sim.md.positions()
    assert len(np.unique(np.round(x[:, 0], 9))) == len(x) and len(np.unique(np.round(x[:, 1], 9))) == len(x)
    d = x[:, None] - x[None]
    d -= h.sim.md.L * np.rint(d / h.sim.md.L)
    assert (np.sqrt((d * d).sum(-1)) + 9 * np.eye(len(x))).min() >= 1.0 - 1e-12
    run(h, 20.0, 20)
    ks = h.sim.md.velocity_ks()
    assert ks["within"], ks


def test_the_crystal_melts_at_120_K_and_stays_at_20_K():
    """Review B7-md M3. The preset's crystal (a perfect triangular lattice of ρσ² = 0.85, the box holding 25 x 15 cells)
    heated by a CSVR bath to 120 K = 1.00 ε/k: at T = 1.0 the 2-D LJ (2.5σ) fluid exists below ρ ≈ 0.896 (Li & Pica
    Ciamarra 2020), so it must melt. Measured in the run (the stats the player draws): the bond-orientational order
    |⟨ψ6⟩| falls from 1 to below 0.3 on average over 40–60 ps (it was 0.44 at 20 ps, 0.07–0.29 later; a liquid of
    750 atoms) and the atoms
    diffuse (MSD over the last 30 ps above 1 σ²: ~1.6 σ² per 20 ps measured). Negative control: the same crystal with
    the bath at 20 K keeps |⟨ψ6⟩| above 0.85 and its MSD below 0.1 σ² (0.02 measured)."""
    h = Harness(V, "melting")
    assert h.sim.info["o1"]["density"] == pytest.approx(0.85, rel=1e-3) and h.sim.info["o1"]["strain"] < 1e-4
    run(h, 30.0, 30)
    h.sim.md.msd_origin()
    run(h, 30.0, 30)
    s = stats_after(h, 40.0)
    T = h.sim.md.temperature()["T"] * KELVIN
    assert abs(T - 120.0) < 15.0, T          # CSVR: relative spread √(2/1498) = 3.7 %, ±4.4 K; four of them + drift
    assert np.mean([m["order"] for m in s]) < 0.3, [m["order"] for m in s]
    assert h.sim.md.msd()["msd"] > 1.0
    c = Harness(V, "melting")
    c.cmd("scene", op="set", id="o2", values={"T": 20.0})
    run(c, 40.0, 40)
    assert min(m["order"] for m in stats_after(c, 10.0)) > 0.85
    assert c.sim.md.msd()["msd"] < 0.1


def _profile(h, t_from, t_to, every=5.0):
    run(h, t_from, int(t_from))
    md = h.sim.md
    nb = int(round(md.L[1]))
    prof = []
    for _ in range(int((t_to - t_from) / every)):
        run(h, every, 2)
        cnt, _ = np.histogram(md.positions()[:, 1], bins=nb, range=(0, md.L[1]))
        prof.append(cnt / (md.L[0] * md.L[2] * md.L[1] / nb))
    return np.mean(prof, axis=0)


def test_liquid_and_vapour_coexist_at_90_K_not_at_120_K():
    """Review B7-md M2. In 3-D the force-shifted LJ (2.5σ) has T_c = 0.937 ε/k = 112 K and its triple point at
    0.560 (Errington, Debenedetti & Torquato 2003; NIST SRS): at 90 K = 0.751 ε/k NIST's coexisting densities are
    ρ_liq = 0.693 and ρ_vap = 0.032. The preset's density profile along the field, averaged over 40–100 ps: a liquid
    plateau within 10 % of 0.693, a vapour (the upper third) below 0.06 (measured 0.02: gravity and 25 vapour atoms),
    a step of more than 0.15 between neighbouring σ-slabs (0.28 measured); the liquid is not a crystal (Q6 below 0.1).
    Negative control: the same scene with the bath at 120 K (above T_c) gives a graded fluid without a liquid plateau
    and with a denser top (measured over 100–200 ps: max 0.47, upper third 0.14, steps ≤ 0.10)."""
    h = Harness(V, "liquid_vapour")
    m = _profile(h, 40.0, 100.0)
    assert 0.62 < m.max() < 0.76, m
    top = m[-len(m) // 3:]
    assert top.mean() < 0.06 and top.mean() > 0.002, m
    assert np.max(np.abs(np.diff(m))) > 0.15, m
    assert stats_after(h, 90.0)[-1]["order"] < 0.1
    c = Harness(V, "liquid_vapour")
    c.cmd("scene", op="set", id="o2", values={"T": 120.0})
    mc = _profile(c, 40.0, 100.0)
    assert mc.max() < 0.6 and mc[-len(mc) // 3:].mean() > 0.06, mc


def test_molecules_share_their_energy_among_the_modes():
    """Review B7-md M4. The preset's dimers start with translation only (400 K: every molecule moves as a whole at a
    Maxwellian velocity of its mass, rest geometry: rotation and vibration at 0 K). Collisions share the energy: after
    20 ps the temperatures of translation, rotation, the vibration's kinetic energy and the bonds' potential energy
    (molecule_modes, shown in the inspector and the chart) agree within 15 % of their mean (measured: all within a
    few % of ~199 K from 10 ps on; the statistical spread of each over 150 molecules is ~5–8 %), averaged over 20–40
    ps. Negative control: at the start rotation and vibration are at 0."""
    h = Harness(V, "molecules")
    mm0 = h.sim.md.molecule_modes()
    assert mm0["rotation"]["T"] < 1e-12 and mm0["vibration"]["T"] < 1e-12 and mm0["bonds"]["T"] < 1e-12
    assert mm0["translation"]["T"] * KELVIN > 300
    run(h, 20.0, 10)
    rows = []
    for _ in range(10):
        run(h, 2.0, 1)
        mm = h.sim.md.molecule_modes()
        rows.append([mm[p]["T"] * KELVIN for p in ("translation", "rotation", "vibration", "bonds")])
    r = np.mean(rows, axis=0)
    assert np.all(np.abs(r / r.mean() - 1) < 0.15), r
    now = h.of("frame")[-1]["now"]["o1"]
    assert "T вращат., K" in now and "T колебат. (кин.), K" in now
    assert any(m.get("modes") for m in h.of("stats"))


def test_molecules_start_at_their_temperature():
    """Review B7-md M4: "всё при T" gives every atom a Maxwell velocity at T (translation included) and thermal bond
    lengths; the object's momentum is removed; atoms are placed without overlaps (each one's energy at its insertion
    below 2kT). At 200 K the kinetic temperature at t = 0 is within 15 % of 200 K (spread √(2/900) = 4.7 % for 300
    atoms; the reviewed start gave 84 K)."""
    h = Harness(V, "molecules")
    h.cmd("scene", op="set", id="o1", values={"start": "maxwell", "T": 200.0})
    md = h.sim.md
    assert not h.errors()
    T0 = md.temperature()["T"] * KELVIN
    assert abs(T0 - 200.0) < 30.0, T0
    assert np.allclose(md.momentum(), 0.0, atol=1e-10)
    pe = md._per_particle_energy()
    assert pe.max() < 4.0 * 200.0 / KELVIN, pe.max()          # the reviewed placement: up to 23 ε = 14 kT


def test_hard_disks_against_the_equation_of_state():
    """Review B7-md M5. The hard-disk world shows its pressure (the collision virial) and checks Z against Kolafa &
    Rottner's equation of state with the ensemble correction for N = 400 (1.8045 at ρσ² = 0.322), from blocks of at
    least 2.2 ps after 10.8 ps: over 100 ps (25 blocks; measured Z = 1.807, tolerance 5 SE + 1e-4 = 0.029) it passes.
    Negative control: the same run against the reference at a density 5 % higher (1.8686, ΔZ = 0.064) fails."""
    if not HARD:
        pytest.skip("hard spheres not in the engine yet")
    h = Harness(V, "hard_disks")
    run(h, 100.0, 600)
    assert all(m["p"] is not None for m in h.of("stats"))
    c = h.checks()["eos"]
    assert c["ok"] is True and c["value"] is not None, c
    from lfphys.core.md import hard as HD
    zr = HD.z_reference

    def shifted(dim, rho):
        return zr(dim, rho * 1.05)
    HD.z_reference = shifted
    try:
        h.sim._z_check()
    finally:
        HD.z_reference = zr
    bad = [m for m in h.of("check") if m["id"] == "eos"][-1]
    assert bad["ok"] is False, bad


def test_the_hard_world_edits_and_its_crystal():
    """Review B7-md M5: in the hard world a change of an object's number makes its atoms anew (the species is reused);
    a crystal in a region counts its atoms over the region; disks are drawn with their own species."""
    if not HARD:
        pytest.skip("hard spheres not in the engine yet")
    h = Harness(V, "hard_disks")
    h.cmd("scene", op="set", id="o1", values={"n": 300})
    assert not h.errors() and h.sim.md.n == 300
    h = Harness(V, None, {"dim": "2d", "dynamics": "hard", "Lx": 12.0, "Ly": 12.0, "boundary": "periodic"})
    h.cmd("scene", op="add", type="crystal", values={"density": 0.7, "T": 300.0, "x": 6.0, "y": 6.0, "sx": 3.0,
                                                     "sy": 3.0, "color": "2"})
    assert not h.errors()
    oid = [k for k, o in h.sim.objects.items() if o["type"] == "crystal"][0]
    n = len(h.sim.parts[oid])
    assert 0.5 * 0.7 * (3.0 / NM) ** 2 < n <= 0.7 * (3.0 / NM) ** 2
    h.runner._frame(0.0)
    blobs = [b for m, b in h.msgs if m.get("type") == "frame"][-1]
    assert len(set(blobs["sp"].tolist())) >= 1 and h.of("frame")[-1]["species_colors"][-1] == P3.COLORS[2]


def test_molecules_carry_their_bonds():
    h = Harness(V, "molecules")
    topo = h.sim.md.topology()
    assert len(topo["bonds"]) == 150 and len(topo["angles"]) == 0
    h.runner._frame(0.0)
    blobs = [b for m, b in h.msgs if m.get("type") == "frame"][-1]
    assert len(blobs["bonds"]) == 2 * 150  # every bond drawn between its two atoms


def test_a_substance_change_keeps_the_atoms_and_their_temperature():
    """Review B7-md M14: the same atoms with a new mass at the same temperature (velocities × √(m/m′)); a change of
    their number makes new ones."""
    h = Harness(V, "maxwell")
    run(h, 1.0, 2)
    keys0 = np.array(h.sim.parts["o1"])
    K0 = h.sim.md.kinetic_energy()
    h.cmd("scene", op="set", id="o1", values={"substance": "custom", "mass": 80.0})
    assert np.array_equal(np.array(h.sim.parts["o1"]), keys0)
    assert h.sim._sp("o1")["mass"] == pytest.approx(U.from_amu(80.0))
    assert h.sim.md.kinetic_energy() == pytest.approx(K0, rel=1e-12)
    h.cmd("scene", op="set", id="o1", values={"n": 100})
    assert len(h.sim.parts["o1"]) == 100 and not h.errors()


def test_a_refused_change_leaves_the_scene_as_it_was():
    h = Harness(V, "melting")
    before = [o["id"] for o in h.of("scene")[-1]["objects"]]
    n0 = h.sim.md.n
    h.cmd("scene", op="add", type="gas", values={"n": 5000, "T": 100.0})  # no room left in a crystal-filled box
    assert h.errors()
    assert [o["id"] for o in h.of("scene")[-1]["objects"]] == before and h.sim.md.n == n0


def _arrays_equal(a, b):
    for k in a:
        if isinstance(a[k], np.ndarray):
            if not np.array_equal(a[k], b[k]):
                return False
        elif k not in ("stats",) and repr(a[k]) != repr(b[k]):
            return False
    return True


def _gas_and_crystal():
    h = Harness(V, None, {"dim": "2d", "model": "lj", "Lx": 12.0, "Ly": 12.0, "boundary": "periodic"})
    h.cmd("scene", op="add", type="crystal", values={"density": 0.8, "T": 30.0, "x": 3.0, "y": 6.0, "sx": 5.0,
                                                     "sy": 11.0})
    h.cmd("scene", op="add", type="gas", values={"n": 60, "T": 100.0, "x": 9.0, "y": 6.0, "sx": 5.0, "sy": 11.0})
    assert not h.errors()
    return h


@pytest.mark.parametrize("case", ["count", "overlap"])
def test_a_refused_set_leaves_the_world_bit_for_bit(case):
    """Review B7-md M6: a refused change of a particle object used to delete its atoms. "count": 5000 atoms do not
    fit the preset's box (refused at once: denser than random insertion allows); "overlap": the crystal made of atoms
    twice as large at a density 1.3 overlaps itself (the engine refuses the insertion after the old atoms were
    removed; a crystal made to fill the whole box no longer overlaps the gas: it leaves the occupied sites empty,
    review UX-ui U4). Now the engine's state is as before bit for bit, the wrapper keeps the object's
    atoms, and the world continues exactly as a twin that never saw the command."""
    if case == "count":
        h, twin, values = Harness(V, "maxwell"), Harness(V, "maxwell"), {"n": 5000}
    else:
        h, twin, values = _gas_and_crystal(), _gas_and_crystal(), {"density": 1.3, "substance": "custom",
                                                                         "sigma": 2.0}
    run(h, 1.0, 2)
    run(twin, 1.0, 2)
    st = h.sim.md.state_dict()
    parts = {k: np.array(v) for k, v in h.sim.parts.items()}
    ne = len(h.errors())
    h.cmd("scene", op="set", id="o1", values=values)
    assert len(h.errors()) == ne + 1, h.errors()
    assert _arrays_equal(st, h.sim.md.state_dict())
    assert all(np.array_equal(parts[k], np.array(v)) for k, v in h.sim.parts.items())
    run(h, 1.0, 2)
    run(twin, 1.0, 2)
    assert np.array_equal(h.sim.md.positions(True), twin.sim.md.positions(True))


def test_refused_molecules_leave_none_behind():
    """Review B7-md M6: molecules that do not all fit are refused as a whole (no partial set of them stays)."""
    h = Harness(V, None, {"dim": "2d", "model": "lj", "Lx": 2.5, "Ly": 2.5, "boundary": "periodic"})
    h.cmd("scene", op="add", type="molecule", values={"count": 40, "T": 100.0})
    assert h.errors() and h.sim.md.n == 0 and not h.sim.objects


def test_removing_the_first_object_keeps_the_world_running():
    """Review B7-md M7: the KS check pools every species (each by its own mass): removing the first particle object
    while another stays no longer stops the frames."""
    h = Harness(V, None, {"dim": "2d", "model": "lj", "Lx": 12.0, "Ly": 12.0, "boundary": "periodic"})
    h.cmd("scene", op="add", type="gas", values={"n": 100, "T": 300.0, "x": 3.0, "y": 6.0, "sx": 5.0, "sy": 11.0})
    h.cmd("scene", op="add", type="gas", values={"n": 100, "T": 300.0, "x": 9.0, "y": 6.0, "sx": 5.0, "sy": 11.0,
                                                 "substance": "custom", "mass": 4.0})
    run(h, 1.0, 20)
    assert h.sim.md.velocity_ks()["n"] == 400
    h.cmd("scene", op="remove", id="o1")
    run(h, 1.0, 20)
    assert not h.errors() and h.sim.md.velocity_ks()["n"] == 200


def test_the_momentum_check_tests_conservation():
    """Review B7-md M8: an atom launched at 400 m/s into the NVE preset: P is not zero but conserved; the check
    compares the change of P since the last edit with its rounding bound and passes. Negative control: a velocity
    changed behind the engine's back (1e-7) fails it."""
    h = Harness(V, "maxwell")
    run(h, 1.0, 5)
    x = h.sim.md.positions() * NM
    grid = [(gx, gy) for gx in np.arange(0.3, 12.0, 0.37) for gy in np.arange(0.3, 12.0, 0.41)]
    gx, gy = max(grid, key=lambda p: np.min(np.hypot(*(((x - p) + 6.0) % 12.0 - 6.0).T)))   # the emptiest place
    h.cmd("scene", op="add", type="atom", values={"x": float(gx), "y": float(gy), "vx": 400.0, "vy": 0.0})
    assert not h.errors() and abs(h.sim.md.momentum()[0]) > 1.0
    run(h, 4.0, 40)
    c = h.checks()["momentum"]
    assert c["ok"] is True and c["value"] <= 1.0, c
    h.sim.md._v[0, 1] += 1e-7
    h.sim.checks()
    assert h.checks()["momentum"]["ok"] is False


def test_a_piston_edit_leaves_the_piston_where_it_is():
    """Review B7-md M12: an edit of the external pressure acts on the piston where it is (it used to jump back to its
    initial position); an edit of the position moves it."""
    h = Harness(V, "piston")
    run(h, 15.0, 15)
    oid = [k for k, o in h.sim.objects.items() if o["type"] == "piston"][0]
    X = h.sim.md.piston()["X"]
    assert X * NM < 9.5
    h.cmd("scene", op="set", id=oid, values={"p_ext": 40.0})
    assert h.sim.md.piston()["X"] == X and not h.errors()
    h.cmd("scene", op="set", id=oid, values={"position": 11.0})
    assert h.sim.md.piston()["X"] * NM == pytest.approx(11.0, rel=1e-12)


def test_texts_state_the_limits():
    """Review B7-md M16, M19, M20: the approximations name Θ_D = 85 K with the Debye heat capacity, the model's
    critical temperature and the bond's ħω/k; the field's unit is ε/(mσ) = 7.3·10¹³ m/s²; W is the piston's work."""
    h = Harness(V, "molecules")
    ap = " ".join(h.of("header")[-1]["approximations"])
    assert "85 K" in ap and "0.47" in ap
    assert "112 K" in ap and "ħω/k = 35 K" in ap
    assert P3.debye_cv_fraction(20, 85) == pytest.approx(0.467, abs=0.002)
    assert P3.einstein_cv_fraction(1e6, 100) == pytest.approx(1.0, abs=1e-6)
    help_g = P3.palette(2, "lj")["gravity"].schema.params[0].help
    assert "7,3·10¹³" in help_g
    g = U.velocity_m_s / U.to_ps(1.0) / 1e-12
    assert g == pytest.approx(7.32e13, rel=2e-3)
    h2 = Harness(V, "piston")
    run(h2, 1.0, 20)
    note = h2.checks()["energy"]["note"]
    assert "работа W" in note and "поршень" in note and "изменения ящика" in note


def test_the_scene_file_starts_the_same_set_up():
    h = Harness(V, "piston")
    run(h, 1.0, 2)
    h.cmd("scene", op="export")
    sc = h.of("scene_export")[-1]["scene"]
    h2 = Harness(V, None, {**sc["laws"], "scene": sc})
    a = [(o["type"], o["label"], o["values"]) for o in h.sim.objects.values()]
    b = [(o["type"], o["label"], o["values"]) for o in h2.sim.objects.values()]
    assert a == b and h2.sim.md.n == h.sim.md.n
