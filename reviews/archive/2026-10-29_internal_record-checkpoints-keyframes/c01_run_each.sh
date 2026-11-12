#!/bin/sh
# [root path fixed after archiving, 2026-10-29, by the responder: reviews/ -> reviews/archive/]
# c01 with one Python process per visualization (as in a worker: lfphys.core.backend's record of the kernels used is
# per process). Usage: sh c01_run_each.sh   (from this folder)
ENGINE=$(cd ../../.. && pwd)
for v in v01_light_travel v02_double_slit v03_quantum_1d v04_orbits v05_optics_bench v06_qcd v07_bell_test v08_wave_3d \
         v09_thomas_3d v10_fast_observer v11_double_slit_2d v12_arrival_times_2d v13_hydrogen_3d v14_quarkonium_3d; do
  docker run --rm --name lf-rev-c01-$v -v "$ENGINE":/lf:ro -v "$PWD/out":/out -e PYTHONDONTWRITEBYTECODE=1 \
    -e LFPHYS_NO_GPU=1 -w /lf/visualizations light-funnel-viz \
    python3 /lf/reviews/archive/2026-10-29_internal_record-checkpoints-keyframes/c01_checkpoint_scenarios.py $v 2>&1 \
    | grep -v "Warning\|warn("
done
