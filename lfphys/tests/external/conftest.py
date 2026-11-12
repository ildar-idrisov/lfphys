# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""pytest configuration of the comparison suite (plan item P13; README.md).

The suite runs only in the image lfphys-ext, which sets LFPHYS_EXTERNAL=1. ../conftest.py keeps the main suite
from collecting this folder. When the folder is named explicitly without the variable (e.g. ``pytest tests/external``
in the runtime image, where the libraries do not exist), its test modules are not collected either, and a header line
says why: nothing tries to import the libraries.

The SWIG-generated bindings of rundec 0.7 trigger a DeprecationWarning of Python 3.11 at import ("builtin type
swigvarlink has no __module__ attribute"); it concerns the bindings' packaging, not a result, and is filtered here.
"""

import os

ENABLED = os.environ.get("LFPHYS_EXTERNAL") == "1"
collect_ignore_glob = [] if ENABLED else ["test_ext_*.py"]


def pytest_report_header(config):
    if not ENABLED:
        return ("tests/external (comparison suite, plan P13) not collected: it runs only in the image "
                "lfphys-ext with LFPHYS_EXTERNAL=1 (tests/external/README.md)")
    return None


def pytest_configure(config):
    config.addinivalue_line("filterwarnings",
                            r"ignore:builtin type .* has no __module__ attribute:DeprecationWarning")
