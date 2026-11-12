# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""pytest configuration: the engine package is importable from the repository (no install needed).

``tests/external`` (plan item P13) compares the engine with third-party libraries that exist only in the separate image
lfphys-ext (``tests/external/README.md``); it is collected only when LFPHYS_EXTERNAL=1 (set in that image), so
the main suite in the runtime image lfphys-viz never imports those libraries.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

collect_ignore = [] if os.environ.get("LFPHYS_EXTERNAL") == "1" else ["external"]
