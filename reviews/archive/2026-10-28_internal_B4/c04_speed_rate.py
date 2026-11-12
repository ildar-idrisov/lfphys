# [root path fixed after archiving, 2026-10-28, by the responder: reviews/ -> reviews/archive/]
# Review B4, check c04: the measured world speed of lfviz.sim.Runner (the owner's note 1 of 2026-10-28). The frame
# field was `rate` as delivered and renamed to `speed_actual` mid-review (it overwrote v04's own `rate` = dτ/dt); this
# script reads `speed_actual` and also prints v04's own `rate` to show it is no longer overwritten.
# (1) v04's black-hole world (preset "default") played at its default speed and at 10x ... 1e4x it: the frames'
#     `rate` and `lag` against the world speed measured here from the frames' t and the wall clock of their arrival;
# (2) edge cases with a synthetic world: the first value after play / a speed change (the window's start), a world
#     whose single step is slower than the frame budget (`lag` stays false), pause.
#
# Root (fix after archiving): engine mounted at /lf (host /home/ildar/hdd/projects/i/light-funnel/engine); this
# script in /lf/reviews/archive/2026-10-28_internal_B4/. CPU only, about 1 min.
# Run:
#   docker run --rm --user "$(id -u):$(id -g)" -v <engine>:/lf:ro \
#     -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server:/lf/lfphys light-funnel-viz \
#     python3 /lf/reviews/archive/2026-10-28_internal_B4/c04_speed_rate.py > out/c04_speed_rate.txt
import queue
import threading
import time

from lfviz import registry
from lfviz.sim import Runner, Simulation


def play(sim, speed, seconds, label, cmds=()):
    frames = []

    def emit(m, b=None):
        if m.get("type") == "frame":
            frames.append((time.monotonic(), m["t"], m.get("speed_actual"), m.get("lag"), m.get("rate")))
    sim.emit = emit
    if hasattr(sim, "_buf") and sim._buf is not None and not isinstance(sim._buf, list):
        pass
    q = queue.Queue()
    r = Runner(sim, emit, q)
    r.emit = emit
    th = threading.Thread(target=r.run, daemon=True)
    th.start()
    q.put({"cmd": "speed", "args": {"value": speed}})
    q.put({"cmd": "play"})
    t_start = time.monotonic()
    for at, c in cmds:
        while time.monotonic() - t_start < at:
            time.sleep(0.01)
        q.put(c)
    while time.monotonic() - t_start < seconds:
        time.sleep(0.05)
    r.stopped = True
    th.join(5)
    return r, frames


def summary(frames, label, speed, last=1.5):
    if not frames:
        print(label, "no frames")
        return
    w_end = frames[-1][0]
    win = [f for f in frames if f[0] >= w_end - last]
    meas = (win[-1][1] - win[0][1]) / max(win[-1][0] - win[0][0], 1e-9)
    rates = [f[2] for f in win if f[2] is not None]
    lags = sum(1 for f in win if f[3])
    print(f"{label}: chosen {speed:.3g} s/s | measured here over the last {last} s: {meas:.3g} s/s "
          f"({meas / speed:.3%} of chosen) | frames' rate (last): {rates[-1] if rates else None!r:.12} | "
          f"lag in {lags}/{len(win)} frames | the player shows «факт» if rate < 0.97 chosen: "
          f"{bool(rates and rates[-1] < 0.97 * speed)} | the world's own frame field 'rate' (v04: dτ/dt): {win[-1][4]!r}")


print("== (1) v04 black hole (preset default) ==")
viz = registry.load("v04_orbits")
p, err = viz["schema"].resolve("default", {})
base = viz["simulation"](p, 1, lambda m, b=None: None)
d = base.default_speed
print(f"default speed {d:.4g} s/s, range {base.speed_range}")
for mult in (1, 10, 100, 1e3, 1e4):
    sim = viz["simulation"](p, 1, lambda m, b=None: None)
    r, fr = play(sim, d * mult, 4.0, f"x{mult:g}")
    summary(fr, f"v04 default x{mult:g}", d * mult)

print("\n== (2) synthetic worlds ==")


class Synthetic(Simulation):
    cost = 0.0     # wall seconds per world second
    step = None    # max_step

    def header(self):
        return {"title": "t"}, {}

    def advance(self, t_target):
        time.sleep(self.cost * (t_target - self.t))
        self.t = t_target

    def frame(self):
        return {}, {}

    def max_step(self):
        return self.step


s = Synthetic({}, 1, lambda m, b=None: None)
r, fr = play(s, 1.0, 3.0, "free")
first = next((f for f in fr if f[2] is not None), None)
t0 = fr[0][0]
print(f"cheap world at 1 s/s: first non-null rate {first[2]:.4f} at {first[0] - t0:.2f} s after play; "
      f"last {fr[-1][2]:.4f}")
summary(fr, "cheap world", 1.0)

s = Synthetic({}, 1, lambda m, b=None: None)
s.cost, s.step = 1.0, None  # one advance call covers the whole frame interval and takes as long as the world time
r, fr = play(s, 1.0, 4.0, "one slow step")
summary(fr, "one slow step per frame (max_step None, cost 1 wall s per world s) at 1 s/s", 1.0)
s = Synthetic({}, 1, lambda m, b=None: None)
s.cost, s.step = 2.0, None
r, fr = play(s, 1.0, 4.0, "one slower step")
summary(fr, "one slow step per frame (max_step None, cost 2 wall s per world s) at 1 s/s", 1.0)

s = Synthetic({}, 1, lambda m, b=None: None)
r, fr = play(s, 1.0, 4.0, "pause", cmds=[(2.0, {"cmd": "pause"})])
print(f"pause at 2 s: frames after pause carry rate {[f[2] for f in fr if f[0] - fr[0][0] > 2.2][:3]} "
      f"(frames are emitted only while playing or dirty)")
