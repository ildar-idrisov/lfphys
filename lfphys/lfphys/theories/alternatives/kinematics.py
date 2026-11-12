# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Pre-relativistic kinematics of light (alternatives to special relativity, kept for "what if" studies).

* ether:    Galilean transformations, absolute time; light moves at c relative to an ether at rest in the lab.
* emission: Galilean transformations; light moves at c relative to its SOURCE (Ritz-type ballistic theory):
            lab velocity = c n' + v_source.

Both are refuted: the ether by Michelson-Morley-type experiments (isotropy of the round-trip speed) and by time
dilation measurements; emission theory by binary-star timing (de Sitter 1913; Brecher 1977) and by gamma rays from
pi0 decays at 0.99975 c (Alväger et al. 1964), which move at c to 1e-4. In this engine they exist only as declared
modifications; a world using them is flagged "modified physics".
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.i18n import T

ABOUT = {
    "layer": "theories", "kind": "alternative",
    "title": T("The ether and the ballistic (Ritz) kinematics of light"),
    "statement": T("Galilean transformations and absolute time; light with the speed c relative to the ether (ether) "
                   "or relative to the source (ballistic)."),
    "validity": T("refuted; only for “what if” studies"),
    "basis": ["Michelson & Morley, Am. J. Sci. 34, 333 (1887)", "Alväger et al., Phys. Lett. 12, 260 (1964)",
              "Brecher, Phys. Rev. Lett. 39, 1051 (1977)"],
    "conflicts": [T("lfphys.core.relativity: a different kinematics (no time dilation; the speed of light depends on "
                    "the frame of reference or on the source)")],
}


def galilean_frame_matrix(v, c: float) -> np.ndarray:
    """Lab (ct, x, y) -> coordinates of a frame moving with lab velocity v: x' = x - v t, t' = t."""
    v = np.asarray(v, dtype=float)
    M = np.eye(3)
    M[1:, 0] = -v / c
    return M


def ether_emit_velocities(directions, v_source, c: float) -> np.ndarray:
    """Directions are taken in the ether (lab) frame; the speed is c whatever the source does."""
    return c * np.asarray(directions, dtype=float)


def emission_emit_velocities(directions_rest, v_source, c: float) -> np.ndarray:
    """c n' + v_source (Galilean addition)."""
    return c * np.asarray(directions_rest, dtype=float) + np.asarray(v_source, dtype=float)


def emission_front_arrival(c, t0, origin, w, wl, t_from=-math.inf):
    """Emission (Ritz) theory: light leaves at c relative to its source, so a flash's front is the sphere
    |x - origin - w (t - t0)| = c (t - t0) about the moving source (lab velocity w). Refuted (de Sitter 1913 binary
    stars; Alväger et al. 1964: photons from pi0 mesons moving at 0.99975 c travel at c). Geometry:
    ``lfphys.core.worldlines.sphere_meeting``."""
    from ...core.worldlines import sphere_meeting
    return sphere_meeting(c, t0, origin, np.asarray(w, float), wl, t_from)
