"""Q: with closed (periodic) window edges — a law the wrapper offers — does the scene refuse a charged particle next
to a vector potential whose line integral across the window does not vanish (the Landau gauge of a confined field,
a flux tube)? The module docstring says psi must vanish at those edges, but nothing enforces it.

Test: a field-free charged packet (electron) far from a confined field Bz (or a flux tube) moves along +y through the
window's face y = +L/2 and comes back at -L/2 (a torus). It never enters the field. Compared with the same run without
the field object: the overlap |<psi_field|psi_none>| after the crossing (1 if the field had no effect on it; the
physics of a field-free region a packet does not encircle) and the change of <p_y>."""
import math
import numpy as np
from lfphys.core.quantum import scene as QS

el = QS.species("electron")
L, n = 40.0, 160
d = L / n


def run(obj):
    s = QS.Scene((n, n), d, dt=0.01, edges=None)  # closed: periodic
    if obj is not None:
        s.add(obj)  # placed before the packet (no switching kick)
    pid = s.add_particle(QS.Packet(el, [5.0, 8.0], [0.0, 2.0], [1.5, 1.5]))
    s.advance(800)  # t = 8: the centre moved by 16 along +y, through the face at y = 20
    return s, pid


s0, p0 = run(None)
psi0 = s0.wave(p0)
g = s0.grid
for label, obj in (("confined Bz (x in [-15,-5], y in [-5, 5]; flux 1.5 h/e), strip towards +x",
                    QS.MagneticField([0, 0, 1.5 * 2 * math.pi / 100.0], lo=[-15.0, -5.0], hi=[-5.0, 5.0], edge=1.0)),
                   ("flux tube at (-10, 0), half a flux quantum, R = 1", QS.FluxTube([-10.0, 0.0], math.pi, 1.0))):
    try:
        s1, p1 = run(obj)
    except ValueError as e:
        print(f"{label}: refused: {e}")
        continue
    psi1 = s1.wave(p1)
    # gauge-invariant comparison: densities, and the overlap after removing the field object's gauge where the
    # packet is (pure gauge there): |<psi1|psi0>| maximised over a constant phase is a lower bound of the agreement
    rho0, rho1 = np.abs(psi0) ** 2, np.abs(psi1) ** 2
    dens = float(np.sum(np.abs(rho1 - rho0))) * g.dV
    X, Y = g.mesh()
    my0 = float(np.sum(Y * rho0) * g.dV)
    print(f"{label}:\n   admitted with closed edges; after crossing the face: int |rho_field - rho_none| = {dens:.3e} "
          f"(0 if the field-free packet were unaffected); window_face check {s1.checks()[p1]['window_face']:.2e}")
