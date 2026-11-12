# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Write player/js/tests/fixtures/message.bin with the Python codec (read back by the JS decoder test).

    python tests/make_js_fixture.py
"""
import argparse
from pathlib import Path

import numpy as np

from lfviz import protocol

OUT = Path(__file__).resolve().parents[1] / "player" / "js" / "tests" / "fixtures" / "message.bin"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    msg = protocol.encode({"type": "probe", "text": "кириллица ✓", "v": float("inf")},  # UTF-8, i18n-ok
                          {"f8": np.array([1.5, -2.25, 1e300]), "u1": np.array([1, 2, 3], np.uint8),
                           "f4": np.array([[0.5, 1.0, 2.0], [3.0, 4.0, 5.0]], np.float32),
                           "i4": np.array([-7, 8], np.int32)})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(msg)
    print(OUT, len(msg))


if __name__ == "__main__":
    main()
