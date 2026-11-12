# Review B5, check c06b: the v15 world found by c06 (chi = 0.998, incl = 81 deg), built as the server builds it: does
# the player get a failed `edge` check for this correct run? Root and run as c02 (see its header).
import sys

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402

for incl in (81.0, 99.0, 80.0):
    h = Harness("v15_kerr_shadow", None, {"res": "s", "chi": 0.998, "incl": incl})
    c = h.checks()["edge"]
    print(f"chi=0.998 incl={incl}: edge value {c['value']:.3e}, tol {c['tol']:.3e}, ok = {c['ok']}")
