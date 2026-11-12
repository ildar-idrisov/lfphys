"""r05: the external comparison rows (tests/external/test_ext_flrw_astropy.py, image light-funnel-ext): where the engine
is farther from the 30-digit reference than Astropy, how far; and how much of each tolerance the difference uses.
Run (from engine/):
  docker run --rm --name lf-b7rc-r05 -v $PWD:/lf:ro -v $PWD/reviews/2026-11-04_internal_B7-flrw:/out \
    -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 -w /lf/lfphys/tests/external light-funnel-ext \
    python3 /out/r05_ext_rows.py
"""
import sys

sys.path.insert(0, "/lf/lfphys")
sys.path.insert(0, "/lf/lfphys/tests/external")
import test_ext_flrw_astropy as T  # noqa: E402

rows = T.rows()
ref = [r for r in rows if r.eng_err is not None]
print(f"{len(rows)} rows, {len(ref)} with an exact reference")
worst = sorted(ref, key=lambda r: r.eng_err / max(abs(float(r.engine)), 1e-300), reverse=True)[:8]
print("largest engine errors relative to the value:")
for r in worst:
    v = abs(float(r.engine))
    print(f"   {r.quantity:55s} {r.inputs:10s} eng rel {r.eng_err / v:.2e}  lib rel {r.lib_err / v:.2e}")
lib_closer = [r for r in ref if r.lib_err < r.eng_err]
big = [r for r in lib_closer if r.eng_err / max(abs(float(r.engine)), 1e-300) > 1e-14]
print(f"rows where Astropy is closer: {len(lib_closer)}; of these with engine rel error > 1e-14: {len(big)}")
for r in big[:10]:
    v = abs(float(r.engine))
    print(f"   {r.quantity:55s} {r.inputs:10s} eng rel {r.eng_err / v:.2e}  lib rel {r.lib_err / v:.2e}")
use = sorted(rows, key=lambda r: r.diff / r.tol if r.tol > 0 else 0, reverse=True)[:8]
print("largest diff/tol:")
for r in use:
    print(f"   {r.quantity:55s} {r.inputs:10s} diff/tol {r.diff / r.tol:.3f}  basis: {r.basis}  "
          f"{'(xfail)' if r.xfail else ''}")
# the engine's own stated error against its actual error, where a reference exists, for the integrals
