# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Molecular dynamics (plan P8): thermodynamics and statistical mechanics against closed forms - the ideal gas on
walls, equipartition, Maxwell-Boltzmann, the canonical kinetic energy under CSVR and Langevin, the heat of thermal
walls (kinetic theory of a Knudsen gas), pistons and the first law, local baths, the barometric law, diffusion of a
Langevin particle. Each tolerance is derived from the statistics (or a measured seed spread, stated); negative
controls show that the same measurement rejects a wrong reference."""

import math

import numpy as np
import pytest

from lfphys.core.md import observables as ob
from lfphys.core.md.system import MD
from lfphys.theories.models.interatomic import LennardJones


def test_ideal_gas_wall_pressure():
    """Non-interacting particles between specular walls: the momentum given to each wall per area and time is the
    kinetic theory's 2 K_a / V (the momentum flux m v_a^2 per volume), so their mean is N k T / V. Each particle's
    flux is periodic (exact free flight), so the time average converges as 1/t: measured within 6e-4 at t = 150;
    tolerance 3e-3. Negative control: N k T' / V with T' = 1.01 T is rejected (the walls resolve 1 % of T)."""
    md = MD(dim=2, box=(10, 10), boundary="walls", pair=None, dt=0.1, seed=1)
    md.add_species("A")
    md.fill("A", n=3000, T=1.3)
    md.reset_counters()
    md.step(1500)
    p = md.pressure()
    V = md.volume()
    kt = md.kinetic_tensor()
    for k, pw in p["walls"].items():
        a = "xy".index(k[0])
        assert abs(pw / (kt[a] / V) - 1) < 3e-3, (k, pw, kt[a] / V)
    T = md.temperature()["T"]
    mean = float(np.mean(list(p["walls"].values())))
    assert abs(mean / (md.n * T / V) - 1) < 3e-3
    assert abs(mean / (md.n * 1.01 * T / V) - 1) > 5e-3
    assert p["virial"] == pytest.approx(md.n * T / V, rel=1e-12)   # no interactions: only the kinetic part


def test_equipartition_between_species():
    """A binary LJ fluid (masses 1 and 4, NVE): the mean kinetic energy per particle and per Cartesian component is
    T/2 for both species - the species temperatures agree within 3 combined block standard errors. Negative control:
    equal mean speeds (<v^2> equal) are rejected - the measured <v^2> ratio is the mass ratio 4."""
    md = MD(dim=3, box=(8, 8, 8), pair=LennardJones(2.5, "force"), dt=0.004, seed=6)
    md.add_species("A")
    md.add_species("H", mass=4.0)
    md.fill("A", n=150, T=1.0, region=([0, 0, 0], [8, 8, 4]))
    md.fill("H", n=150, T=1.0, region=([0, 0, 4], [8, 8, 8]))
    md.step(2000)
    ta, th, comp = [], [], []
    for _ in range(400):
        md.step(25)
        ta.append(md.temperature("A")["T"])
        th.append(md.temperature("H")["T"])
        v = md.velocities()
        m = np.where(np.array(md.particles()["species"]) == "H", 4.0, 1.0)
        comp.append(np.mean(m[:, None] * v * v, axis=0))
    (a, sa), (h, sh) = ob.block_average(ta), ob.block_average(th)
    assert abs(a - h) < 3 * math.hypot(sa, sh), (a, sa, h, sh)
    comp = np.array(comp)
    for c in range(3):
        mc, sc = ob.block_average(comp[:, c])
        assert abs(mc - (a + h) / 2) < 3 * math.hypot(sc, sa, sh)
    ratio_v2 = (a / 1.0) / (h / 4.0)          # <v^2>_A / <v^2>_H
    assert abs(ratio_v2 - 4.0) < 0.2 and abs(ratio_v2 - 1.0) > 2.0


def test_maxwell_boltzmann_velocity_distribution():
    """Langevin bath at T = 1.2 (LJ fluid, 3-D): the velocity components of decorrelated snapshots (2 time units =
    4 / gamma apart) follow N(0, T/m): the KS distance is within the DKW bound at alpha = 0.01; so do the speeds
    against Maxwell's distribution. Negative control: the same sample against T' = 1.1 T exceeds the bound."""
    md = MD(dim=3, box=(8, 8, 8), pair=LennardJones(2.5, "force"), dt=0.005, seed=5)
    md.add_species("A")
    md.fill("A", n=300, T=1.2)
    md.add_thermostat("langevin", T=1.2, gamma=2.0)
    md.step(1000)
    vs = []
    for _ in range(25):
        md.step(400)
        vs.append(md.velocities())
    v = np.concatenate(vs)
    r = ob.ks_gaussian(v.reshape(-1), math.sqrt(1.2))
    assert r["within"], r
    sp = np.sqrt(np.einsum("ij,ij->i", v, v))
    rs = ob.ks_cdf(sp, lambda s: ob.speed_cdf(s, math.sqrt(1.2), 3))
    assert rs["within"], rs
    assert not ob.ks_gaussian(v.reshape(-1), math.sqrt(1.32))["within"]
    # the system's own helper (species, measured T)
    assert md.velocity_ks()["n"] == 900


@pytest.mark.parametrize("kind", ["csvr", "langevin"])
def test_thermostats_sample_the_canonical_kinetic_energy(kind):
    """CSVR (Bussi et al. 2007) and Langevin (BAOAB): the kinetic energy of N_f quadratic degrees of freedom is
    Gamma(N_f/2, kT) distributed (N_f = 2N - 2 for the global CSVR in a periodic box: momentum conserved; 2N for
    Langevin). 2000 samples 0.1 time units apart (2 tau for CSVR; 0.5/gamma for Langevin): KS within the DKW bound
    (alpha = 0.01); mean and variance within 4 standard errors (the variance's from the gamma fourth moment, inflated
    x1.5 for residual correlation). Negative control: NVE (velocity Verlet alone) - its K distribution is far
    narrower (microcanonical) and fails the KS test against the gamma law."""
    T = 1.5

    def run(k):
        md = MD(dim=2, box=(10.3, 10.3), pair=LennardJones(2.5, "force"), dt=0.005, seed=4)
        md.add_species("A")
        md.fill("A", n=64, T=T)
        if k == "csvr":
            md.add_thermostat("csvr", T=T, tau=0.05)
        elif k == "langevin":
            md.add_thermostat("langevin", T=T, gamma=5.0)
        else:
            md.add_thermostat("csvr", T=T, tau=0.05)
            md.step(2000)
            md.remove_thermostat(0)
        md.step(2000)
        K = []
        for _ in range(2000):
            md.step(20)
            K.append(md.temperature()["K"])
        return np.array(K), md.dof()[0]

    K, nf = run(kind)
    assert nf == (126 if kind == "csvr" else 128)
    g = ob.kinetic_energy_gamma(nf, T)
    assert ob.ks_cdf(K, g.cdf)["within"]
    n = len(K)
    assert abs(K.mean() - g.mean()) < 4 * 1.5 * g.std() / math.sqrt(n)
    var_se = g.var() * math.sqrt((2 + 6 / (nf / 2)) / n)    # Var of the sample variance: (mu4 - sigma^4)/n
    assert abs(K.var() - g.var()) < 4 * 1.5 * var_se
    if kind == "csvr":
        Kn, nfn = run("nve")
        assert not ob.ks_cdf(Kn, ob.kinetic_energy_gamma(nfn, T).cdf)["within"]
        assert Kn.var() < 0.5 * g.var()


def test_thermal_walls_deliver_the_kinetic_theory_heat():
    """A Knudsen gas (non-interacting particles) between thermal walls at T1 = 1 and T2 = 2 (2-D, periodic along y).
    Closed form (renewal-reward over a round trip): a particle emitted by a wall carries (d+1)/2 kT (kT normal - the
    flux-weighted Maxwellian - and kT/2 per tangential axis) and crosses the gap L in L/v with <1/v>_flux =
    sqrt(pi m / 2kT), so the hot wall's heat rate is N (d+1)(T2 - T1) / (2 L sqrt(pi m/2k) (T1^-1/2 + T2^-1/2)).
    Measured over 8000 time units after 1000 of relaxation: the seed-to-seed spread of the ratio is 0.35 % (four seeds: 0.9984,
    0.9957, 1.0038, 1.0010; the heavy tail of slow particles' flight times makes block errors underestimate it);
    tolerance 1.5 %. The walls' heats cancel in the steady state. Negative control: the equipartition guess d/2 kT per
    emitted particle (the time-weighted, not flux-weighted, energy) is off by 50 %."""
    d, L, T1, T2 = 2, 10.0, 1.0, 2.0
    md = MD(dim=d, box=(L, 5.0), boundary=["walls", "periodic"], pair=None, dt=0.5, seed=3)
    md.add_species("A")
    md.fill("A", n=2000, T=1.5)
    md.set_wall("x", "lo", "thermal", T=T1)
    md.set_wall("x", "hi", "thermal", T=T2)
    md.step(2000)
    md.reset_counters()
    t = 8000.0
    md.step(int(t / md.dt))
    c = md.counters()["walls"]
    rate = c["x-hi"]["heat"] / t
    den = 2 * L * math.sqrt(math.pi / 2) * (T1 ** -0.5 + T2 ** -0.5)
    pred = md.n * (d + 1) * (T2 - T1) / den
    assert abs(rate / pred - 1) < 0.015, rate / pred
    assert abs(rate / (md.n * d * (T2 - T1) / den) - 1) > 0.3
    assert abs(c["x-lo"]["heat"] + c["x-hi"]["heat"]) < 0.01 * abs(c["x-hi"]["heat"])
    bal = md.energy_balance()
    assert abs(bal["residual"]) < 1e-9 * abs(c["x-hi"]["heat"])   # exact bookkeeping without forces


def _cycle(pair, dt, seed=9):
    """Two isotherms (thermal side walls at 1.5 and 1.0) and two adiabats (specular side walls), the piston driven at
    0.5 between X = 12, 14, 15, 13, 12; returns per stroke (Q, W, residual) and the gas's NVE energy error scale."""
    md = MD(dim=2, box=(16.0, 8.0), boundary="walls", pair=pair, dt=dt, seed=seed)
    md.add_species("A")
    md.set_piston("x", X=12.0)
    md.fill("A", n=60, T=1.5)

    def walls(kind, T=None):
        md.set_wall("y", "lo", kind, T=T)
        md.set_wall("y", "hi", kind, T=T)
    walls("thermal", 1.5)
    md.step(int(2 / dt))
    out = []
    for kind, T, target in (("thermal", 1.5, 14.0), ("specular", None, 15.0), ("thermal", 1.0, 13.0),
                            ("specular", None, 12.0)):
        walls(kind, T)
        md.reset_counters()
        X = md.piston()["X"]
        md.set_piston("x", V=0.5 * np.sign(target - X))
        md.step(int(round(abs(target - X) / 0.5 / dt)))
        md.set_piston("x", V=0.0)
        b = md.energy_balance()
        out.append((b["Q"], b["W"], b["residual"]))
    # the integrator's own energy error on this gas (NVE: specular walls, piston at rest), same dt and length
    walls("specular")
    md.reset_counters()
    E0, dev = md.energy(), []
    for _ in range(int(8 / dt) // 10):
        md.step(10)
        dev.append(md.energy() - E0)
    return out, float(np.sqrt(np.mean(np.square(dev))))


def test_piston_cycle_closes_the_first_law():
    """Every stroke of a cycle (isothermal at 1.5, adiabatic, isothermal at 1.0, adiabatic): dE = Q + W. For an ideal
    gas the bookkeeping is exact (Q: the kinetic energy changed at re-emissions, W: at the piston's collisions):
    residual < 1e-12 of the exchange. For a force-shifted LJ gas the residual is the integrator's energy error: each
    stroke's residual is below 5 times the rms energy deviation of the same gas in NVE at the same dt (measured
    0.2-1.5 times it), and the whole cycle's residual falls when dt is halved."""
    out, _ = _cycle(None, 0.004)
    for Q, W, res in out:
        assert abs(res) < 1e-12 * (abs(Q) + abs(W) + 1.0)
    assert out[0][0] > 0 and out[2][0] < 0          # heat in on the hot isotherm, out on the cold one
    res_dt = []
    for dt in (0.002, 0.001):
        out, rms = _cycle(LennardJones(2.5, "force"), dt)
        for Q, W, res in out:
            assert abs(res) < 5 * rms, (res, rms)
        res_dt.append(sum(abs(r) for _, _, r in out))
    assert res_dt[1] < res_dt[0]


def test_isothermal_compression_work():
    """A 2-D ideal gas compressed to half its volume by a driven piston, the side walls thermal at T = 1: the work
    done on the gas exceeds the quasi-static N kT ln 2 by a dissipation proportional to the piston speed (measured:
    +5.6 % at 0.02, +2.7 % at 0.01); the linear extrapolation to zero speed from 0.04 and 0.02 gives N kT ln 2 within
    1.5 % (statistical spread of W ~0.4 % per run). The first law closes exactly (no forces). Negative control: the
    adiabatic work of the 1-D compression (N kT (2^2 - 1)/2 for the x degrees of freedom only, gamma = 3) is
    rejected."""
    Ws = {}
    for speed in (0.04, 0.02):
        md = MD(dim=2, box=(20.0, 5.0), boundary="walls", pair=None, dt=0.2, seed=7)
        md.add_species("A")
        md.set_piston("x", X=20.0)
        md.fill("A", n=1500, T=1.0)
        md.set_wall("y", "lo", "thermal", T=1.0)
        md.set_wall("y", "hi", "thermal", T=1.0)
        md.step(200)
        md.reset_counters()
        md.set_piston("x", V=-speed)
        md.step(int(round(10.0 / speed / md.dt)))
        md.set_piston("x", V=0.0)
        assert md.volume() == pytest.approx(50.0, rel=1e-9)
        b = md.energy_balance()
        assert abs(b["residual"]) < 1e-9 * abs(b["W"])
        Ws[speed] = b["W"]
    W0 = 2 * Ws[0.02] - Ws[0.04]
    qs = 1500 * math.log(2.0)
    assert abs(W0 / qs - 1) < 0.015, (Ws, qs)
    assert Ws[0.04] > Ws[0.02] > qs
    assert abs(W0 / (1500 * 0.5 * (4 - 1)) - 1) > 0.3


def test_free_piston_mechanical_equilibrium_and_energy():
    """A free piston (mass 50) under p_ext = 2 on an ideal gas with a thermal wall: the time-averaged pressure the
    gas exerts on it equals p_ext (its mean acceleration vanishes; measured 1.99994). NVE (WCA gas, specular walls):
    the gas's energy plus the piston's (M V^2/2 + p_ext A X) is conserved to the integrator's error."""
    md = MD(dim=2, box=(30.0, 10.0), boundary="walls", pair=None, dt=0.05, seed=8)
    md.add_species("A")
    md.set_piston("x", X=20.0, mass=50.0, p_ext=2.0)
    md.fill("A", n=400, T=1.0)
    md.set_wall("y", "lo", "thermal", T=1.0)
    md.step(4000)
    md.reset_counters()
    md.step(20000)
    assert md.pressure()["piston"] == pytest.approx(2.0, rel=2e-3)
    from lfphys.theories.models.interatomic import WCA
    m2 = MD(dim=2, box=(30.0, 10.0), boundary="walls", pair=WCA(), dt=0.002, seed=8)
    m2.add_species("A")
    m2.set_piston("x", X=20.0, mass=10.0, p_ext=0.5)
    m2.fill("A", n=100, T=1.0)
    m2.step(200)
    E0 = m2.energy() + m2.piston_energy()
    dev = []
    for _ in range(1500):
        m2.step(10)
        dev.append(m2.energy() + m2.piston_energy() - E0)
    assert m2.piston()["hits"] > 50
    assert np.max(np.abs(dev)) < 2e-3 * m2.n


def test_local_bath_acts_only_in_its_region():
    """A CSVR bath restricted to the left half of a box of non-interacting particles: the particles that never enter
    the region move exactly as without the bath (bit for bit), and the region's kinetic temperature relaxes to the
    bath's."""
    def make():
        md = MD(dim=2, box=(20.0, 10.0), boundary="walls", pair=None, dt=0.01, seed=12)
        md.add_species("A")
        md.fill("A", n=400, T=1.0)
        return md
    a, b = make(), make()
    b.add_thermostat("csvr", T=3.0, tau=0.1, region=([0, 0], [10, 10]))
    seen = np.zeros(a.n, bool)
    for _ in range(50):
        a.step(10)
        b.step(10)
        seen |= b.positions()[:, 0] < 10.0
    out = ~seen
    assert out.sum() > 20
    assert np.array_equal(a.positions()[out], b.positions()[out])
    assert np.array_equal(a.velocities()[out], b.velocities()[out])
    assert b.temperature(region=([0, 0], [10, 10]))["T"] > 2.0
    assert b.counters()["baths"][0] > 0


def test_barometric_distribution():
    """An ideal gas in a uniform field g (m g / kT = 0.3) with a Langevin bath, in a box of height H = 10: the heights
    follow the truncated exponential law p(z) ~ exp(-m g z / kT) on [0, H] - KS within the DKW bound (alpha = 0.01)
    for snapshots 20 time units apart (the diffusion time over the scale height, 11 at D = kT/(m gamma) = 1). Negative
    control: a uniform distribution (no field) is rejected."""
    g, T, H = 0.3, 1.0, 10.0
    md = MD(dim=2, box=(10.0, H), boundary=["periodic", "walls"], pair=None, dt=0.02, seed=13, gravity=(0, -g))
    md.add_species("A")
    md.fill("A", n=2000, T=T)
    md.add_thermostat("langevin", T=T, gamma=1.0)
    md.step(2000)
    z = []
    for _ in range(10):
        md.step(1000)
        z.append(md.positions()[:, 1])
    z = np.concatenate(z)
    a = g / T

    def cdf(s):
        return (1 - np.exp(-a * s)) / (1 - math.exp(-a * H))
    assert ob.ks_cdf(z, cdf)["within"]
    assert not ob.ks_cdf(z, lambda s: s / H)["within"]


def test_langevin_diffusion_closed_form():
    """Free particles under a Langevin bath (periodic box: the displacement uses unwrapped coordinates): the
    Ornstein-Uhlenbeck closed form MSD(t) = 2 d D [t - (1 - exp(-gamma t))/gamma], D = kT/(m gamma). For BAOAB the
    discrete scheme's D is (kT h / 2m) coth(gamma h / 2) = D (1 + (gamma h)^2/12 + ...), here 1 + 8e-6. Tolerance 4
    standard errors of the mean of N = 8000 squared displacements (Gaussian: SE = MSD sqrt(2/(d N)) ... sqrt(2/N)).
    D from the MSD slope over t in [5, 10] within 5 %. Negative control: the ballistic-free 2 d D t at t = 1 is
    rejected."""
    T, gamma, d = 1.0, 1.0, 2
    D = T / gamma
    md = MD(dim=2, box=(20.0, 20.0), pair=None, dt=0.01, seed=14)
    md.add_species("A")
    md.fill("A", n=8000, T=T)
    md.add_thermostat("langevin", T=T, gamma=gamma)
    md.step(500)
    md.msd_origin()
    ts, ms = [], []
    for k in range(1, 101):
        md.step(10)
        r = md.msd()
        ts.append(r["t"])
        ms.append(r["msd"])
    ts, ms = np.array(ts), np.array(ms)
    exact = 2 * d * D * (ts - (1 - np.exp(-gamma * ts)) / gamma)
    se = exact * math.sqrt(2.0 / md.n)
    assert np.all(np.abs(ms - exact) < 4 * se + 1e-12)
    assert abs(ob.diffusion_from_msd(ts, ms, d, t_min=5.0) / D - 1) < 0.05
    i1 = int(np.argmin(np.abs(ts - 1.0)))
    assert abs(ms[i1] - 2 * d * D * ts[i1]) > 10 * se[i1]
    assert np.max(np.abs(md.positions(unwrapped=True) - md.positions())) > 20.0   # particles crossed the box


# --- review B7-md ------------------------------------------------------------------------------------------------------
def test_global_csvr_keeps_a_nonzero_momentum():
    """Review B7-md M9: a global CSVR bath in a periodic LJ liquid whose total momentum is not zero (a drift 0.5 of
    every particle): the bath rescales only the motion relative to the centre of mass, so P_x stays at its value to
    round-off and the reported temperature (centre-of-mass frame, N_f = dN - d) is the bath's within 4 block standard
    errors. Negative control: the reviewed engine's value (low by 2<P^2/2M>/N_f = 0.082) is rejected."""
    n, rho = 256, 0.6
    L = (n / rho) ** (1 / 3)
    md = MD(dim=3, box=[L] * 3, pair=LennardJones(2.5, "force"), dt=0.004, seed=4)
    md.add_species("A")
    md.fill("A", n=n, T=1.0)
    md.set(md.keys, v=md.velocities() + np.array([0.5, 0.0, 0.0]))
    md.add_thermostat("csvr", T=1.0, tau=0.05)
    P0 = md.momentum().copy()
    md.step(1000)
    Ts, Px = [], []
    for _ in range(400):
        md.step(25)
        Ts.append(md.temperature()["T"])
        Px.append(md.momentum()[0])
    assert np.max(np.abs(np.array(Px) - P0[0])) < 1e-11 * abs(P0[0])
    m, se = ob.block_average(Ts, nblocks=10)
    assert abs(m - 1.0) < 4 * se, (m, se)
    assert abs(m - (1.0 - 0.0823)) > 4 * se


def test_piston_keeps_the_heat_of_the_wall_it_replaces():
    """Review B7-md M10: an ideal gas heated by a thermal hi wall; set_piston on that axis removes the wall and its
    heat stays in the first-law balance (the residual stays at round-off; before the fix it jumped by the heat)."""
    md = MD(dim=2, box=(10.0, 10.0), boundary="walls", pair=None, dt=0.01, seed=3)
    md.add_species("A")
    md.fill("A", n=400, T=1.0)
    md.set_wall("y", "hi", "thermal", T=3.0)
    md.reset_counters()
    md.step(2000)
    Q = md.energy_balance()["Q"]
    md.set_piston("y", X=10.0, mass=float("inf"), V=0.0)
    b = md.energy_balance()
    assert Q > 100 and b["Q"] == pytest.approx(Q, rel=1e-15) and abs(b["residual"]) < 1e-10 * Q
    md.step(500)
    assert abs(md.energy_balance()["residual"]) < 1e-10 * Q


def test_molecule_modes_closed_forms_and_equipartition():
    """Review B7-md M4: molecule_modes splits a dimer's kinetic energy exactly - a pure rotation, a pure stretch and a
    pure translation each land in their own mode (closed forms) -; add_molecule(T) gives each atom a Maxwell velocity
    (translation included: <K_trans> = (d/2) T per molecule over 1500 dimers, within 4 standard errors; with
    zero_momentum it is zero). Under a Langevin bath at T = 1 a dilute gas of 3-D dimers (k = 50) holds every mode -
    translation, rotation, vibration and the bonds' potential energy - at T within 4 block standard errors; negative
    control: counting three rotations for a linear dimer (2/3 of the rotational temperature) is rejected."""
    from lfphys.theories.models.interatomic import HarmonicBond
    md = MD(dim=3, box=(20.0, 20.0, 20.0), pair=None, seed=1)
    md.add_species("A")
    md.set_bond_type("b", HarmonicBond(50.0, 1.1))
    w = 0.7
    md.add_molecule("A", [[9.45, 10, 10], [10.55, 10, 10]], bonds=[(0, 1, "b")],
                    v=[[0, -0.55 * w, 0], [0, 0.55 * w, 0]])                       # rotation about z at w
    md.add_molecule("A", [[2.0, 2, 2], [3.1, 2, 2]], bonds=[(0, 1, "b")], v=[[-0.3, 0, 0], [0.3, 0, 0]])  # stretch
    md.add_molecule("A", [[5.0, 5, 5], [5.0, 6.1, 5]], bonds=[(0, 1, "b")], v=[[0.2, 0.1, 0], [0.2, 0.1, 0]])
    mm = md.molecule_modes([0])
    assert mm["rotation"]["K"] == pytest.approx(0.5 * (2 * 0.55 ** 2) * w * w, rel=1e-12)
    assert abs(mm["vibration"]["K"]) < 1e-14 and mm["translation"]["K"] == 0.0 and mm["rotation"]["terms"] == 2
    mm = md.molecule_modes([1])
    assert mm["vibration"]["K"] == pytest.approx(0.09, rel=1e-12) and abs(mm["rotation"]["K"]) < 1e-14
    mm = md.molecule_modes([2])
    assert mm["translation"]["K"] == pytest.approx(0.05, rel=1e-12) and abs(mm["rotation"]["K"]) < 1e-14
    big = MD(dim=3, box=(80.0, 80.0, 80.0), pair=None, seed=2)
    big.add_species("A")
    big.set_bond_type("b", HarmonicBond(50.0, 1.1))
    rng = np.random.default_rng(3)
    for k in range(1500):
        c = rng.random(3) * 78 + 1
        big.add_molecule("A", [c, c + [1.1, 0, 0]], bonds=[(0, 1, "b")], T=1.0)
    V = np.asarray(big.velocities()).reshape(-1, 2, 3).mean(1)          # equal masses
    Ktr = (V * V).sum(1)                                                  # (1/2) M V^2 with M = 2
    assert abs(Ktr.mean() - 1.5) < 4 * Ktr.std(ddof=1) / math.sqrt(1500)
    z = MD(dim=3, box=(20.0, 20.0, 20.0), pair=None, seed=2)
    z.add_species("A")
    z.set_bond_type("b", HarmonicBond(50.0, 1.1))
    z.add_molecule("A", [[5, 5, 5], [6.1, 5, 5]], bonds=[(0, 1, "b")], T=1.0, zero_momentum=True)
    assert np.allclose(z.momentum(), 0.0, atol=1e-15)
    gas = MD(dim=3, box=(14.0, 14.0, 14.0), pair=LennardJones(2.5, "force"), dt=0.004, seed=5)
    gas.add_species("A")
    gas.set_bond_type("b", HarmonicBond(50.0, 1.1))
    for c in np.array(np.meshgrid(*[np.arange(1.5, 13.0, 2.4)] * 3)).reshape(3, -1).T:
        gas.add_molecule("A", [c, c + [1.1, 0, 0]], bonds=[(0, 1, "b")], T=1.0)
    gas.add_thermostat("langevin", T=1.0, gamma=0.5)
    gas.step(2000)
    rows = []
    for _ in range(300):
        gas.step(20)
        mm = gas.molecule_modes()
        rows.append([mm[p]["T"] for p in ("translation", "rotation", "vibration", "bonds")]
                    + [2 * mm["rotation"]["K"] / (1.5 * mm["rotation"]["terms"])])
    rows = np.array(rows)
    for c in range(4):
        m, se = ob.block_average(rows[:, c])
        assert abs(m - 1.0) < 4 * se + 0.01, (c, m, se)
    m, se = ob.block_average(rows[:, 4])
    assert abs(m - 1.0) > 4 * se + 0.01
