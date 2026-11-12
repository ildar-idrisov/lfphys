# [root path fixed after archiving, 2026-10-29, by the responder: reviews/ -> reviews/archive/]
# Review 2026-10-29, check c07: lfphys.core.backend's record of the kernels used (_USED) is per process and not in a
# checkpoint. Within one visualization's worker, does it change after the header (so that a new world's header would
# differ between the uninterrupted and the resumed worker)? Per visualization in a fresh record: after the first world's
# header, and after 40 frames.
#   docker run --rm --name lf-rev-c07 -v <engine>:/lf:ro -v <this folder>/out:/out -e LFPHYS_NO_GPU=1 \
#     -w /lf/visualizations light-funnel-viz python3 /lf/reviews/archive/2026-10-29_internal_record-checkpoints-keyframes/c07_backend_used.py
import queue
import sys

sys.path[:0] = ["/lf/visualizations/server", "/lf/visualizations", "/lf/lfphys", "/lf/visualizations/tests"]
from lfphys.core import backend as B  # noqa: E402
from lfviz import registry  # noqa: E402
from lfviz.sim import Runner  # noqa: E402
from test_restore import SMALL  # noqa: E402

lines = []
for vid in ["v08_wave_3d", "v09_thomas_3d", "v10_fast_observer", "v11_double_slit_2d", "v12_arrival_times_2d"]:
    B.reset_used()
    viz = registry.load(vid)
    p, _ = viz["schema"].resolve(None, SMALL.get(vid, {}))
    sim = viz["simulation"](p, 7, lambda m, b=None: None)
    r = Runner(sim, sim.emit, queue.Queue())
    r._start_world()
    u0 = {k: sorted(v) for k, v in B.used().items()}
    for k in range(40):
        r._advance(sim.t + 0.3 * sim.default_speed)
        r._frame(0.0)
    u1 = {k: sorted(v) for k, v in B.used().items()}
    lines.append(f"{vid} after header: {u0}  after 40 frames: {u1}  same: {u0 == u1}")
    print(lines[-1], flush=True)
open("/out/c07_backend_used.txt", "w").write("\n".join(lines) + "\n")
