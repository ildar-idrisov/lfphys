# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""A modified Born rule: detection probability proportional to |psi|^p instead of |psi|^2.

With p != 2 the pattern of three slits is no longer the sum of the pairwise patterns (Sorkin's parameter is not
zero), and reading a which-path detector changes the screen distribution (signalling). Experiments bound such
higher-order interference: Sinha et al., Science 329, 418 (2010) (|kappa| < 1e-2 for photons in a triple slit);
later tests improved the bound.
"""

from __future__ import annotations

import numpy as np

from lfphys.i18n import T

ABOUT = {
    "layer": "theories", "kind": "alternative",
    "title": T("A modified Born rule: P ∝ |ψ|^p"),
    "statement": T("The detection probability is proportional to |ψ|^p; for p ≠ 2 third-order interference appears "
                   "(the Sorkin parameter ≠ 0) and signalling through reading the which-path detector."),
    "validity": T("only for “what if” studies; three-slit experiments bound the deviation from p = 2"),
    "basis": ["Sorkin, Mod. Phys. Lett. A 9, 3119 (1994)", "Sinha et al., Science 329, 418 (2010)"],
    "conflicts": [T("lfphys.core.quantum.marks: the Born rule P ∝ |ψ|²")],
}


def weight(I, p: float):
    """|psi|^p from the intensity I = |psi|^2 (I itself for the Born rule)."""
    return I if p == 2.0 else np.power(I, p / 2.0)
