# B3 review, check 14: where v10 says its image was computed. The panel «Где считалось» and the run's passport show
# root path updated to reviews/archive/ when the processed review was archived (responder, 2026-10-28)
# header.backend.used["relativity.raytrace"].drawn, which lfphys.core.backend keeps for the LAST drawn call of the
# kernel. In v10 the image is not the last call of a frame: the stars' visibility trace (scenes with stars) and the
# retarded shapes' visibility trace (moving bodies) come after it. Here each preset's first image is re-traced alone to
# get the device the image itself needs, and compared with what the header reports.
# Run (from engine/), on GPU 0:
#   docker run --rm --gpus '"device=0"' --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf \
#     -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server:/lf/visualizations/tests \
#     light-funnel-viz python3 reviews/archive/2026-10-28_internal_B3/c14_v10_device_report.py > reviews/archive/2026-10-28_internal_B3/out/c14_v10_device_report.txt
from harness import Harness

from lfphys.core import backend as B
from lfphys.core import raytrace as RT
from v10_fast_observer.viz import C

for preset in ("terrell", "city", "sky", "train"):
    h = Harness("v10_fast_observer", preset, seed=1)
    hd = h.of("header")[-1]
    rep = ((hd.get("backend") or {}).get("used") or {}).get(RT.KERNEL, {}).get("drawn")
    s = h.sim
    cam = s.camera()
    B.reset_used()
    RT.render(s.scene, s.observer(), cam, c=C)
    img = B.used()[RT.KERNEL]["drawn"]
    print(f"{preset:8s}: header reports {rep['device'] if rep else None} (size {rep.get('size') if rep else None}: "
          f"{rep.get('reason') if rep else ''}); the image itself: {img['device']} (size {img.get('size')}: {img.get('reason')})")
