"""Review B8 (v02 README table): T_TE, T_TM for two slits, d = 4 a, thin screen, lambda = 632.8 nm, with 'auto' (as v02)
and with the edge basis (exponentially convergent reference)."""
import math
import sys
sys.path.insert(0, "/lf/lfphys")
from lfphys.core.em import slit as S  # noqa: E402
lam = 0.6328
K = 2 * math.pi
for a_um in (2.0, 4.0, 8.0):
    a = a_um / lam
    d = 4 * a
    row = []
    for pol in ("TE", "TM"):
        sa = S.solve(K, [-d / 2, d / 2], a, 0.0, pol)
        se = S.solve(K, [-d / 2, d / 2], a, 0.0, pol, method="edge", modes=int(min(120, K * a / 2 + 20)))
        row.append(f"{pol}: auto ({sa.method}) {sa.transmission():.4f}, edge {se.transmission():.4f}")
    print(f"a = {a_um} um (k a = {K * a:.1f}): " + "; ".join(row) + f"; Kirchhoff {S.kirchhoff_transmission(K, [-d / 2, d / 2], a):.4f}")
