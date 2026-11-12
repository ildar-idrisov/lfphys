# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Hard disks and hard spheres by event-driven molecular dynamics (plan P8, P15.4).

Perfectly elastic smooth rigid disks (d = 2) or spheres (d = 3) of diameters sigma_i and masses m_i move on straight
lines between collisions; a collision of i and j at contact |r_ij| = (sigma_i + sigma_j)/2 exchanges the impulse

    Delta p_i = 2 mu (v_ij . n) n,   n = (r_j - r_i)/|r_j - r_i|,  v_ij = v_j - v_i,  mu = m_i m_j/(m_i + m_j)

(Delta p_j = -Delta p_i): momentum and kinetic energy are conserved exactly in each collision, and the dynamics is
exact up to the rounding of the collision times (no time step). This is the billiard of statistical mechanics
(Alder & Wainwright 1957, 1959); as a picture of real atoms it is a model (no attraction, no softness), which is why
its use for a real substance is a modelling choice: the system itself is exact classical mechanics of rigid bodies.

**Algorithm** (Rapaport, "The Art of Molecular Dynamics Simulation", ch. 14; Allen & Tildesley §3.7): an event
calendar (a binary heap) of predicted events - pair collisions, crossings of the cells of a cell list (cell side >=
the largest contact distance, so a particle can only meet particles of its own and the adjacent cells), wall contacts
- each stamped with the event counters of the particles involved; an event whose particle has had another event since
is stale and skipped. Positions are kept at each particle's last event time and advanced lazily. Collision time: the
smaller root of |r + v s|^2 = sigma^2 in the stable form s = (r^2 - sigma^2) / (-b + sqrt(b^2 - v^2 (r^2 - sigma^2))),
b = r.v < 0. The calendar is rebuilt from the current state when its stale entries exceed 20 N. A periodic axis needs
at least four cells (L_a >= 4 max sigma): partners in adjacent cells are then at most two cell widths <= L_a/2 apart
along it, so the minimum image taken when a collision is predicted stays the colliding image until one of them
crosses a cell, which predicts again (with three cells the other image could collide unpredicted: review B7-md M1).

**Walls** (each side of a walled axis): ``walls_on="surface"`` (the default) - a body touches the wall with its
surface, its centre stays in [sigma_i/2, L_a - sigma_i/2]; ``walls_on="centre"`` - the wall acts on the centres, which
stay in [0, L_a], as the hard walls of ``core.md.system.MD`` do (a body then reaches sigma_i/2 beyond the plane: the
same box means the same region of the centres in both solvers; review LB1-physics P4). ``"specular"`` reflection
or ``"thermal"`` diffuse re-emission at the wall temperature (the flux-weighted Maxwellian, as in ``core.md.system``;
heat counted). No field, no piston, no soft forces (``core.md.system.MD`` has them).

**Pressure.** From the collisions (virial theorem with impulsive forces) over the interval since the counters' reset,
per axis: p_a = (2 <K_a> + W_a/Delta t) / V on a periodic axis, W_a = sum_collisions (r_ij)_a (Delta p_i)_a; on a walled
axis Clausius' theorem with the walls' impulses at their contact planes (sigma_i/2 from each wall; at the wall with
``walls_on="centre"``) gives the pressure on the walls, p_a = (2 <K_a> + W_a/Delta t) / (A_a (L_a - sigma_eff)),
sigma_eff the impulse-weighted diameter of the particles that hit them (0 with walls on the centres; equal walls;
review B7-md M22); "pressure" is the mean over the axes. And the compressibility
factor of the canonical (NVT) ensemble from the microcanonical run (Erpenbeck
& Wood 1984; Kolafa & Rottner 2006, Eq. "Zvir"): Z = 1 + sum r_ij . Delta p_i / (d N T Delta t) with T = 2<K>/N_f
(N_f = d N - d in a periodic box: the total momentum is conserved). The infinite-system value adds the ensemble
correction (rho/2N) p''/p' (Kolafa & Rottner 2006, Eq. "Zenscorr", from an equation of state; ``z_reference``,
``ensemble_correction`` with the published equations of state of one-component disks and spheres). On walls: the
momentum given to them per area and time.

Edits act at the world time, are transactional (refused: overlaps, positions outside the walls, a box too small for
the cell list) and restart the calendar from the current state. The box (``deform``, plan P16.1) changes only by a wall
moved over empty space: an affine jump of hard bodies would change only their kinetic energy (as for an ideal gas) and
do none of the work of the collisional pressure. **Switching the solver** at the current moment (plan P16.1):
``hard_from_md`` takes the particles of a ``system.MD`` over as hard bodies (the same keys, species, positions,
velocities, walls and time, with the walls on the centres as MD's: the region of the centres, so the density, is the
same on both sides; refused with what blocks it, ``hard_blockers``, and when a pair is inside contact,
``contact_violations``), ``md_from_hard`` hands them back to continuous forces (always possible for a pair model finite
at contact; the potential energy appears; from walls on the surfaces the centres' region grows by sigma/2 at each
wall, which it reports). ``state_dict`` / ``from_state_dict``: plain data with
NumPy arrays including the calendar; a restored system continues bit for bit.
"""

from __future__ import annotations

import copy
import heapq
import math
import time

import numpy as np

from . import cells
from .system import _probe, crystal_sites, free_sites, lattice, random_sites

ABOUT = {
    "layer": "core", "kind": "numerical solution",
    "title": "Твёрдые диски и шары: событийная молекулярная динамика",
    "statement": "Абсолютно упругие гладкие твёрдые диски (2-D) и шары (3-D) разных диаметров и масс: точная "
                 "динамика столкновений по календарю событий (столкновения, пересечения ячеек, стенки); давление по "
                 "импульсам столкновений (теорема вириала) и по импульсу, переданному стенкам; тепловые стенки — "
                 "тепловая баня; стенки — на поверхности шаров или на их центрах (как у непрерывных сил); изменения в "
                 "текущий момент (размер ящика — сдвигом стенки по пустому месту); "
                 "передача частиц от непрерывных сил и обратно (те же ключи, положения, скорости, стенки, время; к "
                 "твёрдым — только без перекрытий); состояние продолжает счёт бит в бит.",
    "validity": "точная классическая механика упругих твёрдых тел (ошибка — округление времён столкновений); как "
                "модель атомов — без притяжения и мягкости (модель); без поля и поршня",
    "basis": ["Alder & Wainwright, J. Chem. Phys. 27, 1208 (1957); 31, 459 (1959)",
              "Rapaport, The Art of Molecular Dynamics Simulation (2nd ed., 2004), гл. 14",
              "Erpenbeck & Wood, J. Stat. Phys. 35, 321 (1984): Z из МД (NVE → NVT)",
              "Kolafa & Rottner, Mol. Phys. 104, 3435 (2006), arXiv:cond-mat/0608356: Z дисков, поправка ансамбля",
              "Kolafa, Labík & Malijevský, PCCP 6, 2335 (2004): Z шаров (данные авторов)",
              "Clisby & McCoy, J. Stat. Phys. 122, 15 (2006): вириальные коэффициенты B2–B10"],
    "conflicts": ["как модель атомов (вещества) твёрдые шары — не аргон и не Леннард-Джонс: нет притяжения — нет "
                  "перехода жидкость–пар и критической точки, только жидкость–кристалл (у дисков — через гексатическую "
                  "фазу); нет мягкости — теплоёмкость и уравнение состояния иные (theories.models.interatomic: LJ, "
                  "WCA)"],
}

_FORMAT = "lfphys.hardspheres/1"


def z_kolafa_rottner(eta):
    """Hard disks: Kolafa & Rottner 2006, the equation of state fitted for rho_max = 0.88 (x = eta/(1 - eta)): the
    thermodynamic limit, fluid below the hexatic transition (their abstract: "about reduced density 0.9")."""
    x = eta / (1 - eta)
    c = [1, 2, 1.12801775, 0.00181895291, -0.0526134737, 0.0504951668, -0.0325433846, 0.0133946531,
         0.00174265604, -0.00944632202, 0.00851111768, -0.0035963525, 0.000577345106]
    return sum(ci * x ** i for i, ci in enumerate(c)) - 1.06399127e-7 * x ** 19


def z_klm(eta):
    """Hard spheres: Kolafa, Labik & Malijevsky 2004 (the authors' code hseos.c, zB6_11348; x = eta/(1 - eta)): the
    thermodynamic limit of the fluid."""
    x = eta / (1 - eta)
    return (1 + 4 * x + 6 * x ** 2 + 2.36476838 * x ** 3 - 0.869855149 * x ** 4 + 1.1062803 * x ** 5
            - 1.09504933 * x ** 6 + 0.637614043 * x ** 7 - 0.227939731 * x ** 10 + 0.109894767 * x ** 14
            - 0.00906797261 * x ** 22)


#: number densities rho sigma^d up to which the reference is used: disks, Kolafa & Rottner's corrected range (their
#: Table 1: Eq. "Zenscorr" below 0.88); spheres, inside the fluid data of zfinal.res (which extend to 1.09)
Z_REFERENCE_RANGE = {2: 0.88, 3: 0.90}


def z_reference(dim, rho):
    """The compressibility factor of the one-component hard-disk (d = 2) or hard-sphere (d = 3) fluid of number
    density rho (sigma = 1) in the thermodynamic limit (``z_kolafa_rottner`` / ``z_klm``); None outside
    ``Z_REFERENCE_RANGE``. The fits reproduce the authors' tables to 2e-5 / 4e-5 (tests/test_md_hard.py)."""
    if not (0 < rho <= Z_REFERENCE_RANGE[dim]):
        return None
    return z_kolafa_rottner(math.pi / 4 * rho) if dim == 2 else z_klm(math.pi / 6 * rho)


def ensemble_correction(dim, rho, n):
    """(rho / 2N) p'' / p' with p = rho Z(rho) (kT = 1) by central differences of ``z_reference``'s fit: Z of the
    NVT system of N particles is Z_inf minus this (Kolafa & Rottner 2006, Eq. "Zenscorr", to O(1/N^2))."""
    zf = z_kolafa_rottner if dim == 2 else z_klm
    v = math.pi / 4 if dim == 2 else math.pi / 6

    def p(r):
        return r * zf(v * r)
    h = 1e-4 * rho
    p1 = (p(rho + h) - p(rho - h)) / (2 * h)
    p2 = (p(rho + h) - 2 * p(rho) + p(rho - h)) / h ** 2
    return rho / (2 * n) * p2 / p1
_AX = "xyz"


class HardSpheres:
    """Event-driven hard disks / spheres (see the module docstring).

    HardSpheres(dim=2, box=(10, 10), boundary="periodic", seed=0)
    """

    def __init__(self, dim=2, box=(10.0, 10.0), boundary="periodic", seed=0, t=0.0, walls_on="surface"):
        if dim not in (2, 3):
            raise ValueError("dim must be 2 or 3")
        if walls_on not in ("surface", "centre"):
            raise ValueError("walls_on: 'surface' or 'centre'")
        self.walls_on = walls_on
        self.dim = int(dim)
        L = np.asarray(box, float).reshape(-1)
        if L.shape != (self.dim,) or not np.all((L > 0) & np.isfinite(L)):
            raise ValueError("box: dim positive finite lengths")
        if isinstance(boundary, str):
            boundary = [boundary] * self.dim
        if len(boundary) != self.dim or any(b not in ("periodic", "walls") for b in boundary):
            raise ValueError("boundary: 'periodic' or 'walls' per axis")
        self.L = L
        self.periodic = np.array([b == "periodic" for b in boundary])
        self.rng = np.random.Generator(np.random.PCG64(seed))
        d = self.dim
        self._species: list = []
        self._key = np.zeros(0, np.int64)
        self._typ = np.zeros(0, np.int64)
        self._x = np.zeros((0, d))
        self._v = np.zeros((0, d))
        self._tl = np.zeros(0)
        self._img = np.zeros((0, d), np.int64)
        self._cell = np.zeros((0, d), np.int64)
        self._cnt = np.zeros(0, np.int64)
        self._next_key = 0
        self._t = float(t)
        self._t_ev = float(t)
        self._walls = {}
        for a in range(d):
            if not self.periodic[a]:
                for s in ("lo", "hi"):
                    self._walls[f"{_AX[a]}-{s}"] = {"kind": "specular", "T": None, "impulse": 0.0, "heat": 0.0,
                                                    "hits": 0, "contact": 0.0}
        self._heap: list = []
        self._seq = 0
        self._acc = {"t0": float(t), "t_last": float(t), "Kdt": 0.0, "W": 0.0, "collisions": 0, "E0": 0.0,
                     "Kadt": np.zeros(d), "Wa": np.zeros(d)}
        self._stats = {"events": 0, "stale": 0, "collisions": 0, "rebuilds": 0, "seconds": 0.0}
        self._msd_ref = None
        self._msd_t0 = None
        self._grid()
        self._K = 0.0
        self._Ka = np.zeros(d)
        self._cells = {}

    # --- helpers ---------------------------------------------------------------------------------------------------
    @property
    def t(self) -> float:
        return self._t

    @property
    def n(self) -> int:
        return int(self._key.shape[0])

    @property
    def keys(self) -> np.ndarray:
        return self._key.copy()

    def _species_index(self, name):
        for i, s in enumerate(self._species):
            if s["name"] == name:
                return i
        raise KeyError(f"no species {name!r}")

    def _rows(self, keys):
        keys = np.atleast_1d(np.asarray(keys, np.int64))
        if self.n == 0:
            if len(keys):
                raise KeyError("no particle with some of the keys")
            return np.zeros(0, np.int64)
        r = np.searchsorted(self._key, keys)
        if np.any((r >= self.n) | (self._key[np.minimum(r, self.n - 1)] != keys)):
            raise KeyError("no particle with some of the keys")
        return r

    def _off(self, sigma):
        """The distance of a centre from a wall at contact: sigma/2 (walls on the surfaces) or 0 (on the centres)."""
        return 0.5 * sigma if self.walls_on == "surface" else 0.0 * sigma

    def _sig(self):
        return np.array([s["sigma"] for s in self._species])[self._typ] if self.n else np.zeros(0)

    def _mass(self):
        return np.array([s["mass"] for s in self._species])[self._typ] if self.n else np.zeros(0)

    def _grid(self):
        smax = max([s["sigma"] for s in self._species], default=1.0)
        nc = np.maximum(np.floor(self.L / smax).astype(np.int64), 1)
        if np.any(self.periodic & (nc < 4)):
            raise ValueError(f"a periodic box length must be >= 4 times the largest diameter ({4 * smax:g})")
        self._nc = nc
        self._w = self.L / nc
        self._sp_sig = np.array([s["sigma"] for s in self._species])
        self._sp_mass = np.array([s["mass"] for s in self._species])
        # neighbour cells (flat ids, the cell itself included) of every cell
        import itertools
        ncell = int(np.prod(nc))
        grid = np.stack(np.unravel_index(np.arange(ncell), tuple(nc)), axis=1)
        offs = list(itertools.product(*[(-1, 0, 1) if nc[a] > 1 else (0,) for a in range(self.dim)]))
        nbr = [[] for _ in range(ncell)]
        for o in offs:
            g = grid + np.array(o)
            ok = np.ones(ncell, bool)
            for a in range(self.dim):
                if self.periodic[a]:
                    g[:, a] %= nc[a]
                else:
                    ok &= (g[:, a] >= 0) & (g[:, a] < nc[a])
            flat = np.ravel_multi_index(tuple(np.clip(g, 0, nc - 1).T), tuple(nc))
            for c in np.flatnonzero(ok):
                nbr[c].append(int(flat[c]))
        self._nbr = nbr

    def add_species(self, name, mass=1.0, sigma=1.0):
        if any(s["name"] == name for s in self._species):
            raise KeyError(f"species {name!r} exists")
        mass, sigma = float(mass), float(sigma)
        if not (mass > 0 and math.isfinite(mass) and sigma > 0 and math.isfinite(sigma)):
            raise ValueError("finite mass > 0 and sigma > 0")

        def apply():
            self._species.append({"name": name, "mass": mass, "sigma": sigma})
        self._transaction(apply)
        return name

    def set_species(self, name, mass=None, sigma=None):
        i = self._species_index(name)
        sp = dict(self._species[i])
        if mass is not None:
            sp["mass"] = float(mass)
        if sigma is not None:
            sp["sigma"] = float(sigma)
        if not (sp["mass"] > 0 and math.isfinite(sp["mass"]) and sp["sigma"] > 0):
            raise ValueError("finite mass > 0 and sigma > 0")

        def apply():
            self._species[i] = sp
        self._transaction(apply)

    def species(self) -> list:
        return [dict(s) for s in self._species]

    # --- particles -------------------------------------------------------------------------------------------------
    def add(self, species, x, v=None, T=None, zero_momentum=False, _random=None):
        """Add particles at positions x (n, d) with velocities v, Maxwell velocities at T, or zero; refused on overlap
        or outside the walls. Returns keys."""
        ti = self._species_index(species)
        if _random is None:
            x = np.atleast_2d(np.asarray(x, float))
            if x.shape[1] != self.dim or not np.all(np.isfinite(x)):
                raise ValueError(f"positions (n, {self.dim})")
            n = x.shape[0]
        else:
            n = int(_random[0])
        m = self._species[ti]["mass"]
        if v is not None:
            v = np.broadcast_to(np.asarray(v, float), (n, self.dim)).copy()

        def apply():
            nonlocal x
            if _random is not None:
                sn = self._species[ti]["sigma"]
                od = 0.5 * (sn + self._sig()) if self.n else np.zeros(0)
                x = random_sites(n, _random[1], _random[2], sn, self.rng, self.L, self.periodic, self._x, od)
            vv = v
            if vv is None:
                if T is None:
                    vv = np.zeros((n, self.dim))
                else:
                    vv = self.rng.standard_normal((n, self.dim)) * math.sqrt(T / m)
                    if zero_momentum and n > 1:
                        vv -= vv.mean(axis=0)
            keys = np.arange(self._next_key, self._next_key + n, dtype=np.int64)
            self._next_key += n
            xw, img = self._wrap(x)
            self._key = np.concatenate([self._key, keys])
            self._typ = np.concatenate([self._typ, np.full(n, ti, np.int64)])
            self._x = np.vstack([self._x, xw])
            self._v = np.vstack([self._v, vv])
            self._tl = np.concatenate([self._tl, np.full(n, self._t)])
            self._img = np.vstack([self._img, img])
            self._cnt = np.concatenate([self._cnt, np.zeros(n, np.int64)])
            self._cell = np.vstack([self._cell, np.zeros((n, self.dim), np.int64)])
            if self._msd_ref is not None:
                self._msd_ref = np.vstack([self._msd_ref, xw + img * self.L])
        keys = np.arange(self._next_key, self._next_key + n, dtype=np.int64)
        self._transaction(apply)
        return keys

    def fill(self, species, n=None, density=None, region=None, lattice_kind="auto", T=None, zero_momentum=True,
             arrangement="lattice", info=None, skip_occupied=False):
        """Particles of one species in ``region`` (default: the box), kept sigma/2 from the walls, with Maxwell
        velocities at T: ``density`` - a perfect lattice of that number density in the region (``system.crystal_sites``;
        along a periodic axis the block spans the cells are fitted to the box, ``info`` gets the density); ``n`` - the
        first n sites of a lattice filling the region (``arrangement="lattice"``) or random places without overlaps
        (``"random"``: random sequential insertion from the system's generator; refused when too dense). ``skip_occupied``
        (a crystal): the sites nearer than sigma_ij to a particle already present stay empty (``info["skipped"]``; a block
        with no free site is refused), as in ``system.MD.fill``."""
        ti = self._species_index(species)
        s = self._species[ti]["sigma"]
        wlo = np.where(self.periodic, 0.0, 0.5 * s)        # placed sigma/2 from the walls with either kind of wall
        whi = np.where(self.periodic, self.L, self.L - 0.5 * s)
        if region is None:
            lo, hi = wlo.copy(), whi.copy()
        else:
            lo = np.maximum(np.asarray(region[0], float), wlo)
            hi = np.minimum(np.asarray(region[1], float), whi)
            if not np.all(hi > lo):
                raise ValueError("region: hi > lo inside the walls")
        if n is None and density is None:
            raise ValueError("give n or density")
        if arrangement not in ("lattice", "random"):
            raise ValueError("arrangement: 'lattice' or 'random'")
        if n is None:
            full = self.periodic & (lo <= 0.0) & (hi >= self.L)
            pos, inf = crystal_sites(np.where(full, 0.0, lo), np.where(full, self.L, hi), float(density),
                                     lattice_kind, full)
            inf["skipped"] = 0
            if skip_occupied and self.n:
                pw, _ = self._wrap(pos)
                keep = free_sites(pw, s, self._wrap(self.positions())[0], self._sig(), self.L, self.periodic)
                inf["skipped"] = int(np.sum(~keep))
                if not keep.any():
                    raise ValueError(f"no free lattice site: all {len(pos)} sites of the block are occupied")
                pos = pos[keep]
            if info is not None:
                info.update(inf)
            return self.add(species, pos, T=T, zero_momentum=zero_momentum)
        n = int(n)
        if arrangement == "lattice" or n == 0:
            return self.add(species, lattice(n, lo, hi, lattice_kind), T=T, zero_momentum=zero_momentum)
        return self.add(species, None, T=T, zero_momentum=zero_momentum, _random=(n, lo, hi))

    def adopt(self, keys, species_index, x, v, next_key=None):
        """Particles taken over from another solver at the current time (``hard_from_md``): their keys (increasing),
        species indices, positions and velocities, kept as they are, into an empty system, in one edit (refused:
        overlaps, centres beyond a wall's contact plane: sigma/2 from it, or the wall itself with walls on the
        centres)."""
        if self.n:
            raise ValueError("adopt: the system must be empty")
        keys = np.asarray(keys, np.int64).reshape(-1)
        n = len(keys)
        if n > 1 and np.any(np.diff(keys) <= 0):
            raise ValueError("adopt: keys must increase")
        typ = np.asarray(species_index, np.int64).reshape(-1)
        if typ.shape != (n,) or (n and (typ.min() < 0 or typ.max() >= len(self._species))):
            raise ValueError("adopt: a species index per particle")
        x = np.asarray(x, float).reshape(n, self.dim)
        v = np.asarray(v, float).reshape(n, self.dim)

        def apply():
            xw, img = self._wrap(x)
            self._key, self._typ = keys.copy(), typ.copy()
            self._x, self._v, self._img = xw, v.copy(), img
            self._tl = np.full(n, self._t)
            self._cnt = np.zeros(n, np.int64)
            self._cell = np.zeros((n, self.dim), np.int64)
            self._next_key = max(int(next_key) if next_key is not None else 0, int(keys[-1]) + 1 if n else 0)
        self._transaction(apply)

    def remove(self, keys):
        rows = self._rows(keys)

        def apply():
            keep = np.ones(self.n, bool)
            keep[rows] = False
            for k in ("_key", "_typ", "_x", "_v", "_tl", "_img", "_cnt", "_cell"):
                setattr(self, k, getattr(self, k)[keep])
            if self._msd_ref is not None:
                self._msd_ref = self._msd_ref[keep]
        self._transaction(apply)

    def set(self, keys, x=None, v=None):
        rows = self._rows(keys)
        n = len(rows)

        def apply():
            if x is not None:
                xw, img = self._wrap(np.broadcast_to(np.asarray(x, float), (n, self.dim)))
                self._x[rows] = xw
                self._img[rows] = img
                if self._msd_ref is not None:
                    self._msd_ref[rows] = xw + img * self.L
            if v is not None:
                self._v[rows] = np.broadcast_to(np.asarray(v, float), (n, self.dim))
        self._transaction(apply)

    def set_wall(self, axis, side, kind, T=None):
        a = _AX.index(axis) if isinstance(axis, str) else int(axis)
        if self.periodic[a]:
            raise ValueError("a periodic axis has no walls")
        if kind not in ("specular", "thermal") or side not in ("lo", "hi"):
            raise ValueError("kind 'specular' or 'thermal', side 'lo' or 'hi'")
        if kind == "thermal" and not (T is not None and T > 0):
            raise ValueError("a thermal wall needs T > 0")

        def apply():
            old = self._walls[f"{_AX[a]}-{side}"]
            self._acc["Q_removed"] = self._acc.get("Q_removed", 0.0) + old["heat"]
            self._walls[f"{_AX[a]}-{side}"] = {"kind": kind, "T": None if T is None else float(T), "impulse": 0.0,
                                               "heat": 0.0, "hits": 0, "contact": 0.0}
        self._transaction(apply)

    def set_boundary(self, axis, kind):
        """Make one axis periodic or bounded by specular walls at the current moment (review UX-ui U7), as
        ``system.MD.set_boundary``: ``"walls"`` is refused while a particle's centre is beyond a face's contact plane
        (it would be inside a wall), ``"periodic"`` when particles across the joined faces would overlap, and when the
        box is too short for the cell list (L_a >= 4 max sigma); the walls' heat stays in the balance."""
        a = _AX.index(axis) if isinstance(axis, str) else int(axis)
        if kind not in ("periodic", "walls"):
            raise ValueError("boundary: 'periodic' or 'walls'")
        if (kind == "periodic") == bool(self.periodic[a]):
            return

        def apply():
            per = self.periodic.copy()
            per[a] = kind == "periodic"
            self.periodic = per
            for side in ("lo", "hi"):
                key = f"{_AX[a]}-{side}"
                if kind == "walls":
                    self._walls[key] = {"kind": "specular", "T": None, "impulse": 0.0, "heat": 0.0, "hits": 0,
                                        "contact": 0.0}
                else:
                    old = self._walls.pop(key, None)
                    if old is not None:
                        self._acc["Q_removed"] = self._acc.get("Q_removed", 0.0) + old["heat"]
            if kind == "periodic" and self.n:
                xw, img = self._wrap(self._x)
                self._x, self._img = xw, self._img + img
        self._transaction(apply)

    def deform(self, L, mode="wall") -> dict:
        """Change the box lengths at the current time (plan P16.1). Only ``"wall"``: on walled axes the hi wall moves to
        L'_a over empty space (a free expansion follows; refused where a particle's centre would be beyond the moved
        wall's contact plane); no work, nothing else moves (the pressure's accumulators mix the two boxes until the next
        ``reset_counters``). ``"affine"`` is refused: an instantaneous affine jump of hard
        bodies changes only their kinetic energy (as for an ideal gas) and does none of the work of the collisional
        pressure, so even in small steps it would not follow the hard-sphere adiabat (``system.MD.deform`` does it for
        continuous forces, where the configurational work is the potential energy's change). Returns {"mode",
        "lambda", "V0", "V1", "dE": 0}."""
        L_new = np.asarray(L, float).reshape(-1)
        if L_new.shape != (self.dim,) or not np.all((L_new > 0) & np.isfinite(L_new)):
            raise ValueError("box: dim positive finite lengths")
        if mode != "wall":
            raise ValueError("hard spheres: an affine jump does no work of the collisional pressure (only 'wall')")
        changed = np.flatnonzero(L_new != self.L)
        per = [_AX[a] for a in changed if self.periodic[a]]
        if per:
            raise ValueError(f"axis {', '.join(per)} is periodic: it has no wall to move")
        V0 = self.volume()
        lam = (L_new / self.L).tolist()

        def apply():
            self.L = L_new.copy()
        self._transaction(apply)
        return {"mode": mode, "lambda": lam, "V0": V0, "V1": self.volume(), "dE": 0.0}

    def _wrap(self, x):
        x = np.array(x, float)
        img = np.zeros(x.shape, np.int64)
        per = np.flatnonzero(self.periodic)
        if len(per):
            k = np.floor(x[:, per] / self.L[per]).astype(np.int64)
            x[:, per] -= k * self.L[per]
            x[:, per] = np.where(x[:, per] >= self.L[per], x[:, per] - self.L[per], x[:, per])
            x[:, per] = np.where(x[:, per] < 0.0, 0.0, x[:, per])
            img[:, per] = k
        return x, img

    _STATE = ("L", "periodic", "_species", "_key", "_typ", "_x", "_v", "_tl", "_img", "_cell", "_cnt", "_next_key", "_walls",
              "_heap",
              "_seq", "_acc", "rng", "_msd_ref", "_nc", "_w", "_K", "_Ka", "_t_ev", "_cells", "_sp_sig", "_sp_mass",
              "_nbr")

    def _transaction(self, apply):
        snap = {k: copy.deepcopy(getattr(self, k)) for k in self._STATE}
        try:
            self._sync()
            K_before = self._K
            apply()
            self._grid()
            self._check()
            self._restart()
            self._acc["E0"] += self._K - K_before
        except BaseException:
            for k, val in snap.items():
                setattr(self, k, val)
            raise

    def _sync(self):
        """Bring every particle to the world time (before an edit or a save of the positions)."""
        self._accumulate(self._t)
        if self.n:
            self._x = self._x + self._v * (self._t - self._tl)[:, None]
            self._tl = np.full(self.n, self._t)
        self._t_ev = self._t

    def _check(self):
        if self.n == 0:
            return
        sig = self._sig()
        off = self._off(sig)
        for a in range(self.dim):
            if not self.periodic[a]:
                if np.any(self._x[:, a] < off * (1 - 1e-12)) or np.any(self._x[:, a] > self.L[a] - off * (1 - 1e-12)):
                    raise ValueError(f"a particle outside the walls on axis {_AX[a]}")
        smax = float(sig.max())
        i, j = cells.pair_list(self._x, self.L, self.periodic, smax)
        if len(i):
            dx = self._x[j] - self._x[i]
            for a in np.flatnonzero(self.periodic):
                dx[:, a] -= self.L[a] * np.rint(dx[:, a] / self.L[a])
            r2 = np.einsum("ij,ij->i", dx, dx)
            s = 0.5 * (sig[i] + sig[j])
            if np.any(r2 < (s * (1.0 - 1e-12)) ** 2):
                raise ValueError("overlapping hard particles")

    def _restart(self):
        """Cells, counters and the event calendar from the current state (all particles at the world time)."""
        self._K = self.kinetic_energy()
        self._Ka = 0.5 * np.einsum("i,ij->j", self._mass(), self._v * self._v) if self.n else np.zeros(self.dim)
        self._cells = {}
        if self.n:
            self._cell = np.clip(np.floor(self._x / self._w).astype(np.int64), 0, self._nc - 1)
        for r in range(self.n):
            self._cells.setdefault(self._flat(self._cell[r]), set()).add(r)
        self._heap = []
        self._seq = 0
        for r in range(self.n):
            self._predict(r, self._t)

    def _flat(self, c):
        f = 0
        for a in range(self.dim):
            f = f * int(self._nc[a]) + int(c[a])
        return f

    def _neighbours(self, r):
        out = []
        cells_ = self._cells
        for f in self._nbr[self._flat(self._cell[r])]:
            s = cells_.get(f)
            if s:
                out.extend(s)
        return out

    # --- events ----------------------------------------------------------------------------------------------------
    def _push(self, t, kind, i, j, ci, cj):
        heapq.heappush(self._heap, (t, self._seq, kind, i, j, ci, cj))
        self._seq += 1

    def _predict(self, i, t):
        xi = self._x[i] + self._v[i] * (t - self._tl[i])
        vi = self._v[i]
        sp = self._sp_sig
        si = sp[self._typ[i]]
        cand = [k for k in self._neighbours(i) if k != i]
        if cand:
            c = np.array(sorted(cand), np.int64)
            xj = self._x[c] + self._v[c] * (t - self._tl[c])[:, None]
            r = xj - xi
            for a in np.flatnonzero(self.periodic):
                r[:, a] -= self.L[a] * np.rint(r[:, a] / self.L[a])
            v = self._v[c] - vi
            b = np.einsum("ij,ij->i", r, v)
            s = 0.5 * (si + sp[self._typ[c]])
            r2 = np.einsum("ij,ij->i", r, r)
            v2 = np.einsum("ij,ij->i", v, v)
            q = r2 - s * s
            disc = b * b - v2 * q
            hit = (b < 0.0) & (disc > 0.0)
            if np.any(hit):
                with np.errstate(divide="ignore", invalid="ignore"):
                    dt = np.where(q > 0.0, q / (-b + np.sqrt(np.maximum(disc, 0.0))), 0.0)
                for k in np.flatnonzero(hit):
                    j = int(c[k])
                    self._push(t + float(dt[k]), 0, i, j, int(self._cnt[i]), int(self._cnt[j]))
        # cell crossing
        best, code = math.inf, -1
        for a in range(self.dim):
            if self._nc[a] == 1 or vi[a] == 0.0:
                continue
            ca = self._cell[i, a]
            if vi[a] > 0.0:
                if not self.periodic[a] and ca == self._nc[a] - 1:
                    continue
                dt = ((ca + 1) * self._w[a] - xi[a]) / vi[a]
                cd = 2 * a + 1
            else:
                if not self.periodic[a] and ca == 0:
                    continue
                dt = (ca * self._w[a] - xi[a]) / vi[a]
                cd = 2 * a
            dt = max(dt, 0.0)
            if dt < best:
                best, code = dt, cd
        if code >= 0:
            self._push(t + best, 1, i, code, int(self._cnt[i]), 0)
        # walls
        for a in range(self.dim):
            if self.periodic[a] or vi[a] == 0.0:
                continue
            off = self._off(si)
            if vi[a] < 0.0:
                dt = (xi[a] - off) / (-vi[a])
                cd = 2 * a
            else:
                dt = (self.L[a] - off - xi[a]) / vi[a]
                cd = 2 * a + 1
            self._push(t + max(dt, 0.0), 2, i, cd, int(self._cnt[i]), 0)

    def _move(self, i, t):
        self._x[i] = self._x[i] + self._v[i] * (t - self._tl[i])
        self._tl[i] = t

    def _accumulate(self, t):
        a = self._acc
        if t > a["t_last"]:
            a["Kdt"] += self._K * (t - a["t_last"])
            a["Kadt"] = a.get("Kadt", np.zeros(self.dim)) + self._Ka * (t - a["t_last"])
            a["t_last"] = t

    def _process(self, ev) -> bool:
        t, _, kind, i, j, ci, cj = ev
        if self._cnt[i] != ci or (kind == 0 and self._cnt[j] != cj):
            self._stats["stale"] += 1
            return False
        self._accumulate(t)
        self._t_ev = t
        self._stats["events"] += 1
        if kind == 0:
            self._move(i, t)
            self._move(j, t)
            r = self._x[j] - self._x[i]
            for a in np.flatnonzero(self.periodic):
                r[a] -= self.L[a] * np.rint(r[a] / self.L[a])
            nr = math.sqrt(float(r @ r))
            nhat = r / nr
            mi, mj = self._sp_mass[self._typ[i]], self._sp_mass[self._typ[j]]
            mu = mi * mj / (mi + mj)
            vn = float((self._v[j] - self._v[i]) @ nhat)
            dp = 2.0 * mu * vn * nhat
            ka = mi * self._v[i] * self._v[i] + mj * self._v[j] * self._v[j]
            self._v[i] += dp / mi
            self._v[j] -= dp / mj
            self._Ka = self._Ka + 0.5 * (mi * self._v[i] * self._v[i] + mj * self._v[j] * self._v[j] - ka)
            self._acc["W"] += float(-r @ dp)          # r_ij . Delta p_i with r_ij = r_i - r_j = -r
            self._acc["Wa"] = self._acc.get("Wa", np.zeros(self.dim)) - r * dp
            self._acc["collisions"] += 1
            self._stats["collisions"] += 1
            self._cnt[i] += 1
            self._cnt[j] += 1
            self._predict(i, t)
            self._predict(j, t)
        elif kind == 1:
            self._move(i, t)
            a, up = j // 2, j % 2
            old = self._flat(self._cell[i])
            ca = self._cell[i, a] + (1 if up else -1)
            if self.periodic[a]:
                if ca >= self._nc[a]:
                    ca = 0
                    self._x[i, a] -= self.L[a]
                    self._img[i, a] += 1
                elif ca < 0:
                    ca = self._nc[a] - 1
                    self._x[i, a] += self.L[a]
                    self._img[i, a] -= 1
            self._cells[old].discard(i)
            self._cell[i, a] = ca
            self._cells.setdefault(self._flat(self._cell[i]), set()).add(i)
            self._cnt[i] += 1
            self._predict(i, t)
        else:
            self._move(i, t)
            a, side = j // 2, ("hi" if j % 2 else "lo")
            w = self._walls[f"{_AX[a]}-{side}"]
            m = self._species[self._typ[i]]["mass"]
            v_old = self._v[i].copy()
            if w["kind"] == "specular":
                self._v[i, a] = -v_old[a]
            else:
                sd = math.sqrt(w["T"] / m)
                vn = sd * math.sqrt(-2.0 * math.log1p(-float(self.rng.random())))
                vt = self.rng.standard_normal(self.dim) * sd
                vt[a] = vn if side == "lo" else -vn
                self._v[i] = vt
                dK = 0.5 * m * (float(vt @ vt) - float(v_old @ v_old))
                w["heat"] += dK
                self._K += dK
                self._Ka = self._Ka + 0.5 * m * (vt * vt - v_old * v_old)
            dv = self._v[i, a] - v_old[a]
            w["impulse"] += m * (dv if side == "lo" else -dv)
            w["contact"] = w.get("contact", 0.0) + self._off(self._species[self._typ[i]]["sigma"]) * m * abs(dv)
            w["hits"] += 1
            self._cnt[i] += 1
            self._predict(i, t)
        return True

    def advance(self, t_target) -> int:
        """Process the events up to t_target; the world time becomes t_target. Returns the events processed."""
        t_target = float(t_target)
        if t_target < self._t:
            raise ValueError("time runs forward")
        t0 = time.perf_counter()
        done = 0
        while self._heap and self._heap[0][0] <= t_target:
            if self._process(heapq.heappop(self._heap)):
                done += 1
            if len(self._heap) > 20 * self.n + 1000:
                self._rebuild_calendar()
        self._t = t_target
        self._stats["seconds"] += time.perf_counter() - t0
        return done

    def _rebuild_calendar(self):
        """Drop the stale entries: predict every particle again at the last event time (deterministic)."""
        t = self._t_ev
        self._heap = []
        self._seq = 0
        for r in range(self.n):
            self._predict(r, t)
        self._stats["rebuilds"] += 1

    # --- measurements ----------------------------------------------------------------------------------------------
    def positions(self, unwrapped=False) -> np.ndarray:
        x = self._x + self._v * (self._t - self._tl)[:, None]
        return x + self._img * self.L if unwrapped else x

    def velocities(self) -> np.ndarray:
        return self._v.copy()

    def kinetic_energy(self) -> float:
        if self.n == 0:
            return 0.0
        return 0.5 * float(np.sum(self._mass() * np.einsum("ij,ij->i", self._v, self._v)))

    def momentum(self) -> np.ndarray:
        return np.sum(self._mass()[:, None] * self._v, axis=0)

    def dof(self) -> int:
        return self.dim * self.n - (self.dim if np.all(self.periodic) and self.n > 1 else 0)

    def temperature(self, species=None) -> dict:
        """Kinetic temperature 2 (K - P^2/2M)/(dN - d) in a periodic box, 2K/(dN) with walls; of one species: 2K/(d n)."""
        if species is not None:
            sel = self._typ == self._species_index(species)
            n = int(sel.sum())
            K = 0.5 * float(np.sum(self._mass()[sel] * np.einsum("ij,ij->i", self._v[sel], self._v[sel]))) if n else 0.0
            return {"T": 2.0 * K / (self.dim * n) if n else float("nan"), "dof": self.dim * n, "K": K}
        nf = self.dof()
        K = self.kinetic_energy()
        if np.all(self.periodic) and self.n > 1:
            P = self.momentum()
            K -= 0.5 * float(P @ P) / float(np.sum(self._mass()))
        return {"T": 2.0 * K / nf if nf else float("nan"), "dof": nf, "K": K}

    def volume(self) -> float:
        return float(np.prod(self.L))

    def packing_fraction(self) -> float:
        sig = self._sig()
        vol = (math.pi / 4 * sig ** 2) if self.dim == 2 else (math.pi / 6 * sig ** 3)
        return float(np.sum(vol)) / self.volume()

    def pressure(self) -> dict:
        """Since the counters' reset: the mechanical pressure (2<K>/d + W/(d Delta t))/V, the NVT compressibility
        factor Z = 1 + W/(d N T Delta t) (T = 2<K>/N_f), the collision rate, the pressure on each wall by its
        impulse, and the interval."""
        self._accumulate(self._t)
        a = self._acc
        dt = self._t - a["t0"]
        out = {"interval": dt, "collisions": a["collisions"], "walls": {}}
        if dt <= 0 or self.n == 0:
            return out
        K = a["Kdt"] / dt
        Ka = a.get("Kadt", np.full(self.dim, a["Kdt"] / self.dim)) / dt
        Wa = a.get("Wa", np.full(self.dim, a["W"] / self.dim))
        V = self.volume()
        nf = self.dof()
        T = 2.0 * K / nf if nf > 0 else 0.0
        sig = self._sig()
        tens = []
        for ax in range(self.dim):
            area = float(np.prod(np.delete(self.L, ax)))
            if self.periodic[ax]:
                tens.append((2.0 * Ka[ax] + Wa[ax] / dt) / V)
                continue
            lo, hi = self._walls[f"{_AX[ax]}-lo"], self._walls[f"{_AX[ax]}-hi"]
            imp = lo["impulse"] + hi["impulse"]
            s_eff = (2.0 * (lo.get("contact", 0.0) + hi.get("contact", 0.0)) / imp if imp > 0
                     else 2.0 * float(np.mean(self._off(sig))))
            tens.append((2.0 * Ka[ax] + Wa[ax] / dt) / (area * (self.L[ax] - s_eff)))
        # at T = 0 (a single particle at rest, a cold gas) the pressure is 0 and Z = p/(rho T) has no value
        # (review UX-ui U6: a division by zero stopped the world)
        out.update({"pressure": float(np.mean(tens)), "tensor": [float(z) for z in tens], "T": T,
                    "Z": (1.0 + a["W"] / (self.dim * self.n * T * dt)) if T > 0 else None,
                    "collision_rate": a["collisions"] / dt})
        for k, w in self._walls.items():
            ax = _AX.index(k[0])
            area = float(np.prod(np.delete(self.L, ax)))
            out["walls"][k] = w["impulse"] / (area * dt)
        return out

    def accumulators(self) -> dict:
        """The running sums since the counters' reset (for block averages): the time, the time integral of the
        kinetic energy, the collision virial sum_collisions r_ij . Delta p_i and the collisions."""
        self._accumulate(self._t)
        a = self._acc
        return {"t0": a["t0"], "t": self._t, "Kdt": a["Kdt"], "W": a["W"], "collisions": a["collisions"],
                "n": self.n, "dof": self.dof()}

    def counters(self) -> dict:
        return {"t0": self._acc["t0"], "t": self._t,
                "walls": {k: {kk: w[kk] for kk in ("kind", "impulse", "heat", "hits")} for k, w in self._walls.items()},
                "collisions": self._acc["collisions"]}

    def heat(self) -> float:
        return float(sum(w["heat"] for w in self._walls.values()) + self._acc.get("Q_removed", 0.0))

    def energy_balance(self) -> dict:
        E = self.kinetic_energy()
        Q = self.heat()
        return {"E": E, "E0": self._acc["E0"], "dE": E - self._acc["E0"], "Q": Q,
                "residual": E - self._acc["E0"] - Q}

    def reset_counters(self):
        self._accumulate(self._t)
        for w in self._walls.values():
            w.update(impulse=0.0, heat=0.0, hits=0, contact=0.0)
        self._acc = {"t0": self._t, "t_last": self._t, "Kdt": 0.0, "W": 0.0, "collisions": 0,
                     "E0": self.kinetic_energy(), "Q_removed": 0.0, "Kadt": np.zeros(self.dim),
                     "Wa": np.zeros(self.dim)}

    def rdf(self, r_max, nbins=100):
        from .observables import rdf as _rdf
        return _rdf(self.positions(), self.L, self.periodic, r_max, nbins)

    def msd_origin(self):
        self._msd_ref = self.positions(True)
        self._msd_t0 = self._t

    def msd(self) -> dict:
        if self._msd_ref is None:
            raise RuntimeError("call msd_origin() first")
        dx = self.positions(True) - self._msd_ref
        return {"t": self._t - self._msd_t0, "msd": float(np.mean(np.einsum("ij,ij->i", dx, dx))), "n": self.n}

    def velocity_ks(self, species=None, T=None, alpha=0.01) -> dict:
        """As ``MD.velocity_ks``: every component divided by sqrt(T/m) of its own mass, pooled over ``species`` (a
        name, a list, or None: all), against N(0, 1); T given or the sample's 2K/(d n); empty: D None."""
        from .observables import ks_gaussian
        sel = np.ones(self.n, bool)
        if species is not None:
            names = [species] if isinstance(species, str) else list(species)
            sel &= np.isin(self._typ, [self._species_index(nm) for nm in names])
        m = self._mass()[sel]
        v = self._v[sel]
        if T is None:
            T = float(np.sum(m[:, None] * v * v)) / v.size if v.size else float("nan")
        if not v.size or not (T > 0):
            return ks_gaussian(np.zeros(0), 1.0, alpha=alpha)
        return ks_gaussian((v * np.sqrt(m / T)[:, None]).reshape(-1), 1.0, alpha=alpha)

    def particles(self, keys=None) -> dict:
        """Keys, positions (at the world time), velocities and species names of the particles (all, or ``keys``)."""
        rows = np.arange(self.n) if keys is None else self._rows(keys)
        return {"keys": self._key[rows].copy(), "x": self.positions()[rows], "v": self._v[rows].copy(),
                "species": [self._species[t]["name"] for t in self._typ[rows]]}

    def probe(self, center, radius) -> dict:
        """As ``MD.probe``: number, density over the ball's part inside the walls and 2K/(d n) of the particles whose
        centres lie within the ball (minimum image on periodic axes)."""
        return _probe(self.positions(), self._v, self._mass(), self.L, self.periodic, center, radius)

    def cost_estimate(self) -> dict:
        """Measured seconds per processed event and events per unit time (this run)."""
        ev = self._stats["events"]
        sec = self._stats["seconds"]
        dt = self._t - self._acc["t0"]
        rate = self._acc["collisions"] / dt if dt > 0 else None
        return {"s_per_event": sec / ev if ev else None, "collisions_per_time": rate, "n": self.n,
                "events": ev, "stale": self._stats["stale"], "device": "cpu"}

    # --- state -----------------------------------------------------------------------------------------------------
    def state_dict(self) -> dict:
        H = self._heap
        return {"format": _FORMAT, "dim": self.dim, "L": self.L.copy(), "periodic": self.periodic.copy(),
                "walls_on": self.walls_on,
                "rng": self.rng.bit_generator.state, "species": [dict(s) for s in self._species],
                "key": self._key.copy(), "typ": self._typ.copy(), "x": self._x.copy(), "v": self._v.copy(),
                "tl": self._tl.copy(), "img": self._img.copy(), "cell": self._cell.copy(), "cnt": self._cnt.copy(),
                "next_key": self._next_key, "t": self._t, "t_ev": self._t_ev,
                "walls": {k: dict(w) for k, w in self._walls.items()},
                "heap_t": np.array([e[0] for e in H], float),
                "heap_i": np.array([e[1:] for e in H], np.int64).reshape(-1, 6), "seq": self._seq,
                "acc": {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in self._acc.items()},
                "stats": dict(self._stats), "K": self._K, "Ka": self._Ka.copy(),
                "msd_ref": None if self._msd_ref is None else self._msd_ref.copy(), "msd_t0": self._msd_t0}

    @classmethod
    def from_state_dict(cls, d) -> "HardSpheres":
        if d.get("format") != _FORMAT:
            raise ValueError(f"not an {_FORMAT} state")
        o = cls.__new__(cls)
        o.dim = int(d["dim"])
        o.L = np.array(d["L"], float)
        o.periodic = np.array(d["periodic"], bool)
        o.walls_on = d.get("walls_on", "surface")
        o.rng = np.random.Generator(np.random.PCG64())
        o.rng.bit_generator.state = copy.deepcopy(d["rng"])
        o._species = [dict(s) for s in d["species"]]
        n = len(d["key"])
        dd = o.dim
        o._key = np.array(d["key"], np.int64)
        o._typ = np.array(d["typ"], np.int64)
        o._x = np.array(d["x"], float).reshape(n, dd)
        o._v = np.array(d["v"], float).reshape(n, dd)
        o._tl = np.array(d["tl"], float)
        o._img = np.array(d["img"], np.int64).reshape(n, dd)
        o._cell = np.array(d["cell"], np.int64).reshape(n, dd)
        o._cnt = np.array(d["cnt"], np.int64)
        o._next_key = int(d["next_key"])
        o._t, o._t_ev = float(d["t"]), float(d["t_ev"])
        o._walls = {k: dict(w) for k, w in d["walls"].items()}
        hi = np.array(d["heap_i"], np.int64).reshape(-1, 6)
        o._heap = [(float(t),) + tuple(int(z) for z in row) for t, row in zip(np.array(d["heap_t"], float), hi)]
        heapq.heapify(o._heap)
        o._seq = int(d["seq"])
        o._acc = {k: (np.array(v, float) if k in ("Kadt", "Wa") else v) for k, v in d["acc"].items()}
        o._stats = dict(d["stats"])
        o._K = float(d["K"])
        o._Ka = np.array(d["Ka"], float) if d.get("Ka") is not None else (
            0.5 * np.einsum("i,ij->j", np.array([s["mass"] for s in o._species])[o._typ], o._v * o._v) if n
            else np.zeros(dd))
        o._msd_ref = None if d["msd_ref"] is None else np.array(d["msd_ref"], float).reshape(n, dd)
        o._msd_t0 = d["msd_t0"]
        o._grid()
        o._cells = {}
        for r in range(n):
            o._cells.setdefault(o._flat(o._cell[r]), set()).add(r)
        return o

    def clone(self) -> "HardSpheres":
        return HardSpheres.from_state_dict(self.state_dict())


# --- switching the solver at the current moment (plan P16.1: soft <-> hard spheres in one world) -------------------------
def contact_violations(x, sigma, L, periodic, walled_hi=None, walls_on="surface") -> dict:
    """What keeps a configuration from being hard spheres of diameters ``sigma``: the pairs nearer than their contact
    distance (sigma_i + sigma_j)/2 (minimum image on periodic axes) and the centres beyond a wall's contact plane on a
    walled axis (walls at 0 and at ``walled_hi`` or L): sigma_i/2 from the wall with ``walls_on="surface"``, the wall
    itself with ``"centre"``. Returns {"pairs", "walls", "closest": the smallest r_ij / sigma_ij}."""
    x = np.asarray(x, float)
    sig = np.asarray(sigma, float).reshape(-1)
    L = np.asarray(L, float)
    periodic = np.asarray(periodic, bool)
    out = {"pairs": 0, "walls": 0, "closest": None}
    if len(x) == 0:
        return out
    hi = L if walled_hi is None else np.asarray(walled_hi, float)
    off = 0.5 * sig if walls_on == "surface" else 0.0 * sig
    for a in np.flatnonzero(~periodic):
        out["walls"] += int(np.sum((x[:, a] < off * (1 - 1e-12)) | (x[:, a] > hi[a] - off * (1 - 1e-12))))
    if len(x) > 1:
        i, j = cells.pair_list(x, L, periodic, float(sig.max()))
        if len(i):
            dx = x[j] - x[i]
            for a in np.flatnonzero(periodic):
                dx[:, a] -= L[a] * np.rint(dx[:, a] / L[a])
            r = np.sqrt(np.einsum("ij,ij->i", dx, dx))
            s = 0.5 * (sig[i] + sig[j])
            out["pairs"] = int(np.sum(r < s * (1.0 - 1e-12)))
            out["closest"] = float(np.min(r / s))
    return out


def hard_blockers(md) -> list:
    """What a ``system.MD`` holds that the hard-sphere solver has not (English names): molecules (bonds), a piston,
    thermostats, a field, soft walls, charges, frozen species."""
    out = []
    if len(md._bonds) or np.any(md._mol >= 0):
        out.append("molecules")
    if md.piston() is not None:
        out.append("piston")
    if md.thermostats():
        out.append("thermostats")
    if np.any(np.asarray(md.g) != 0.0):
        out.append("field")
    if any(w["kind"] == "soft" for w in md.walls().values()):
        out.append("soft walls")
    sp = md.species()
    if any(float(s.get("charge", 0.0)) != 0.0 for s in sp):
        out.append("charges")
    if any(not math.isfinite(float(s["mass"])) for s in sp):
        out.append("frozen species")
    return out


def hard_from_md(md, seed=0, walls_on="centre") -> "HardSpheres":
    """The same particles - keys, species (mass, sigma), positions, velocities, walls (specular, thermal) - as hard
    disks / spheres at the same time (the event-driven solver takes over a ``system.MD``). The walls act on the centres
    by default, as MD's hard walls do: the region of the centres - the density - is the same on both sides of the
    switch (review LB1-physics P4: with walls on the surfaces the switch was refused whenever a centre lay within
    sigma/2 of a wall, and when it was made the centres' region shrank by sigma at each walled axis). Refused
    (ValueError) with what blocks it (``hard_blockers``) and when particles overlap as hard bodies
    (``contact_violations``)."""
    bl = hard_blockers(md)
    if bl:
        raise ValueError("not in the hard-sphere solver: " + ", ".join(bl))
    p = md.particles()
    sp = md.species()
    names = [s["name"] for s in sp]
    sig = np.array([s["sigma"] for s in sp])
    typ = np.array([names.index(q) for q in p["species"]], np.int64)
    cv = contact_violations(p["x"], sig[typ] if len(typ) else np.zeros(0), md.L, md.periodic, walls_on=walls_on)
    if cv["pairs"] or cv["walls"]:
        raise ValueError(f"overlapping hard particles: {cv['pairs']} pairs nearer than contact, {cv['walls']} centres "
                         f"beyond a wall's contact plane")
    hs = HardSpheres(md.dim, md.L.copy(), ["periodic" if q else "walls" for q in md.periodic], seed=seed, t=md.t,
                     walls_on=walls_on)
    for s in sp:
        hs.add_species(s["name"], mass=s["mass"], sigma=s["sigma"])
    for k, w in md.walls().items():
        if w["kind"] == "thermal":
            hs.set_wall(k[0], k[2:], "thermal", T=w["T"])
    hs.adopt(p["keys"], typ, p["x"], p["v"], next_key=int(md._next_key))
    hs.reset_counters()
    hs.msd_origin()
    return hs


def md_from_hard(hs, pair, dt, seed=0, species_extra=None, **kwargs):
    """The same particles of a ``HardSpheres`` - keys, species, positions, velocities, walls - as a ``system.MD`` with
    the pair model ``pair`` and the time step ``dt`` at the same time. ``species_extra``: {name: {"epsilon", "charge"}}
    (default 1, 0). Always possible for a pair model that is finite at contact (no pair of hard bodies is nearer than
    contact); the potential energy appears (the returned system's energy minus the hard bodies' kinetic energy). MD's
    hard walls act on the centres: from a hard system with walls on the surfaces (``walls_on="surface"``) the region the
    centres may take grows by sigma/2 at each wall (the returned system's attribute ``centres_region_grew`` is True
    then; ``hard_from_md``'s systems have walls on the centres and nothing changes)."""
    from .system import MD
    md = MD(hs.dim, hs.L.copy(), ["periodic" if q else "walls" for q in hs.periodic], pair=pair, dt=dt, seed=seed,
            t=hs.t, **kwargs)
    extra = species_extra or {}
    for s in hs.species():
        e = extra.get(s["name"], {})
        md.add_species(s["name"], mass=s["mass"], sigma=s["sigma"], epsilon=float(e.get("epsilon", 1.0)),
                       charge=float(e.get("charge", 0.0)))
    for k, w in hs._walls.items():
        if w["kind"] == "thermal":
            md.set_wall(k[0], k[2:], "thermal", T=w["T"])
    p = hs.particles()
    names = [s["name"] for s in hs.species()]
    typ = np.array([names.index(q) for q in p["species"]], np.int64)
    md.adopt(p["keys"], typ, p["x"], p["v"], next_key=int(hs._next_key))
    md.reset_counters()
    md.msd_origin()
    md.centres_region_grew = bool(hs.walls_on == "surface" and not np.all(hs.periodic))
    return md
