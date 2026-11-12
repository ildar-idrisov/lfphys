# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Phenomenological interatomic potentials for the molecular dynamics of ``lfphys.core.md`` (plan P8, P15.4).

Why these are models and the dynamics is core (LAYERS.md §1). The equations of motion, the integrators, the ensembles
and the statistical mechanics measured from a run (``core.md``) are established physics computed with a stated error,
for any Hamiltonian. The functional forms below are fitted phenomenology: the r^-12 repulsion of Lennard-Jones has no
derivation (the true repulsion is close to exponential), argon's well is shallower and wider than the 12-6 well, real
atoms have three-body forces (Axilrod-Teller), real bonds are anharmonic (Morse) and break. So they live in
``theories.models`` and the core takes them by injection: ``core.md.MD(pair=LennardJones(...))``,
``md.set_bond_type("b", HarmonicBond(...))``, ``md.set_wall(..., term=LJWall(...))``. The core imports nothing from
here (a saved state names its terms by module and class and is restored through ``importlib``).

Every term returns its energy and minus its derivative, and the forces are exactly the gradient of the energy
(tests: central differences and the complex-step derivative). Parameters are in the engine's reduced units
(``core.md.units``: length sigma0, energy epsilon0, mass m0, k_B = 1).

Pair terms (``tables(sigma, epsilon)`` per species -> (ns, ns) tables; ``evaluate(r2, P)`` -> (u, fr) with
fr = -u'(r)/r, so that the force on i from j is -fr (x_j - x_i)):

* ``LennardJones(cutoff=2.5, shift="energy")``: u = 4 eps_ij [(s_ij/r)^12 - (s_ij/r)^6] for r < r_c, zero beyond.
  ``shift="energy"``: u - u(r_c) (the energy is continuous; the force is that of the plainly truncated potential, so
  the trajectories are those of "truncated" MD, e.g. NIST's 3 sigma benchmarks); ``"force"``: the linear force shift
  u - u(r_c) - (r - r_c) u'(r_c) (energy and force continuous; NIST's "linear-force shifted" benchmarks); ``"none"``:
  plainly truncated (the energy jumps by u(r_c) at the cut: the integrator then conserves the energy-shifted
  Hamiltonian, which ``MD.potential_energy`` reports next to the truncated one). The cutoff is a multiple of s_ij
  (``relative_cutoff=True``, default) or a length. Mixing (stated choice): Lorentz-Berthelot s_ij = (s_i + s_j)/2,
  eps_ij = sqrt(eps_i eps_j) (``mixing="lorentz-berthelot"``) or geometric s_ij = sqrt(s_i s_j); any pair can be set
  explicitly (``overrides={(a, b): (sigma, epsilon)}`` by species index). Long-range tail corrections of the full
  12-6 potential beyond r_c with g(r) = 1 (``tail``): in d = 3, U/N = (8/3) pi rho eps s^3 [(1/3)(s/r_c)^9 -
  (s/r_c)^3], p = (16/3) pi rho^2 eps s^3 [(2/3)(s/r_c)^9 - (s/r_c)^3]; in d = 2, U/N = pi rho eps s^2 [(2/5)
  (s/r_c)^10 - (s/r_c)^4], p = (pi/2) rho^2 4 eps s^2 [(6/5)(s/r_c)^10 - (3/2)(s/r_c)^4] (mixtures: summed over
  species pairs with N_a N_b / V). Not defined for the force-shifted form (it differs from 12-6 inside r_c too).
* ``WCA()``: Weeks-Chandler-Andersen: the 12-6 potential cut at its minimum 2^(1/6) s_ij and shifted up by eps_ij -
  purely repulsive, continuous force.
* ``SoftRepulsion(alpha=2)``: u = (eps_ij/alpha) (1 - r/s_ij)^alpha for r < s_ij (alpha = 2 harmonic spheres, 5/2
  Hertzian); finite at r = 0, so overlapping particles can be inserted live and pushed apart.

Bonded terms (by bond or angle type; bonds ``evaluate(r)`` -> (u, -u'(r)); angles ``evaluate(theta, cos theta)`` ->
(u, du/d cos theta), from which the core takes the forces on the three atoms):

* ``HarmonicBond(k, r0)``: u = (k/2)(r - r0)^2. ``FENE(k, R0)``: u = -(k/2) R0^2 ln(1 - (r/R0)^2), r < R0 (the bond
  breaks the step - FloatingPointError - at r >= R0; Kremer & Grest 1990 use k = 30 eps/s^2, R0 = 1.5 s with WCA
  between all beads).
* ``HarmonicAngle(k, theta0)``: u = (k/2)(theta - theta0)^2; ``CosineAngle(k, theta0)``: u = (k/2)(cos theta -
  cos theta0)^2 (regular at theta = 0, pi).

Wall terms (``evaluate(z, P)`` -> (u, -u'(z)) at the distance z > 0 from the wall plane): ``LJWall`` - the 12-6
potential integrated over a half-space of wall atoms of number density rho_w (derived here):

    d = 3 ("9-3"): U(z) = eps_w [(2/15)(s_w/z)^9 - (s_w/z)^3],     eps_w = (2 pi/3) rho_w eps s^3,
    d = 2 ("10-4"): U(z) = eps_w [(21/80)(s_w/z)^10 - (s_w/z)^4],   eps_w = (3 pi/8) rho_w eps s^2

(d = 3: the integral of 4 eps [(s/r)^12 - (s/r)^6] over a plane gives 4 pi eps [s^12/(5 z^10) - s^6/(2 z^4)] per unit
area density, and over the depth 4 pi eps rho_w [s^12/(45 z^9) - s^6/(6 z^3)]; d = 2: over a line (63 pi/256) s^12
z^-11 and (3 pi/8) s^6 z^-5, then over the depth). Cut at ``cutoff`` (a multiple of s_w; ``"min"`` = at the minimum,
z_min = (2/5)^(1/6) s_w in d = 3 and (21/32)^(1/6) s_w in d = 2: purely repulsive) and shifted to zero there.
Optionally mixed with each species (``mixing=True``: s = (s_w + s_i)/2, eps = sqrt(eps_w eps_i)).

Argon (``ARGON``, ``argon_units``): sigma = 3.405 Angstrom, eps/k_B = 119.8 K (Hirschfelder, Curtiss & Bird, as
tabulated in arXiv:2511.14399, Table 1; Michels et al. 1949 via arXiv:cond-mat/0212198 give 3.405 Angstrom and
0.01034 eV = 120.0 K), m = 39.948 u (CIAAW 1979 value 39.948(1), the value used with these parameters; the standard
atomic weight is the interval [39.792, 39.963] since 2017): ``sources/verification_2026-11-04_p8_md.md``.
"""

from __future__ import annotations

import math

import numpy as np

ABOUT = {
    "layer": "theories", "kind": "model",
    "title": "Межатомные потенциалы: Леннард-Джонс, WCA, мягкие сферы, связи, углы, стенки",
    "statement": "Феноменологические потенциалы для молекулярной динамики ядра (core.md): Леннард-Джонс 12-6 с "
                 "обрезкой (сдвиг энергии или линейный сдвиг силы; правило смешивания Лоренца–Бертло или "
                 "геометрическое; поправки дальнего хвоста), WCA, мягкое отталкивание (гармоническое, Герц), "
                 "гармоническая связь и FENE, гармонический угол (по углу или по косинусу), стенки Леннард-Джонса "
                 "9-3 (3-D) и 10-4 (2-D), выведенные интегрированием 12-6 по полупространству; параметры аргона. "
                 "Сила — точный градиент энергии.",
    "validity": "подогнанные формы: отталкивание r^-12 не выведено (истинное близко к экспоненциальному), у аргона яма "
                "мельче и шире 12-6, нет трёхчастичных сил (Аксильрод–Теллер) и квантовых поправок (для лёгких атомов "
                "и низких T); связи гармонические (не рвутся; FENE рвёт шаг), углы гармонические; стенка — "
                "сплошная среда атомов стенки. Параметры аргона воспроизводят второй вириальный коэффициент и "
                "свойства жидкости с точностью процентов",
    "basis": ["Lennard-Jones, Proc. R. Soc. A 106, 463 (1924)",
              "Weeks, Chandler & Andersen, J. Chem. Phys. 54, 5237 (1971)",
              "Kremer & Grest, J. Chem. Phys. 92, 5057 (1990): FENE + WCA",
              "Steele, Surf. Sci. 36, 317 (1973): стенка 9-3 (здесь выведена заново)",
              "NIST SRS: эталоны LJ (усечение 3σ + хвост; линейный сдвиг силы 2.5σ)",
              "аргон: Hirschfelder, Curtiss & Bird (через arXiv:2511.14399); CIAAW"],
    "conflicts": ["реальный аргон: потенциал Азиза (HFDID) и трёхчастичная поправка Аксильрода–Теллера дают "
                  "давление и критическую точку иначе, чем 12-6 (критическая T для 12-6 — 1.312 ε/k, т.е. 157 K "
                  "против 150.7–150.9 K у аргона по NIST WebBook)",
                  "обрезанный и сдвинутый потенциал — другая модель, чем полный 12-6: фазовая диаграмма зависит от "
                  "r_c (3-D: критическая T при линейном сдвиге силы 2.5σ — 0.937, тройная точка 0.560 — у полного "
                  "1.312 и 0.687; 2-D: у полного 0.515, у обрезанного на 2.5σ со сдвигом энергии 0.459, тройная "
                  "около 0.42 — жидкость и пар на плоскости сосуществуют лишь в узком интервале)",
                  "гармоническая связь не рвётся и не ангармонична (Морзе, квантовые колебания при ħω > kT)"],
}

_SHIFTS = ("energy", "force", "none")


def _mix(sigma, epsilon, mixing, overrides):
    s = np.asarray(sigma, float)
    e = np.asarray(epsilon, float)
    if mixing == "lorentz-berthelot":
        S = 0.5 * (s[:, None] + s[None, :])
    elif mixing == "geometric":
        S = np.sqrt(s[:, None] * s[None, :])
    else:
        raise ValueError("mixing must be 'lorentz-berthelot' or 'geometric'")
    E = np.sqrt(e[:, None] * e[None, :])
    for (a, b), (sab, eab) in (overrides or {}).items():
        a, b = int(a), int(b)
        if a < len(s) and b < len(s):
            S[a, b] = S[b, a] = float(sab)
            E[a, b] = E[b, a] = float(eab)
    return S, E


def _ov_list(overrides):
    return [[int(a), int(b), float(s), float(e)] for (a, b), (s, e) in sorted((overrides or {}).items())]


class LennardJones:
    """Truncated 12-6 Lennard-Jones pair term (see the module docstring)."""

    kind = "pair"

    def __init__(self, cutoff=2.5, shift="energy", mixing="lorentz-berthelot", relative_cutoff=True, overrides=None):
        if shift not in _SHIFTS:
            raise ValueError(f"shift must be one of {_SHIFTS}")
        if not (float(cutoff) > 0 and math.isfinite(float(cutoff))):
            raise ValueError("cutoff must be finite and > 0")
        if mixing not in ("lorentz-berthelot", "geometric"):
            raise ValueError("mixing must be 'lorentz-berthelot' or 'geometric'")
        self.cutoff = float(cutoff)
        self.shift = shift
        self.mixing = mixing
        self.relative_cutoff = bool(relative_cutoff)
        self.overrides = {(int(a), int(b)): (float(s), float(e)) for (a, b), (s, e) in (overrides or {}).items()}
        for (s, e) in self.overrides.values():
            if not (s > 0 and e >= 0):
                raise ValueError("override sigma must be > 0 and epsilon >= 0")

    def params(self) -> dict:
        return {"cutoff": self.cutoff, "shift": self.shift, "mixing": self.mixing,
                "relative_cutoff": self.relative_cutoff, "overrides": _ov_list(self.overrides)}

    @classmethod
    def from_params(cls, p):
        ov = {(a, b): (s, e) for a, b, s, e in p.get("overrides", [])}
        return cls(p["cutoff"], p["shift"], p["mixing"], p["relative_cutoff"], ov)

    def tables(self, sigma, epsilon) -> dict:
        """(ns, ns) parameter tables: rc (the cutoff), and what ``evaluate`` needs: s2, eps4, rc2, ushift, fshift."""
        S, E = _mix(sigma, epsilon, self.mixing, self.overrides)
        rc = self.cutoff * S if self.relative_cutoff else np.full_like(S, self.cutoff)
        x6 = (S / rc) ** 6
        uc = 4.0 * E * (x6 * x6 - x6)                      # u(rc)
        duc = -4.0 * E * (12.0 * x6 * x6 - 6.0 * x6) / rc   # u'(rc)
        if self.shift == "energy":
            ushift, fshift = uc, np.zeros_like(uc)
        elif self.shift == "force":
            ushift, fshift = uc, duc
        else:
            ushift, fshift = np.zeros_like(uc), np.zeros_like(uc)
        return {"rc": rc, "rc2": rc * rc, "s2": S * S, "eps4": 4.0 * E, "ushift": ushift, "fshift": fshift,
                "uc": uc, "sigma": S, "epsilon": E}

    def evaluate(self, r2, P):
        """Pair energies u and fr = -u'(r)/r at squared distances r2 (zero at r >= r_c). P: per-pair (or scalar)
        values of the tables (s2, eps4, rc2, ushift, fshift; rc for the force shift)."""
        inside = r2 < P["rc2"]
        r2s = np.where(inside, r2, P["rc2"])
        q = P["s2"] / r2s
        q6 = q * q * q
        u = P["eps4"] * (q6 * q6 - q6) - P["ushift"]
        fr = P["eps4"] * (12.0 * q6 * q6 - 6.0 * q6) / r2s
        if self.shift == "force":
            r = np.sqrt(r2s)
            rc = np.sqrt(P["rc2"])
            u = u - (r - rc) * P["fshift"]
            fr = fr + P["fshift"] / r
        return np.where(inside, u, 0.0), np.where(inside, fr, 0.0)

    def tail(self, tables, counts, volume, dim):
        """(U_tail, p_tail): the full 12-6 potential beyond r_c with g = 1 (summed over species pairs, N_a N_b / V).
        Zero for the force-shifted form (not a correction to 12-6) and for a relative cutoff of an absent pair."""
        if self.shift == "force":
            return 0.0, 0.0
        n = np.asarray(counts, float)
        S, E, rc = tables["sigma"], tables["epsilon"], tables["rc"]
        x = S / rc
        NN = n[:, None] * n[None, :]
        if dim == 3:
            iu = 4.0 * E * S ** 3 * (x ** 9 / 9.0 - x ** 3 / 3.0)            # int r^2 u dr
            ip = 4.0 * E * S ** 3 * (-(4.0 / 3.0) * x ** 9 + 2.0 * x ** 3)   # int r^3 u' dr
            U = 2.0 * math.pi / volume * float(np.sum(NN * iu))
            p = -2.0 * math.pi / (3.0 * volume ** 2) * float(np.sum(NN * ip))
        elif dim == 2:
            iu = 4.0 * E * S ** 2 * (x ** 10 / 10.0 - x ** 4 / 4.0)          # int r u dr
            ip = 4.0 * E * S ** 2 * (-(6.0 / 5.0) * x ** 10 + 1.5 * x ** 4)  # int r^2 u' dr
            U = math.pi / volume * float(np.sum(NN * iu))
            p = -math.pi / (2.0 * volume ** 2) * float(np.sum(NN * ip))
        else:
            raise ValueError("dim must be 2 or 3")
        return U, p


class WCA(LennardJones):
    """Weeks-Chandler-Andersen: 12-6 cut at its minimum 2^(1/6) s_ij and shifted by eps_ij (purely repulsive)."""

    def __init__(self, mixing="lorentz-berthelot", overrides=None):
        super().__init__(2.0 ** (1.0 / 6.0), "energy", mixing, True, overrides)

    def params(self) -> dict:
        return {"mixing": self.mixing, "overrides": _ov_list(self.overrides)}

    @classmethod
    def from_params(cls, p):
        return cls(p["mixing"], {(a, b): (s, e) for a, b, s, e in p.get("overrides", [])})

    def tail(self, tables, counts, volume, dim):
        return 0.0, 0.0


class SoftRepulsion:
    """u = (eps_ij/alpha)(1 - r/s_ij)^alpha for r < s_ij (alpha = 2: harmonic spheres; 2.5: Hertz)."""

    kind = "pair"

    def __init__(self, alpha=2.0, mixing="lorentz-berthelot", overrides=None):
        if not float(alpha) > 1.0:
            raise ValueError("alpha must be > 1 (a continuous force)")
        self.alpha = float(alpha)
        self.mixing = mixing
        self.overrides = {(int(a), int(b)): (float(s), float(e)) for (a, b), (s, e) in (overrides or {}).items()}

    def params(self) -> dict:
        return {"alpha": self.alpha, "mixing": self.mixing, "overrides": _ov_list(self.overrides)}

    @classmethod
    def from_params(cls, p):
        return cls(p["alpha"], p["mixing"], {(a, b): (s, e) for a, b, s, e in p.get("overrides", [])})

    def tables(self, sigma, epsilon) -> dict:
        S, E = _mix(sigma, epsilon, self.mixing, self.overrides)
        return {"rc": S.copy(), "rc2": S * S, "sig": S, "eps": E, "ushift": np.zeros_like(S), "sigma": S,
                "epsilon": E}

    def evaluate(self, r2, P):
        inside = r2 < P["rc2"]
        r = np.sqrt(np.where(inside, r2, P["rc2"]))
        y = 1.0 - r / P["sig"]
        a = self.alpha
        u = P["eps"] / a * y ** a
        # -u'(r)/r = eps (1 - r/s)^(a-1) / (s r); at r = 0 the force direction is undefined: zero there
        rr = np.where(r > 0.0, r, 1.0)
        fr = np.where(r > 0.0, P["eps"] * y ** (a - 1.0) / (P["sig"] * rr), 0.0)
        return np.where(inside, u, 0.0), np.where(inside, fr, 0.0)

    def tail(self, tables, counts, volume, dim):
        return 0.0, 0.0


# --- bonded terms --------------------------------------------------------------------------------------------------
class HarmonicBond:
    """u = (k/2)(r - r0)^2."""

    kind = "bond"

    def __init__(self, k, r0):
        if not (float(k) >= 0 and float(r0) >= 0):
            raise ValueError("k and r0 must be >= 0")
        self.k, self.r0 = float(k), float(r0)

    def params(self):
        return {"k": self.k, "r0": self.r0}

    @classmethod
    def from_params(cls, p):
        return cls(p["k"], p["r0"])

    def evaluate(self, r):
        d = r - self.r0
        return 0.5 * self.k * d * d, -self.k * d

    def omega2(self, mu):
        """Closed-form squared angular frequency k/mu of a free diatomic of reduced mass mu (small vibrations)."""
        return self.k / mu


class FENE:
    """Finitely extensible nonlinear elastic bond: u = -(k/2) R0^2 ln(1 - (r/R0)^2) for r < R0."""

    kind = "bond"

    def __init__(self, k=30.0, R0=1.5):
        if not (float(k) > 0 and float(R0) > 0):
            raise ValueError("k and R0 must be > 0")
        self.k, self.R0 = float(k), float(R0)

    def params(self):
        return {"k": self.k, "R0": self.R0}

    @classmethod
    def from_params(cls, p):
        return cls(p["k"], p["R0"])

    def evaluate(self, r):
        x = (np.asarray(r, float) / self.R0) ** 2
        if np.any(x >= 1.0):
            raise FloatingPointError("a FENE bond stretched to R0 (the bond broke)")
        return -0.5 * self.k * self.R0 ** 2 * np.log1p(-x), -self.k * r / (1.0 - x)


class HarmonicAngle:
    """u = (k/2)(theta - theta0)^2 (theta in radians)."""

    kind = "angle"

    def __init__(self, k, theta0):
        if not (float(k) >= 0 and 0.0 <= float(theta0) <= math.pi):
            raise ValueError("k >= 0, 0 <= theta0 <= pi")
        self.k, self.theta0 = float(k), float(theta0)

    def params(self):
        return {"k": self.k, "theta0": self.theta0}

    @classmethod
    def from_params(cls, p):
        return cls(p["k"], p["theta0"])

    def evaluate(self, theta, cos):
        """(u, du/dcos): the core needs the derivative with respect to cos(theta); -u'(theta)/... handled there.
        du/dcos = du/dtheta / (-sin theta), regularised at sin = 0 by the limit when theta0 = 0 or pi."""
        d = theta - self.theta0
        u = 0.5 * self.k * d * d
        s = np.sqrt(np.maximum(1.0 - cos * cos, 0.0))
        tiny = 1e-12
        if self.theta0 in (0.0, math.pi):
            # (theta - theta0)/sin(theta) -> +-1 as theta -> theta0; use the exact ratio where sin is not tiny
            ratio = np.where(s > tiny, d / np.where(s > tiny, s, 1.0), -1.0 if self.theta0 == math.pi else 1.0)
            return u, -self.k * ratio
        return u, -self.k * d / np.maximum(s, tiny)

    def omega2_fixed_centre(self, m, r0):
        """Closed-form squared bending frequency 2k/(m r0^2) of two outer atoms of mass m at distance r0 from a fixed
        central atom (small vibrations: bending and stretching decouple at linear order)."""
        return 2.0 * self.k / (m * r0 * r0)


class CosineAngle:
    """u = (k/2)(cos theta - cos theta0)^2."""

    kind = "angle"

    def __init__(self, k, theta0):
        if not (float(k) >= 0 and 0.0 <= float(theta0) <= math.pi):
            raise ValueError("k >= 0, 0 <= theta0 <= pi")
        self.k, self.theta0 = float(k), float(theta0)
        self._c0 = math.cos(self.theta0)

    def params(self):
        return {"k": self.k, "theta0": self.theta0}

    @classmethod
    def from_params(cls, p):
        return cls(p["k"], p["theta0"])

    def evaluate(self, theta, cos):
        d = cos - self._c0
        return 0.5 * self.k * d * d, self.k * d


# --- walls ---------------------------------------------------------------------------------------------------------
class LJWall:
    """Lennard-Jones wall: 9-3 (d = 3) or 10-4 (d = 2), cut at ``cutoff`` s_w (or ``"min"``) and shifted (see the
    module docstring). ``eps_w`` is the prefactor of the formula; ``from_density`` builds it from the wall atoms'
    density rho_w and their 12-6 parameters."""

    kind = "wall"
    _FORMS = {3: (2.0 / 15.0, 9, 3), 2: (21.0 / 80.0, 10, 4)}

    def __init__(self, dim, epsilon=1.0, sigma=1.0, cutoff=2.5, mixing=False):
        if dim not in (2, 3):
            raise ValueError("dim must be 2 or 3")
        if not (float(epsilon) >= 0 and float(sigma) > 0):
            raise ValueError("epsilon >= 0, sigma > 0")
        self.dim = int(dim)
        self.epsilon, self.sigma = float(epsilon), float(sigma)
        a, n, m = self._FORMS[self.dim]
        zmin = (a * n / m) ** (1.0 / (n - m))   # in units of sigma
        if cutoff == "min":
            self.cutoff = "min"
            self._zc = zmin
        else:
            if not float(cutoff) > 0:
                raise ValueError("cutoff must be > 0 or 'min'")
            self.cutoff = float(cutoff)
            self._zc = float(cutoff)
        self.mixing = bool(mixing)

    @classmethod
    def from_density(cls, dim, rho_w, epsilon=1.0, sigma=1.0, cutoff=2.5, mixing=False):
        """eps_w = (2 pi/3) rho_w eps s^3 (d = 3) or (3 pi/8) rho_w eps s^2 (d = 2)."""
        pref = 2.0 * math.pi / 3.0 * rho_w * sigma ** 3 if dim == 3 else 3.0 * math.pi / 8.0 * rho_w * sigma ** 2
        return cls(dim, pref * epsilon, sigma, cutoff, mixing)

    def params(self):
        return {"dim": self.dim, "epsilon": self.epsilon, "sigma": self.sigma, "cutoff": self.cutoff,
                "mixing": self.mixing}

    @classmethod
    def from_params(cls, p):
        return cls(p["dim"], p["epsilon"], p["sigma"], p["cutoff"], p["mixing"])

    def tables(self, sigma, epsilon) -> dict:
        """Per species (ns,): zc (the cutoff distance), and what ``evaluate`` needs."""
        s = np.asarray(sigma, float)
        e = np.asarray(epsilon, float)
        if self.mixing:
            sw = 0.5 * (self.sigma + s)
            ew = np.sqrt(self.epsilon * e)
        else:
            sw = np.full_like(s, self.sigma)
            ew = np.full_like(s, self.epsilon)
        a, n, m = self._FORMS[self.dim]
        zc = self._zc * sw
        y = sw / zc
        uc = ew * (a * y ** n - y ** m)
        return {"zc": zc, "sw": sw, "ew": ew, "uc": uc}

    def evaluate(self, z, P):
        a, n, m = self._FORMS[self.dim]
        inside = z < P["zc"]
        zz = np.where(inside, z, P["zc"])
        y = P["sw"] / zz
        yn, ym = y ** n, y ** m
        u = P["ew"] * (a * yn - ym) - P["uc"]
        f = P["ew"] * (n * a * yn - m * ym) / zz       # -u'(z)
        return np.where(inside, u, 0.0), np.where(inside, f, 0.0)


# --- argon -----------------------------------------------------------------------------------------------------------
ARGON = {"sigma_angstrom": 3.405, "epsilon_kelvin": 119.8, "mass_amu": 39.948,
         "source": "sigma, eps/k_B: Hirschfelder, Curtiss & Bird (arXiv:2511.14399, Table 1); "
                   "mass: CIAAW 1979, 39.948(1); sources/verification_2026-11-04_p8_md.md"}


def argon_units():
    """The engine's reduced units with argon's 12-6 parameters (core.md.units.Units)."""
    from lfphys.core.md.units import Units
    return Units.from_lj(ARGON["sigma_angstrom"], ARGON["epsilon_kelvin"], ARGON["mass_amu"])
