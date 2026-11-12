#!/bin/bash
cd /lf/visualizations
python3 /out/repro/r_v06_rg.py > /out/repro/r_v06_rg.out 2>&1
python3 /out/repro/r_v03_timing.py > /out/repro/r_v03_timing.out 2>&1
echo "$(date +%T) repro done" >> /out/logs/batch.log
for w in "$@"; do
  python3 /out/audit.py $w --out /out/res >> /out/logs/$w.log 2>&1
  echo "$(date +%T) $w done" >> /out/logs/batch.log
done
