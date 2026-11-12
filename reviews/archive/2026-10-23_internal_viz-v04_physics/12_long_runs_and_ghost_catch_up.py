"""12: wall time of long runs and of switching the ghost on late (the ghost is recomputed from the segment's start up
to now inside the 'set' command, i.e. inside one step of the worker; the real-time runner cannot interrupt it).

Each measurement in a child process with a time box.
"""
import multiprocessing as mpr
import time

BOX = 240.0


def job(preset, n_orbits, ghost_late, q):
    from harness import Harness
    h = Harness("v04_orbits", preset, {"ghost": False})
    P = h.sim._period_estimate(h.sim.track) * h.sim.T_s
    t0 = time.time()
    h.run_to(n_orbits * P)
    t_run = time.time() - t0
    t_ghost = None
    if ghost_late:
        t0 = time.time()
        h.set(ghost=True)
        t_ghost = time.time() - t0
    q.put((t_run, t_ghost, len(h.errors()), len(h.msgs)))


if __name__ == "__main__":
    for preset, n in (("mercury", 415), ("mercury", 2000), ("default", 1000), ("newton_ellipse", 1000),
                      ("newton_ellipse", 3000)):
        q = mpr.Queue()
        p = mpr.Process(target=job, args=(preset, n, True, q))
        t0 = time.time()
        p.start()
        p.join(BOX)
        if p.is_alive():
            p.kill()
            p.join()
            print(f"{preset:15s} {n:5d} orbits: TIMEOUT > {BOX:.0f} s")
            continue
        t_run, t_ghost, n_err, n_msg = q.get()
        print(f"{preset:15s} {n:5d} orbits: run {t_run:7.2f} s, then ghost on (catch-up from the segment start) "
              f"{t_ghost:7.2f} s; errors {n_err}, messages {n_msg}", flush=True)
