# Review B6-framework, script s05: a viewer's history (Run.send_history) while the window is trimmed.
# send_history awaits every ws.send_bytes; meanwhile the worker's next segment marker runs _new_segment -> _trim on the
# same event loop. The real Viewer.pump and Run are used with a fake websocket; the trim is triggered from inside
# send_bytes, as an ingested record_segment would do between two sends.
#   1: protected segments first (recording was on), unprotected ones after them: the trim deletes a segment the history
#      has not opened yet -> FileNotFoundError, which Viewer.pump does not catch: the history stops without
#      history_end and the pump is dead (no live messages either), the websocket stays open.
#   2: segment 0 being sent when the trim drops it: segment 0 is emptied in place (write_bytes), so the open handle
#      reads b"" and empty messages are sent.
# Usage: see s01; python3 /out/s05_history_trim_race.py
import asyncio
import tempfile
from pathlib import Path

from lfviz import protocol, runs


class Mgr:
    pass


def make_run(protect):
    d = Path(tempfile.mkdtemp())
    meta = {"id": "x", "viz": "p99_toy", "restorable": True, "kind": "playground", "state": "running",
            "buffer": {**runs.BUFFER_DEFAULT, "recording": False, "protected": [],
                       "segs": [{"k": 0, "wall0": 0.0, "t0": 0.0, "world": 1}]}}
    run = runs.Run(Mgr(), "x", "p99_toy", meta, d)
    run.file = open(run.stream_path, "wb")
    run.file.write(protocol.MAGIC)
    run.file.flush()
    ing = lambda m: run._ingest(protocol.encode(m))  # noqa: E731
    ing({"type": "header", "t": 0.0, "world": 1})
    t = 0.0
    for k in range(6):
        if k:
            if k == 1 and protect:
                run.set_recording(True)
            if k == 3 and protect:
                run.set_recording(False)
            ing({"type": "record_segment", "t": t, "world": 1})
            ing({"type": "checkpoint", "t": t, "world": 1, "file": "w1-1.pkl"})
        for _ in range(50):
            t += 0.05
            ing({"type": "event", "t": t, "kind": "x", "text": "x" * 100})
    return run


class FakeWS:
    def __init__(self, run, at, mark_old):
        self.run, self.n, self.at, self.mark_old, self.types = run, 0, at, mark_old, []

    async def send_bytes(self, b):
        self.n += 1
        try:
            self.types.append(protocol.peek_meta(b).get("type"))
        except Exception:  # noqa: BLE001 - what the player would get: a message it cannot decode
            self.types.append(f"<corrupt: {len(b)} bytes>")
        if self.n == self.at:  # the worker's next segment arrives while the history is being sent
            for sg in self.run.meta["buffer"]["segs"]:
                if sg["k"] in self.mark_old:
                    sg["wall0"] -= 10_000
            for sg in self.run.meta["buffer"]["segs"][1:]:
                if sg["k"] - 1 in self.mark_old:
                    sg["wall0"] -= 10_000  # the dropped segment's end (the next one's start) is old too
            self.run._ingest(protocol.encode({"type": "record_segment", "t": 99.0, "world": 1}))
        await asyncio.sleep(0)


async def case(title, protect, at, mark_old):
    print("===", title, "===")
    run = make_run(protect)
    print("segments:", [sg["k"] for sg in run.meta["buffer"]["segs"]], "protected:", run.meta["buffer"]["protected"])
    ws = FakeWS(run, at, mark_old)
    v = runs.Viewer(ws, run, len(run.entries))
    task = asyncio.create_task(v.pump())
    await asyncio.sleep(0.5)
    print("segments after the trim:", [sg["k"] for sg in run.meta["buffer"]["segs"]])
    print("pump finished:", task.done(), " viewer alive:", v.alive,
          " exception:", repr(task.exception()) if task.done() else None)
    print("messages sent:", ws.n, " history_end sent:", "history_end" in ws.types,
          " corrupt or empty messages sent:", sum(1 for x in ws.types if str(x).startswith("<")),
          [x for x in ws.types if str(x).startswith("<")][:3])
    if not task.done():
        v.alive = False
        v.q.put_nowait((None, False))
        await task


async def main():
    await case("1: a not yet opened unprotected segment is deleted during the history", True, 60, {3, 4})
    await case("2: segment 0 is emptied while it is being sent", False, 10, {0})


asyncio.run(main())
