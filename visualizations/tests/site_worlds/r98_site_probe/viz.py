# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""A tiny research world for the tests of the site's build (``tests/test_site_build.py``; found only through
``LFVIZ_EXTRA``): the point of ``u98_site_toy`` under a research audience, with its question and prior art."""

from __future__ import annotations

from lfviz.i18n import T
from u98_site_toy.viz import SCHEMA, Simulation as Toy


class Simulation(Toy):
    pass


VIZ = {"id": "r98_site_probe", "title": T("A probe for the tests of the site"), "summary": "", "purpose": "",
       "version": "1.0", "schema": SCHEMA, "simulation": Simulation, "audience": "research", "section": "mechanics",
       "teaser": T("A point moves; the question is a test's."), "related": ["u98_site_toy"],
       "question": T("Does the site's build carry a research world's question?"), "status": "hypothesis",
       "prior_art": [{"ref": "A test reference (2026)", "url": "https://example.org/"}],
       "recordings": [{"id": "only", "preset": "slow", "seconds": 1, "fps": 10, "speed": None, "seed": 1,
                       "poster": 0.5, "script": []}]}
