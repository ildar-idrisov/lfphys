# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Classical molecular dynamics (plan P8, P15.4): ``system.MD`` (soft potentials, molecules, walls, piston, NVE/NVT),
``hard.HardSpheres`` (event-driven hard disks and spheres), ``observables`` (statistical mechanics of a run),
``cells`` (neighbour search), ``units`` (reduced and physical units). The interatomic potentials themselves are
phenomenological models: ``lfphys.theories.models.interatomic`` (LAYERS.md)."""
