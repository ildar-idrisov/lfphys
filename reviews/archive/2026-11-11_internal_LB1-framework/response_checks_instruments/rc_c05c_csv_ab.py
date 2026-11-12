"""rc_c05c (response to F11): A/B on one record. The server app (lfviz.app) runs in a CHILD process on a copy of the
record of rc_c05b (p97, 40 oscillators, 82 measurables); the parent asks /api/health every 20 ms from its own thread
(as the reviewer's c05 did from another process: a poller inside the server's own loop could not see a blocked loop)
while it downloads the CSV of all 82 ids, five times each way:
  A — as now: each batch read and formatted in a thread (instruments.csv_batch through asyncio.to_thread);
  B — the old way emulated: the batch formatted in the event loop (csv_batch called in the loop).
Run: docker run --rm -v <engine>:/lf:ro -v <runs of lf-lpi-srv>:/runs_src:ro -v <this folder>:/out light-funnel-viz \
     python3 /out/rc_c05c_csv_ab.py <run id>"""
import json
import multiprocessing as mp
import shutil
import sys
import threading
import time
import urllib.request

sys.path[:0] = ["/lf/visualizations/server", "/lf/visualizations", "/lf/lfphys"]


def serve(mode, port):
    import asyncio
    from pathlib import Path

    from aiohttp import web

    from lfviz import instruments as I
    from lfviz.app import create_app
    if mode == "B":
        real = asyncio.to_thread

        async def to_thread(f, *a, **k):
            if f is I.csv_batch:
                return f(*a, **k)
            return await real(f, *a, **k)
        I.asyncio = type("A", (), {"to_thread": staticmethod(to_thread), "Lock": asyncio.Lock})
    web.run_app(create_app(Path("/tmp/runs"), max_workers=1), host="127.0.0.1", port=port, print=None)


def main():
    rid = sys.argv[1]
    shutil.copytree(f"/runs_src/{rid}", f"/tmp/runs/{rid}")
    out = {}
    for k, mode in enumerate(("A", "B", "A", "B")):
        port = 18700 + k
        p = mp.Process(target=serve, args=(mode, port), daemon=True)
        p.start()
        base = f"http://127.0.0.1:{port}"
        for _ in range(200):
            try:
                urllib.request.urlopen(base + "/api/health").read()
                break
            except OSError:
                time.sleep(0.1)
        try:
            urllib.request.urlopen(base + f"/api/runs/{rid}/series?ids=__none__")
        except urllib.error.HTTPError as e:
            ids = json.loads(e.read())["error"].split("есть: ")[1].rstrip(")").split(", ")
        lat, stop = [], [False]

        def poll():
            while not stop[0]:
                a = time.monotonic()
                urllib.request.urlopen(base + "/api/health").read()
                lat.append(time.monotonic() - a)
                time.sleep(0.02)
        th = threading.Thread(target=poll)
        th.start()
        sizes, secs = [], []
        for _ in range(5):
            a = time.monotonic()
            sizes.append(len(urllib.request.urlopen(base + f"/api/runs/{rid}/series?ids={','.join(ids)}&format=csv").read()))
            secs.append(time.monotonic() - a)
            time.sleep(0.2)
        stop[0] = True
        th.join()
        p.terminate()
        p.join()
        lat.sort()
        out.setdefault({"A": "A_thread", "B": "B_in_loop"}[mode], []).append(
            {"csv_bytes": sizes[-1], "csv_s_mean": round(sum(secs) / len(secs), 3), "health_max_s": round(lat[-1], 4),
             "health_p95_s": round(lat[int(0.95 * (len(lat) - 1))], 4), "polls": len(lat), "ids": len(ids)})
    print(json.dumps({"run": rid, **out}, indent=1))
    json.dump({"run": rid, **out}, open("/out/rc_c05c_csv_ab.json", "w"), indent=1)


if __name__ == "__main__":
    main()
