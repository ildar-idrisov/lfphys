#!/bin/bash
cd /lf/visualizations
AUDIT_MEM_GB=6 python3 /out/audit.py v08_wave_3d --workers 5 --only default,single,pair,all,preset,view_extreme,new_world --out /out/res >> /out/logs/v08_wave_3d.log 2>&1
echo "$(date +%T) v08_wave_3d done" >> /out/logs/batch.log
for w in v11_double_slit_2d v12_arrival_times_2d; do
  AUDIT_MEM_GB=6 python3 /out/audit.py $w --workers 5 --out /out/res >> /out/logs/$w.log 2>&1
  echo "$(date +%T) $w done" >> /out/logs/batch.log
done
