# [root path fixed after archiving, 2026-10-28, by the responder: reviews/ -> reviews/archive/]
# Review B4, check c01: the Marchewka-Schuss intensity as Das & Struyve (PRA 104, 042214 (2021), arXiv:2105.14744)
# define it (Table I and Sec. III.B, eq. 27-28) against lfphys.theories.models.detection.marchewka_schuss_intensity.
#
# Root (fix after archiving): the engine is mounted at /lf (host: /home/ildar/hdd/projects/i/light-funnel/engine);
# this script lives in /lf/reviews/archive/2026-10-28_internal_B4/. The source text is mounted at /src (host:
# /tmp/claude-1000/-home-ildar-hdd/2d877fb3-83c1-460d-af16-9ddd26aff08b/scratchpad/b4src).
# Run:
#   docker run --rm --user "$(id -u):$(id -g)" -v <engine>:/lf:ro -v <b4src>:/src:ro -e PYTHONPATH=/lf/lfphys \
#     light-funnel-viz python3 /lf/reviews/archive/2026-10-28_internal_B4/c01_ms_intensity_source.py > out/c01_ms_intensity_source.txt
"""What the source says (text dump lines quoted below; the bars and primes of the PDF are lost in the dump, they were
read off the rendered page 2 and 4: Table I has (lambda' eps / pi) |d_x psibar(L, t)|^2 with psibar the Dirichlet
solution on (-inf, L], eq. 27 psibar(x, t) = psi(x, t) - psi(2L - x, t), so d_x psibar(L, t) = 2 d_x psi(L, t)).
The engine's docstring and ABOUT write lambda_MS = (lambda0/pi)|d psi/dx (L, t)|^2 with psi THE FREE WAVE, citing
'Das 2021, Table I'. Numerically: for the paper's Fig. 3 train (N = 10, sigma = 5, L = 10 sigma, eps = 0.01, v = 1,
lambda' = 0.01) the engine's intensity is 1/4 of the paper's, and the non-detection probability differs."""

import math
import re
import sys

import numpy as np

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.quantum.schrodinger1d import FreeGaussians  # noqa: E402
from lfphys.theories.models import detection as D  # noqa: E402

txt = open("/src/2105.14744.txt", encoding="utf-8").read().splitlines()
print("== source text (arXiv:2105.14744v1), lines with the authors, Table I and eqs. 27-28 ==")
for i, line in enumerate(txt):
    if re.search(r"Siddhant Das|Ward Struyve|Marchewka & Schuss \(MS\)|Dirichlet bound|ψ\(x, t\) − ψ\(2L − x, t\)|2∂x ψ\(L, t\)", line):
        print(f"{i + 1:4d}: {line.strip()[:150]}")
ref = open("/src/2211.13362.txt", encoding="utf-8").read().splitlines()
for i, line in enumerate(ref):
    if "042214" in line or "Questioning the adequacy" in line:
        print(f"2211.13362.txt {i + 1}: {line.strip()}")

# Fig. 3 parameters; packets phi(x + jL, 0) as in eq. 18 (carrier phase e^{i v jL / eps}); s = sigma / sqrt 2
N, sig, eps, v, lam = 10, 5.0, 0.01, 1.0, 0.01
L = 10 * sig
s, k0 = sig / math.sqrt(2), v / eps
fg = FreeGaussians([(np.exp(1j * k0 * j * L), -j * L, k0, s) for j in range(N)], m=1.0, hbar=eps)
tau0 = L / v
t = np.linspace(0, (N + 1) * tau0, 22001)
dpsi_free = fg.dpsi(L, t)
# the Dirichlet solution's left derivative at L, by a one-sided 4th-order difference of psibar(x) = psi(x) - psi(2L - x)
h = 1e-3
def psibar(x, tt):
    return fg.psi(x, tt) - fg.psi(2 * L - x, tt)
dbar = (25 * psibar(L, t) - 48 * psibar(L - h, t) + 36 * psibar(L - 2 * h, t) - 16 * psibar(L - 3 * h, t)
        + 3 * psibar(L - 4 * h, t)) / (12 * h)
ratio = np.abs(dbar) ** 2 / np.maximum(np.abs(dpsi_free) ** 2, 1e-300)
mask = np.abs(dpsi_free) ** 2 > 1e-3 * np.max(np.abs(dpsi_free) ** 2)
print("\n== |d_x psibar(L,t)|^2 / |d_x psi_free(L,t)|^2 where the flux is not negligible ==")
print(f"min {ratio[mask].min():.6f}  max {ratio[mask].max():.6f}  (eq. 27-28: exactly 4)")

lam_engine = D.marchewka_schuss_intensity(dpsi_free, lam)            # engine: (lam/pi)|d psi_free|^2  (eps = 1 here)
lam_paper = lam * eps / math.pi * np.abs(dbar) ** 2                  # Table I: (lam' eps / pi)|d psibar|^2
Pi_e, P_e = D.exponential(t, lam_engine)
Pi_p, P_p = D.exponential(t, lam_paper)
print("\n== non-detection probability P(inf) for the Fig. 3 train, lambda' = 0.01 ==")
print(f"engine's formula (lambda0/pi)|d psi_free|^2 with lambda0 = 0.01: P(inf) = {P_e:.6f}")
print(f"paper's Table I  (lambda' eps/pi)|d psibar|^2, lambda' = 0.01:   P(inf) = {P_p:.6f}")
print(f"ratio of the intensities (paper/engine) = {np.max(lam_paper[mask] / lam_engine[mask]):.6f} "
      f"(= 4 eps = {4 * eps:g} here; = 4 with hbar = m = 1)")
# eq. 31 of the paper: lambda_MS ~ (4 v^2 lambda' / (N pi eps)) sum |phi(kL - vt, 0)|^2 -- check the paper's own value
# at the first peak against lam_paper
i = int(np.argmin(np.abs(t - tau0)))
eq31 = 4 * v * v * lam / (N * math.pi * eps) * (1 / (sig * math.sqrt(math.pi)))
print(f"\npaper eq. 31 at t = tau0: {eq31:.6f}; Table I with psibar: {lam_paper[i]:.6f}; engine: {lam_engine[i]:.6f}")
