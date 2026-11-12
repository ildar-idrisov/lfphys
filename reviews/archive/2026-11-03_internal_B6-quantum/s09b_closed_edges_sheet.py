"""Q (continuation of s09): crossing the window's y-face in the gauge strip only twists the boundary condition (a
packet that does not interfere with itself across the face keeps its density: s09). The Landau gauge of a confined
field, A_y = B g(y) F(x), is not periodic in x: on the closed (periodic) window it drops from B W g(y) to 0 at the
x-face, i.e. a field sheet of flux -Phi sits at the face (the torus needs zero net flux). A charged packet crossing
that face inside the strip's y-range gets the kick Delta(k_y) = q Delta A_y = -q B W (here 0.94/nm), although it never
comes near the field region the user placed.

Field: Bz in x in [-5, 5], y in [5, 15] (flux 1.5 h/e). Packet: an electron at (12, 10), k = (2, 0), window 60 nm, crossing x = 30
-> -30 and stopping at x ~ -24 (t = 12): it never enters x in [-5, 5]. Closed edges against no field; the same with
open edges (absorbing layers: the packet is absorbed before the face, as the module requires)."""
import math
import numpy as np
from lfphys.core.quantum import scene as QS

el = QS.species("electron")
L, n = 60.0, 240
d = L / n
Bz = 1.5 * 2 * math.pi / 100.0


def run(field, edges):
    s = QS.Scene((n, n), d, dt=0.01, edges=edges)
    if field:
        s.add(QS.MagneticField([0, 0, Bz], lo=[-5.0, 5.0], hi=[5.0, 15.0], edge=1.0))
    pid = s.add_particle(QS.Packet(el, [12.0, 10.0], [2.0, 0.0], [1.5, 1.5]))
    s.advance(1200)
    psi = s.wave(pid)
    g = s.grid
    X, Y = g.mesh()
    rho = np.abs(psi) ** 2
    N = float(np.sum(rho)) * g.dV
    # <y> and the kinetic <v_y> from the density's current (gauge invariant): j_y integrated
    J = g.current(psi, s.hamiltonian(s._key(s.particles[pid])))
    vy = float(np.sum(J[1])) * g.dV / max(N, 1e-300)
    my = float(np.sum(np.broadcast_to(Y, g.shape) * rho)) * g.dV / max(N, 1e-300)
    mx = float(np.sum(np.broadcast_to(X, g.shape) * rho)) * g.dV / max(N, 1e-300)
    return N, mx, my, vy


for edges, lab in ((None, "closed (periodic)"), (QS.EdgeLayers(3.0, 4.0), "open (absorbing layers)")):
    a = run(False, edges)
    b = run(True, edges)
    print(f"{lab}: no field: norm {a[0]:.3f}, <x> {a[1]:.2f}, <y> {a[2]:.3f}, <v_y> {a[3]:+.4f};  "
          f"with the field: norm {b[0]:.3f}, <x> {b[1]:.2f}, <y> {b[2]:.3f}, <v_y> {b[3]:+.4f}  "
          f"(expected kick -q B W g = {Bz * 10:+.3f}/nm for q = -1)")
