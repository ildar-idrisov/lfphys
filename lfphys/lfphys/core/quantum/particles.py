# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Particles and their wave kinematics (relativistic throughout).

photon:  E = h nu = h c / lambda,  p = E / c,  group velocity c.
massive: E = E_kin + m c^2,  p c = sqrt(E^2 - m^2 c^4),  lambda = h / p (de Broglie),  v_g = p c^2 / E.

Masses: CODATA via scipy.constants (electron, neutron, atomic mass constant u). He-4 atom: 4.002 603 254 u
(atomic mass of 4He, AME 2020); C60: 720 u for the 12C60 isotopologue (12C has exactly 12 u by definition).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from scipy import constants as sc

ABOUT = {
    "layer": 'core', "kind": 'kinematics',
    "title": 'Частицы и волновая кинематика',
    "statement": 'Фотон: E = hν, p = E/c; массивная частица: p = √(E_k² + 2E_k mc²)/c, λ = h/p (де Бройль), групповая скорость pc²/E.',
    "validity": 'релятивистская кинематика свободной частицы',
    "basis": ['CODATA (scipy.constants)', 'AME 2020 (масса ⁴He)', 'Davisson–Germer 1927 (дифракция электронов)'],
    "conflicts": [],
}

H = sc.h
HBAR = sc.hbar
C = sc.c
E_CHARGE = sc.e
U = sc.physical_constants["atomic mass constant"][0]
EV = sc.electron_volt

SPECIES = {
    # id: (label, mass kg, charge in e, internal: "pol" | "spin" | None, nucleons)
    "photon": ("Фотон", 0.0, 0, "pol", 0),
    "electron": ("Электрон", sc.m_e, -1, "spin", 0),
    "neutron": ("Нейтрон", sc.m_n, 0, "spin", 1),
    "he4": ("Атом ⁴He", 4.002603254 * U, 0, None, 4),
    "c60": ("Фуллерен ¹²C₆₀", 720.0 * U, 0, None, 720),
    "custom": ("Своя частица", None, None, None, None),
}


@dataclass(frozen=True)
class Particle:
    species: str
    label: str
    mass: float  # kg
    charge: float  # C
    internal: str | None  # "pol" (photon polarization), "spin" (spin 1/2) or None (no internal state)
    nucleons: int
    lam: float  # m
    p: float  # kg m/s
    E: float  # total energy, J
    Ekin: float  # J
    v: float  # group velocity, m/s

    @property
    def k(self) -> float:
        return 2.0 * math.pi / self.lam

    @property
    def nu(self) -> float:
        return self.E / H

    def describe(self) -> dict:
        d = {"species": self.species, "label": self.label, "mass_kg": self.mass, "charge_e": self.charge / E_CHARGE,
             "internal": self.internal, "lambda_m": self.lam, "p": self.p, "E_eV": self.E / EV,
             "Ekin_eV": self.Ekin / EV, "v": self.v, "beta": self.v / C, "k": self.k, "nucleons": self.nucleons}
        d["nu_Hz"] = self.nu
        return d


def make(species: str, by: str, value: float, mass_u: float = 1.0, charge_e: float = 0.0,
         spin_half: bool = False) -> Particle:
    """by: "lambda" (m), "ekin" (eV; photon: photon energy), "speed" (m/s, massive only), "freq" (Hz, photon)."""
    if species not in SPECIES:
        raise ValueError(f"неизвестная частица {species}")
    label, m, q, internal, nuc = SPECIES[species]
    if species == "custom":
        m = mass_u * U
        q = charge_e
        internal = "spin" if spin_half else None
        nuc = int(round(mass_u))
        if m <= 0:
            raise ValueError("масса своей частицы должна быть > 0 (для безмассовой выберите фотон)")
    q = q * E_CHARGE
    if m == 0.0:
        if by == "lambda":
            lam = value
        elif by in ("ekin", "energy"):
            lam = H * C / (value * EV)
        elif by == "freq":
            lam = C / value
        else:
            raise ValueError("для фотона задайте длину волны, энергию или частоту")
        p = H / lam
        E = p * C
        return Particle(species, label, 0.0, 0.0, internal, 0, lam, p, E, E, C)
    mc2 = m * C * C
    if by == "lambda":
        p = H / value
        E = math.hypot(p * C, mc2)
    elif by == "ekin":
        ek = value * EV
        p = math.sqrt(ek * ek + 2.0 * ek * mc2) / C  # without the cancellation E^2 - (mc^2)^2 (review R5)
        E = math.hypot(p * C, mc2)
    elif by == "speed":
        b = value / C
        if not 0 < b < 1:
            raise ValueError("скорость массивной частицы должна быть в (0, c)")
        g = 1.0 / math.sqrt(1.0 - b * b)
        p = g * m * value
        E = g * mc2
    else:
        raise ValueError("для массивной частицы задайте длину волны, кинетическую энергию или скорость")
    if p <= 0:
        raise ValueError("импульс должен быть > 0")
    lam = H / p
    v = p * C * C / E
    ekin = (p * C) ** 2 / (E + mc2)  # = E - mc^2 without cancellation (slow neutrons, molecules)
    return Particle(species, label, m, q, internal, nuc, lam, p, E, ekin, v)
