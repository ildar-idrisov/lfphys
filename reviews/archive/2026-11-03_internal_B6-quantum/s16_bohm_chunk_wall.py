"""Q: the Bohm interval of 8 steps with psi quadratic in time, near a wall: inside the wall's edges the potential turns
the phase by V h (preset: 3 eV, h = 8 dt: 2.5 rad; a 30 eV wall: 25 rad), where the time interpolation is poor.
The double-slit preset's wave (scene built by the wrapper, wall 3 eV, and the same at 30 eV), 300 Bohm points from
|psi|^2 advanced to t = 12 units (after the wall) with intervals of 2, 4 and 8 steps from the same starts; the
differences between them (an interpolation error falling as h^3 would make 8 vs 2 ~ 64x the 4 vs 2 difference / 9)."""
import copy, math, sys
import numpy as np
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness
from lfphys.core.quantum import scene as QS
from lfphys.theories.interpretations import bohm
from p02_quantum import viz as P

for V in (3.0, 30.0):
    pr = copy.deepcopy(P.SCHEMA.presets["double_slit"]["params"])
    for o in pr["scene"]["objects"]:
        if o["type"] == "packet":
            o["values"]["bohm"] = 0
        if o["type"] == "slit_wall":
            o["values"]["V"] = V
    h = Harness("p02_quantum", None, pr)
    st0 = h.sim.qs.state_dict()
    rho = np.abs(st0["particles"][0]["psi"]) ** 2
    g0 = h.sim.qs.grid
    rng = np.random.default_rng(7)
    idx = rng.choice(rho.size, size=300, p=(rho / rho.sum()).ravel())
    ii = np.unravel_index(idx, g0.shape)
    X0 = np.stack([g0.axes[a][ii[a]] + (rng.random(300) - 0.5) * g0.d[a] for a in range(2)], axis=1)
    res = {}
    for chunk in (2, 4, 8):
        s = QS.Scene.from_state_dict(copy.deepcopy(st0))
        X = X0.copy()
        alive = np.ones(len(X), bool)
        n = int(round(12.0 / s.dt))
        for _ in range(n // chunk):
            s.advance(chunk, snapshots=True)
            snaps, hh = s.snapshots(1)
            grid, H, xp = s.guidance(1)
            X, _ = bohm.advance_ensemble(grid, snaps, X, hh, H, xp=xp)
        res[chunk] = X
    d42 = np.linalg.norm(res[4] - res[2], axis=1)
    d82 = np.linalg.norm(res[8] - res[2], axis=1)
    print(f"wall {V:4.0f} eV (dt {st0['dt']}): |X(4) - X(2)| max {d42.max():.2e} median {np.median(d42):.1e} nm; "
          f"|X(8) - X(2)| max {d82.max():.2e} median {np.median(d82):.1e} nm; points > 0.5 nm apart (8 vs 2): "
          f"{int(np.sum(d82 > 0.5))}/300; fringe spacing at the screen ~ 5.8 nm")
