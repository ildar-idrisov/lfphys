# Reviewer's follow-up of lbm_dye_check.py: the dye refined (dx/2, dt/4) at rest, for two widths and two remap times,
# with the coarse run's own error at the remap time and the error history after it. Run in Docker from engine/.
import sys
sys.path[:0] = ["/out", "/lf/lfphys"]
import lbm_dye_check as M  # noqa: E402
from lfphys.core import backend  # noqa: E402
from lfphys.core.fluids import lbm  # noqa: E402

backend.configure(None)
variants = {"engine": lbm, "kgm = 1": M.variant("one", "1.0"), "kgm = kgp": M.variant("kgp", "kgp")}
for S0 in (2.5, 5.0):
    M.S0 = S0
    for t_r in (100, 600):
        co = M.flow(lbm, 1.0, 1.0)
        co.advance(t_r + 1)
        e_co_r = M.err(co)
        co.advance(400)
        tgt = M.flow(lbm, 0.5, 0.25)
        tgt.advance(4 * (t_r + 1) + 1600)
        line = [f"coarse at remap {e_co_r:.3e}, coarse at end {M.err(co):.3e}, fine alone at end {M.err(tgt):.3e}"]
        for name, Lm in variants.items():
            fl = M.flow(Lm, 1.0, 1.0)
            fl.advance(t_r)
            fl.remap(dx=0.5, dt=0.25)
            hist = [M.err(fl)]
            for k in range(4):
                fl.advance(400)
                hist.append(M.err(fl))
            line.append(f"[{name}] t = remap, +100, +200, +300, +400: " + ", ".join(f"{h:.2e}" for h in hist))
        print(f"S0 {S0} remap at t = {t_r + 1}: " + "; ".join(line), flush=True)
