# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Copenhagen (textbook) reading of measurement: a measurement has one outcome, drawn with the Born probability, and
the state is replaced by the projected state (collapse). It adds no prediction to the core's Born rule. The
conditional (Lueders) state itself is interpretation-neutral and lives in the core (``lfphys.core.quantum.qubits``:
the state to use for later predictions given the outcome; Everett calls it the relative state of the branch, Bohm
the effective wave function). What this module adds is the reading: the projection is a physical collapse of the
one real state, and what counts as a measurement is left open (the "Heisenberg cut"). (Wording clarified after the
review of 2026-10-23, E11.)
"""

from __future__ import annotations

import numpy as np

ABOUT = {
    "layer": "theories", "kind": "interpretation",
    "title": "Копенгагенская интерпретация: исход и коллапс состояния",
    "statement": "Измерение даёт один исход с вероятностью по правилу Борна; состояние заменяется спроецированным. "
                 "Граница «прибор — система» не определена теорией.",
    "validity": "те же предсказания, что у ядра, для всех исходов измерений",
    "basis": ["Bohr, Nature 121, 580 (1928)", "von Neumann, Mathematische Grundlagen der Quantenmechanik (1932)"],
    "conflicts": ["интерпретации Бома и Эверетта: нет коллапса; объективный коллапс (GRW) — другая динамика"],
}


def measure_and_collapse(psi, projectors, rng):
    """One outcome k ~ |Pi_k psi|^2 and the collapsed state Pi_k psi / |Pi_k psi| (pure states)."""
    psi = np.asarray(psi, complex)
    branches = [P @ psi for P in projectors]
    p = np.array([np.vdot(b, b).real for b in branches])
    k = int(rng.choice(len(p), p=p / p.sum()))
    return k, branches[k] / np.sqrt(p[k]), p


def position_detection(psi, x, rng, window: float):
    """Detection of a particle at a position (a screen): x_det ~ |psi|^2; the state collapses to a packet of the
    detector's resolution ``window`` around it (a Gaussian localisation)."""
    w = np.abs(psi) ** 2
    w = w / w.sum()
    i = int(rng.choice(len(x), p=w))
    post = psi * np.exp(-((x - x[i]) ** 2) / (4 * window**2))
    return float(x[i]), post / np.sqrt(np.sum(np.abs(post) ** 2) * (x[1] - x[0]))
