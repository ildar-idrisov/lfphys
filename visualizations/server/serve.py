# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Start the lfphys visualization server (one server for all visualizations).

    python serve.py --host 0.0.0.0 --port 8479

Normally started by Docker: ``docker compose -f visualizations/docker/docker-compose.yml up -d`` (README.md).
"""

from __future__ import annotations

import argparse
import logging
import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aiohttp import web  # noqa: E402

from lfviz import registry  # noqa: E402
from lfviz.app import MGR, create_app  # noqa: E402
from lfviz.limits import fmt_bytes  # noqa: E402


def lan_addresses() -> list[str]:
    out = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127.") and ip not in out:
                out.append(ip)
    except OSError:
        pass
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="lfphys visualization server (HTTP + WebSocket, LAN).")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8479)
    ap.add_argument("--runs-dir", default=str(registry.ROOT / "runs"), help="where run records are written")
    ap.add_argument("--max-workers", type=int, default=3, help="concurrent runs (worker processes)")
    ap.add_argument("--keep-days", type=float, default=3.0,
                    help="runs whose last action (a viewer, a command) is older than this are removed unless kept")
    ap.add_argument("--quota-gb", type=float, default=5.0, help="size limit of the runs folder")
    ap.add_argument("--idle-pause", type=float, default=60.0, help="pause a run after this many s without viewers")
    ap.add_argument("--idle-suspend", type=float, default=1800.0,
                    help="release a run's worker after this many s without viewers (it resumes when asked to compute)")
    ap.add_argument("--worker-mem-gb", type=float, default=0.0,
                    help="memory budget and hard limit of every worker, GB (0: a share of the container's or the "
                         "host's memory, lfviz.limits.default_budget)")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    app = create_app(Path(a.runs_dir), max_workers=a.max_workers, keep_days=a.keep_days, quota_gb=a.quota_gb,
                     idle_pause=a.idle_pause, idle_suspend=a.idle_suspend, worker_mem_gb=a.worker_mem_gb or None)
    print(f"lfphys viz server: http://127.0.0.1:{a.port}/", flush=True)
    print(f"  memory per worker (hard limit): {fmt_bytes(app[MGR].worker_mem)}", flush=True)
    for ip in lan_addresses():
        print(f"  LAN: http://{ip}:{a.port}/", flush=True)
    web.run_app(app, host=a.host, port=a.port, print=None, access_log=None)


if __name__ == "__main__":
    main()
