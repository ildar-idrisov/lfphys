# Review B8-mie, script s10: what v17's checks "debye", "energy" and "theorem" can detect. A deliberately wrong
# engine is made by perturbing one ingredient (monkeypatching lfphys.core.optics.mie); a check that still passes is
# blind to that ingredient.
#   D: the logarithmic derivative D_n(z) multiplied by (1 + 1e-3) (both for mx and x)
#   PSI: psi_n multiplied by (1 + 1e-3 n/N) (a smooth, order-dependent error)
#   CHI: chi_n multiplied by (1 + 1e-3)
# For each: the error of a_n, b_n against the unperturbed engine, and the residuals the three checks compute.
import sys
import numpy as np
sys.path.insert(0, "/lf/lfphys")
from lfphys.core.optics import mie, mie_debye as dbe  # noqa: E402

m, x = 1.3354, 300.0
a0, b0 = mie.coefficients(m, x)
orig = {"log_derivative": mie.log_derivative, "psi": mie.psi, "chi": mie.chi}


def checks(tag):
    a, b = mie.coefficients(m, x)
    N = len(a)
    s = max(np.abs(a0).max(), np.abs(b0).max())
    dcoef = max(np.abs(a - a0[:N]).max(), np.abs(b - b0[:N]).max()) / s if N == len(a0) else float("nan")
    q = mie.efficiencies_from(a, b, x)
    S1, _ = mie.amplitudes(a, b, np.array([0.0]))
    theorem = abs(q["Qext"] - 4 / x ** 2 * S1[0].real) / q["Qext"]
    energy = max(np.abs(a.real - np.abs(a) ** 2).max(), np.abs(b.real - np.abs(b) ** 2).max())
    c = dbe.coefficients(m, x, p_max=3)
    aa, bb = mie.coefficients(m, x, n_max=c["N"])
    debye = max(np.abs(c["sum_a"] - aa).max(), np.abs(c["sum_b"] - bb).max()) / max(np.abs(aa).max(), np.abs(bb).max())
    print(f"{tag:6s}: coefficients off by {dcoef:.1e} of the largest; theorem residual {theorem:.1e} (v17 tol ~1e-11); "
          f"energy |Re a - |a|^2| {energy:.1e} (tol 1e-10); debye {debye:.1e} (tol 5e-10)")


checks("none")
mie.log_derivative = lambda z, N: orig["log_derivative"](z, N) * (1 + 1e-3)
checks("D")
mie.log_derivative = orig["log_derivative"]
mie.psi = lambda z, N: orig["psi"](z, N) * (1 + 1e-3 * np.arange(N + 1) / N).reshape((-1,) + (1,) * np.ndim(np.atleast_1d(z)))
checks("PSI")
mie.psi = orig["psi"]
mie.chi = lambda xx, N: orig["chi"](xx, N) * (1 + 1e-3)
checks("CHI")
mie.chi = orig["chi"]

# targeted: D_n wrong only at the argument m x (psi(mx) is then also built from the wrong D by Miller's algorithm in
# the Debye route, consistently); D_n(x) and psi(x) exact
def d_mx_only(z, N):
    out = orig["log_derivative"](z, N)
    zz = np.atleast_1d(np.asarray(z))
    if not np.allclose(zz, x):
        out = out * (1 + 1e-3)
    return out


mie.log_derivative = d_mx_only
checks("D(mx)")
mie.log_derivative = orig["log_derivative"]
