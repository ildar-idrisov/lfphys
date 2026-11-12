#!/bin/bash
# root path updated to reviews/archive/ when the processed review was archived (responder, 2026-10-28)
# B3 review: the GPU checks c04 (full narrow), c06 (small, full narrow), one after another on GPU 0, with the GPU's
# temperature logged between them. Run from engine/: setsid bash reviews/archive/2026-10-28_internal_B3/run_gpu_batch1.sh
R=reviews/archive/2026-10-28_internal_B3
D="docker run --rm --gpus \"device=0\" --user $(id -u):$(id -g) -v $PWD:/lf -w /lf -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server:/lf/visualizations/tests light-funnel-viz python3"
log() { echo "$(date +%T) $1 $(nvidia-smi --query-gpu=temperature.gpu,utilization.gpu,power.draw --format=csv,noheader -i 0)" >> $R/out/gpu_batch1.log; }
log start
eval $D $R/c04_v11_grid_fixed_wall.py narrow full 0.2 > $R/out/c04_v11_grid_fixed_wall_narrow_full.txt 2>&1; log c04
eval $D $R/c06_v11_absorber_width.py narrow small > $R/out/c06_v11_absorber_width_narrow_small.txt 2>&1; log c06s
eval $D $R/c06_v11_absorber_width.py narrow full > $R/out/c06_v11_absorber_width_narrow_full.txt 2>&1; log c06f
log done
