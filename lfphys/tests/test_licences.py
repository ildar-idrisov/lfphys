# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Licence-clean dependencies (plan item P12; owner, 2026-10-24; engine/AGENTS.md §3 rule 8).

Runs in the lfphys-viz image. Every package pinned in `visualizations/docker/requirements.lock` must have a row in
ALLOWED below and the same row in `sources/dependencies.md` §1. Its licence is read from the installed metadata
(License-Expression, else License, else the `License ::` classifiers); it must fall into the category of its row, and
that category must be allowed for the package's role. A pinned package that the image does not have (a CPU-only build
without the GPU packages) is skipped with a message. The audit behind the table: `sources/dependencies.md`.
"""

from __future__ import annotations

import importlib.metadata as md
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
LOCK_IN_ENGINE = Path("visualizations", "docker", "requirements.lock")
AUDIT = HERE.parents[1] / "sources" / "dependencies.md"

# --- the allow-table (keep in sync with sources/dependencies.md §1) ---------------------------------------------------

RUNTIME, RUNTIME_GPU, TEST_TOOLING = "runtime", "runtime-GPU", "test tooling"

# classes of a declared licence, from the most to the least permissive (AND takes the worst part, OR the best)
PERMISSIVE, WEAK, STRONG, PROPRIETARY, NONCOMMERCIAL, UNKNOWN = (
    "permissive", "weak copyleft", "strong copyleft", "proprietary", "noncommercial", "unknown")
NONE = "nothing declared"
RANK = {PERMISSIVE: 0, WEAK: 1, STRONG: 2, PROPRIETARY: 3, NONCOMMERCIAL: 4, UNKNOWN: 5}

# category of a row (the word used in dependencies.md) -> the class its declared licence must have
CATEGORY_CLASS = {
    "permissive": PERMISSIVE,
    "weak copyleft": WEAK,             # LGPL / MPL-2.0, used unmodified as a separate library
    "platform runtime": PROPRIETARY,   # vendor runtime whose terms permit commercial use (dependencies.md §3)
    "metadata only": NONE,             # installs no code
}
# categories allowed per role; strong copyleft, noncommercial and other proprietary licences are not allowed in this
# image at all (third-party comparison libraries live in the separate comparison suite, plan item P13)
ROLE_CATEGORIES = {
    RUNTIME: {"permissive", "weak copyleft", "metadata only"},
    RUNTIME_GPU: {"permissive", "weak copyleft", "platform runtime", "metadata only"},
    TEST_TOOLING: {"permissive", "weak copyleft"},
}
# the only vendor runtime audited (dependencies.md §3: the CUDA Toolkit EULA); another vendor needs its own audit first
PLATFORM_RUNTIME_NAME = re.compile(r"nvidia-[a-z0-9-]+-cu12")

ALLOWED = {
    "aiohappyeyeballs": (RUNTIME, "permissive"),
    "aiohttp": (RUNTIME, "permissive"),
    "aiosignal": (RUNTIME, "permissive"),
    "attrs": (RUNTIME, "permissive"),
    "cuda-pathfinder": (RUNTIME_GPU, "permissive"),
    "cuda-toolkit": (RUNTIME_GPU, "metadata only"),
    "cupy-cuda12x": (RUNTIME_GPU, "permissive"),
    "frozenlist": (RUNTIME, "permissive"),
    "idna": (RUNTIME, "permissive"),
    "iniconfig": (TEST_TOOLING, "permissive"),
    "mpmath": (RUNTIME, "permissive"),
    "multidict": (RUNTIME, "permissive"),
    "numpy": (RUNTIME, "permissive"),
    "nvidia-cublas-cu12": (RUNTIME_GPU, "platform runtime"),
    "nvidia-cuda-nvrtc-cu12": (RUNTIME_GPU, "platform runtime"),
    "nvidia-cuda-runtime-cu12": (RUNTIME_GPU, "platform runtime"),
    "nvidia-cufft-cu12": (RUNTIME_GPU, "platform runtime"),
    "nvidia-curand-cu12": (RUNTIME_GPU, "platform runtime"),
    "nvidia-cusolver-cu12": (RUNTIME_GPU, "platform runtime"),
    "nvidia-cusparse-cu12": (RUNTIME_GPU, "platform runtime"),
    "nvidia-nvjitlink-cu12": (RUNTIME_GPU, "platform runtime"),
    "packaging": (TEST_TOOLING, "permissive"),
    "pluggy": (TEST_TOOLING, "permissive"),
    "propcache": (RUNTIME, "permissive"),
    "pygments": (TEST_TOOLING, "permissive"),
    "pytest": (TEST_TOOLING, "permissive"),
    "python-flint": (RUNTIME, "weak copyleft"),
    "scipy": (RUNTIME, "permissive"),
    "typing-extensions": (RUNTIME, "permissive"),
    "yarl": (RUNTIME, "permissive"),
}
# installed by the base image python:3.11-slim, not pinned (MIT; dependencies.md §5); and the engine itself if installed
BASE_IMAGE_TOOLS = {"pip", "setuptools", "wheel"}
OWN = {"lfphys"}

# --- reading the lock -------------------------------------------------------------------------------------------------


def _norm(name: str) -> str:
    """PEP 503 normal form of a distribution name."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _find_lock() -> Path:
    """The lock of the engine's image: the nearest parent of this file holding visualizations/docker/requirements.lock."""
    for parent in HERE.parents:
        if (parent / LOCK_IN_ENGINE).is_file():
            return parent / LOCK_IN_ENGINE
    raise FileNotFoundError(f"no {LOCK_IN_ENGINE} above {HERE}")


PIN = re.compile(r"([A-Za-z0-9][A-Za-z0-9._-]*)\s*(\[[^\]]*\])?\s*==\s*([^\s;\\]+)\s*(;\s*(.*))?$")


def _read_lock(path: Path):
    """{normalized name: (name as written, version, marker or None)} and a list of problems."""
    pins, problems = {}, []
    text = path.read_text(encoding="utf-8").replace("\\\n", " ")
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.split(" #", 1)[0].strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-"):
            if line.split()[0] in ("-r", "--requirement", "-c", "--constraint", "-e", "--editable"):
                problems.append(f"line {n}: {raw.strip()!r}: nested, constraint or editable entries are not audited")
            continue
        line = re.split(r"\s--hash", line)[0].strip()
        m = PIN.match(line)
        if not m:
            problems.append(f"line {n}: {raw.strip()!r} is not pinned as name==version")
            continue
        key = _norm(m.group(1))
        if key in pins:
            problems.append(f"line {n}: {m.group(1)} pinned twice")
        pins[key] = (m.group(1), m.group(3), m.group(5))
    return pins, problems


try:
    LOCK = _find_lock()
    PINS, LOCK_PROBLEMS = _read_lock(LOCK)
    LOCK_ERROR = None
except (OSError, UnicodeDecodeError) as exc:
    LOCK, PINS, LOCK_PROBLEMS, LOCK_ERROR = None, {}, [], repr(exc)

# --- classifying a declared licence -----------------------------------------------------------------------------------

PERMISSIVE_IDS = {"MIT", "MIT-0", "0BSD", "BSD-2-Clause", "BSD-3-Clause", "BSD-3-Clause-Clear",
                  "BSD-3-Clause-Open-MPI", "Apache-2.0", "ISC", "PSF-2.0", "Python-2.0", "Zlib", "CC0-1.0",
                  "Unlicense"}
RUNTIME_EXCEPTIONS = {"GCC-exception-2.0", "GCC-exception-3.1", "Classpath-exception-2.0"}


def _classify_id(lid: str, exception: str | None = None) -> str:
    """Class of one SPDX licence identifier (optionally WITH an exception)."""
    low = lid.lower()
    if "noncommercial" in low or "-nc-" in low or low.endswith("-nc") or low.startswith("polyform-") \
            or low == "busl-1.1":
        cls = NONCOMMERCIAL
    elif low.startswith("licenseref-"):
        cls = PROPRIETARY if "proprietary" in low else UNKNOWN
    elif lid in PERMISSIVE_IDS:
        cls = PERMISSIVE
    elif lid.startswith(("LGPL-", "MPL-2.0")):
        cls = WEAK
    elif lid.startswith(("GPL-", "AGPL-")) or lid == "SSPL-1.0":
        cls = STRONG
    else:
        cls = UNKNOWN
    if exception and cls == STRONG and lid.startswith("GPL-") and exception in RUNTIME_EXCEPTIONS:
        return WEAK  # a GPL runtime library with a linking exception
    return cls


def _classify_spdx(expr: str) -> str:
    """Class of an SPDX licence expression: AND takes the most restrictive part, OR the least."""
    tokens = re.findall(r"\(|\)|[^\s()]+", expr)
    pos = 0

    def peek():
        return tokens[pos].upper() if pos < len(tokens) else None

    def take():
        nonlocal pos
        if pos >= len(tokens):
            raise ValueError(expr)
        pos += 1
        return tokens[pos - 1]

    def atom():
        tok = take()
        if tok == "(":
            cls = any_of()
            if take() != ")":
                raise ValueError(expr)
            return cls
        if tok.upper() in ("AND", "OR", "WITH", ")"):
            raise ValueError(expr)
        if peek() == "WITH":
            take()
            return _classify_id(tok, take())
        return _classify_id(tok)

    def all_of():
        parts = [atom()]
        while peek() == "AND":
            take()
            parts.append(atom())
        return max(parts, key=RANK.__getitem__)

    def any_of():
        parts = [all_of()]
        while peek() == "OR":
            take()
            parts.append(all_of())
        return min(parts, key=RANK.__getitem__)

    try:
        cls = any_of()
    except ValueError:
        return UNKNOWN
    return cls if pos == len(tokens) else UNKNOWN


LICENSE_FIELD_ALIASES = {
    "bsd": PERMISSIVE, "bsd license": PERMISSIVE, "new bsd": PERMISSIVE, "new bsd license": PERMISSIVE,
    "3-clause bsd": PERMISSIVE, "mit license": PERMISSIVE, "apache 2.0": PERMISSIVE, "apache-2": PERMISSIVE,
    "apache license 2.0": PERMISSIVE, "apache license, version 2.0": PERMISSIVE, "apache software license": PERMISSIVE,
    "psf": PERMISSIVE, "psf license": PERMISSIVE, "public domain": PERMISSIVE,
    "nvidia proprietary software": PROPRIETARY, "proprietary": PROPRIETARY,
}


def _classify_license_field(text: str) -> str | None:
    """Class of the free-text License field; None when it holds a whole licence text (then the classifiers decide)."""
    if "\n" in text or len(text) > 200:
        return None
    cls = _classify_spdx(text)
    if cls != UNKNOWN:
        return cls
    return LICENSE_FIELD_ALIASES.get(text.lower().rstrip("."), UNKNOWN)


def _classify_classifier(classifier: str) -> str:
    s = classifier.lower()
    if "proprietary" in s:
        return PROPRIETARY
    if "lesser general public" in s or "library or lesser" in s or "mozilla public license 2.0" in s:
        return WEAK
    if "gnu general public" in s or "affero" in s:
        return STRONG
    if any(k in s for k in ("mit license", "mit no attribution", "bsd license", "apache software license",
                            "python software foundation license", "isc license", "zlib/libpng", "public domain",
                            "0bsd", "the unlicense")):
        return PERMISSIVE
    return UNKNOWN


def declared_licence(dist) -> tuple[str, str]:
    """(what the metadata declares, its class): License-Expression, else License, else the License classifiers."""
    meta = dist.metadata
    expr = (meta.get("License-Expression") or "").strip()
    if expr:
        return f"License-Expression: {expr}", _classify_spdx(expr)
    field = (meta.get("License") or "").strip()
    if field:
        cls = _classify_license_field(field)
        if cls is not None:
            return f"License: {field}", cls
    classifiers = [c for c in (meta.get_all("Classifier") or []) if c.startswith("License ::")]
    if classifiers:
        return ("classifiers: " + "; ".join(classifiers),
                max((_classify_classifier(c) for c in classifiers), key=RANK.__getitem__))
    if field:
        return f"License: a licence text of {len(field)} characters, no classifier", UNKNOWN
    return "no License-Expression, License or classifier", NONE


# --- the tests --------------------------------------------------------------------------------------------------------


def test_classifier_of_declared_licences():
    """The classification rules on the forms met in practice."""
    assert _classify_spdx("BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0") == PERMISSIVE
    assert _classify_spdx("Apache-2.0 OR BSD-2-Clause") == PERMISSIVE
    assert _classify_spdx("MIT AND LGPL-3.0-or-later") == WEAK
    assert _classify_spdx("GPL-3.0-or-later WITH GCC-exception-3.1") == WEAK
    assert _classify_spdx("(MIT OR GPL-2.0-only) AND Apache-2.0") == PERMISSIVE
    assert _classify_spdx("MIT AND GPL-3.0-only") == STRONG
    assert _classify_spdx("AGPL-3.0-or-later") == STRONG
    assert _classify_spdx("LicenseRef-NVIDIA-Proprietary") == PROPRIETARY
    assert _classify_spdx("CC-BY-NC-SA-4.0") == NONCOMMERCIAL
    assert _classify_spdx("PolyForm-Noncommercial-1.0.0") == NONCOMMERCIAL
    assert _classify_spdx("MIT AND") == UNKNOWN
    assert _classify_spdx("LicenseRef-Custom") == UNKNOWN
    assert _classify_license_field("Apache 2.0") == PERMISSIVE
    assert _classify_license_field("NVIDIA Proprietary Software") == PROPRIETARY
    assert _classify_license_field("Copyright (c) ...\nRedistribution and use ...") is None
    assert _classify_classifier("License :: OSI Approved :: GNU General Public License v3 (GPLv3)") == STRONG
    assert _classify_classifier("License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)") == WEAK
    assert _classify_classifier("License :: Other/Proprietary License") == PROPRIETARY


def test_lock_is_found_and_every_entry_is_pinned():
    assert LOCK_ERROR is None, f"requirements.lock not readable: {LOCK_ERROR}"
    assert PINS, f"{LOCK}: no pinned packages"
    assert not LOCK_PROBLEMS, LOCK_PROBLEMS


def test_allow_table_matches_the_lock():
    new = sorted(PINS[k][0] for k in set(PINS) - set(ALLOWED))
    stale = sorted(set(ALLOWED) - set(PINS))
    assert not new, (f"pinned packages without a licence row: {new}. Audit each (installed metadata and the project's "
                     f"own site), add a row to sources/dependencies.md §1 and to ALLOWED in this test.")
    assert not stale, f"rows for packages no longer pinned: {stale}; remove them here and in sources/dependencies.md"


def test_allow_table_uses_only_allowed_categories():
    bad = []
    for name, (role, category) in ALLOWED.items():
        if name != _norm(name):
            bad.append(f"{name}: key not in normal form")
        if role not in ROLE_CATEGORIES:
            bad.append(f"{name}: unknown role {role!r}")
        elif category not in ROLE_CATEGORIES[role]:
            bad.append(f"{name}: category {category!r} is not allowed for role {role!r}")
        if category == "platform runtime" and not PLATFORM_RUNTIME_NAME.fullmatch(name):
            bad.append(f"{name}: the platform-runtime exception is audited only for the NVIDIA CUDA libraries")
    assert not bad, bad


@pytest.mark.parametrize("key", sorted(PINS))
def test_pinned_package_licence(key):
    name, version, marker = PINS[key]
    assert key in ALLOWED, (f"{name}=={version} is pinned but has no licence row: audit it and add it to "
                            f"sources/dependencies.md §1 and to ALLOWED")
    role, category = ALLOWED[key]
    try:
        dist = md.distribution(name)
    except md.PackageNotFoundError:
        pytest.skip(f"{name}=={version} ({role}) is pinned but not installed in this image"
                    f"{' (marker: ' + marker + ')' if marker else ''}, e.g. a CPU-only build without the GPU "
                    f"packages: its licence row is not checked here")
    assert dist.version == version, (f"{name}: installed {dist.version}, pinned {version}: the image is not built from "
                                     f"the current lock; rebuild it")
    declared, cls = declared_licence(dist)
    expected = CATEGORY_CLASS[category]
    assert cls == expected, (f"{name} {version}: the installed metadata declares '{declared}' (class: {cls}); its row "
                             f"says '{category}' (class: {expected}). Re-audit the licence and update "
                             f"sources/dependencies.md §1 and ALLOWED; categories allowed for role '{role}': "
                             f"{sorted(ROLE_CATEGORIES[role])}.")
    if category == "metadata only":
        code = [str(f) for f in (dist.files or []) if ".dist-info/" not in str(f).replace("\\", "/")]
        assert not code, f"{name} {version} is audited as a metapackage but installs files: {code[:10]}"


def _audit_rows():
    rows, problems, in_table = {}, [], False
    for line in AUDIT.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_table = line.startswith("## 1.")
            continue
        if not (in_table and line.startswith("| `")):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 7:
            problems.append(f"row with {len(cells)} cells instead of 7: {line[:80]}")
            continue
        name = cells[0].strip("`")
        if _norm(name) in rows:
            problems.append(f"{name}: two rows")
        rows[_norm(name)] = {"name": name, "pinned": cells[1], "role": cells[2], "category": cells[5],
                             "allowed": cells[6]}
    return rows, problems


def test_audit_file_matches_the_lock_and_the_table():
    """sources/dependencies.md §1 has exactly one row per pinned package, with the pinned version and the decision of
    the allow-table."""
    rows, problems = _audit_rows()
    for key in sorted(set(PINS) | set(rows)):
        if key not in rows:
            problems.append(f"{PINS[key][0]}: pinned, no row in dependencies.md §1")
            continue
        row = rows[key]
        if key not in PINS:
            problems.append(f"{row['name']}: row in dependencies.md §1 but not pinned")
            continue
        if row["pinned"] != PINS[key][1]:
            problems.append(f"{row['name']}: dependencies.md says {row['pinned']}, the lock pins {PINS[key][1]}")
        if key in ALLOWED:
            role, category = ALLOWED[key]
            if (row["role"], row["category"]) != (role, category):
                problems.append(f"{row['name']}: dependencies.md says ({row['role']}, {row['category']}), "
                                f"ALLOWED says ({role}, {category})")
            if not row["allowed"].startswith("yes") or category not in ROLE_CATEGORIES.get(role, ()):
                problems.append(f"{row['name']}: decision '{row['allowed']}' does not match the rule")
    assert not problems, problems


# out of scope: the comparison-only image lfphys-ext (tests/external, plan P13; dependencies.md §10)
def test_image_has_no_unaudited_packages():
    """Everything installed is pinned and audited, or one of the base image's own tools."""
    installed = {_norm(d.metadata["Name"]): d.version for d in md.distributions() if d.metadata["Name"]}
    extra = sorted(f"{k}=={v}" for k, v in installed.items() if k not in PINS and k not in BASE_IMAGE_TOOLS | OWN)
    assert not extra, (f"installed but not pinned in requirements.lock (so not audited): {extra}. Pin and audit them, "
                       f"or remove them from the image.")


# --- what the engine and the server actually load ---------------------------------------------------------------------

PROBE = r'''
import importlib, json, os, pkgutil, sys
engine = sys.argv[1]
for name in ("cupy", "cupyx", "cupy_backends", "cuda"):
    sys.modules[name] = None  # "import cupy" now raises ImportError, as on a CPU-only install
roots = [(pkg, os.path.join(engine, *sub)) for pkg, sub in
         (("lfphys", ("lfphys",)), ("lfviz", ("visualizations", "server")))]
roots = [(pkg, path) for pkg, path in roots if os.path.isdir(os.path.join(path, pkg))]
sys.path[:0] = [path for _, path in roots] + [os.path.join(engine, "visualizations")]
errors = {}
def record(name):
    errors[name] = repr(sys.exc_info()[1])
for pkg, _ in roots:
    try:
        mod = importlib.import_module(pkg)
    except Exception as exc:
        errors[pkg] = repr(exc)
        continue
    for info in pkgutil.walk_packages(mod.__path__, pkg + ".", onerror=record):
        try:
            importlib.import_module(info.name)
        except Exception as exc:
            errors[info.name] = repr(exc)
maps = []
if os.path.exists("/proc/self/maps"):
    with open("/proc/self/maps") as fh:
        maps = sorted({line.split()[-1] for line in fh if ".so" in line})
print("PROBE-JSON " + json.dumps({"roots": [pkg for pkg, _ in roots], "errors": errors, "maps": maps,
                                  "modules": sorted(k for k, v in sys.modules.items() if v is not None)}))
'''

# CPython modules of the base image linked against copyleft libraries (dependencies.md §5): must not be loaded
GPL_LINKED_MODULES = {"readline": "GNU Readline (GPL-3.0-or-later)", "_gdbm": "GNU dbm (GPL-3.0-or-later)",
                      "_dbm": "Berkeley DB (Sleepycat)"}
GPL_LINKED_LIBS = ("libreadline", "libgdbm", "libdb-")


@pytest.fixture(scope="module")
def probe(tmp_path_factory):
    """Import every lfphys and lfviz module in a fresh interpreter with CuPy blocked; report errors and what loaded."""
    assert LOCK is not None, LOCK_ERROR
    engine = LOCK.parents[len(LOCK_IN_ENGINE.parts) - 1]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    out = subprocess.run([sys.executable, "-c", PROBE, str(engine)], capture_output=True, text=True, timeout=600,
                         cwd=tmp_path_factory.mktemp("probe"), env=env)
    lines = [ln for ln in out.stdout.splitlines() if ln.startswith("PROBE-JSON ")]
    assert out.returncode == 0 and lines, f"probe failed ({out.returncode}): {out.stderr[-2000:]}"
    result = json.loads(lines[-1][len("PROBE-JSON "):])
    assert "lfphys" in result["roots"], result["roots"]
    return result


def test_gpu_runtime_is_optional(probe):
    """The NVIDIA libraries are allowed as an optional platform runtime: every module imports without CuPy."""
    assert not probe["errors"], f"with CuPy unavailable these modules fail to import: {probe['errors']}"
    assert not [m for m in probe["modules"] if m.split(".")[0] in ("cupy", "cupyx", "cupy_backends")]


def test_no_gpl_linked_standard_module_is_loaded(probe):
    loaded = {m: why for m, why in GPL_LINKED_MODULES.items() if m in probe["modules"]}
    libs = [p for p in probe["maps"] if any(Path(p).name.startswith(lib) for lib in GPL_LINKED_LIBS)]
    assert not loaded and not libs, f"copyleft-linked modules loaded at import: {loaded} {libs}"


def test_vendored_code_is_permissive_unmodified_and_recorded():
    """Third-party code in engine/ only under visualizations/player/vendor/ (AGENTS.md §3 rule 8: permissive licences
    only): each folder has its licence text (MIT here), every file's sha256 equals the one recorded in
    vendor/README.md (copied unmodified), and the folder is listed in sources/dependencies.md §7."""
    import hashlib
    import re as _re
    engine = HERE.parents[2]
    vendor = engine / "visualizations" / "player" / "vendor"
    readme = (vendor / "README.md").read_text(encoding="utf-8")
    audit = AUDIT.read_text(encoding="utf-8")
    recorded = dict(_re.findall(r"^\| ([\w.\-]+) \| ([0-9a-f]{64}) \|$", readme, flags=_re.M))
    folders = [p for p in vendor.iterdir() if p.is_dir()]
    assert folders
    for d in folders:
        lic = (d / "LICENSE").read_text(encoding="utf-8")
        assert lic.startswith("The MIT License"), d.name
        assert f"## {d.name}" in readme and d.name in audit, d.name
        for f in d.iterdir():
            assert recorded.get(f.name) == hashlib.sha256(f.read_bytes()).hexdigest(), f"{d.name}/{f.name}"

