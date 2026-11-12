#!/bin/bash
# usage: batch.sh world1 world2 ...   (inside the container)
cd /lf/visualizations
for w in "$@"; do
  python3 /out/audit.py $w --out /out/res >> /out/logs/$w.log 2>&1
  echo "$(date +%T) $w done" >> /out/logs/batch.log
done
