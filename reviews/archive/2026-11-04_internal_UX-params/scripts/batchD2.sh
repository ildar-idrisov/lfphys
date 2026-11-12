#!/bin/bash
cd /lf/visualizations
for w in "$@"; do
  python3 /out/audit.py $w --workers 8 --out /out/res >> /out/logs/$w.log 2>&1
  echo "$(date +%T) $w done" >> /out/logs/batch.log
done
