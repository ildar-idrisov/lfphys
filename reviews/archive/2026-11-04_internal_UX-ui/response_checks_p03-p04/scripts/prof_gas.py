import sys, cProfile, pstats
sys.path[:0] = ["/lf/visualizations/tests", "/lf/visualizations/server", "/lf/visualizations", "/lf/lfphys"]
from harness import Harness
h = Harness("p03_molecules", None, {"dim": "3d"})
cProfile.run('h.cmd("scene", op="add", type="gas", values={"n": 12000})', "/tmp/g.out")
pstats.Stats("/tmp/g.out").sort_stats("cumtime").print_stats(18)
