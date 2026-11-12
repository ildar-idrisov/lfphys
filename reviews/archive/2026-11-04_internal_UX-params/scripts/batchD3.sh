#!/bin/bash
cd /lf/visualizations
timeout 900 python3 /out/audit.py p02_quantum --workers 8 --n-random 15 --only palette,palette_edit,preset_add,preset_edit,palette_param,random --out /out/res >> /out/logs/p02_quantum.log 2>&1
echo "$(date +%T) p02_quantum done (time-boxed)" >> /out/logs/batch.log
timeout 1200 python3 /out/audit.py p03_molecules --workers 8 --n-random 20 --out /out/res >> /out/logs/p03_molecules.log 2>&1
echo "$(date +%T) p03_molecules done (time-boxed)" >> /out/logs/batch.log
