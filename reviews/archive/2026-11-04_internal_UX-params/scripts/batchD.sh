#!/bin/bash
cd /lf/visualizations
python3 /out/typed.py > /out/typed.out 2>&1
for w in "$@"; do
  python3 /out/audit.py $w --out /out/res >> /out/logs/$w.log 2>&1
  echo "$(date +%T) $w done" >> /out/logs/batch.log
done
