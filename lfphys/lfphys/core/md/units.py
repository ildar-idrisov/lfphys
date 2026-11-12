# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Units of the molecular dynamics (plan P8): reduced units and their exact conversions to physical units.

The MD engine works in reduced units: a length sigma0, an energy epsilon0, a mass m0 and k_B = 1. Derived units
(exact, from these three and CODATA constants through ``scipy.constants``):

    time         tau = sigma0 sqrt(m0 / epsilon0)
    temperature  epsilon0 / k_B
    velocity     sigma0 / tau = sqrt(epsilon0 / m0)
    force        epsilon0 / sigma0;  acceleration epsilon0 / (m0 sigma0)
    pressure     epsilon0 / sigma0^3 (d = 3);  epsilon0 / sigma0^2 (d = 2: a force per length)
    density      1 / sigma0^d
    diffusion    sigma0^2 / tau
    charge       q0 = sqrt(4 pi eps_vac sigma0 epsilon0)  (so that the Coulomb energy of q1, q2 at r is q1 q2 / r)

``Units.from_lj(sigma_angstrom, epsilon_kelvin, mass_amu)`` sets them from a Lennard-Jones parameter set; argon's is
in ``theories.models.interatomic.ARGON`` (a fitted model parameter set, so outside the core). The conversions are
exact up to the CODATA values (k_B, the atomic mass constant, e and eps_vac).
"""

from __future__ import annotations

import math

from scipy import constants as sc

ABOUT = {
    "layer": "core", "kind": "data",
    "title": "Единицы молекулярной динамики: приведённые и физические",
    "statement": "Приведённые единицы (σ0, ε0, m0, k_B = 1) и точные переводы в Å, пс, K, а.е.м., бар, элементарные "
                 "заряды, кг/м³, м²/с через постоянные CODATA.",
    "validity": "точно (в пределах значений CODATA); давление в 2-D — сила на единицу длины",
    "basis": ["CODATA через scipy.constants"],
    "conflicts": [],
}

ANGSTROM = 1e-10
PS = 1e-12
BAR = 1e5


class Units:
    """Reduced units with sigma0 [m], epsilon0 [J], m0 [kg]."""

    def __init__(self, sigma_m: float, epsilon_J: float, mass_kg: float):
        if not (sigma_m > 0 and epsilon_J > 0 and mass_kg > 0):
            raise ValueError("sigma, epsilon and mass must be > 0")
        self.sigma_m = float(sigma_m)
        self.epsilon_J = float(epsilon_J)
        self.mass_kg = float(mass_kg)

    @classmethod
    def from_lj(cls, sigma_angstrom, epsilon_kelvin, mass_amu):
        return cls(sigma_angstrom * ANGSTROM, epsilon_kelvin * sc.k, mass_amu * sc.atomic_mass)

    def params(self) -> dict:
        return {"sigma_m": self.sigma_m, "epsilon_J": self.epsilon_J, "mass_kg": self.mass_kg}

    # --- the derived units, in SI ----------------------------------------------------------------------------------
    @property
    def tau_s(self) -> float:
        return self.sigma_m * math.sqrt(self.mass_kg / self.epsilon_J)

    @property
    def temperature_K(self) -> float:
        return self.epsilon_J / sc.k

    @property
    def velocity_m_s(self) -> float:
        return math.sqrt(self.epsilon_J / self.mass_kg)

    @property
    def force_N(self) -> float:
        return self.epsilon_J / self.sigma_m

    @property
    def acceleration_m_s2(self) -> float:
        return self.epsilon_J / (self.mass_kg * self.sigma_m)

    def pressure_Pa(self, dim: int = 3) -> float:
        """The pressure unit: epsilon0/sigma0^3 Pa in d = 3; epsilon0/sigma0^2 N/m in d = 2."""
        return self.epsilon_J / self.sigma_m ** dim

    @property
    def charge_C(self) -> float:
        return math.sqrt(4.0 * math.pi * sc.epsilon_0 * self.sigma_m * self.epsilon_J)

    @property
    def diffusion_m2_s(self) -> float:
        return self.sigma_m ** 2 / self.tau_s

    # --- conversions -------------------------------------------------------------------------------------------------
    def to_angstrom(self, x):
        return x * (self.sigma_m / ANGSTROM)

    def from_angstrom(self, x):
        return x / (self.sigma_m / ANGSTROM)

    def to_ps(self, t):
        return t * (self.tau_s / PS)

    def from_ps(self, t):
        return t / (self.tau_s / PS)

    def to_kelvin(self, T):
        return T * self.temperature_K

    def from_kelvin(self, T):
        return T / self.temperature_K

    def to_amu(self, m):
        return m * (self.mass_kg / sc.atomic_mass)

    def from_amu(self, m):
        return m / (self.mass_kg / sc.atomic_mass)

    def to_bar(self, p):
        """Pressure in bar (d = 3)."""
        return p * self.pressure_Pa(3) / BAR

    def from_bar(self, p):
        return p / (self.pressure_Pa(3) / BAR)

    def to_elementary_charge(self, q):
        return q * self.charge_C / sc.e

    def from_elementary_charge(self, q):
        return q / (self.charge_C / sc.e)

    def to_kg_m3(self, rho, mass=1.0, dim=3):
        """Mass density of a number density rho (reduced) of particles of reduced mass ``mass`` (d = 3: kg/m^3)."""
        return rho * mass * self.mass_kg / self.sigma_m ** dim

    def to_m2_s(self, D):
        return D * self.diffusion_m2_s

    def to_kJ_mol(self, E):
        return E * self.epsilon_J * sc.N_A / 1e3

    def to_m_s(self, v):
        return v * self.velocity_m_s

    def from_m_s2(self, g):
        """A gravitational acceleration in m/s^2 to reduced units (Earth's 9.81 m/s^2 is ~1e-13 for argon)."""
        return g / self.acceleration_m_s2

    def table(self, dim: int = 3) -> dict:
        """The units in physical terms (for display)."""
        return {"sigma_angstrom": self.sigma_m / ANGSTROM, "epsilon_kelvin": self.temperature_K,
                "mass_amu": self.mass_kg / sc.atomic_mass, "tau_ps": self.tau_s / PS,
                "pressure_bar": self.pressure_Pa(3) / BAR if dim == 3 else None,
                "pressure_N_per_m": self.pressure_Pa(2) if dim == 2 else None,
                "velocity_m_s": self.velocity_m_s, "charge_e": self.charge_C / sc.e,
                "diffusion_m2_s": self.diffusion_m2_s}
