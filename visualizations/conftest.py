# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""pytest configuration: make the server package, the visualization packages and the engine importable."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "server", ROOT.parent / "lfphys"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
