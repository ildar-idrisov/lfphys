# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Weak-field gravity in the parametrized post-Newtonian (PPN) form: leading-order effects in terms of the PPN
parameters gamma (space curvature per unit mass) and beta (non-linearity). General relativity: gamma = beta = 1.

* light deflection at impact parameter b:      delta = (1 + gamma)/2 * 4 GM / (c^2 b);
* Shapiro delay of a radar echo r1 -> r2:      Delta t = (1 + gamma) GM / c^3 ln(4 r1 r2 / b^2)  (one way, b << r1, r2);
* periapsis advance per orbit:                Delta phi = (2 + 2 gamma - beta)/3 * 6 pi GM / (c^2 a (1 - e^2)).

These are expansions to first order in GM/(c^2 r); the exact general-relativistic values are in
lfphys.core.gravity (schwarzschild, orbits). gamma = 0 in the deflection reproduces the Newtonian corpuscle value
(Soldner), half the observed one.
"""

from __future__ import annotations

import math

from lfphys.i18n import T

from ...core.constants import C

ABOUT = {
    "layer": "theories", "kind": "approximation",
    "title": T("Weak field: the parametrised post-Newtonian formalism (PPN)"),
    "statement": T("First-order effects in GM/(c²r) through the parameters γ and β: deflection of light, Shapiro "
                   "delay, periapsis shift; GR: γ = β = 1."),
    "validity": T("weak field, GM/(c²r) ≪ 1 (the Solar System, binary pulsars at lowest order)"),
    "basis": ["Will, Living Rev. Relativ. 17, 4 (2014)", "Bertotti, Iess, Tortora, Nature 425, 374 (2003)"],
    "conflicts": [T("lfphys.core.gravity.orbits, schwarzschild: the exact GR values differ in a strong field (near "
                    "6M the expansion does not apply)")],
}


def deflection(gm: float, b: float, gamma: float = 1.0) -> float:
    return (1.0 + gamma) / 2.0 * 4.0 * gm / (C * C * b)


def shapiro_delay(gm: float, r1: float, r2: float, b: float, gamma: float = 1.0) -> float:
    return (1.0 + gamma) * gm / C**3 * math.log(4.0 * r1 * r2 / (b * b))


def periapsis_advance(gm: float, a: float, ecc: float, gamma: float = 1.0, beta: float = 1.0) -> float:
    return (2.0 + 2.0 * gamma - beta) / 3.0 * 6.0 * math.pi * gm / (C * C * a * (1.0 - ecc * ecc))
