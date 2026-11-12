"""v07: which natural settings make the run's advance raise (negative joint probability from round-off ->
numpy Generator.choice: "Probabilities are not non-negative"). Fixed settings (preset scan: a = b = 0, "move b") and
random settings of the CHSH presets with one angle moved to a 'round' value. Also the cost of many pairs in flight
(spin, v/c = 1e-4).
Output: out/09b_v07_zero_cells_in_the_run.txt
"""
import sys
import time

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402

OUT = open("out/09b_v07_zero_cells_in_the_run.txt", "w")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.write(s + "\n")
    OUT.flush()


def try_run(preset, params, label, set_after=None):
    h = Harness("v07_bell_test", preset, params)
    try:
        if set_after:
            h.run_to(2 * h.sim._flight())
            h.set(**set_after)
        h.run_to(h.sim.t + 3 * h.sim._flight())
        return "ok"
    except Exception as e:  # noqa: BLE001
        return f"RAISES {type(e).__name__}: {e}"


say("A. preset 'scan' (photons, fixed a = b = 0): move b live (as the preset label suggests)")
for b in (0.0, 22.5, 30.0, 45.0, 60.0, 90.0, 135.0, 180.0, -90.0, 270.0, 360.0, 10.0, 15.0, 75.0, 120.0, 150.0):
    say(f"  b = {b:g}: {try_run('scan', {}, '', {'b_deg': b})}")
say("B. spins, fixed settings: a = 0, move b")
for b in (0.0, 30.0, 45.0, 60.0, 90.0, 120.0, 180.0, 270.0, 360.0):
    say(f"  b = {b:g}: {try_run('spin_chsh', {'switch': 'fixed', 'a_deg': 0.0}, '', {'b_deg': b})}")
say("C. photon_chsh (random): b' set equal to a' or to a + 90")
for upd in ({"b2_deg": 45.0}, {"b2_deg": 135.0}, {"b_deg": 0.0}, {"a2_deg": 22.5}, {"a2_deg": 112.5}):
    say(f"  {upd}: {try_run('photon_chsh', {}, '', upd)}")
say("D. many pairs in flight: spin, v/c = 1e-4, L = 1000 m, rate = 1e8 /s")
h = Harness("v07_bell_test", None, {"pair": "spin", "spin_beta": 1e-4, "L_m": 1000.0, "rate": 1e8})
fl = h.sim._flight()
for frac in (0.02, 0.04, 0.08):
    t0 = time.time()
    h.run_to(frac * fl)
    say(f"  advanced to {frac:.2f} of the flight ({frac * fl:.3g} s of world time): in flight {h.sim.exp.n_flight}, "
        f"cumulative wall {time.time() - t0:.1f} s for this slice")
