# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
# lfphys-ext: the engine's runtime image plus the third-party libraries used ONLY by the comparison suite
# lfphys/tests/external (plan item P13; engine/AGENTS.md section 3, rule 8). The rule admits libraries under any licence
# here (at the pinned versions they are MIT or BSD-3-Clause, with weak-copyleft parts: sources/dependencies.md, section
# "Comparison-only libraries"); this image is for local testing only and is NEVER distributed or pushed. The engine
# never imports them.
# Build and run from engine/, the repository root (lfphys/tests/external/README.md):
#   docker build -f lfphys/tests/external/docker/Dockerfile -t lfphys-ext:latest .
#   docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf/lfphys -e LFPHYS_EXTERNAL=1 \
#       lfphys-ext:latest python3 -m pytest -q -p no:cacheprovider tests/external
FROM lfphys-viz:latest

# LFPHYS_EXTERNAL=1 makes lfphys/tests/conftest.py collect tests/external; matplotlib (pulled in by kerrgeopy) and
# astropy get writable configuration and cache folders for any --user
ENV LFPHYS_EXTERNAL=1 \
    MPLBACKEND=Agg \
    MPLCONFIGDIR=/tmp/lf-ext-mpl \
    XDG_CONFIG_HOME=/tmp/lf-ext-config \
    XDG_CACHE_HOME=/tmp/lf-ext-cache

COPY lfphys/tests/external/docker/requirements-external.lock /tmp/requirements-external.lock
# --no-deps: exactly the pinned set, nothing of the runtime image is upgraded; pip check: the set is complete
RUN pip install --no-deps -r /tmp/requirements-external.lock && pip check \
    && mkdir -p /tmp/lf-ext-mpl /tmp/lf-ext-config/astropy /tmp/lf-ext-cache/astropy \
    && chmod -R 1777 /tmp/lf-ext-mpl /tmp/lf-ext-config /tmp/lf-ext-cache

WORKDIR /lf/lfphys
CMD ["python3", "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/external"]
