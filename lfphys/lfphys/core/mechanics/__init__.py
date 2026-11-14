# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Classical mechanics of point bodies (plan M1, first scope: the projectile; design
``lfphys/sources/explore_2026-11-14_design.md`` §4).

* ``particle``: a point body in a uniform gravitational field with any declared forces, integrated by DOP853 with
  located events (landing, apex, declared ones), the forces' work carried along (the running energy balance), sampling
  on exact multiples of 1/rate, and the closed forms of the flight in vacuum.
* ``drag``: linear (Stokes) drag of a sphere, its Reynolds number along the path, and the closed forms of a flight
  with linear drag (the landing time from a height by Lambert's W).

The quadratic drag with a constant drag coefficient is a model with a fitted parameter and lives outside the core:
``lfphys.theories.models.drag_quadratic`` (it plugs into ``fly`` as a declared force). Springs, constraints,
collisions and rigid bodies are later modules of this package (``constraints.py``, ``contact.py``); they will not
change ``particle``'s interface.
"""

from .particle import (G_STANDARD, Body, Event, Flight, fly, vacuum_apex_height, vacuum_landing_time,  # noqa: F401
                       vacuum_state)
from .drag import (STOKES_RE_MAX, LinearDrag, air, linear_drag_apex_time, linear_drag_landing_time,  # noqa: F401
                   linear_drag_state, oseen_error, stokes_drag)
