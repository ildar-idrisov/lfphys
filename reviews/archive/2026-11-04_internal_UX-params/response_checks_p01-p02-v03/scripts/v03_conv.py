"""P19: why does a 10 nm barrier with delta = 0.02 nm transmit 55x too much? Convergence in dt and dx of v03's own
evolution (the world's code with its step and grid scaled), against the stationary reference."""
import sys, time, math, json
root = sys.argv[1]
sys.path[:0] = [f"{root}/visualizations", f"{root}/visualizations/server", f"{root}/lfphys", root]
from lfviz import registry
registry.ensure_path()
import numpy as np
viz = registry.load("v03_quantum_1d")
M = sys.modules[viz["simulation"].__module__]
M.COST_MAX = 1e14
from lfphys.core.quantum import schrodinger1d as S1
ft, fx = float(sys.argv[2]), float(sys.argv[3])
vals = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {"width": 10.0, "edge": 0.02}

class Sim(viz["simulation"]):
    def _dt_max(self):
        return super()._dt_max() * ft
    def _evolve(self):
        if fx != 1.0:
            n = int(round(self.n_grid * fx))
            self.n_grid = n
            x = np.linspace(-self.L, self.L, n, endpoint=False)
            self.grid = S1.Grid(x, self.m, M.HBAR)
            self.V = self.Vf(x)
            W = np.zeros_like(x)
            for side in (-1, 1):
                d = np.clip((side * x - (self.L - self.det)) / self.det, 0, 1)
                W += self.W0 * d ** 2
            self.W = W
        return super()._evolve()

p, e = viz["schema"].resolve(None, vals)
msgs = []
t0 = time.time()
s = Sim(p, 1, lambda m, b=None: msgs.append(m))
T = s.PR[-1] / (s.PL[-1] + s.PR[-1])
ref = s._expected_T()[0]
print(json.dumps({"vals": vals, "ft": ft, "fx": fx, "n": s.n_grid, "dx": s.grid.dx, "dt": s._dt_max(), "T": T, "ref": ref,
                  "ratio": T / ref, "leftover": s.leftover, "capped": s.capped, "s": round(time.time() - t0, 1)}), flush=True)
