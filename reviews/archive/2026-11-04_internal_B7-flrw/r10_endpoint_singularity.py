"""r10: the error estimate at an integrable endpoint singularity. Dark energy alone with constant w: the conformal-time
integrand in xi is 2 xi^alpha with alpha = 1 - p = 3w (w in (-1/3, 0)), the age integrand 2 xi^(3 - p) = 2 xi^(2 + 3w)
(w in (-1, -2/3)). For a panel [0, h] the Gauss-Legendre error scales as h^(1 + alpha), so the error left after
halving is 1/(2^(1 + alpha) - 1) times the difference d that the engine records as the error (_adaptive accepts the
panel at xi = 0 when d <= rtol/10 of the segment). Closed forms as in r02.
Run (from engine/):
  docker run --rm --name lf-b7rc-r10 -v $PWD:/lf:ro -v $PWD/reviews/2026-11-04_internal_B7-flrw:/out \
    -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 -w /lf/lfphys light-funnel-viz python3 /out/r10_endpoint_singularity.py
"""
import sys
import warnings

import mpmath as mp

sys.path.insert(0, "/lf/lfphys")
from lfphys.theories.models import dark_energy as DE  # noqa: E402

mp.mp.dps = 40


def one(kind, w, z=0.0):
    bg = DE.background(70.0, 0.0, w0=w, wa=0.0)
    q = 1.5 * (1 + w)
    a = 1 / (1 + z)
    with warnings.catch_warnings(record=True) as wl:
        warnings.simplefilter("always")
        try:
            if kind == "eta":
                v, e = bg.conformal_time(z, with_error=True)
                ex = mp.mpf(a) ** (q - 1) / (q - 1) * bg.hubble_time
                alpha = 3 * w
            else:
                v, e = bg.age(z, with_error=True)
                ex = mp.mpf(a) ** q / q * bg.hubble_time
                alpha = 2 + 3 * w
        except Exception as exc:  # noqa: BLE001
            return f"{kind:4s} w = {w:6.3f}: {type(exc).__name__}: {exc}"
    act = abs(v - float(ex))
    warn = f"  [{len(wl)} warning(s): {str(wl[0].message)[:50]}]" if wl else ""
    amp = 1 / (2 ** (1 + alpha) - 1)
    return (f"{kind:4s} w = {w:6.3f} (alpha = {alpha:+.2f}, error-after-halving/d = {amp:5.2f}): actual rel "
            f"{act / float(ex):.2e}, stated rel {e / float(ex):.2e}, actual/stated {act / e:6.2f}"
            f"{'  BOUND FAILS' if act > e else ''}{warn}")


for w in (-0.1, -0.15, -0.2, -0.22, -0.24, -0.26, -0.28):
    print(one("eta", w))
for w in (-0.7, -0.75, -0.8, -0.82, -0.84, -0.86, -0.88):
    print(one("t", w))
