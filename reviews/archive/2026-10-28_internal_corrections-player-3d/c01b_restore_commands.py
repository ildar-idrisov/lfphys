"""C1 review, check 01b: two restore cases at the worlds' own time scales (c01 part C/D redone).

[C] a `step` and a `set` handled in one batch (a paused world; the run loop handles every queued command before it
    draws the next frame): the `set` is recorded at the time after the step, but no frame lies between them; the
    restore applies the commands at the time it has reached, ignoring their recorded time.
[D] a world n >= 2 restored: the slice planes the previous world handed over at `new_world` (adopt_view) — v08.

Run: docker run --rm --name lf-c1rev-c01b -v <engine>:/lf:ro -v <this folder>:/rev -w /lf/visualizations \
         light-funnel-viz python3 /rev/c01b_restore_commands.py
Output: /rev/out/c01b_restore_commands.txt
"""
import queue
import sys
import traceback

sys.path[:0] = ["/rev"]
from c01_restore_all_messages import Rec, build, compare, drive, SMALL  # noqa: E402

sys.path[:0] = ["/lf/visualizations/server", "/lf/visualizations", "/lf/lfphys"]
from lfviz import registry  # noqa: E402
from lfviz.sim import Runner  # noqa: E402


def script_after(rec, idx):
    out = []
    for m, _ in rec.msgs[idx + 1:]:
        if m.get("type") == "frame":
            out.append({"frame": m["t"]})
        elif m.get("type") == "command":
            out.append({"t": m["t"], "cmd": m["cmd"], "args": m["args"]})
    return out


def case_c(out):
    out.append("[C] v11 (small): a `step` and a `set` (slit B closed) handled in one batch, then frames; restored from "
               "the record's script")
    run, rec = build("v11_double_slit_2d")
    run._start_world()
    sp = run.sim.default_speed  # world seconds per wall second: the experiment lasts ~40 of them
    drive(run, [2 * sp, 4 * sp])
    run.handle({"cmd": "step", "args": {"dt": 3 * sp}})
    run.handle({"cmd": "set", "args": {"values": {"slit_b": False}}})
    run._frame(0.0)
    script = list(rec.script)
    t_end = run.sim.t
    cmd = [c for c in script if "cmd" in c][-1]
    frames = [c["frame"] for c in script if "frame" in c]
    out.append(f"  recorded: set at t = {cmd['t']:.6g} s; frames {[f'{f:.4g}' for f in frames]}")
    k = len(rec.msgs)
    cont = [t_end + i * sp for i in (1, 2, 3, 4)]
    drive(run, cont)
    orig_after = rec.msgs[k:]
    run2, rec2 = build("v11_double_slit_2d")
    applied = {}
    orig_handle = run2.handle

    def spy(msg):
        if msg.get("cmd") == "set":
            applied["t"] = run2.sim.t
        return orig_handle(msg)
    run2.handle = spy
    run2.restore(1, script, t_end, lambda on: setattr(rec2, "muted", bool(on)))
    rec2.muted = False
    out.append(f"  restored: set applied at t = {applied.get('t', float('nan')):.6g} s (recorded {cmd['t']:.6g} s)")
    drive(run2, cont)
    compare(orig_after, rec2.msgs, "  v11 continuation after step+set", out)


def case_d(out):
    out.append("\n[D] v08: planes 1 (tilted) and 2 placed in world 1, `new_world` (the planes carry over), frames; the "
               "latest world restored as the server does (from its header's params and seed, script after its header)")
    run, rec = build("v08_wave_3d")
    run._start_world()
    sp = run.sim.default_speed
    drive(run, [sp, 2 * sp])
    run.handle({"cmd": "view", "args": {"op": "plane", "id": 1, "origin": [0, 0, 5], "normal": [0.5, 0.0, 0.866]}})
    run.handle({"cmd": "view", "args": {"op": "plane", "id": 2, "origin": [0, 0, 5], "normal": [0.0, 1.0, 0.0]}})
    drive(run, [3 * sp])
    run.handle({"cmd": "new_world", "args": {"params": {**SMALL["v08_wave_3d"]}}})
    hidx = max(i for i, (m, _) in enumerate(rec.msgs) if m.get("type") == "header")
    header2 = rec.msgs[hidx][0]
    drive(run, [sp, 2 * sp])
    script = script_after(rec, hidx)
    live = {pid: [round(c, 3) for c in p["normal"]] for pid, p in run.sim.planes.items()}
    viz = registry.load("v08_wave_3d")
    rec2 = Rec()
    sim2 = viz["simulation"](header2["params"], header2["seed"], rec2.emit)
    run2 = Runner(sim2, rec2.emit, queue.Queue())
    run2.restore(2, script, run.sim.t, lambda on: setattr(rec2, "muted", bool(on)))
    rest = {pid: [round(c, 3) for c in p["normal"]] for pid, p in run2.sim.planes.items()}
    out.append(f"  world 2 as it ran: planes {live}")
    out.append(f"  world 2 restored: planes {rest}")
    out.append("  -> " + ("same" if live == rest else "DIFFERENT: the restored world lost the planes handed over by "
                                                       "world 1"))
    rec.msgs.clear()
    rec2.muted = False
    run.handle({"cmd": "view", "args": {"op": "plane", "id": 2}})  # e.g. the owner nudges plane 2 after the resume
    run2.handle({"cmd": "view", "args": {"op": "plane", "id": 2}})
    out.append(f"  after the same `view plane 2` on both: live answered {[m.get('type') for m, _ in rec.msgs]}, "
               f"restored answered {[m.get('type') for m, _ in rec2.msgs]}")
    errs = [m.get("text") for m, _ in rec2.msgs if m.get("type") == "error"]
    if errs:
        out.append(f"  restored world's errors: {errs}")


def main():
    out = ["C1 check 01b — restore: command times and new worlds"]
    for f in (case_c, case_d):
        try:
            f(out)
        except Exception as e:  # noqa: BLE001
            out.append(f"  ERROR {e!r}\n{traceback.format_exc(limit=4)}")
        print("\n".join(out), flush=True)
    with open("/rev/out/c01b_restore_commands.txt", "w") as fh:
        fh.write("\n".join(out) + "\n")


main()
