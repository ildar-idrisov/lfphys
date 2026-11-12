"""P13: what the step's stop criterion waits for (E 0.8 eV below the step V0 = 1 eV)."""
import sys, time, math, json
root = sys.argv[1]
sys.path[:0] = [f"{root}/visualizations", f"{root}/visualizations/server", f"{root}/lfphys", root]
from lfviz import registry
registry.ensure_path()
import numpy as np
viz = registry.load("v03_quantum_1d")
M = sys.modules[viz["simulation"].__module__]
log = []
class Sim(viz["simulation"]):
    def _fates(self, psi):
        cl, cr = super()._fates(psi)
        g = self.grid
        rho = np.abs(psi) ** 2
        x = g.x
        n = g.norm(psi)
        reg = {"x<-30": float(np.sum(rho[x < -30]) * g.dx), "-30..-5": float(np.sum(rho[(x >= -30) & (x < -5)]) * g.dx),
               "-5..5": float(np.sum(rho[(x >= -5) & (x < 5)]) * g.dx), "5..30": float(np.sum(rho[(x >= 5) & (x < 30)]) * g.dx),
               "x>30": float(np.sum(rho[x >= 30]) * g.dx)}
        log.append({"t": round(self._t_now, 1) if hasattr(self, "_t_now") else None, "norm": n, "cl": cl, "cr": cr, "unc": n - cl - cr, **reg})
        return cl, cr
vals = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {"scenario": "step"}
p, e = viz["schema"].resolve(None, vals)
t0 = time.time()
s = Sim(p, 1, lambda m, b=None: None)
print(json.dumps({"vals": vals, "n": s.n_grid, "L": s.L, "t_end_est": s.t_end_est, "dt": s._dt_max(), "capped": s.capped,
                  "T": s.PR[-1] / (s.PL[-1] + s.PR[-1]), "ref": s._expected_T()[0], "leftover": s.leftover,
                  "allowed": s.leftover_allowed, "assigned": s.assigned, "s": round(time.time() - t0, 1),
                  "t_last": float(s.t_snap[-1])}))
for r in log[:: max(1, len(log) // 25)] + log[-2:]:
    print(json.dumps(r))
