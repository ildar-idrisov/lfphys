#!/bin/bash
cd /lf/visualizations
python3 /out/repro/r_v06_rg.py > /out/repro/r_v06_rg.out 2>&1
python3 /out/repro/r_v01_flash.py > /out/repro/r_v01_flash.out 2>&1
echo "$(date +%T) v06 scan done" >> /out/logs/batch.log
AUDIT_MEM_GB=6 python3 /out/audit.py v08_wave_3d --workers 2 --out /out/res >> /out/logs/v08_wave_3d.log 2>&1
echo "$(date +%T) v08_wave_3d done" >> /out/logs/batch.log
for w in v11_double_slit_2d v12_arrival_times_2d; do
  AUDIT_MEM_GB=6 python3 /out/audit.py $w --workers 3 --out /out/res >> /out/logs/$w.log 2>&1
  echo "$(date +%T) $w done" >> /out/logs/batch.log
done
