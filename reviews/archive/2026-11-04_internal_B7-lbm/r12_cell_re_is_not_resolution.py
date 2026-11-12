"""R12: the module's validity says the flows are "resolved by the grid (cell Reynolds number u dx / nu <= 25, with an
inlet or outlet <= 10 - measured)". The limits were measured as stability edges. Here the driven cavity at Re = 1000 on
64^2 (cell Re 15.6, accepted) and 128^2 (7.8) against Ghia, Ghia & Shin's Re = 1000 columns (the transcription the
engine's note cites for Re = 100: gist ivan-pi/3e9326d1..., /caa6c673...).

Run (from engine/): docker run --rm --name lf-b7rl-r12 -v $PWD:/lf:ro -v <this folder>:/out -e PYTHONDONTWRITEBYTECODE=1
-e LFPHYS_NO_GPU=1 -e PYTHONPATH=/lf/lfphys:/lf/lfphys/tests -w /lf/lfphys light-funnel-viz python3 /out/r12_cell_re_is_not_resolution.py
"""
import numpy as np

from lfphys.core.fluids import lbm
from test_lbm_benchmarks import GHIA_X, GHIA_Y

U1000 = np.array([1.0, .65928, .57492, .51117, .46604, .33304, .18719, .05702, -.06080, -.10648, -.27805, -.38289,
                  -.29730, -.22220, -.20196, -.18109, 0.0])
V1000 = np.array([0.0, -.21388, -.27669, -.33714, -.39188, -.51500, -.42665, -.31966, .02526, .32235, .33075, .37095,
                  .32627, .30353, .29012, .27485, 0.0])

for N in (64, 128):
    fl = lbm.Flow2D((1.0, 1.0), 1.0 / N, nu=1e-3, rho=1.0, u_max=1.0, mach=0.1, tau_max=None,
                    sides={"top": lbm.Wall(1.0)}, device="cpu")
    fl.advance_to(59.0)
    u_prev = fl.velocity()[0]
    fl.advance_to(60.0)
    ux, uy = fl.velocity()
    i = N // 2
    ye = np.concatenate([[0.0], fl.y, [1.0]])
    u = np.interp(GHIA_Y, ye, np.concatenate([[0.0], 0.5 * (ux[i - 1] + ux[i]), [1.0]]))
    v = np.interp(GHIA_X, ye, np.concatenate([[0.0], 0.5 * (uy[:, i - 1] + uy[:, i]), [0.0]]))
    du, dv = np.abs(u - U1000)[1:-1], np.abs(v - V1000)[1:-1]
    print("Re 1000, %d^2: cell Re (lid) %.3g, limit %g, accepted; tau+ = %.4f; steady to %.1e; max |u - Ghia| = %.4f at "
          "y = %.4f, max |v - Ghia| = %.4f at x = %.4f; checks ok: %s" % (
              N, 1.0 / N / 1e-3, fl.re_cell_limit(), fl.tau_p, np.nanmax(np.abs(ux - u_prev)), du.max(),
              GHIA_Y[1:-1][du.argmax()], dv.max(), GHIA_X[1:-1][dv.argmax()],
              all(c["ok"] for c in fl.checks().values())))
